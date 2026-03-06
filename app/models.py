from datetime import datetime
from fastapi import Request
from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Numeric,
    DateTime,
    Float,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    role: Mapped[str] = mapped_column(String(20))
    avatar_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("media.id", ondelete="SET NULL"), nullable=True
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="waiter")
    avatar: Mapped["Media"] = relationship("Media", foreign_keys=[avatar_id])
    stock_movements:Mapped["StockMovements"]=relationship("StockMovements",back_populates="user")

class DiningTable(BaseModel):
    __tablename__ = "dining_table"

    table_no: Mapped[str] = mapped_column(String(3), unique=True)
    capacity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), nullable=True, default="free")

    orders = relationship("Order", back_populates="table")


class MenuCategory(BaseModel):
    __tablename__ = "menu_category"

    name: Mapped[str] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(Integer)

    items = relationship("MenuItem", back_populates="category")

    def __admin_repr__(self, request: Request):
        return self.name


class MenuItem(BaseModel):
    __tablename__ = "menu_item"

    category_id: Mapped[int] = mapped_column(
        ForeignKey("menu_category.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(50))
    img_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("media.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(String(100))
    base_price: Mapped[int] = mapped_column(BigInteger)
    station: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category = relationship("MenuCategory", back_populates="items")
    variants = relationship("MenuItemVariant", back_populates="menu_item")
    img: Mapped["Media"] = relationship("Media", foreign_keys=[img_id])
    ingredients:Mapped[list["MenuIngredient"]] = relationship("MenuIngredient",back_populates="menu_item")

class MenuItemVariant(BaseModel):
    __tablename__ = "menu_item_variant"

    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_item.id"))
    name: Mapped[str] = mapped_column(String(50))
    price_delta: Mapped[int] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    menu_item = relationship("MenuItem", back_populates="variants")


class Order(BaseModel):
    __tablename__ = "orders"

    table_id: Mapped[int] = mapped_column(ForeignKey("dining_table.id"))
    waiter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20))
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(String, nullable=True)

    table = relationship("DiningTable", back_populates="orders")
    waiter = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    payments = relationship("Payment", back_populates="order")


class OrderItem(BaseModel):
    __tablename__ = "order_item"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_item.id"))
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("menu_item_variant.id"), nullable=True
    )
    qty: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(String, nullable=True)

    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    ready_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    served_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    order = relationship("Order", back_populates="items")




class Payment(BaseModel):
    __tablename__ = "payment"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    cashier_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    method: Mapped[str] = mapped_column(String(10))
    amount: Mapped[int] = mapped_column(BigInteger)
    paid_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    receipt_no: Mapped[str] = mapped_column(String(50), unique=True)

    order = relationship("Order", back_populates="payments")


class AuditLog(BaseModel):
    __tablename__ = "audit_log"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    entity: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(100))
    meta: Mapped[dict] = mapped_column(JSON)


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    url: Mapped[str] = mapped_column(String(150))


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    token: Mapped[str] = mapped_column(String(200), primary_key=True)


class Ingredient(BaseModel):
    __tablename__="ingredients"
    
    name:Mapped[str]= mapped_column(String(50))
    uom:Mapped[str]=mapped_column(String(10))
    min_stock:Mapped[int]= mapped_column(BigInteger)
    is_active:Mapped[bool] = mapped_column(Boolean,default=True)
    
    menu_ingredients: Mapped[list["MenuIngredient"]] = relationship(
        back_populates="ingredient"
    )

    stock: Mapped["IngredientStock"] = relationship(
        back_populates="ingredient"
    )

    stock_movements: Mapped[list["StockMovements"]] = relationship(
        back_populates="ingredient"
    )
    
    def __repr__(self):
        return self.name
    

class MenuIngredient(BaseModel):
    __tablename__="menu_ingredient"
    
    menu_item_id:Mapped[int] = mapped_column(ForeignKey("menu_item.id"))
    ingredient_id:Mapped[int] = mapped_column(ForeignKey("ingredients.id"))
    qty_required:Mapped[float] = mapped_column(Float)
    
    ingredient: Mapped["Ingredient"] = relationship(
        back_populates="menu_ingredients"
    )

    menu_item = relationship("MenuItem", back_populates="ingredients")
    
    def __repr__(self):
        return f"{self.menu_item_id} {self.ingredient_id}"
    

class IngredientStock(BaseModel):
    __tablename__="ingredient_stock"
    
    ingredient_id:Mapped[int] = mapped_column(ForeignKey("ingredients.id"),unique=True)
    qty_on_hand:Mapped[float] = mapped_column(Float)
    
    ingredient: Mapped["Ingredient"] = relationship(
        back_populates="stock"
    )
    
    def __repr__(self):
        return f"{self.ingredient_id} {self.qty_on_hand}"
    
    
class StockMovements(BaseModel):
    __tablename__="stock_movements"
    
    ingredient_id:Mapped[int] = mapped_column(ForeignKey("ingredients.id"))
    status:Mapped[str] = mapped_column(String(5))
    qty:Mapped[float] = mapped_column(Float)
    created_by:Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    ingredient: Mapped["Ingredient"] = relationship(
        back_populates="stock_movements"
    )

    user: Mapped["User"] = relationship(
    "User",
    back_populates="stock_movements"
)
    
    def __repr__(self):
        return f"{self.created_by} {self.ingredient_id}"