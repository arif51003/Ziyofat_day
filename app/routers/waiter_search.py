from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user_jwt
from app import models
from app.schemas.search import OrderSearchResult, MenuItemSearchResult, TableSearchResult

router = APIRouter(
    prefix="/waiter/search",
    tags=["Waiter Search"],
)


@router.get("/orders", response_model=list[OrderSearchResult])
def search_my_orders(
    q: Optional[str] = Query(None, description="Search by table number, status, or notes"),
    status: Optional[str] = Query(None, description="open | submitted | closed"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_jwt),
):
    query = db.query(models.Order).filter(
        models.Order.waiter_id == current_user.id
    )

    if q:
        query = query.join(models.DiningTable).filter(
            or_(
                models.DiningTable.table_no.ilike(f"%{q}%"),
                models.Order.status.ilike(f"%{q}%"),
                models.Order.notes.ilike(f"%{q}%"),
            )
        )

    if status:
        query = query.filter(models.Order.status == status)

    return query.order_by(models.Order.created_at.desc()).limit(50).all()


@router.get("/menu", response_model=list[MenuItemSearchResult])
def search_menu(
    q: str = Query(..., min_length=1, description="Search menu items by name"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user_jwt),
):
    return (
        db.query(models.MenuItem)
        .filter(
            models.MenuItem.is_active == True,
            or_(
                models.MenuItem.name.ilike(f"%{q}%"),
                models.MenuItem.description.ilike(f"%{q}%"),
            ),
        )
        .order_by(models.MenuItem.name)
        .limit(30)
        .all()
    )


@router.get("/tables", response_model=list[TableSearchResult])
def search_tables(
    q: Optional[str] = Query(None, description="Table number"),
    status: Optional[str] = Query(None, description="available | occupied | reserved"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user_jwt),
):
    query = db.query(models.DiningTable)

    if q:
        query = query.filter(models.DiningTable.table_no.ilike(f"%{q}%"))
    if status:
        query = query.filter(models.DiningTable.status == status)

    return query.order_by(models.DiningTable.table_no).all()