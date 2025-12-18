> **[← Voltar para Teletools Database API](../database_api_index.md)**


# `query_numbers_carriers`

Consulta informações de operadora e status de portabilidade para números telefônicos brasileiros.

```python
query_numbers_carriers(numbers_to_query, reference_date=None)
```

**Parâmetros**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `numbers_to_query` | list, tuple, np.array | - | Lista de números telefônicos (10 ou 11 dígitos) |
| `reference_date` | str, date, None | None | Data de referência para consulta histórica |

**Retorna**

`dict` : Dicionário com estrutura:
```python
{
    'column_names': tuple,  # ('nu_terminal', 'nome_prestadora', 'ind_portado', 'ind_designado')
    'results': list         # Lista de tuplas com os dados
}
```

**Colunas do resultado**

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `nu_terminal` | int | Número telefônico completo |
| `nome_prestadora` | str | Nome da operadora atual |
| `ind_portado` | int | 1 se portado, 0 caso contrário |
| `ind_designado` | int | 1 se existe no plano de numeração, 0 caso contrário |

**Exemplos**

```python
from teletools.database import query_numbers_carriers

# Exemplo básico
resultado = query_numbers_carriers([11987654321, 11912345678])
print(resultado['results'])
# [(11987654321, 'Vivo', 1, 1), (11912345678, 'Tim', 0, 1)]

# Com data de referência
resultado = query_numbers_carriers(
    [11987654321], 
    reference_date='2024-12-15'
)

# Com pandas
import pandas as pd
df = pd.DataFrame(resultado['results'], columns=resultado['column_names'])
```

**Formatos de data aceitos**

```python
# String ISO
reference_date='2024-12-15'

# String formato brasileiro
reference_date='15/12/2024'

# String formato compacto
reference_date='20241215'

# Objeto date
from datetime import date
reference_date=date(2024, 12, 15)
```

**Notas**

- Números duplicados são automaticamente tratados
- Números com formato inválido não retornam correspondência
- Consultas em lote (10k-100k números) são mais eficientes
- A função mantém conexão única para todas as operações

---

## Exemplos Práticos

### Consulta Básica

```python
from teletools.database import query_numbers_carriers

numeros = [11987654321, 11912345678, 21987654321]
resultado = query_numbers_carriers(numeros)

for numero, operadora, portado, designado in resultado['results']:
    status = "portado" if portado else "original"
    print(f"{numero}: {operadora} ({status})")
```

### Integração com Pandas

```python
import pandas as pd
from teletools.database import query_numbers_carriers

# Carregar números de CSV
df_input = pd.read_csv('telefones.csv')
numeros = df_input['numero'].tolist()

# Consultar
resultado = query_numbers_carriers(numeros, reference_date='2024-12-15')

# Criar DataFrame
df = pd.DataFrame(resultado['results'], columns=resultado['column_names'])

# Análise
print(f"Taxa de portabilidade: {df['ind_portado'].mean() * 100:.2f}%")
print(df['nome_prestadora'].value_counts())
```

### Consulta Histórica

```python
from teletools.database import query_numbers_carriers

numero = [11987654321]

# Comparar operadoras em diferentes datas
res_2023 = query_numbers_carriers(numero, reference_date='2023-12-01')
res_2024 = query_numbers_carriers(numero, reference_date='2024-12-01')

op_2023 = res_2023['results'][0][1]
op_2024 = res_2024['results'][0][1]

if op_2023 != op_2024:
    print(f"Portado de {op_2023} para {op_2024}")
```

### Processamento em Lote

```python
from teletools.database import query_numbers_carriers
import pandas as pd

# Lista grande de números
df_numeros = pd.read_csv('numeros_grandes.csv')
lista_numeros = df_numeros['telefone'].tolist()

# Processar em lotes
batch_size = 50000
resultados = []

for i in range(0, len(lista_numeros), batch_size):
    batch = lista_numeros[i:i + batch_size]
    res = query_numbers_carriers(batch)
    resultados.extend(res['results'])
    print(f"Processados {i + len(batch)}/{len(lista_numeros)}")

# Consolidar
df_final = pd.DataFrame(
    resultados,
    columns=['nu_terminal', 'nome_prestadora', 'ind_portado', 'ind_designado']
)
df_final.to_csv('resultado.csv', index=False)
```

### Tratamento de Erros

```python
from teletools.database import query_numbers_carriers

def consultar_safe(numeros, data=None):
    try:
        if not numeros:
            raise ValueError("Lista vazia")
        
        resultado = query_numbers_carriers(numeros, reference_date=data)
        
        if not resultado['results']:
            print("Nenhum resultado encontrado")
            return None
            
        return resultado
        
    except Exception as e:
        print(f"Erro: {e}")
        return None

# Uso
resultado = consultar_safe([11987654321, 11912345678])
if resultado:
    print(f"{len(resultado['results'])} números consultados")
```

---

## Estrutura de Dados

### Tabelas Utilizadas

| Tabela | Descrição |
|--------|-----------|
| `public.teletools_tb_numeracao` | Plano de numeração consolidado |
| `public.teletools_tb_portabilidade_historico` | Histórico de portabilidade |
| `public.teletools_tb_prestadoras` | Cadastro de operadoras |

### Fluxo de Resolução

```
Número → Extrair CN/Prefixo → Buscar Numeração → Buscar Portabilidade → Retornar Operadora
```

---

## Performance

### Dicas de Otimização

```python
# ✅ BOM: Consulta em lote grande
query_numbers_carriers(lista_10000_numeros)

# ✅ BOM: Lotes otimizados
for i in range(0, len(lista), 50000):
    batch = lista[i:i+50000]
    query_numbers_carriers(batch)

# ❌ RUIM: Múltiplas consultas pequenas
for numero in lista:
    query_numbers_carriers([numero])  # Muito lento!
```

### Recomendações

- **Tamanho ideal de lote**: 10.000 - 100.000 números
- **Evite**: Consultas individuais em loops
- **Use**: Processamento em lote sempre que possível

---

## Solução de Problemas

### Erro de Conexão

```bash
# Verificar configuração
cat ~/.teletools.env

# Testar conexão
abr_loader test-connection

# Verificar PostgreSQL
docker ps | grep postgre
```

### Números Não Encontrados

Se `ind_designado = 0`:

1. Verificar formato do número (10 ou 11 dígitos)
2. Confirmar que dados foram importados:
   ```bash
   abr_loader load-nsapn /dados/numeracao/
   ```

### Data Inválida

Formatos aceitos:
- ✅ `'2024-12-15'` (ISO)
- ✅ `'15/12/2024'` (BR)
- ✅ `'20241215'` (compacto)
- ✅ `date(2024, 12, 15)` (objeto)
- ❌ `'12-15-2024'` (inválido)

---

## Documentação Relacionada

- **[Teletools](../README.md)** - Visão geral do projeto Teletools
- **[Teletools ABR Loader](abr_loader.md)** - Cliente para importação de dados da ABR Telecom
- **[Teletools CDR Stage Database](cdr_stage.md)** - Configuração do banco de dados PostgreSQL