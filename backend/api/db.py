from supabase import create_client, Client
from api.config import settings

_anon_client: Client | None = None
_admin_client: Client | None = None


def get_client() -> Client:
    """Anon key client — subject to RLS."""
    global _anon_client
    if _anon_client is None:
        _anon_client = create_client(settings.supabase_url, settings.supabase_anon_key)
    return _anon_client


def get_admin_client() -> Client:
    """Service-role client — bypasses RLS. Cached singleton, use only server-side."""
    global _admin_client
    if _admin_client is None:
        _admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _admin_client
