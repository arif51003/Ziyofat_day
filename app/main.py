from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

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

# Frontend is served by this same app (see the static mounts and SPA
# fallback route below), so requests are same-origin and CORS isn't needed.

app.include_router(login_router)
app.include_router(user_router)
app.include_router(cashier_router)
app.include_router(waiter_router)
app.include_router(kitchen_router)



admin.mount_to(app=app)


# Mount static files
app.mount("/static", StaticFiles(directory="media_uploads"), name="uploads")

# Serve frontend assets
try:
    app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
    app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
except Exception as e:
    print(f"Warning: Could not mount frontend static files: {e}")

# Serve index.html for all non-API routes (SPA support)
# This must be last so API routes are matched first
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve index.html for SPA routing"""
    # Skip API routes
    api_prefixes = ["login", "waiter", "kitchen", "cashier", "user", "admin", "static"]
    if any(full_path.startswith(p) for p in api_prefixes):
        return {"detail": "Not found"}
    
    frontend_path = f"frontend/{full_path}"
    
    # Try to serve actual file if it exists
    if full_path and os.path.exists(frontend_path) and os.path.isfile(frontend_path):
        if full_path.endswith('.css'):
            return FileResponse(frontend_path, media_type="text/css")
        elif full_path.endswith('.js'):
            return FileResponse(frontend_path, media_type="application/javascript")
        elif full_path.endswith('.html'):
            return FileResponse(frontend_path, media_type="text/html")
        return FileResponse(frontend_path)
    
    # Default to index.html for SPA client-side routing
    return FileResponse("frontend/index.html", media_type="text/html")
