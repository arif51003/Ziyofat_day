from datetime import datetime
from sqlalchemy import BigInteger, Integer, String, Boolean, ForeignKey, Numeric, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    full_name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    password_hash: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    orders = relationship("Order", back_populates="waiter")


class DiningTable(Base):
    __tablename__ = "dining_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_no: Mapped[str] = mapped_column(String, unique=True)
    capacity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String)

    orders = relationship("Order", back_populates="table")


class MenuCategory(Base):
    __tablename__ = "menu_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    sort_order: Mapped[int] = mapped_column(Integer)

    items = relationship("MenuItem", back_populates="category")


class MenuItem(Base):
    __tablename__ = "menu_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("menu_category.id"))
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    base_price: Mapped[float] = mapped_column(Numeric)
    station: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category = relationship("MenuCategory", back_populates="items")
    variants = relationship("MenuItemVariant", back_populates="menu_item")


class MenuItemVariant(Base):
    __tablename__ = "menu_item_variant"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_item.id"))
    name: Mapped[str] = mapped_column(String)
    price_delta: Mapped[float] = mapped_column(Numeric)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    menu_item = relationship("MenuItem", back_populates="variants")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("dining_table.id"))
    waiter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String)
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(String, nullable=True)

    table = relationship("DiningTable", back_populates="orders")
    waiter = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    payments = relationship("Payment", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_item.id"))
    variant_id: Mapped[int] = mapped_column(ForeignKey("menu_item_variant.id"), nullable=True)
    qty: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Numeric)
    status: Mapped[str] = mapped_column(String)
    note: Mapped[str] = mapped_column(String, nullable=True)


    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    ready_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    served_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    order = relationship("Order", back_populates="items")
    modifiers = relationship("OrderItemModifier", back_populates="order_item")


class OrderItemModifier(Base):
    __tablename__ = "order_item_modifier"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_item.id"))
    name: Mapped[str] = mapped_column(String)
    price_delta: Mapped[float] = mapped_column(Numeric)

    order_item = relationship("OrderItem", back_populates="modifiers")


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    cashier_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    method: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Numeric)
    paid_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    receipt_no: Mapped[str] = mapped_column(String, unique=True)

    order = relationship("Order", back_populates="payments")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    entity: Mapped[str] = mapped_column(String)
    entity_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String)
    meta: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
