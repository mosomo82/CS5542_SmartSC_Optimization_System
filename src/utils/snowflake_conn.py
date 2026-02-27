"""
Snowflake Connection Utility

This module provides a singleton pattern for managing Snowflake Snowpark sessions.
It loads connection parameters from environment variables and maintains a single
session throughout the application lifecycle.

Supports two authentication methods:
1. Password authentication (SNOWFLAKE_PASSWORD)
2. Key pair authentication (SNOWFLAKE_PRIVATE_KEY_PATH)

Environment Variables Required:
    - SNOWFLAKE_ACCOUNT: Snowflake account identifier
    - SNOWFLAKE_USER: Snowflake username
    - SNOWFLAKE_PASSWORD: Snowflake password (if using password auth)
      OR
    - SNOWFLAKE_PRIVATE_KEY_PATH: Path to private key file (if using key pair auth)
    - SNOWFLAKE_ROLE: Snowflake role to use
    - SNOWFLAKE_WAREHOUSE: Snowflake warehouse name
    - SNOWFLAKE_DATABASE: Snowflake database name

Example Usage:
    from src.utils.snowflake_conn import get_session, close_session

    # Get session (creates new or returns cached)
    session = get_session()
    result = session.sql("SELECT CURRENT_WAREHOUSE()").collect()

    # Close session when done
    close_session()
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from snowflake.snowpark import Session

# Attempt to import cryptography (only needed for key pair auth)
try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False


# Module-level singleton session
_session = None


def get_session() -> Session:
    """
    Get or create a Snowflake Snowpark session.

    This function implements a singleton pattern, creating a new session
    on first call and returning the cached session on subsequent calls.

    Returns:
        Session: Active Snowflake Snowpark session

    Raises:
        ValueError: If required environment variables are missing
        Exception: If session creation fails
    """
    global _session

    # Return existing session if available
    if _session is not None:
        return _session

    try:
        # Load environment variables from .env file
        load_dotenv()

        # Common required variables
        common_vars = [
            'SNOWFLAKE_ACCOUNT',
            'SNOWFLAKE_USER',
            'SNOWFLAKE_ROLE',
            'SNOWFLAKE_WAREHOUSE',
            'SNOWFLAKE_DATABASE'
        ]

        # Check for missing common variables
        missing_vars = [var for var in common_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        # Build base connection parameters
        connection_params = {
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'user': os.getenv('SNOWFLAKE_USER'),
            'role': os.getenv('SNOWFLAKE_ROLE'),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
            'database': os.getenv('SNOWFLAKE_DATABASE')
        }

        # Determine authentication method
        password = os.getenv('SNOWFLAKE_PASSWORD')
        private_key_path = os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH')

        if private_key_path:
            # Key pair authentication (for MFA-enabled accounts)
            if not _HAS_CRYPTO:
                raise ImportError(
                    "Key pair auth requires 'cryptography' package. "
                    "Install it with: pip install cryptography"
                )

            print(f"Using key pair authentication from: {private_key_path}")

            key_path = Path(private_key_path).expanduser()
            if not key_path.exists():
                raise FileNotFoundError(
                    f"Private key file not found: {private_key_path}"
                )

            with open(key_path, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,  # Assumes unencrypted key
                    backend=default_backend()
                )

            pkb = private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            connection_params['private_key'] = pkb

        elif password:
            # Password authentication
            print("Using password authentication")
            connection_params['password'] = password

        else:
            raise ValueError(
                "Either SNOWFLAKE_PASSWORD or SNOWFLAKE_PRIVATE_KEY_PATH "
                "must be set in your .env file"
            )

        # Create new Snowpark session
        _session = Session.builder.configs(connection_params).create()

        print(
            f"Snowflake session created successfully "
            f"for user: {connection_params['user']}"
        )

        return _session

    except ValueError as ve:
        raise ve
    except Exception as e:
        raise Exception(f"Failed to create Snowflake session: {str(e)}")


def close_session() -> None:
    """
    Close the active Snowflake Snowpark session.

    This function properly closes the session and resets the singleton.
    It's safe to call even if no session exists.
    """
    global _session

    if _session is not None:
        try:
            _session.close()
            print("Snowflake session closed successfully")
        except Exception as e:
            print(f"Error closing Snowflake session: {str(e)}")
        finally:
            _session = None
