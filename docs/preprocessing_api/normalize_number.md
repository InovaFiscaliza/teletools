> **[← Voltar para Teletools Preprocessing API](../preprocessing_api_index.md)**

# `normalize_number`

Normaliza um número telefônico brasileiro segundo os padrões ANATEL e ITU-T E.164.

```python
normalize_number(subscriber_number, national_destination_code="")
```

**Parâmetros**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `subscriber_number` | str, int | - | Número telefônico a normalizar. Pode conter letras, pontuação e prefixos diversos |
| `national_destination_code` | str | "" | Código de área (2 dígitos) para adicionar a números locais de 8-9 dígitos |

**Retorna**

`tuple` : Tupla com dois elementos:
```python
(
    str,   # Número normalizado (ou original se inválido)
    bool   # True se normalizado com sucesso, False caso contrário
)
```

**Processamento**

A função executa as seguintes etapas:

1. Trata números separados por ponto-e-vírgula (usa primeira parte)
2. Remove caracteres de preenchimento ('f')
3. Remove letras e pontuação
4. Remove prefixos de chamada (a cobrar, internacional, nacional)
5. Valida contra padrões de numeração brasileiros
6. Adiciona código de área a números locais quando fornecido

**Exemplos**

```python
from teletools.preprocessing import normalize_number

# Número móvel com formatação
resultado, valido = normalize_number("(11) 99999-9999")
print(resultado, valido)
# ('11999999999', True)

# Número 0800 com pontuação
resultado, valido = normalize_number("0800-123-4567")
print(resultado, valido)
# ('08001234567', True)

# Número local com código de área
resultado, valido = normalize_number("99999999", "11")
print(resultado, valido)
# ('1199999999', True)

# Número fixo formatado
resultado, valido = normalize_number("(11) 3333-4444")
print(resultado, valido)
# ('1133334444', True)

# Número inválido
resultado, valido = normalize_number("invalid")
print(resultado, valido)
# ('invalid', False)
```

**Formatos de entrada aceitos**

```python
# Com pontuação e parênteses
normalize_number("(11) 99999-9999")

# Apenas dígitos
normalize_number("11999999999")

# Com prefixo nacional (0)
normalize_number("011999999999")

# Com prefixo a cobrar (90)
normalize_number("9011999999999")

# Número inteiro
normalize_number(11999999999)

# Com código de país (55)
normalize_number("5511999999999")
```

**Tipos de números suportados**

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| **SMP** | Serviço Móvel Pessoal (celular) | 11999999999 (11 dígitos) |
| **STFC** | Serviço Telefônico Fixo Comutado | 1133334444 (10 dígitos) |
| **CNG** | Códigos Não Geográficos (0800, 0300) | 08001234567 (10-11 dígitos) |
| **SME** | Serviço Móvel Especializado | 1178012345 (10 dígitos) |
| **SUP** | Serviço de Utilidade Pública | 190, 192, 193 |

**Notas**

- Remove automaticamente prefixos de chamadas a cobrar (90, 9090)
- Remove prefixos internacionais (00) e nacionais (0)
- Mantém o número original se a validação falhar
- Números com ponto-e-vírgula são divididos e apenas a primeira parte é processada
- O código de área deve ter exatamente 2 dígitos
- Números locais devem ter 8 ou 9 dígitos para aceitar código de área

---

## Exemplos Práticos

### Limpeza de Números em CSV

```python
import pandas as pd
from teletools.preprocessing import normalize_number

# Carregar dados
df = pd.read_csv('telefones.csv')

# Normalizar coluna de telefones
df['telefone_limpo'] = df['telefone'].apply(
    lambda x: normalize_number(x)[0]
)
df['telefone_valido'] = df['telefone'].apply(
    lambda x: normalize_number(x)[1]
)

# Filtrar apenas números válidos
df_validos = df[df['telefone_valido'] == True]
```

### Processar Lista com Código de Área

```python
from teletools.preprocessing import normalize_number

# Lista de números locais de São Paulo
numeros_locais = ["99999-9999", "3333-4444", "2222-1111"]
codigo_area = "11"

numeros_normalizados = []
for numero in numeros_locais:
    normalizado, valido = normalize_number(numero, codigo_area)
    if valido:
        numeros_normalizados.append(normalizado)

print(numeros_normalizados)
# ['1199999999', '1133334444', '1122221111']
```

### Validação de Dados de Entrada

```python
from teletools.preprocessing import normalize_number

def validar_telefone(telefone):
    """Valida e retorna telefone normalizado ou None se inválido"""
    normalizado, valido = normalize_number(telefone)
    if valido:
        return normalizado
    else:
        print(f"Telefone inválido: {telefone}")
        return None

# Usar em processamento de formulário
telefone_usuario = input("Digite seu telefone: ")
telefone_validado = validar_telefone(telefone_usuario)

if telefone_validado:
    print(f"Telefone válido: {telefone_validado}")
```

### Processamento em Lote

```python
from teletools.preprocessing import normalize_number
import pandas as pd

def processar_lote_telefones(lista_telefones, codigo_area_padrao=""):
    """Processa lote de telefones e retorna DataFrame com resultados"""
    resultados = []
    
    for telefone in lista_telefones:
        normalizado, valido = normalize_number(telefone, codigo_area_padrao)
        resultados.append({
            'original': telefone,
            'normalizado': normalizado,
            'valido': valido
        })
    
    return pd.DataFrame(resultados)

# Exemplo de uso
telefones = [
    "(11) 99999-9999",
    "0800-123-4567",
    "invalid",
    "3333-4444"
]

df_resultado = processar_lote_telefones(telefones, "11")
print(df_resultado)
```

---

## Ver Também

- **[normalize_number_pair](normalize_number_pair.md)** - Normaliza par de números com inferência contextual
- **[Teletools Preprocessing API](../preprocessing_api_index.md)** - Índice de APIs de pré-processamento
- **[ANATEL Plano de Numeração](https://www.anatel.gov.br/)** - Padrões oficiais de numeração