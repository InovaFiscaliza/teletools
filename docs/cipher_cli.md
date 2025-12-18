# Teletools Cipher

> **[← Voltar para o README principal](../README.md)** | [Database API](database.md) | [ABR Loader](abr_loader.md) | [CDR Stage Database](cdr_stage.md)

Teletools Cipher é um cliente de linha de comando para criptografia e descriptografia de arquivos usando criptografia GPG (GNU Privacy Guard) com chaves públicas/privadas.

## Índice

- [Teletools Cipher](#teletools-cipher)
  - [Índice](#índice)
  - [Visão Geral](#visão-geral)
    - [Características Principais](#características-principais)
  - [Instalação e Configuração](#instalação-e-configuração)
    - [Pré-requisitos](#pré-requisitos)
    - [Instalação do Teletools](#instalação-do-teletools)
    - [Instalação do GnuPG](#instalação-do-gnupg)
      - [Linux (Ubuntu/Debian)](#linux-ubuntudebian)
      - [Linux (RHEL/CentOS/Fedora)](#linux-rhelcentosfedora)
      - [Windows](#windows)
      - [Verificação da Instalação](#verificação-da-instalação)
  - [Geração de Chaves](#geração-de-chaves)
    - [Gerar Par de Chaves GPG](#gerar-par-de-chaves-gpg)
    - [Exportar Chave Pública](#exportar-chave-pública)
    - [Exportar Chave Privada](#exportar-chave-privada)
  - [Comandos Disponíveis](#comandos-disponíveis)
    - [`encrypt` - Criptografia de Arquivos](#encrypt---criptografia-de-arquivos)
    - [`decrypt` - Descriptografia de Arquivos](#decrypt---descriptografia-de-arquivos)
  - [Criptografia de Arquivos](#criptografia-de-arquivos)
    - [Uso Básico](#uso-básico)
    - [Criptografar um único arquivo](#criptografar-um-único-arquivo)
    - [Criptografar todos os arquivos de um diretório](#criptografar-todos-os-arquivos-de-um-diretório)
    - [Criptografar no mesmo local do arquivo original](#criptografar-no-mesmo-local-do-arquivo-original)
    - [Processo de Criptografia](#processo-de-criptografia)
      - [Formato dos Arquivos Criptografados](#formato-dos-arquivos-criptografados)
  - [Descriptografia de Arquivos](#descriptografia-de-arquivos)
    - [Uso Básico](#uso-básico-1)
    - [Descriptografar um único arquivo](#descriptografar-um-único-arquivo)
    - [Descriptografar todos os arquivos de um diretório](#descriptografar-todos-os-arquivos-de-um-diretório)
    - [Descriptografar no mesmo local do arquivo original](#descriptografar-no-mesmo-local-do-arquivo-original)
    - [Processo de Descriptografia](#processo-de-descriptografia)
  - [Casos de Uso](#casos-de-uso)
    - [Proteção de Dados Sensíveis](#proteção-de-dados-sensíveis)
    - [Transferência Segura de Arquivos](#transferência-segura-de-arquivos)
    - [Backup Criptografado](#backup-criptografado)
  - [Segurança e Boas Práticas](#segurança-e-boas-práticas)
    - [Proteção de Chaves Privadas](#proteção-de-chaves-privadas)
    - [Distribuição de Chaves Públicas](#distribuição-de-chaves-públicas)
    - [Gestão de Chaves](#gestão-de-chaves)
  - [Limitações Conhecidas](#limitações-conhecidas)
  - [Solução de Problemas](#solução-de-problemas)
    - [Erro: "Public key file not found"](#erro-public-key-file-not-found)
    - [Erro: "Error reading public key file"](#erro-error-reading-public-key-file)
    - [Erro: "Missing required dependency"](#erro-missing-required-dependency)
  - [Contribuindo](#contribuindo)
  - [Licença](#licença)
  - [Contato e Suporte](#contato-e-suporte)

## Visão Geral

Teletools Cipher fornece uma interface de linha de comando simples e segura para criptografar e descriptografar arquivos usando o padrão GPG (GNU Privacy Guard). A ferramenta utiliza criptografia assimétrica (chave pública/privada), garantindo que apenas o destinatário com a chave privada correspondente possa descriptografar os dados.

### Características Principais

- ✅ **Criptografia Assimétrica**: Usa par de chaves GPG (pública/privada)
- ✅ **Processamento em Lote**: Criptografa/descriptografa arquivos individuais ou diretórios completos
- ✅ **Padrão Aberto**: Baseado no padrão OpenPGP amplamente utilizado
- ✅ **Interface Simples**: Comandos intuitivos para operações comuns
- ✅ **Tratamento de Erros**: Mensagens de erro claras e códigos de saída apropriados
- ✅ **Compatibilidade**: Arquivos criptografados podem ser descriptografados com qualquer ferramenta compatível com GPG

## Instalação e Configuração

### Pré-requisitos

- Python 3.13+ com gerenciador de pacotes [UV](https://docs.astral.sh/uv/)
- GnuPG (GPG) instalado no sistema
- Par de chaves GPG (pública e privada)

### Instalação do Teletools

```bash
# Clone o repositório
git clone https://github.com/InovaFiscaliza/teletools.git
cd teletools

# Instale as dependências
uv sync

# Ative o ambiente virtual
source .venv/bin/activate
```

### Instalação do GnuPG

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install gnupg
```

#### Linux (RHEL/CentOS/Fedora)

```bash
sudo dnf install gnupg2
# ou
sudo yum install gnupg2
```

#### Windows

1. Baixe o instalador do [Gpg4win](https://gpg4win.org/download.html)
2. Execute o instalador e siga as instruções
3. Adicione o GPG ao PATH do sistema (geralmente `C:\Program Files (x86)\GnuPG\bin`)

#### Verificação da Instalação

```bash
gpg --version
```

Você deve ver informações sobre a versão do GPG instalada.

## Geração de Chaves

Antes de usar o Teletools Cipher, você precisa de um par de chaves GPG. Se você ainda não tem chaves, siga estas instruções:

### Gerar Par de Chaves GPG

```bash
# Gerar novo par de chaves (interativo)
gpg --full-generate-key
```

Durante o processo interativo, você será solicitado a:
1. Escolher o tipo de chave (recomendado: RSA and RSA)
2. Definir o tamanho da chave (recomendado: 4096 bits)
3. Definir a validade da chave (0 = não expira)
4. Fornecer seu nome e email
5. Definir uma senha (passphrase) para proteger a chave privada

### Exportar Chave Pública

```bash
# Listar chaves disponíveis
gpg --list-keys

# Exportar chave pública para arquivo
gpg --armor --export seu_email@exemplo.com > chave_publica.asc
```

### Exportar Chave Privada

```bash
# Exportar chave privada para arquivo (MANTENHA SEGURO!)
gpg --armor --export-secret-keys seu_email@exemplo.com > chave_privada.asc
```

⚠️ **ATENÇÃO**: A chave privada deve ser mantida em segredo absoluto. Nunca compartilhe ou exponha sua chave privada.

## Comandos Disponíveis

Teletools Cipher oferece dois comandos principais para gerenciar a criptografia e descriptografia de arquivos:

### `encrypt` - Criptografia de Arquivos

Criptografa um arquivo ou todos os arquivos de um diretório usando uma chave pública GPG.

**Finalidade:**
- Proteger arquivos sensíveis com criptografia forte
- Preparar dados para transferência segura
- Criar backups criptografados

**Uso:**
```bash
cipher encrypt [CHAVE_PUBLICA] [ARQUIVO_OU_DIRETORIO] [PASTA_SAIDA]
```

### `decrypt` - Descriptografia de Arquivos

Descriptografa arquivos `.gpg` usando uma chave privada GPG.

**Finalidade:**
- Recuperar arquivos originais de versões criptografadas
- Acessar dados protegidos recebidos de terceiros
- Restaurar backups criptografados

**Uso:**
```bash
cipher decrypt [CHAVE_PRIVADA] [ARQUIVO_OU_DIRETORIO] [PASTA_SAIDA]
```

## Criptografia de Arquivos

### Uso Básico

```bash
# Ative o ambiente teletools
$ source teletools/.venv/bin/activate

# Execute o cliente cipher
(teletools) $ cipher_cli encrypt --help

Usage: cipher_cli encrypt [OPTIONS] PUBLIC_KEY_FILE INPUT_PATH OUTPUT_FOLDER

 Encrypt files using RSA public key.

 This command encrypts one or more files using the specified RSA public key. The encryption
 process uses hybrid encryption combining RSA and AES for efficient handling of large files.
 
 Args:     
    public_key_file: Path to the RSA public key file (PEM format)
    input_file_or_folder: Path to file or folder to encrypt     
    output_folder: Destination folder for encrypted files (optional)      
    
 Returns:     
    None: Results are displayed to console
 
 Raises:     
    typer.Exit: On encryption failure or invalid inputs      
    
 Examples:     
    # Encrypt a single file     
    $ cipher_cli encrypt public.pem data.txt encrypted/          
    
    # Encrypt all files in a folder     
    $ cipher_cli encrypt public.pem data_folder/ encrypted/
    
    # Encrypt to same location     
    $ cipher_cli encrypt public.pem data.txt

╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────╮
│ *    public_key_file           TEXT        Path to the public key file used for encryption.    │
│                                            Must be a valid file containing the public key in   │
│                                            the appropriate format.                             │
│                                            [required]                                          │
│ *    input_file_or_folder      INPUT_PATH  Path to the input file or folder to be encrypted.   │
│                                            If a folder is provided, all files within it will   │
│                                            be encrypted (non-recursively).                     │
│                                            [required]                                          │
│      output_folder             TEXT        Path to the output folder where encrypted content   │
│                                            will be saved. If not specified, encrypted files    │
│                                            will be saved in the same location as the input.    │
╰────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                    │
╰────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Criptografar um único arquivo

```bash
# Ative o ambiente teletools
$ source repositorios/teletools/.venv/bin/activate

# Criptografar um arquivo específico
(teletools) $ cipher encrypt chave_publica.asc documento.txt arquivos_criptografados/

✅ Encryption completed successfully!

# Desative o ambiente virtual Python
(teletools) $ deactivate
$
```

### Criptografar todos os arquivos de um diretório

```bash
# Ative o ambiente teletools
$ source repositorios/teletools/.venv/bin/activate

# Criptografar todos os arquivos de uma pasta
(teletools) $ cipher encrypt chave_publica.asc dados_sensiveis/ dados_criptografados/

Public key file chave_publica.asc found.
File dados_sensiveis/documento1.txt successfully encrypted to dados_criptografados/documento1.txt.gpg
File dados_sensiveis/documento2.pdf successfully encrypted to dados_criptografados/documento2.pdf.gpg
File dados_sensiveis/planilha.xlsx successfully encrypted to dados_criptografados/planilha.xlsx.gpg
✅ Encryption completed successfully!

# Desative o ambiente virtual Python
(teletools) $ deactivate
$
```

### Criptografar no mesmo local do arquivo original

```bash
# Ative o ambiente teletools
$ source repositorios/teletools/.venv/bin/activate

# Omitir pasta de saída - arquivos .gpg serão criados no mesmo diretório
(teletools) $ cipher encrypt chave_publica.asc documento_importante.txt

Public key file chave_publica.asc found.
File documento_importante.txt successfully encrypted to documento_importante.txt.gpg
✅ Encryption completed successfully!

# Desative o ambiente virtual Python
(teletools) $ deactivate
$
```

### Processo de Criptografia

O comando `encrypt` executa as seguintes etapas:

1. **Validação da chave pública:**
   - Verifica se o arquivo de chave pública existe
   - Importa a chave no keyring do GPG
   - Valida que a chave é válida e pode ser usada para criptografia

2. **Preparação do ambiente:**
   - Verifica se o arquivo/diretório de entrada existe
   - Cria a pasta de saída se especificada e não existir
   - Se nenhuma pasta de saída for especificada, usa a pasta do arquivo de entrada

3. **Processamento de arquivos:**
   - **Arquivo único**: Criptografa o arquivo diretamente
   - **Diretório**: Processa todos os arquivos no diretório (não recursivo)

4. **Criptografia:**
   - Usa GPG com a chave pública especificada
   - Cada arquivo é criptografado individualmente
   - Arquivos criptografados recebem a extensão `.gpg`
   - Aplica `always_trust=True` para evitar interação do usuário

5. **Confirmação:**
   - Exibe mensagem de sucesso para cada arquivo processado
   - Mostra caminho completo do arquivo criptografado gerado

#### Formato dos Arquivos Criptografados

- **Extensão**: `.gpg` é adicionada ao nome do arquivo original
- **Formato**: Binário GPG padrão (OpenPGP)
- **Compatibilidade**: Pode ser descriptografado com qualquer ferramenta compatível com GPG
- **Exemplo**: `documento.txt` → `documento.txt.gpg`

## Descriptografia de Arquivos

### Uso Básico

```bash
# Ative o ambiente teletools
$ source teletools/.venv/bin/activate

# Execute o cliente cipher
(teletools) $ cipher_cli decrypt --help

Usage: cipher_cli decrypt [OPTIONS] PRIVATE_KEY_FILE INPUT_PATH OUTPUT_FOLDER

 Decrypt files using RSA private key.

 This command decrypts one or more files that were encrypted using the corresponding RSA public
 key. The decryption process reverses the hybrid encryption (RSA + AES) used during encryption.
 
 Args:     
    private_key_file: Path to the RSA private key file (PEM format)
    input_file_or_folder: Path to encrypted file or folder     
    output_folder: Destination folder for decrypted files (optional)      
    
 Returns:     
    None: Results are displayed to console      
    
 Raises:
    typer.Exit: On decryption failure or invalid inputs      
    
 Examples:     
    # Decrypt a single file
    $ cipher_cli decrypt private.pem encrypted.bin decrypted/          
    
    # Decrypt all files in a folder     
    $ cipher_cli decrypt private.pem encrypted_folder/ decrypted/
    
    # Decrypt to same location     
    $ cipher_cli decrypt private.pem encrypted.bin

╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────╮
│ *    private_key_file          TEXT        Path to the private key file used for decryption.   │
│                                            Must be a valid file containing the private key in  │
│                                            the appropriate format.                             │
│                                            [required]                                          │
│ *    input_file_or_folder      INPUT_PATH  Path to the input file or folder to be decrypted.   │
│                                            If a folder is provided, all files within it will   │
│                                            be decrypted (non-recursively).                     │
│                                            [required]                                          │
│      output_folder             TEXT        Path to the output folder where decrypted content   │
│                                            will be saved. If not specified, decrypted files    │
│                                            will be saved in the same location as the input.    │
╰────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                    │
╰────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Descriptografar um único arquivo

```bash
# Ative o ambiente teletools
$ source repositorios/teletools/.venv/bin/activate

# Descriptografar um arquivo específico
(teletools) $ cipher_cli decrypt chave_privada.asc documento.txt.gpg arquivos_descriptografados/

File documento.txt.gpg sucessfully decrypted to arquivos_descriptografados/documento.txt
✅ Decryption completed successfully!

# Desative o ambiente virtual Python
(teletools) $ deactivate
$
```

### Descriptografar todos os arquivos de um diretório

```bash
# Ative o ambiente teletools
$ source repositorios/teletools/.venv/bin/activate

# Descriptografar todos os arquivos .gpg de uma pasta
(teletools) $ cipher_cli decrypt chave_privada.asc dados_criptografados/ dados_recuperados/

File dados_criptografados/documento1.txt.gpg sucessfully decrypted to dados_recuperados/documento1.txt
File dados_criptografados/documento2.pdf.gpg sucessfully decrypted to dados_recuperados/documento2.pdf
File dados_criptografados/planilha.xlsx.gpg sucessfully decrypted to dados_recuperados/planilha.xlsx
✅ Decryption completed successfully!

# Desative o ambiente virtual Python
(teletools) $ deactivate
$
```

### Descriptografar no mesmo local do arquivo original

```bash
# Ative o ambiente teletools
$ source repositorios/teletools/.venv/bin/activate

# Omitir pasta de saída - arquivos descriptografados serão criados no mesmo diretório
(teletools) $ cipher_cli decrypt chave_privada.asc documento_importante.txt.gpg

File documento_importante.txt.gpg sucessfully decrypted to documento_importante.txt
✅ Decryption completed successfully!

# Desative o ambiente virtual Python
(teletools) $ deactivate
$
```

### Processo de Descriptografia

O comando `decrypt` executa as seguintes etapas:

1. **Validação da chave privada:**
   - Verifica se o arquivo de chave privada existe
   - Importa a chave no keyring do GPG
   - Valida que a chave é válida e pode ser usada para descriptografia

2. **Preparação do ambiente:**
   - Verifica se o arquivo/diretório de entrada existe
   - Cria a pasta de saída se especificada e não existir
   - Se nenhuma pasta de saída for especificada, usa a pasta do arquivo de entrada

3. **Processamento de arquivos:**
   - **Arquivo único**: Descriptografa o arquivo `.gpg` diretamente
   - **Diretório**: Processa apenas arquivos com extensão `.gpg` (não recursivo)

4. **Descriptografia:**
   - Usa GPG com a chave privada especificada
   - Cada arquivo é descriptografado individualmente
   - Remove a extensão `.gpg` do nome do arquivo original
   - Se a chave privada tiver senha, o GPG solicitará a senha

5. **Confirmação:**
   - Exibe mensagem de sucesso para cada arquivo processado
   - Mostra caminho completo do arquivo descriptografado gerado

## Casos de Uso

### Proteção de Dados Sensíveis

```bash
# Cenário: Proteger CDRs antes de análise
cipher_cli encrypt chave_publica.asc cdrs_originais/ cdrs_protegidos/

# Análise é feita em ambiente seguro após descriptografar
cipher_cli decrypt chave_privada.asc cdrs_protegidos/ ambiente_analise/
```

### Transferência Segura de Arquivos

```bash
# Cenário: Enviar relatórios confidenciais
# 1. Criptografar com chave pública do destinatário
cipher_cli encrypt chave_publica_destinatario.asc relatorio_fiscal.pdf arquivos_envio/

# 2. Transferir arquivo .gpg por canal inseguro (email, FTP, etc.)
# 3. Destinatário descriptografa com sua chave privada
cipher_cli decrypt chave_privada_destinatario.asc relatorio_fiscal.pdf.gpg
```

### Backup Criptografado

```bash
# Cenário: Criar backup criptografado de dados
# 1. Comprimir dados
tar -czf backup_2025.tar.gz dados_importantes/

# 2. Criptografar backup
cipher_cli encrypt chave_publica.asc backup_2025.tar.gz backups_criptografados/

# 3. Para restaurar
cipher_cli decrypt chave_privada.asc backups_criptografados/backup_2025.tar.gz.gpg restauracao/
tar -xzf restauracao/backup_2025.tar.gz
```

## Segurança e Boas Práticas

### Proteção de Chaves Privadas

1. **Armazenamento Seguro:**
   - Mantenha chaves privadas em diretórios com permissões restritas
   ```bash
   chmod 600 chave_privada.asc
   chmod 700 ~/.gnupg/
   ```

2. **Backup Seguro:**
   - Faça backup da chave privada em mídia offline
   - Considere usar um cofre físico ou serviço de custódia de chaves

3. **Senha Forte:**
   - Use sempre uma senha (passphrase) forte na chave privada
   - Considere usar gerenciador de senhas

4. **Não Compartilhar:**
   - Nunca compartilhe a chave privada
   - Nunca envie por email, chat ou armazene em nuvem sem proteção adicional

### Distribuição de Chaves Públicas

1. **Compartilhamento Seguro:**
   - Chaves públicas podem ser compartilhadas livremente
   - Considere usar servidor de chaves público (keyserver)
   - Publique em site institucional ou repositório

2. **Verificação de Integridade:**
   - Forneça fingerprint da chave por canal separado
   ```bash
   gpg --fingerprint seu_email@exemplo.com
   ```

### Gestão de Chaves

1. **Validade:**
   - Configure validade apropriada para chaves
   - Renove chaves antes da expiração

2. **Revogação:**
   - Gere certificado de revogação preventivamente
   ```bash
   gpg --gen-revoke seu_email@exemplo.com > revoke.asc
   ```

3. **Múltiplas Chaves:**
   - Considere chaves separadas para diferentes propósitos
   - Use subchaves para operações específicas

## Limitações Conhecidas

1. **Processamento não recursivo**: Ao criptografar/descriptografar diretórios, apenas arquivos no nível raiz são processados (subdiretórios são ignorados)

2. **Dependência do GPG**: Requer instalação do GnuPG no sistema

3. **Senha interativa**: Se a chave privada tiver senha, o GPG solicitará interativamente durante descriptografia

4. **Tamanho de arquivos**: Para arquivos muito grandes (>GB), considere compressão prévia

5. **Metadados não protegidos**: Nome do arquivo original é preservado no arquivo criptografado

6. **Sem compressão automática**: Arquivos não são comprimidos automaticamente antes da criptografia

## Solução de Problemas

### Erro: "Public key file not found"

**Causa**: Arquivo de chave pública não existe no caminho especificado.

**Solução**:
```bash
# Verificar se o arquivo existe
ls -l chave_publica.asc

# Verificar caminho absoluto
readlink -f chave_publica.asc
```

### Erro: "Error reading public key file"

**Causa**: Arquivo não contém chave GPG válida ou está corrompido.

**Solução**:
```bash
# Verificar conteúdo do arquivo
gpg --show-keys chave_publica.asc

# Importar manualmente para testar
gpg --import chave_publica.asc

# Re-exportar chave se necessário
gpg --armor --export seu_email@exemplo.com > nova_chave_publica.asc
```

### Erro: "Missing required dependency"

**Causa**: Biblioteca python-gnupg não está instalada.

**Solução**:
```bash
# Reinstalar dependências
uv sync

# Ou instalar diretamente
pip install python-gnupg
```

**Verificar instalação do GPG**:
```bash
# Linux
which gpg
gpg --version

# Windows
where gpg
gpg --version
```

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
