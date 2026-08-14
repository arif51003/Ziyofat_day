from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.dependencies import waiter_user, db_dep
from app.models import (
    DiningTable,
    MenuCategory,
    MenuItem,
    MenuItemVariant,
    Order,
    OrderItem,
    MenuIngredient,
    Ingredient,
    IngredientStock,
    StockMovements,
)
from app.schemas.waiter_schema import (
    OpenOrderRequest,
    AddOrderItemRequest,
    UpdateOrderItemRequest,
    MenuCategoryResponse,
    MenuItemResponse,
    MenuVariantResponse,
    FreeTableResponse,
    OpenOrderResponse,
    OrderResponse,
    OrderItemResponse,
    AddOrderItemResponse,
    UpdateOrderItemResponse,
    DeleteOrderItemResponse,
    SubmitOrderResponse,
    DeductedIngredientResponse,
    ServeOrderItemResponse,
)

router = APIRouter(prefix="/waiter", tags=["Waiter"])

@router.get("/menu", response_model=list[MenuCategoryResponse])
def get_menu(user: waiter_user, db: db_dep):

    stmt = (
        select(MenuCategory)
        .where(MenuCategory.restaurant_id == user.restaurant_id)
        .options(
            selectinload(MenuCategory.items).selectinload(MenuItem.variants),
            selectinload(MenuCategory.items).selectinload(MenuItem.img),
        )
        .order_by(MenuCategory.sort_order, MenuCategory.id)
    )
    categories = db.scalars(stmt).all()

    result: list[MenuCategoryResponse] = []

    for category in categories:
        items: list[MenuItemResponse] = []

        for item in category.items:
            if not item.is_active:
                continue

            variants: list[MenuVariantResponse] = []
            for variant in item.variants:
                if not variant.is_active:
                    continue

                variants.append(
                    MenuVariantResponse(
                        id=variant.id,
                        name=variant.name,
                        price_delta=variant.price_delta,
                    )
                )

            items.append(
                MenuItemResponse(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    base_price=item.base_price,
                    station=item.station,
                    img_url=item.img.url if item.img else None,
                    variants=variants,
                )
            )

        if items:
            result.append(
                MenuCategoryResponse(
                    id=category.id,
                    name=category.name,
                    sort_order=category.sort_order,
                    items=items,
                )
            )

    return result



@router.get("/tables/free", response_model=list[FreeTableResponse])
def get_free_tables(user: waiter_user, db: db_dep):

    stmt = (
        select(DiningTable)
        .where(DiningTable.restaurant_id == user.restaurant_id, DiningTable.status == "free")
        .order_by(DiningTable.table_no)
    )
    tables = db.scalars(stmt).all()

    return tables
    
    
@router.post("/orders/open", response_model=OpenOrderResponse, status_code=201)
def open_order(data: OpenOrderRequest, user: waiter_user, db: db_dep):

    table = db.scalar(
        select(DiningTable).where(
            DiningTable.id == data.table_id,
            DiningTable.restaurant_id == user.restaurant_id,
        )
    )
    if not table:
        raise HTTPException(status_code=404, detail="Stol topilmadi")

    if table.status != "free":
        raise HTTPException(status_code=400, detail="Stol bo'sh emas")

    exists = db.scalar(
        select(Order).where(
            Order.table_id == table.id,
            Order.status.in_(["open", "submitted"]),
        )
    )
    if exists:
        raise HTTPException(
            status_code=400,
            detail="Bu stol uchun active order mavjud",
        )

    order = Order(
        restaurant_id=user.restaurant_id,
        table_id=table.id,
        waiter_id=user.id,
        status="open",
        opened_at=datetime.now(),
    )
    db.add(order)
    table.status = "occupied"

    db.commit()
    db.refresh(order)

    return order
    
@router.get("/orders/my-active", response_model=list[OrderResponse])
def get_my_active_orders(user: waiter_user, db: db_dep):

    stmt = (
        select(Order)
        .where(
            Order.waiter_id == user.id,
            Order.status.in_(["open", "submitted"]),
        )
        .options(
            selectinload(Order.table),
            selectinload(Order.items).selectinload(OrderItem.menu_item),
            selectinload(Order.items).selectinload(OrderItem.variant),
        )
        .order_by(Order.id.desc())
    )
    orders = db.scalars(stmt).all()

    result: list[OrderResponse] = []

    for order in orders:
        items: list[OrderItemResponse] = []
        total = 0

        for item in order.items:
            subtotal = item.qty * item.unit_price
            total += subtotal

            items.append(
                OrderItemResponse(
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
                    sent_at=item.sent_at,
                    ready_at=item.ready_at,
                    served_at=item.served_at,
                )
            )

        result.append(
            OrderResponse(
                id=order.id,
                table_id=order.table_id,
                table_no=order.table.table_no if order.table else None,
                waiter_id=order.waiter_id,
                status=order.status,
                opened_at=order.opened_at,
                submitted_at=order.submitted_at,
                closed_at=order.closed_at,
                notes=order.notes,
                items=items,
                total_amount=total,
            )
        )

    return result


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, user: waiter_user, db: db_dep):

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

    if order.waiter_id != user.id:
        raise HTTPException(status_code=403, detail="Bu order sizga tegishli emas")

    items: list[OrderItemResponse] = []
    total = 0

    for item in order.items:
        subtotal = item.qty * item.unit_price
        total += subtotal

        items.append(
            OrderItemResponse(
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
                sent_at=item.sent_at,
                ready_at=item.ready_at,
                served_at=item.served_at,
            )
        )

    return OrderResponse(
        id=order.id,
        table_id=order.table_id,
        table_no=order.table.table_no if order.table else None,
        waiter_id=order.waiter_id,
        status=order.status,
        opened_at=order.opened_at,
        submitted_at=order.submitted_at,
        closed_at=order.closed_at,
        notes=order.notes,
        items=items,
        total_amount=total,
    )
    
@router.post("/orders/{order_id}/items", response_model=AddOrderItemResponse, status_code=201)
def add_order_item(order_id: int, data: AddOrderItemRequest, user: waiter_user, db: db_dep):

    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order topilmadi")

    if order.waiter_id != user.id:
        raise HTTPException(status_code=403, detail="Bu order sizga tegishli emas")

    if order.status not in ["open", "submitted"]:
        raise HTTPException(status_code=400, detail="Faqat open yoki submitted orderga item qo'shiladi")

    menu_item = db.scalar(
        select(MenuItem).where(
            MenuItem.id == data.menu_item_id,
            MenuItem.restaurant_id == user.restaurant_id,
        )
    )
    if not menu_item or not menu_item.is_active:
        raise HTTPException(status_code=404, detail="Menu item topilmadi")

    unit_price = menu_item.base_price
    variant_id = None
    variant_name = None

    if data.variant_id is not None:
        variant = db.get(MenuItemVariant, data.variant_id)
        if not variant:
            raise HTTPException(status_code=404, detail="Variant topilmadi")
        if variant.menu_item_id != menu_item.id:
            raise HTTPException(status_code=400, detail="Variant noto'g'ri")
        if not variant.is_active:
            raise HTTPException(status_code=400, detail="Variant nofaol")

        unit_price += variant.price_delta
        variant_id = variant.id
        variant_name = variant.name

    item = OrderItem(
        restaurant_id=user.restaurant_id,
        order_id=order.id,
        menu_item_id=menu_item.id,
        variant_id=variant_id,
        qty=data.qty,
        unit_price=unit_price,
        status="new",
        note=data.note,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return AddOrderItemResponse(
        id=item.id,
        order_id=item.order_id,
        menu_item_id=item.menu_item_id,
        menu_item_name=menu_item.name,
        variant_id=item.variant_id,
        variant_name=variant_name,
        qty=item.qty,
        unit_price=item.unit_price,
        subtotal=item.qty * item.unit_price,
        status=item.status,
        note=item.note,
    )
    
@router.patch("/orders/{order_id}/items/{item_id}", response_model=UpdateOrderItemResponse)
def update_order_item(
    order_id: int,
    item_id: int,
    data: UpdateOrderItemRequest,
    user: waiter_user,
    db: db_dep,
):

    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order topilmadi")

    if order.waiter_id != user.id:
        raise HTTPException(status_code=403, detail="Bu order sizga tegishli emas")

    if order.status not in ["open", "submitted"]:
        raise HTTPException(status_code=400, detail="Faqat open yoki submitted orderdagi itemni o'zgartiriladi")

    item = db.scalar(select(OrderItem).where(OrderItem.id == item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Order item topilmadi")

    if item.order_id != order.id:
        raise HTTPException(status_code=400, detail="Item bu orderga tegishli emas")

    if item.status != "new":
        raise HTTPException(status_code=400, detail="Oshxonaga yuborilgan itemni o'zgartirib bo'lmaydi")

    payload = data.model_dump(exclude_unset=True)

    if "qty" in payload and payload["qty"] is not None:
        item.qty = payload["qty"]

    if "note" in payload:
        item.note = payload["note"]

    db.commit()
    db.refresh(item)

    return UpdateOrderItemResponse(
        id=item.id,
        qty=item.qty,
        note=item.note,
        unit_price=item.unit_price,
        subtotal=item.qty * item.unit_price,
        status=item.status,
    )
    
@router.delete("/orders/{order_id}/items/{item_id}", response_model=DeleteOrderItemResponse)
def delete_order_item(order_id: int, item_id: int, user: waiter_user, db: db_dep):

    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order topilmadi")

    if order.waiter_id != user.id:
        raise HTTPException(status_code=403, detail="Bu order sizga tegishli emas")

    if order.status not in ["open", "submitted"]:
        raise HTTPException(status_code=400, detail="Faqat open yoki submitted orderdagi itemlar o'chiriladi")

    item = db.scalar(select(OrderItem).where(OrderItem.id == item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Order item topilmadi")

    if item.order_id != order.id:
        raise HTTPException(status_code=400, detail="Item bu orderga tegishli emas")

    if item.status != "new":
        raise HTTPException(status_code=400, detail="Oshxonaga yuborilgan itemni o'chirib bo'lmaydi")

    db.delete(item)
    db.commit()

    return DeleteOrderItemResponse(message="Item o'chirildi")


@router.post("/orders/{order_id}/items/{item_id}/serve", response_model=ServeOrderItemResponse)
def serve_order_item(order_id: int, item_id: int, user: waiter_user, db: db_dep):

    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order topilmadi")

    if order.waiter_id != user.id:
        raise HTTPException(status_code=403, detail="Bu order sizga tegishli emas")

    item = db.scalar(select(OrderItem).where(OrderItem.id == item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Order item topilmadi")

    if item.order_id != order.id:
        raise HTTPException(status_code=400, detail="Item bu orderga tegishli emas")

    if item.status != "ready":
        raise HTTPException(
            status_code=400,
            detail="Faqat oshxonada tayyor bo'lgan itemni servaga berish mumkin",
        )

    item.status = "served"
    item.served_at = datetime.now()

    db.commit()
    db.refresh(item)

    return ServeOrderItemResponse(
        id=item.id,
        status=item.status,
        served_at=item.served_at,
    )


@router.post("/orders/{order_id}/submit", response_model=SubmitOrderResponse)
def submit_order(order_id: int, user: waiter_user, db: db_dep):

    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items), selectinload(Order.table))
    )
    order = db.scalar(stmt)

    if not order:
        raise HTTPException(status_code=404, detail="Order topilmadi")

    if order.waiter_id != user.id:
        raise HTTPException(status_code=403, detail="Bu order sizga tegishli emas")

    if order.status not in ["open", "submitted"]:
        raise HTTPException(status_code=400, detail="Faqat open yoki submitted order submit qilinadi")

    new_items = [item for item in order.items if item.status == "new"]

    if not new_items:
        raise HTTPException(status_code=400, detail="Yangi item yo'q")

    ingredient_totals: dict[int, float] = {}

    for order_item in new_items:
        recipes = db.scalars(
            select(MenuIngredient).where(MenuIngredient.menu_item_id == order_item.menu_item_id)
        ).all()

        if not recipes:
            menu_item = db.get(MenuItem, order_item.menu_item_id)
            raise HTTPException(
                status_code=400,
                detail=f"{menu_item.name} uchun retsept yo'q",
            )

        for recipe in recipes:
            needed_qty = recipe.qty_required * order_item.qty
            ingredient_totals[recipe.ingredient_id] = (
                ingredient_totals.get(recipe.ingredient_id, 0) + needed_qty
            )

    ingredient_ids = list(ingredient_totals.keys())

    stocks = db.scalars(
        select(IngredientStock).where(IngredientStock.ingredient_id.in_(ingredient_ids))
    ).all()
    stock_map = {stock.ingredient_id: stock for stock in stocks}

    for ingredient_id, needed_qty in ingredient_totals.items():
        ingredient = db.get(Ingredient, ingredient_id)
        stock = stock_map.get(ingredient_id)

        if not stock:
            raise HTTPException(
                status_code=400,
                detail=f"{ingredient.name} uchun stock topilmadi",
            )

        if stock.qty_on_hand < needed_qty:
            raise HTTPException(
                status_code=400,
                detail=f"{ingredient.name} yetarli emas. Kerak {needed_qty}, bor {stock.qty_on_hand}",
            )

    for ingredient_id, needed_qty in ingredient_totals.items():
        stock = stock_map[ingredient_id]
        stock.qty_on_hand -= needed_qty

        movement = StockMovements(
            restaurant_id=user.restaurant_id,
            ingredient_id=ingredient_id,
            status="OUT",
            qty=needed_qty,
            created_by=user.id,
        )
        db.add(movement)

    now = datetime.now()
    order.status = "submitted"
    order.submitted_at = now

    for item in new_items:
        item.status = "sent"
        item.sent_at = now

    db.commit()

    return SubmitOrderResponse(
        order_id=order.id,
        status=order.status,
        submitted_at=order.submitted_at,
        deducted_ingredients=[
            DeductedIngredientResponse(
                ingredient_id=ingredient_id,
                qty=qty,
            )
            for ingredient_id, qty in ingredient_totals.items()
        ],
    )


@router.get("/orders/search")
def search_orders(q: str, user: waiter_user, db: db_dep):
    """Search orders by ID, table number, or item name"""
    search_term = f"%{q.lower()}%"
    
    # Search by order ID, table number, or menu item name
    stmt = (
        select(Order)
        .where(Order.waiter_id == user.id)
        .join(DiningTable)
        .join(OrderItem)
        .join(MenuItem)
        .where(
            or_(
                Order.id == int(q) if q.isdigit() else False,
                DiningTable.table_no.like(search_term),
                MenuItem.name.ilike(search_term),
            )
        )
        .distinct()
        .order_by(Order.id.desc())
    )
    
    try:
        orders = db.scalars(stmt).all()
        return [
            OrderResponse(
                id=o.id,
                table_id=o.table_id,
                table_no=o.table.table_no,
                waiter_id=o.waiter_id,
                status=o.status,
                total_amount=sum((item.qty * item.unit_price) for item in o.items),
                items=[
                    OrderItemResponse(
                        id=item.id,
                        order_id=item.order_id,
                        menu_item_id=item.menu_item_id,
                        menu_item_name=item.menu_item.name,
                        variant_id=item.variant_id,
                        variant_name=item.variant.name if item.variant else None,
                        qty=item.qty,
                        unit_price=item.unit_price,
                        subtotal=item.qty * item.unit_price,
                        status=item.status,
                    )
                    for item in o.items
                ],
                opened_at=o.opened_at,
                submitted_at=o.submitted_at,
            )
            for o in orders
        ]
    except Exception:
        # If search fails, return empty list
        return []