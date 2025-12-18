> **[← Voltar para Teletools Cipher API](../cipher_api_index.md)**

# `decrypt_file_or_folder`

Descriptografa arquivo .gpg ou todos os arquivos .gpg de uma pasta usando chave privada GPG.

```python
decrypt_file_or_folder(private_key_file, input_file_or_folder, output_folder=None)
```

**Parâmetros**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `private_key_file` | str, Path | - | Caminho para o arquivo de chave privada GPG |
| `input_file_or_folder` | str, Path | - | Caminho para arquivo .gpg ou pasta com arquivos .gpg |
| `output_folder` | str, Path, None | None | Pasta de saída (se None, usa pasta pai do input) |

**Retorna**

`None` : Cria arquivos descriptografados na pasta de saída

**Comportamento**

| Tipo de Input | Comportamento |
|---------------|---------------|
| **Arquivo .gpg** | Descriptografa o arquivo e remove extensão .gpg |
| **Pasta** | Descriptografa todos os arquivos .gpg da pasta (não recursivo) |
| **output_folder=None** | Arquivo: usa pasta pai; Pasta: usa a própria pasta |

**Exceções**

- `FileNotFoundError` - Chave privada ou arquivo/pasta de entrada não encontrado
- `ValueError` - Arquivo de chave privada inválido ou sem chaves
- `OSError` - Erro ao criar pasta de saída ou ler input

**Exemplos**

```python
from teletools.cipher import decrypt_file_or_folder

# Descriptografar arquivo único
decrypt_file_or_folder(
    'private.key',
    'documento_confidencial.pdf.gpg',
    'decrypted/'
)
# Cria: decrypted/documento_confidencial.pdf

# Descriptografar pasta inteira
decrypt_file_or_folder(
    'private.key',
    'dados_criptografados/',
    'dados_originais/'
)
# Cria: dados_originais/arquivo1.txt
#       dados_originais/arquivo2.csv
#       dados_originais/arquivo3.json

# Descriptografar in-place (mesma pasta)
decrypt_file_or_folder(
    'private.key',
    'relatorio.xlsx.gpg'
)
# Cria: relatorio.xlsx (na mesma pasta do arquivo criptografado)

# Usando Path do pathlib
from pathlib import Path
decrypt_file_or_folder(
    Path.home() / '.ssh' / 'private.key',
    Path('backup') / 'encrypted' / 'confidencial.txt.gpg',
    Path('dados') / 'decrypted'
)
```

**Notas**

- Arquivos .gpg **não são removidos** após descriptografia
- Extensão `.gpg` é removida do nome do arquivo original
- Chave privada deve estar em formato GPG válido
- Não requer senha (`passphrase=None`) - chave privada sem senha
- Processa apenas arquivos .gpg no primeiro nível (não recursivo para pastas)
- Arquivos sem extensão .gpg são ignorados ao descriptografar pastas

---

## Exemplos Práticos

### Restauração de Backup Criptografado

```python
from teletools.cipher import decrypt_file_or_folder
from pathlib import Path
import shutil
from datetime import datetime

def restaurar_backup(pasta_backup_encrypted, pasta_destino, chave_privada):
    """
    Restaura backup criptografado para pasta de destino.
    """
    # Criar pasta temporária para descriptografia
    temp_decrypt = Path('temp_decrypt')
    temp_decrypt.mkdir(exist_ok=True)
    
    try:
        # Descriptografar arquivos
        print("Descriptografando backup...")
        decrypt_file_or_folder(
            chave_privada,
            pasta_backup_encrypted,
            temp_decrypt
        )
        
        # Mover para destino final
        print(f"Restaurando arquivos em {pasta_destino}...")
        pasta_destino = Path(pasta_destino)
        pasta_destino.mkdir(exist_ok=True)
        
        for arquivo in temp_decrypt.glob('*'):
            if arquivo.is_file():
                destino_arquivo = pasta_destino / arquivo.name
                shutil.move(str(arquivo), str(destino_arquivo))
                print(f"✓ Restaurado: {arquivo.name}")
        
        print(f"\nBackup restaurado em: {pasta_destino}")
        
    finally:
        # Limpar pasta temporária
        if temp_decrypt.exists():
            shutil.rmtree(temp_decrypt)

# Uso
restaurar_backup(
    'backup_encrypted/',
    'dados_importantes_restaurados/',
    'keys/private.key'
)
```

### Pipeline de Auditoria com Descriptografia

```python
from teletools.cipher import decrypt_file_or_folder
from teletools.utils import setup_logger, inspect_file
from pathlib import Path
import pandas as pd

def auditar_cdr_criptografado(arquivo_gpg, chave_privada):
    """
    Descriptografa CDR, realiza auditoria e gera relatório.
    """
    logger = setup_logger('auditoria.log')
    logger.info("Iniciando auditoria de CDR criptografado")
    
    # Criar pasta temporária
    temp_folder = Path('temp_audit')
    temp_folder.mkdir(exist_ok=True)
    
    try:
        # Descriptografar
        logger.info(f"Descriptografando: {arquivo_gpg}")
        decrypt_file_or_folder(
            chave_privada,
            arquivo_gpg,
            temp_folder
        )
        
        # Encontrar arquivo descriptografado
        arquivo_csv = list(temp_folder.glob('*.csv'))[0]
        logger.info(f"Arquivo descriptografado: {arquivo_csv}")
        
        # Inspecionar
        logger.info("Preview do arquivo:")
        inspect_file(arquivo_csv, nrows=5)
        
        # Carregar e analisar
        logger.info("Carregando dados para análise...")
        df = pd.read_csv(arquivo_csv)
        
        # Estatísticas
        logger.info("="*60)
        logger.info("ESTATÍSTICAS DO CDR")
        logger.info(f"Total de registros: {len(df)}")
        logger.info(f"Colunas: {', '.join(df.columns)}")
        logger.info(f"Período: {df['timestamp'].min()} até {df['timestamp'].max()}")
        logger.info("="*60)
        
        return df
        
    finally:
        # Limpar arquivo descriptografado
        if temp_folder.exists():
            shutil.rmtree(temp_folder)
            logger.info("Arquivos temporários removidos")

# Uso
df_auditado = auditar_cdr_criptografado(
    'dados_seguros/cdr_janeiro_2025.csv.gpg',
    'keys/auditor_private.key'
)
```

### Descriptografia em Lote com Validação de Hash

```python
from teletools.cipher import decrypt_file_or_folder
from pathlib import Path
import hashlib

def calcular_hash(arquivo):
    """Calcula hash SHA256 de um arquivo."""
    sha256 = hashlib.sha256()
    with open(arquivo, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def descriptografar_com_validacao(pasta_encrypted, pasta_destino, chave_privada, arquivo_hashes):
    """
    Descriptografa arquivos e valida integridade usando hashes.
    """
    pasta_encrypted = Path(pasta_encrypted)
    pasta_destino = Path(pasta_destino)
    pasta_destino.mkdir(exist_ok=True)
    
    # Carregar hashes originais
    hashes_originais = {}
    with open(arquivo_hashes, 'r') as f:
        for linha in f:
            nome, hash_val = linha.strip().split('\t')
            hashes_originais[nome] = hash_val
    
    print(f"Carregados {len(hashes_originais)} hashes para validação")
    
    # Descriptografar
    print("Descriptografando arquivos...")
    decrypt_file_or_folder(
        chave_privada,
        pasta_encrypted,
        pasta_destino
    )
    
    # Validar hashes
    print("\nValidando integridade...")
    validados = 0
    invalidos = 0
    
    for nome_arquivo, hash_esperado in hashes_originais.items():
        arquivo_destino = pasta_destino / nome_arquivo
        
        if arquivo_destino.exists():
            hash_atual = calcular_hash(arquivo_destino)
            
            if hash_atual == hash_esperado:
                print(f"✓ {nome_arquivo}: Hash válido")
                validados += 1
            else:
                print(f"✗ {nome_arquivo}: Hash inválido!")
                invalidos += 1
        else:
            print(f"⚠ {nome_arquivo}: Arquivo não encontrado")
    
    print(f"\nValidação concluída:")
    print(f"Válidos: {validados}")
    print(f"Inválidos: {invalidos}")
    
    return validados, invalidos

# Uso
validados, invalidos = descriptografar_com_validacao(
    'relatorios_encrypted/',
    'relatorios_restaurados/',
    'keys/private.key',
    'relatorios_encrypted/hashes.txt'
)
```

### Processamento Seguro de Dados Sensíveis

```python
from teletools.cipher import decrypt_file_or_folder, encrypt_file_or_folder
from teletools.preprocessing import normalize_number_pair
from pathlib import Path
import pandas as pd
import shutil

def processar_cdr_seguro(arquivo_gpg, chave_privada, chave_publica):
    """
    Descriptografa, processa e re-criptografa CDR de forma segura.
    """
    temp_folder = Path('temp_processing')
    temp_folder.mkdir(exist_ok=True)
    
    try:
        # 1. Descriptografar
        print("Descriptografando arquivo...")
        decrypt_file_or_folder(
            chave_privada,
            arquivo_gpg,
            temp_folder
        )
        
        # Encontrar arquivo CSV
        arquivo_csv = list(temp_folder.glob('*.csv'))[0]
        
        # 2. Processar dados
        print("Processando dados...")
        df = pd.read_csv(arquivo_csv)
        
        # Normalizar números
        resultado = df.apply(
            lambda row: normalize_number_pair(
                row['numero_origem'],
                row['numero_destino']
            ),
            axis=1
        )
        
        df[['origem_norm', 'origem_valid', 'destino_norm', 'destino_valid']] = \
            pd.DataFrame(resultado.tolist(), index=df.index)
        
        # Salvar processado
        arquivo_processado = temp_folder / 'cdr_processado.csv'
        df.to_csv(arquivo_processado, index=False)
        
        # 3. Re-criptografar
        print("Re-criptografando resultado...")
        encrypt_file_or_folder(
            chave_publica,
            arquivo_processado,
            'dados_processados/'
        )
        
        print("Processamento seguro concluído!")
        print("Resultado: dados_processados/cdr_processado.csv.gpg")
        
    finally:
        # Limpar arquivos temporários
        if temp_folder.exists():
            shutil.rmtree(temp_folder)
            print("Arquivos temporários removidos (segurança)")

# Uso
processar_cdr_seguro(
    'dados_seguros/cdr_janeiro.csv.gpg',
    'keys/private.key',
    'keys/public.key'
)
```

### Sistema de Recuperação de Desastres

```python
from teletools.cipher import decrypt_file_or_folder
from teletools.utils import setup_logger
from pathlib import Path
from datetime import datetime
import tarfile
import shutil

def recuperacao_completa(backup_encrypted_dir, chave_privada, destino_final):
    """
    Sistema completo de recuperação de desastres.
    """
    logger = setup_logger('recuperacao_desastres.log')
    
    logger.info("="*60)
    logger.info("INICIANDO RECUPERAÇÃO DE DESASTRES")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info(f"Backup: {backup_encrypted_dir}")
    logger.info("="*60)
    
    temp_folder = Path('temp_recovery')
    temp_folder.mkdir(exist_ok=True)
    
    try:
        # Fase 1: Descriptografar
        logger.info("FASE 1: Descriptografando backup...")
        decrypt_file_or_folder(
            chave_privada,
            backup_encrypted_dir,
            temp_folder
        )
        
        arquivos_recuperados = list(temp_folder.glob('*'))
        logger.info(f"Arquivos descriptografados: {len(arquivos_recuperados)}")
        
        # Fase 2: Validar integridade
        logger.info("FASE 2: Validando integridade...")
        for arquivo in arquivos_recuperados:
            tamanho = arquivo.stat().st_size
            logger.info(f"✓ {arquivo.name}: {tamanho} bytes")
        
        # Fase 3: Restaurar para destino
        logger.info("FASE 3: Restaurando para destino final...")
        destino = Path(destino_final)
        destino.mkdir(exist_ok=True)
        
        for arquivo in arquivos_recuperados:
            destino_arquivo = destino / arquivo.name
            shutil.copy2(arquivo, destino_arquivo)
            logger.info(f"✓ Restaurado: {arquivo.name}")
        
        # Fase 4: Criar arquivo tar de backup adicional
        logger.info("FASE 4: Criando arquivo tar de segurança...")
        tar_backup = f"backup_recovery_{datetime.now():%Y%m%d_%H%M%S}.tar.gz"
        with tarfile.open(tar_backup, "w:gz") as tar:
            tar.add(destino, arcname=destino.name)
        
        logger.info(f"Backup tar criado: {tar_backup}")
        
        # Relatório final
        logger.info("="*60)
        logger.info("RECUPERAÇÃO CONCLUÍDA COM SUCESSO")
        logger.info(f"Arquivos restaurados: {len(arquivos_recuperados)}")
        logger.info(f"Destino: {destino}")
        logger.info(f"Backup adicional: {tar_backup}")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"ERRO CRÍTICO na recuperação: {e}")
        return False
        
    finally:
        # Limpar temporários
        if temp_folder.exists():
            shutil.rmtree(temp_folder)
            logger.info("Arquivos temporários removidos")

# Uso
sucesso = recuperacao_completa(
    'backup_encrypted/',
    'keys/recovery_private.key',
    'sistema_restaurado/'
)

if sucesso:
    print("Sistema recuperado com sucesso!")
else:
    print("FALHA na recuperação - verificar logs")
```

### Descriptografia com Controle de Acesso

```python
from teletools.cipher import decrypt_file_or_folder
from pathlib import Path
from datetime import datetime
import json

def descriptografar_auditado(arquivo_gpg, chave_privada, usuario, justificativa):
    """
    Descriptografa com registro de auditoria (quem, quando, por quê).
    """
    # Criar pasta de saída
    output_folder = Path('decrypted_audit')
    output_folder.mkdir(exist_ok=True)
    
    # Registro de auditoria
    audit_log = output_folder / 'access_log.json'
    
    # Carregar log existente
    if audit_log.exists():
        with open(audit_log, 'r') as f:
            acessos = json.load(f)
    else:
        acessos = []
    
    # Descriptografar
    print(f"Descriptografando {arquivo_gpg}...")
    decrypt_file_or_folder(
        chave_privada,
        arquivo_gpg,
        output_folder
    )
    
    # Registrar acesso
    registro = {
        'timestamp': datetime.now().isoformat(),
        'usuario': usuario,
        'arquivo': str(arquivo_gpg),
        'justificativa': justificativa
    }
    acessos.append(registro)
    
    # Salvar log
    with open(audit_log, 'w') as f:
        json.dump(acessos, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Acesso registrado no log de auditoria")
    print(f"Arquivo descriptografado em: {output_folder}")
    
    return output_folder

# Uso
output = descriptografar_auditado(
    'confidencial.pdf.gpg',
    'keys/auditor_private.key',
    usuario='maria.silva',
    justificativa='Auditoria trimestral 2025-Q1'
)
```

---

## Ver Também

- **[encrypt_file_or_folder](encrypt_file_or_folder.md)** - Criptografar arquivos e pastas
- **[Teletools Cipher API](../cipher_api_index.md)** - Índice de APIs de criptografia
- **[Teletools Cipher CLI](../cipher_cli.md)** - Interface de linha de comando