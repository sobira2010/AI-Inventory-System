from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.product import Product
from app.models.stock_history import StockHistory
from app.schemas.stock import StockAdjustRequest, StockHistoryResponse, StockHistoryListResponse
from app.dependencies import get_current_user, require_staff_or_admin
from app.models.user import User

router = APIRouter(prefix="/api/stock", tags=["Stock Management"])


@router.post("/adjust", response_model=StockHistoryResponse, status_code=status.HTTP_201_CREATED)
def adjust_stock(
    request: StockAdjustRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_admin),
):
    """Adjust stock for a product. Positive values add stock, negative values remove stock."""
    product = db.query(Product).filter(Product.id == request.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    new_quantity = product.quantity + request.quantity_change
    if new_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Current: {product.quantity}, requested change: {request.quantity_change}",
        )

    # Create stock history record
    stock_entry = StockHistory(
        product_id=product.id,
        user_id=current_user.id,
        quantity_change=request.quantity_change,
        previous_quantity=product.quantity,
        new_quantity=new_quantity,
        reason=request.reason,
        notes=request.notes,
    )

    # Update product quantity
    product.quantity = new_quantity

    db.add(stock_entry)
    db.commit()
    db.refresh(stock_entry)

    return StockHistoryResponse(
        id=stock_entry.id,
        product_id=stock_entry.product_id,
        user_id=stock_entry.user_id,
        quantity_change=stock_entry.quantity_change,
        previous_quantity=stock_entry.previous_quantity,
        new_quantity=stock_entry.new_quantity,
        reason=stock_entry.reason,
        notes=stock_entry.notes,
        created_at=stock_entry.created_at,
        product_name=product.name,
        user_name=current_user.name,
    )


@router.get("/history", response_model=StockHistoryListResponse)
def get_stock_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_admin),
):
    """Get stock change history with pagination."""
    query = db.query(StockHistory)

    if product_id:
        query = query.filter(StockHistory.product_id == product_id)

    query = query.order_by(StockHistory.created_at.desc())

    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    history = query.offset((page - 1) * page_size).limit(page_size).all()

    # Enrich with product and user names
    enriched = []
    for entry in history:
        product = db.query(Product).filter(Product.id == entry.product_id).first()
        user = db.query(User).filter(User.id == entry.user_id).first()
        enriched.append(
            StockHistoryResponse(
                id=entry.id,
                product_id=entry.product_id,
                user_id=entry.user_id,
                quantity_change=entry.quantity_change,
                previous_quantity=entry.previous_quantity,
                new_quantity=entry.new_quantity,
                reason=entry.reason,
                notes=entry.notes,
                created_at=entry.created_at,
                product_name=product.name if product else "Unknown",
                user_name=user.name if user else "Unknown",
            )
        )

    return StockHistoryListResponse(
        history=enriched,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
