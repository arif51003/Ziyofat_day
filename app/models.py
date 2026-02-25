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

    username: Mapped[str] = mapped_column(String, unique=True)
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String)
    avatar_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("media.id", ondelete="SET NULL"), nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="waiter")
    avatar: Mapped["Media"] = relationship("Media", foreign_keys=[avatar_id])


class DiningTable(BaseModel):
    __tablename__ = "dining_table"

    table_no: Mapped[str] = mapped_column(String, unique=True)
    capacity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String)

    orders = relationship("Order", back_populates="table")


class MenuCategory(BaseModel):
    __tablename__ = "menu_category"

    name: Mapped[str] = mapped_column(String)
    sort_order: Mapped[int] = mapped_column(Integer)

    items = relationship("MenuItem", back_populates="category")
    
    def __admin_repr__(self, request: Request):
        return self.name


class MenuItem(BaseModel):
    __tablename__ = "menu_item"

    category_id: Mapped[int] = mapped_column(ForeignKey("menu_category.id"),nullable=True)
    name: Mapped[str] = mapped_column(String)
    img_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("media.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(String)
    base_price: Mapped[float] = mapped_column(Numeric)
    station: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category = relationship("MenuCategory", back_populates="items")
    variants = relationship("MenuItemVariant", back_populates="menu_item")
    img: Mapped["Media"] = relationship("Media", foreign_keys=[img_id])


class MenuItemVariant(BaseModel):
    __tablename__ = "menu_item_variant"

    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_item.id"))
    name: Mapped[str] = mapped_column(String)
    price_delta: Mapped[float] = mapped_column(Numeric)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    menu_item = relationship("MenuItem", back_populates="variants")


class Order(BaseModel):
    __tablename__ = "orders"

    table_id: Mapped[int] = mapped_column(ForeignKey("dining_table.id"))
    waiter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String)
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_item.id"))
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("menu_item_variant.id"), nullable=True
    )
    qty: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Numeric)
    status: Mapped[str] = mapped_column(String)
    note: Mapped[str] = mapped_column(String, nullable=True)

    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    ready_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    served_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    order = relationship("Order", back_populates="items")
    modifiers = relationship("OrderItemModifier", back_populates="order_item")


class OrderItemModifier(BaseModel):
    __tablename__ = "order_item_modifier"

    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_item.id"))
    name: Mapped[str] = mapped_column(String)
    price_delta: Mapped[float] = mapped_column(Numeric)

    order_item = relationship("OrderItem", back_populates="modifiers")


class Payment(BaseModel):
    __tablename__ = "payment"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    cashier_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    method: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Numeric)
    paid_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    receipt_no: Mapped[str] = mapped_column(String, unique=True)

    order = relationship("Order", back_populates="payments")


class AuditLog(BaseModel):
    __tablename__ = "audit_log"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    entity: Mapped[str] = mapped_column(String)
    entity_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String)
    meta: Mapped[dict] = mapped_column(JSON)


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    url: Mapped[str] = mapped_column(String)
