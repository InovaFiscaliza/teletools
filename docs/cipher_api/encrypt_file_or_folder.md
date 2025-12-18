> **[← Voltar para Teletools Cipher API](../cipher_api_index.md)**

# `encrypt_file_or_folder`

Criptografa arquivo ou todos os arquivos de uma pasta usando chave pública GPG.

```python
encrypt_file_or_folder(public_key_file, input_file_or_folder, output_folder=None)
```

**Parâmetros**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `public_key_file` | str, Path | - | Caminho para o arquivo de chave pública GPG |
| `input_file_or_folder` | str, Path | - | Caminho para arquivo ou pasta a ser criptografado |
| `output_folder` | str, Path, None | None | Pasta de saída (se None, usa pasta pai do input) |

**Retorna**

`None` : Cria arquivos .gpg criptografados na pasta de saída

**Comportamento**

| Tipo de Input | Comportamento |
|---------------|---------------|
| **Arquivo único** | Criptografa o arquivo e salva como `nome_arquivo.ext.gpg` |
| **Pasta** | Criptografa todos os arquivos da pasta (não recursivo) |
| **output_folder=None** | Arquivo: usa pasta pai; Pasta: usa a própria pasta |

**Exceções**

- `FileNotFoundError` - Chave pública ou arquivo/pasta de entrada não encontrado
- `ValueError` - Arquivo de chave pública inválido ou sem chaves
- `OSError` - Erro ao criar pasta de saída

**Exemplos**

```python
from teletools.cipher import encrypt_file_or_folder

# Criptografar arquivo único
encrypt_file_or_folder(
    'public.key',
    'documento_confidencial.pdf',
    'encrypted/'
)
# Cria: encrypted/documento_confidencial.pdf.gpg

# Criptografar pasta inteira
encrypt_file_or_folder(
    'public.key',
    'dados_sensiveis/',
    'dados_criptografados/'
)
# Cria: dados_criptografados/arquivo1.txt.gpg
#       dados_criptografados/arquivo2.csv.gpg
#       dados_criptografados/arquivo3.json.gpg

# Criptografar in-place (mesma pasta)
encrypt_file_or_folder(
    'public.key',
    'relatorio.xlsx'
)
# Cria: relatorio.xlsx.gpg (na mesma pasta do arquivo original)

# Usando Path do pathlib
from pathlib import Path
encrypt_file_or_folder(
    Path.home() / '.ssh' / 'public.key',
    Path('dados') / 'confidencial.txt',
    Path('backup') / 'encrypted'
)
```

**Notas**

- Arquivos originais **não são removidos** após criptografia
- Extensão `.gpg` é adicionada ao nome do arquivo original
- Chave pública deve estar em formato GPG válido
- Usa `always_trust=True` para evitar prompts interativos
- Processa apenas arquivos no primeiro nível (não recursivo para pastas)

---

## Exemplos Práticos

### Pipeline de Backup Criptografado

```python
from teletools.cipher import encrypt_file_or_folder
from pathlib import Path
import shutil
from datetime import datetime

def backup_criptografado(pasta_origem, pasta_backup, chave_publica):
    """
    Cria backup criptografado de uma pasta.
    """
    # Criar pasta temporária para backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_backup = Path(f'temp_backup_{timestamp}')
    temp_backup.mkdir()
    
    try:
        # Copiar arquivos
        print(f"Copiando arquivos de {pasta_origem}...")
        for arquivo in Path(pasta_origem).glob('*'):
            if arquivo.is_file():
                shutil.copy2(arquivo, temp_backup)
        
        # Criptografar backup
        print("Criptografando arquivos...")
        encrypt_file_or_folder(
            chave_publica,
            temp_backup,
            pasta_backup
        )
        
        print(f"Backup criptografado salvo em: {pasta_backup}")
        
    finally:
        # Limpar pasta temporária
        shutil.rmtree(temp_backup)

# Uso
backup_criptografado(
    'dados_importantes/',
    'backup_encrypted/',
    'keys/public.key'
)
```

### Criptografia de Arquivos CSV Sensíveis

```python
from teletools.cipher import encrypt_file_or_folder
from pathlib import Path
import pandas as pd

def processar_e_criptografar_cdr(arquivo_cdr, chave_publica):
    """
    Processa CDR, remove dados sensíveis do original,
    e criptografa versão completa.
    """
    # Ler dados
    df_completo = pd.read_csv(arquivo_cdr)
    
    # Salvar versão completa temporária
    arquivo_completo = 'cdr_completo_temp.csv'
    df_completo.to_csv(arquivo_completo, index=False)
    
    # Criptografar versão completa
    print("Criptografando dados completos...")
    encrypt_file_or_folder(
        chave_publica,
        arquivo_completo,
        'dados_seguros/'
    )
    
    # Criar versão anonimizada
    df_anonimizado = df_completo.copy()
    df_anonimizado['numero_origem'] = 'XXXXX' + df_anonimizado['numero_origem'].astype(str).str[-4:]
    df_anonimizado['numero_destino'] = 'XXXXX' + df_anonimizado['numero_destino'].astype(str).str[-4:]
    
    # Salvar versão anonimizada (não criptografada)
    df_anonimizado.to_csv('cdr_anonimizado.csv', index=False)
    
    # Remover arquivo temporário
    Path(arquivo_completo).unlink()
    
    print("Processamento concluído!")
    print("- Versão completa criptografada: dados_seguros/cdr_completo_temp.csv.gpg")
    print("- Versão anonimizada: cdr_anonimizado.csv")

# Uso
processar_e_criptografar_cdr(
    'cdr_janeiro_2025.csv',
    'keys/anatel_public.key'
)
```

### Criptografia em Lote com Validação

```python
from teletools.cipher import encrypt_file_or_folder
from pathlib import Path
import hashlib

def calcular_hash(arquivo):
    """Calcula hash SHA256 de um arquivo."""
    sha256 = hashlib.sha256()
    with open(arquivo, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def criptografar_com_validacao(pasta_origem, pasta_destino, chave_publica):
    """
    Criptografa arquivos e salva hashes para validação.
    """
    pasta_origem = Path(pasta_origem)
    pasta_destino = Path(pasta_destino)
    pasta_destino.mkdir(exist_ok=True)
    
    # Arquivo de log com hashes
    log_hashes = pasta_destino / 'hashes.txt'
    
    arquivos = [f for f in pasta_origem.glob('*') if f.is_file()]
    
    with open(log_hashes, 'w') as log:
        for arquivo in arquivos:
            print(f"Processando: {arquivo.name}")
            
            # Calcular hash do arquivo original
            hash_original = calcular_hash(arquivo)
            
            # Criptografar
            encrypt_file_or_folder(
                chave_publica,
                arquivo,
                pasta_destino
            )
            
            # Registrar hash
            log.write(f"{arquivo.name}\t{hash_original}\n")
    
    print(f"\nCriptografia concluída!")
    print(f"Arquivos criptografados: {pasta_destino}")
    print(f"Hashes salvos em: {log_hashes}")

# Uso
criptografar_com_validacao(
    'relatorios_mensais/',
    'relatorios_encrypted/',
    'keys/auditor_public.key'
)
```

### Automatização de Arquivamento Seguro

```python
from teletools.cipher import encrypt_file_or_folder
from pathlib import Path
from datetime import datetime, timedelta
import shutil

def arquivar_arquivos_antigos(pasta_monitorada, dias_limite, chave_publica):
    """
    Encontra arquivos antigos, criptografa e move para arquivo.
    """
    pasta_monitorada = Path(pasta_monitorada)
    pasta_arquivo = pasta_monitorada / 'arquivo_criptografado'
    pasta_arquivo.mkdir(exist_ok=True)
    
    data_limite = datetime.now() - timedelta(days=dias_limite)
    
    print(f"Procurando arquivos anteriores a {data_limite.date()}")
    
    arquivos_arquivados = 0
    
    for arquivo in pasta_monitorada.glob('*.csv'):
        if arquivo.is_file():
            # Verificar data de modificação
            data_mod = datetime.fromtimestamp(arquivo.stat().st_mtime)
            
            if data_mod < data_limite:
                print(f"Arquivando: {arquivo.name} ({data_mod.date()})")
                
                # Criptografar
                encrypt_file_or_folder(
                    chave_publica,
                    arquivo,
                    pasta_arquivo
                )
                
                # Remover original após criptografia bem-sucedida
                arquivo_encrypted = pasta_arquivo / f"{arquivo.name}.gpg"
                if arquivo_encrypted.exists():
                    arquivo.unlink()
                    arquivos_arquivados += 1
                    print(f"✓ {arquivo.name} arquivado e removido")
    
    print(f"\nTotal arquivado: {arquivos_arquivados} arquivos")
    return arquivos_arquivados

# Uso - Arquivar arquivos com mais de 90 dias
arquivar_arquivos_antigos(
    'dados_cdr/',
    dias_limite=90,
    chave_publica='keys/arquivo_public.key'
)
```

### Integração com Sistema de Logs

```python
from teletools.cipher import encrypt_file_or_folder
from teletools.utils import setup_logger
from pathlib import Path
import time

def criptografar_com_log(arquivos, chave_publica, pasta_saida):
    """
    Criptografa múltiplos arquivos com logging detalhado.
    """
    logger = setup_logger('criptografia.log')
    
    logger.info("="*60)
    logger.info("Iniciando processo de criptografia")
    logger.info(f"Chave pública: {chave_publica}")
    logger.info(f"Pasta de saída: {pasta_saida}")
    logger.info(f"Total de arquivos: {len(arquivos)}")
    logger.info("="*60)
    
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(exist_ok=True)
    
    sucesso = 0
    falha = 0
    inicio = time.time()
    
    for idx, arquivo in enumerate(arquivos, 1):
        try:
            logger.info(f"[{idx}/{len(arquivos)}] Criptografando: {arquivo}")
            
            inicio_arquivo = time.time()
            encrypt_file_or_folder(
                chave_publica,
                arquivo,
                pasta_saida
            )
            duracao = time.time() - inicio_arquivo
            
            # Verificar arquivo de saída
            arquivo_saida = pasta_saida / f"{Path(arquivo).name}.gpg"
            tamanho = arquivo_saida.stat().st_size / 1024  # KB
            
            logger.info(
                f"✓ Concluído em {duracao:.2f}s - "
                f"Tamanho: {tamanho:.2f} KB"
            )
            sucesso += 1
            
        except Exception as e:
            logger.error(f"✗ Erro ao criptografar {arquivo}: {e}")
            falha += 1
    
    # Relatório final
    duracao_total = time.time() - inicio
    logger.info("")
    logger.info("="*60)
    logger.info("RELATÓRIO FINAL")
    logger.info(f"Sucesso: {sucesso}/{len(arquivos)}")
    logger.info(f"Falha: {falha}/{len(arquivos)}")
    logger.info(f"Duração total: {duracao_total:.2f} segundos")
    logger.info(f"Taxa de sucesso: {sucesso/len(arquivos)*100:.1f}%")
    logger.info("="*60)
    
    return {'sucesso': sucesso, 'falha': falha}

# Uso
arquivos_para_criptografar = [
    'relatorio1.pdf',
    'dados_confidenciais.xlsx',
    'cdr_janeiro.csv'
]

resultado = criptografar_com_log(
    arquivos_para_criptografar,
    'keys/public.key',
    'documentos_seguros/'
)
```

---

## Ver Também

- **[decrypt_file_or_folder](decrypt_file_or_folder.md)** - Descriptografar arquivos e pastas
- **[Teletools Cipher API](../cipher_api_index.md)** - Índice de APIs de criptografia
- **[Teletools Cipher CLI](../cipher_cli.md)** - Interface de linha de comando