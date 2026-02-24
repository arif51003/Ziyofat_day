from fastapi import FastAPI
from app.routers import table_router, admin

app=FastAPI(
    title="ZIYOFAT-DAY"
)

app.include_router(table_router)

admin.mount_to(app=app)