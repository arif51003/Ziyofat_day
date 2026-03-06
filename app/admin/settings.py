from starlette_admin.contrib.sqla import Admin

from app.database import engine
from app.models import (
    User,
    MenuCategory,
    MenuItem,
    DiningTable,
    Payment,
    Order,
    OrderItem,
    AuditLog,
    MenuItemVariant,
    Ingredient,
    MenuIngredient,
    IngredientStock,
    StockMovements
)
from .views import (
    UserAdminView,
    MenuCategoryView,
    MenuItemView,
    TableViews,
    PaymentView,
    OrdersView,
    OrderItemView,
    MenuVariantView,
    AuditLogView,
    IngredientsView,
    MenuIngredientsView,
    IngredientStockView,
    StockMovementsView
)
from app.admin.auth import JSONAuthProvider

admin = Admin(
    engine=engine,
    title="ZIYOFAT ADMIN",
    base_url="/admin",
    auth_provider=JSONAuthProvider(login_path="/login", logout_path="/logout"),
)

admin.add_view(UserAdminView(User, icon="fa fa-users"))
admin.add_view(MenuCategoryView(MenuCategory, icon="fa fa-list"))
admin.add_view(MenuItemView(MenuItem, icon="fa fa-utensils"))
admin.add_view(TableViews(DiningTable, icon="fa fa-chair"))
admin.add_view(PaymentView(Payment, icon="fa fa-usd"))
admin.add_view(OrdersView(Order, icon="fa fa-shopping-basket"))
admin.add_view(OrderItemView(OrderItem, icon="fa fa-coffee"))
admin.add_view(MenuVariantView(MenuItemVariant, icon="fa fa-tasks"))
admin.add_view(AuditLogView(AuditLog, icon="fa fa-camera"))
admin.add_view(MenuIngredientsView(MenuIngredient))
admin.add_view(IngredientsView(Ingredient))
admin.add_view(IngredientStockView(IngredientStock))
admin.add_view(StockMovementsView(StockMovements))