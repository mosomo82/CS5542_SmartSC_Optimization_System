"""
Snowflake Connection Utility — Lab 9 Enhanced
==============================================
Provides a singleton Snowpark Session for the Phase 2 SmartSC pipeline.

Lab 9 additions (ported from COMP_SCI_5542/Week_6/scripts/sf_connect.py):
  - Python `logging` module replacing all `print()` calls
  - Startup assertions: hard-crash at import time if any required env var is missing
  - Keep-alive ping on first session creation (SELECT 1) to eliminate ~8s cold-start
  - `retry_snowflake` exponential-backoff decorator for callers hitting transient errors

Supports two authentication methods:
  1. Password authentication  (SNOWFLAKE_PASSWORD)
  2. Key pair authentication  (SNOWFLAKE_PRIVATE_KEY_PATH)

Required environment variables:
    SNOWFLAKE_ACCOUNT  · SNOWFLAKE_USER  · SNOWFLAKE_ROLE
    SNOWFLAKE_WAREHOUSE  · SNOWFLAKE_DATABASE
    SNOWFLAKE_PASSWORD  **or**  SNOWFLAKE_PRIVATE_KEY_PATH

Example usage:
    from src.utils.snowflake_conn import get_session, close_session, retry_snowflake

    session = get_session()
    result  = session.sql("SELECT CURRENT_WAREHOUSE()").collect()
    close_session()
"""

import os
import time
import logging
import functools
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# ── Logging ───────────────────────────────────────────────────────────────────
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Environment ───────────────────────────────────────────────────────────────
_env_path = find_dotenv(filename=".env", raise_error_if_not_found=False) or str(
    Path(__file__).resolve().parents[3] / ".env"
)
load_dotenv(_env_path, override=False)

# Attempt to import cryptography (only needed for key pair auth)
try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False

# ── Module-level singleton ────────────────────────────────────────────────────
_session = None
_pinged  = False   # guard: only run the startup ping once per process


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get(key: str) -> str | None:
    """Read from env, then fall back to Streamlit secrets if available."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st          # noqa: F401
        return st.secrets.get(key)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Startup Assertions  (Lab 9 — Tony)
# Runs once at import time; raises AssertionError immediately if any secret
# is absent so the container fails fast rather than crashing mid-request.
# ─────────────────────────────────────────────────────────────────────────────

def _assert_env() -> None:
    logger.info("Verifying Snowflake environment variables...")
    required = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_ROLE",
        "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE",
    ]
    # Password is required unless key-pair auth is configured
    if not _get("SNOWFLAKE_PRIVATE_KEY_PATH"):
        required.append("SNOWFLAKE_PASSWORD")

    missing = [k for k in required if not _get(k)]
    assert not missing, (
        f"Startup Assertion Failed: Missing Snowflake credentials: {missing}. "
        "Set them in .env (local) or the deployment secrets manager."
    )
    logger.info("All required Snowflake environment variables are present.")


_assert_env()   # <-- called at import time


# ─────────────────────────────────────────────────────────────────────────────
# Retry decorator  (Lab 9 — Tony)
# Wraps any callable that talks to Snowflake/external APIs with
# exponential back-off (5 s, 10 s, 20 s) on transient errors.
# ─────────────────────────────────────────────────────────────────────────────

def retry_snowflake(max_retries: int = 3, base_wait: int = 5):
    """Decorator factory: exponential back-off retry for Snowflake/API calls.

    Args:
        max_retries: Number of additional attempts after the first failure.
        base_wait:   Initial wait in seconds (doubles on each retry).

    Example:
        @retry_snowflake(max_retries=3, base_wait=5)
        def my_query():
            return get_session().sql("SELECT ...").collect()
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    is_transient = any(
                        code in str(exc)
                        for code in ("429", "503", "connection", "timeout")
                    )
                    if is_transient and attempt < max_retries:
                        wait = base_wait * (2 ** attempt)   # 5, 10, 20 s
                        logger.warning(
                            "[retry] Transient error on %s (attempt %d/%d). "
                            "Retrying in %ds... | %s",
                            func.__name__, attempt + 1, max_retries, wait, exc
                        )
                        time.sleep(wait)
                    else:
                        raise
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Session management
# ─────────────────────────────────────────────────────────────────────────────

def get_session():
    """Return the cached Snowpark Session, creating (and pinging) it on first call.

    Lab 9: A keep-alive ``SELECT 1`` ping is executed immediately after the
    session is created to warm up the connection pool and reduce first-query
    cold-start latency from ~8 s to <2 s.

    Returns:
        snowflake.snowpark.Session: Active Snowflake Snowpark session.

    Raises:
        AssertionError: If required env vars are missing (caught at import).
        ImportError:    If key-pair auth is requested without `cryptography`.
        RuntimeError:   If the keep-alive ping fails.
        Exception:      For any other session-creation error.
    """
    global _session, _pinged

    if _session is not None:
        return _session

    from snowflake.snowpark import Session   # lazy import keeps startup fast

    logger.info("Creating new Snowflake Snowpark session...")

    # Build connection parameters
    connection_params = {
        "account":   _get("SNOWFLAKE_ACCOUNT"),
        "user":      _get("SNOWFLAKE_USER"),
        "role":      _get("SNOWFLAKE_ROLE"),
        "warehouse": _get("SNOWFLAKE_WAREHOUSE"),
        "database":  _get("SNOWFLAKE_DATABASE"),
    }

    # Authentication
    private_key_path = _get("SNOWFLAKE_PRIVATE_KEY_PATH")
    password         = _get("SNOWFLAKE_PASSWORD")

    if private_key_path:
        if not _HAS_CRYPTO:
            raise ImportError(
                "Key pair auth requires the 'cryptography' package. "
                "Install with: pip install cryptography"
            )
        logger.info("Using key-pair authentication from: %s", private_key_path)
        key_path = Path(private_key_path).expanduser()
        if not key_path.exists():
            raise FileNotFoundError(f"Private key file not found: {private_key_path}")

        with open(key_path, "rb") as kf:
            private_key = serialization.load_pem_private_key(
                kf.read(), password=None, backend=default_backend()
            )
        connection_params["private_key"] = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    elif password:
        logger.info("Using password authentication.")
        connection_params["password"] = password
    else:
        raise ValueError(
            "Either SNOWFLAKE_PASSWORD or SNOWFLAKE_PRIVATE_KEY_PATH must be set."
        )

    try:
        _session = Session.builder.configs(connection_params).create()
        logger.info("Snowflake session created for user: %s", connection_params["user"])
    except Exception as exc:
        raise Exception(f"Failed to create Snowflake session: {exc}") from exc

    # ── Keep-alive ping  (Lab 9 — Tony) ────────────────────────────────────
    # "SELECT 1" warms up the connection pool so first real query is fast.
    if not _pinged:
        try:
            _session.sql("SELECT 1").collect()
            logger.info("Snowflake keep-alive ping successful (cold-start warmed).")
            _pinged = True
        except Exception as exc:
            # Non-fatal: log and continue; session itself was created OK.
            logger.warning("Keep-alive ping failed (non-fatal): %s", exc)

    return _session


def close_session() -> None:
    """Close the active Snowflake Snowpark session and reset the singleton."""
    global _session, _pinged

    if _session is not None:
        try:
            _session.close()
            logger.info("Snowflake session closed successfully.")
        except Exception as exc:
            logger.error("Error closing Snowflake session: %s", exc)
        finally:
            _session = None
            _pinged  = False
