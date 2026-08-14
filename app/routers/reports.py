from collections import defaultdict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import admin_user, db_dep
from app.models import Ingredient, MenuIngredient, Order
from app.schemas.reports import RevenueBucket, RevenueReportResponse

router = APIRouter(prefix="/reports", tags=["Reports"])


def _bucket_key(when: datetime, period: str) -> str:
    return when.strftime("%Y-%m") if period == "monthly" else when.strftime("%Y-%m-%d")


@router.get("/revenue", response_model=RevenueReportResponse)
def get_revenue_report(
    admin: admin_user,
    db: db_dep,
    period: str = "daily",
    days: int = 30,
):
    if period not in ("daily", "monthly"):
        raise HTTPException(status_code=400, detail="period 'daily' yoki 'monthly' bo'lishi kerak")

    if days <= 0 or days > 366:
        raise HTTPException(status_code=400, detail="days 1 dan 366 gacha bo'lishi kerak")

    to_date = date.today()
    from_date = to_date - timedelta(days=days - 1)
    range_start = datetime.combine(from_date, datetime.min.time())
    range_end = datetime.combine(to_date, datetime.max.time())

    stmt = (
        select(Order)
        .where(
            Order.restaurant_id == admin.restaurant_id,
            Order.status == "closed",
            Order.closed_at >= range_start,
            Order.closed_at <= range_end,
        )
        .options(
            selectinload(Order.items),
            selectinload(Order.payments),
        )
        .order_by(Order.closed_at.asc())
    )
    orders = db.scalars(stmt).all()

    menu_item_ids = {item.menu_item_id for order in orders for item in order.items}

    recipes_by_menu_item: dict[int, list[MenuIngredient]] = defaultdict(list)
    if menu_item_ids:
        recipes = db.scalars(
            select(MenuIngredient).where(MenuIngredient.menu_item_id.in_(menu_item_ids))
        ).all()
        for recipe in recipes:
            recipes_by_menu_item[recipe.menu_item_id].append(recipe)

        ingredient_ids = {r.ingredient_id for r in recipes}
        ingredients = db.scalars(
            select(Ingredient).where(Ingredient.id.in_(ingredient_ids))
        ).all()
        cost_by_ingredient = {ing.id: ing.cost_price for ing in ingredients}
    else:
        cost_by_ingredient = {}

    buckets: dict[str, dict[str, int]] = {}

    for order in orders:
        key = _bucket_key(order.closed_at, period)
        bucket = buckets.setdefault(key, {"orders_count": 0, "revenue": 0, "cost": 0})

        bucket["orders_count"] += 1
        bucket["revenue"] += sum(item.qty * item.unit_price for item in order.items)

        for item in order.items:
            for recipe in recipes_by_menu_item.get(item.menu_item_id, []):
                unit_cost = cost_by_ingredient.get(recipe.ingredient_id, 0)
                bucket["cost"] += round(recipe.qty_required * item.qty * unit_cost)

    bucket_list = [
        RevenueBucket(
            period=key,
            orders_count=data["orders_count"],
            revenue=data["revenue"],
            cost=data["cost"],
            profit=data["revenue"] - data["cost"],
        )
        for key, data in sorted(buckets.items())
    ]

    return RevenueReportResponse(
        period_type=period,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
        buckets=bucket_list,
        total_orders=sum(b.orders_count for b in bucket_list),
        total_revenue=sum(b.revenue for b in bucket_list),
        total_cost=sum(b.cost for b in bucket_list),
        total_profit=sum(b.profit for b in bucket_list),
    )
