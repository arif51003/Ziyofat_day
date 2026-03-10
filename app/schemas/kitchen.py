from datetime import datetime
from pydantic import BaseModel


class KitchenOrderItemResponse(BaseModel):
    id: int
    order_id: int
    table_id: int | None = None
    table_no: str | None = None
    menu_item_id: int
    menu_item_name: str | None = None
    variant_id: int | None = None
    variant_name: str | None = None
    qty: int
    status: str
    note: str | None = None
    sent_at: datetime | None = None
    ready_at: datetime | None = None
    served_at: datetime | None = None


class KitchenOrderResponse(BaseModel):
    id: int
    table_id: int
    table_no: str | None = None
    waiter_id: int
    status: str
    opened_at: datetime | None = None
    submitted_at: datetime | None = None
    closed_at: datetime | None = None
    items: list[KitchenOrderItemResponse]


class KitchenActionResponse(BaseModel):
    item_id: int
    status: str
    ready_at: datetime | None = None