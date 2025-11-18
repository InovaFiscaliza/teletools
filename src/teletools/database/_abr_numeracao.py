"""ABR Numbering Data Import Module.

This module provides functionality to import Brazilian telecom numbering data
plan from ABR reports. It handles different types of CSV files with numbering 
information and imports them into a PostgreSQL database with optimized 
performance using chunked processing and bulk insert operations.

Data Sources - Official ABR Telecom Portal:
    All files for import must be downloaded from the official ABR portal:
    
    - CNG (Código Não Geográfico):
      https://easi.abrtelecom.com.br/nsapn/#/public/files/download/cng
      Free call numbers (0800, 0300, etc.)
    
    - SME (Serviço Móvel Especializado):
      https://easi.abrtelecom.com.br/nsapn/#/public/files/download/sme
      Specialized mobile service numbering
    
    - SMP (Serviço Móvel Pessoal):
      https://easi.abrtelecom.com.br/nsapn/#/public/files/download/smp
      Personal mobile service numbering
    
    - STFC (Serviço Telefônico Fixo Comutado):
      https://easi.abrtelecom.com.br/nsapn/#/public/files/download/stfc
      Fixed telephony service numbering
    
    - STFC-FATB (Serviço Telefônico Fixo Comutado - Fora da Area de Tarifa Básica):
      https://easi.abrtelecom.com.br/nsapn/#/public/files/download/stfc-fatb
      Fixed telephony outside basic tariff area numbering

    - SUP (Serviços de Utilidade Pública):
        https://easi.abrtelecom.com.br/nsapn/#/public/files/download/sup
        Public utility service numbering

    Note: These files contain official ANATEL numbering data and are 
    updated regularly. Always download the latest versions for accurate data.

Supported File Types:
    - STFC (Fixed Telephony): Complete numbering data with all columns
    - SMP/SME (Mobile Telephony): Numbering data without locality information
    - CNG (Non-Geographic Codes): Special codes with simplified structure
    - SUP (Public Utility Services): Public utility service numbering

File Type Detection:
    File type is automatically detected based on filename prefix:
    - Files starting with "STFC": Fixed telephony (all columns)
    - Files starting with "SMP" or "SME": Mobile telephony (subset of columns)
    - Files starting with "CNG": Non-geographic codes (minimal columns)
    - Files starting with "SUP": Public utility services (specific columns)

Module Features:
    - Automatic file type detection and appropriate column mapping
    - Memory-efficient chunked reading for large files
    - Bulk database insertions using PostgreSQL COPY FROM
    - Comprehensive logging and progress tracking
    - Data validation and type optimization
    - Separate table handling for different data types

Typical Usage:
    from _abr_numeracao import load_numbering_reports

    # Import single file (auto-detects type)
    results = load_numbering_reports('/path/to/STFC_FILE.zip')

    # Import all files from directory
    results = load_numbering_reports('/path/to/directory/')

Example Workflow:
    1. Download files from official ABR portal (see Data Sources above)
    2. Copy ZIP files to a directory (there is no need to extract them)
    3. Run import: load_numbering_reports('/path/to/downloaded/files/')
    4. Check logs for import statistics and any errors
"""

import time
from collections.abc import Iterator
from io import StringIO
from pathlib import Path

import pandas as pd
from _database_config import get_db_connection

from teletools.utils import setup_logger

# Configure logger
logger = setup_logger()

# Performance settings
CHUNK_SIZE = 100000  # Process in chunks of 100k rows

# Table and schema names
IMPORT_SCHEMA = "entrada"
TABLE_NUMERACAO = "abr_numeracao_teletools"
TABLE_CNG = "abr_cng_teletools"
TABLE_SUP = "abr_sup_teletools"

# Column definitions for different file types

STFC_FILE_COLUMNS = {
    "nome_prestadora": "str",
    "cnpj_prestadora": "str",
    "uf": "str",
    "cn": "str",
    "prefixo": "str",
    "faixa_inicial": "str",
    "faixa_final": "str",
    "codigo_cnl": "str",
    "nome_localidade": "str",
    "area_local": "str",
    "sigla_area_local": "str",
    "codigo_area_local": "str",
    "status": "str",
}

STFC_TABLE_COLUMNS = list(STFC_FILE_COLUMNS.keys()) + ["servico", "nome_arquivo"]

SMP_SME_FILE_COLUMNS = {
    "nome_prestadora": "str",
    "cnpj_prestadora": "str",
    "cn": "str",
    "prefixo": "str",
    "faixa_inicial": "str",
    "faixa_final": "str",
    "status": "str",
}

SMP_SME_TABLE_COLUMNS = list(SMP_SME_FILE_COLUMNS.keys()) + ["servico", "nome_arquivo"]

CNG_FILE_COLUMNS = {
    "nome_prestadora": "str",
    "cnpj_prestadora": "str",
    "codigo_nao_geografico": "str",
    "status": "str",
}

CNG_TABLE_COLUMNS = list(CNG_FILE_COLUMNS.keys()) + ["nome_arquivo"]

SUP_FILE_COLUMNS = {
    "nome_prestadora": "str",
    "cnpj_prestadora": "str",
    "numero_sup": "str",
    "extensao": "str",
    "uf": "str",
    "cn": "str",
    "codigo_municipio": "str",
    "nome_municipio": "str",
    "instituicao": "str",
    "tipo": "str",
    "status": "str",
}

SUP_TABLE_COLUMNS = list(SUP_FILE_COLUMNS.keys()) + ["nome_arquivo"]

def _detect_file_type(file: Path) -> str:
    """Detect file type based on filename prefix.

    Args:
        file: Path to the file

    Returns:
        str: File type ('STFC', 'SMP_SME', or 'CNG')
    """
    filename_upper = file.name.upper()

    if filename_upper.startswith("STFC"):
        return "STFC"
    elif filename_upper.startswith(("SMP", "SME")):
        return "SMP_SME"
    elif filename_upper.startswith("CNG"):
        return "CNG"
    elif filename_upper.startswith("SUP"):
        return "SUP"
    else:
        # Default to STFC if cannot determine
        logger.warning(f"Cannot determine file type for {file.name}.")
        return None


def _get_file_config(file_type: str) -> dict:
    """Get configuration for specific file type.

    Args:
        file_type: Type of file ('STFC', 'SMP_SME', or 'CNG')

    Returns:
        dict: Configuration including columns, table name, and data types
    """
    if file_type == "STFC":
        return {
            "columns": list(STFC_FILE_COLUMNS.keys()),
            "table": TABLE_NUMERACAO,
            "dtype": STFC_FILE_COLUMNS,
        }
    elif file_type == "SMP_SME":
        return {
            "columns": list(SMP_SME_FILE_COLUMNS.keys()),
            "table": TABLE_NUMERACAO,
            "dtype": SMP_SME_FILE_COLUMNS,
        }
    elif file_type == "CNG":
        return {
            "columns": list(CNG_FILE_COLUMNS.keys()),
            "table": TABLE_CNG,
            "dtype": CNG_FILE_COLUMNS,
        }
    elif file_type == "SUP":
        return {
            "columns": list(SUP_FILE_COLUMNS.keys()),
            "table": TABLE_SUP,
            "dtype": SUP_FILE_COLUMNS,
        }
    else:
        raise ValueError(f"Unknown file type: {file_type}")


def _read_file_in_chunks(
    file: Path, chunk_size: int = CHUNK_SIZE
) -> Iterator[tuple[pd.DataFrame, str]]:
    """
    Read CSV file in chunks to optimize memory usage.

    Args:
        file: Path to the file
        chunk_size: Size of each chunk

    Yields:
        tuple: (DataFrame chunk with filename column added, file_type)

    Raises:
        Exception: If file reading fails
    """
    # Detect file type
    file_type = _detect_file_type(file)
    config = _get_file_config(file_type)

    logger.info(f"  File type detected: {file_type}")

    try:
        # Use chunksize for optimized reading
        chunk_reader = pd.read_csv(
            file,
            sep=";",
            encoding="latin1",
            header=0,
            names=config["columns"],
            index_col=False,
            chunksize=chunk_size,
            dtype=config["dtype"],
            low_memory=True,
        )

        for chunk in chunk_reader:
            # Add servico column for telephony files
            if file_type in ("STFC", "SMP_SME"):
                chunk["servico"] = file_type
            # Add filename column
            chunk["nome_arquivo"] = file.name
            yield chunk, file_type

    except Exception as e:
        logger.error(f"Error reading file {file}: {e}")
        raise


def _create_numeracao_table_if_not_exists(
    conn, table_name: str = TABLE_NUMERACAO, schema: str = IMPORT_SCHEMA
) -> None:
    """
    Create numbering table if it doesn't exist.

    Args:
        conn: Database connection
        table_name: Name of the table
        schema: Table schema

    Raises:
        Exception: If table creation fails
    """
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
        nome_prestadora VARCHAR(200),
        cnpj_prestadora VARCHAR(20),
        uf VARCHAR(2),
        cn VARCHAR(10),
        prefixo VARCHAR(10),
        faixa_inicial VARCHAR(20),
        faixa_final VARCHAR(20),
        codigo_cnl VARCHAR(10),
        nome_localidade VARCHAR(200),
        area_local VARCHAR(100),
        sigla_area_local VARCHAR(10),
        codigo_area_local VARCHAR(10),
        status VARCHAR(50),
        servico VARCHAR(10),
        nome_arquivo VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_{table_name}_faixa_inicial ON {schema}.{table_name}(faixa_inicial);
    CREATE INDEX IF NOT EXISTS idx_{table_name}_faixa_final ON {schema}.{table_name}(faixa_final);
    CREATE INDEX IF NOT EXISTS idx_{table_name}_cnpj ON {schema}.{table_name}(cnpj_prestadora);
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)
        conn.commit()
        logger.info(f"  Table {schema}.{table_name} created/verified successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"  Error creating table: {e}")
        raise


def _create_cng_table_if_not_exists(
    conn, table_name: str = TABLE_CNG, schema: str = IMPORT_SCHEMA
) -> None:
    """
    Create CNG table if it doesn't exist.

    Args:
        conn: Database connection
        table_name: Name of the table
        schema: Table schema

    Raises:
        Exception: If table creation fails
    """
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
        nome_prestadora VARCHAR(200),
        cnpj_prestadora VARCHAR(20),
        codigo_nao_geografico VARCHAR(20),
        status VARCHAR(50),
        nome_arquivo VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_{table_name}_codigo_nao_geografico ON {schema}.{table_name}(codigo_nao_geografico);
    CREATE INDEX IF NOT EXISTS idx_{table_name}_cnpj ON {schema}.{table_name}(cnpj_prestadora);
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)
        conn.commit()
        logger.info(f"  Table {schema}.{table_name} created/verified successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating table: {e}")
        raise

def _create_sup_table_if_not_exists(
    conn, table_name: str = TABLE_SUP, schema: str = IMPORT_SCHEMA
) -> None:
    """
    Create SUP table if it doesn't exist.

    Args:
        conn: Database connection
        table_name: Name of the table
        schema: Table schema
    
    Raises:
        Exception: If table creation fails
    """
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
        nome_prestadora VARCHAR(200),
        cnpj_prestadora VARCHAR(20),
        numero_sup VARCHAR(20),
        extensao VARCHAR(10),
        uf VARCHAR(2),
        cn VARCHAR(10),
        codigo_municipio VARCHAR(10),
        nome_municipio VARCHAR(200),
        instituicao VARCHAR(100),
        tipo VARCHAR(50),
        status VARCHAR(50),
        nome_arquivo VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_{table_name}_numero_sup ON {schema}.{table_name}(numero_sup);
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)
        conn.commit()
        logger.info(f"  Table {schema}.{table_name} created/verified successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating table: {e}")
        raise

def _bulk_insert_with_copy(
    conn, df: pd.DataFrame, file_type: str, schema: str = IMPORT_SCHEMA
) -> None:
    """
    Perform bulk insert using PostgreSQL COPY FROM for maximum performance.

    Args:
        conn: Database connection
        df: DataFrame to insert
        file_type: Type of file being processed
        schema: Target schema

    Raises:
        Exception: If bulk insert fails
    """
    config = _get_file_config(file_type)
    table_name = config["table"]

    # Create StringIO buffer
    output = StringIO()

    # Convert DataFrame to CSV in memory
    df.to_csv(
        output,
        sep="\t",
        header=False,
        index=False,
        na_rep="\\N",  # NULL representation for PostgreSQL
    )

    output.seek(0)

    # Define column list for COPY command
    if file_type == "CNG":
        copy_columns = ", ".join(CNG_TABLE_COLUMNS)
    elif file_type == "SMP_SME":
        copy_columns = ", ".join(SMP_SME_TABLE_COLUMNS)
    elif file_type == "SUP":
        copy_columns = ", ".join(SUP_TABLE_COLUMNS)
    elif file_type == "STFC":
        copy_columns = ", ".join(STFC_TABLE_COLUMNS)
    else:
        logger.error(f"Unknown file type for COPY: {file_type}")
        raise ValueError(f"Unknown file type for COPY: {file_type}")
    try:
        with conn.cursor() as cursor:
            # Use COPY FROM for ultra-fast insertion
            cursor.copy_expert(
                f"""
                COPY {schema}.{table_name} ({copy_columns})
                FROM STDIN WITH CSV DELIMITER E'\\t' NULL '\\N'
                """,
                output,
            )
        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Error in insertion: {e}")
        raise


def _import_single_file(
    file: Path,
    schema: str = IMPORT_SCHEMA,
    truncate_table: bool = False,
) -> int:
    """
    Import a single numbering file into the database.

    Args:
        file: Path to the file to import
        schema: Target schema
        truncate_table: Whether to truncate table before import

    Returns:
        int: Number of rows imported

    Raises:
        Exception: If import fails
    """
    start_time = time.time()
    total_rows = 0

    logger.info(f"  Starting import of file {file}.")

    try:
        with get_db_connection() as conn:
            # Process file in chunks
            chunk_count = 0
            file_type = None

            for chunk_df, detected_file_type in _read_file_in_chunks(file):
                chunk_count += 1
                chunk_start = time.time()

                # Store file type from first chunk
                if file_type is None:
                    file_type = detected_file_type

                    # Create appropriate table
                    if file_type == "CNG":
                        _create_cng_table_if_not_exists(conn, TABLE_CNG, schema)
                        table_name = TABLE_CNG
                    elif file_type == "SUP":
                        _create_sup_table_if_not_exists(conn, TABLE_SUP, schema)
                        table_name = TABLE_SUP
                    elif file_type in ("STFC", "SMP_SME"):
                        _create_numeracao_table_if_not_exists(
                            conn, TABLE_NUMERACAO, schema
                        )
                        table_name = TABLE_NUMERACAO
                    else:
                        logger.warning(f"Unknown file type for {file.name}. Skipping file.")
                        return 0

                    # Truncate table if requested (only on first chunk)
                    if truncate_table and chunk_count == 1:
                        with conn.cursor() as cursor:
                            cursor.execute(f"TRUNCATE TABLE {schema}.{table_name}")
                            conn.commit()
                            logger.info(f"  Table {table_name} truncated")

                # Insert chunk using COPY FROM
                _bulk_insert_with_copy(conn, chunk_df, file_type, schema)

                chunk_rows = len(chunk_df)
                total_rows += chunk_rows
                chunk_time = time.time() - chunk_start
                chunk_time_str = f"{chunk_time:.2f}".replace(".", ",")
                logger.info(
                    f"  Chunk {chunk_count:03d}: {chunk_rows:,} rows inserted in {chunk_time_str}s ({chunk_rows / chunk_time:,.0f} rows/s)".replace(
                        ",", "."
                    )
                )

        end_time = time.time()
        total_time = end_time - start_time

        total_rows_str = f"{total_rows:,}".replace(",", ".")
        total_time_str = f"{total_time:.2f}".replace(".", ",")
        insert_speed_str = f"{total_rows / total_time:,.0f}".replace(",", ".")

    except Exception as e:
        logger.error(f"Error during import: {e}")
        raise

    else:
        logger.info(
            f"  ✅ Import of file {file.name} completed: {total_rows_str} rows in {total_time_str}s ({insert_speed_str} rows/s)"
        )
        return total_rows


def _import_multiple_files(
    file_list: list[Path],
    schema: str = IMPORT_SCHEMA,
    truncate_table: bool = False,
) -> dict:
    """
    Process multiple numbering files sequentially.

    Args:
        file_list: List of files to process
        schema: Target schema
        truncate_table: Whether to truncate tables before first import

    Returns:
        dict: Detailed processing statistics
    """
    if not file_list or not isinstance(file_list, list):
        logger.warning("File list is empty or not a list.")
        return {}

    logger.info(f"Starting import of {len(file_list)} files.")

    start_time_total = time.time()
    results = {}
    total_rows_all_files = 0

    for idx, file in enumerate(file_list, 1):
        logger.info(f"📁 Processing file {idx}/{len(file_list)}:")

        try:
            file_start = time.time()

            # Only truncate on first import if requested
            should_truncate = truncate_table and idx == 1

            # Import file
            file_rows = _import_single_file(
                file,
                schema=schema,
                truncate_table=should_truncate,
            )

            file_time = time.time() - file_start

            total_rows_all_files += file_rows

            results[file.name] = {
                "status": "success",
                "tempo": file_time,
                "linhas": file_rows,
                "velocidade": file_rows / file_time if file_time > 0 else 0,
            }

        except Exception as e:
            logger.error(f"❌ Error processing {file.name}: {e}")
            results[file.name] = {
                "status": "error",
                "erro": str(e),
                "tempo": 0,
                "linhas": 0,
                "velocidade": 0,
            }

    total_time = time.time() - start_time_total

    # Final report
    sucessos = sum(1 for r in results.values() if r["status"] == "success")
    erros = len(results) - sucessos
    total_rows_all_files_str = f"{total_rows_all_files:,}".replace(",", ".")
    total_time_str = f"{total_time:.2f}".replace(".", ",")
    avg_speed_str = f"{total_rows_all_files / total_time:,.0f}".replace(",", ".")

    logger.info("File import report")
    logger.info("════════════════════════════════════")
    logger.info(f"📊 Files processed: {len(file_list)}")
    logger.info(f"✅ Successes: {sucessos}")
    logger.info(f"❌ Errors: {erros}")
    logger.info(f"📈 Total rows: {total_rows_all_files_str}")
    logger.info(f"⏱️ Total time: {total_time_str}s")
    logger.info(f"🚀 Average speed: {avg_speed_str} rows/s")

    if erros > 0:
        logger.info("Files with errors:")
        for file_name, stats in results.items():
            if stats["status"] == "error":
                logger.info(f" - {file_name}: {stats['erro']}")

    return results


def load_nsapn_files(
    input_path: str, schema: str = IMPORT_SCHEMA, truncate_table: bool = False
) -> dict:
    """
    Import Brazilian telecom numbering data plan from files or folders.

    This function automatically detects the file type based on filename prefix
    and imports the data to the appropriate table:

    - STFC files → abr_numeracao table (all columns)
    - SMP/SME files → abr_numeracao table (subset of columns)
    - CNG files → abr_cng table (CNG-specific columns)

    File Type Detection:
    - Files starting with "STFC": Fixed telephony data
    - Files starting with "SMP" or "SME": Mobile telephony data
    - Files starting with "CNG": Non-geographic codes

    Expected file formats (Zipped CSV with semicolon separator):

    STFC (Fixed Telephony) - Complete format:
    | Column              | Description                    |
    |---------------------|--------------------------------|
    | nome_prestadora     | Provider name                  |
    | cnpj_prestadora     | Provider CNPJ                  |
    | uf                  | State                          |
    | cn                  | CN code                        |
    | prefixo             | Prefix                         |
    | faixa_inicial       | Initial range                  |
    | faixa_final         | Final range                    |
    | codigo_cnl          | CNL code                       |
    | nome_localidade     | Locality name                  |
    | area_local          | Local area                     |
    | sigla_area_local    | Local area acronym             |
    | codigo_area_local   | Local area code                |
    | status              | Status                         |

    SMP/SME (Mobile Telephony) - Subset format:
    | Column              | Description                    |
    |---------------------|--------------------------------|
    | nome_prestadora     | Provider name                  |
    | cnpj_prestadora     | Provider CNPJ                  |
    | uf                  | State                          |
    | cn                  | CN code                        |
    | prefixo             | Prefix                         |
    | faixa_inicial       | Initial range                  |
    | faixa_final         | Final range                    |
    | status              | Status                         |

    CNG (Non-Geographic Codes) - Minimal format:
    | Column                 | Description                    |
    |------------------------|--------------------------------|
    | nome_prestadora        | Provider name                  |
    | cnpj_prestadora        | Provider CNPJ                  |
    | codigo_nao_geografico  | Non-geographic code            |
    | status                 | Status                         |

    SUP (Public Utility Services) - SUP format:
    | Column              | Description                    |
    |---------------------|--------------------------------|
    | nome_prestadora     | Provider name                  |
    | cnpj_prestadora     | Provider CNPJ                  |
    | numero_sup          | SUP number                     |
    | extensao            | Extension                      |
    | uf                  | State                          |
    | cn                  | CN code                        |
    | codigo_municipio    | Municipality code              |
    | nome_municipio      | Municipality name              |
    | instituicao         | Institution                    |
    | tipo                | Type                           |
    | status              | Status                         |
    
    Args:
        input_path: Path to the file or folder containing numbering files
        schema: Database schema name (default: "entrada")
        truncate_table: Whether to truncate tables before import

    Returns:
        dict: Detailed processing statistics including success/error counts,
              processing times, and row counts per file

    Raises:
        FileNotFoundError: If the input path does not exist
        Exception: For database connection or processing errors

    Example:
        # Import single file
        results = load_numbering_reports('/path/to/numbering_file.zip')

        # Import directory with mixed file types
        results = load_numbering_reports('/path/to/numbering_files/')

        # Import with table truncation
        results = load_numbering_reports('/path/to/files/', truncate_table=True)
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file or folder {input_path} not found.")

    if input_path.is_file():
        files_to_import = [input_path]
    elif input_path.is_dir():
        # Look for common numbering file extensions
        files_to_import = sorted(input_path.rglob("*.zip"))
    else:
        logger.error(f"Invalid path: {input_path}")
        return {}

    if not files_to_import:
        logger.warning("No files found to import.")
        return {}

    return _import_multiple_files(
        files_to_import, schema=schema, truncate_table=truncate_table
    )


if __name__ == "__main__":
    # Example usage for testing

    input_path = "/data/cdr/arquivos_auxiliares/abr/numeracao/nsapn/"
    results = load_nsapn_files(input_path, truncate_table=True)
