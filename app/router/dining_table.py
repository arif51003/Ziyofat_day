from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.models import DiningTable
from app.database import db_dep
from app.schemas import TableRead

router = APIRouter(prefix="/tables", tags=["Tables"])

@router.get("/", response_model=list[TableRead])
async def get_tables(session: db_dep, status: str | None = None):
    stmt = select(DiningTable)
    if status:
        stmt = stmt.where(DiningTable.status == status)
    res = session.execute(stmt)
    return res.scalars().all()

@router.get("/{table_id}/", response_model=TableRead)
async def get_table(session: db_dep, table_id: int):
    stmt = select(DiningTable).where(DiningTable.id == table_id)
    res = session.execute(stmt)
    table = res.scalars().first()

    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    return table

@router.post("/{table_id}/reserve/")
async def reserve_table(session: db_dep, table_id: int):
    stmt = select(DiningTable).where(DiningTable.id == table_id)
    res = session.execute(stmt)
    table = res.scalars().first()

    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    if table.status != "free":
        raise HTTPException(status_code=400, detail="Table is not free")
    
    table.status = "reserved"
    session.commit()
    session.refresh(table)
    return table

@router.post("/{table_id}/occupy/")
async def occupy_table(session: db_dep, table_id: int):
    stmt = select(DiningTable).where(DiningTable.id == table_id)
    res = session.execute(stmt)
    table = res.scalars().first()

    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    if table.status == "occupied":
        raise HTTPException(status_code=400, detail="Table is already occupied")
    
    table.status = "occupied"
    session.commit()
    session.refresh(table)
    return table

@router.post("/{table_id}/release/")
async def release_table(session: db_dep, table_id: int):
    stmt = select(DiningTable).where(DiningTable.id == table_id)
    res = session.execute(stmt)
    table = res.scalars().first()

    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    
    table.status = "free"
    session.commit()
    session.refresh(table)
    return table