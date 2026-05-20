from supabase import create_client, Client
from api.config import settings

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_anon_key)
    return _client


def get_admin_client() -> Client:
    """Service-role client — bypasses RLS. Use only in server-side operations."""
    return create_client(settings.supabase_url, settings.supabase_service_key)
