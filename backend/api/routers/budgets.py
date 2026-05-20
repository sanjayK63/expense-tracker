from fastapi import APIRouter, Header
from pydantic import BaseModel
from api.services.auth_helper import require_user
from api.db import get_client

router = APIRouter()


class BudgetIn(BaseModel):
    category: str
    monthly_limit: float


@router.get("/")
async def get_budgets(authorization: str = Header(...)):
    user_id = await require_user(authorization)
    result  = get_client().table("budgets").select("*").eq("user_id", user_id).execute()
    return result.data


@router.put("/")
async def upsert_budgets(budgets: list[BudgetIn], authorization: str = Header(...)):
    user_id = await require_user(authorization)
    client  = get_client()
    rows    = [{"user_id": user_id, **b.model_dump()} for b in budgets]
    result  = client.table("budgets").upsert(rows, on_conflict="user_id,category").execute()
    return result.data
