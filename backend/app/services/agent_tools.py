"""
Controlled Inventory Tools for the AI Agent.

These tools wrap existing database operations and services.
They are the ONLY way the AI agent interacts with the database.
No direct SQL or model access is allowed from Gemini.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.product import Product
from app.models.sale import Sale
from app.models.stock_history import StockHistory
from app.services.inventory_service import get_product_status
from app.services.ai_service import predict_demand, get_reorder_recommendations

logger = logging.getLogger(__name__)


def list_products(db: Session) -> dict:
    """List all products in the inventory."""
    try:
        products = db.query(Product).order_by(Product.name.asc()).all()
        result = []
        for p in products:
            result.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "description": p.description,
                "price": p.price,
                "quantity": p.quantity,
                "minimum_stock": p.minimum_stock,
                "supplier": p.supplier,
                "status": get_product_status(p),
            })
        return {
            "success": True,
            "products": result,
            "total": len(result),
            "message": f"Found {len(result)} products in inventory.",
        }
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        return {"success": False, "message": f"Error listing products: {str(e)}", "products": []}


def get_product(db: Session, product_id: int) -> dict:
    """Get a single product by ID."""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "message": f"Product with ID {product_id} not found.", "product": None}
        return {
            "success": True,
            "product": {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "price": product.price,
                "quantity": product.quantity,
                "minimum_stock": product.minimum_stock,
                "supplier": product.supplier,
                "status": get_product_status(product),
                "created_at": str(product.created_at) if product.created_at else None,
                "updated_at": str(product.updated_at) if product.updated_at else None,
            },
            "message": f"Found product: {product.name} (ID: {product.id})",
        }
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        return {"success": False, "message": f"Error retrieving product: {str(e)}", "product": None}


def search_products(db: Session, search_term: str) -> dict:
    """Search products by name, category, or supplier."""
    try:
        products = db.query(Product).filter(
            or_(
                Product.name.ilike(f"%{search_term}%"),
                Product.category.ilike(f"%{search_term}%"),
                Product.supplier.ilike(f"%{search_term}%"),
            )
        ).order_by(Product.name.asc()).all()

        result = []
        for p in products:
            result.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "quantity": p.quantity,
                "minimum_stock": p.minimum_stock,
                "supplier": p.supplier,
                "status": get_product_status(p),
            })

        if not result:
            return {
                "success": True,
                "products": [],
                "total": 0,
                "message": f"No products found matching '{search_term}'.",
            }

        return {
            "success": True,
            "products": result,
            "total": len(result),
            "message": f"Found {len(result)} products matching '{search_term}'.",
        }
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return {"success": False, "message": f"Error searching products: {str(e)}", "products": []}


def create_product(
    db: Session,
    name: str,
    category: str,
    price: float,
    quantity: int,
    minimum_stock: int,
    description: Optional[str] = None,
    supplier: Optional[str] = None,
) -> dict:
    """Create a new product."""
    try:
        # Validate inputs
        if not name or not name.strip():
            return {"success": False, "message": "Product name is required.", "product": None}
        if not category or not category.strip():
            return {"success": False, "message": "Product category is required.", "product": None}
        if price < 0:
            return {"success": False, "message": "Price cannot be negative.", "product": None}
        if quantity < 0:
            return {"success": False, "message": "Quantity cannot be negative.", "product": None}
        if minimum_stock < 0:
            return {"success": False, "message": "Minimum stock cannot be negative.", "product": None}

        product = Product(
            name=name.strip(),
            category=category.strip(),
            description=description.strip() if description else None,
            price=round(float(price), 2),
            quantity=int(quantity),
            minimum_stock=int(minimum_stock),
            supplier=supplier.strip() if supplier else None,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return {
            "success": True,
            "product": {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "price": product.price,
                "quantity": product.quantity,
                "minimum_stock": product.minimum_stock,
                "supplier": product.supplier,
                "status": get_product_status(product),
            },
            "message": f"Product '{product.name}' created successfully with ID {product.id}.",
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating product: {e}")
        return {"success": False, "message": f"Error creating product: {str(e)}", "product": None}


def update_product(db: Session, product_id: int, **fields) -> dict:
    """Update an existing product's fields."""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "message": f"Product with ID {product_id} not found.", "product": None}

        # Validate fields
        if "price" in fields and fields["price"] is not None:
            if fields["price"] < 0:
                return {"success": False, "message": "Price cannot be negative.", "product": None}
            fields["price"] = round(float(fields["price"]), 2)

        if "quantity" in fields and fields["quantity"] is not None:
            if fields["quantity"] < 0:
                return {"success": False, "message": "Quantity cannot be negative.", "product": None}
            fields["quantity"] = int(fields["quantity"])

        if "minimum_stock" in fields and fields["minimum_stock"] is not None:
            if fields["minimum_stock"] < 0:
                return {"success": False, "message": "Minimum stock cannot be negative.", "product": None}
            fields["minimum_stock"] = int(fields["minimum_stock"])

        if "name" in fields and fields["name"]:
            fields["name"] = fields["name"].strip()
        if "category" in fields and fields["category"]:
            fields["category"] = fields["category"].strip()
        if "supplier" in fields and fields["supplier"]:
            fields["supplier"] = fields["supplier"].strip()

        # Track changes for response
        changes = {}
        for field, value in fields.items():
            if value is not None and hasattr(product, field):
                old_value = getattr(product, field)
                if old_value != value:
                    changes[field] = {"old": old_value, "new": value}
                    setattr(product, field, value)

        if not changes:
            return {
                "success": True,
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "category": product.category,
                    "price": product.price,
                    "quantity": product.quantity,
                    "minimum_stock": product.minimum_stock,
                    "supplier": product.supplier,
                    "status": get_product_status(product),
                },
                "message": f"No changes detected for product '{product.name}'.",
                "changes": {},
            }

        db.commit()
        db.refresh(product)

        return {
            "success": True,
            "product": {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "price": product.price,
                "quantity": product.quantity,
                "minimum_stock": product.minimum_stock,
                "supplier": product.supplier,
                "status": get_product_status(product),
            },
            "message": f"Product '{product.name}' updated successfully.",
            "changes": changes,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating product {product_id}: {e}")
        return {"success": False, "message": f"Error updating product: {str(e)}", "product": None}


def delete_product(db: Session, product_id: int) -> dict:
    """Delete a product from the inventory. This is destructive."""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "message": f"Product with ID {product_id} not found.", "product": None}

        product_name = product.name
        db.delete(product)
        db.commit()

        return {
            "success": True,
            "message": f"Product '{product_name}' (ID: {product_id}) has been deleted successfully.",
            "product": None,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting product {product_id}: {e}")
        return {"success": False, "message": f"Error deleting product: {str(e)}", "product": None}


def get_out_of_stock_products(db: Session) -> dict:
    """Get all products that are out of stock (quantity = 0)."""
    try:
        products = db.query(Product).filter(Product.quantity == 0).order_by(Product.name.asc()).all()
        result = []
        for p in products:
            result.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "minimum_stock": p.minimum_stock,
                "supplier": p.supplier,
            })

        return {
            "success": True,
            "products": result,
            "total": len(result),
            "message": f"Found {len(result)} out-of-stock products." if result else "No products are currently out of stock.",
        }
    except Exception as e:
        logger.error(f"Error getting out-of-stock products: {e}")
        return {"success": False, "message": f"Error: {str(e)}", "products": []}


def get_low_stock_products(db: Session) -> dict:
    """Get products where current stock is at or below minimum stock threshold."""
    try:
        products = db.query(Product).filter(
            Product.quantity > 0,
            Product.quantity <= Product.minimum_stock,
        ).order_by(Product.name.asc()).all()

        result = []
        for p in products:
            result.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "quantity": p.quantity,
                "minimum_stock": p.minimum_stock,
                "supplier": p.supplier,
                "deficit": p.minimum_stock - p.quantity,
            })

        return {
            "success": True,
            "products": result,
            "total": len(result),
            "message": f"Found {len(result)} low-stock products." if result else "No products are currently low on stock.",
        }
    except Exception as e:
        logger.error(f"Error getting low-stock products: {e}")
        return {"success": False, "message": f"Error: {str(e)}", "products": []}


def get_restock_recommendations(db: Session) -> dict:
    """Get restocking recommendations using existing AI prediction logic."""
    try:
        recommendations = get_reorder_recommendations(db)

        # Filter to only HIGH and MEDIUM risk items
        urgent = [r for r in recommendations if r["risk_level"] in ("HIGH", "MEDIUM")]

        if not urgent:
            return {
                "success": True,
                "recommendations": [],
                "total": 0,
                "all_count": len(recommendations),
                "message": "All products have adequate stock levels. No urgent restocking needed.",
            }

        return {
            "success": True,
            "recommendations": urgent,
            "total": len(urgent),
            "all_count": len(recommendations),
            "message": f"Found {len(urgent)} products that may need restocking.",
        }
    except Exception as e:
        logger.error(f"Error getting restock recommendations: {e}")
        return {"success": False, "message": f"Error: {str(e)}", "recommendations": []}


def get_inventory_summary(db: Session) -> dict:
    """Get a summary of the entire inventory."""
    try:
        from sqlalchemy import func

        total_products = db.query(func.count(Product.id)).scalar() or 0
        total_stock = db.query(func.sum(Product.quantity)).scalar() or 0
        total_value = db.query(func.sum(Product.price * Product.quantity)).scalar() or 0.0
        out_of_stock_count = db.query(func.count(Product.id)).filter(Product.quantity == 0).scalar() or 0
        low_stock_count = db.query(func.count(Product.id)).filter(
            Product.quantity > 0,
            Product.quantity <= Product.minimum_stock,
        ).scalar() or 0
        in_stock_count = total_products - out_of_stock_count - low_stock_count

        # Stock by category
        categories = db.query(
            Product.category,
            func.count(Product.id),
            func.sum(Product.quantity),
        ).group_by(Product.category).all()

        category_summary = []
        for cat, count, stock in categories:
            category_summary.append({
                "category": cat,
                "product_count": count,
                "total_stock": stock,
            })

        return {
            "success": True,
            "summary": {
                "total_products": total_products,
                "total_stock": total_stock,
                "total_value": round(float(total_value), 2),
                "out_of_stock_count": out_of_stock_count,
                "low_stock_count": low_stock_count,
                "in_stock_count": in_stock_count,
                "categories": category_summary,
            },
            "message": f"Inventory: {total_products} products, {total_stock} total units, worth ₹{total_value:,.2f}.",
        }
    except Exception as e:
        logger.error(f"Error getting inventory summary: {e}")
        return {"success": False, "message": f"Error: {str(e)}", "summary": {}}


def get_restock_analysis(db: Session) -> dict:
    """Combined restock analysis: merges inventory status with AI demand predictions.

    Returns a unified, prioritised list of products that need restocking,
    each with inventory data, demand predictions (when available),
    recommended reorder quantities, risk levels, and plain-English reasons.
    """
    try:
        products = db.query(Product).all()

        # Get AI predictions (demand + reorder) — keyed by product_id for fast lookup
        try:
            demand_preds = {p["product_id"]: p for p in predict_demand(db)}
        except Exception as e:
            logger.warning(f"Demand prediction failed, continuing without it: {e}")
            demand_preds = {}

        try:
            reorder_recs = {r["product_id"]: r for r in get_reorder_recommendations(db)}
        except Exception as e:
            logger.warning(f"Reorder recommendations failed, continuing without them: {e}")
            reorder_recs = {}

        analysis_items: list[dict] = []

        for p in products:
            # Only include products that need attention
            needs_attention = (
                p.quantity == 0
                or p.quantity <= p.minimum_stock
                or p.id in reorder_recs
            )
            if not needs_attention:
                continue

            # Determine inventory status
            if p.quantity == 0:
                status = "OUT OF STOCK"
                base_risk = "HIGH"
                reason = (
                    f"Product '{p.name}' (ID: {p.id}) is currently out of stock "
                    f"and requires immediate restocking."
                )
            elif p.quantity <= p.minimum_stock:
                deficit = p.minimum_stock - p.quantity
                status = "LOW STOCK"
                base_risk = "HIGH"
                reason = (
                    f"Product '{p.name}' (ID: {p.id}) has {p.quantity} units, "
                    f"which is below the minimum threshold of {p.minimum_stock}. "
                    f"Deficit: {deficit} units."
                )
            else:
                status = "IN STOCK"
                base_risk = "LOW"
                reason = None

            # Merge AI prediction data
            demand_data = demand_preds.get(p.id, {})
            reorder_data = reorder_recs.get(p.id, {})

            predicted_demand = demand_data.get("predicted_demand")
            predicted_demand_available = (
                predicted_demand is not None and predicted_demand > 0
            )
            ai_risk = demand_data.get("risk_level")
            recommended_reorder = reorder_data.get("recommended_reorder", 0)

            # Final risk level — prefer the more severe of inventory vs AI risk
            risk_level = base_risk
            if ai_risk == "HIGH":
                risk_level = "HIGH"
            elif ai_risk == "MEDIUM" and risk_level != "HIGH":
                risk_level = "MEDIUM"

            # Build a richer reason incorporating demand data when available
            if predicted_demand_available:
                shortage = max(0, round(predicted_demand - p.quantity))
                reason = (
                    f"Product '{p.name}' (ID: {p.id}) currently has {p.quantity} units, "
                    f"while predicted demand over the next 30 days is "
                    f"{round(predicted_demand)} units. "
                    f"The system expects a potential shortage of {shortage} units. "
                    f"After applying safety-stock logic, the recommended reorder "
                    f"quantity is {round(recommended_reorder)} units."
                )
                if p.quantity <= p.minimum_stock:
                    risk_level = "HIGH"
                    status = "LOW STOCK"
                elif risk_level == "LOW":
                    risk_level = "MEDIUM"
                    status = "AT RISK"
            else:
                if p.quantity == 0:
                    reason = (
                        f"Product '{p.name}' (ID: {p.id}) is currently out of stock "
                        f"and requires immediate restocking. "
                        f"Demand prediction is currently unavailable for this product."
                    )
                elif p.quantity <= p.minimum_stock:
                    deficit = p.minimum_stock - p.quantity
                    reason = (
                        f"Product '{p.name}' (ID: {p.id}) has {p.quantity} units, "
                        f"which is below the minimum threshold of {p.minimum_stock}. "
                        f"Deficit: {deficit} units. "
                        f"Demand prediction is currently unavailable for this product."
                    )

            # Compute recommended_reorder for display
            if p.quantity == 0:
                display_reorder = f"{p.minimum_stock}+"
            elif p.quantity <= p.minimum_stock:
                deficit = p.minimum_stock - p.quantity
                display_reorder = f"{deficit}+"
            elif recommended_reorder > 0:
                display_reorder = str(round(recommended_reorder))
            else:
                display_reorder = "0"

            analysis_items.append({
                "product_id": p.id,
                "product_name": p.name,
                "category": p.category,
                "current_stock": p.quantity,
                "minimum_stock": p.minimum_stock,
                "predicted_demand": round(predicted_demand) if predicted_demand_available else None,
                "predicted_demand_available": predicted_demand_available,
                "recommended_reorder": display_reorder,
                "risk_level": risk_level,
                "status": status,
                "reason": reason,
            })

        # Sort: HIGH first, then MEDIUM, then LOW; within each tier sort by deficit desc
        risk_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        analysis_items.sort(
            key=lambda x: (
                risk_order.get(x["risk_level"], 9),
                -(x["minimum_stock"] - x["current_stock"]),
            )
        )

        # Build priority summary
        high_priority = [
            {"id": i["product_id"], "name": i["product_name"]}
            for i in analysis_items if i["risk_level"] == "HIGH"
        ]
        medium_priority = [
            {"id": i["product_id"], "name": i["product_name"]}
            for i in analysis_items if i["risk_level"] == "MEDIUM"
        ]
        low_priority = [
            {"id": i["product_id"], "name": i["product_name"]}
            for i in analysis_items if i["risk_level"] == "LOW"
        ]

        if not analysis_items:
            return {
                "success": True,
                "products_need_restocking": False,
                "analysis": [],
                "total": 0,
                "priority_summary": {
                    "high": [],
                    "medium": [],
                    "low": [],
                },
                "message": "✅ No products currently require restocking. All inventory levels are adequate.",
            }

        return {
            "success": True,
            "products_need_restocking": True,
            "analysis": analysis_items,
            "total": len(analysis_items),
            "priority_summary": {
                "high": high_priority,
                "medium": medium_priority,
                "low": low_priority,
            },
            "message": f"Found {len(analysis_items)} products that need restocking attention.",
        }
    except Exception as e:
        logger.error(f"Error getting restock analysis: {e}")
        return {
            "success": False,
            "products_need_restocking": False,
            "analysis": [],
            "total": 0,
            "priority_summary": {"high": [], "medium": [], "low": []},
            "message": f"Error generating restock analysis: {str(e)}",
        }
