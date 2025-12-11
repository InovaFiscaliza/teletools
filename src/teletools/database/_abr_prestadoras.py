from ._database_config import (
    check_if_table_exists,
    get_db_connection,
    IMPORT_SCHEMA,
    IMPORT_TABLE_CNG,
    IMPORT_TABLE_SUP,
    IMPORT_TABLE_STFC_SMP_SME,
    IMPORT_TABLE_PORTABILIDADE,
    TARGET_SCHEMA,
    TB_PRESTADORAS,
)


from teletools.utils import setup_logger

logger = setup_logger()


UPDATE_TB_PRESTADORAS_FROM_TB_PORTABILIDADE = f"""
-- Script to insert new data into TB_PRESTADORAS table
-- Optimized to insert only carriers that do not already exist in the table
-- Treats NULL values as -1 and avoids duplicates

INSERT INTO {TARGET_SCHEMA}.{TB_PRESTADORAS} (cod_prestadora, nome_prestadora)
WITH prestadoras AS (
    -- Combine all unique carriers (recipient and donor)
    -- Replace NULL with -1 and consolidate into a single record
    SELECT DISTINCT
        COALESCE(cod_receptora, -1) AS cod_prestadora,
        CASE
            WHEN cod_receptora IS NULL THEN 'NÃO IDENTIFICADO'
            ELSE nome_receptora
        END AS nome_prestadora
    FROM {IMPORT_SCHEMA}.{IMPORT_TABLE_PORTABILIDADE}
    WHERE cod_receptora IS NOT NULL OR nome_receptora IS NOT NULL

    UNION
    SELECT DISTINCT
        COALESCE(cod_doadora, -1) AS cod_prestadora,
        CASE
            WHEN cod_doadora IS NULL THEN 'NÃO IDENTIFICADO'
            ELSE nome_doadora
        END AS nome_prestadora
    FROM {IMPORT_SCHEMA}.{IMPORT_TABLE_PORTABILIDADE}
    WHERE cod_doadora IS NOT NULL OR nome_doadora IS NOT NULL

    UNION
    -- Explicitly add the record for unidentified carriers
    SELECT -1 AS cod_prestadora, 'NÃO IDENTIFICADO' AS nome_prestadora
)
SELECT 
    pn.cod_prestadora,
    pn.nome_prestadora
FROM prestadoras pn
LEFT JOIN {TARGET_SCHEMA}.{TB_PRESTADORAS} tp 
    ON pn.cod_prestadora = tp.cod_prestadora
WHERE tp.cod_prestadora IS NULL;  -- Insert only those that do not exist
"""

UPDATE_TB_PRESTADORAS_FROM_TB_NUMERACAO = f"""
-- Script to insert new data into TB_PRESTADORAS table
-- Optimized to insert only carriers that do not already exist in the table
-- Treats NULL values as -1 and avoids duplicates

INSERT INTO {TARGET_SCHEMA}.{TB_PRESTADORAS} (cod_prestadora, nome_prestadora)
WITH prestadoras AS (
    -- Combine all unique carriers from numeracao tables
    -- Replace NULL with -1 and consolidate into a single record
    SELECT DISTINCT
        COALESCE(cnpj_prestadora::bigint, -1) AS cod_prestadora,
        CASE
            WHEN cnpj_prestadora IS NULL THEN 'NÃO IDENTIFICADO'
            ELSE nome_prestadora
        END AS nome_prestadora
    FROM {IMPORT_SCHEMA}.{{}}
    WHERE cnpj_prestadora IS NOT NULL OR nome_prestadora IS NOT NULL

    UNION
    -- Explicitly add the record for unidentified carriers
    SELECT -1 AS cod_prestadora, 'NÃO IDENTIFICADO' AS nome_prestadora
)
SELECT 
    pn.cod_prestadora,
    pn.nome_prestadora
FROM prestadoras pn
LEFT JOIN {TARGET_SCHEMA}.{TB_PRESTADORAS} tp 
    ON pn.cod_prestadora = tp.cod_prestadora
WHERE tp.cod_prestadora IS NULL;  -- Insert only those that do not exist
"""

def _create_table_prestadoras(conn) -> None:
    """Create the TB_PRESTADORAS table if it does not exist."""
    create_table_prestadoras_query = f"""
    CREATE TABLE IF NOT EXISTS {TARGET_SCHEMA}.{TB_PRESTADORAS} (
        cod_prestadora BIGINT PRIMARY KEY,
        nome_prestadora VARCHAR(255)
    );
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(create_table_prestadoras_query)
            conn.commit()
        logger.info(
            f"Table {TARGET_SCHEMA}.{TB_PRESTADORAS} created/verified successfully"
        )
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating table {TARGET_SCHEMA}.{TB_PRESTADORAS}: {e}")
        raise


def update_table_prestadoras() -> None:
    """Update TB_PRESTADORAS with data from IMPORT_TABLE_PORTABILIDADE."""

    import_table_sequence = [
        IMPORT_TABLE_PORTABILIDADE,
        IMPORT_TABLE_CNG,
        IMPORT_TABLE_SUP,
        IMPORT_TABLE_STFC_SMP_SME,
    ]

    with get_db_connection() as conn:
        _create_table_prestadoras(conn)
        try:
            with conn.cursor() as cursor:
                for import_table in import_table_sequence:
                    if check_if_table_exists(IMPORT_SCHEMA, import_table):
                        if import_table == IMPORT_TABLE_PORTABILIDADE:
                            cursor.execute(UPDATE_TB_PRESTADORAS_FROM_TB_PORTABILIDADE)
                        else:
                            query = UPDATE_TB_PRESTADORAS_FROM_TB_NUMERACAO.format(
                                import_table
                            )
                            cursor.execute(query)
                        conn.commit()
                        logger.info(
                            f"Table {TARGET_SCHEMA}.{TB_PRESTADORAS} updated successfully from {IMPORT_SCHEMA}.{import_table}"
                        )
                    else:
                        logger.info(
                            f"Import table {IMPORT_SCHEMA}.{import_table} does not exist. Skipping update."
                        )
            # Final log to indicate completion
            logger.info(
                f"Table {TARGET_SCHEMA}.{TB_PRESTADORAS} updated successfully from all available import tables."
            )
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating table {TARGET_SCHEMA}.{TB_PRESTADORAS}: {e}")
            raise
