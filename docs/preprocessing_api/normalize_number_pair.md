> **[← Voltar para Teletools Preprocessing API](../preprocessing_api_index.md)**

# `normalize_number_pair`

Normaliza um par de números telefônicos brasileiros relacionados com inferência contextual de código de área.

```python
normalize_number_pair(number_a, number_b, national_destination_code="")
```

**Parâmetros**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `number_a` | str, int | - | Primeiro número telefônico, tipicamente o número originador/chamador |
| `number_b` | str, int | - | Segundo número telefônico, tipicamente o número destino/chamado |
| `national_destination_code` | str | "" | Código de área (2 dígitos) para adicionar a números locais de 8-9 dígitos |

**Retorna**

`tuple` : Tupla com quatro elementos:
```python
(
    str,   # Número A normalizado (ou original se inválido)
    bool,  # True se número A normalizado com sucesso
    str,   # Número B normalizado (ou original se inválido)
    bool   # True se número B normalizado com sucesso
)
```

**Lógica de Processamento**

A função executa as seguintes etapas:

1. Normaliza `number_a` primeiro
2. Se `number_a` é válido e tem 10-11 dígitos, extrai código de área (primeiros 2 dígitos)
3. Usa o código de área extraído como contexto para normalizar `number_b`
4. Retorna resultados de normalização para ambos os números

**Exemplos**

```python
from teletools.preprocessing import normalize_number_pair

# Número A fornece contexto para número B local
num_a, valid_a, num_b, valid_b = normalize_number_pair(
    "11999999999",  # Número completo com área
    "88888888"      # Número local sem área
)
print(num_a, valid_a, num_b, valid_b)
# ('11999999999', True, '1188888888', True)

# Número A inválido, B normalizado independentemente
num_a, valid_a, num_b, valid_b = normalize_number_pair(
    "invalid",
    "11999999999"
)
print(num_a, valid_a, num_b, valid_b)
# ('invalid', False, '11999999999', True)

# Número A fixo fornece área para número B fixo local
num_a, valid_a, num_b, valid_b = normalize_number_pair(
    "1133334444",   # Fixo SP
    "22225555"      # Local SP
)
print(num_a, valid_a, num_b, valid_b)
# ('1133334444', True, '1122225555', True)

# Ambos os números completos
num_a, valid_a, num_b, valid_b = normalize_number_pair(
    "11999999999",
    "21988888888"
)
print(num_a, valid_a, num_b, valid_b)
# ('11999999999', True, '21988888888', True)
```

**Casos de Uso Típicos**

| Cenário | number_a | number_b | Resultado |
|---------|----------|----------|-----------|
| **CDR móvel** | 11999999999 (chamador) | 88888888 (local) | B ganha área 11 |
| **CDR fixo** | 1133334444 (origem) | 55556666 (local) | B ganha área 11 |
| **Ambos completos** | 11999999999 | 21988888888 | Ambos normalizados independentemente |
| **A inválido** | invalid | 11999999999 | B normalizado, A retorna original |
| **Interurbano** | 11999999999 (SP) | 21988888888 (RJ) | Ambos mantêm suas áreas |

**Notas**

- Especialmente útil para processar CDRs (Call Detail Records)
- O número originador frequentemente fornece contexto geográfico
- Se `number_a` for inválido ou incompleto, `number_b` é processado com o `national_destination_code` fornecido
- Números locais (8-9 dígitos) recebem o código de área automaticamente
- Números completos (10-11 dígitos) são validados mas mantêm sua área original

---

## Exemplos Práticos

### Processamento de CDR

```python
import pandas as pd
from teletools.preprocessing import normalize_number_pair

# Carregar CDR
df = pd.read_csv('cdr_mensal.csv')

# Normalizar pares de números (origem → destino)
resultado = df.apply(
    lambda row: normalize_number_pair(
        row['numero_origem'],
        row['numero_destino']
    ),
    axis=1
)

# Expandir tupla em colunas
df[['origem_norm', 'origem_valid', 'destino_norm', 'destino_valid']] = pd.DataFrame(
    resultado.tolist(), 
    index=df.index
)

# Filtrar apenas registros com ambos válidos
df_validos = df[
    (df['origem_valid'] == True) & 
    (df['destino_valid'] == True)
]
```

### Análise de Chamadas Locais vs Interurbanas

```python
from teletools.preprocessing import normalize_number_pair

def classificar_chamada(numero_origem, numero_destino):
    """Classifica chamada como local, interurbana ou inválida"""
    origem, valid_o, destino, valid_d = normalize_number_pair(
        numero_origem, 
        numero_destino
    )
    
    if not (valid_o and valid_d):
        return 'INVALIDO'
    
    # Extrair códigos de área
    if len(origem) >= 10 and len(destino) >= 10:
        area_origem = origem[:2]
        area_destino = destino[:2]
        
        if area_origem == area_destino:
            return 'LOCAL'
        else:
            return 'INTERURBANA'
    
    return 'INDEFINIDO'

# Exemplo de uso
chamadas = [
    ("11999999999", "1188888888"),   # Local SP
    ("11999999999", "21988888888"),  # SP → RJ (Interurbana)
    ("1133334444", "55556666"),      # Local SP (fixo)
]

for origem, destino in chamadas:
    tipo = classificar_chamada(origem, destino)
    print(f"{origem} → {destino}: {tipo}")
```

### Processamento em Lote com Contexto de Área

```python
from teletools.preprocessing import normalize_number_pair
import pandas as pd

def processar_cdr_lote(df_cdr):
    """
    Processa CDR em lote normalizando pares de números.
    Assume colunas: 'numero_a' (origem) e 'numero_b' (destino)
    """
    resultados = []
    
    for idx, row in df_cdr.iterrows():
        num_a, valid_a, num_b, valid_b = normalize_number_pair(
            row['numero_a'],
            row['numero_b']
        )
        
        resultados.append({
            'index': idx,
            'numero_a_original': row['numero_a'],
            'numero_a_normalizado': num_a,
            'numero_a_valido': valid_a,
            'numero_b_original': row['numero_b'],
            'numero_b_normalizado': num_b,
            'numero_b_valido': valid_b,
            'ambos_validos': valid_a and valid_b
        })
    
    return pd.DataFrame(resultados)

# Exemplo de uso
df_cdr = pd.DataFrame({
    'numero_a': ['11999999999', '1133334444', 'invalid'],
    'numero_b': ['88888888', '22225555', '11999999999']
})

df_processado = processar_cdr_lote(df_cdr)
print(df_processado[['numero_a_normalizado', 'numero_b_normalizado', 'ambos_validos']])
```

### Validação de Pares de Números

```python
from teletools.preprocessing import normalize_number_pair

def validar_par_telefones(tel_origem, tel_destino):
    """
    Valida e normaliza par de telefones.
    Retorna dicionário com status detalhado.
    """
    origem, valid_o, destino, valid_d = normalize_number_pair(
        tel_origem,
        tel_destino
    )
    
    return {
        'origem': {
            'original': tel_origem,
            'normalizado': origem,
            'valido': valid_o
        },
        'destino': {
            'original': tel_destino,
            'normalizado': destino,
            'valido': valid_d
        },
        'par_valido': valid_o and valid_d
    }

# Exemplo
resultado = validar_par_telefones(
    "(11) 99999-9999",
    "8888-8888"
)

print(f"Origem: {resultado['origem']['normalizado']}")
print(f"Destino: {resultado['destino']['normalizado']}")
print(f"Par válido: {resultado['par_valido']}")
```

### Enriquecimento de Dados CDR

```python
from teletools.preprocessing import normalize_number_pair
import pandas as pd

def enriquecer_cdr(df_cdr):
    """
    Enriquece CDR com informações de normalização e classificação.
    """
    # Normalizar pares
    resultado = df_cdr.apply(
        lambda row: normalize_number_pair(
            row['calling_number'],
            row['called_number']
        ),
        axis=1
    )
    
    # Expandir resultado
    df_cdr[['calling_norm', 'calling_valid', 'called_norm', 'called_valid']] = \
        pd.DataFrame(resultado.tolist(), index=df_cdr.index)
    
    # Classificar tipo de chamada
    def get_tipo_chamada(row):
        if not (row['calling_valid'] and row['called_valid']):
            return 'INVALIDO'
        
        calling = row['calling_norm']
        called = row['called_norm']
        
        if len(calling) >= 10 and len(called) >= 10:
            if calling[:2] == called[:2]:
                return 'LOCAL'
            else:
                return 'DDD'
        return 'OUTROS'
    
    df_cdr['tipo_chamada'] = df_cdr.apply(get_tipo_chamada, axis=1)
    
    return df_cdr

# Exemplo
df = pd.DataFrame({
    'calling_number': ['11999999999', '1133334444'],
    'called_number': ['1188888888', '21944445555']
})

df_enriquecido = enriquecer_cdr(df)
print(df_enriquecido[['calling_norm', 'called_norm', 'tipo_chamada']])
```

---

## Ver Também

- **[normalize_number](normalize_number.md)** - Normaliza número telefônico único
- **[Teletools Preprocessing API](../preprocessing_api_index.md)** - Índice de APIs de pré-processamento
- **[Teletools Database API](../database_api_index.md)** - APIs para consulta de dados de telecomunicações