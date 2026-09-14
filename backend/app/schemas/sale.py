from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SaleCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class SaleResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    total_price: float
    sold_by: int
    sale_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    product_name: Optional[str] = None
    seller_name: Optional[str] = None

    class Config:
        from_attributes = True


class SaleListResponse(BaseModel):
    sales: list[SaleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
