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
    CREATE_IMPORT_TABLE_CNG,
    CREATE_IMPORT_TABLE_STFC_SMP_SME,
    CREATE_IMPORT_TABLE_SUP,
    CREATE_TB_NUMERACAO,
    FILE_TYPE_CONFIG,
    IMPORT_SCHEMA,
    IMPORT_TABLE_CNG,
    IMPORT_TABLE_STFC_SMP_SME,
    IMPORT_TABLE_SUP,
)
from ._abr_prestadoras import update_table_prestadoras

# Performance settings
from ._database_config import (
    CHUNK_SIZE,
    TARGET_SCHEMA,
    TB_NUMERACAO,
    execute_create_table,
    execute_drop_table,
    execute_truncate_table,
    get_db_connection,
)

# Configure logger
logger = setup_logger("abr_numeracao.log")


def _get_file_config(file: Path) -> dict:
    """Get configuration for specific file type based on filename.

    Automatically detects file type from filename prefix and returns
    the appropriate configuration for processing.

    Args:
        file: Path to the file to analyze

    Returns:
        dict: Configuration including columns, table name, data types,
              and file type identifier

    Raises:
        ValueError: If file type cannot be determined from filename
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
) -> Iterator[pd.DataFrame]:
    """
    Read CSV file in chunks for memory-efficient processing.

    Reads semicolon-delimited CSV files with Latin-1 encoding in configurable
    chunks. Automatically adds service type and filename columns to each chunk.

    Args:
        file: Path to the CSV file to read
        file_config: Configuration dictionary with columns, dtypes, and file type
        chunk_size: Number of rows per chunk (default from CHUNK_SIZE constant)

    Yields:
        pd.DataFrame: Data chunk with 'servico' (for STFC/SMP_SME) and
                     'nome_arquivo' columns added

    Raises:
        Exception: If file reading or parsing fails
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
    Perform high-performance bulk insert using PostgreSQL COPY FROM.

    Converts DataFrame to tab-delimited format in memory and uses PostgreSQL's
    COPY FROM command for optimal insertion speed.

    Args:
        conn: Active PostgreSQL database connection
        df: DataFrame containing data to insert
        file_config: Configuration dict with 'table_name' and 'table_columns' keys

    Raises:
        Exception: If data conversion or database insertion fails
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
    Create staging table for STFC/SMP/SME data if it doesn't exist.

    Creates the entrada.abr_numeracao table with all columns needed for
    fixed and mobile telephony numbering data.

    Args:
        conn: Active PostgreSQL database connection

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
    Create staging table for CNG (non-geographic codes) data if it doesn't exist.

    Creates the entrada.abr_cng table for importing free call numbers
    (0800, 0300, etc.) and other non-geographic codes.

    Args:
        conn: Active PostgreSQL database connection

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
    Create staging table for SUP (public utility services) data if it doesn't exist.

    Creates the entrada.abr_sup table for importing public utility service
    numbering data.

    Args:
        conn: Active PostgreSQL database connection

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
) -> int:
    """
    Import a single numbering file into the staging table.

    Automatically detects file type from filename, creates the appropriate
    staging table if needed, and processes the file in memory-efficient chunks.

    Args:
        file: Path to the CSV/ZIP file to import

    Returns:
        int: Total number of rows successfully imported

    Raises:
        ValueError: If file type cannot be determined
        Exception: If database operations or file reading fails
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
) -> dict:
    """
    Process multiple numbering files sequentially with progress tracking.

    Imports all files into their respective staging tables with detailed logging
    and error handling. Each file is processed independently.

    Args:
        file_list: List of file paths to process

    Returns:
        dict: Processing statistics per file with keys:
              - status: 'success' or 'error'
              - tempo: Processing time in seconds
              - linhas: Number of rows imported
              - velocidade: Import speed (rows/second)
              - erro: Error message (only present if status is 'error')
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

            # Import file
            file_rows = _import_single_file(file)
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
    if total_time < 60:
        total_time_str = f"{total_time:.2f}s".replace(".", ",")
    elif total_time < 3600:
        minutes = int(total_time // 60)
        seconds = total_time % 60
        total_time_str = f"{minutes}m {seconds:.2f}s".replace(".", ",")
    else:
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = total_time % 60
        total_time_str = f"{hours}h {minutes}m {seconds:.2f}s".replace(".", ",")
    avg_speed_str = f"{total_rows_all_files / total_time:,.0f}".replace(",", ".")

    logger.info("File import report")
    logger.info("══════════════════")
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


def _create_tb_numeracao() -> None:
    """
    Create or recreate the final tb_numeracao table from staging data.

    Drops the existing tb_numeracao table if it exists and recreates it
    by consolidating data from all staging tables (STFC/SMP_SME, CNG, SUP).

    Raises:
        Exception: If table creation or data consolidation fails
    """
    with get_db_connection() as conn:
        try:
            logger.info(f"Updating {TARGET_SCHEMA}.{TB_NUMERACAO} table...")
            conn.cursor().execute(CREATE_TB_NUMERACAO)
            conn.commit()
            logger.info(f"Table {TARGET_SCHEMA}.{TB_NUMERACAO} updated successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating {TARGET_SCHEMA}.{TB_NUMERACAO} table: {e}")
            raise


def load_nsapn_files(input_path: str, drop_table: bool = False) -> dict:
    """
    Import Brazilian telecom numbering plan data from files or folders.

    This function automatically detects the file type based on filename prefix
    and imports the data to the appropriate import table:

    - STFC files → entrada.abr_numeracao table (all columns)
    - SMP/SME files → entrada.abr_numeracao table (subset of columns)
    - CNG files → entrada.abr_cng table (CNG-specific columns)
    - SUP files → entrada.abr_sup table (SUP-specific columns)

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
        input_path: Path to a single file or folder containing numbering files (ZIP format).
                   Files are processed recursively if a directory is provided.
        drop_table: Whether to drop all staging tables after processing completes.
                   Default is False to preserve staging data for inspection.

    Returns:
        dict: Processing statistics per file with keys:
              - status: 'success' or 'error'
              - tempo: Processing time in seconds
              - linhas: Number of rows imported
              - velocidade: Import speed (rows/second)
              - erro: Error message (only if status is 'error')

    Raises:
        FileNotFoundError: If the input path does not exist
        Exception: For database connection or processing errors

    Notes:
        - All staging tables are automatically created and truncated before import
        - After import, data is consolidated into the final tb_numeracao table
        - Provider data is updated in tb_prestadoras table
        - If drop_table=True, staging tables are removed after successful import

    Example:
        # Import single file
        results = load_nsapn_files('/path/to/numbering_file.zip')

        # Import directory with mixed file types
        results = load_nsapn_files('/path/to/numbering_files/')

        # Import and clean up staging tables
        results = load_nsapn_files('/path/to/files/', drop_table=True)
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

    # Ensure import tables exist and are empty before import
    import_table_sequence = [
        IMPORT_TABLE_CNG,
        IMPORT_TABLE_SUP,
        IMPORT_TABLE_STFC_SMP_SME,
    ]

    for table in import_table_sequence:
        execute_create_table(
            IMPORT_SCHEMA,
            table,
            {
                IMPORT_TABLE_STFC_SMP_SME: CREATE_IMPORT_TABLE_STFC_SMP_SME,
                IMPORT_TABLE_CNG: CREATE_IMPORT_TABLE_CNG,
                IMPORT_TABLE_SUP: CREATE_IMPORT_TABLE_SUP,
            }[table],
            logger,
        )
        execute_truncate_table(IMPORT_SCHEMA, table, logger)

    results = _import_multiple_files(files_to_import)

    _create_tb_numeracao()

    update_table_prestadoras()

    if drop_table:
        for table in import_table_sequence:
            execute_drop_table(IMPORT_SCHEMA, table, logger)

    return results
