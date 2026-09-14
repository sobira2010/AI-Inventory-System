from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.models.sale import Sale
from app.models.stock_history import StockHistory
from app.schemas.sale import SaleCreate, SaleResponse, SaleListResponse
from app.dependencies import require_staff_or_admin
from app.models.user import User

router = APIRouter(prefix="/api/sales", tags=["Sales"])


@router.post("", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    sale_data: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_admin),
):
    """Create a new sale. Validates stock, calculates total, and updates inventory in a transaction."""
    # Validate product exists
    product = db.query(Product).filter(Product.id == sale_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Validate sufficient stock
    if product.quantity < sale_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available: {product.quantity}, requested: {sale_data.quantity}",
        )

    # Calculate total price
    total_price = product.price * sale_data.quantity

    # Create sale record
    sale = Sale(
        product_id=product.id,
        quantity=sale_data.quantity,
        unit_price=product.price,
        total_price=total_price,
        sold_by=current_user.id,
    )

    # Update product stock
    previous_quantity = product.quantity
    product.quantity -= sale_data.quantity

    # Create stock history record
    stock_entry = StockHistory(
        product_id=product.id,
        user_id=current_user.id,
        quantity_change=-sale_data.quantity,
        previous_quantity=previous_quantity,
        new_quantity=product.quantity,
        reason="Sale",
        notes=f"Sale of {sale_data.quantity} units",
    )

    db.add(sale)
    db.add(stock_entry)
    db.commit()
    db.refresh(sale)

    return SaleResponse(
        id=sale.id,
        product_id=sale.product_id,
        quantity=sale.quantity,
        unit_price=sale.unit_price,
        total_price=sale.total_price,
        sold_by=sale.sold_by,
        sale_date=sale.sale_date,
        created_at=sale.created_at,
        product_name=product.name,
        seller_name=current_user.name,
    )


@router.get("", response_model=SaleListResponse)
def list_sales(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_admin),
):
    """List all sales with pagination."""
    query = db.query(Sale).order_by(Sale.created_at.desc())
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    sales = query.offset((page - 1) * page_size).limit(page_size).all()

    enriched = []
    for sale in sales:
        product = db.query(Product).filter(Product.id == sale.product_id).first()
        seller = db.query(User).filter(User.id == sale.sold_by).first()
        enriched.append(
            SaleResponse(
                id=sale.id,
                product_id=sale.product_id,
                quantity=sale.quantity,
                unit_price=sale.unit_price,
                total_price=sale.total_price,
                sold_by=sale.sold_by,
                sale_date=sale.sale_date,
                created_at=sale.created_at,
                product_name=product.name if product else "Unknown",
                seller_name=seller.name if seller else "Unknown",
            )
        )

    return SaleListResponse(
        sales=enriched,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_admin),
):
    """Get a single sale by ID."""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found",
        )

    product = db.query(Product).filter(Product.id == sale.product_id).first()
    seller = db.query(User).filter(User.id == sale.sold_by).first()

    return SaleResponse(
        id=sale.id,
        product_id=sale.product_id,
        quantity=sale.quantity,
        unit_price=sale.unit_price,
        total_price=sale.total_price,
        sold_by=sale.sold_by,
        sale_date=sale.sale_date,
        created_at=sale.created_at,
        product_name=product.name if product else "Unknown",
        seller_name=seller.name if seller else "Unknown",
    )
