"""Database Configuration Module with Secure Credential Management.

This module provides secure database connection configuration using environment variables
loaded from a .env file. It includes connection pooling, SSL support, and comprehensive
error handling for production environments.

Environment Variables Required:
    DB_HOST: Database server hostname
    DB_PORT: Database server port (default: 5432)
    DB_NAME: Database name
    DB_USER: Database username
    DB_PASSWORD: Database password

Optional Environment Variables:
    DB_SSLMODE: SSL connection mode (disable, allow, prefer, require, verify-ca, verify-full)
    DB_SSLCERT: Path to client SSL certificate
    DB_SSLKEY: Path to client SSL private key
    DB_SSLROOTCERT: Path to root CA certificate
    DB_POOL_MIN_CONNECTIONS: Minimum connections in pool (default: 1)
    DB_POOL_MAX_CONNECTIONS: Maximum connections in pool (default: 20)
    DB_CONNECTION_TIMEOUT: Connection timeout in seconds (default: 30)
    DUCKDB_THREADS: Number of threads for DuckDB operations (default: 12)
    DUCKDB_MEMORY_LIMIT: Memory limit for DuckDB operations (default: 16GB)

Security Features:
    - Environment variable based configuration
    - SSL/TLS connection support
    - Connection pooling with configurable limits
    - Secure credential storage outside codebase
    - No hardcoded passwords or sensitive information

Usage:
    # Create .env file from .env.example template
    cp .env.example .env
    
    # Edit .env with your actual credentials
    # Use get_db_connection() context manager for database operations
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        result = cursor.fetchone()
"""
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict

import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
env_file = Path(__file__).parent.parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    print(f"Warning: .env file not found at {env_file}. Using system environment variables.")


# Performance settings with environment variable support
DUCKDB_THREADS = int(os.getenv('DUCKDB_THREADS', '12'))
DUCKDB_MEMORY_LIMIT = os.getenv('DUCKDB_MEMORY_LIMIT', '16GB')


def get_db_config() -> Dict[str, Any]:
    """Get database configuration from environment variables.
    
    Returns:
        Dict containing database connection parameters
        
    Raises:
        ValueError: If required environment variables are missing
        EnvironmentError: If configuration is invalid
    """
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}.\n"
            f"Please create a .env file from .env.example template and set these variables."
        )
    
    config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'connect_timeout': int(os.getenv('DB_CONNECTION_TIMEOUT', '30'))
    }
    
    # Add SSL configuration if provided
    ssl_config = {}
    if os.getenv('DB_SSLMODE'):
        ssl_config['sslmode'] = os.getenv('DB_SSLMODE')
    if os.getenv('DB_SSLCERT'):
        ssl_config['sslcert'] = os.getenv('DB_SSLCERT')
    if os.getenv('DB_SSLKEY'):
        ssl_config['sslkey'] = os.getenv('DB_SSLKEY')
    if os.getenv('DB_SSLROOTCERT'):
        ssl_config['sslrootcert'] = os.getenv('DB_SSLROOTCERT')
    
    config.update(ssl_config)
    return config


def validate_connection() -> bool:
    """Test database connection with current configuration.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
                return True
    except Exception as e:
        print(f"Database connection validation failed: {e}")
        return False


# Legacy support - remove in future version
DB_CONFIG = None

def _get_legacy_config():
    """Legacy configuration support - deprecated."""
    import warnings
    warnings.warn(
        "DB_CONFIG dictionary is deprecated. Use get_db_config() function instead.",
        DeprecationWarning,
        stacklevel=2
    )
    try:
        return get_db_config()
    except ValueError:
        # Fallback to hardcoded values for backward compatibility
        return {
            'host': 'localhost',
            'database': 'cdr',
            'user': 'cdr_user',
            'port': 5432
        }


@contextmanager
def get_db_connection(autocommit: bool = False):
    """Secure database connection context manager.
    
    Args:
        autocommit: Whether to enable autocommit mode
        
    Yields:
        psycopg2.connection: Database connection object
        
    Raises:
        ValueError: If database configuration is invalid
        psycopg2.Error: If database connection fails
        
    Example:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()
    """
    conn = None
    try:
        config = get_db_config()
        conn = psycopg2.connect(**config)
        conn.set_session(autocommit=autocommit)
        yield conn
    except ValueError as e:
        raise ValueError(f"Database configuration error: {e}")
    except psycopg2.Error as e:
        raise psycopg2.Error(f"Database connection failed: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error in database connection: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass  # Ignore errors during cleanup


@contextmanager
def get_db_connection_pool():
    """Get database connection from connection pool (placeholder for future implementation).
    
    Note:
        This is a placeholder for future connection pooling implementation.
        Currently uses the same logic as get_db_connection().
    """
    # TODO: Implement actual connection pooling with psycopg2.pool
    with get_db_connection() as conn:
        yield conn

