from ._database_config import (
    IMPORT_SCHEMA,
    IMPORT_TABLE_CNG,
    IMPORT_TABLE_STFC_SMP_SME,
    IMPORT_TABLE_SUP,
    TARGET_SCHEMA,
    TB_NUMERACAO,
)

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

FILE_TYPE_CONFIG = {
    "STFC": {
        "file_type": "STFC",
        "file_columns": list(STFC_FILE_COLUMNS.keys()),
        "table_name": IMPORT_TABLE_STFC_SMP_SME,
        "table_columns": STFC_TABLE_COLUMNS,
        "dtype": STFC_FILE_COLUMNS,
    },
    "SMP_SME": {
        "file_type": "SMP_SME",
        "file_columns": list(SMP_SME_FILE_COLUMNS.keys()),
        "table_name": IMPORT_TABLE_STFC_SMP_SME,
        "table_columns": SMP_SME_TABLE_COLUMNS,
        "dtype": SMP_SME_FILE_COLUMNS,
    },
    "CNG": {
        "file_type": "CNG",
        "file_columns": list(CNG_FILE_COLUMNS.keys()),
        "table_name": IMPORT_TABLE_CNG,
        "table_columns": CNG_TABLE_COLUMNS,
        "dtype": CNG_FILE_COLUMNS,
    },
    "SUP": {
        "file_type": "SUP",
        "file_columns": list(SUP_FILE_COLUMNS.keys()),
        "table_name": IMPORT_TABLE_SUP,
        "table_columns": SUP_TABLE_COLUMNS,
        "dtype": SUP_FILE_COLUMNS,
    },
}

CREATE_IMPORT_TABLE_STFC_SMP_SME = f"""
    CREATE TABLE IF NOT EXISTS {IMPORT_SCHEMA}.{IMPORT_TABLE_STFC_SMP_SME} (
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
    CREATE INDEX IF NOT EXISTS idx_{IMPORT_TABLE_STFC_SMP_SME}_faixa_inicial ON {IMPORT_SCHEMA}.{IMPORT_TABLE_STFC_SMP_SME}(faixa_inicial);
    CREATE INDEX IF NOT EXISTS idx_{IMPORT_TABLE_STFC_SMP_SME}_faixa_final ON {IMPORT_SCHEMA}.{IMPORT_TABLE_STFC_SMP_SME}(faixa_final);
    CREATE INDEX IF NOT EXISTS idx_{IMPORT_TABLE_STFC_SMP_SME}_cnpj ON {IMPORT_SCHEMA}.{IMPORT_TABLE_STFC_SMP_SME}(cnpj_prestadora);
    """

CREATE_IMPORT_TABLE_CNG = f"""
    CREATE TABLE IF NOT EXISTS {IMPORT_SCHEMA}.{IMPORT_TABLE_CNG} (
        nome_prestadora VARCHAR(200),
        cnpj_prestadora VARCHAR(20),
        codigo_nao_geografico VARCHAR(20),
        status VARCHAR(50),
        nome_arquivo VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_{IMPORT_TABLE_CNG}_codigo_nao_geografico ON {IMPORT_SCHEMA}.{IMPORT_TABLE_CNG}(codigo_nao_geografico);
    CREATE INDEX IF NOT EXISTS idx_{IMPORT_TABLE_CNG}_cnpj ON {IMPORT_SCHEMA}.{IMPORT_TABLE_CNG}(cnpj_prestadora);
    """

CREATE_IMPORT_TABLE_SUP = f"""
    CREATE TABLE IF NOT EXISTS {IMPORT_SCHEMA}.{IMPORT_TABLE_SUP} (
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
    CREATE INDEX IF NOT EXISTS idx_{IMPORT_TABLE_SUP}_numero_sup ON {IMPORT_SCHEMA}.{IMPORT_TABLE_SUP}(numero_sup);
    """

CREATE_TB_NUMERACAO = f"""
-- Drop the table if it exists
DROP TABLE IF EXISTS {TARGET_SCHEMA}.{TB_NUMERACAO} CASCADE;
-- Create the optimized table
CREATE TABLE IF NOT EXISTS {TARGET_SCHEMA}.{TB_NUMERACAO} (
    cn SMALLINT NOT NULL,             -- Area code (first 2 digits)
    prefixo INTEGER NOT NULL,         -- Prefix (next 4-5 digits)
    faixa_inicial BIGINT NOT NULL,    -- Range start (full number)
    faixa_final BIGINT NOT NULL,      -- Range end (full number)
    codigo_cnl INTEGER NOT NULL,      -- CNL code
    cod_prestadora BIGINT NOT NULL    -- Provider code (CNPJ)
) WITH (fillfactor = 100);            -- fillfactor=100 for read-only/rarely updated tables

-- Populate the table with STFC/SMP/SME data
INSERT INTO {TARGET_SCHEMA}.{TB_NUMERACAO}
SELECT
    cn::smallint,
    prefixo::integer, 
    concat(cn, prefixo, faixa_inicial)::bigint AS faixa_inicial,  -- Construct full start number
    concat(cn, prefixo, faixa_final)::bigint AS faixa_final,      -- Construct full end number
    COALESCE(codigo_cnl, '-1')::int AS codigo_cnl,
    cnpj_prestadora::bigint AS cod_prestadora
FROM {IMPORT_SCHEMA}.{IMPORT_TABLE_STFC_SMP_SME}
UNION ALL
-- Add CNG (non-geographic codes) data
SELECT
    -- Extract CN and prefix from non-geographic code (similar logic to STFC)
    left(codigo_nao_geografico, 2)::smallint AS cn,
    substring(codigo_nao_geografico from 3 for 4)::integer as prefixo,
    codigo_nao_geografico::bigint AS faixa_inicial,
    codigo_nao_geografico::bigint AS faixa_final,
    -1 AS codigo_cnl,
    cnpj_prestadora::bigint AS cod_prestadora
FROM {IMPORT_SCHEMA}.{IMPORT_TABLE_CNG};
-- TODO: SUP data integration (currently commented out)
-- UNION ALL
-- SELECT
--    concat(numero_sup, extensao)::bigint AS faixa_inicial,
--    concat(numero_sup, extensao)::bigint AS faixa_final,
--    CASE
--        WHEN cn = 'Todos' THEN -1
--        ELSE cn::smallint
--    END AS cn,
--    -1 AS codigo_cnl,
--    cnpj_prestadora::bigint AS cod_prestadora
-- FROM {IMPORT_SCHEMA}.{IMPORT_TABLE_SUP};

-- Create composite B-tree index for efficient range lookups
-- Includes cod_prestadora for index-only scans
CREATE INDEX idx_{TB_NUMERACAO}_cn_prefixo_faixas 
ON {TARGET_SCHEMA}.{TB_NUMERACAO} (cn, prefixo, faixa_inicial, faixa_final) 
INCLUDE (cod_prestadora);

-- Update statistics for query optimizer
ANALYZE {TARGET_SCHEMA}.{TB_NUMERACAO};
"""
