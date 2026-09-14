"""
Agent Service for the Inventory AI Agent.

Orchestrates the conversation flow between the user, Gemini LLM, and
inventory tools.

The Chat API (client.chats.create + chat.send_message) handles the
function-call loop internally via Automatic Function Calling (AFC).
We register our controlled inventory tools as Python callables so the
SDK can invoke them directly, then returns the final natural-language
response.  No manual iteration over function_call parts is needed.
"""

import json
import logging
import re
from typing import Optional, Callable
from google.genai import types
from google.genai.errors import ClientError
from sqlalchemy.orm import Session
from app.config import settings

from app.services.gemini_service import (
    _get_client,
    SYSTEM_PROMPT,
)
from app.services import agent_tools
from app.services import openrouter_service

logger = logging.getLogger(__name__)


# ── Custom exception for Gemini quota exhaustion ────────────────────
class GeminiQuotaExceeded(Exception):
    """Raised when the Gemini API returns HTTP 429 RESOURCE_EXHAUSTED."""

    def __init__(self, message: str, retry_after_seconds: Optional[int] = None):
        self.message = message
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message)


def _is_quota_exceeded(exc: Exception) -> bool:
    """Check whether an exception represents a Gemini 429 quota error."""
    if not isinstance(exc, ClientError):
        return False
    if exc.code == 429:
        return True
    # Fallback: check the status string in case code is not set
    if getattr(exc, "status", None) and "RESOURCE_EXHAUSTED" in str(exc.status).upper():
        return True
    return False


def _extract_retry_delay(exc: Exception) -> Optional[int]:
    """Try to extract a retry delay in seconds from the Gemini error details."""
    try:
        msg = str(exc.message) or str(exc)
        match = re.search(r'retry\s+in\s+(\d+)\s*sec', msg, re.IGNORECASE)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return None

# In-memory conversation store: {user_id: [messages]}
_conversations: dict[int, list[dict]] = {}


def get_conversation_history(user_id: int) -> list[dict]:
    """Get conversation history for a user."""
    return _conversations.get(user_id, [])


def add_to_history(user_id: int, role: str, content: str):
    """Add a message to user's conversation history."""
    if user_id not in _conversations:
        _conversations[user_id] = []
    _conversations[user_id].append({"role": role, "content": content})
    if len(_conversations[user_id]) > 40:
        _conversations[user_id] = _conversations[user_id][-40:]


def clear_conversation(user_id: int):
    """Clear conversation history for a user."""
    _conversations.pop(user_id, None)


# ── Controlled inventory callables ──────────────────────────────────
# Each wraps a tool from agent_tools and is registered as an AFC
# callable so the Chat API can invoke it automatically.

def _list_products() -> dict:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        return agent_tools.list_products(db)
    finally:
        db.close()


def _get_product(product_id: int) -> dict:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        return agent_tools.get_product(db, product_id=product_id)
    finally:
        db.close()


def _search_products(search_term: str) -> dict:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        return agent_tools.search_products(db, search_term=search_term)
    finally:
        db.close()


def _create_product(
    name: str,
    category: str,
    price: float,
    quantity: int,
    minimum_stock: int,
    description: Optional[str] = None,
    supplier: Optional[str] = None,
) -> dict:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        return agent_tools.create_product(
            db,
            name=name,
            category=category,
            price=price,
            quantity=quantity,
            minimum_stock=minimum_stock,
            description=description,
            supplier=supplier,
        )
    finally:
        db.close()


def _update_product(
    product_id: int,
    name: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    price: Optional[float] = None,
    quantity: Optional[int] = None,
    minimum_stock: Optional[int] = None,
    supplier: Optional[str] = None,
) -> dict:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        fields = {}
        if name is not None:
            fields["name"] = name
        if category is not None:
            fields["category"] = category
        if description is not None:
            fields["description"] = description
        if price is not None:
            fields["price"] = price
        if quantity is not None:
            fields["quantity"] = quantity
        if minimum_stock is not None:
            fields["minimum_stock"] = minimum_stock
        if supplier is not None:
            fields["supplier"] = supplier
        return agent_tools.update_product(db, product_id=product_id, **fields)
    finally:
        db.close()


def _delete_product(product_id: int, confirm: bool = False) -> dict:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        if not confirm:
            # Return product info for confirmation prompt — do NOT delete
            product_result = agent_tools.get_product(db, product_id)
            if product_result.get("success") and product_result.get("product"):
                p = product_result["product"]
                return {
                    "success": True,
                    "needs_confirmation": True,
                    "product": p,
                    "message": (
                        f"⚠️ **Delete Confirmation Required**\n\n"
                        f"I found this product:\n"
                        f"- **ID:** {p['id']}\n"
                        f"- **Name:** {p['name']}\n"
                        f"- **Category:** {p['category']}\n"
                        f"- **Quantity:** {p['quantity']}\n"
                        f"- **Price:** ₹{p['price']:,.2f}\n\n"
                        f"Are you sure you want to delete this product? "
                        f"This action cannot be undone.\n\n"
                        f"Reply **yes** to confirm or **no** to cancel."
                    ),
                }
            return product_result
        return agent_tools.delete_product(db, product_id=product_id)
    finally:
        db.close()


def _get_out_of_stock_products() -> dict:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        return agent_tools.get_out_of_stock_products(db)
    finally:
        db.close()


def _get_low_stock_products() -> dict:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        return agent_tools.get_low_stock_products(db)
    finally:
        db.close()


def _get_restock_recommendations() -> dict:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        return agent_tools.get_restock_recommendations(db)
    finally:
        db.close()


def _get_inventory_summary() -> dict:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        return agent_tools.get_inventory_summary(db)
    finally:
        db.close()


def _get_restock_analysis() -> dict:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        return agent_tools.get_restock_analysis(db)
    finally:
        db.close()


# Map of tool name → callable
TOOL_CALLABLES: dict[str, Callable] = {
    "list_products": _list_products,
    "get_product": _get_product,
    "search_products": _search_products,
    "create_product": _create_product,
    "update_product": _update_product,
    "delete_product": _delete_product,
    "get_out_of_stock_products": _get_out_of_stock_products,
    "get_low_stock_products": _get_low_stock_products,
    "get_restock_recommendations": _get_restock_recommendations,
    "get_inventory_summary": _get_inventory_summary,
    "get_restock_analysis": _get_restock_analysis,
}


def _extract_last_product_id(history: list[dict]) -> Optional[int]:
    """Extract the most recently mentioned product ID from conversation history."""
    import re
    for msg in reversed(history[-6:]):
        text = msg["content"]
        matches = re.findall(r'(?:ID\s*[:=]?\s*|product\s+)(\d+)', text, re.IGNORECASE)
        if matches:
            return int(matches[-1])
    return None


def _detect_action(text: str) -> str:
    """Detect the action type from the AI response text."""
    text_lower = text.lower()
    if "created" in text_lower or "added" in text_lower:
        return "create_product"
    if "updated" in text_lower or "changed" in text_lower:
        return "update_product"
    if "deleted" in text_lower or "removed" in text_lower:
        return "delete_product"
    if "out of stock" in text_lower:
        return "get_out_of_stock_products"
    if "low stock" in text_lower or "restock" in text_lower:
        return "get_low_stock_products"
    if "recommend" in text_lower:
        return "get_restock_recommendations"
    if "inventory" in text_lower and "summary" in text_lower:
        return "get_inventory_summary"
    if "found" in text_lower or "product" in text_lower:
        return "search_products"
    return "unknown"


def _try_openrouter_fallback(message: str, user_id: int) -> Optional[dict]:
    """Attempt to handle the message via OpenRouter / Nemotron 3.

    Returns a result dict on success, or None if OpenRouter is not
    configured or also fails.
    """
    if not settings.OPENROUTER_API_KEY:
        logger.info("OpenRouter not configured — skipping fallback.")
        return None

    try:
        history = get_conversation_history(user_id)
        # Pass the google-genai Tool objects — openrouter_service
        # converts them to OpenAI format internally.
        from app.services.gemini_service import build_tools_schema
        tools_schema = build_tools_schema()

        response = openrouter_service.send_message(
            message=message,
            history=history,
            tools=tools_schema,
            tool_callables=TOOL_CALLABLES,
        )

        # Extract text — response is an OpenRouterResponse wrapper
        ai_text = ""
        if response.candidates and response.candidates[0].content:
            parts = response.candidates[0].content.parts
            text_parts = [p.text for p in parts if p.text]
            ai_text = "\n".join(text_parts) if text_parts else ""

        if not ai_text:
            ai_text = "I completed the operation."

        action_type = _detect_action(ai_text)
        needs_confirmation = False
        confirmation_type = None

        if "delete confirmation" in ai_text.lower() or (
            "confirm" in ai_text.lower() and "delet" in ai_text.lower()
        ):
            needs_confirmation = True
            confirmation_type = "delete"
            action_type = "delete_product"

        add_to_history(user_id, "user", message)
        add_to_history(user_id, "assistant", ai_text)

        logger.info("OpenRouter fallback succeeded.")
        return {
            "message": ai_text,
            "action": action_type,
            "success": True,
            "data": None,
            "needs_confirmation": needs_confirmation,
            "confirmation_type": confirmation_type,
        }

    except Exception as e:
        logger.error(f"OpenRouter fallback failed: {e}")
        return None


def process_message(message: str, db: Session, user_id: int) -> dict:
    """
    Process a user message through the AI agent.

    Uses the Chat API which handles the function-call loop internally.
    We register our inventory tools as Python callables so the SDK's
    AFC can invoke them directly, and we get back the final
    natural-language response.
    """
    try:
        # ── Handle confirmation/cancel responses ─────────────────
        stripped = message.strip().lower()
        if stripped in ("yes", "confirm", "delete it", "do it", "proceed", "ok", "okay"):
            history = get_conversation_history(user_id)
            if history and history[-1]["role"] == "assistant":
                last_msg = history[-1]["content"]
                if "confirm" in last_msg.lower() and "delet" in last_msg.lower():
                    product_id = _extract_last_product_id(history)
                    if product_id is not None:
                        result = agent_tools.delete_product(db, product_id)
                        add_to_history(user_id, "user", message)
                        add_to_history(user_id, "assistant", result["message"])
                        return {
                            "message": result["message"],
                            "action": "delete_product",
                            "success": result["success"],
                            "data": None,
                            "needs_confirmation": False,
                        }

        if stripped in ("no", "cancel", "don't delete", "nope", "nevermind", "never mind"):
            add_to_history(user_id, "user", message)
            cancel_msg = "Understood. No changes were made."
            add_to_history(user_id, "assistant", cancel_msg)
            return {
                "message": cancel_msg,
                "action": "cancel",
                "success": True,
                "data": None,
                "needs_confirmation": False,
            }

        # ── Build tools + callables for AFC ─────────────────────
        history = get_conversation_history(user_id)

        # Pass the actual Python callables as tools so the SDK's
        # Automatic Function Calling can invoke them when Gemini
        # requests a tool call.
        function_list = list(TOOL_CALLABLES.values())

        client = _get_client()

        # Create a chat session with history
        chat = client.chats.create(
            model=settings.GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=function_list,
                temperature=0.3,
            ),
            history=[
                types.Content(
                    role="user" if m["role"] == "user" else "model",
                    parts=[types.Part(text=m["content"])],
                )
                for m in history
            ],
        )

        # Send message — Chat API handles tool-call loop via AFC
        response = chat.send_message(message)

        # Extract text from response
        ai_text = ""
        if response.candidates and response.candidates[0].content:
            parts = response.candidates[0].content.parts
            text_parts = [p.text for p in parts if p.text]
            ai_text = "\n".join(text_parts) if text_parts else ""

        if not ai_text:
            ai_text = "I completed the operation."

        # Determine action and data from the response
        action_type = _detect_action(ai_text)
        needs_confirmation = False
        confirmation_type = None
        tool_data = None

        # Check if the response contains a delete confirmation prompt
        if "delete confirmation" in ai_text.lower() or ("confirm" in ai_text.lower() and "delet" in ai_text.lower()):
            needs_confirmation = True
            confirmation_type = "delete"
            action_type = "delete_product"

        add_to_history(user_id, "user", message)
        add_to_history(user_id, "assistant", ai_text)

        return {
            "message": ai_text,
            "action": action_type,
            "success": True,
            "data": tool_data,
            "needs_confirmation": needs_confirmation,
            "confirmation_type": confirmation_type,
        }

    except ClientError as e:
        # ── Gemini API client error — check for quota exhaustion ────
        if _is_quota_exceeded(e):
            logger.warning("Gemini API quota exceeded — trying OpenRouter fallback.")
            # Attempt fallback to OpenRouter / Nemotron 3
            fallback_result = _try_openrouter_fallback(
                message=message, user_id=user_id,
            )
            if fallback_result is not None:
                return fallback_result
            # OpenRouter also failed or not configured
            retry = _extract_retry_delay(e)
            raise GeminiQuotaExceeded(
                message="The AI service quota has been reached. Please try again later.",
                retry_after_seconds=retry,
            ) from e
        # Other Gemini client errors (bad request, auth, server, etc.)
        logger.error(f"Gemini client error: {e}")
        error_msg = "The AI service is temporarily unavailable. Please try again."
        add_to_history(user_id, "user", message)
        add_to_history(user_id, "assistant", error_msg)
        return {
            "message": error_msg,
            "action": "error",
            "success": False,
            "data": None,
            "needs_confirmation": False,
        }

    except Exception as e:
        logger.error(f"Agent processing error: {e}", exc_info=True)
        error_msg = "I encountered an error processing your request. Please try again."
        add_to_history(user_id, "user", message)
        add_to_history(user_id, "assistant", error_msg)
        return {
            "message": error_msg,
            "action": "error",
            "success": False,
            "data": None,
            "needs_confirmation": False,
        }
