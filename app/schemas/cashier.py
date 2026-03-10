from datetime import datetime
from pydantic import BaseModel


class CashierOrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    menu_item_name: str | None = None
    variant_id: int | None = None
    variant_name: str | None = None
    qty: int
    unit_price: int
    subtotal: int
    status: str
    note: str | None = None


class CashierOrderSummaryResponse(BaseModel):
    id: int
    table_id: int
    table_no: str | None = None
    waiter_id: int
    status: str
    opened_at: datetime | None = None
    submitted_at: datetime | None = None
    closed_at: datetime | None = None
    items: list[CashierOrderItemResponse]
    total_amount: int
    paid_amount: int
    remaining_amount: int


class CashierUnpaidOrderResponse(BaseModel):
    id: int
    table_id: int
    table_no: str | None = None
    waiter_id: int
    status: str
    submitted_at: datetime | None = None
    total_amount: int
    paid_amount: int
    remaining_amount: int


class CreatePaymentRequest(BaseModel):
    method: str
    amount: int


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    cashier_id: int | None = None
    method: str
    amount: int
    paid_at: datetime
    receipt_no: str

    model_config = {"from_attributes": True}


class CloseOrderResponse(BaseModel):
    order_id: int
    status: str
    closed_at: datetime