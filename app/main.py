from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import (
    login_router,
    waiter_router,
    user_router,
    cashier_router,
    kitchen_router
    
)

# from app.middleware.dbmiddleware import DBSessionMiddleware
from app.admin.settings import admin

app = FastAPI(title="ZIYOFAT-DAY")


app.include_router(login_router)
app.include_router(user_router)
app.include_router(cashier_router)
app.include_router(waiter_router)
app.include_router(kitchen_router)



admin.mount_to(app=app)


app.mount("/static", StaticFiles(directory="media_uploads"), name="uploads")
