from fastapi import HTTPException
from api.db import get_admin_client


async def require_user(authorization: str) -> str:
    """Extract and verify Supabase JWT. Returns user_id."""
    token = authorization.removeprefix("Bearer ").strip()
    try:
        user = get_admin_client().auth.get_user(token)
        return user.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")
