"""
SQL query constants for ABR portability data import and management.

This module provides SQL scripts for creating, updating, and managing tables related to Brazilian phone number portability data.
It is used by the data import pipeline to automate schema creation, bulk inserts, partitioning, and index management in PostgreSQL.

Key tables:
    - IMPORT_TABLE_PORTABILIDADE: Raw import table for PIP reports
    - TB_PORTABILIDADE_HISTORICO: Partitioned history table for portability events
    - TB_PRESTADORAS: Reference table for unique carriers (operators)

Usage:
    Import scripts are executed via psycopg2 or other database adapters during ETL operations.
    All comments and documentation are in English for international developer teams.
"""

from ._database_config import (
    IMPORT_SCHEMA,
    IMPORT_TABLE_PORTABILIDADE,
    TARGET_SCHEMA,
    TB_PORTABILIDADE_HISTORICO,
    TB_PRESTADORAS,
)

CREATE_IMPORT_TABLE = f"""
    CREATE TABLE IF NOT EXISTS {IMPORT_SCHEMA}.{IMPORT_TABLE_PORTABILIDADE} (
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
    CREATE INDEX IF NOT EXISTS idx_{IMPORT_TABLE_PORTABILIDADE}_tn_inicial ON {IMPORT_SCHEMA}.{IMPORT_TABLE_PORTABILIDADE}(tn_inicial);
    CREATE INDEX IF NOT EXISTS idx_{IMPORT_TABLE_PORTABILIDADE}_data_agendamento ON {IMPORT_SCHEMA}.{IMPORT_TABLE_PORTABILIDADE}(data_agendamento);
    """

COPY_TO_IMPORT_TABLE = f"""
COPY {IMPORT_SCHEMA}.{IMPORT_TABLE_PORTABILIDADE} (
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
"""

CREATE_TB_PORTABILIDADE_HISTORICO = f"""
-- Optimized script to create the tb_portabilidade_historico table
-- Partitioned by CN (area code) with strategic grouping
-- Designed for up to 60 million records

-- Remove the table if it already exists
DROP TABLE IF EXISTS {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} CASCADE;

-- Create the table partitioned by CN
CREATE TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} (
    tn_inicial BIGINT NOT NULL,
    numero_bp BIGINT,
    data_agendamento DATE NOT NULL,
    cod_receptora INTEGER,
    cod_doadora INTEGER,
    cod_status INTEGER,
    ind_portar_origem SMALLINT,
    cn SMALLINT NOT NULL,
    nome_arquivo VARCHAR(255),
    PRIMARY KEY (cn, tn_inicial, data_agendamento)
) 
PARTITION BY LIST (cn);

-- Partition 1: CN 11
CREATE TABLE {TB_PORTABILIDADE_HISTORICO}_cn_11
    PARTITION OF {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}
    FOR VALUES IN (11);

-- Partition 2: CN 12 to 28
CREATE TABLE {TB_PORTABILIDADE_HISTORICO}_cn_12_28
    PARTITION OF {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}
    FOR VALUES IN (12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 24, 27, 28);

-- Partition 3: CN 30 to 55 (CN 30 includes prefixes 300 and 303)
CREATE TABLE {TB_PORTABILIDADE_HISTORICO}_cn_30_55
    PARTITION OF {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}
    FOR VALUES IN (30, 31, 32, 33, 34, 35, 37, 38, 41, 42, 43, 44, 45, 46, 47, 48, 49, 51, 53, 54, 55);

-- Partition 4: CN 61 to 99 (CN 80 includes prefix 800)
CREATE TABLE {TB_PORTABILIDADE_HISTORICO}_cn_61_99
    PARTITION OF {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}
    FOR VALUES IN (61, 62, 63, 64, 65, 66, 67, 68, 69, 71, 73, 74, 75, 77, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 91, 92, 93, 94, 95, 96, 97, 98, 99);

-- DEFAULT partition for unidentified or invalid CNs
CREATE TABLE {TB_PORTABILIDADE_HISTORICO}_cn_default
    PARTITION OF {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}
    DEFAULT;

"""

DROP_TB_PORTABILIDADE_HISTORICO_INDEXES = """
-- Drop all indexes for tb_portabilidade_historico table
DROP INDEX IF EXISTS idx_historico_tn_data;
DROP INDEX IF EXISTS idx_historico_bp;
DROP INDEX IF EXISTS idx_historico_data;
DROP INDEX IF EXISTS idx_historico_receptora;
DROP INDEX IF EXISTS idx_historico_doadora;
DROP INDEX IF EXISTS idx_historico_cn_data;
DROP INDEX IF EXISTS idx_historico_status;
DROP INDEX IF EXISTS idx_historico_fluxo;
"""

CREATE_TB_PORTABILIDADE_HISTORICO_INDEXES = f"""
-- Create all indexes for tb_portabilidade_historico table
DROP INDEX IF EXISTS idx_historico_tn_data;
DROP INDEX IF EXISTS idx_historico_bp;
DROP INDEX IF EXISTS idx_historico_data;
DROP INDEX IF EXISTS idx_historico_receptora;
DROP INDEX IF EXISTS idx_historico_doadora;
DROP INDEX IF EXISTS idx_historico_cn_data;
DROP INDEX IF EXISTS idx_historico_status;
DROP INDEX IF EXISTS idx_historico_fluxo;

CREATE INDEX idx_historico_tn_data 
ON {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} (tn_inicial, data_agendamento DESC);

-- Index for queries by numero_bp
CREATE INDEX idx_historico_bp 
ON {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} (numero_bp)
WHERE numero_bp IS NOT NULL;

-- Index for queries by date (temporal analysis)
CREATE INDEX idx_historico_data 
ON {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} (data_agendamento DESC);

-- Index for queries by recipient operator
CREATE INDEX idx_historico_receptora 
ON {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} (cod_receptora, data_agendamento DESC)
WHERE cod_receptora <> -1;

-- Index for queries by donor operator
CREATE INDEX idx_historico_doadora 
ON {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} (cod_doadora, data_agendamento DESC)
WHERE cod_doadora <> -1;

-- Composite index for analysis by CN and period
CREATE INDEX idx_historico_cn_data 
ON {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} (cn, data_agendamento DESC);

-- Index for queries by status
CREATE INDEX idx_historico_status 
ON {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} (cod_status, data_agendamento DESC);

-- Index for operator combination (portability flow)
CREATE INDEX idx_historico_fluxo 
ON {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} (cod_doadora, cod_receptora, data_agendamento DESC)
WHERE cod_doadora <> -1 AND cod_receptora <> -1;

-- Storage settings for optimization
ALTER TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_11 SET (
    fillfactor = 100,  -- 100% fillfactor because this is a history table (insert only)
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_12_28 SET (
    fillfactor = 100,  -- 100% fillfactor because this is a history table (insert only)
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_30_55 SET (
    fillfactor = 100,  -- 100% fillfactor because this is a history table (insert only)
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_61_99 SET (
    fillfactor = 100,  -- 100% fillfactor because this is a history table (insert only)
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_default SET (
    fillfactor = 100,  -- 100% fillfactor because this is a history table (insert only)
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Analyze the table to update optimizer statistics
ANALYZE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO};
"""

UPDATE_TB_PORTABILIDADE_HISTORICO = f"""
WITH port_entrada AS (
    SELECT DISTINCT ON (
        tn_inicial,
        data_agendamento::date
    )
        tn_inicial,
        numero_bp,
        data_agendamento::date AS data_agendamento,
        COALESCE(cod_receptora, -1) AS cod_receptora,
        COALESCE(cod_doadora, -1)   AS cod_doadora,
        cod_status,
        ind_portar_origem,
        CAST(SUBSTRING(tn_inicial::TEXT, 1, 2) AS SMALLINT) AS cn,
        nome_arquivo
    FROM {IMPORT_SCHEMA}.{IMPORT_TABLE_PORTABILIDADE}
    ORDER BY
        tn_inicial,
        data_agendamento,
        nome_arquivo DESC   -- mantém a linha mais recente
)
INSERT INTO {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} (
    tn_inicial,
    numero_bp,
    data_agendamento,
    cod_receptora,
    cod_doadora,
    cod_status,
    ind_portar_origem,
    cn,
    nome_arquivo
)
SELECT
    tn_inicial,
    numero_bp,
    data_agendamento,
    cod_receptora,
    cod_doadora,
    cod_status,
    ind_portar_origem,
    cn,
    nome_arquivo
FROM port_entrada
ON CONFLICT ON CONSTRAINT {TB_PORTABILIDADE_HISTORICO}_pkey
DO UPDATE SET
    numero_bp         = EXCLUDED.numero_bp,
    cod_receptora     = EXCLUDED.cod_receptora,
    cod_doadora       = EXCLUDED.cod_doadora,
    cod_status        = EXCLUDED.cod_status,
    ind_portar_origem = EXCLUDED.ind_portar_origem,
    nome_arquivo      = EXCLUDED.nome_arquivo;
"""

CREATE_TB_PRESTADORAS = f"""
-- Script to create the TB_PRESTADORAS table
-- Optimized to aggregate all unique carriers (recipient and donor)
-- Treats NULL values as -1 and consolidates into a single record

-- Remove the table if it already exists
DROP TABLE IF EXISTS {TARGET_SCHEMA}.{TB_PRESTADORAS};

-- Create the table with aggregated data
CREATE TABLE {TARGET_SCHEMA}.{TB_PRESTADORAS} AS
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
SELECT * FROM prestadoras;

-- Add primary key
ALTER TABLE {TARGET_SCHEMA}.{TB_PRESTADORAS} 
ADD PRIMARY KEY (cod_prestadora);
"""

UPDATE_TB_PRESTADORAS = f"""
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
