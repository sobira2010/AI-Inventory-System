from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.product import Product
from app.models.sale import Sale
from app.models.stock_history import StockHistory
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard statistics and chart data."""
    # Basic stats
    total_products = db.query(func.count(Product.id)).scalar() or 0
    total_stock = db.query(func.sum(Product.quantity)).scalar() or 0
    total_sales = db.query(func.count(Sale.id)).scalar() or 0
    total_revenue = db.query(func.sum(Sale.total_price)).scalar() or 0.0

    # Low stock products (quantity > 0 but <= minimum_stock)
    low_stock_products = db.query(Product).filter(
        Product.quantity > 0,
        Product.quantity <= Product.minimum_stock,
    ).all()

    # Out of stock products
    out_of_stock_products = db.query(Product).filter(Product.quantity == 0).all()

    # Top selling products (by quantity sold)
    top_selling = (
        db.query(
            Product.name,
            func.sum(Sale.quantity).label("total_sold"),
        )
        .join(Sale, Product.id == Sale.product_id)
        .group_by(Product.name)
        .order_by(func.sum(Sale.quantity).desc())
        .limit(5)
        .all()
    )

    # Stock by category
    stock_by_category = (
        db.query(
            Product.category,
            func.sum(Product.quantity).label("total_stock"),
            func.count(Product.id).label("product_count"),
        )
        .group_by(Product.category)
        .all()
    )

    # Sales over time (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    sales_over_time = (
        db.query(
            func.date(Sale.sale_date).label("date"),
            func.sum(Sale.total_price).label("revenue"),
            func.count(Sale.id).label("sales_count"),
        )
        .filter(Sale.sale_date >= thirty_days_ago)
        .group_by(func.date(Sale.sale_date))
        .order_by(func.date(Sale.sale_date))
        .all()
    )

    return {
        "total_products": total_products,
        "total_stock": total_stock,
        "total_sales": total_sales,
        "total_revenue": round(total_revenue, 2),
        "low_stock_count": len(low_stock_products),
        "out_of_stock_count": len(out_of_stock_products),
        "low_stock_products": [
            {"id": p.id, "name": p.name, "quantity": p.quantity, "minimum_stock": p.minimum_stock}
            for p in low_stock_products
        ],
        "out_of_stock_products": [
            {"id": p.id, "name": p.name, "category": p.category}
            for p in out_of_stock_products
        ],
        "top_selling_products": [
            {"name": name, "total_sold": total_sold}
            for name, total_sold in top_selling
        ],
        "stock_by_category": [
            {
                "category": category,
                "total_stock": total_stock,
                "product_count": product_count,
            }
            for category, total_stock, product_count in stock_by_category
        ],
        "sales_over_time": [
            {
                "date": str(date),
                "revenue": round(revenue, 2),
                "sales_count": sales_count,
            }
            for date, revenue, sales_count in sales_over_time
        ],
    }
