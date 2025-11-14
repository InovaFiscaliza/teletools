import logging
import time
from collections.abc import Iterator
from io import StringIO
from pathlib import Path

import pandas as pd
from _database_config import get_db_connection


# Configuração avançada de logging para console e arquivo
def setup_logger():
    """Configura logger para exibir no console e gravar em arquivo."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Remove handlers existentes para evitar duplicação
    if logger.handlers:
        logger.handlers.clear()
    
    # Formato das mensagens
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Handler para arquivo
    file_handler = logging.FileHandler('abr_portabilidade.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Adicionar handlers ao logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Configurar logger
logger = setup_logger()

# Configurações de performance
CHUNK_SIZE = 100000  # Processar em chunks de 100k linhas

# Nomes das tabelas e esquemas
IMPORT_SCHEMA = "entrada"
IMPORT_TABLE = "abr_portabilidade"


def read_file_in_chunks(
    file: Path, chunk_size: int = CHUNK_SIZE
) -> Iterator[pd.DataFrame]:
    """
    Lê arquivo CSV em chunks para otimizar uso de memória.

    Args:
        file: Caminho para o arquivo
        chunk_size: Tamanho do chunk

    Yields:
        DataFrame: Chunk dos dados
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
        # Usar chunksize para leitura otimizada
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
            yield process_chunk(chunk)

    except Exception as e:
        logger.error(f"Erro ao ler arquivo {file}: {e}")
        raise


def process_chunk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processa um chunk de dados aplicando transformações otimizadas.

    Args:
        df: DataFrame chunk

    Returns:
        DataFrame processado
    """

    # Mapeamento otimizado usando categorical
    map_ind_portar_origem = {"Sim": 1, "Nao": 0}

    # Aplicar mapeamento de forma eficiente
    df["ind_portar_origem"] = (
        df["ind_portar_origem"].map(map_ind_portar_origem).astype("int8")
    )

    # Otimizar tipos de dados
    df["cod_receptora"] = pd.to_numeric(df["cod_receptora"], errors="coerce").astype(
        "Int32"
    )
    df["cod_doadora"] = pd.to_numeric(df["cod_doadora"], errors="coerce").astype(
        "Int32"
    )
    df["cod_status"] = pd.to_numeric(df["cod_status"], errors="coerce").astype("Int16")

    # Remover linhas com dados críticos ausentes
    df = df.dropna(subset=["numero_bp", "tn_inicial"])

    return df


def create_table_if_not_exists(
    conn, table_name: str = IMPORT_TABLE, schema: str = IMPORT_SCHEMA
) -> None:
    """
    Cria tabela otimizada se não existir.

    Args:
        conn: Conexão com banco
        table_name: Nome da tabela
        schema: Schema da tabela
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
    
    -- Criar índices para performance
    CREATE INDEX IF NOT EXISTS idx_{table_name}_tn_inicial ON {schema}.{table_name}(tn_inicial);
    CREATE INDEX IF NOT EXISTS idx_{table_name}_data_agendamento ON {schema}.{table_name}(data_agendamento);
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)
        conn.commit()
        logger.info(f"Tabela {schema}.{table_name} criada/verificada com sucesso")
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao criar tabela: {e}")
        raise


def bulk_insert_with_copy(
    conn, df: pd.DataFrame, table_name: str = IMPORT_TABLE, schema: str = IMPORT_SCHEMA
):
    # Criar StringIO buffer
    output = StringIO()

    # Converter DataFrame para CSV em memória
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
            # Usar COPY FROM para inserção ultra-rápida
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
        logger.error(f"Erro na inserção: {e}")
        raise


def import_single_file(
    file: Path,
    table_name: str = IMPORT_TABLE,
    schema: str = IMPORT_SCHEMA,
    truncate_table: bool = True,
) -> int:
    start_time = time.time()
    total_rows = 0

    logger.info(f"Iniciando importação do arquivo {file}.")

    try:
        with get_db_connection() as conn:
            # Criar tabela se necessário
            create_table_if_not_exists(conn, table_name, schema)

            # Truncar tabela se solicitado
            if truncate_table:
                with conn.cursor() as cursor:
                    cursor.execute(f"TRUNCATE TABLE {schema}.{table_name}")
                conn.commit()
                logger.info("Tabela truncada")

            # Processar arquivo em chunks
            chunk_count = 0
            for chunk_df in read_file_in_chunks(file):
                chunk_count += 1
                chunk_start = time.time()

                # Inserir chunk usando COPY FROM
                bulk_insert_with_copy(conn, chunk_df, table_name, schema)

                chunk_rows = len(chunk_df)
                total_rows += chunk_rows
                chunk_time = time.time() - chunk_start
                chunk_time_str = f"{chunk_time:.2f}".replace(".", ",")
                logger.info(
                    f"Chunk {chunk_count:03d}: {chunk_rows:,} linhas inseridas em {chunk_time_str}s ({chunk_rows / chunk_time:,.0f} linhas/s)".replace(
                        ",", "."
                    )
                )

        end_time = time.time()
        total_time = end_time - start_time

        total_rows_str = f"{total_rows:,}".replace(",", ".")
        total_time_str = f"{total_time:.2f}".replace(".", ",")
        insert_speed_str = f"{total_rows / total_time:,.0f}".replace(",", ".")

    except Exception as e:
        logger.error(f"Erro durante importação: {e}")
        raise

    else:
        logger.info(
            f"✅ Importação do arquivo {file.name} concluída: {total_rows_str} linhas em {total_time_str}s ({insert_speed_str} linhas/s)"
        )
        return total_rows


def import_multiple_files(file_list: list[Path], truncate_table: bool = True) -> dict:
    """
    Processa múltiplos arquivos de portabilidade sequencialmente.

    Args:
        file_list: Lista de arquivos para processar
        truncate_table: Se deve truncar a tabela antes da primeira importação

    Returns:
        dict: Estatísticas detalhadas do processamento
    """
    if not file_list or not isinstance(file_list, list):
        logger.warning("Lista de arquivos está vazia ou não é uma lista.")
        return {}

    logger.info(f"═══ PROCESSAMENTO DE {len(file_list)} ARQUIVOS ═══")

    start_time_total = time.time()
    results = {}
    total_rows_all_files = 0

    for idx, file in enumerate(file_list, 1):
        logger.info(f"📁 Processando arquivo {idx}/{len(file_list)}:")

        try:
            file_start = time.time()

            # Só trunca na primeira importação se solicitado
            should_truncate = truncate_table and idx == 1

            # Importar arquivo
            file_rows = import_single_file(file, truncate_table=should_truncate)

            file_time = time.time() - file_start

            total_rows_all_files += file_rows

            results[file.name] = {
                "status": "sucesso",
                "tempo": file_time,
                "linhas": file_rows,
                "velocidade": file_rows / file_time if file_time > 0 else 0,
            }

        except Exception as e:
            logger.error(f"❌ Erro ao processar {file.name}: {e}")
            results[file.name] = {
                "status": "erro",
                "erro": str(e),
                "tempo": 0,
                "linhas": 0,
                "velocidade": 0,
            }

    total_time = time.time() - start_time_total

    # Relatório final
    sucessos = sum(1 for r in results.values() if r["status"] == "sucesso")
    erros = len(results) - sucessos
    total_rows_all_files_str = f"{total_rows_all_files:,}".replace(",", ".")
    total_time_str = f"{total_time:.2f}".replace(".", ",")
    avg_speed_str = f"{total_rows_all_files / total_time:,.0f}".replace(",", ".")

    logger.info(f"""
    
    ═══════════════════════════════════════════════════════════════════════
    RELATÓRIO FINAL - PROCESSAMENTO DE MÚLTIPLOS ARQUIVOS
    ═══════════════════════════════════════════════════════════════════════
    📊 Arquivos processados: {len(file_list)}
    ✅ Sucessos: {sucessos}
    ❌ Erros: {erros}
    📈 Total de linhas: {total_rows_all_files_str}
    ⏱️  Tempo total: {total_time_str}s
    🚀 Velocidade média: {avg_speed_str} linhas/s
    ═══════════════════════════════════════════════════════════════════════
    
    """)

    return results

if __name__ == "__main__":
    folder = Path(
        "/data/cdr/arquivos_auxiliares/abr/portabilidade/pip"
    )
    files = sorted(folder.rglob("*.csv.gz"))
    import_multiple_files(files, truncate_table=True)
