"""
Auth is handled entirely by Supabase Auth on the frontend.
This router exposes a /me endpoint so the frontend can verify
the JWT and get the user profile.
"""
from fastapi import APIRouter, Header, HTTPException
from api.db import get_client

router = APIRouter()


@router.get("/me")
async def me(authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ").strip()
    try:
        client = get_client()
        user = client.auth.get_user(token)
        return {"id": user.user.id, "email": user.user.email}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
