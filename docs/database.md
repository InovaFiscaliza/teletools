# Teletools ABR Database

> **[← Voltar para o README principal](../README.md)** | [ABR Loader](abr_loader.md) | [CDR Stage Database](cdr_stage.md)

Documentação do módulo `abr_database` da biblioteca Teletools para consulta de dados de telecomunicações brasileiras da ABR Telecom (Associação Brasileira de Recursos em Telecomunicações).

## Índice

- [Teletools ABR Database](#teletools-abr-database)
  - [Índice](#índice)
  - [Visão Geral](#visão-geral)
    - [Características Principais](#características-principais)
  - [Instalação e Configuração](#instalação-e-configuração)
    - [Pré-requisitos](#pré-requisitos)
    - [Instalação](#instalação)
    - [Configuração do Banco de Dados](#configuração-do-banco-de-dados)
  - [Função query\_numbers\_carriers](#função-query_numbers_carriers)
    - [Descrição](#descrição)
    - [Parâmetros](#parâmetros)
      - [`numbers_to_query` (obrigatório)](#numbers_to_query-obrigatório)
      - [`reference_date` (opcional)](#reference_date-opcional)
    - [Retorno](#retorno)
      - [Estrutura do Retorno](#estrutura-do-retorno)
      - [Colunas do Resultado](#colunas-do-resultado)
    - [Exemplos de Uso Python](#exemplos-de-uso-python)
      - [Exemplo Básico](#exemplo-básico)
      - [Exemplo com Pandas DataFrame](#exemplo-com-pandas-dataframe)
      - [Exemplo com Consulta Histórica](#exemplo-com-consulta-histórica)
      - [Exemplo com Múltiplas Consultas](#exemplo-com-múltiplas-consultas)
      - [Exemplo com Análise de Portabilidade](#exemplo-com-análise-de-portabilidade)
      - [Exemplo de Tratamento de Erros](#exemplo-de-tratamento-de-erros)
  - [Estrutura de Dados](#estrutura-de-dados)
    - [Schemas do Banco de Dados](#schemas-do-banco-de-dados)
    - [Tabelas Principais](#tabelas-principais)
      - [1. teletools\_tb\_numeracao](#1-teletools_tb_numeracao)
      - [2. teletools\_tb\_portabilidade\_historico](#2-teletools_tb_portabilidade_historico)
      - [3. teletools\_tb\_prestadoras](#3-teletools_tb_prestadoras)
    - [Tabelas Temporárias](#tabelas-temporárias)
      - [entrada.teletools\_numbers\_to\_query](#entradateletools_numbers_to_query)
  - [Arquitetura e Performance](#arquitetura-e-performance)
    - [Estratégia de Consulta - query\_numbers\_carriers()](#estratégia-de-consulta---query_numbers_carriers)
    - [Dicas de Performance](#dicas-de-performance)
  - [Solução de Problemas](#solução-de-problemas)
    - [Erro de Conexão](#erro-de-conexão)
  - [Solução de Problemas](#solução-de-problemas-1)
    - [Erro de Conexão com Banco de Dados](#erro-de-conexão-com-banco-de-dados)
    - [Números Não Encontrados](#números-não-encontrados)
    - [Tabelas Travadas (Locked)](#tabelas-travadas-locked)
    - [Data de Referência Inválida](#data-de-referência-inválida)
  - [Referências](#referências)
    - [Fontes de Dados ABR Telecom](#fontes-de-dados-abr-telecom)
  - [Contribuindo](#contribuindo)
  - [Licença](#licença)
  - [Contato e Suporte](#contato-e-suporte)

## Visão Geral

O módulo Teletools ABR Database (`abr_database`) oferece interface Python de alto nível para consulta de dados de telecomunicações armazenados no banco de dados PostgreSQL. Permite consultar informações de operadoras e status de portabilidade para números telefônicos brasileiros considerando o histórico completo de portabilidade.

### Características Principais

- ✅ **Consultas em Lote**: Processamento eficiente de milhares de números em uma única operação
- ✅ **Consultas Históricas**: Suporte a datas de referência para análise temporal
- ✅ **Resolução Automática**: Determina operadora atual considerando numeração + portabilidade
- ✅ **Retorno Estruturado**: Resultados com nomes de colunas para fácil integração
- ✅ **Alta Performance**: Arquitetura otimizada com conexão única e bulk inserts
- ✅ **API Simples**: Interface Python intuitiva para scripts e aplicações

> **Nota:** Para importar dados da ABR Telecom (portabilidade e numeração), consulte a documentação do [Cliente ABR Loader](abr_loader.md).

## Instalação e Configuração

### Pré-requisitos

- Python 3.13+ com gerenciador de pacotes [UV](https://docs.astral.sh/uv/)
- Banco de dados [Teletools CDR Stage Database](cdr_stage.md) com dados da ABR importados


### Instalação

```bash
# Clone o repositório
git clone https://github.com/InovaFiscaliza/teletools.git
cd teletools

# Instale as dependências
uv sync

# Ative o ambiente virtual
source .venv/bin/activate
```

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

2. **Importe os dados da ABR** (se ainda não foi feito):

Consulte a documentação do [Cliente ABR Loader](abr_loader.md) para instruções detalhadas sobre como importar dados de portabilidade e numeração.

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

### Estratégia de Consulta - query_numbers_carriers()

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

## Solução de Problemas

### Erro de Conexão com Banco de Dados

**Problema**: `Database connection failed`

**Soluções:**

1. Verificar arquivo `~/.teletools.env`
2. Testar conexão:
```bash
abr_loader test-connection
```
3. Verificar se o PostgreSQL está rodando:
```bash
(teletools) $ docker ps
CONTAINER ID   IMAGE            COMMAND                  CREATED      STATUS      PORTS                                              NAMES
5b2bb3845977   dpage/pgadmin4   "/entrypoint.sh"         5 days ago   Up 5 days   443/tcp, 0.0.0.0:5050->80/tcp, [::]:5050->80/tcp   pgadmin-cdr
cba7220ab8ca   postgrescdr      "docker-entrypoint.s…"   5 days ago   Up 5 days   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp        postgre-cdr
(teletools) $ docker exec -it postgre-cdr pg_isready
/var/run/postgresql:5432 - accepting connections
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

## Contribuindo

Para contribuir com melhorias neste módulo:
1. Fork o repositório `teletools`
2. Crie um branch para sua feature
3. Implemente testes para novas funcionalidades
4. Submeta um pull request

## Licença

Este módulo é parte do projeto `teletools` e segue a mesma licença do projeto principal.

## Contato e Suporte

Para questões, bugs ou sugestões:
- Abra uma issue no repositório do projeto
- Consulte a documentação adicional em `/docs`

---

**Versão:** 0.0.2
**Última atualização:** 2025-12-17
**Status:** Em desenvolvimento ativo
