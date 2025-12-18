> **[← Voltar para Teletools Utils API](../utils_api_index.md)**

# `inspect_file`

Inspeciona as primeiras linhas de um arquivo de forma rápida e flexível.

```python
inspect_file(file, nrows=5, encoding="utf8")
```

**Parâmetros**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `file` | str, Path | - | Caminho para o arquivo a ser inspecionado |
| `nrows` | int | 5 | Número de linhas a exibir |
| `encoding` | str | "utf8" | Codificação do texto (utf8, latin1, cp1252, etc.) |

**Retorna**

`None` : Imprime conteúdo diretamente no console

**Formatos Suportados**

| Formato | Extensão | Comportamento |
|---------|----------|---------------|
| **Texto** | .txt, .csv, .log | Lê arquivo texto diretamente |
| **Gzip** | .gz | Descomprime e lê conteúdo |
| **Zip** | .zip | Lê primeiro arquivo do archive |

**Exceções**

- `FileNotFoundError` - Arquivo não encontrado
- `Exception` - Erros de leitura (encoding inválido, arquivo corrompido)

**Exemplos**

```python
from teletools.utils import inspect_file

# Inspecionar arquivo CSV
inspect_file('dados.csv')
# ======== FILE: dados.csv ========
# id,nome,telefone
# 1,João,11999999999
# 2,Maria,21988888888
# 3,Pedro,85977777777
# 4,Ana,11966666666

# Inspecionar arquivo comprimido
inspect_file('cdr_janeiro.csv.gz', nrows=10)
# ======== FILE: cdr_janeiro.csv.gz ========
# timestamp,origem,destino,duracao
# 2025-01-01 00:00:15,11999999999,1133334444,120
# 2025-01-01 00:02:30,21988888888,11977777777,45
# ...

# Inspecionar arquivo ZIP
inspect_file('relatorios_2025.zip', nrows=3)
# ======== FILE: relatorios_2025.zip ========
# Reading first file in ZIP: janeiro_2025.csv
# data,registros,total
# 2025-01-01,1523,45620.50
# 2025-01-02,1647,49235.75

# Arquivo com encoding específico
inspect_file('dados_legacy.csv', encoding='latin1')
```

**Notas**

- Não carrega arquivo completo na memória - eficiente para arquivos grandes
- Para arquivos ZIP, sempre inspeciona o primeiro arquivo do archive
- Exibe mensagem de erro amigável se arquivo não existir
- Suporta qualquer encoding Python válido

---

## Exemplos Práticos

### Validação Rápida de Formato CDR

```python
from teletools.utils import inspect_file
import os

def validar_formato_cdr(diretorio):
    """
    Valida formato de arquivos CDR em um diretório.
    """
    arquivos_cdr = [
        f for f in os.listdir(diretorio) 
        if f.endswith(('.csv', '.csv.gz'))
    ]
    
    print(f"Encontrados {len(arquivos_cdr)} arquivos CDR\n")
    
    for arquivo in arquivos_cdr:
        caminho = os.path.join(diretorio, arquivo)
        inspect_file(caminho, nrows=2)
        print()  # Linha em branco entre arquivos

# Uso
validar_formato_cdr('/dados/cdr/janeiro_2025/')
```

### Diagnóstico de Encoding

```python
from teletools.utils import inspect_file

def detectar_encoding(arquivo):
    """
    Tenta diferentes encodings para encontrar o correto.
    """
    encodings = ['utf8', 'latin1', 'cp1252', 'iso-8859-1']
    
    print(f"Testando encodings para: {arquivo}\n")
    
    for enc in encodings:
        print(f"Tentando {enc}:")
        try:
            inspect_file(arquivo, nrows=3, encoding=enc)
            print(f"✓ Sucesso com {enc}\n")
            break
        except UnicodeDecodeError:
            print(f"✗ Falhou com {enc}\n")
            continue

# Uso
detectar_encoding('dados_problematicos.csv')
```

### Inspeção de Múltiplos Arquivos

```python
from teletools.utils import inspect_file
from pathlib import Path

def inspecionar_lote(diretorio, extensao='*.csv', linhas=3):
    """
    Inspeciona todos os arquivos de um tipo em um diretório.
    """
    caminho = Path(diretorio)
    arquivos = list(caminho.glob(extensao))
    
    print(f"Inspecionando {len(arquivos)} arquivos {extensao}\n")
    print("=" * 60)
    
    for arquivo in sorted(arquivos):
        inspect_file(arquivo, nrows=linhas)
        print("-" * 60)

# Uso - Inspecionar todos CSV
inspecionar_lote('/dados/cdr/', '*.csv', linhas=5)

# Uso - Inspecionar arquivos comprimidos
inspecionar_lote('/dados/backup/', '*.csv.gz', linhas=3)
```

### Validação de Headers CSV

```python
from teletools.utils import inspect_file
import io
import sys
from contextlib import redirect_stdout

def extrair_header(arquivo):
    """
    Extrai o cabeçalho de um arquivo CSV.
    Retorna lista de colunas.
    """
    # Capturar saída do inspect_file
    f = io.StringIO()
    with redirect_stdout(f):
        inspect_file(arquivo, nrows=1)
    
    output = f.getvalue()
    
    # Extrair primeira linha (após o separador)
    linhas = output.strip().split('\n')
    if len(linhas) >= 2:
        header = linhas[1]  # Pula linha "======== FILE..."
        return header.split(',')
    
    return []

def validar_headers_cdr(arquivo):
    """
    Valida se arquivo CDR tem headers esperados.
    """
    headers_esperados = {'timestamp', 'origem', 'destino', 'duracao'}
    
    headers = extrair_header(arquivo)
    headers_set = set(h.strip() for h in headers)
    
    if headers_esperados.issubset(headers_set):
        print(f"✓ {arquivo}: Headers válidos")
        return True
    else:
        faltando = headers_esperados - headers_set
        print(f"✗ {arquivo}: Faltam headers: {faltando}")
        return False

# Uso
validar_headers_cdr('cdr_janeiro.csv.gz')
```

### Pipeline de Inspeção Pré-Processamento

```python
from teletools.utils import inspect_file
from pathlib import Path
import json

def criar_relatorio_arquivos(diretorio, output='relatorio.json'):
    """
    Cria relatório com informações de todos os arquivos.
    """
    caminho = Path(diretorio)
    relatorio = {
        'diretorio': str(diretorio),
        'arquivos': []
    }
    
    for arquivo in sorted(caminho.glob('**/*')):
        if arquivo.is_file():
            info = {
                'nome': arquivo.name,
                'caminho': str(arquivo.relative_to(caminho)),
                'tamanho': arquivo.stat().st_size,
                'extensao': arquivo.suffix
            }
            
            # Adicionar preview se for texto/CSV
            if arquivo.suffix in ['.csv', '.txt', '.log']:
                print(f"Inspecionando: {arquivo.name}")
                inspect_file(arquivo, nrows=2)
                info['formato'] = 'texto'
            elif arquivo.suffix == '.gz':
                print(f"Inspecionando: {arquivo.name}")
                inspect_file(arquivo, nrows=2)
                info['formato'] = 'gzip'
            
            relatorio['arquivos'].append(info)
    
    # Salvar relatório
    with open(output, 'w', encoding='utf8') as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    
    print(f"\nRelatório salvo em: {output}")
    return relatorio

# Uso
relatorio = criar_relatorio_arquivos('/dados/cdr/janeiro_2025/')
print(f"Total de arquivos: {len(relatorio['arquivos'])}")
```

### Comparação de Estruturas de Arquivo

```python
from teletools.utils import inspect_file

def comparar_estruturas(arquivo1, arquivo2):
    """
    Compara estrutura (headers) de dois arquivos CSV.
    """
    print("ARQUIVO 1:")
    inspect_file(arquivo1, nrows=1)
    
    print("\nARQUIVO 2:")
    inspect_file(arquivo2, nrows=1)
    
    print("\n" + "="*60)
    print("COMPARAÇÃO:")
    print("Verifique se os headers são compatíveis")

# Uso
comparar_estruturas(
    'cdr_janeiro_2025.csv.gz',
    'cdr_fevereiro_2025.csv.gz'
)
```

---

## Ver Também

- **[setup_logger](setup_logger.md)** - Configuração de logging para processamento
- **[Teletools Utils API](../utils_api_index.md)** - Índice de utilitários
- **[Teletools Database API](../database_api_index.md)** - APIs para consulta de dados