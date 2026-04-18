from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OrderSearchResult(BaseModel):
    id: int
    table_id: int
    status: str
    opened_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class MenuItemSearchResult(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    base_price: int
    station: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class TableSearchResult(BaseModel):
    id: int
    table_no: str
    capacity: int
    status: str

    class Config:
        from_attributes = True