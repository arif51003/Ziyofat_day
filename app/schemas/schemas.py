from pydantic import BaseModel


class TableBase(BaseModel):
    table_no: str
    capacity: int
    status: str


class TableCreate(TableBase):
    pass  # Admin CRUD uchun kerak bo‘lsa


class TableRead(TableBase):
    id: int


class UserProfileResponse(BaseModel):
    username: str |None =None
    first_name:str | None = None
    last_name:str | None = None
    avatar_url:str | None = None
    
    
class UserLoginRequest(BaseModel):
    username:str | None = None
    password:str | None = None
    
    
class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
    
class UserUploadRequest(BaseModel):
    pass


from pydantic import BaseModel


# ───── TABLE ─────────────────────────────────────
class TableBase(BaseModel):
    table_no: str
    capacity: int
    status: str


class TableCreate(TableBase):
    pass


class TableRead(TableBase):
    id: int

    model_config = {"from_attributes": True}


# ───── MENU CATEGORY ─────────────────────────────
class MenuCategoryCreate(BaseModel):
    name: str
    sort_order: int = 0


class MenuCategoryUpdate(BaseModel):
    name: str | None = None
    sort_order: int | None = None


class MenuCategoryRead(BaseModel):
    id: int
    name: str
    sort_order: int

    model_config = {"from_attributes": True}


# ───── MENU ITEM VARIANT ─────────────────────────
class MenuItemVariantCreate(BaseModel):
    name: str
    price_delta: float = 0.0
    is_active: bool = True


class MenuItemVariantRead(BaseModel):
    id: int
    name: str
    price_delta: float
    is_active: bool

    model_config = {"from_attributes": True}


# ───── MENU ITEM ─────────────────────────────────
class MenuItemCreate(BaseModel):
    name: str
    description: str
    base_price: float
    station: str                 # "kitchen" | "bar" | "grill"
    category_id: int | None = None
    is_active: bool = True
    # img_id admin panel orqali yuklanadi, API dan kelmaydi


class MenuItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    base_price: float | None = None
    station: str | None = None
    category_id: int | None = None
    is_active: bool | None = None


class MenuItemRead(BaseModel):
    id: int
    name: str
    description: str
    base_price: float
    station: str
    is_active: bool
    category_id: int | None
    img_id: int | None          # rasm ID — frontend /static/uploads/ orqali oladi
    variants: list[MenuItemVariantRead] = []

    model_config = {"from_attributes": True}