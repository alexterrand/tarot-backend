"""Supabase client configuration for game data logging.

This module provides a singleton Supabase client instance used across
the application for database operations.
"""

import logging
from functools import lru_cache

from supabase import Client, create_client

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Get or create Supabase client singleton.

    Uses LRU cache to ensure only one client instance exists.

    Returns:
        Supabase client instance

    Raises:
        ValueError: If Supabase credentials are missing
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError(
            "Missing Supabase credentials. "
            "Set SUPABASE_URL and SUPABASE_KEY in .env"
        )

    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise


# Export singleton instance
supabase = get_supabase_client()
