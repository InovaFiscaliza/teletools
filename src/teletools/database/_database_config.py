import psycopg2
from contextlib import contextmanager

#: Number of threads to use for DuckDB operations
DUCKDB_THREADS = 12

#: Memory limit for DuckDB operations
DUCKDB_MEMORY_LIMIT = "16GB"

# Database connection parameters
DB_CONFIG = {
    'host': 'rhfiprtipdin01',
    'database': 'cdr',
    'user': 'cdr.service',
    'port': 5432
}

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_session(autocommit=False)
        yield conn
    finally:
        if conn:
            conn.close()

