> **[← Voltar para Teletools Utils API](../utils_api_index.md)**

# `setup_logger`

Configura um logger padronizado com saída simultânea para console e arquivo.

```python
setup_logger(log_file="log.log")
```

**Parâmetros**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `log_file` | str | "log.log" | Caminho do arquivo de log |

**Retorna**

`logging.Logger` : Instância configurada do logger

**Configuração Aplicada**

| Aspecto | Configuração |
|---------|-------------|
| **Nível** | INFO |
| **Formato** | `%(asctime)s - %(levelname)s - %(message)s` |
| **Data** | `%Y-%m-%d %H:%M:%S` |
| **Saídas** | Console (StreamHandler) + Arquivo (FileHandler) |
| **Encoding** | UTF-8 |

**Características**

- Remove handlers existentes para evitar duplicação
- Mensagens aparecem simultaneamente no console e arquivo
- Formato padronizado com timestamp, nível e mensagem
- Encoding UTF-8 para suportar caracteres especiais

**Exemplos**

```python
from teletools.utils import setup_logger

# Configuração básica
logger = setup_logger()
logger.info("Aplicação iniciada")
# 2025-12-18 10:30:45 - INFO - Aplicação iniciada

# Logger com arquivo específico
logger = setup_logger('processamento_cdr.log')
logger.info("Iniciando processamento de CDR")
logger.warning("Arquivo grande detectado")
logger.error("Erro ao processar linha 1523")

# Múltiplos níveis de log
logger = setup_logger('pipeline.log')
logger.debug("Detalhes de debug")      # Não aparece (nível INFO)
logger.info("Informação geral")         # Aparece
logger.warning("Aviso importante")      # Aparece
logger.error("Erro encontrado")         # Aparece
logger.critical("Erro crítico")         # Aparece
```

**Níveis de Log Disponíveis**

| Nível | Método | Uso Típico |
|-------|--------|------------|
| **DEBUG** | `logger.debug()` | Informações detalhadas para diagnóstico |
| **INFO** | `logger.info()` | Confirmação de funcionamento normal |
| **WARNING** | `logger.warning()` | Indicação de problema potencial |
| **ERROR** | `logger.error()` | Erro que afeta funcionalidade |
| **CRITICAL** | `logger.critical()` | Erro grave que pode parar aplicação |

**Notas**

- Logger configurado com nível INFO (DEBUG não aparece por padrão)
- Arquivo de log é criado automaticamente se não existir
- Logs são escritos com encoding UTF-8
- Handlers existentes são limpos para evitar duplicação
- Ambas as saídas (console + arquivo) usam o mesmo formato

---

## Exemplos Práticos

### Pipeline de Processamento CDR

```python
from teletools.utils import setup_logger, inspect_file
from teletools.preprocessing import normalize_number_pair
import pandas as pd

def processar_cdr_com_log(arquivo_entrada, arquivo_saida):
    """
    Processa CDR com logging completo de todas as etapas.
    """
    logger = setup_logger('processamento_cdr.log')
    
    logger.info(f"Iniciando processamento: {arquivo_entrada}")
    
    # Inspeção inicial
    logger.info("Inspecionando arquivo de entrada...")
    inspect_file(arquivo_entrada, nrows=3)
    
    try:
        # Carregar dados
        logger.info("Carregando dados...")
        df = pd.read_csv(arquivo_entrada)
        logger.info(f"Carregados {len(df)} registros")
        
        # Normalizar números
        logger.info("Normalizando números telefônicos...")
        resultado = df.apply(
            lambda row: normalize_number_pair(
                row['numero_origem'],
                row['numero_destino']
            ),
            axis=1
        )
        
        df[['origem_norm', 'origem_valid', 'destino_norm', 'destino_valid']] = \
            pd.DataFrame(resultado.tolist(), index=df.index)
        
        # Validar resultados
        invalidos = len(df[~(df['origem_valid'] & df['destino_valid'])])
        if invalidos > 0:
            logger.warning(f"Encontrados {invalidos} registros com números inválidos")
        
        # Salvar resultado
        logger.info(f"Salvando dados processados em: {arquivo_saida}")
        df.to_csv(arquivo_saida, index=False)
        
        logger.info("Processamento concluído com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"Erro durante processamento: {e}")
        return False

# Uso
sucesso = processar_cdr_com_log(
    'cdr_janeiro.csv.gz',
    'cdr_janeiro_normalizado.csv'
)
```

### Sistema de ETL com Logging

```python
from teletools.utils import setup_logger
from pathlib import Path
import time

def etl_completo(diretorio_origem, diretorio_destino):
    """
    Sistema ETL completo com logging de todas as fases.
    """
    logger = setup_logger('etl_telecom.log')
    
    inicio = time.time()
    logger.info("="*60)
    logger.info("Iniciando processo ETL")
    logger.info(f"Origem: {diretorio_origem}")
    logger.info(f"Destino: {diretorio_destino}")
    logger.info("="*60)
    
    try:
        # Fase 1: Extração
        logger.info("FASE 1: Extração de dados")
        origem = Path(diretorio_origem)
        arquivos = list(origem.glob('*.csv*'))
        logger.info(f"Encontrados {len(arquivos)} arquivos para processar")
        
        # Fase 2: Transformação
        logger.info("FASE 2: Transformação de dados")
        processados = 0
        erros = 0
        
        for arquivo in arquivos:
            try:
                logger.info(f"Processando: {arquivo.name}")
                # Lógica de transformação aqui
                processados += 1
                logger.info(f"✓ {arquivo.name} processado com sucesso")
            except Exception as e:
                erros += 1
                logger.error(f"✗ Erro em {arquivo.name}: {e}")
        
        # Fase 3: Carga
        logger.info("FASE 3: Carga de dados")
        # Lógica de carga aqui
        logger.info(f"Dados carregados em: {diretorio_destino}")
        
        # Relatório final
        duracao = time.time() - inicio
        logger.info("="*60)
        logger.info("RESUMO DO PROCESSAMENTO")
        logger.info(f"Arquivos processados: {processados}")
        logger.info(f"Erros encontrados: {erros}")
        logger.info(f"Duração total: {duracao:.2f} segundos")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.critical(f"Erro crítico no ETL: {e}")
        return False

# Uso
etl_completo('/dados/raw/cdr/', '/dados/processed/cdr/')
```

### Monitoramento de Processamento em Lote

```python
from teletools.utils import setup_logger
import pandas as pd
from datetime import datetime

def processar_lote_com_metricas(arquivos):
    """
    Processa lote de arquivos com métricas detalhadas.
    """
    logger = setup_logger(f'lote_{datetime.now():%Y%m%d_%H%M%S}.log')
    
    logger.info("Iniciando processamento em lote")
    logger.info(f"Total de arquivos: {len(arquivos)}")
    
    metricas = {
        'total': len(arquivos),
        'sucesso': 0,
        'falha': 0,
        'registros_processados': 0,
        'tempo_total': 0
    }
    
    for idx, arquivo in enumerate(arquivos, 1):
        inicio_arquivo = datetime.now()
        logger.info(f"[{idx}/{len(arquivos)}] Processando: {arquivo}")
        
        try:
            df = pd.read_csv(arquivo)
            registros = len(df)
            
            # Processamento aqui
            # ...
            
            metricas['sucesso'] += 1
            metricas['registros_processados'] += registros
            
            duracao = (datetime.now() - inicio_arquivo).total_seconds()
            logger.info(
                f"✓ Concluído: {registros} registros em {duracao:.2f}s"
            )
            
        except Exception as e:
            metricas['falha'] += 1
            logger.error(f"✗ Erro: {e}")
    
    # Relatório final
    logger.info("")
    logger.info("="*60)
    logger.info("RELATÓRIO FINAL")
    logger.info(f"Total: {metricas['total']} arquivos")
    logger.info(f"Sucesso: {metricas['sucesso']}")
    logger.info(f"Falha: {metricas['falha']}")
    logger.info(f"Registros: {metricas['registros_processados']}")
    logger.info(f"Taxa sucesso: {metricas['sucesso']/metricas['total']*100:.1f}%")
    logger.info("="*60)
    
    return metricas

# Uso
arquivos = ['jan.csv', 'fev.csv', 'mar.csv']
resultado = processar_lote_com_metricas(arquivos)
```

### Debug e Troubleshooting

```python
from teletools.utils import setup_logger
import traceback

def processar_com_debug(dados):
    """
    Processamento com logging detalhado para debug.
    """
    logger = setup_logger('debug.log')
    
    logger.info("Iniciando processamento com debug ativado")
    logger.info(f"Tipo de dados: {type(dados)}")
    logger.info(f"Tamanho: {len(dados) if hasattr(dados, '__len__') else 'N/A'}")
    
    try:
        # Checkpoint 1
        logger.info("Checkpoint 1: Validando entrada")
        if not dados:
            logger.warning("Dados vazios recebidos")
            return None
        
        # Checkpoint 2
        logger.info("Checkpoint 2: Processando dados")
        resultado = []
        for idx, item in enumerate(dados):
            try:
                # Processar item
                processado = item * 2  # Exemplo
                resultado.append(processado)
                
                if idx % 100 == 0:
                    logger.info(f"Processados {idx} itens...")
                    
            except Exception as e:
                logger.error(f"Erro no item {idx}: {e}")
                logger.error(f"Valor do item: {item}")
                continue
        
        # Checkpoint 3
        logger.info("Checkpoint 3: Finalizando")
        logger.info(f"Total processado: {len(resultado)}/{len(dados)}")
        
        return resultado
        
    except Exception as e:
        logger.critical(f"Erro crítico: {e}")
        logger.critical(traceback.format_exc())
        raise

# Uso
try:
    resultado = processar_com_debug([1, 2, 3, 4, 5])
except Exception:
    print("Verifique o arquivo debug.log para detalhes")
```

### Integração com Database API

```python
from teletools.utils import setup_logger
from teletools.database import query_numbers_carriers
import pandas as pd

def enriquecer_cdr_com_operadoras(arquivo_cdr):
    """
    Enriquece CDR com informações de operadoras usando logging.
    """
    logger = setup_logger('enriquecimento_cdr.log')
    
    logger.info("Iniciando enriquecimento de CDR")
    logger.info(f"Arquivo: {arquivo_cdr}")
    
    try:
        # Carregar CDR
        logger.info("Carregando CDR...")
        df = pd.read_csv(arquivo_cdr)
        logger.info(f"Carregados {len(df)} registros")
        
        # Extrair números únicos
        logger.info("Extraindo números únicos...")
        numeros = pd.concat([
            df['numero_origem'],
            df['numero_destino']
        ]).unique()
        logger.info(f"Total de números únicos: {len(numeros)}")
        
        # Consultar operadoras
        logger.info("Consultando informações de operadoras...")
        operadoras = query_numbers_carriers(numeros.tolist())
        logger.info(f"Consulta retornou {len(operadoras)} resultados")
        
        # Fazer merge
        logger.info("Mesclando informações...")
        df_op = pd.DataFrame(operadoras)
        df = df.merge(
            df_op[['numero', 'operadora']],
            left_on='numero_origem',
            right_on='numero',
            how='left'
        ).rename(columns={'operadora': 'operadora_origem'})
        
        logger.info("CDR enriquecido com sucesso!")
        return df
        
    except Exception as e:
        logger.error(f"Erro durante enriquecimento: {e}")
        raise

# Uso
df_enriquecido = enriquecer_cdr_com_operadoras('cdr_janeiro.csv')
```

---

## Ver Também

- **[inspect_file](inspect_file.md)** - Inspeção rápida de arquivos
- **[Teletools Utils API](../utils_api_index.md)** - Índice de utilitários
- **[Teletools Database API](../database_api_index.md)** - APIs para consulta de dados

---

**Versão:** 0.0.2  
**Última atualização:** 2025-12-18  
**Status:** Em desenvolvimento ativo
