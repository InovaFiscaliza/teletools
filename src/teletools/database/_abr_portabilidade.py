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
from teletools.database._database_config import get_db_connection

from teletools.utils import setup_logger

# Configure logger
logger = setup_logger("abr_portabilidade.log")

# Performance settings
CHUNK_SIZE = 100000  # Process in chunks of 100k rows

# Table and schema names
IMPORT_SCHEMA = "entrada"
IMPORT_TABLE = "abr_portabilidade"


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


def _create_table_if_not_exists(
    conn, table_name: str = IMPORT_TABLE, schema: str = IMPORT_SCHEMA
) -> None:
    """
    Create optimized table if it doesn't exist.

    Args:
        conn: Database connection
        table_name: Name of the table
        schema: Table schema

    Raises:
        Exception: If table creation fails
    """
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
        tipo_registro INT8,
        numero_bp INT8 NOT NULL,
        tn_inicial INT8 NOT NULL,
        cod_receptora INT2,
        nome_receptora VARCHAR(100),
        cod_doadora INT2,
        nome_doadora VARCHAR(100),
        data_agendamento TIMESTAMP,
        cod_status INT2,
        status VARCHAR(50),
        ind_portar_origem INT2,
        nome_arquivo VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_{table_name}_tn_inicial ON {schema}.{table_name}(tn_inicial);
    CREATE INDEX IF NOT EXISTS idx_{table_name}_data_agendamento ON {schema}.{table_name}(data_agendamento);
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
    conn, df: pd.DataFrame, table_name: str = IMPORT_TABLE, schema: str = IMPORT_SCHEMA
) -> None:
    """
    Perform bulk insert using PostgreSQL COPY FROM for maximum performance.

    Args:
        conn: Database connection
        df: DataFrame to insert
        table_name: Target table name
        schema: Target schema

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
                f"""
                COPY {schema}.{table_name} (
                    tipo_registro, 
                    numero_bp, 
                    tn_inicial, 
                    cod_receptora,
                    nome_receptora, 
                    cod_doadora,
                    nome_doadora, 
                    data_agendamento,
                    cod_status, 
                    status, 
                    ind_portar_origem, 
                    nome_arquivo
                ) FROM STDIN WITH CSV DELIMITER E'\\t' NULL '\\N'
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
    table_name: str = IMPORT_TABLE,
    schema: str = IMPORT_SCHEMA,
    truncate_table: bool = True,
) -> int:
    """
    Import a single portability file into the database.

    Args:
        file: Path to the file to import
        table_name: Target table name
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
            # Create table if necessary
            _create_table_if_not_exists(conn, table_name, schema)
            # Truncate table if requested
            if truncate_table:
                with conn.cursor() as cursor:
                    cursor.execute(f"TRUNCATE TABLE {schema}.{table_name}")
                    conn.commit()
                    logger.info("  Table truncated")

            # Process file in chunks
            chunk_count = 0
            for chunk_df in _read_file_in_chunks(file):
                chunk_count += 1
                chunk_start = time.time()

                # Insert chunk using COPY FROM
                _bulk_insert_with_copy(conn, chunk_df, table_name, schema)

                chunk_rows = len(chunk_df)
                total_rows += chunk_rows
                chunk_time = time.time() - chunk_start
                chunk_time_str = f"{chunk_time:.2f}".replace(".", ",")
                logger.info(
                    f"  Chunk {chunk_count:03d}: {chunk_rows:,} linhas inseridas em {chunk_time_str}s ({chunk_rows / chunk_time:,.0f} linhas/s)".replace(
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


def _import_pip_files(
    file_list: list[Path],
    table_name: str = IMPORT_TABLE,
    schema: str = IMPORT_SCHEMA,
    truncate_table: bool = True,
) -> dict:
    """
    Process multiple portability files sequentially.

    Args:
        file_list: List of files to process
        truncate_table: Whether to truncate table before first import

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
                table_name=table_name,
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
    logger.info(f"🕑 Total time: {total_time_str}s")
    logger.info(f"🚀 Average speed: {avg_speed_str} rows/s")

    if erros > 0:
        logger.info("Files with errors:")
        for file_name, stats in results.items():
            if stats["status"] == "error":
                logger.info(f" - {file_name}: {stats['erro']}")

    return results


def load_pip_reports(
    input_path: str,
    table_name: str = IMPORT_TABLE,
    schema: str = IMPORT_SCHEMA,
    truncate_table: bool = False,
    rebuild_database: bool = False,
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
        input_file_or_folder: Path to the file or folder
        truncate_table: Whether to truncate the table before import

    Returns:
        dict: Detailed processing statistics

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

    _ = _import_pip_files(
        files_to_import,
        table_name=table_name,
        schema=schema,
        truncate_table=truncate_table,
    )

    if rebuild_database:
        _create_tb_portabilidade_historico()

    if not check_table_exists("public", "tb_portabilidade_historico"):
        _create_tb_portabilidade_historico()
        # if table was just created, we need to create indexes as well
        rebuild_database = True

    _update_tb_portabilidade_historico()

    if rebuild_database:
        _create_tb_portabilidade_historico_indexes()


# function will be called if rebuild_database is True
def _create_tb_portabilidade_historico() -> None:
    """
    Create the tb_portabilidade_historico table if it does not exist.

    Args:
        conn: Database connection

    """
    with get_db_connection() as conn:
        try:
            logger.info("Creating tb_portabilidade_historico table...")
            conn.cursor().execute(CREATE_TB_PORTABILIDADE_HISTORICO)
            conn.commit()
            logger.info(
                "Table tb_portabilidade_historico created/verified successfully"
            )
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating tb_portabilidade_historico table: {e}")
            raise


def _create_tb_portabilidade_historico_indexes() -> None:
    """
    Create indexes for the tb_portabilidade_historico table.

    Args:
        conn: Database connection
    """

    with get_db_connection() as conn:
        try:
            logger.info("Creating indexes for tb_portabilidade_historico table...")
            conn.cursor().execute(CREATE_TB_PORTABILIDADE_HISTORICO_INDEXES)
            conn.commit()
            logger.info("Indexes for tb_portabilidade_historico created successfully")
        except Exception as e:
            conn.rollback()
            logger.error(
                f"Error creating indexes for tb_portabilidade_historico table: {e}"
            )
            raise


def _update_tb_portabilidade_historico(
    schema=IMPORT_SCHEMA, table_name=IMPORT_TABLE
) -> None:
    """
    Update the tb_portabilidade_historico table with new records from the
    abr_portabilidade table.

    Args:
        conn: Database connection
        table_name: Source table name
        schema: Source schema
    """
    with get_db_connection() as conn:
        try:
            logger.info("Updating tb_portabilidade_historico table...")
            conn.cursor().execute(
                UPDATE_TB_PORTABILIDADE_HISTORICO.format(
                    schema=schema, table_name=table_name
                )
            )
            conn.commit()
            logger.info("Table tb_portabilidade_historico updated successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating tb_portabilidade_historico table: {e}")
            raise
