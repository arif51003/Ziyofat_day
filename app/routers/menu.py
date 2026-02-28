from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.database import db_dep
from app.models import MenuCategory, MenuItem, MenuItemVariant
from app.schemas import (
    MenuCategoryCreate, MenuCategoryRead, MenuCategoryUpdate,
    MenuItemCreate, MenuItemRead, MenuItemUpdate,
    MenuItemVariantCreate, MenuItemVariantRead,
)

router = APIRouter(prefix="/menu", tags=["Menu"])


# ════════════════════════════════
#  KATEGORIYALAR
# ════════════════════════════════

@router.get("/categories/", response_model=list[MenuCategoryRead])
def get_categories(session: db_dep):
    """Barcha kategoriyalar (sort_order bo'yicha)"""
    return session.execute(
        select(MenuCategory).order_by(MenuCategory.sort_order)
    ).scalars().all()


@router.get("/categories/{category_id}/", response_model=MenuCategoryRead)
def get_category(category_id: int, session: db_dep):
    """Bitta kategoriya"""
    category = session.get(MenuCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Kategoriya topilmadi")
    return category


@router.post("/categories/", response_model=MenuCategoryRead, status_code=201)
def create_category(data: MenuCategoryCreate, session: db_dep):
    """Yangi kategoriya"""
    category = MenuCategory(**data.model_dump())
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.put("/categories/{category_id}/", response_model=MenuCategoryRead)
def update_category(category_id: int, data: MenuCategoryUpdate, session: db_dep):
    """Kategoriyani tahrirlash"""
    category = session.get(MenuCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Kategoriya topilmadi")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    session.commit()
    session.refresh(category)
    return category


@router.delete("/categories/{category_id}/", status_code=204)
def delete_category(category_id: int, session: db_dep):
    """Kategoriyani o'chirish (bog'liq taomlar bo'lsa xato qaytaradi)"""
    category = session.get(MenuCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Kategoriya topilmadi")
    has_items = session.execute(
        select(MenuItem).where(MenuItem.category_id == category_id)
    ).scalars().first()
    if has_items:
        raise HTTPException(
            status_code=400,
            detail="Kategoriyada taomlar bor. Avval taomlarni ko'chiring."
        )
    session.delete(category)
    session.commit()


# ════════════════════════════════
#  TAOMLAR
# ════════════════════════════════

@router.get("/items/", response_model=list[MenuItemRead])
def get_items(
    session: db_dep,
    category_id: int | None = None,
    is_active: bool = True,
    station: str | None = None,
):
    """
    Taomlar ro'yxati.
    - ?category_id=1     — kategoriya bo'yicha filter
    - ?station=kitchen   — stantsiya bo'yicha filter
    - ?is_active=false   — o'chirilgan taomlarni ko'rish
    """
    stmt = select(MenuItem).where(MenuItem.is_active == is_active)
    if category_id is not None:
        stmt = stmt.where(MenuItem.category_id == category_id)
    if station is not None:
        stmt = stmt.where(MenuItem.station == station)
    return session.execute(stmt).scalars().all()


@router.get("/items/{item_id}/", response_model=MenuItemRead)
def get_item(item_id: int, session: db_dep):
    """Bitta taom — variantlari bilan"""
    item = session.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Taom topilmadi")
    return item


@router.post("/items/", response_model=MenuItemRead, status_code=201)
def create_item(data: MenuItemCreate, session: db_dep):
    """Yangi taom qo'shish"""
    if data.category_id is not None:
        if not session.get(MenuCategory, data.category_id):
            raise HTTPException(status_code=404, detail="Kategoriya topilmadi")
    item = MenuItem(**data.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/items/{item_id}/", response_model=MenuItemRead)
def update_item(item_id: int, data: MenuItemUpdate, session: db_dep):
    """Taomni tahrirlash"""
    item = session.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Taom topilmadi")
    if data.category_id is not None:
        if not session.get(MenuCategory, data.category_id):
            raise HTTPException(status_code=404, detail="Kategoriya topilmadi")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/items/{item_id}/", response_model=MenuItemRead)
def delete_item(item_id: int, session: db_dep):
    """
    Taomni o'chirish — SOFT DELETE.
    Bazadan o'chirmaydi, is_active=False qiladi.
    Eski buyurtmalar buzilmaydi.
    """
    item = session.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Taom topilmadi")
    item.is_active = False
    session.commit()
    session.refresh(item)
    return item


# ════════════════════════════════
#  VARIANTLAR
# ════════════════════════════════

@router.get("/items/{item_id}/variants/", response_model=list[MenuItemVariantRead])
def get_variants(item_id: int, session: db_dep):
    """Taomning variantlari (katta/kichik porsiya va h.k.)"""
    if not session.get(MenuItem, item_id):
        raise HTTPException(status_code=404, detail="Taom topilmadi")
    return session.execute(
        select(MenuItemVariant).where(
            MenuItemVariant.menu_item_id == item_id,
            MenuItemVariant.is_active == True,  # noqa: E712
        )
    ).scalars().all()


@router.post("/items/{item_id}/variants/", response_model=MenuItemVariantRead, status_code=201)
def create_variant(item_id: int, data: MenuItemVariantCreate, session: db_dep):
    """
    Taomga variant qo'shish.
    price_delta — asosiy narxga qo'shiladigan farq.
    Masalan: base_price=35000, price_delta=10000 => yakuniy narx 45000
    """
    if not session.get(MenuItem, item_id):
        raise HTTPException(status_code=404, detail="Taom topilmadi")
    variant = MenuItemVariant(menu_item_id=item_id, **data.model_dump())
    session.add(variant)
    session.commit()
    session.refresh(variant)
    return variant