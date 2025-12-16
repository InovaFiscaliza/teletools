"""ABR Portability Data Import Module.

This module provides functionality to import Brazilian phone number portability data
from ABR Telecom PIP system reports. It handles CSV files with portability information
and imports them into a PostgreSQL database with optimized performance using chunked
processing and bulk insert operations.

The module supports:
- Single file or multiple file processing
- Memory-efficient chunked reading
- Bulk database insertions using COPY FROM
- Comprehensive logging and progress tracking
- Data validation and type optimization

Typical usage:
    from _abr_portabilidade import load_pip_reports

    # Import single file
    results = load_pip_reports('/path/to/file.csv.gz')

    # Import all files from directory
    results = load_pip_reports('/path/to/directory/')
"""

import time
from collections.abc import Iterator
from pathlib import Path

import pandas as pd

from teletools.utils import setup_logger

from ._abr_portabilidade_sql_queries import (
    COPY_TO_IMPORT_TABLE_PORTABILIDADE,
    CREATE_IMPORT_TABLE_PORTABILIDADE,
    CREATE_TB_PORTABILIDADE_HISTORICO,
    CREATE_TB_PORTABILIDADE_HISTORICO_INDEXES,
    DROP_TB_PORTABILIDADE_HISTORICO_INDEXES,
    UPDATE_TB_PORTABILIDADE_HISTORICO,
)
from ._abr_prestadoras import update_table_prestadoras
from ._database_config import (
    CHUNK_SIZE,
    IMPORT_SCHEMA,
    IMPORT_TABLE_PORTABILIDADE,
    TARGET_SCHEMA,
    TB_PORTABILIDADE_HISTORICO,
    TB_PRESTADORAS,
    bulk_insert_with_copy,
    check_if_table_exists,
    execute_create_table,
    execute_drop_table,
    execute_truncate_table,
    get_db_connection,
)

# Configure logger
logger = setup_logger("abr_portabilidade.log")


def _read_file_in_chunks(
    file: Path, chunk_size: int = CHUNK_SIZE
) -> Iterator[pd.DataFrame]:
    """
    Read CSV file in chunks for memory-efficient processing.

    Reads semicolon-delimited CSV files from ABR PIP reports in configurable
    chunks to handle large files without memory overflow. Automatically parses
    date columns and optimizes data types using pandas categories.

    Args:
        file: Path to the CSV/compressed file to read (supports .csv.gz)
        chunk_size: Number of rows per chunk (default from CHUNK_SIZE constant)

    Yields:
        pd.DataFrame: Data chunk with processed data types and added filename column

    Raises:
        Exception: If file reading or parsing fails

    Note:
        - Uses Latin-1 encoding for Brazilian Portuguese characters
        - Parses dates in DD/MM/YYYY HH:MM:SS format
        - Applies categorical types for memory optimization
        - Adds 'nome_arquivo' column to track data source
    """
    # Column definitions from ABR PIP system reports
    # Maps to official PIP layout structure
    names = [
        "tipo_registro",        # Record type identifier
        "numero_bp",            # BP number (portability request ID)
        "tn_inicial",           # Initial phone number
        "cod_receptora",        # Receiving carrier code
        "nome_receptora",       # Receiving carrier name
        "cod_doadora",          # Donor carrier code
        "nome_doadora",         # Donor carrier name
        "data_agendamento",     # Scheduled date for portability
        "cod_status",           # Status code
        "status",               # Status description
        "ind_portar_origem",    # Indicator to port back to origin
    ]

    # Optimize data types for memory efficiency
    # Use categories for low-cardinality columns (tipo_registro, status)
    # Use appropriate integer sizes to minimize memory footprint
    dtype = {
        "tipo_registro": "category",   # Limited set of record types
        "numero_bp": "int",            # BP request number
        "tn_inicial": "int",           # Phone number as integer
        "cod_receptora": "str",        # Carrier code (may have leading zeros)
        "nome_receptora": "str",       # Carrier name text
        "cod_doadora": "str",          # Carrier code (may have leading zeros)
        "nome_doadora": "str",         # Carrier name text
        "cod_status": "int",           # Status code number
        "status": "category",          # Limited set of status values
        "ind_portar_origem": "str",    # "Sim" or "Nao" values
    }

    try:
        # Use chunksize for optimized reading
        chunk_reader = pd.read_csv(
            file,
            sep=";",
            names=names,
            header=0,
            chunksize=chunk_size,
            parse_dates=["data_agendamento"],
            date_format="%d/%m/%Y %H:%M:%S",
            dtype=dtype,
            low_memory=True,
        )

        for chunk in chunk_reader:
            chunk["nome_arquivo"] = file.name
            yield _process_chunk(chunk)

    except Exception as e:
        logger.error(f"Error reading file {file}: {e}")
        raise


def _process_chunk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a data chunk by applying optimized transformations.

    Performs data cleaning and type optimization on portability records:
    - Converts text indicators to numeric flags (0/1)
    - Optimizes carrier codes to appropriate integer types
    - Removes records with missing critical identifiers

    Args:
        df: DataFrame chunk to process

    Returns:
        pd.DataFrame: Processed DataFrame with optimized data types and cleaned data

    Note:
        - Maps "Sim"/"Nao" to 1/0 for boolean indicator
        - Converts carrier codes to Int32 (nullable integer)
        - Drops rows missing numero_bp or tn_inicial (required fields)
    """

    # Map Portuguese boolean text to numeric flags for database efficiency
    map_ind_portar_origem = {"Sim": 1, "Nao": 0}

    # Apply mapping efficiently using pandas map function
    df["ind_portar_origem"] = (
        df["ind_portar_origem"].map(map_ind_portar_origem).astype("int8")
    )

    # Convert carrier codes to numeric, handling missing values gracefully
    # Int32 (capital I) allows NULL values, unlike int32
    df["cod_receptora"] = pd.to_numeric(df["cod_receptora"], errors="coerce").astype(
        "Int32"
    )
    df["cod_doadora"] = pd.to_numeric(df["cod_doadora"], errors="coerce").astype(
        "Int32"
    )
    df["cod_status"] = pd.to_numeric(df["cod_status"], errors="coerce").astype("Int16")

    # Remove rows with missing critical identifiers
    # Both numero_bp and tn_inicial are required for portability tracking
    df = df.dropna(subset=["numero_bp", "tn_inicial"])

    return df

# function will be called if rebuild_database is True
def _create_tb_portabilidade_historico() -> bool:
    """
    Create the tb_portabilidade_historico table.

    Returns:
        bool: Always returns True after successful creation

    Raises:
        Exception: If table creation fails
    """
    with get_db_connection() as conn:
        try:
            if not check_if_table_exists(TARGET_SCHEMA, TB_PRESTADORAS):
                update_table_prestadoras()  # ensure prestadoras table exists
            logger.info("Creating tb_portabilidade_historico table...")
            conn.cursor().execute(CREATE_TB_PORTABILIDADE_HISTORICO)
            conn.commit()
            logger.info(
                f"Table {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} created/verified successfully"
            )
        except Exception as e:
            conn.rollback()
            logger.error(
                f"Error creating {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} table: {e}"
            )
            raise
    return True


def _drop_tb_portabilidade_historico() -> None:
    """
    Drop the tb_portabilidade_historico table if it exists.

    Raises:
        Exception: If table drop fails.
    """
    with get_db_connection() as conn:
        try:
            logger.info(
                f"Dropping {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} table..."
            )
            conn.cursor().execute(
                f"DROP TABLE IF EXISTS {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} CASCADE;"
            )
            conn.commit()
            logger.info(
                f"Table {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} dropped successfully"
            )
        except Exception as e:
            conn.rollback()
            logger.error(
                f"Error dropping {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} table: {e}"
            )
            raise


def _create_tb_portabilidade_historico_indexes() -> None:
    """
    Create indexes for the tb_portabilidade_historico table.

    Raises:
        Exception: If index creation fails.
    """
    with get_db_connection() as conn:
        try:
            logger.info(
                f"Creating indexes for {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} table..."
            )
            conn.cursor().execute(CREATE_TB_PORTABILIDADE_HISTORICO_INDEXES)
            conn.commit()
            logger.info(
                f"Indexes for {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} created successfully"
            )
        except Exception as e:
            conn.rollback()
            logger.error(
                f"Error creating indexes for {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} table: {e}"
            )
            raise


def _drop_tb_portabilidade_historico_indexes() -> None:
    """
    Drop indexes for the tb_portabilidade_historico table.

    Raises:
        Exception: If index drop fails.
    """
    with get_db_connection() as conn:
        try:
            logger.info(
                f"Dropping indexes for {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} table..."
            )
            conn.cursor().execute(DROP_TB_PORTABILIDADE_HISTORICO_INDEXES)
            conn.commit()
            logger.info(
                f"Indexes for {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} dropped successfully"
            )
        except Exception as e:
            conn.rollback()
            logger.error(
                f"Error dropping indexes for {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} table: {e}"
            )
            raise


def _update_tb_portabilidade_historico() -> None:
    """
    Update tb_portabilidade_historico with new records from the import table.

    Transfers data from the import table to the partitioned history table,
    performing an upsert operation that updates existing records or inserts
    new ones based on the primary key (cn, tn_inicial, data_agendamento).

    Raises:
        Exception: If table update fails
    """
    with get_db_connection() as conn:
        try:
            logger.info(
                f"Updating {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} table..."
            )
            conn.cursor().execute(UPDATE_TB_PORTABILIDADE_HISTORICO)
            conn.commit()
            logger.info(
                f"Table {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} updated successfully"
            )
        except Exception as e:
            conn.rollback()
            logger.error(
                f"Error updating {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} table: {e}"
            )
            raise


def _import_single_pip_report_file(
    file: Path,
) -> int:
    """
    Import a single portability file into the staging table.

    Processes the CSV file in chunks and performs bulk inserts using PostgreSQL
    COPY FROM for optimal performance.

    Args:
        file: Path to the CSV file to import

    Returns:
        int: Total number of rows imported from the file

    Raises:
        Exception: If file reading or database insertion fails
    """
    start_time = time.time()
    total_rows = 0

    logger.info(f"  Starting import of file {file}.")

    try:
        with get_db_connection() as conn:
            # Process file in memory-efficient chunks to handle large datasets
            chunk_count = 0
            for chunk_df in _read_file_in_chunks(file):
                chunk_count += 1
                chunk_start = time.time()

                # Bulk insert using PostgreSQL COPY for maximum performance
                bulk_insert_with_copy(conn, chunk_df, COPY_TO_IMPORT_TABLE_PORTABILIDADE)
                chunk_rows = len(chunk_df)
                total_rows += chunk_rows
                chunk_time = time.time() - chunk_start
                chunk_time_str = f"{chunk_time:.2f}".replace(".", ",")
                logger.info(
                    f"  Chunk {chunk_count:03d}: {chunk_rows:,} lines inserted in {chunk_time_str}s ({chunk_rows / chunk_time:,.0f} lines/s)".replace(
                        ",", "."
                    )
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


def _import_multiple_pip_reports_files(
    file_list: list[Path],
) -> dict:
    """
    Process multiple portability files sequentially into staging table.

    Truncates the staging table (tb_portabilidade) before processing begins,
    then imports all files using chunked reads and bulk inserts via PostgreSQL
    COPY command for optimal performance. Each file is processed sequentially
    with detailed statistics tracking.

    Args:
        file_list: List of Path objects pointing to compressed CSV files (*.csv.gz)

    Returns:
        dict: Dictionary with filename as key and processing statistics as value.
              Each value contains:
              - status: 'success' or 'error'
              - time: Processing time in seconds
              - lines: Number of rows processed
              - speed: Import speed in rows/second
              - error: Error message (only if status is 'error')
    """
    if not file_list or not isinstance(file_list, list):
        logger.warning("File list is empty or not a list.")
        return {}

    logger.info(f"Starting import of {len(file_list)} files.")

    start_time_total = time.time()
    results = {}
    total_rows_all_files = 0

    # Prepare staging table: create if not exists, then truncate for clean import
    execute_create_table(
        IMPORT_SCHEMA,
        IMPORT_TABLE_PORTABILIDADE,
        CREATE_IMPORT_TABLE_PORTABILIDADE,
        logger,
    )
    # Clear any existing data to ensure clean import state
    execute_truncate_table(IMPORT_SCHEMA, IMPORT_TABLE_PORTABILIDADE, logger)

    # Process each file sequentially with progress tracking
    for idx, file in enumerate(file_list, 1):
        logger.info(f"📁 Processing file {idx}/{len(file_list)}:")

        try:
            file_start = time.time()

            # Import file
            file_rows = _import_single_pip_report_file(file)
            file_time = time.time() - file_start
            total_rows_all_files += file_rows
            results[file.name] = {
                "status": "success",
                "time": file_time,
                "lines": file_rows,
                "speed": file_rows / file_time if file_time > 0 else 0,
            }

        except Exception as e:
            logger.error(f"❌ Error processing {file.name}: {e}")
            results[file.name] = {
                "status": "error",
                "error": str(e),
                "time": 0,
                "lines": 0,
                "speed": 0,
            }

    total_time = time.time() - start_time_total

    # Generate comprehensive import statistics report
    successes = sum(1 for r in results.values() if r["status"] == "success")
    errors = len(results) - successes
    total_rows_all_files_str = f"{total_rows_all_files:,}".replace(",", ".")
    
    # Format time for human-readable display (seconds, minutes, or hours)
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

    # Log comprehensive import summary with statistics
    logger.info("File import report")
    logger.info("══════════════════")
    logger.info(f"📊 Files processed: {len(file_list)}")
    logger.info(f"✅ Successes: {successes}")
    logger.info(f"❌ Errors: {errors}")
    logger.info(f"📈 Total rows: {total_rows_all_files_str}")
    logger.info(f"🕑 Total time: {total_time_str}")
    logger.info(f"🚀 Average speed: {avg_speed_str} rows/s")

    # List files that encountered errors during import
    if errors > 0:
        logger.info("Files with errors:")
        for file_name, stats in results.items():
            if stats["status"] == "error":
                logger.info(f" - {file_name}: {stats['error']}")
    return results


def load_pip_reports(
    input_path: str,
    drop_table: bool = False,
    rebuild_database: bool = False,
    rebuild_indexes: bool = False,
) -> dict:
    """
    Imports portability data from a file or folder.

    The files must be reports extracted from the ABR Telecom PIP system,
    in CSV format (*.csv.gz) with the following columns:

    |Report column           |PIP Layout column |PIP Description         |
    |------------------------|------------------|------------------------|
    |TIPO REG                |                  |                        |
    |NUMERO BP               |POBNROBILHETE     |Número BP               |
    |TN INICIAL              |POBTNINI          |TN Inicial              |
    |RECEPTORA               |CIACODCIA         |Receptora               |
    |RECEPTORA               |POBCIATXTDESC     |Receptora               |
    |DOADORA                 |CIACODCIA_DOA     |Doadora                 |
    |DOADORA                 |POBCIATXTDESC_DOA |Doadora                 |
    |DATA AGENDAMENTO        |POBDATULTAG       |Data Agendamento        |
    |STATUS ATUAL            |POBNROSTATUS      |Status Atual            |
    |STATUS ATUAL            |POBTXTDESCSTATUS  |Status Atual            |
    |IND. PORTAR PARA ORIGEM |POBINDPTO         |Ind. Portar para Origem |

    Example first rows of a CSV file:
    TIPO REG;NUMERO BP;TN INICIAL;RECEPTORA;RECEPTORA;DOADORA;DOADORA;DATA AGENDAMENTO;STATUS ATUAL;STATUS ATUAL;IND. PORTAR PARA ORIGEM
    1;7266080;2139838686;0123;TIM SA;0121;EMBRATEL;11/06/2010 00:00:00;1;Ativo;Nao
    1;7266082;2139838688;0123;TIM SA;0121;EMBRATEL;11/06/2010 00:00:00;1;Ativo;Nao
    1;7266083;2139838689;0123;TIM SA;0121;EMBRATEL;11/06/2010 00:00:00;1;Ativo;Nao
    1;7266084;2139838690;0123;TIM SA;0121;EMBRATEL;11/06/2010 00:00:00;1;Ativo;Nao

    Args:
        input_path: Path to a single CSV file or directory containing CSV files
        drop_table: Whether to drop the import staging table after import.
                    Default is False to append data from multiple imports.
        rebuild_database: Whether to drop and recreate tb_portabilidade_historico
                         table. When True, indexes are also rebuilt automatically.
        rebuild_indexes: Whether to drop and recreate all indexes. Use after
                        large data imports for optimization. Automatically enabled
                        when table is newly created.

    Returns:
        dict: Processing statistics per file with keys as filenames and values
              containing status, processing time, line count, and import speed.

    Raises:
        FileNotFoundError: If the input path does not exist
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file or folder {input_path} not found.")

    if input_path.is_file():
        files_to_import = [input_path]
    elif input_path.is_dir():
        files_to_import = sorted(input_path.rglob("*.csv.gz"))
    else:
        logger.error(f"Invalid path: {input_path}")
        return {}

    if len(files_to_import) == 0:
        logger.warning(f"No CSV (*.csv.gz) files found in {input_path}")
        return {}

    # Step 1: Import all PIP report files to staging table
    results = _import_multiple_pip_reports_files(files_to_import)

    # Step 2: Rebuild target table/indexes if requested (for fresh database setup)
    if rebuild_database:
        _drop_tb_portabilidade_historico()
        _create_tb_portabilidade_historico()
    elif rebuild_indexes:
        # Only rebuild indexes (useful after large data imports)
        _drop_tb_portabilidade_historico_indexes()

    # Step 3: Create indexes if table was just created (always needed for new tables)
    if not check_if_table_exists(TARGET_SCHEMA, TB_PORTABILIDADE_HISTORICO):
        rebuild_indexes = _create_tb_portabilidade_historico()

    # Step 4: Transfer data from staging to partitioned history table (upsert)
    _update_tb_portabilidade_historico()

    # Step 5: Rebuild indexes if requested or if table was newly created
    if rebuild_indexes or rebuild_database:
        _create_tb_portabilidade_historico_indexes()

    # Step 6: Update provider reference table with any new carriers found
    update_table_prestadoras()

    # Step 7: Optionally drop staging table to free disk space
    if drop_table:
        execute_drop_table(IMPORT_SCHEMA, IMPORT_TABLE_PORTABILIDADE, logger)

    return results
