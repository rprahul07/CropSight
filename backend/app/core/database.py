from supabase import create_client, Client
from app.core.config import settings

def get_supabase_client() -> Client:
    # Initialize the Supabase client using environment variables
    # For backend operations on behalf of user, client can pass JWT using `supabase.auth.set_session()` or as headers if required.
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

supabase = get_supabase_client()
