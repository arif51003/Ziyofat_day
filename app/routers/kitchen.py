from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import current_user, db_dep
from app.models import Order, OrderItem
from app.schemas.kitchen import (
    KitchenOrderItemResponse,
    KitchenOrderResponse,
    KitchenActionResponse,
)

router = APIRouter(prefix="/kitchen", tags=["Kitchen"])

@router.get("/order-items/queue", response_model=list[KitchenOrderItemResponse])
def get_kitchen_queue(user: current_user, db: db_dep):
    if user.role != "kitchen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat kitchen uchun",
        )

    stmt = (
        select(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.status == "submitted",
            OrderItem.status.in_(["sent", "preparing"]),
        )
        .options(
            selectinload(OrderItem.order).selectinload(Order.table),
            selectinload(OrderItem.menu_item),
            selectinload(OrderItem.variant),
        )
        .order_by(Order.submitted_at.asc(), OrderItem.id.asc())
    )
    items = db.scalars(stmt).all()

    return [
        KitchenOrderItemResponse(
            id=item.id,
            order_id=item.order_id,
            table_id=item.order.table_id if item.order else None,
            table_no=item.order.table.table_no if item.order and item.order.table else None,
            menu_item_id=item.menu_item_id,
            menu_item_name=item.menu_item.name if item.menu_item else None,
            variant_id=item.variant_id,
            variant_name=item.variant.name if item.variant else None,
            qty=item.qty,
            status=item.status,
            note=item.note,
            sent_at=item.sent_at,
            ready_at=item.ready_at,
            served_at=item.served_at,
        )
        for item in items
    ]
    
    
@router.get("/orders/{order_id}", response_model=KitchenOrderResponse)
def get_kitchen_order(order_id: int, user: current_user, db: db_dep):
    if user.role != "kitchen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat kitchen uchun",
        )

    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.table),
            selectinload(Order.items).selectinload(OrderItem.menu_item),
            selectinload(Order.items).selectinload(OrderItem.variant),
        )
    )
    order = db.scalar(stmt)

    if not order:
        raise HTTPException(status_code=404, detail="Order topilmadi")

    if order.status not in ["submitted", "closed"]:
        raise HTTPException(
            status_code=400,
            detail="Kitchen faqat submitted yoki closed orderni ko'ra oladi",
        )

    items = [
        KitchenOrderItemResponse(
            id=item.id,
            order_id=item.order_id,
            table_id=order.table_id,
            table_no=order.table.table_no if order.table else None,
            menu_item_id=item.menu_item_id,
            menu_item_name=item.menu_item.name if item.menu_item else None,
            variant_id=item.variant_id,
            variant_name=item.variant.name if item.variant else None,
            qty=item.qty,
            status=item.status,
            note=item.note,
            sent_at=item.sent_at,
            ready_at=item.ready_at,
            served_at=item.served_at,
        )
        for item in order.items
    ]

    return KitchenOrderResponse(
        id=order.id,
        table_id=order.table_id,
        table_no=order.table.table_no if order.table else None,
        waiter_id=order.waiter_id,
        status=order.status,
        opened_at=order.opened_at,
        submitted_at=order.submitted_at,
        closed_at=order.closed_at,
        items=items,
    )
    
@router.post("/order-items/{item_id}/start", response_model=KitchenActionResponse)
def start_preparing(item_id: int, user: current_user, db: db_dep):
    if user.role != "kitchen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat kitchen uchun",
        )

    stmt = (
        select(OrderItem)
        .where(OrderItem.id == item_id)
        .options(selectinload(OrderItem.order))
    )
    item = db.scalar(stmt)

    if not item:
        raise HTTPException(status_code=404, detail="Order item topilmadi")

    if not item.order or item.order.status != "submitted":
        raise HTTPException(
            status_code=400,
            detail="Faqat submitted orderdagi itemni tayyorlash mumkin",
        )

    if item.status != "sent":
        raise HTTPException(
            status_code=400,
            detail="Faqat sent holatdagi itemni preparing qilish mumkin",
        )

    item.status = "preparing"

    db.commit()
    db.refresh(item)

    return KitchenActionResponse(
        item_id=item.id,
        status=item.status,
        ready_at=item.ready_at,
    )
    
    
@router.post("/order-items/{item_id}/ready", response_model=KitchenActionResponse)
def mark_item_ready(item_id: int, user: current_user, db: db_dep):
    if user.role != "kitchen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat kitchen uchun",
        )

    stmt = (
        select(OrderItem)
        .where(OrderItem.id == item_id)
        .options(
            selectinload(OrderItem.order).selectinload(Order.items)
        )
    )
    item = db.scalar(stmt)

    if not item:
        raise HTTPException(status_code=404, detail="Order item topilmadi")

    if not item.order or item.order.status != "submitted":
        raise HTTPException(
            status_code=400,
            detail="Faqat submitted orderdagi itemni ready qilish mumkin",
        )

    if item.status not in ["sent", "preparing"]:
        raise HTTPException(
            status_code=400,
            detail="Faqat sent yoki preparing holatdagi itemni ready qilish mumkin",
        )

    item.status = "ready"
    item.ready_at = datetime.now()

    db.commit()
    db.refresh(item)

    return KitchenActionResponse(
        item_id=item.id,
        status=item.status,
        ready_at=item.ready_at,
    )