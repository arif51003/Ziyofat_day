from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers import (
    login_router,
    waiter_router,
    user_router,
    cashier_router,
    kitchen_router,
    reports_router,
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
app.include_router(reports_router)



admin.mount_to(app=app)


# Mount static files
app.mount("/static", StaticFiles(directory="media_uploads"), name="uploads")

# Serve frontend assets
try:
    app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
    app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
except Exception as e:
    print(f"Warning: Could not mount frontend static files: {e}")

FRONTEND_DIR = Path("frontend").resolve()

# Serve index.html for all non-API routes (SPA support)
# This must be last so API routes are matched first
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve index.html for SPA routing"""
    # Skip API routes
    api_prefixes = ["auth", "waiter", "kitchen", "cashier", "user", "admin", "static", "reports"]
    if any(full_path.startswith(p) for p in api_prefixes):
        return {"detail": "Not found"}

    # Resolve against FRONTEND_DIR and confirm the result is still inside it,
    # so "../.env" or similar can't escape the frontend directory.
    requested_path = (FRONTEND_DIR / full_path).resolve() if full_path else None

    if (
        requested_path is not None
        and requested_path.is_relative_to(FRONTEND_DIR)
        and requested_path.is_file()
    ):
        if full_path.endswith('.css'):
            return FileResponse(requested_path, media_type="text/css")
        elif full_path.endswith('.js'):
            return FileResponse(requested_path, media_type="application/javascript")
        elif full_path.endswith('.html'):
            return FileResponse(requested_path, media_type="text/html")
        return FileResponse(requested_path)

    # Default to index.html for SPA client-side routing
    return FileResponse(FRONTEND_DIR / "index.html", media_type="text/html")
