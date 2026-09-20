"""Supabase Client Management Module.

Provides singleton access to the Supabase client with graceful error handling
when environment variables are missing or misconfigured.
"""

from typing import Any, Optional

try:
    from supabase import Client, create_client
except ImportError:
    Client = Any  # type: ignore
    create_client = None  # type: ignore

from src.config import settings


_client_instance: Optional[Client] = None


def get_supabase_client() -> Client:
    """Retrieve or initialize the Supabase client instance.

    Returns:
        Client: An authenticated Supabase client using the service role key.

    Raises:
        RuntimeError: If SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY are not configured.
    """
    global _client_instance
    if _client_instance is not None:
        return _client_instance

    if create_client is None:
        raise RuntimeError(
            "The 'supabase' Python package is not installed. "
            "Please install it using 'pip install supabase' or 'pip install -r requirements.txt'."
        )

    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY

    missing = []
    if not url:
        missing.append("SUPABASE_URL")
    if not key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")

    if missing:
        raise RuntimeError(
            f"Missing required Supabase configuration: {', '.join(missing)}. "
            "Please check your .env file or environment variables. "
            "Refer to apps/backend/.env.example for guidance."
        )

    try:
        _client_instance = create_client(url, key)
        return _client_instance
    except Exception as exc:
        raise RuntimeError(
            f"Failed to connect to Supabase at '{url}': {str(exc)}"
        ) from exc
