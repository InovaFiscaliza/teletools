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

from asyncio.log import logger
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict

import psycopg2
from dotenv import load_dotenv

# Performance settings
CHUNK_SIZE = 100000  # Process in chunks of 100k rows

# Schemas 
IMPORT_SCHEMA = "entrada"
TARGET_SCHEMA = "public"

# Tables for number portability and providers
IMPORT_TABLE_PORTABILIDADE = "abr_portabilidade"
TB_PORTABILIDADE_HISTORICO = "tb_portabilidade_historico"

# Tables for providers
TB_PRESTADORAS = "tb_prestadoras"

# Tables for numbering plans
IMPORT_TABLE_STFC_SMP_SME = "abr_numeracao_stfc_smp_sme"
IMPORT_TABLE_CNG = "abr_numeracao_cng"
IMPORT_TABLE_SUP = "abr_numeracao_sup"
TB_NUMERACAO = "tb_numeracao"

# Tables for queries
TB_NUMBERS_TO_QUERY = "numbers_to_query"

# Load environment variables from .env file
env_file = Path("~").expanduser() / ".teletools.env"
if env_file.exists():
    load_dotenv(env_file)
else:
    print(
        f"Warning: .env file not found at {env_file}. Using system environment variables."
    )


def get_db_config() -> Dict[str, Any]:
    """Get database configuration from environment variables.

    Returns:
        Dict containing database connection parameters

    Raises:
        ValueError: If required environment variables are missing
        EnvironmentError: If configuration is invalid
    """
    required_vars = [
        "TELETOOLS_DB_HOST",
        "TELETOOLS_DB_NAME",
        "TELETOOLS_DB_USER",
        "TELETOOLS_DB_PASSWORD",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}.\n"
            f"Please create a .env file from .env.example template and set these variables."
        )

    config = {
        "host": os.getenv("TELETOOLS_DB_HOST"),
        "port": int(os.getenv("TELETOOLS_DB_PORT", "5432")),
        "database": os.getenv("TELETOOLS_DB_NAME"),
        "user": os.getenv("TELETOOLS_DB_USER"),
        "password": os.getenv("TELETOOLS_DB_PASSWORD"),
    }

    return config


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


def validate_connection() -> bool:
    """Test database connection with current configuration.

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
    except Exception:
        return False

def check_if_table_exists(schema: str, table_name: str) -> bool:
    """Check if a table exists in the database.

    Args:
        table_name: Name of the table to check
    
    Returns:
        True if table exists, False otherwise
    """
    query = """
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
    );
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (schema, table_name))
                exists = cursor.fetchone()[0]
                return exists
    except Exception as e:
        logger.info(f"Error checking table existence: {e}")
        return False
    
def execute_truncate_table(schema: str, table_name: str, logger: any) -> None:
    """
    Truncate specified table.

    Args:
        schema: Schema of the table
        table_name: Name of the table to truncate

    Raises:
        Exception: If truncation fails
    """

    if not check_if_table_exists(schema, table_name):
        logger.info(f"Table {schema}.{table_name} does not exist. Skipping truncation.")
        return

    with get_db_connection() as conn: 
        try:
            with conn.cursor() as cursor:
                logger.info(f"Truncating table {schema}.{table_name}...")
                cursor.execute(f"TRUNCATE TABLE {schema}.{table_name};")
            conn.commit()
            logger.info(f"Table {schema}.{table_name} truncated successfully.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error truncating table {schema}.{table_name}: {e}")
            raise

def execute_drop_table(schema: str, table_name: str, logger: any) -> None:
    """
    Drop specified table.

    Args:
        schema: Schema of the table
        table_name: Name of the table to drop

    Raises:
        Exception: If dropping fails
    """

    if not check_if_table_exists(schema, table_name):
        logger.info(f"Table {schema}.{table_name} does not exist. Skipping dropping.")
        return

    with get_db_connection() as conn: 
        try:
            with conn.cursor() as cursor:
                logger.info(f"Dropping table {schema}.{table_name}...")
                cursor.execute(f"DROP TABLE {schema}.{table_name} CASCADE;")
            conn.commit()
            logger.info(f"Table {schema}.{table_name} dropped successfully.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error dropping table {schema}.{table_name}: {e}")
            raise

