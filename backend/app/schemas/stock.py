from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StockAdjustRequest(BaseModel):
    product_id: int
    quantity_change: int  # Positive to add, negative to remove
    reason: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None


class StockHistoryResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    quantity_change: int
    previous_quantity: int
    new_quantity: int
    reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    product_name: Optional[str] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class StockHistoryListResponse(BaseModel):
    history: list[StockHistoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
