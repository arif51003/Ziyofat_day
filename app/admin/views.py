import os
import uuid
from typing import Any, Dict
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView
from starlette.datastructures import UploadFile
from starlette_admin.fields import FileField, EnumField
from app.utils import hash_password
from app.models import Media


UPLOAD_DIR = "media_uploads"


def looks_hashed(p: str):
    return p.startswith("$argon2")


class UserAdminView(ModelView):
    fields = [
        "id",
        "username",
        "first_name",
        "last_name",
        "password_hash",
        "role",
        FileField("img_file", label="Avatar"),
        "created_at",
        "updated_at",
        "is_active",
        "is_admin",
        "is_deleted",
    ]
    exclude_fields_from_list = [
        "id",
        "username",
        "password_hash",
        "created_at",
        "is_deleted",
        "updated_at",
    ]
    exclude_fields_from_create = [
        "id",
        "avatar_id",
        "is_deleted",
        "created_at",
        "updated_at",
    ]
    exclude_fields_from_edit = ["id", "avatar_id", "created_at", "updated_at"]

    async def before_create(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        pwd = data.get("password_hash")
        if pwd and not looks_hashed(pwd):
            obj.password_hash = hash_password(pwd)  # ASOSIY FIX

        session = request.state.session

        up: UploadFile | None = extract_upload(data.get("img_file"))
        if up:
            os.makedirs(UPLOAD_DIR, exist_ok=True)

            filename = f"{uuid.uuid4().hex}{_safe_ext(up.filename)}"
            path = os.path.join(UPLOAD_DIR, filename)

            content = await up.read()
            with open(path, "wb") as f:
                f.write(content)

            # BU URL app.mount(...) ga mos bo‘lishi shart
            url = f"/{UPLOAD_DIR}/{filename}"

            media = Media(url=url)
            session.add(media)
            session.flush([media])  # media.id olish uchun

            obj.avatar_id = media.id

        data.pop("img_file", None)

    async def before_edit(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        if "password_hash" in data:
            pwd = data.get("password_hash")
            if not pwd:
                return  # bo‘sh bo‘lsa o‘zgartirmaydi
            if not looks_hashed(pwd):
                obj.password_hash = hash_password(pwd)

        session = request.state.session

        up: UploadFile | None = extract_upload(data.get("img_file"))
        if up:
            os.makedirs(UPLOAD_DIR, exist_ok=True)

            filename = f"{uuid.uuid4().hex}{_safe_ext(up.filename)}"
            path = os.path.join(UPLOAD_DIR, filename)

            content = await up.read()
            with open(path, "wb") as f:
                f.write(content)

            url = f"/{UPLOAD_DIR}/{filename}"

            media = Media(url=url)
            session.add(media)
            session.flush([media])

            obj.avatar_id = media.id

        data.pop("img_file", None)


def extract_upload(v) -> UploadFile | None:
    if v is None:
        return None
    if isinstance(v, UploadFile):
        return v
    if isinstance(v, tuple):
        for item in v:
            if isinstance(item, UploadFile):
                return item
    return None


class MenuCategoryView(ModelView):
    fields = ["id", "name", "sort_order", "created_at", "updated_at"]
    exclude_fields_from_create = ["id", "created_at", "updated_at"]
    exclude_fields_from_edit = ["id", "created_at", "updated_at"]
    exclude_fields_from_detail = ["id", "sort_order", "created_at", "updated_at"]


def _safe_ext(filename: str) -> str:
    _, ext = os.path.splitext(filename or "")
    return ext.lower()[:10] if ext else ""


class MenuItemView(ModelView):
    fields = [
        "id",
        "name",
        "category",  # <-- shu dropdown chiqadi
        FileField("img_file", label="Image file"),
        "station",
        "base_price",
        "description",
        "is_active",
        "created_at",
        "updated_at",
    ]

    exclude_fields_from_create = ["id", "updated_at", "created_at"]
    exclude_fields_from_edit = ["id", "updated_at", "created_at"]
    exclude_fields_from_detail = [
        "id",
        "station",
        "base_price",
        "description",
        "is_active",
        "created_at",
        "updated_at",
    ]

    async def before_create(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        session = request.state.session

        # category -> category_id
        cat = data.get("category")
        if cat is not None:
            obj.category_id = cat.id if hasattr(cat, "id") else int(cat)

        # file upload
        up: UploadFile | None = extract_upload(data.get("img_file"))
        if up:
            os.makedirs(UPLOAD_DIR, exist_ok=True)

            filename = f"{uuid.uuid4().hex}{_safe_ext(up.filename)}"
            path = os.path.join(UPLOAD_DIR, filename)

            content = await up.read()
            with open(path, "wb") as f:
                f.write(content)

            # BU URL app.mount(...) ga mos bo‘lishi shart
            url = f"/{UPLOAD_DIR}/{filename}"

            media = Media(url=url)
            session.add(media)
            session.flush([media])  # media.id olish uchun

            obj.img_id = media.id

        data.pop("img_file", None)

    async def before_edit(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        session = request.state.session

        # category -> category_id (agar editda category o'zgartirilsa)
        if "category" in data:
            cat = data.get("category")
            if cat is not None:
                obj.category_id = cat.id if hasattr(cat, "id") else int(cat)

        # file upload (agar yangi rasm yuklansa)
        up: UploadFile | None = extract_upload(data.get("img_file"))
        if up:
            os.makedirs(UPLOAD_DIR, exist_ok=True)

            filename = f"{uuid.uuid4().hex}{_safe_ext(up.filename)}"
            path = os.path.join(UPLOAD_DIR, filename)

            content = await up.read()
            with open(path, "wb") as f:
                f.write(content)

            url = f"/{UPLOAD_DIR}/{filename}"

            media = Media(url=url)
            session.add(media)
            session.flush([media])

            obj.img_id = media.id

        data.pop("img_file", None)


class TableViews(ModelView):
    fields = [
        "id",
        "table_no",
        "capacity",
        EnumField(
            "status",
            choices=[
                ("free", "Free"),
                ("occupied", "Occupied"),
                ("reversed", "Reversed"),
            ],
        ),
        "created_at",
        "updated_at",
    ]
    exclude_fields_from_create = ["updated_at", "created_at", "id", "status"]
    exclude_fields_from_edit = ["updated_at", "created_at", "id"]
    exclude_fields_from_list = ["updated_at", "created_at", "id"]


class PaymentView(ModelView):
    fields = [
        "id",
        "order",
        "cashier_id",
        "method",
        "paid_at",
        "receipt_no",
        "created_at",
        "updated_at",
    ]
    exclude_fields_from_list = [
        "id",
        "updated_at",
    ]


class OrdersView(ModelView):
    pass


class OrderItemView(ModelView):
    pass


class MenuVariantView(ModelView):
    pass


class AuditLogView(ModelView):
    pass

class IngredientsView(ModelView):
    pass

class MenuIngredientsView(ModelView):
    pass

class IngredientStockView(ModelView):
    pass

class StockMovementsView(ModelView):
    pass