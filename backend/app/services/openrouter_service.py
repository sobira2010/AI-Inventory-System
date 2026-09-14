"""
OpenRouter Fallback LLM Service.

Uses the OpenAI-compatible API via httpx to call NVIDIA Nemotron 3
through OpenRouter when Gemini quota is exhausted.

The tool-calling loop is handled manually since OpenRouter does not
have Automatic Function Calling like the google-genai SDK.
"""

import json
import logging
import time
from typing import Any, Callable, Optional

import httpx

from app.config import settings
from app.services.gemini_service import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MAX_TOOL_ROUNDS = 8  # safety cap to prevent infinite loops

MAX_ATTEMPTS = 3           # attempts per API call for transient failures
RETRY_DELAYS = [1.0, 2.5]  # backoff (s) between attempts
TRANSIENT_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


# ── Lightweight response wrapper ────────────────────────────────────
# Mimics the google-genai response structure so agent_service.py
# can extract text with the same code path.

class _Part:
    def __init__(self, text: str):
        self.text = text


class _Content:
    def __init__(self, parts: list[_Part]):
        self.parts = parts


class _Candidate:
    def __init__(self, content: _Content):
        self.content = content


class OpenRouterResponse:
    """Thin wrapper that looks like a Gemini GenerateContentResponse."""

    def __init__(self, text: str):
        self.candidates = [_Candidate(_Content([_Part(text)]))]


# ── Tool conversion ─────────────────────────────────────────────────

def _gemini_tools_to_openai(tools: list) -> list[dict]:
    """Convert google-genai Tool objects to OpenAI-format tool dicts.

    ``tools`` is a list of ``google.genai.types.Tool`` objects each
    containing ``function_declarations``.  We flatten them into the
    OpenAI ``tools`` array.
    """
    openai_tools: list[dict] = []
    for tool in tools:
        for decl in getattr(tool, "function_declarations", []):
            params = getattr(decl, "parameters", None)
            schema: dict[str, Any] = {"type": "object", "properties": {}}
            if params is not None:
                props = getattr(params, "properties", None) or {}
                for prop_name, prop_schema in props.items():
                    prop_type = getattr(prop_schema, "type", None)
                    type_map = {
                        "STRING": "string",
                        "INTEGER": "integer",
                        "NUMBER": "number",
                        "BOOLEAN": "boolean",
                        "ARRAY": "array",
                        "OBJECT": "object",
                    }
                    schema["properties"][prop_name] = {
                        "type": type_map.get(str(prop_type), "string"),
                        "description": getattr(prop_schema, "description", ""),
                    }
                required = getattr(params, "required", None)
                if required:
                    schema["required"] = list(required)

            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": decl.name,
                        "description": getattr(decl, "description", ""),
                        "parameters": schema,
                    },
                }
            )
    return openai_tools


def _build_openai_messages(
    history: list[dict],
    user_message: str,
) -> list[dict]:
    """Build OpenAI-format messages from conversation history."""
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    for msg in history:
        role = msg["role"]
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    return messages


# ── Tool execution ──────────────────────────────────────────────────

def _execute_tool(
    tool_name: str,
    tool_args: dict,
    tool_callables: dict[str, Callable],
) -> str:
    """Execute a tool callable and return the result as a JSON string."""
    callable_fn = tool_callables.get(tool_name)
    if callable_fn is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        result = callable_fn(**tool_args)
        return json.dumps(result, default=str)
    except Exception as e:
        logger.error(f"OpenRouter tool execution error ({tool_name}): {e}")
        return json.dumps({"error": str(e)})


# ── Main API ────────────────────────────────────────────────────────

def _post_chat(
    client: httpx.Client,
    headers: dict,
    payload: dict,
) -> dict:
    """POST to /chat/completions with retry for transient failures.

    Retries network errors, transient HTTP statuses (429/5xx), and the
    "HTTP 200 with an {\"error\": ...} body and no ``choices``" case
    that OpenRouter's free tier sometimes returns under load.

    Raises RuntimeError (after retries) or httpx.HTTPError for
    non-transient HTTP errors (e.g. 401, 400).
    """
    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    last_error = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = client.post(url, headers=headers, json=payload)

            if resp.status_code in TRANSIENT_STATUS:
                last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
                logger.warning(
                    "OpenRouter transient error "
                    f"(attempt {attempt}/{MAX_ATTEMPTS}): {last_error}"
                )
            else:
                resp.raise_for_status()
                data = resp.json()

                if "choices" not in data:
                    # OpenRouter quirk: 200 + {"error": {...}} under load
                    last_error = f"200 without choices: {resp.text[:300]}"
                    logger.warning(
                        "OpenRouter malformed response "
                        f"(attempt {attempt}/{MAX_ATTEMPTS}): {last_error}"
                    )
                else:
                    return data

        except httpx.HTTPStatusError:
            # Non-transient HTTP error (auth, bad request…) — do not retry
            raise
        except (httpx.HTTPError, ValueError) as exc:
            # Network errors, timeouts, and invalid-JSON (ValueError)
            last_error = f"{type(exc).__name__}: {exc}"
            logger.warning(
                "OpenRouter request error "
                f"(attempt {attempt}/{MAX_ATTEMPTS}): {last_error}"
            )

        if attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_DELAYS[attempt - 1])

    raise RuntimeError(
        f"OpenRouter failed after {MAX_ATTEMPTS} attempts — last error: {last_error}"
    )


def send_message(
    message: str,
    history: list[dict],
    tools: list,
    tool_callables: dict[str, Callable],
) -> OpenRouterResponse:
    """Send a message via OpenRouter with tool-calling loop.

    Args:
        message:         The user's latest message.
        history:         Previous conversation messages.
        tools:           google-genai Tool objects (will be converted).
        tool_callables:  Map of tool name → callable for execution.

    Returns:
        OpenRouterResponse that mimics the Gemini response structure.
    """
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not configured. "
            "Please add it to your .env file."
        )

    model = settings.OPENROUTER_MODEL
    openai_tools = _gemini_tools_to_openai(tools)
    messages = _build_openai_messages(history, message)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "AI Inventory Management System",
    }

    with httpx.Client(timeout=60.0) as client:
        for round_num in range(MAX_TOOL_ROUNDS):
            payload: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,
            }
            if openai_tools:
                payload["tools"] = openai_tools

            data = _post_chat(client, headers, payload)

            msg = data["choices"][0]["message"]

            # If there are no tool calls, we're done.  Do not depend on
            # finish_reason — providers report it inconsistently.
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                # Fall back to reasoning text when content is empty
                text = msg.get("content") or msg.get("reasoning") or ""
                return OpenRouterResponse(text)

            # Execute tool calls and append results.  Re-append only the
            # standard fields — echoing reasoning_details back can cause
            # 400s on the next round with some providers.
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.get("content"),
                    "tool_calls": tool_calls,
                }
            )

            for tc in tool_calls:
                fn = tc["function"]
                tool_name = fn["name"]
                try:
                    tool_args = json.loads(fn["arguments"])
                except (json.JSONDecodeError, TypeError):
                    tool_args = {}

                logger.info(
                    f"OpenRouter tool call: {tool_name}({tool_args})"
                )
                result_str = _execute_tool(
                    tool_name, tool_args, tool_callables
                )
                logger.info(
                    f"OpenRouter tool result: {tool_name} -> "
                    f"{result_str[:200]}..."
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result_str,
                    }
                )

        # Safety cap reached — return whatever we have
        logger.warning("OpenRouter tool-calling loop hit max rounds.")
        # Ask the model to summarise without tools
        payload_no_tools = {
            "model": model,
            "messages": messages
            + [
                {
                    "role": "user",
                    "content": (
                        "Please provide your final answer now based on "
                        "the tool results above. Do not call any more tools."
                    ),
                }
            ],
            "temperature": 0.3,
        }
        data = _post_chat(client, headers, payload_no_tools)
        final_msg = data["choices"][0]["message"]
        final_text = final_msg.get("content") or final_msg.get("reasoning") or ""
        return OpenRouterResponse(final_text)
