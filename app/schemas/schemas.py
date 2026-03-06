from pydantic import BaseModel
from enum import Enum


class UserProfileResponse(BaseModel):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None


class UserLoginRequest(BaseModel):
    username: str | None = None
    password: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserUploadRequest(BaseModel):
    pass


from pydantic import BaseModel


class TableBase(BaseModel):
    table_no: str
    capacity: int
    status: str


class TableCreate(TableBase):
    pass


class TableRead(TableBase):
    id: int

class TableStatusChoise(str,Enum):
    FREE="free"
    OCCUPIED="occupied"
    REVERSED="reversed"




class MenuCategoryRead(BaseModel):
    id: int
    name: str
    sort_order: int

    model_config = {"from_attributes": True}




class MenuItemVariantRead(BaseModel):
    id: int
    name: str
    price_delta: float
    is_active: bool

    model_config = {"from_attributes": True}


class MenuItemRead(BaseModel):
    id: int
    name: str
    description: str
    base_price: float
    station: str
    is_active: bool
    category_id: int | None
    img_id: int | None 
    variants: list[MenuItemVariantRead] = []

    model_config = {"from_attributes": True}


class OrderRead(BaseModel):
    id: int | None = None
    waiter_id: int | None = None
    table_id: int | None = None
