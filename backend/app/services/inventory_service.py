from sqlalchemy.orm import Session
from app.models.product import Product


def get_product_status(product: Product) -> str:
    """Determine the stock status of a product."""
    if product.quantity == 0:
        return "OUT OF STOCK"
    elif product.quantity <= product.minimum_stock:
        return "LOW STOCK"
    else:
        return "IN STOCK"


def calculate_stock_value(db: Session) -> float:
    """Calculate total inventory value."""
    products = db.query(Product).all()
    return sum(p.price * p.quantity for p in products)
