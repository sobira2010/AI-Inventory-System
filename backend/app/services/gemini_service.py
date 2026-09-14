"""
Gemini LLM Service for the Inventory AI Agent.

Uses the google-genai SDK with the Chat API for function calling.
The Chat API correctly handles tool invocation loops internally,
avoiding the generate_content AFC attribute errors.

All Gemini API calls go through this service — the frontend never
has direct access.
"""

import json
import logging
from typing import Optional
from google import genai
from google.genai import types
from app.config import settings

logger = logging.getLogger(__name__)

# ── Lazy-initialized Gemini client ──────────────────────────────────

_client = None


def _get_client():
    """Get or create the Gemini client. Initialized on first use."""
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured. "
                "Please add it to your .env file."
            )
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


# ── Tool schema ─────────────────────────────────────────────────────

def build_tools_schema() -> list[types.Tool]:
    """Build tool declarations for Gemini function calling.

    Returns a list of types.Tool objects.  Each Tool wraps one or
    more FunctionDeclaration entries.  The google-genai SDK requires
    this exact structure — bare FunctionDeclaration lists cause an
    AttributeError at call time.
    """
    declarations = [
        types.FunctionDeclaration(
            name="list_products",
            description="List all products in the inventory. Returns a list of products with their details.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        ),
        types.FunctionDeclaration(
            name="get_product",
            description="Get detailed information about a specific product by its ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "product_id": types.Schema(
                        type=types.Type.INTEGER,
                        description="The ID of the product to retrieve",
                    ),
                },
                required=["product_id"],
            ),
        ),
        types.FunctionDeclaration(
            name="search_products",
            description="Search products by name, category, or supplier. Returns matching products.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "search_term": types.Schema(
                        type=types.Type.STRING,
                        description="The search term to match against product name, category, or supplier",
                    ),
                },
                required=["search_term"],
            ),
        ),
        types.FunctionDeclaration(
            name="create_product",
            description="Create a new product in the inventory. Requires name, category, price, quantity, and minimum_stock.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "name": types.Schema(
                        type=types.Type.STRING,
                        description="Product name (required)",
                    ),
                    "category": types.Schema(
                        type=types.Type.STRING,
                        description="Product category, e.g. Electronics, Furniture (required)",
                    ),
                    "description": types.Schema(
                        type=types.Type.STRING,
                        description="Optional product description",
                    ),
                    "price": types.Schema(
                        type=types.Type.NUMBER,
                        description="Product price (required, must be >= 0)",
                    ),
                    "quantity": types.Schema(
                        type=types.Type.INTEGER,
                        description="Initial stock quantity (required, must be >= 0)",
                    ),
                    "minimum_stock": types.Schema(
                        type=types.Type.INTEGER,
                        description="Minimum stock threshold before restocking is needed (required, must be >= 0)",
                    ),
                    "supplier": types.Schema(
                        type=types.Type.STRING,
                        description="Optional supplier name",
                    ),
                },
                required=["name", "category", "price", "quantity", "minimum_stock"],
            ),
        ),
        types.FunctionDeclaration(
            name="update_product",
            description="Update an existing product's fields. Provide product_id and the fields to update.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "product_id": types.Schema(
                        type=types.Type.INTEGER,
                        description="The ID of the product to update (required)",
                    ),
                    "name": types.Schema(
                        type=types.Type.STRING,
                        description="New product name",
                    ),
                    "category": types.Schema(
                        type=types.Type.STRING,
                        description="New category",
                    ),
                    "description": types.Schema(
                        type=types.Type.STRING,
                        description="New description",
                    ),
                    "price": types.Schema(
                        type=types.Type.NUMBER,
                        description="New price (must be >= 0)",
                    ),
                    "quantity": types.Schema(
                        type=types.Type.INTEGER,
                        description="New quantity (must be >= 0)",
                    ),
                    "minimum_stock": types.Schema(
                        type=types.Type.INTEGER,
                        description="New minimum stock threshold (must be >= 0)",
                    ),
                    "supplier": types.Schema(
                        type=types.Type.STRING,
                        description="New supplier name",
                    ),
                },
                required=["product_id"],
            ),
        ),
        types.FunctionDeclaration(
            name="delete_product",
            description="Delete a product from the inventory. This is destructive and requires confirmation.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "product_id": types.Schema(
                        type=types.Type.INTEGER,
                        description="The ID of the product to delete (required)",
                    ),
                    "confirm": types.Schema(
                        type=types.Type.BOOLEAN,
                        description="Set to true only after user explicitly confirms deletion",
                    ),
                },
                required=["product_id", "confirm"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_out_of_stock_products",
            description="Get all products that are currently out of stock (quantity = 0).",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        ),
        types.FunctionDeclaration(
            name="get_low_stock_products",
            description="Get all products where current stock is at or below the minimum stock threshold.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        ),
        types.FunctionDeclaration(
            name="get_restock_recommendations",
            description="Get restocking recommendations based on current stock, historical sales, and predicted demand.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        ),
        types.FunctionDeclaration(
            name="get_inventory_summary",
            description="Get a summary of the entire inventory including total products, total stock value, out-of-stock count, and low-stock count.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        ),
        types.FunctionDeclaration(
            name="get_restock_analysis",
            description=(
                "Combined restock analysis: merges inventory status with AI demand predictions. "
                "Returns a prioritised list of products needing restocking, each with: product_id, "
                "product_name, category, current_stock, minimum_stock, predicted_demand (or null if "
                "unavailable), recommended_reorder, risk_level (HIGH/MEDIUM/LOW), status, and a plain-"
                "English reason. Also includes a priority_summary grouping products by risk level."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        ),
    ]

    return [types.Tool(function_declarations=declarations)]


# ── System prompt ───────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an Inventory Management AI Agent. You help users manage their inventory through natural language commands.

## YOUR CAPABILITIES
You can perform these inventory operations by calling the appropriate tools:
- List all products
- Search for products by name, category, or supplier
- Get details of a specific product by ID
- Create new products with name, category, price, quantity, minimum stock, and optional supplier/description
- Update existing product fields
- Delete products (ALWAYS requires explicit user confirmation)
- Check out-of-stock products
- Check low-stock products
- Get restocking recommendations
- Get inventory summary
- Get combined restock analysis (inventory status + AI demand predictions)

## RESTOCK ANALYSIS TOOL
The `get_restock_analysis` tool provides a combined view of inventory status and AI demand predictions. Use it when the user asks about restocking, stock needs, or inventory health.

When you receive results from `get_restock_analysis`, format the response as follows:

### Header
Start with: `### 📦 Inventory Restock Analysis`

### Per-Product Format (use compact card layout)
For each product, display as a compact card:

📦 **Product Name** (ID: X)
- Current Stock: N
- Minimum Stock: N
- Predicted Demand: N (or "N/A" if unavailable)
- Recommended Reorder: N
- Risk: 🔴 HIGH / 🟠 MEDIUM / 🟢 LOW
- Reason: <plain-English reason from the data>

### Priority Summary
After all product cards, add:

### 🚨 Priority Summary
🔴 **HIGH PRIORITY**
- Product #X — Product Name

🟠 **MEDIUM PRIORITY**
- Product #X — Product Name

Then add: "Recommended action: Restock the high-priority products first, followed by the medium-risk products."

### Empty Case
If no products need restocking, simply say:
"✅ No products currently require restocking. All inventory levels are adequate."
Do NOT show an empty table.

### Key Formatting Rules
- NEVER invent product IDs, stock quantities, prices, predicted demand, reorder quantities, or risk levels.
- ALWAYS use the data returned by the tool. The tool data is the source of truth.
- When predicted_demand is null, show "N/A" and note that demand prediction is unavailable.
- When risk is HIGH, use 🔴. When MEDIUM, use 🟠. When LOW, use 🟢.
- Keep each product card concise — avoid huge markdown tables that overflow the chat panel.
- Include the plain-English reason from the tool data for every product.

## RULES
1. **NEVER invent product information.** If the user says "Add a laptop" without price/quantity, ask them for the missing details.
2. **NEVER delete without confirmation.** When the user asks to delete, first show the product details and ask "Are you sure you want to delete this product?" Pass confirm=false to the delete_product tool.
3. **Confirm before executing create/update** if details seem ambiguous. If all details are clear, proceed directly.
4. **If multiple products match a search**, show the matching products with IDs and ask the user which one they mean.
5. **Be concise.** Give clear, structured responses. Use bullet points or numbered lists.
6. **Handle errors gracefully.** If a product isn't found, say so clearly. If an operation fails, report the real error.
7. **For partial information:** When updating, only update the fields the user mentioned. Don't clear other fields.
8. **Use currency formatting** with ₹ symbol for prices in India, or $ for general use.
9. **When showing product lists**, include: ID, Name, Category, Price, Quantity, and Stock Status.
10. **For confirmation flows**, clearly state what will happen and provide a yes/no mechanism.

## RESTOCKING QUERIES
When the user asks about restocking (e.g., "Which products need restocking?", "What should I restock first?", "Give me a restock analysis"), ALWAYS call the `get_restock_analysis` tool and use the results to format a clear, prioritised response using the format described above.

When the user asks WHY a product needs restocking (e.g., "Why does Product 1 need 72 units?"), use the `get_restock_analysis` tool data and explain the calculation using the actual numbers from the tool response. Do not invent calculations.

## RESPONSE STYLE
- Greet the user briefly when they start a conversation
- Format product lists in a readable way
- Use tables or structured lists for multiple products
- Always include product IDs for reference
- For creation/update confirmations, show the before/after if applicable
"""


# ── Public API ──────────────────────────────────────────────────────

def send_message(
    message: str,
    history: list[dict],
    tools: list,
) -> types.GenerateContentResponse:
    """
    Send a message to Gemini via the Chat API with function calling.

    The Chat API handles the tool-call loop internally, so we never
    need to manually iterate over function_call / function_response
    parts — that is exactly the class of code that caused the
    ``'FunctionDeclaration' object has no attribute 'function_declarations'``
    AttributeError when using ``Models.generate_content``.

    Args:
        message: The user's message
        history: Previous conversation messages
        tools:   List of types.Tool objects

    Returns:
        Gemini GenerateContentResponse
    """
    try:
        client = _get_client()

        chat = client.chats.create(
            model=settings.GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=tools,
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

        response = chat.send_message(message)
        return response

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise


def send_function_response(
    history: list[dict],
    function_calls: list,
    function_results: list[dict],
    tools: list,
) -> types.GenerateContentResponse:
    """
    Send function call results back to Gemini for processing.

    NOTE: With the Chat API, this function is mostly a fallback.
    The Chat.send_message call in ``send_message`` already handles
    the function-call → function-response → final-text loop
    automatically via AFC.  This method exists only for backward
    compatibility and is no longer called in the normal flow.
    """
    return send_message(
        message=function_results[-1]["result"].get("message", "Done.") if function_results else "Done.",
        history=history,
        tools=tools,
    )
