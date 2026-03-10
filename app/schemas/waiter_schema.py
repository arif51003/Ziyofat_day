from datetime import datetime
from pydantic import BaseModel, Field


class OpenOrderRequest(BaseModel):
    table_id: int


class AddOrderItemRequest(BaseModel):
    menu_item_id: int
    variant_id: int | None = None
    qty: int = Field(gt=0)
    note: str | None = None


class UpdateOrderItemRequest(BaseModel):
    qty: int | None = Field(default=None, gt=0)
    note: str | None = None


class MenuVariantResponse(BaseModel):
    id: int
    name: str
    price_delta: int

    model_config = {"from_attributes": True}


class MenuItemResponse(BaseModel):
    id: int
    name: str
    description: str
    base_price: int
    station: str
    img_url: str | None = None
    variants: list[MenuVariantResponse]

    model_config = {"from_attributes": True}


class MenuCategoryResponse(BaseModel):
    id: int
    name: str
    sort_order: int
    items: list[MenuItemResponse]

    model_config = {"from_attributes": True}


class FreeTableResponse(BaseModel):
    id: int
    table_no: str
    capacity: int
    status: str

    model_config = {"from_attributes": True}


class OpenOrderResponse(BaseModel):
    id: int
    table_id: int
    status: str


class OrderItemShortResponse(BaseModel):
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


class OrderItemResponse(BaseModel):
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
    sent_at: datetime | None = None
    ready_at: datetime | None = None
    served_at: datetime | None = None


class OrderResponse(BaseModel):
    id: int
    table_id: int
    table_no: str | None = None
    waiter_id: int
    status: str
    opened_at: datetime | None = None
    submitted_at: datetime | None = None
    closed_at: datetime | None = None
    notes: str | None = None
    items: list[OrderItemResponse]
    total_amount: int


class AddOrderItemResponse(BaseModel):
    id: int
    order_id: int
    menu_item_id: int
    menu_item_name: str | None = None
    variant_id: int | None = None
    variant_name: str | None = None
    qty: int
    unit_price: int
    subtotal: int
    status: str
    note: str | None = None


class UpdateOrderItemResponse(BaseModel):
    id: int
    qty: int
    note: str | None = None
    unit_price: int
    subtotal: int
    status: str


class DeleteOrderItemResponse(BaseModel):
    message: str


class DeductedIngredientResponse(BaseModel):
    ingredient_id: int
    qty: float


class SubmitOrderResponse(BaseModel):
    order_id: int
    status: str
    submitted_at: datetime
    deducted_ingredients: list[DeductedIngredientResponse]