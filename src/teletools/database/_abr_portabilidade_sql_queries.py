"""SQL Query Constants for ABR Portability Data Import and Management.

This module provides SQL scripts for creating, updating, and managing tables
related to Brazilian phone number portability data from ABR Telecom's PIP system.
It is used by the data import pipeline to automate schema creation, bulk inserts,
partitioning, and index management in PostgreSQL.

SQL Query Categories:
    Table Creation:
        - CREATE_IMPORT_TABLE_PORTABILIDADE: Staging table for raw PIP report data
        - CREATE_TB_PORTABILIDADE_HISTORICO: Partitioned final history table

    Data Operations:
        - COPY_TO_IMPORT_TABLE: Bulk insert template for COPY FROM command
        - UPDATE_TB_PORTABILIDADE_HISTORICO: Upsert query from staging to final table

    Index Management:
        - DROP_TB_PORTABILIDADE_HISTORICO_INDEXES: Remove all indexes
        - CREATE_TB_PORTABILIDADE_HISTORICO_INDEXES: Create optimized indexes

Key Tables:
    - entrada.abr_portabilidade: Staging table for raw PIP reports
    - public.tb_portabilidade_historico: Partitioned history table (by CN/area code)

Partitioning Strategy:
    The history table is partitioned by CN (area code) for optimal query performance:
    - Partition 1: CN 11 (São Paulo metropolitan area)
    - Partition 2: CN 12-28 (Southeast and South regions)
    - Partition 3: CN 30-55 (Central-West and North regions)
    - Partition 4: CN 61-99 (Northeast and special codes)
    - Default: Invalid or unrecognized CNs

Usage:
    These SQL queries are executed via psycopg2 during ETL operations.
    All comments and documentation are in English for international teams.

Example:
    from ._abr_portabilidade_sql_queries import CREATE_IMPORT_TABLE_PORTABILIDADE
    
    with conn.cursor() as cursor:
        cursor.execute(CREATE_IMPORT_TABLE_PORTABILIDADE)
        conn.commit()
"""

from ._database_config import (
    IMPORT_SCHEMA,
    IMPORT_TABLE_PORTABILIDADE,
    TARGET_SCHEMA,
    TB_PORTABILIDADE_HISTORICO,
)

CREATE_IMPORT_TABLE_PORTABILIDADE = f"""
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

COPY_TO_IMPORT_TABLE_PORTABILIDADE = f"""
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
-- Partitioned by CN (area code) for efficient querying and maintenance
-- Designed to handle up to 60 million portability records with optimal performance

-- Drop the table if it already exists (including all partitions)
DROP TABLE IF EXISTS {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} CASCADE;

-- Create the main partitioned table
-- Primary key includes CN to ensure partition pruning works correctly
CREATE TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} (
    tn_inicial BIGINT NOT NULL,              -- Phone number (terminal number)
    numero_bp BIGINT,                        -- BP request number (portability request ID)
    data_agendamento DATE NOT NULL,          -- Scheduled portability date
    cod_receptora INTEGER,                   -- Receiving carrier code
    cod_doadora INTEGER,                     -- Donor carrier code
    cod_status INTEGER,                      -- Portability status code
    ind_portar_origem SMALLINT,              -- Indicator to port back to origin (0/1)
    cn SMALLINT NOT NULL,                    -- Area code (first 2 digits)
    nome_arquivo VARCHAR(255),               -- Source filename for audit trail
    PRIMARY KEY (cn, tn_inicial, data_agendamento)  -- Composite PK for unique identification
) 
PARTITION BY RANGE (cn);  -- Partition by area code for locality-based queries

-- Create partitions for strategic CN ranges
-- Partition boundaries chosen based on data distribution and query patterns

-- Partition 1: São Paulo metropolitan area (CN 11)
-- High volume partition, isolated for better performance
CREATE TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_11
PARTITION OF {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}
FOR VALUES FROM (11) TO (12);

-- Partition 2: Southeast region secondary areas (CN 12-20)
-- Includes interior São Paulo, Rio de Janeiro area
CREATE TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_12_20
PARTITION OF {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}
FOR VALUES FROM (12) TO (21);

-- Partition 3: South and more Southeast (CN 21-40)
-- Rio de Janeiro metro, Minas Gerais, Espírito Santo, South region
CREATE TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_21_40
PARTITION OF {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}
FOR VALUES FROM (21) TO (41);

-- Partition 4: Central-West and initial North (CN 41-70)
-- Brasília, Goiás, and start of North region
CREATE TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_41_70
PARTITION OF {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}
FOR VALUES FROM (41) TO (71);

-- Partition 5: Northeast and remaining North (CN 71-99)
-- Bahia, Pernambuco, Ceará, Amazonas, Pará, etc.
CREATE TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_71_99
PARTITION OF {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}
FOR VALUES FROM (71) TO (100);

-- Default partition for unidentified, invalid, or future CNs
-- Catches any CN values outside defined ranges (error handling)
CREATE TABLE {TB_PORTABILIDADE_HISTORICO}_cn_default
    PARTITION OF {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}
    DEFAULT;

"""

DROP_TB_PORTABILIDADE_HISTORICO_INDEXES = f"""
-- Drop all indexes for tb_portabilidade_historico table
DROP INDEX IF EXISTS idx_{TB_PORTABILIDADE_HISTORICO}_cn_tn_data;
"""

CREATE_TB_PORTABILIDADE_HISTORICO_INDEXES = f"""
-- Create optimized indexes for portability history table
-- Drop first to ensure clean recreation
DROP INDEX IF EXISTS idx_{TB_PORTABILIDADE_HISTORICO}_cn_tn_data;

-- Create composite index for efficient lookup queries
-- Order: cn, tn_inicial, data_agendamento DESC
-- This supports: WHERE cn = ? AND tn_inicial = ? ORDER BY data_agendamento DESC
-- INCLUDE clause adds cod_receptora for index-only scans (covering index)
CREATE INDEX idx_{TB_PORTABILIDADE_HISTORICO}_cn_tn_data 
ON {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO} (cn, tn_inicial, data_agendamento DESC)
INCLUDE (cod_receptora);

-- Apply storage optimization settings to all partitions
-- These settings are optimized for append-only history tables

-- Partition 1: São Paulo metro (CN 11) - highest volume
ALTER TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_11 SET (
    fillfactor = 100,  -- 100% page fill for insert-only tables (no updates)
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.05,   -- Vacuum when 5% of table is dead tuples
    autovacuum_analyze_scale_factor = 0.02   -- Analyze when 2% of table changes
);

-- Partition 2: Southeast secondary (CN 12-20)
ALTER TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_12_20 SET (
    fillfactor = 100,
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Partition 3: South and more Southeast (CN 21-40)
ALTER TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_21_40 SET (
    fillfactor = 100,
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Partition 4: Central-West and initial North (CN 41-70)
ALTER TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_41_70 SET (
    fillfactor = 100,
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Partition 5: Northeast and remaining North (CN 71-99)
ALTER TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_71_99 SET (
    fillfactor = 100,
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Default partition: edge cases and invalid CNs
ALTER TABLE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}_cn_default SET (
    fillfactor = 100,
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Update table statistics for query optimizer
-- Essential after bulk data loads or index creation
ANALYZE {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO};
"""

UPDATE_TB_PORTABILIDADE_HISTORICO = f"""
-- Upsert portability records from staging table to partitioned history table
-- Uses CTE for deduplication and ON CONFLICT for efficient upsert

-- Step 1: Deduplicate staging data using DISTINCT ON
-- Keeps only the most recent record for each (tn_inicial, date) combination
WITH port_entrada AS (
    SELECT DISTINCT ON (
        tn_inicial,
        data_agendamento::date  -- Group by phone number and date (ignore time)
    )
        tn_inicial,
        numero_bp,
        data_agendamento::date AS data_agendamento,  -- Convert timestamp to date
        COALESCE(cod_receptora, -1) AS cod_receptora,  -- Replace NULL with -1
        COALESCE(cod_doadora, -1)   AS cod_doadora,    -- Replace NULL with -1
        cod_status,
        ind_portar_origem,
        CAST(SUBSTRING(tn_inicial::TEXT, 1, 2) AS SMALLINT) AS cn,  -- Extract CN from phone
        nome_arquivo
    FROM {IMPORT_SCHEMA}.{IMPORT_TABLE_PORTABILIDADE}
    ORDER BY
        tn_inicial,
        data_agendamento,
        nome_arquivo DESC   -- Keep most recent file's record when duplicates exist
)
-- Step 2: Insert deduplicated records into history table
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
-- Step 3: Handle conflicts (existing records) with UPDATE
-- Primary key: (cn, tn_inicial, data_agendamento)
ON CONFLICT ON CONSTRAINT {TB_PORTABILIDADE_HISTORICO}_pkey
DO UPDATE SET
    numero_bp         = EXCLUDED.numero_bp,         -- Update with new values
    cod_receptora     = EXCLUDED.cod_receptora,
    cod_doadora       = EXCLUDED.cod_doadora,
    cod_status        = EXCLUDED.cod_status,
    ind_portar_origem = EXCLUDED.ind_portar_origem,
    nome_arquivo      = EXCLUDED.nome_arquivo;       -- Track most recent source file
"""
