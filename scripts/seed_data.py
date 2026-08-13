"""
Ziyofat Day uchun namuna (demo) ma'lumotlar bilan bazani to'ldirish skripti.

DIQQAT: bu skript quyidagi jadvallardagi BARCHA mavjud ma'lumotlarni
o'chirib tashlaydi (TRUNCATE ... CASCADE) va o'rniga to'liq bog'langan
(retsept, ombor, buyurtma namunalari bilan) yangi demo ma'lumotlarni
joylashtiradi.

Ishlatish:
    uv run python scripts/seed_data.py --yes
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import (
    User,
    DiningTable,
    MenuCategory,
    MenuItem,
    MenuItemVariant,
    Ingredient,
    MenuIngredient,
    IngredientStock,
    Order,
    OrderItem,
    Payment,
    AuditLog,
)
from app.utils import hash_password
from sqlalchemy import text

TABLES_TO_TRUNCATE = [
    "audit_log",
    "payment",
    "order_item",
    "orders",
    "menu_ingredient",
    "ingredient_stock",
    "stock_movements",
    "menu_item_variant",
    "menu_item",
    "menu_category",
    "dining_table",
    "ingredients",
    "media",
    "token_blacklist",
    "users",
]


def wipe_tables(db):
    table_list = ", ".join(TABLES_TO_TRUNCATE)
    db.execute(text(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE"))
    db.commit()


def seed_users(db) -> dict[str, User]:
    def make(username, role, first_name, last_name, is_admin=False):
        return User(
            username=username,
            password_hash=hash_password(f"{username}123"),
            role=role,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
            is_active=True,
        )

    users = {
        "admin": make("admin", "admin", "Sardor", "Administrator", is_admin=True),
        "aziz": make("aziz", "waiter", "Aziz", "Karimov"),
        "malika": make("malika", "waiter", "Malika", "Yusupova"),
        "javlon": make("javlon", "waiter", "Javlon", "Toshpo'latov"),
        "botir": make("botir", "kitchen", "Botir", "Nazarov"),
        "dilnoza": make("dilnoza", "kitchen", "Dilnoza", "Qosimova"),
        "shahnoza": make("shahnoza", "cashier", "Shahnoza", "Rashidova"),
        "otabek": make("otabek", "cashier", "Otabek", "Yo'ldoshev"),
    }
    db.add_all(users.values())
    db.flush()
    return users


def seed_tables(db) -> dict[str, DiningTable]:
    layout = [
        ("1", 2), ("2", 2), ("3", 4), ("4", 4), ("5", 4),
        ("6", 6), ("7", 6), ("8", 8), ("9", 4), ("10", 2),
    ]
    tables = {
        table_no: DiningTable(table_no=table_no, capacity=cap, status="free")
        for table_no, cap in layout
    }
    db.add_all(tables.values())
    db.flush()
    return tables


def seed_categories(db) -> dict[str, MenuCategory]:
    names = [
        ("Salatlar", 1),
        ("Sho'rvalar", 2),
        ("Issiq taomlar", 3),
        ("Fast-food", 4),
        ("Ichimliklar", 5),
        ("Shirinliklar", 6),
    ]
    categories = {
        name: MenuCategory(name=name, sort_order=order) for name, order in names
    }
    db.add_all(categories.values())
    db.flush()
    return categories


def seed_ingredients(db) -> dict[str, Ingredient]:
    # name -> (uom, min_stock, initial_stock)
    data = {
        "Guruch": ("kg", 10, 60),
        "Mol go'shti": ("kg", 5, 30),
        "Tovuq go'shti": ("kg", 5, 25),
        "Piyoz": ("kg", 5, 20),
        "Sabzi": ("kg", 5, 18),
        "Kartoshka": ("kg", 10, 40),
        "Pomidor": ("kg", 3, 15),
        "Bodring": ("kg", 3, 12),
        "Un": ("kg", 10, 35),
        "Sut": ("l", 5, 20),
        "Tuxum": ("dona", 20, 100),
        "Choy bargi": ("kg", 1, 5),
        "Shakar": ("kg", 3, 15),
        "O'simlik yog'i": ("l", 5, 25),
        "Non": ("dona", 20, 60),
        "Pishloq": ("kg", 2, 8),
        "Limon": ("dona", 10, 40),
        "Mineral suv (idish)": ("dona", 20, 100),
    }

    ingredients = {}
    for name, (uom, min_stock, _stock) in data.items():
        ingredients[name] = Ingredient(name=name, uom=uom, min_stock=min_stock)
    db.add_all(ingredients.values())
    db.flush()

    for name, (_uom, _min_stock, qty) in data.items():
        db.add(IngredientStock(ingredient_id=ingredients[name].id, qty_on_hand=qty))

    return ingredients


def seed_menu(db, categories, ingredients) -> dict[str, MenuItem]:
    # name -> (category, base_price, description, station, recipe[(ingredient, qty)])
    items_data = {
        "Achchiq-chuchuk salat": (
            "Salatlar", 15000, "Pomidor, bodring va piyozdan tayyorlangan yengil salat",
            "Salatlar sexi",
            [("Pomidor", 0.15), ("Bodring", 0.10), ("Piyoz", 0.05)],
        ),
        "Vitamin salat": (
            "Salatlar", 18000, "Sabzi va tuxum bilan tayyorlangan sog'lom salat",
            "Salatlar sexi",
            [("Sabzi", 0.15), ("Tuxum", 1), ("Kartoshka", 0.10)],
        ),
        "Tsezar salat (tovuq bilan)": (
            "Salatlar", 28000, "Tovuq go'shti, pishloq va pomidor bilan Tsezar salat",
            "Salatlar sexi",
            [("Tovuq go'shti", 0.15), ("Pomidor", 0.05), ("Pishloq", 0.05)],
        ),
        "Mastava": (
            "Sho'rvalar", 20000, "Guruch va go'sht bilan an'anaviy sho'rva",
            "Issiq sex",
            [("Guruch", 0.10), ("Mol go'shti", 0.15), ("Kartoshka", 0.10), ("Sabzi", 0.05), ("Piyoz", 0.05)],
        ),
        "Shurpa": (
            "Sho'rvalar", 25000, "Go'sht va sabzavotlar bilan boy sho'rva",
            "Issiq sex",
            [("Mol go'shti", 0.20), ("Kartoshka", 0.15), ("Sabzi", 0.05), ("Piyoz", 0.05), ("Pomidor", 0.05)],
        ),
        "Osh (Palov)": (
            "Issiq taomlar", 35000, "An'anaviy o'zbek oshi",
            "Issiq sex",
            [("Guruch", 0.25), ("Mol go'shti", 0.20), ("Sabzi", 0.15), ("Piyoz", 0.05), ("O'simlik yog'i", 0.05)],
        ),
        "Lag'mon": (
            "Issiq taomlar", 30000, "Qo'lda cho'zilgan xamir va go'shtli sous bilan",
            "Issiq sex",
            [("Un", 0.20), ("Mol go'shti", 0.15), ("Sabzi", 0.05), ("Piyoz", 0.05), ("Pomidor", 0.10)],
        ),
        "Manti": (
            "Issiq taomlar", 28000, "Bug'da pishirilgan go'shtli manti (5 dona)",
            "Issiq sex",
            [("Un", 0.15), ("Mol go'shti", 0.20), ("Piyoz", 0.08)],
        ),
        "Chuchvara": (
            "Issiq taomlar", 26000, "Go'shtli mayda chuchvara sho'rvada",
            "Issiq sex",
            [("Un", 0.10), ("Mol go'shti", 0.12), ("Piyoz", 0.05)],
        ),
        "Norin": (
            "Issiq taomlar", 32000, "Qo'lda tayyorlangan xamir va go'sht bilan sovuq taom",
            "Issiq sex",
            [("Un", 0.15), ("Mol go'shti", 0.20), ("Piyoz", 0.05)],
        ),
        "Tovuq shashlik": (
            "Issiq taomlar", 25000, "Ko'mirda pishirilgan tovuq shashlik (2 shish)",
            "Grill",
            [("Tovuq go'shti", 0.30), ("Piyoz", 0.05)],
        ),
        "Mol go'shti shashlik": (
            "Issiq taomlar", 35000, "Ko'mirda pishirilgan mol go'shti shashlik (2 shish)",
            "Grill",
            [("Mol go'shti", 0.30), ("Piyoz", 0.05)],
        ),
        "Dimlama": (
            "Issiq taomlar", 30000, "Sabzavot va go'sht bilan dimlab pishirilgan taom",
            "Issiq sex",
            [("Kartoshka", 0.20), ("Mol go'shti", 0.20), ("Sabzi", 0.10), ("Piyoz", 0.05), ("Pomidor", 0.10)],
        ),
        "Gamburger": (
            "Fast-food", 22000, "Mol go'shti kotleti, sabzavotlar bilan burger",
            "Fast-food sexi",
            [("Non", 1), ("Mol go'shti", 0.15), ("Pomidor", 0.03), ("Bodring", 0.03), ("Piyoz", 0.02)],
        ),
        "Xot-dog": (
            "Fast-food", 15000, "Klassik xot-dog",
            "Fast-food sexi",
            [("Non", 1), ("Mol go'shti", 0.10), ("Pomidor", 0.02)],
        ),
        "Lavash (tovuq)": (
            "Fast-food", 20000, "Tovuq go'shti va sabzavotlar bilan lavash",
            "Fast-food sexi",
            [("Non", 1), ("Tovuq go'shti", 0.15), ("Pomidor", 0.03), ("Bodring", 0.03), ("Piyoz", 0.02)],
        ),
        "Somsa (qiyma)": (
            "Fast-food", 12000, "Tandirda pishirilgan go'shtli somsa",
            "Fast-food sexi",
            [("Un", 0.10), ("Mol go'shti", 0.12), ("Piyoz", 0.04)],
        ),
        "Somsa (tovuq)": (
            "Fast-food", 12000, "Tandirda pishirilgan tovuqli somsa",
            "Fast-food sexi",
            [("Un", 0.10), ("Tovuq go'shti", 0.12), ("Piyoz", 0.04)],
        ),
        "Qora choy": (
            "Ichimliklar", 8000, "Choynakda tortilgan qora choy",
            "Ichimliklar",
            [("Choy bargi", 0.01)],
        ),
        "Ko'k choy": (
            "Ichimliklar", 8000, "Choynakda tortilgan ko'k choy",
            "Ichimliklar",
            [("Choy bargi", 0.01)],
        ),
        "Limonad": (
            "Ichimliklar", 12000, "Uy sharoitida tayyorlangan limonad",
            "Ichimliklar",
            [("Limon", 1), ("Shakar", 0.03)],
        ),
        "Mineral suv": (
            "Ichimliklar", 6000, "Gazlangan mineral suv",
            "Ichimliklar",
            [("Mineral suv (idish)", 1)],
        ),
        "Napoleon tort": (
            "Shirinliklar", 18000, "Qatlamli krem tort (bo'lak)",
            "Shirinliklar",
            [("Un", 0.08), ("Sut", 0.05), ("Tuxum", 1), ("Shakar", 0.05)],
        ),
        "Muzqaymoq": (
            "Shirinliklar", 12000, "Sut va shakar asosidagi muzqaymoq",
            "Shirinliklar",
            [("Sut", 0.10), ("Shakar", 0.03)],
        ),
    }

    menu_items: dict[str, MenuItem] = {}
    for name, (cat_name, price, desc, station, _recipe) in items_data.items():
        menu_items[name] = MenuItem(
            category_id=categories[cat_name].id,
            name=name,
            description=desc,
            base_price=price,
            station=station,
            is_active=True,
        )
    db.add_all(menu_items.values())
    db.flush()

    for name, (_cat, _price, _desc, _station, recipe) in items_data.items():
        for ingredient_name, qty in recipe:
            db.add(
                MenuIngredient(
                    menu_item_id=menu_items[name].id,
                    ingredient_id=ingredients[ingredient_name].id,
                    qty_required=qty,
                )
            )

    # Ba'zi taomlarga variant (o'lcham/qo'shimcha) qo'shamiz
    variants = [
        ("Osh (Palov)", "Katta porsiya", 8000),
        ("Tovuq shashlik", "3 shish", 8000),
        ("Mol go'shti shashlik", "3 shish", 10000),
        ("Lavash (tovuq)", "Katta", 5000),
        ("Qora choy", "Katta choynak", 4000),
        ("Ko'k choy", "Katta choynak", 4000),
    ]
    for item_name, variant_name, delta in variants:
        db.add(
            MenuItemVariant(
                menu_item_id=menu_items[item_name].id,
                name=variant_name,
                price_delta=delta,
                is_active=True,
            )
        )

    return menu_items


def seed_orders(db, users, tables, menu_items):
    now = datetime.now()

    # --- Order 1: to'liq yakunlangan (yopilgan, to'langan) ---
    order1 = Order(
        table_id=tables["1"].id,
        waiter_id=users["aziz"].id,
        status="closed",
        opened_at=now - timedelta(hours=2),
        submitted_at=now - timedelta(hours=1, minutes=50),
        closed_at=now - timedelta(hours=1),
    )
    db.add(order1)
    db.flush()

    osh = menu_items["Osh (Palov)"]
    choy = menu_items["Qora choy"]
    db.add_all(
        [
            OrderItem(
                order_id=order1.id,
                menu_item_id=osh.id,
                qty=2,
                unit_price=osh.base_price,
                status="served",
                sent_at=now - timedelta(hours=1, minutes=50),
                ready_at=now - timedelta(hours=1, minutes=30),
                served_at=now - timedelta(hours=1, minutes=25),
            ),
            OrderItem(
                order_id=order1.id,
                menu_item_id=choy.id,
                qty=1,
                unit_price=choy.base_price,
                status="served",
                sent_at=now - timedelta(hours=1, minutes=50),
                ready_at=now - timedelta(hours=1, minutes=48),
                served_at=now - timedelta(hours=1, minutes=45),
            ),
        ]
    )
    total1 = 2 * osh.base_price + choy.base_price
    db.add(
        Payment(
            order_id=order1.id,
            cashier_id=users["shahnoza"].id,
            method="cash",
            amount=total1,
            paid_at=now - timedelta(hours=1, minutes=5),
            receipt_no="RCPT-DEMO0001",
        )
    )

    # --- Order 2: oshxonaga yuborilgan, hali to'lanmagan ---
    order2 = Order(
        table_id=tables["3"].id,
        waiter_id=users["malika"].id,
        status="submitted",
        opened_at=now - timedelta(minutes=30),
        submitted_at=now - timedelta(minutes=20),
    )
    db.add(order2)
    tables["3"].status = "occupied"
    db.flush()

    lagmon = menu_items["Lag'mon"]
    limonad = menu_items["Limonad"]
    db.add_all(
        [
            OrderItem(
                order_id=order2.id,
                menu_item_id=lagmon.id,
                qty=1,
                unit_price=lagmon.base_price,
                status="preparing",
                sent_at=now - timedelta(minutes=20),
            ),
            OrderItem(
                order_id=order2.id,
                menu_item_id=limonad.id,
                qty=2,
                unit_price=limonad.base_price,
                status="ready",
                sent_at=now - timedelta(minutes=20),
                ready_at=now - timedelta(minutes=10),
            ),
        ]
    )

    # --- Order 3: hali ochiq, oshxonaga yuborilmagan ---
    order3 = Order(
        table_id=tables["5"].id,
        waiter_id=users["aziz"].id,
        status="open",
        opened_at=now - timedelta(minutes=5),
    )
    db.add(order3)
    tables["5"].status = "occupied"
    db.flush()

    tsezar = menu_items["Tsezar salat (tovuq bilan)"]
    db.add(
        OrderItem(
            order_id=order3.id,
            menu_item_id=tsezar.id,
            qty=1,
            unit_price=tsezar.base_price,
            status="new",
        )
    )

    # Bitta stolni "band" (reserved) holatida ko'rsatish uchun
    tables["7"].status = "reserved"

    db.flush()
    return {"order1": order1, "order2": order2, "order3": order3, "total1": total1}


def seed_audit_log(db, users, order_ctx):
    db.add_all(
        [
            AuditLog(
                user_id=users["admin"].id,
                entity="User",
                entity_id=users["aziz"].id,
                action="user_created",
                meta={"role": "waiter", "created_by": "admin"},
            ),
            AuditLog(
                user_id=users["aziz"].id,
                entity="Order",
                entity_id=order_ctx["order1"].id,
                action="order_closed",
                meta={"total_amount": order_ctx["total1"]},
            ),
            AuditLog(
                user_id=users["shahnoza"].id,
                entity="Payment",
                entity_id=order_ctx["order1"].id,
                action="payment_created",
                meta={"amount": order_ctx["total1"], "method": "cash"},
            ),
        ]
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--yes", action="store_true", help="Tasdiqlashsiz ishga tushirish (baza tozalanadi!)"
    )
    args = parser.parse_args()

    if not args.yes:
        answer = input(
            "OGOHLANTIRISH: bu amal bazadagi barcha ma'lumotlarni o'chirib, "
            "demo ma'lumotlar bilan almashtiradi. Davom etasizmi? [y/N]: "
        )
        if answer.strip().lower() != "y":
            print("Bekor qilindi.")
            sys.exit(0)

    db = SessionLocal()
    try:
        wipe_tables(db)

        users = seed_users(db)
        tables = seed_tables(db)
        categories = seed_categories(db)
        ingredients = seed_ingredients(db)
        menu_items = seed_menu(db, categories, ingredients)
        order_ctx = seed_orders(db, users, tables, menu_items)
        seed_audit_log(db, users, order_ctx)

        db.commit()
        print("Demo ma'lumotlar muvaffaqiyatli joylandi.")
        print(f"  Foydalanuvchilar: {len(users)} (parol: <username>123, masalan admin123)")
        print(f"  Stollar: {len(tables)}")
        print(f"  Kategoriyalar: {len(categories)}")
        print(f"  Ingredientlar: {len(ingredients)}")
        print(f"  Menyu bandlari: {len(menu_items)}")
        print("  Namuna buyurtmalar: 1 yopilgan/to'langan, 1 oshxonada, 1 ochiq")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
