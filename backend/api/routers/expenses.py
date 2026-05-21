from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel
from datetime import date
from typing import Optional
import calendar
from api.db import get_admin_client as get_client
from api.services.auth_helper import require_user

router = APIRouter()


class ExpenseIn(BaseModel):
    date: date
    amount: float
    category: str
    description: str
    payment_method: str = "UPI"
    source: str = ""


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None


@router.get("/")
async def list_expenses(
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    authorization: str = Header(...),
):
    user_id = await require_user(authorization)
    client  = get_client()
    q = client.table("expenses").select("*").eq("user_id", user_id)
    if month and year:
        last_day = calendar.monthrange(year, month)[1]
        from_d   = f"{year}-{month:02d}-01"
        to_d     = f"{year}-{month:02d}-{last_day:02d}"
        q = q.gte("date", from_d).lte("date", to_d)
    if category:
        q = q.eq("category", category)
    if source:
        q = q.eq("source", source)
    result = q.order("date", desc=True).execute()
    return result.data


@router.post("/", status_code=201)
async def create_expense(body: ExpenseIn, authorization: str = Header(...)):
    user_id = await require_user(authorization)
    client  = get_client()
    row = {**body.model_dump(), "date": str(body.date), "user_id": user_id}
    result = client.table("expenses").insert(row).execute()
    return result.data[0]


@router.patch("/{expense_id}")
async def update_expense(expense_id: str, body: ExpenseUpdate, authorization: str = Header(...)):
    user_id = await require_user(authorization)
    client  = get_client()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    result  = (
        client.table("expenses")
        .update(updates)
        .eq("id", expense_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Expense not found")
    return result.data[0]


@router.delete("/{expense_id}", status_code=204)
async def delete_expense(expense_id: str, authorization: str = Header(...)):
    user_id = await require_user(authorization)
    client  = get_client()
    client.table("expenses").delete().eq("id", expense_id).eq("user_id", user_id).execute()


@router.delete("/batch/by-source")
async def delete_by_source(source: str = Query(...), authorization: str = Header(...)):
    user_id = await require_user(authorization)
    client  = get_client()
    result = (
        client.table("expenses")
        .delete()
        .eq("user_id", user_id)
        .eq("source", source)
        .execute()
    )
    return {"deleted": len(result.data)}
