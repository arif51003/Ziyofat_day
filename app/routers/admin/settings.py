from starlette_admin.contrib.sqla import Admin

from app.database import engine
from app.models import User
from .views import UserAdminView

admin=Admin(
    engine=engine,
    title="ZIYOFAT ADMIN",
    base_url="/admin"
    
)

admin.add_view(UserAdminView(User,icon="fa fa-user"))