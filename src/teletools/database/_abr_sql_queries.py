from ._database_config import TB_NUMERACAO, TB_PORTABILIDADE_HISTORICO, TB_PRESTADORAS, TARGET_SCHEMA, IMPORT_SCHEMA, TB_NUMBERS_TO_QUERY

QUERY_NUMBERS_CARRIERS = f"""
-- Query otimizada
SELECT
    ntq.nu_terminal,
    tp.nome_prestadora,
    CASE WHEN up.cod_receptora IS NOT NULL THEN 1 ELSE 0 END AS ind_portado,
    CASE WHEN tn.cod_prestadora IS NOT NULL THEN 1 ELSE 0 END AS ind_designado
FROM {IMPORT_SCHEMA}.{TB_NUMBERS_TO_QUERY} ntq
LEFT JOIN LATERAL (
    SELECT cod_prestadora
    FROM {TARGET_SCHEMA}.{TB_NUMERACAO}
    WHERE faixa_inicial <= ntq.nu_terminal 
      AND faixa_final >= ntq.nu_terminal
    ORDER BY faixa_inicial DESC
    LIMIT 1
) tn ON true
LEFT JOIN LATERAL (
    SELECT cod_receptora
    FROM {TARGET_SCHEMA}.{TB_PORTABILIDADE_HISTORICO}
    WHERE tn_inicial = ntq.nu_terminal
      AND data_agendamento <= %s
    ORDER BY data_agendamento DESC
    LIMIT 1
) up ON true
LEFT JOIN {TARGET_SCHEMA}.{TB_PRESTADORAS} tp
    ON COALESCE(up.cod_receptora, tn.cod_prestadora) = tp.cod_prestadora;
"""
# Example usage:
# data_referencia = '2024-06-30'
# cur.execute(QUERY_NUMBERS_CARRIERS, (data_referencia,))  # PostgreSQL faz conversão implícita