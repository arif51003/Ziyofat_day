from pydantic import BaseModel

class TableBase(BaseModel):
    table_no: str
    capacity: int
    status: str

class TableCreate(TableBase):
    pass  # Admin CRUD uchun kerak bo‘lsa

class TableRead(TableBase):
    id: int
    class Config:
        orm_mode = True