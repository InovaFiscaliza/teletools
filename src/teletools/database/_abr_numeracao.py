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

from teletools.utils import setup_logger

# Import and target table names
# Import table definitions and configurations
from ._abr_numeracao_sql_queries import (
    CNG_FILE_COLUMNS,
    CNG_TABLE_COLUMNS,
    CREATE_IMPORT_TABLE_CNG,
    CREATE_IMPORT_TABLE_STFC_SMP_SME,
    CREATE_IMPORT_TABLE_SUP,
    # CREATE_TB_NUMERACAO,
    FILE_TYPE_CONFIG,
    IMPORT_SCHEMA,
    IMPORT_TABLE_CNG,
    IMPORT_TABLE_STFC_SMP_SME,
    IMPORT_TABLE_SUP,
    SMP_SME_FILE_COLUMNS,
    SMP_SME_TABLE_COLUMNS,
    STFC_FILE_COLUMNS,
    STFC_TABLE_COLUMNS,
    SUP_FILE_COLUMNS,
    SUP_TABLE_COLUMNS,
    TARGET_SCHEMA,
    TB_NUMERACAO,
    TB_NUMERACAO_PRESTADORAS,
)

# Performance settings
from ._database_config import CHUNK_SIZE, check_if_table_exists, execute_truncate_table, get_db_connection

# Configure logger
logger = setup_logger("abr_numeracao.log")


def _get_file_config(file: Path) -> dict:
    """Get configuration for specific file type.

    Args:
        file_type: Type of file ('STFC', 'SMP_SME', or 'CNG')

    Returns:
        dict: Configuration including columns, table name, and data types
    """

    filename_upper = file.name.upper()

    if filename_upper.startswith("STFC"):
        file_type = "STFC"
    elif filename_upper.startswith(("SMP", "SME")):
        file_type = "SMP_SME"
    elif filename_upper.startswith("CNG"):
        file_type = "CNG"
    elif filename_upper.startswith("SUP"):
        file_type = "SUP"
    else:
        logger.warning(f"Cannot determine file type for {file.name}.")
        raise ValueError(f"Unknown file type for file {file.name}")

    if file_type in FILE_TYPE_CONFIG:
        return FILE_TYPE_CONFIG[file_type]
    else:
        raise ValueError(f"Unknown file type: {file_type} for file {file.name}")


def _read_file_in_chunks(
    file: Path, file_config: dict, chunk_size: int = CHUNK_SIZE
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

    try:
        # Use chunksize for optimized reading

        chunk_reader = pd.read_csv(
            file,
            sep=";",
            encoding="latin1",
            header=0,
            names=file_config["file_columns"],
            index_col=False,
            chunksize=chunk_size,
            dtype=file_config["dtype"],
            low_memory=True,
        )

        for chunk in chunk_reader:
            # Add servico column for telephony files
            if file_config["file_type"] in ("STFC", "SMP_SME"):
                chunk["servico"] = file_config["file_type"]
            # Add filename column
            chunk["nome_arquivo"] = file.name
            yield chunk
    except Exception as e:
        logger.error(f"Error reading file CHUNK {file}: {e}")
        raise


def _bulk_insert_with_copy(conn, df: pd.DataFrame, file_config: dict) -> None:
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

    # Get table name from file configuration
    table_name = file_config["table_name"]
    # Define column list for COPY command
    copy_columns = ", ".join(file_config["table_columns"])

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

    try:
        with conn.cursor() as cursor:
            # Use COPY FROM for ultra-fast insertion
            cursor.copy_expert(
                f"""
                COPY {IMPORT_SCHEMA}.{table_name} ({copy_columns})
                FROM STDIN WITH CSV DELIMITER E'\\t' NULL '\\N'
                """,
                output,
            )
        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Error in insertion: {e}")
        raise


def _create_import_table_stfc_smp_sme_if_not_exists(
    conn,
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

    try:
        with conn.cursor() as cursor:
            cursor.execute(CREATE_IMPORT_TABLE_STFC_SMP_SME)
        conn.commit()
        logger.info(
            f"Table {IMPORT_SCHEMA}.{IMPORT_TABLE_STFC_SMP_SME} created/verified successfully"
        )
    except Exception as e:
        conn.rollback()
        logger.error(
            f"Error creating table {IMPORT_SCHEMA}.{IMPORT_TABLE_STFC_SMP_SME}: {e}"
        )
        raise


def _create_import_table_cng_if_not_exists(conn) -> None:
    """
    Create CNG table if it doesn't exist.

    Args:
        conn: Database connection
        table_name: Name of the table
        schema: Table schema

    Raises:
        Exception: If table creation fails
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(CREATE_IMPORT_TABLE_CNG)
        conn.commit()
        logger.info(
            f"Table {IMPORT_SCHEMA}.{IMPORT_TABLE_CNG} created/verified successfully"
        )
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating table {IMPORT_SCHEMA}.{IMPORT_TABLE_CNG}: {e}")
        raise


def _create_import_table_sup_if_not_exists(conn) -> None:
    """
    Create SUP table if it doesn't exist.

    Args:
        conn: Database connection
        table_name: Name of the table
        schema: Table schema

    Raises:
        Exception: If table creation fails
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(CREATE_IMPORT_TABLE_SUP)
        conn.commit()
        logger.info(
            f"  Table {IMPORT_SCHEMA}.{IMPORT_TABLE_SUP} created/verified successfully"
        )
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating table {IMPORT_SCHEMA}.{IMPORT_TABLE_SUP}: {e}")
        raise


def _import_single_file(
    file: Path,
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

    logger.info(f"Starting import of file {file}.")

    if file_config := _get_file_config(file):
        file_type = file_config["file_type"]
        table_name = file_config["table_name"]
        logger.info(f"  File type detected for {file.name}: {file_type}")
        logger.info(
            f"  Target table for file {file.name}: {IMPORT_SCHEMA}.{table_name}"
        )
    else:
        logger.warning(f"Unable to get file config for {file.name}. Skipping file.")
        return 0

    try:
        with get_db_connection() as conn:
            if file_type == "STFC" or file_type == "SMP_SME":
                _create_import_table_stfc_smp_sme_if_not_exists(conn)
            elif file_type == "CNG":
                _create_import_table_cng_if_not_exists(conn)
            elif file_type == "SUP":
                _create_import_table_sup_if_not_exists(conn)

            if truncate_table:
                execute_truncate_table(IMPORT_SCHEMA, table_name, logger)

            # Process file in chunks
            chunk_count = 0
            for chunk in _read_file_in_chunks(file, file_config, chunk_size=CHUNK_SIZE):
                chunk_count += 1
                rows_in_chunk = len(chunk)
                _bulk_insert_with_copy(conn, chunk, file_config)
                total_rows += rows_in_chunk
                logger.info(
                    f"    Inserted chunk {chunk_count} with {rows_in_chunk} rows."
                )

        end_time = time.time()
        total_time = end_time - start_time

        total_rows_str = f"{total_rows:,}".replace(",", ".")
        total_time_str = f"{total_time:.2f}".replace(".", ",")
        insert_speed_str = f"{total_rows / total_time:,.0f}".replace(",", ".")

    except Exception as e:
        logger.error(f"Error during import of file {file.name}: {e}")
        raise

    else:
        logger.info(
            f"  ✅ Import of file {file.name} completed: {total_rows_str} rows in {total_time_str}s ({insert_speed_str} rows/s)"
        )
        return total_rows


def _import_multiple_files(
    file_list: list[Path],
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

    if truncate_table:
        logger.info("Truncating all target tables before import...")
        for file_type in FILE_TYPE_CONFIG:
            table_name = FILE_TYPE_CONFIG[file_type]["table_name"]
            execute_truncate_table(IMPORT_SCHEMA, table_name, logger)

    for idx, file in enumerate(file_list, 1):
        logger.info(f"📁 Processing file {idx}/{len(file_list)}:")

        try:
            file_start = time.time()

            # Import file
            file_rows = _import_single_file(
                file,
                truncate_table=False,
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


def load_nsapn_files(input_path: str, truncate_table: bool = False) -> dict:
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

    return _import_multiple_files(files_to_import, truncate_table=truncate_table)


if __name__ == "__main__":
    # Example usage for testing

    input_path = "/data/cdr/arquivos_auxiliares/abr/numeracao/nsapn/"
    results = load_nsapn_files(input_path, truncate_table=True)
