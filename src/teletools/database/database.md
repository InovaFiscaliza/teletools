# Módulo Database - Teletools

Documentação completa do módulo `database` da biblioteca Teletools, que fornece ferramentas para importação e consulta de dados de telecomunicações brasileiras da ABR Telecom (Associação Brasileira de Recursos em Telecomunicações).

## Índice

- [Visão Geral](#visão-geral)
- [Instalação e Configuração](#instalação-e-configuração)
- [Cliente ABR Loader](#cliente-abr-loader)
  - [Comandos Disponíveis](#comandos-disponíveis)
  - [Exemplos de Uso](#exemplos-de-uso)
- [Função query_numbers_carriers](#função-query_numbers_carriers)
  - [Descrição](#descrição)
  - [Parâmetros](#parâmetros)
  - [Retorno](#retorno)
  - [Exemplos de Uso Python](#exemplos-de-uso-python)
- [Estrutura de Dados](#estrutura-de-dados)
- [Arquitetura e Performance](#arquitetura-e-performance)
- [Solução de Problemas](#solução-de-problemas)

## Visão Geral

O módulo `database` oferece funcionalidades essenciais para trabalhar com dados de telecomunicações da ABR Telecom:

- **Importação de Dados**: Cliente de linha de comando para importação eficiente de grandes volumes de dados de portabilidade e numeração
- **Consultas Otimizadas**: Interface de alto nível para consultas de informações de operadoras e portabilidade
- **Performance**: Processamento em chunks e bulk inserts para lidar com milhões de registros
- **Histórico**: Suporte a consultas históricas com datas de referência

### Principais Componentes

1. **abr_loader**: Cliente de linha de comando para importação de dados da ABR
2. **query_numbers_carriers()**: Função para consultas de operadoras e portabilidade
3. **Gerenciamento de Conexão**: Configuração segura via variáveis de ambiente

## Instalação e Configuração

### Pré-requisitos

- Python 3.8 ou superior
- PostgreSQL 12 ou superior
- Pacotes Python: `typer`, `pandas`, `psycopg2`, `python-dotenv`

### Configuração do Banco de Dados

1. **Crie o arquivo de configuração** `~/.teletools.env`:

```bash
# Arquivo: ~/.teletools.env

# Configurações obrigatórias
TELETOOLS_DB_HOST=localhost
TELETOOLS_DB_PORT=5432
TELETOOLS_DB_NAME=telecom_db
TELETOOLS_DB_USER=seu_usuario
TELETOOLS_DB_PASSWORD=sua_senha

# Configurações opcionais
DB_SSLMODE=prefer
DB_CONNECTION_TIMEOUT=30
```

2. **Teste a conexão**:

```bash
abr_loader test-connection
```

Se a conexão for bem-sucedida, você verá:

```
✅ Database connection successful!
✓ Configuration is valid
✓ Server is reachable
✓ Credentials are correct

💡 You can now proceed with data import operations.
```

## Cliente ABR Loader

O `abr_loader` é uma ferramenta de linha de comando (CLI) para importar dados de telecomunicações brasileiras da ABR Telecom para o PostgreSQL.

### Comandos Disponíveis

#### 1. load-pip - Importar Dados de Portabilidade

Importa relatórios de portabilidade numérica do sistema PIP (Plataforma de Integração da Portabilidade) da ABR.

**Sintaxe:**

```bash
abr_loader load-pip INPUT_PATH [OPTIONS]
```

**Parâmetros:**

- `INPUT_PATH`: Caminho para arquivo CSV.gz ou diretório com múltiplos arquivos

**Opções:**

- `--drop-table/--no-drop-table`: Remove tabela de staging após importação (padrão: True (drop-table))
- `--rebuild-database/--no-rebuild-database`: Reconstrói banco de dados antes da importação (padrão: False (no-rebuild-database))
- `--rebuild-indexes/--no-rebuild-indexes`: Reconstrói índices do banco de dados (padrão: False (no-rebuild-indexes))

**Fonte de Dados:**

Os arquivos de portabilidade são obtidos do sistema PIP da ABR Telecom (acesso restrito).

**Exemplo de Uso:**

```bash
# Importar arquivo único
abr_loader load-pip /dados/portabilidade_202412.csv.gz

# Importar diretório completo com rebuild
abr_loader load-pip /dados/portabilidade/ --rebuild-database

# Importar e não remover tabela temporária
abr_loader load-pip /dados/pip_reports/ --no-drop-table
```

#### 2. load-nsapn - Importar Plano de Numeração

Importa dados do plano de numeração brasileiro do portal público da [EASI (Entidade Administradora do Sistema Informatizado)](https://easi.abrtelecom.com.br/nsapn/#/public/files).

**Sintaxe:**

```bash
abr_loader load-nsapn INPUT_PATH [OPTIONS]
```

**Parâmetros:**

- `INPUT_PATH`: Caminho para arquivo ZIP ou diretório com múltiplos arquivos

**Opções:**

- `--drop-table/--no-drop-table`: Remove tabela após importação (padrão: True)

**Tipos de Arquivo Suportados:**

O sistema detecta automaticamente o tipo de arquivo pelo prefixo do nome:

| Prefixo | Descrição | URL de Download |
|---------|-----------|-----------------|
| STFC | Telefonia Fixa Comutada | [Download STFC](https://easi.abrtelecom.com.br/nsapn/#/public/files/download/stfc) |
| SMP | Serviço Móvel Pessoal | [Download SMP](https://easi.abrtelecom.com.br/nsapn/#/public/files/download/smp) |
| SME | Serviço Móvel Especializado | [Download SME](https://easi.abrtelecom.com.br/nsapn/#/public/files/download/sme) |
| CNG | Códigos Não Geográficos (0800, 0300, etc.) | [Download CNG](https://easi.abrtelecom.com.br/nsapn/#/public/files/download/cng) |
| SUP | Serviços de Utilidade Pública | [Download SUP](https://easi.abrtelecom.com.br/nsapn/#/public/files/download/sup) |
| STFC-FATB | STFC Fora da Área de Tarifa Básica | [Download STFC-FATB](https://easi.abrtelecom.com.br/nsapn/#/public/files/download/stfc-fatb) |

**Exemplo de Uso:**

```bash
# Importar arquivo único de STFC
abr_loader load-nsapn /dados/STFC_202412.zip

# Importar todos os arquivos de um diretório
abr_loader load-nsapn /dados/numeracao/

# Importar sem remover dados existentes
abr_loader load-nsapn /dados/nsapn/ --no-drop-table
```

#### 3. test-connection - Testar Conexão

Valida a configuração do banco de dados e testa a conectividade.

**Sintaxe:**

```bash
abr_loader test-connection
```

**Exemplo de Uso:**

```bash
# Testar conexão antes de importar dados
abr_loader test-connection && abr_loader load-pip dados.csv.gz
```

### Exemplos de Uso

#### Workflow Completo de Importação

```bash
# 1. Testar conexão
abr_loader test-connection

# 2. Importar plano de numeração (dados públicos)
abr_loader load-nsapn /dados/nsapn/

# 3. Importar dados de portabilidade (dados restritos)
abr_loader load-pip /dados/portabilidade/ --rebuild-database

# 4. Verificar logs
tail -f abr_portabilidade.log
```

#### Atualização Mensal de Dados

```bash
# Script para atualização mensal
#!/bin/bash

# Baixar arquivos mais recentes do portal NSAPN
# (você precisa implementar o download)

# Importar novos dados sem rebuild
abr_loader load-nsapn /dados/nsapn_202412/ --no-drop-table
abr_loader load-pip /dados/pip_202412/ --no-rebuild-database
```

## Função query_numbers_carriers

A função `query_numbers_carriers()` é a interface principal para consultar informações de operadoras e portabilidade de números telefônicos brasileiros.

### Descrição

Consulta informações de operadora e status de portabilidade para uma lista de números telefônicos, considerando tanto a designação original do plano de numeração quanto operações de portabilidade até uma data de referência específica.

**Características:**

- ✅ Processamento em lote (bulk queries) para alta performance
- ✅ Consultas históricas com data de referência
- ✅ Resolução automática de operadora (numeração + portabilidade)
- ✅ Retorno estruturado com nomes de colunas
- ✅ Arquitetura de conexão única para evitar locks

### Parâmetros

```python
def query_numbers_carriers(numbers_to_query, reference_date=None)
```

#### `numbers_to_query` (obrigatório)

Lista ou iterável de números telefônicos para consulta.

- **Tipo**: `list`, `tuple`, `np.array`, ou qualquer iterável
- **Formato**: Números completos com código de área (10 ou 11 dígitos)
- **Exemplos válidos**:
  - `[11987654321, 11912345678]` (lista de inteiros)
  - `['11987654321', '21912345678']` (lista de strings)
  - `np.array([11987654321, 21912345678])` (numpy array)

**Observações:**
- Números duplicados são automaticamente tratados
- Números com formato inválido (diferente de 10 ou 11 dígitos) não retornam correspondência

#### `reference_date` (opcional)

Data de referência para consulta de portabilidade.

- **Tipo**: `date`, `str`, ou `None`
- **Padrão**: Data atual
- **Formatos aceitos para string**:
  - `'YYYY-MM-DD'` - Formato ISO: `'2024-12-15'`
  - `'DD/MM/YYYY'` - Formato brasileiro: `'15/12/2024'`
  - `'YYYYMMDD'` - Formato compacto: `'20241215'`

**Exemplos:**

```python
from datetime import date

# Usar data atual (padrão)
query_numbers_carriers([11987654321])

# Usar objeto date
query_numbers_carriers([11987654321], reference_date=date(2024, 12, 15))

# Usar string ISO
query_numbers_carriers([11987654321], reference_date='2024-12-15')

# Usar string formato brasileiro
query_numbers_carriers([11987654321], reference_date='15/12/2024')

# Usar string formato compacto
query_numbers_carriers([11987654321], reference_date='20241215')
```

### Retorno

A função retorna um dicionário com duas chaves:

```python
{
    'column_names': tuple,  # Nomes das colunas
    'results': list         # Lista de tuplas com os resultados
}
```

#### Estrutura do Retorno

**`column_names`** (tuple):

Tupla com os nomes das colunas do resultado:

```python
('nu_terminal', 'nome_prestadora', 'ind_portado', 'ind_designado')
```

**`results`** (list):

Lista de tuplas, onde cada tupla representa um número consultado:

```python
[
    (11987654321, 'Vivo', 1, 1),
    (11912345678, 'Tim', 0, 1),
    (21987654321, 'Claro', 1, 1),
    ...
]
```

#### Colunas do Resultado

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `nu_terminal` | `int` | Número telefônico completo (10 ou 11 dígitos) |
| `nome_prestadora` | `str` | Nome da operadora na data de referência (considerando portabilidade) |
| `ind_portado` | `int` | Indicador de portabilidade: `1` se portado, `0` caso contrário |
| `ind_designado` | `int` | Indicador de designação no plano de numeração: `1` se designado, `0` caso contrário |

**Observações sobre os Indicadores:**

- **`ind_portado = 1`**: O número foi portado para outra operadora. `nome_prestadora` mostra a operadora receptora.
- **`ind_portado = 0`**: O número não foi portado. `nome_prestadora` mostra a operadora original do plano de numeração.
- **`ind_designado = 1`**: O número existe no plano de numeração.
- **`ind_designado = 0`**: O número não foi encontrado no plano de numeração (número inválido ou não designado).

### Exemplos de Uso Python

#### Exemplo Básico

```python
from teletools.database import query_numbers_carriers

# Lista de números para consulta
numeros = [11987654321, 11912345678, 21987654321]

# Realizar consulta
resultado = query_numbers_carriers(numeros)

# Acessar nomes das colunas
print("Colunas:", resultado['column_names'])
# Saída: ('nu_terminal', 'nome_prestadora', 'ind_portado', 'ind_designado')

# Iterar sobre os resultados
for registro in resultado['results']:
    numero, operadora, portado, designado = registro
    status = "portado" if portado else "original"
    print(f"Número: {numero}, Operadora: {operadora}, Status: {status}")
```

**Saída esperada:**

```
Colunas: ('nu_terminal', 'nome_prestadora', 'ind_portado', 'ind_designado')
Número: 11987654321, Operadora: Vivo, Status: portado
Número: 11912345678, Operadora: Tim, Status: original
Número: 21987654321, Operadora: Claro, Status: portado
```

#### Exemplo com Pandas DataFrame

```python
import pandas as pd
from teletools.database import query_numbers_carriers

# Números para consulta
numeros = [11987654321, 11912345678, 21987654321, 11998765432]

# Realizar consulta com data de referência
resultado = query_numbers_carriers(numeros, reference_date='2024-12-15')

# Converter para DataFrame
df = pd.DataFrame(resultado['results'], columns=resultado['column_names'])

print(df)
```

**Saída esperada:**

```
    nu_terminal nome_prestadora  ind_portado  ind_designado
0  11987654321            Vivo            1              1
1  11912345678             Tim            0              1
2  21987654321           Claro            1              1
3  11998765432             Oi             0              1
```

#### Exemplo com Consulta Histórica

```python
from datetime import date
from teletools.database import query_numbers_carriers

# Mesmo número em diferentes datas
numero = [11987654321]

# Consultar em dezembro de 2023
resultado_2023 = query_numbers_carriers(numero, reference_date='2023-12-01')
operadora_2023 = resultado_2023['results'][0][1]

# Consultar em dezembro de 2024
resultado_2024 = query_numbers_carriers(numero, reference_date='2024-12-01')
operadora_2024 = resultado_2024['results'][0][1]

print(f"Operadora em 2023: {operadora_2023}")
print(f"Operadora em 2024: {operadora_2024}")

if operadora_2023 != operadora_2024:
    print(f"Número foi portado de {operadora_2023} para {operadora_2024}")
```

#### Exemplo com Múltiplas Consultas

```python
from teletools.database import query_numbers_carriers
import pandas as pd

# Carregar números de um CSV
df_numeros = pd.read_csv('numeros_para_validar.csv')
lista_numeros = df_numeros['telefone'].tolist()

# Consultar em lotes (exemplo: 10000 números por vez)
batch_size = 10000
resultados_completos = []

for i in range(0, len(lista_numeros), batch_size):
    batch = lista_numeros[i:i + batch_size]
    resultado = query_numbers_carriers(batch, reference_date='2024-12-15')
    resultados_completos.extend(resultado['results'])
    print(f"Processados {min(i + batch_size, len(lista_numeros))} de {len(lista_numeros)} números")

# Criar DataFrame com resultados completos
df_resultado = pd.DataFrame(
    resultados_completos,
    columns=['nu_terminal', 'nome_prestadora', 'ind_portado', 'ind_designado']
)

# Salvar resultados
df_resultado.to_csv('resultado_consulta.csv', index=False)
print(f"Total de números processados: {len(df_resultado)}")
```

#### Exemplo com Análise de Portabilidade

```python
from teletools.database import query_numbers_carriers
import pandas as pd

# Consultar números
numeros = df_telefones['numero'].tolist()
resultado = query_numbers_carriers(numeros)

# Converter para DataFrame
df = pd.DataFrame(resultado['results'], columns=resultado['column_names'])

# Estatísticas de portabilidade
print("=== Análise de Portabilidade ===")
print(f"Total de números: {len(df)}")
print(f"Números portados: {df['ind_portado'].sum()}")
print(f"Taxa de portabilidade: {df['ind_portado'].mean() * 100:.2f}%")
print(f"\nNúmeros não designados: {(df['ind_designado'] == 0).sum()}")

# Distribuição por operadora
print("\n=== Distribuição por Operadora ===")
print(df['nome_prestadora'].value_counts())

# Números portados por operadora
df_portados = df[df['ind_portado'] == 1]
print("\n=== Operadoras Receptoras (Números Portados) ===")
print(df_portados['nome_prestadora'].value_counts())
```

#### Exemplo de Tratamento de Erros

```python
from teletools.database import query_numbers_carriers

def consultar_numeros_safe(numeros, data_referencia=None):
    """Wrapper com tratamento de erros para query_numbers_carriers"""
    try:
        # Validar entrada
        if not numeros:
            raise ValueError("Lista de números vazia")
        
        # Realizar consulta
        resultado = query_numbers_carriers(numeros, reference_date=data_referencia)
        
        # Verificar se há resultados
        if not resultado['results']:
            print("Aviso: Nenhum resultado encontrado")
            return None
        
        return resultado
        
    except TypeError as e:
        print(f"Erro de tipo: {e}")
        return None
    except ValueError as e:
        print(f"Erro de valor: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return None

# Uso
numeros = [11987654321, 11912345678]
resultado = consultar_numeros_safe(numeros, '2024-12-15')

if resultado:
    print(f"Consulta bem-sucedida: {len(resultado['results'])} resultados")
```

## Estrutura de Dados

### Schemas do Banco de Dados

O módulo utiliza dois schemas principais:

- **`entrada`** (IMPORT_SCHEMA): Schema temporário para staging e importação de dados
- **`public`** (TARGET_SCHEMA): Schema final com dados consolidados

### Tabelas Principais

#### 1. teletools_tb_numeracao

Tabela de plano de numeração consolidado.

**Colunas principais:**
- `cn`: Código Nacional (área) - 2 dígitos
- `prefixo`: Prefixo do número - 4 ou 5 dígitos
- `faixa_inicial`: Início da faixa de numeração
- `faixa_final`: Fim da faixa de numeração
- `cod_prestadora`: Código da operadora designada
- Outras colunas: localidade, modalidade, tipo de serviço, etc.

#### 2. teletools_tb_portabilidade_historico

Tabela histórica de portabilidade numérica.

**Colunas principais:**
- `cn`: Código Nacional
- `tn_inicial`: Número telefônico portado
- `cod_doadora`: Código da operadora doadora
- `cod_receptora`: Código da operadora receptora
- `data_agendamento`: Data da portabilidade
- `status`: Status da portabilidade

#### 3. teletools_tb_prestadoras

Tabela de cadastro de operadoras.

**Colunas:**
- `cod_prestadora`: Código único da operadora
- `nome_prestadora`: Nome da operadora

### Tabelas Temporárias

#### entrada.teletools_numbers_to_query

Tabela temporária para consultas em lote (criada e destruída por `query_numbers_carriers()`).

**Estrutura:**
```sql
CREATE TABLE entrada.teletools_numbers_to_query (
    nu_terminal BIGINT PRIMARY KEY,
    cn SMALLINT,
    prefixo INTEGER
);
```

## Arquitetura e Performance

### Estratégia de Importação

1. **Processamento em Chunks**: Arquivos grandes são processados em blocos de 100.000 linhas
2. **Bulk Insert com COPY**: Uso do comando COPY do PostgreSQL para máxima performance
3. **Tabelas de Staging**: Dados são primeiro importados para tabelas temporárias
4. **Consolidação**: Dados são então movidos/transformados para tabelas finais

### Estratégia de Consulta

#### query_numbers_carriers()

1. **Criação de Tabela Temporária**: Lista de números é inserida em tabela staging
2. **JOIN Lateral**: Consulta eficiente usando LATERAL joins para buscar numeração e portabilidade
3. **Índices Otimizados**: Consultas aproveitam índices em CN, prefixo e faixas
4. **Conexão Única**: Todas as operações usam a mesma conexão para evitar locks

**Fluxo de resolução de operadora:**

```
Número de entrada
    ↓
Extrair CN e Prefixo
    ↓
Buscar em tb_numeracao (operadora original)
    ↓
Buscar em tb_portabilidade_historico (até data_referencia)
    ↓
Retornar operadora portada OU operadora original
```

### Dicas de Performance

#### Para Importação

```bash
# Para datasets grandes, reconstruir banco e índices de uma vez
abr_loader load-pip /dados/grandes/ --rebuild-database --rebuild-indexes

# Para atualizações incrementais, não reconstruir
abr_loader load-pip /dados/novos/ --no-rebuild-database
```

#### Para Consultas

```python
# Consultar em lotes grandes (10k-100k números por vez) é mais eficiente
# que múltiplas consultas pequenas

# ❌ Ineficiente - múltiplas consultas pequenas
for numero in lista_grande:
    query_numbers_carriers([numero])

# ✅ Eficiente - consulta em lote
query_numbers_carriers(lista_grande)

# ✅ Muito eficiente - lotes de tamanho otimizado
for i in range(0, len(lista_grande), 50000):
    batch = lista_grande[i:i+50000]
    query_numbers_carriers(batch)
```

### Requisitos de Hardware

Para processar datasets completos da ABR:

- **CPU**: 4+ cores recomendado
- **RAM**: 8GB mínimo, 16GB recomendado
- **Disco**: SSD recomendado para PostgreSQL
- **Espaço em disco**:
  - Portabilidade: ~5GB para dados históricos completos
  - Numeração: ~2GB para plano completo
  - Índices: ~3GB adicionais

## Solução de Problemas

### Erro de Conexão

**Problema**: `Database connection failed`

**Soluções:**

1. Verificar arquivo `~/.teletools.env`:
```bash
cat ~/.teletools.env
```

2. Testar conexão:
```bash
abr_loader test-connection
```

3. Verificar se o PostgreSQL está rodando:
```bash
pg_isready -h localhost -p 5432
```

### Erro de Memória

**Problema**: `MemoryError` durante importação

**Soluções:**

1. Processar arquivos menores:
```bash
# Em vez de importar diretório inteiro
abr_loader load-pip /dados/grandes/

# Importar arquivos individualmente
for file in /dados/grandes/*.csv.gz; do
    abr_loader load-pip "$file" --no-rebuild-database
done
```

2. Ajustar CHUNK_SIZE no código (requer modificação do código):
```python
# Em _database_config.py
CHUNK_SIZE = 50000  # Reduzir de 100000 para 50000
```

### Performance Lenta

**Problema**: Consultas ou importações lentas

**Soluções:**

1. Reconstruir índices:
```bash
abr_loader load-pip /dados/ --rebuild-indexes
```

2. Verificar índices no PostgreSQL:
```sql
-- Verificar índices existentes
SELECT schemaname, tablename, indexname 
FROM pg_indexes 
WHERE tablename LIKE 'teletools%';

-- Verificar uso de índices
EXPLAIN ANALYZE
SELECT * FROM public.teletools_tb_numeracao 
WHERE cn = 11 AND prefixo = 9876;
```

3. Vacuum e análise:
```sql
VACUUM ANALYZE public.teletools_tb_numeracao;
VACUUM ANALYZE public.teletools_tb_portabilidade_historico;
```

### Números Não Encontrados

**Problema**: `query_numbers_carriers()` retorna `ind_designado = 0`

**Causas possíveis:**

1. Número não existe no plano de numeração
2. Formato de número inválido (diferente de 10 ou 11 dígitos)
3. Dados de numeração não foram importados

**Verificação:**

```python
from teletools.database import query_numbers_carriers

# Verificar formato
numeros = ['11987654321']  # Deve ter 10 ou 11 dígitos
resultado = query_numbers_carriers(numeros)

for row in resultado['results']:
    if row[3] == 0:  # ind_designado == 0
        print(f"Número {row[0]} não encontrado no plano de numeração")
```

### Tabelas Travadas (Locked)

**Problema**: `relation "..." is locked`

**Soluções:**

1. Verificar transações pendentes:
```sql
SELECT pid, state, query 
FROM pg_stat_activity 
WHERE datname = 'seu_banco' 
AND state = 'idle in transaction';
```

2. Terminar processos travados (cuidado!):
```sql
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'seu_banco' 
AND pid <> pg_backend_pid() 
AND state = 'idle in transaction';
```

### Data de Referência Inválida

**Problema**: `ValueError: Invalid date format`

**Solução**: Use um dos formatos suportados:

```python
# ✅ Formatos válidos
query_numbers_carriers(numeros, reference_date='2024-12-15')
query_numbers_carriers(numeros, reference_date='15/12/2024')
query_numbers_carriers(numeros, reference_date='20241215')

from datetime import date
query_numbers_carriers(numeros, reference_date=date(2024, 12, 15))

# ❌ Formato inválido
query_numbers_carriers(numeros, reference_date='12-15-2024')  # Erro!
```

## Referências

### Fontes de Dados ABR Telecom

- **Portal NSAPN** (Plano de Numeração): https://easi.abrtelecom.com.br/nsapn/#/public/files/download/
- **Sistema PIP** (Portabilidade): Acesso restrito via ABR Telecom

### Documentação Relacionada

- [ABR Loader](../../docs/abr_loader.md)

### Contato e Suporte

Para questões sobre o módulo database:

- **Issues**: Abra uma issue no repositório GitHub
- **Documentação**: Consulte os docstrings nos arquivos Python
- **Logs**: Verifique `abr_portabilidade.log` e `abr_numeracao.log` para detalhes de importação

---

**Última atualização**: Dezembro 2024  
**Versão do módulo**: 0.1.0  
**Autor**: Maxwell Freitas  
**Licença**: Ver LICENSE no repositório
