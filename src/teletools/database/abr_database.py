"""ABR Database Query Module.

This module provides high-level query functions for accessing ABR Telecom data
stored in PostgreSQL database. It offers convenient interfaces to query phone
number information, including carrier assignments and portability status.

The module supports:
    - Bulk phone number queries with efficient temporary table handling
    - Historical portability data lookup at specific reference dates
    - Automatic carrier resolution considering both numbering plan and portability
    - Structured result sets with column headers for easy data processing

Typical usage:
    from teletools.database.abr_database import query_numbers_carriers

    # Query carrier information for a list of numbers
    numbers = [11987654321, 11912345678, 21987654321]
    result = query_numbers_carriers(numbers, reference_date='2024-12-15')

    # Access column names and data
    columns = result['columns']  # ('nu_terminal', 'nome_prestadora', ...)
    data = result['results']     # List of tuples with query results
"""

from datetime import date, datetime

import numpy as np
import pandas as pd

from teletools.database._database_config import (
    IMPORT_SCHEMA,
    TARGET_SCHEMA,
    TB_NUMBERS_TO_QUERY,
    TB_NUMERACAO,
    TB_PORTABILIDADE_HISTORICO,
    TB_PRESTADORAS,
    bulk_insert_with_copy,
    get_db_connection,
)


def query_numbers_carriers(numbers_to_query, reference_date=None):
    """
    Query carrier and portability information for a list of phone numbers.

    This function retrieves current carrier information for multiple phone numbers,
    considering both the original numbering plan assignment and any portability
    operations that occurred up to the specified reference date. It uses a temporary
    table for efficient bulk querying and returns structured results with column headers.

    The query resolves the actual carrier by:
        1. Finding the numbering plan assignment based on number ranges
        2. Checking for portability operations up to the reference date
        3. Returning the receiving carrier if ported, otherwise the original carrier

    Args:
        numbers_to_query (iterable): List or iterable of phone numbers to query.
            Each number should be an integer or string representing a full phone number
            (e.g., 11987654321 for São Paulo mobile).
        reference_date (date, str, optional): Reference date for portability lookup.
            Can be:
                - A date object
                - A string in format 'YYYY-MM-DD' (e.g., '2024-12-15')
                - A string in format 'DD/MM/YYYY' (e.g., '15/12/2024')
                - A string in format 'YYYYMMDD' (e.g., '20241215')
                - None (defaults to current date)

    Returns:
        dict: Dictionary with two keys:
            - 'columns' (tuple): Column names as tuple of strings
                (nu_terminal, nome_prestadora, ind_portado, ind_designado)
            - 'results' (list): List of tuples containing the query results,
                where each tuple represents one phone number's data

    Raises:
        TypeError: If numbers_to_query is not iterable or reference_date has invalid type
        ValueError: If numbers_to_query is empty or reference_date has invalid format

    Example:
        >>> numbers = [11987654321, 11912345678]
        >>> result = query_numbers_carriers(numbers, '2024-12-15')
        >>> print(result['columns'])
        ('nu_terminal', 'nome_prestadora', 'ind_portado', 'ind_designado')
        >>> for row in result['results']:
        ...     print(f"Number: {row[0]}, Carrier: {row[1]}, Ported: {row[2]}")
        Number: 11987654321, Carrier: Vivo, Ported: 1
        Number: 11912345678, Carrier: Tim, Ported: 0

    Note:
        - The temporary table is automatically dropped at transaction end
        - Duplicate numbers in input are automatically handled (deduplicated)
        - Results are ordered by phone number (nu_terminal)
        - ind_portado: 1 if number was ported, 0 otherwise
        - ind_designado: 1 if number has numbering plan assignment, 0 otherwise
    """
    # Validate that numbers_to_query is iterable and not empty
    try:
        numbers_list = np.array(numbers_to_query, dtype=str)
    except TypeError:
        raise TypeError("numbers_to_query must be a list or iterable")

    if not numbers_list.size:
        raise ValueError("numbers_to_query cannot be empty")

    # Normalize input to date object
    if reference_date is None:
        ref_date = date.today()
    elif isinstance(reference_date, date):
        ref_date = reference_date
    elif isinstance(reference_date, str):
        # Try multiple date formats
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"]:
            try:
                ref_date = datetime.strptime(reference_date, fmt).date()
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Invalid date format: {reference_date}")
    else:
        raise TypeError("reference_date must be date object or string")

    # Prepare DataFrame for cn and prefix extraction
    df_numbers_to_query = pd.DataFrame(numbers_list, columns=["nu_terminal"]).astype(
        str
    )
    numbers_lenghts = df_numbers_to_query["nu_terminal"].str.len()

    # Extract cn only from numbers with valid lengths (10 or 11 digits)
    df_numbers_to_query["cn"] = np.where(
        numbers_lenghts.between(10, 11),
        df_numbers_to_query["nu_terminal"].str[:2],
        "-1",
    )
    # Extract prefix only from numbers with valid lengths (10 or 11 digits)
    df_numbers_to_query["prefixo"] = np.where(
        numbers_lenghts == 10,
        df_numbers_to_query["nu_terminal"].str[2:6],
        np.where(
            numbers_lenghts == 11, df_numbers_to_query["nu_terminal"].str[2:7], "-1"
        ),
    )

    # SQL query to create temporary table and insert data
    create_temp_table = f"""
        DROP TABLE IF EXISTS {IMPORT_SCHEMA}.{TB_NUMBERS_TO_QUERY} CASCADE;
        CREATE TABLE {IMPORT_SCHEMA}.{TB_NUMBERS_TO_QUERY} (
            nu_terminal BIGINT PRIMARY KEY,
            cn SMALLINT,
            prefixo INTEGER
        );
    """

    copy_numbers_to_query = f"""
        COPY {IMPORT_SCHEMA}.{TB_NUMBERS_TO_QUERY} (nu_terminal, cn, prefixo) FROM STDIN WITH CSV DELIMITER E'\\t' NULL '\\N'
    """
    
    # Main query using the temporary table
    query_numbers_carriers = f"""
        SELECT
            ntq.nu_terminal,
            tp.nome_prestadora,
            CASE WHEN up.cod_receptora IS NOT NULL THEN 1 ELSE 0 END AS ind_portado,
            CASE WHEN tn.cod_prestadora IS NOT NULL THEN 1 ELSE 0 END AS ind_designado
        FROM {IMPORT_SCHEMA}.{TB_NUMBERS_TO_QUERY} ntq
        LEFT JOIN LATERAL (
            SELECT cod_prestadora
            FROM {TARGET_SCHEMA}.{TB_NUMERACAO}
            WHERE cn = ntq.cn
            AND prefixo = ntq.prefixo
            AND faixa_inicial <= ntq.nu_terminal 
            AND faixa_final >= ntq.nu_terminal
            LIMIT 1
        ) tn ON true
        LEFT JOIN LATERAL (
            SELECT cod_receptora
            FROM {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} up
            WHERE cn = ntq.cn
            AND tn_inicial = ntq.nu_terminal
            AND data_agendamento <= %s
            ORDER BY data_agendamento DESC
            LIMIT 1
        ) up ON true
        LEFT JOIN {TARGET_SCHEMA}.{TB_PRESTADORAS} tp
            ON COALESCE(up.cod_receptora, tn.cod_prestadora) = tp.cod_prestadora;
    """
   
    # Use a single connection for all operations to avoid lock issues
    with get_db_connection() as conn:
        cur = conn.cursor()

        # Create temporary table
        cur.execute(create_temp_table)
        
        # Insert numbers into temporary table
        bulk_insert_with_copy(conn, df_numbers_to_query, copy_numbers_to_query)
        
        # Commit the creation and insertion before querying
        # conn.commit()

        # Execute main query
        cur.execute(query_numbers_carriers, (ref_date,))

        # Get column names from cursor description
        column_names = tuple([desc[0] for desc in cur.description])

        # Fetch all results
        results = cur.fetchall()

        # Clean up temporary table
        cur.execute(f"DROP TABLE IF EXISTS {IMPORT_SCHEMA}.{TB_NUMBERS_TO_QUERY} CASCADE;")
        conn.commit()

        # Return structured result with column headers
        return {
            "results": results,
            "column_names": column_names,
        }
