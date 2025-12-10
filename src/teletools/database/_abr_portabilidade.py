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
from io import StringIO
from pathlib import Path

import pandas as pd

from teletools.utils import setup_logger

from ._abr_portabilidade_sql_queries import (
    COPY_TO_IMPORT_TABLE,
    CREATE_IMPORT_TABLE,
    CREATE_TB_PORTABILIDADE_HISTORICO,
    CREATE_TB_PORTABILIDADE_HISTORICO_INDEXES,
    DROP_TB_PORTABILIDADE_HISTORICO_INDEXES,
    UPDATE_TB_PORTABILIDADE_HISTORICO,
)

from ._database_config import (
    CHUNK_SIZE,
    IMPORT_SCHEMA,
    IMPORT_TABLE_PORTABILIDADE,
    TARGET_SCHEMA,
    TB_PORTABILIDADE_HISTORICO,
    check_if_table_exists,
    get_db_connection,
)

# Configure logger
logger = setup_logger("abr_portabilidade.log")




def _read_file_in_chunks(
    file: Path, chunk_size: int = CHUNK_SIZE
) -> Iterator[pd.DataFrame]:
    """
    Read CSV file in chunks to optimize memory usage.

    Args:
        file: Path to the file
        chunk_size: Size of each chunk

    Yields:
        pd.DataFrame: Data chunk with filename column added

    Raises:
        Exception: If file reading fails
    """
    names = [
        "tipo_registro",
        "numero_bp",
        "tn_inicial",
        "cod_receptora",
        "nome_receptora",
        "cod_doadora",
        "nome_doadora",
        "data_agendamento",
        "cod_status",
        "status",
        "ind_portar_origem",
    ]

    dtype = {
        "tipo_registro": "category",
        "numero_bp": "int",
        "tn_inicial": "int",
        "cod_receptora": "str",
        "nome_receptora": "str",
        "cod_doadora": "str",
        "nome_doadora": "str",
        "cod_status": "int",
        "status": "category",
        "ind_portar_origem": "str",
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

    Args:
        df: DataFrame chunk to process

    Returns:
        pd.DataFrame: Processed DataFrame with optimized data types
    """

    # Optimized mapping using categorical
    map_ind_portar_origem = {"Sim": 1, "Nao": 0}

    # Apply mapping efficiently
    df["ind_portar_origem"] = (
        df["ind_portar_origem"].map(map_ind_portar_origem).astype("int8")
    )

    # Optimize data types
    df["cod_receptora"] = pd.to_numeric(df["cod_receptora"], errors="coerce").astype(
        "Int32"
    )
    df["cod_doadora"] = pd.to_numeric(df["cod_doadora"], errors="coerce").astype(
        "Int32"
    )
    df["cod_status"] = pd.to_numeric(df["cod_status"], errors="coerce").astype("Int16")

    # Remove rows with missing critical data
    df = df.dropna(subset=["numero_bp", "tn_inicial"])

    return df


def _create_import_table_if_not_exists(conn) -> None:
    """
    Create the import table if it doesn't exist.

    Args:
        conn: Database connection

    Raises:
        Exception: If table creation fails
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(CREATE_IMPORT_TABLE)
        conn.commit()
        logger.info(
            f"  Table {IMPORT_SCHEMA}.{IMPORT_TABLE_PORTABILIDADE} created/verified successfully"
        )
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating table: {e}")
        raise


def _bulk_insert_with_copy(conn, df: pd.DataFrame) -> None:
    """
    Perform bulk insert using PostgreSQL COPY FROM for maximum performance.

    Args:
        conn: Database connection
        df: DataFrame to insert

    Raises:
        Exception: If bulk insert fails
    """
    # Create StringIO buffer
    output = StringIO()

    # Convert DataFrame to CSV in memory
    df.to_csv(
        output,
        sep="\t",
        header=False,
        index=False,
        na_rep="\\N",  # NULL representation for PostgreSQL
        date_format="%Y-%m-%d %H:%M:%S",
    )

    output.seek(0)

    try:
        with conn.cursor() as cursor:
            # Use COPY FROM for ultra-fast insertion
            cursor.copy_expert(
                COPY_TO_IMPORT_TABLE,
                output,
            )
        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Error in insertion: {e}")
        raise


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
    truncate_table: bool = True,
) -> int:
    """
    Import a single portability file into the staging table.

    Processes the CSV file in chunks and performs bulk inserts using PostgreSQL
    COPY FROM for optimal performance.

    Args:
        file: Path to the CSV file to import
        truncate_table: Whether to truncate the staging table before import

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
            # Create table if necessary
            _create_import_table_if_not_exists(conn)
            # Truncate table if requested
            if truncate_table:
                with conn.cursor() as cursor:
                    logger.info(f"Truncating {IMPORT_SCHEMA}.{IMPORT_TABLE_PORTABILIDADE} table...")
                    cursor.execute(f"TRUNCATE TABLE {IMPORT_SCHEMA}.{IMPORT_TABLE_PORTABILIDADE}")
                    conn.commit()
                    logger.info(f"Table {IMPORT_SCHEMA}.{IMPORT_TABLE_PORTABILIDADE} truncated")

            # Process file in chunks
            chunk_count = 0
            for chunk_df in _read_file_in_chunks(file):
                chunk_count += 1
                chunk_start = time.time()

                # Insert chunk using COPY FROM
                _bulk_insert_with_copy(conn, chunk_df)

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
    truncate_table: bool = True,
) -> dict:
    """
    Process multiple portability files sequentially.

    Imports all files into the staging table, truncating only before the first
    import if requested. Provides detailed statistics for each file processed.

    Args:
        file_list: List of file paths to process
        truncate_table: Whether to truncate staging table before first import

    Returns:
        dict: Dictionary with filename as key and processing statistics as value.
              Each value contains status, time, lines, and speed metrics.
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
            file_rows = _import_single_pip_report_file(
                file,
                truncate_table=should_truncate,
            )

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

    # Final report
    successes = sum(1 for r in results.values() if r["status"] == "success")
    errors = len(results) - successes
    total_rows_all_files_str = f"{total_rows_all_files:,}".replace(",", ".")
    total_time_str = f"{total_time:.2f}".replace(".", ",")
    avg_speed_str = f"{total_rows_all_files / total_time:,.0f}".replace(",", ".")

    logger.info("File import report")
    logger.info("══════════════════")
    logger.info(f"📊 Files processed: {len(file_list)}")
    logger.info(f"✅ Successes: {successes}")
    logger.info(f"❌ Errors: {errors}")
    logger.info(f"📈 Total rows: {total_rows_all_files_str}")
    logger.info(f"🕑 Total time: {total_time_str}s")
    logger.info(f"🚀 Average speed: {avg_speed_str} rows/s")

    if errors > 0:
        logger.info("Files with errors:")
        for file_name, stats in results.items():
            if stats["status"] == "error":
                logger.info(f" - {file_name}: {stats['error']}")
    return results


def load_pip_reports(
    input_path: str,
    truncate_table: bool = False,
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
        truncate_table: Whether to truncate the import staging table before import.
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

    # import pip files to staging table
    results = _import_multiple_pip_reports_files(
        files_to_import,
        truncate_table=truncate_table,
    )

    # rebuild target table/indexes if requested
    if rebuild_database:
        _drop_tb_portabilidade_historico()
        _create_tb_portabilidade_historico()
    elif rebuild_indexes:
        _drop_tb_portabilidade_historico_indexes()

    # if table was just created, we need to create indexes as well
    if not check_if_table_exists(TARGET_SCHEMA, TB_PORTABILIDADE_HISTORICO):
        rebuild_indexes = _create_tb_portabilidade_historico()

    _update_tb_portabilidade_historico()

    if rebuild_indexes or rebuild_database:
        _create_tb_portabilidade_historico_indexes()

    return results
