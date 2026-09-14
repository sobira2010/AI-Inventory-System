from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database import get_db
from app.models.product import Product
from app.models.stock_history import StockHistory
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse
from app.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    stock_status: Optional[str] = None,
    sort_by: Optional[str] = "name",
    sort_order: Optional[str] = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all products with pagination, search, and filters."""
    query = db.query(Product)

    # Search filter
    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%")
            | Product.category.ilike(f"%{search}%")
            | Product.supplier.ilike(f"%{search}%")
        )

    # Category filter
    if category:
        query = query.filter(Product.category == category)

    # Stock status filter
    if stock_status == "out_of_stock":
        query = query.filter(Product.quantity == 0)
    elif stock_status == "low_stock":
        query = query.filter(Product.quantity > 0, Product.quantity <= Product.minimum_stock)
    elif stock_status == "in_stock":
        query = query.filter(Product.quantity > Product.minimum_stock)

    # Sorting
    sort_column = getattr(Product, sort_by, Product.name)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Count total
    total = query.count()

    # Pagination
    total_pages = (total + page_size - 1) // page_size
    products = query.offset((page - 1) * page_size).limit(page_size).all()

    return ProductListResponse(
        products=products,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new product (Admin only)."""
    product = Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a product (Admin only)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    update_data = product_data.model_dump(exclude_unset=True)

    # If quantity is changing, record stock history
    if "quantity" in update_data and update_data["quantity"] != product.quantity:
        quantity_change = update_data["quantity"] - product.quantity
        stock_entry = StockHistory(
            product_id=product.id,
            user_id=current_user.id,
            quantity_change=quantity_change,
            previous_quantity=product.quantity,
            new_quantity=update_data["quantity"],
            reason="Product update",
            notes=f"Stock updated via product edit by {current_user.name}",
        )
        db.add(stock_entry)

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a product (Admin only)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    db.delete(product)
    db.commit()
    return None
