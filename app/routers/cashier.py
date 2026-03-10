from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import current_user, db_dep
from app.models import Order, OrderItem, Payment
from app.schemas.cashier import (
    CashierOrderItemResponse,
    CashierOrderSummaryResponse,
    CashierUnpaidOrderResponse,
    CreatePaymentRequest,
    PaymentResponse,
    CloseOrderResponse,
)

router = APIRouter(prefix="/cashier", tags=["Cashier"])

@router.get("/orders/unpaid", response_model=list[CashierUnpaidOrderResponse])
def get_unpaid_orders(user: current_user, db: db_dep):
    if user.role != "cashier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat cashier uchun",
        )

    stmt = (
        select(Order)
        .where(Order.status == "submitted")
        .options(
            selectinload(Order.table),
            selectinload(Order.items),
            selectinload(Order.payments),
        )
        .order_by(Order.submitted_at.asc(), Order.id.asc())
    )
    orders = db.scalars(stmt).all()

    result: list[CashierUnpaidOrderResponse] = []

    for order in orders:
        total_amount = sum(item.qty * item.unit_price for item in order.items)
        paid_amount = sum(payment.amount for payment in order.payments)
        remaining_amount = total_amount - paid_amount

        result.append(
            CashierUnpaidOrderResponse(
                id=order.id,
                table_id=order.table_id,
                table_no=order.table.table_no if order.table else None,
                waiter_id=order.waiter_id,
                status=order.status,
                submitted_at=order.submitted_at,
                total_amount=total_amount,
                paid_amount=paid_amount,
                remaining_amount=remaining_amount,
            )
        )

    return result


@router.get("/orders/{order_id}/summary", response_model=CashierOrderSummaryResponse)
def get_order_summary(order_id: int, user: current_user, db: db_dep):
    if user.role != "cashier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat cashier uchun",
        )

    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.table),
            selectinload(Order.items).selectinload(OrderItem.menu_item),
            selectinload(Order.items).selectinload(OrderItem.variant),
            selectinload(Order.payments),
        )
    )
    order = db.scalar(stmt)

    if not order:
        raise HTTPException(status_code=404, detail="Order topilmadi")

    items: list[CashierOrderItemResponse] = []
    total_amount = 0

    for item in order.items:
        subtotal = item.qty * item.unit_price
        total_amount += subtotal

        items.append(
            CashierOrderItemResponse(
                id=item.id,
                menu_item_id=item.menu_item_id,
                menu_item_name=item.menu_item.name if item.menu_item else None,
                variant_id=item.variant_id,
                variant_name=item.variant.name if item.variant else None,
                qty=item.qty,
                unit_price=item.unit_price,
                subtotal=subtotal,
                status=item.status,
                note=item.note,
            )
        )

    paid_amount = sum(payment.amount for payment in order.payments)
    remaining_amount = total_amount - paid_amount

    return CashierOrderSummaryResponse(
        id=order.id,
        table_id=order.table_id,
        table_no=order.table.table_no if order.table else None,
        waiter_id=order.waiter_id,
        status=order.status,
        opened_at=order.opened_at,
        submitted_at=order.submitted_at,
        closed_at=order.closed_at,
        items=items,
        total_amount=total_amount,
        paid_amount=paid_amount,
        remaining_amount=remaining_amount,
    )
    
    
@router.post("/orders/{order_id}/pay", response_model=PaymentResponse, status_code=201)
def create_payment(order_id: int, data: CreatePaymentRequest, user: current_user, db: db_dep):
    if user.role != "cashier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat cashier uchun",
        )

    if data.method not in ["cash", "card", "mixed"]:
        raise HTTPException(status_code=400, detail="Noto'g'ri payment method")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount 0 dan katta bo'lishi kerak")

    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.items),
            selectinload(Order.payments),
        )
    )
    order = db.scalar(stmt)

    if not order:
        raise HTTPException(status_code=404, detail="Order topilmadi")

    if order.status != "submitted":
        raise HTTPException(
            status_code=400,
            detail="Faqat submitted orderga payment qilish mumkin",
        )

    total_amount = sum(item.qty * item.unit_price for item in order.items)
    paid_amount = sum(payment.amount for payment in order.payments)
    remaining_amount = total_amount - paid_amount

    if remaining_amount <= 0:
        raise HTTPException(status_code=400, detail="Bu order allaqachon to'langan")

    if data.amount > remaining_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Ortiqcha to'lov. Qolgan summa: {remaining_amount}",
        )

    payment = Payment(
        order_id=order.id,
        cashier_id=user.id,
        method=data.method,
        amount=data.amount,
        paid_at=datetime.now(),
        receipt_no=f"RCPT-{uuid4().hex[:12].upper()}",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return PaymentResponse.model_validate(payment)


@router.post("/orders/{order_id}/close", response_model=CloseOrderResponse)
def close_order(order_id: int, user: current_user, db: db_dep):
    if user.role != "cashier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat cashier uchun",
        )

    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.items),
            selectinload(Order.payments),
            selectinload(Order.table),
        )
    )
    order = db.scalar(stmt)

    if not order:
        raise HTTPException(status_code=404, detail="Order topilmadi")

    if order.status != "submitted":
        raise HTTPException(
            status_code=400,
            detail="Faqat submitted orderni close qilish mumkin",
        )

    total_amount = sum(item.qty * item.unit_price for item in order.items)
    paid_amount = sum(payment.amount for payment in order.payments)
    remaining_amount = total_amount - paid_amount

    if remaining_amount != 0:
        raise HTTPException(
            status_code=400,
            detail=f"Orderni yopib bo'lmaydi. Qolgan summa: {remaining_amount}",
        )

    order.status = "closed"
    order.closed_at = datetime.now()

    if order.table:
        order.table.status = "free"

    db.commit()
    db.refresh(order)

    return order