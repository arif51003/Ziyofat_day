from starlette_admin.contrib.sqla import ModelView

class UserAdminView(ModelView):
    fields=[
        "id",
        "username",
        "first_name",
        "last_name",
        "password_hash",
        "role",
        "created_at",
        "updated_at",
        "is_active",
        "is_admin",
        "is_deleted"
    ]
    exclude_fields_from_list=[
        "id",
        "username",
        "password_hash",
        "created_at",
        "is_deleted",
        "updated_at"
    ]