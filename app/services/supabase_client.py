import os
from functools import lru_cache
from typing import Optional

from supabase import Client, create_client


def _env(*names: str) -> Optional[str]:
    for name in names:
        val = os.getenv(name)
        if val:
            return val
    return None


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Server-side Supabase client.

    Supports both:
    - SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY (recommended for backend), and
    - VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY (fallback for local dev).
    """
    url = _env("SUPABASE_URL", "VITE_SUPABASE_URL")
    key = _env("SUPABASE_SERVICE_ROLE_KEY", "VITE_SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY", "VITE_SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError(
            "Supabase env vars missing. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
            "(or SUPABASE_ANON_KEY / VITE_SUPABASE_* for local dev)."
        )
    
    print("Final Supabase URL:", url)

    return create_client(url, key)

