# Teletools ABR Loader

> **[← Voltar para o README principal](../README.md)** | [Database API](database.md) | [CDR Stage Database](cdr_stage.md)

Teletools ABR Loader é um cliente de linha de comando para importação de dados de telecomunicações brasileiras da ABR Telecom (Associação Brasileira de Recursos em Telecomunicações).

## Índice

- [Teletools ABR Loader](#teletools-abr-loader)
  - [Índice](#índice)
  - [Visão Geral](#visão-geral)
    - [Características Principais](#características-principais)
  - [Instalação e Configuração](#instalação-e-configuração)
    - [Pré-requisitos](#pré-requisitos)
    - [Instalação do Teletools](#instalação-do-teletools)
    - [Configuração para acesso ao banco de dados Teletools CDR Stage Database](#configuração-para-acesso-ao-banco-de-dados-teletools-cdr-stage-database)
      - [Opção 1: Arquivo de Configuração do Usuário (Recomendado)](#opção-1-arquivo-de-configuração-do-usuário-recomendado)
      - [Opção 2: Variáveis de Ambiente do Sistema](#opção-2-variáveis-de-ambiente-do-sistema)
      - [Testar a Conexão](#testar-a-conexão)
  - [Comandos Disponíveis](#comandos-disponíveis)
    - [`load-pip` - Importação de Dados de Portabilidade](#load-pip---importação-de-dados-de-portabilidade)
    - [`load-nsapn` - Importação do Plano de Numeração](#load-nsapn---importação-do-plano-de-numeração)
    - [`test-connection` - Teste de Conectividade](#test-connection---teste-de-conectividade)
  - [Importação de Dados de Portabilidade (PIP)](#importação-de-dados-de-portabilidade-pip)
    - [Extração dos Arquivos](#extração-dos-arquivos)
    - [Extração dos arquivos para importação no PIP](#extração-dos-arquivos-para-importação-no-pip)
    - [Uso Básico](#uso-básico)
    - [Importar um único arquivo](#importar-um-único-arquivo)
    - [Importar todos os arquivos de um diretório](#importar-todos-os-arquivos-de-um-diretório)
    - [Processo de Importação](#processo-de-importação)
      - [Dicas de Performance](#dicas-de-performance)
    - [Limitações Conhecidas](#limitações-conhecidas)
  - [Importação do Plano de Numeração](#importação-do-plano-de-numeração)
    - [Descrição](#descrição)
    - [Fontes de Dados Oficiais](#fontes-de-dados-oficiais)
    - [Formato dos Arquivos](#formato-dos-arquivos)
      - [CNG](#cng)
      - [SME](#sme)
      - [SMP](#smp)
      - [STFC](#stfc)
    - [Uso Básico](#uso-básico-1)
    - [Importar um único arquivo](#importar-um-único-arquivo-1)
    - [Importar todos os arquivos de um diretório](#importar-todos-os-arquivos-de-um-diretório-1)
    - [Importar e manter tabelas temporárias](#importar-e-manter-tabelas-temporárias)
    - [Processo de Importação](#processo-de-importação-1)
    - [Limitações Conhecidas](#limitações-conhecidas-1)
  - [Contribuindo](#contribuindo)
  - [Licença](#licença)
  - [Contato e Suporte](#contato-e-suporte)

## Visão Geral

Teletools ABR Loader importa dados de relatório de bilhetes de portabilidade concluídos e de faixas de numeração da ABR Telecom em um banco de dados PostgreSQL. A ferramenta suporta dois tipos principais de dados:

- **Dados de Portabilidade**: Histórico de portabilidade numérica do sistema PIP (Portal de Informações da Portabilidade)
- **Plano de Numeração**: Designação de faixas de numeração do sistema NSAPN (Novo Sistema de Administração dos Planos de Numeração)

### Características Principais

- ✅ **Importação em Lote**: Processa arquivo único ou diretórios completos
- ✅ **Alta Performance**: Processamento em chunks e bulk inserts otimizados
- ✅ **Detecção Automática**: Identifica tipos de arquivo automaticamente
- ✅ **Logging Completo**: Rastreamento detalhado do progresso de importação
- ✅ **Gestão de Índices**: Criação e reconstrução automática de índices
- ✅ **Validação de Dados**: Otimização de tipos e validação de estrutura

## Instalação e Configuração

### Pré-requisitos

- Python 3.13+ com gerenciador de pacotes [UV](https://docs.astral.sh/uv/)
- Banco de dados [Teletools CDR Stage Database](cdr_stage.md)

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

### Configuração para acesso ao banco de dados Teletools CDR Stage Database

Existem duas formas de configurar as variáveis de ambiente necessárias:

#### Opção 1: Arquivo de Configuração do Usuário (Recomendado)

**Crie o arquivo** `~/.teletools.env`:

```bash
# Arquivo: ~/.teletools.env

# Configurações obrigatórias
TELETOOLS_DB_HOST=localhost
TELETOOLS_DB_NAME=telecom_db
TELETOOLS_DB_USER=seu_usuario
TELETOOLS_DB_PASSWORD=sua_senha

# Configurações opcionais
TELETOOLS_DB_PORT=5432
```

**Vantagens:**
- Centraliza todas as configurações em um único arquivo
- Facilita manutenção e atualização
- Mantém credenciais fora do controle de versão
- Carregamento automático pelo aplicativo

#### Opção 2: Variáveis de Ambiente do Sistema

**Defina as variáveis no sistema operacional:**

```bash
# Adicionar ao ~/.bashrc ou ~/.zshrc para persistência no usuário
# Configurações obrigatórias
export TELETOOLS_DB_HOST=localhost
export TELETOOLS_DB_NAME=telecom_db
export TELETOOLS_DB_USER=seu_usuario
export TELETOOLS_DB_PASSWORD=sua_senha
# Configurações opcionais
export TELETOOLS_DB_PORT=5432

# Ou adicionar ao /etc/environment para persistência no sistema
# Configurações obrigatórias
TELETOOLS_DB_HOST=localhost
TELETOOLS_DB_NAME=telecom_db
TELETOOLS_DB_USER=seu_usuario
TELETOOLS_DB_PASSWORD=sua_senha
# Configurações opcionais
TELETOOLS_DB_PORT=5432
```

**Vantagens:**
- Útil em ambientes containerizados (Docker, Kubernetes)
- Integração com sistemas de CI/CD
- Configuração por ambiente (desenvolvimento, produção)
- Configuração pode ser global, não dependente do usuário

**Observação:** Se ambas as opções estiverem configuradas, o arquivo `~/.teletools.env` terá prioridade sobre as variáveis de ambiente do sistema.

#### Testar a Conexão

**Teste a conexão após configurar:**

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

## Comandos Disponíveis

Teletools ABR Loader oferece três comandos principais para gerenciar a importação de dados da ABR Telecom:

### `load-pip` - Importação de Dados de Portabilidade

Importa dados de portabilidade numérica do sistema a partir de relatório de bilhetes concluídos extraídos do PIP (Portal de Informações da Portabilidade) da ABR Telecom.

**Finalidade:**
- Carregar histórico de bilhetes de portabilidade concluídos
- Rastrear mudanças de operadora por número telefônico
- Manter base histórica para análises de portabilidade

**Uso:**
```bash
abr_loader load-pip [ARQUIVO_OU_DIRETÓRIO]
```

### `load-nsapn` - Importação do Plano de Numeração

Importa dados de designação de faixas de numeração do sistema NSAPN (Novo Sistema de Administração dos Planos de Numeração).

**Finalidade:**
- Carregar faixas de numeração designadas às operadoras
- Manter plano de numeração atualizado
- Permitir identificação de operadora original por faixa numérica

**Uso:**
```bash
abr_loader load-nsapn [ARQUIVO_OU_DIRETÓRIO]
```

### `test-connection` - Teste de Conectividade

Verifica a conectividade com o banco de dados PostgreSQL usando as credenciais configuradas.

**Finalidade:**
- Validar configuração de conexão antes de importações
- Diagnosticar problemas de conectividade
- Confirmar que credenciais estão corretas

**Uso:**
```bash
abr_loader test-connection
```

## Importação de Dados de Portabilidade (PIP)

### Extração dos Arquivos

Os arquivos para importação devem ser relatórios de bilhetes concluídos, extraídos do sistema PIP, no formato CSV comprimido (*.csv.gz) com as seguintes colunas:

| Coluna do Relatório        | Coluna Layout PIP | Descrição PIP              | Tipo no BD   |
|----------------------------|-------------------|----------------------------|--------------|
| TIPO REG                   | -                 | Tipo de Registro           | INT8         |
| NUMERO BP                  | POBNROBILHETE     | Número BP                  | INT8         |
| TN INICIAL                 | POBTNINI          | TN Inicial                 | INT8         |
| RECEPTORA                  | CIACODCIA         | Código Operadora Receptora | INT2         |
| RECEPTORA                  | POBCIATXTDESC     | Nome Operadora Receptora   | VARCHAR(100) |
| DOADORA                    | CIACODCIA_DOA     | Código Operadora Doadora   | INT2         |
| DOADORA                    | POBCIATXTDESC_DOA | Nome Operadora Doadora     | VARCHAR(100) |
| DATA AGENDAMENTO           | POBDATULTAG       | Data Agendamento           | TIMESTAMP    |
| STATUS ATUAL               | POBNROSTATUS      | Código Status Atual        | INT2         |
| STATUS ATUAL               | POBTXTDESCSTATUS  | Descrição Status Atual     | VARCHAR(50)  |
| IND. PORTAR PARA ORIGEM    | POBINDPTO         | Indicador Portar p/ Origem | INT2         |

Exemplo de dados do arquivo
```csv
TIPO REG;NUMERO BP;TN INICIAL;RECEPTORA;RECEPTORA;DOADORA;DOADORA;DATA AGENDAMENTO;STATUS ATUAL;STATUS ATUAL;IND. PORTAR PARA ORIGEM
1;7266080;2139838686;0123;TIM SA;0121;EMBRATEL;11/06/2010 00:00:00;1;Ativo;Nao
1;7266082;2139838688;0123;TIM SA;0121;EMBRATEL;11/06/2010 00:00:00;1;Ativo;Nao
1;7266083;2139838689;0123;TIM SA;0121;EMBRATEL;11/06/2010 00:00:00;1;Ativo;Nao
```

### Extração dos arquivos para importação no PIP

Para obter os arquivos para importação no PIP execute e exporte o relatório "BP Concluído" em formato CSV, com layout de saída com as colunas indicadas:

**Parâmetros para extração do relatório de BP Concluído**

![Layout de saída do PIP](https://raw.githubusercontent.com/InovaFiscaliza/teletools/0daa0d46077d5164df1f3c62e7061fb821bd4546/images/pip_bp_concluido.png)

**Layout de saída**

![Layout de saída do PIP](https://raw.githubusercontent.com/InovaFiscaliza/teletools/0daa0d46077d5164df1f3c62e7061fb821bd4546/images/pip_layout_saida.png)



### Uso Básico

```bash
# Ative o ambiente teletools
$ source teletools/.venv/bin/activate

# Execute o cliente abr_loader
(teletools) $ abr_loader load-pip --help

Usage: abr_loader load-pip [OPTIONS] INPUT_PATH

 Import ABR portability data into PostgreSQL database.

 This command processes Brazilian phone number portability reports from ABR Telecom's PIP
 system. The input files should be in CSV format (*.csv.gz) with specific column structure
 defined by ABR standards.

 The import process includes: 
    - Automatic table creation with optimized schema 
    - Chunked processing for memory efficiency 
    - Bulk insertions using PostgreSQL COPY FROM 
    - Comprehensive progress tracking and error handling 
    - Data type optimization and validation

 Args:     
    input_path: Path to CSV file or directory containing CSV files     
    drop_table: Whether to drop staging table after import (default: True)
    rebuild_database: Whether to rebuild the entire portability database before import     
    rebuild_indexes: Whether to rebuild portability database indexes

 Returns:     
    None: Results are logged to console and log file

Raises:     
    typer.Exit: On file not found, database connection errors, or import failures

 Examples:     
 
 Import single file with default settings:     
 $ abr_loader load-pip data.csv.gz

 Import directory with rebuild database:     
 $ abr_loader load-pip /data/ --rebuild-database
 
 No drop staging table after import:     
 $ abr_loader load-pip /data/ --no-drop-table

╭─ Arguments ───────────────────────────────────────────────────────────────────────────────╮
│ *    input_path      TEXT  Path to input file or directory. If directory provided, all    │
│                            *.csv.gz files will be processed recursively. Supports single  │
│                            files or batch processing.                                     │
│                            [required]                                                     │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────╮
│ --drop-table          --no-drop-table            Drop table after import. When enabled,   │
│                                                  imported data will be deleted after      │
│                                                  import. Use --no-drop-table to keep it   │
│                                                  after import.                            │
│                                                  [default: drop-table]                    │
│ --rebuild-database    --no-rebuild-database      Rebuild entire portability database.     │
│                                                  When enabled, existing data will be      │
│                                                  deleted before import. Use               │
│                                                  --no-rebuild-database to append to       │
│                                                  existing data.                           │
│                                                  [default: no-rebuild-database]           │
│ --rebuild-indexes     --no-rebuild-indexes       Rebuild portability database             │
│                                                  indexes.When enabled, existing indexes   │
│                                                  will be deleted before import and        │
│                                                  rebuilt. Use --no-rebuild-indexes to     │
│                                                  keep existing indexes.                   │
│                                                  [default: no-rebuild-indexes]            │
│ --help                                           Show this message and exit.              │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
```

### Importar um único arquivo

```bash
# Ative o ambiente teletools
$ source repositorios/teletools/.venv/bin/activate

# Importe um arquivo
(teletools) $ abr_loader load-pip /data/cdr/arquivos_auxiliares/abr/portabilidade/pip/relatorios_mensais/relatorio_bilhetes_portabilidade_pip_202502.csv.gz

# Desative o ambiente virtual Python
(teletools) $ deactivate
$
```

### Importar todos os arquivos de um diretório

```bash
# Ative o ambiente teletools
$ source repositorios/teletools/.venv/bin/activate

# Importe vários arquivos .csv.gz contidos em um diretório
(teletools) $ abr_loader load-pip /data/cdr/arquivos_auxiliares/abr/portabilidade/pip/

# Desative o ambiente virtual Python
(teletools) $ deactivate
$
```

### Processo de Importação

O comando `load-pip` executa as seguintes etapas:

1. **Preparação da tabela de staging:**
   - Cria tabela temporária: `entrada.teletools_import_portabilidade`
   - Trunca tabela existente para garantir importação limpa

2. **Processamento de arquivos em chunks:**
   - Lê arquivos CSV comprimidos (*.csv.gz) em blocos de 100.000 linhas
   - Aplica otimizações de tipo de dados (categorias, inteiros apropriados)
   - Processa datas no formato brasileiro (DD/MM/YYYY HH:MM:SS)

3. **Transformação de dados:**
   - Converte indicadores textuais para numéricos ("Sim"/"Nao" → 1/0)
   - Otimiza códigos de operadoras para tipos inteiros apropriados
   - Remove registros com identificadores críticos ausentes

4. **Inserção em lote:**
   - Usa PostgreSQL COPY FROM para inserções de alta performance
   - Registra estatísticas detalhadas por chunk e arquivo

5. **Reconstrução da base (opcional):**
   - Se `--rebuild-database` for especificado, remove e recria `public.teletools_tb_portabilidade_historico`
   - Se `--rebuild-indexes` for especificado, reconstrói índices da tabela  `public.teletools_tb_portabilidade_historico` após a importação

6. **Atualização da tabela histórica:**
   - Transfere dados da staging para tabela particionada  `public.teletools_tb_portabilidade_historico`
   - Executa operação upsert baseada em (cn, tn_inicial, data_agendamento)
   - Atualiza registros existentes ou insere novos

7. **Criação/reconstrução de índices:**
   - Cria índices automaticamente se a tabela foi recém-criada
   - Reconstrói índices se solicitado (recomendado após importações grandes) com a opção `--rebuild-indexes`

8. **Atualização de prestadoras:**
   - Atualiza tabela de referência `public.teletools_tb_prestadoras`
   - Adiciona novas operadoras identificadas nos arquivos

9. **Limpeza:**
   - Remove tabela de staging. Se `--no-drop-table` for especificado a tabela é mantida.


#### Dicas de Performance

```bash
# Para datasets grandes, reconstruir banco e índices de uma vez
abr_loader load-pip /dados/grandes/ --rebuild-database

# Para atualizações incrementais, não reconstruir
abr_loader load-pip /dados/novos/

# Se houver lentidão após várias atualizações incrementais, reconstruir índices
abr_loader load-pip /dados/novos/ --rebuild-indexes
```

### Limitações Conhecidas

1. **Formato de arquivo fixo:** Requer formato CSV específico da ABR
2. **Encoding:** Assume UTF-8 (pode requerer ajuste para outros encodings)
3. **Sem paralelização:** Processa arquivos sequencialmente
4. **PostgreSQL apenas:** Não suporta outros bancos de dados nativamente

## Importação do Plano de Numeração

### Descrição

O comando `load-nsapn` importa dados do Plano de Numeração brasileiro a partir dos relatórios oficiais da ABR Telecom. Este comando processa diferentes tipos de arquivos de numeração (STFC, SMP, SME, CNG, SUP) e os consolida em tabelas otimizadas no PostgreSQL.

### Fontes de Dados Oficiais

Todos os arquivos para importação devem ser obtidos do portal oficial da ABR Telecom:

| Tipo de Serviço | Descrição | URL de Download |
|-----------------|-----------|-----------------|
| **CNG** | Código Não Geográfico (0800, 0300, etc.) | https://easi.abrtelecom.com.br/nsapn/#/public/files/download/cng |
| **SME** | Serviço Móvel Especializado | https://easi.abrtelecom.com.br/nsapn/#/public/files/download/sme |
| **SMP** | Serviço Móvel Pessoal | https://easi.abrtelecom.com.br/nsapn/#/public/files/download/smp |
| **STFC** | Serviço Telefônico Fixo Comutado | https://easi.abrtelecom.com.br/nsapn/#/public/files/download/stfc |
| **STFC-FATB** | STFC Fora da Área de Tarifa Básica | https://easi.abrtelecom.com.br/nsapn/#/public/files/download/stfc-fatb |
| **SUP** | Serviços de Utilidade Pública | https://easi.abrtelecom.com.br/nsapn/#/public/files/download/sup |

⚠️ **Importante:** 
- Os arquivos contêm dados oficiais da ANATEL e são atualizados regularmente. Sempre baixe as versões mais recentes para garantir dados precisos.
- A importação de arquivos SUP está desabilitada na versão atual

### Formato dos Arquivos

Os arquivos devem ser mantidos em seu formato original de download: CSV comprimido (*.zip) com delimitador ponto-e-vírgula (;) e encoding Latin-1. O tipo de arquivo é detectado automaticamente pelo prefixo do nome do arquivo.

Exemplo de dados dos arquivos:

#### CNG
```csv
# Nome da Prestadora;CNPJ da Prestadora;Cdigo No Geogrfico;Status
TELECOM SOUTH AMERICA LTDA.;02777002000117;8000387204;1
AGERA TELECOMUNICACOES SA;01009876000161;8005917204;1
OI S.A. - EM RECUPERACAO JUDICIAL;33000118000179;8000717469;1
CLARO S.A.;40432544000147;8007227505;1
CLARO S.A.;40432544000147;8007357505;1
CLARO S.A.;40432544000147;8007037632;1
CLARO S.A.;40432544000147;8007227632;1
CLARO S.A.;40432544000147;8007247632;1
AGERA TELECOMUNICACOES SA;01009876000161;8005917632;1
```
#### SME
```csv
# Nome da Prestadora;CNPJ da Prestadora;Cdigo Nacional;Prefixo;Faixa Inicial;Faixa Final;Status
Claro NXT Telecomunicaes LTDA;66970229000167;11;7801;0000;0999;1
Claro NXT Telecomunicaes LTDA;66970229000167;11;7801;1000;1999;1
Claro NXT Telecomunicaes LTDA;66970229000167;11;7801;2000;2999;1
Claro NXT Telecomunicaes LTDA;66970229000167;11;7801;3000;3999;1
Claro NXT Telecomunicaes LTDA;66970229000167;11;7801;4000;4999;1
Claro NXT Telecomunicaes LTDA;66970229000167;11;7801;5000;5999;1
Claro NXT Telecomunicaes LTDA;66970229000167;11;7801;6000;6999;1
Claro NXT Telecomunicaes LTDA;66970229000167;11;7801;7000;7999;1
Claro NXT Telecomunicaes LTDA;66970229000167;11;7801;8000;8999;1
```
#### SMP
```csv
# Nome da Prestadora;CNPJ da Prestadora;Cdigo Nacional;Prefixo;Faixa Inicial;Faixa Final;Status
1NCE TELECOMUNICACOES LTDA;45061943000162;11;91932;0000;9999;1
1NCE TELECOMUNICACOES LTDA;45061943000162;11;92119;0000;9999;1
1NCE TELECOMUNICACOES LTDA;45061943000162;12;91002;0000;9999;1
1NCE TELECOMUNICACOES LTDA;45061943000162;12;91007;0000;9999;1
1NCE TELECOMUNICACOES LTDA;45061943000162;12;91009;0000;9999;1
1NCE TELECOMUNICACOES LTDA;45061943000162;12;91044;0000;9999;1
1NCE TELECOMUNICACOES LTDA;45061943000162;12;91045;0000;9999;1
1NCE TELECOMUNICACOES LTDA;45061943000162;12;91109;0000;9999;1
1NCE TELECOMUNICACOES LTDA;45061943000162;13;91002;0000;9999;1
```
#### STFC
```csv
# Nome da Prestadora;CNPJ da Prestadora;UF;Cdigo Nacional;Prefixo;Faixa Inicial;Faixa Final;Cdigo CNL;Nome da Localidade;rea Local;Sigla rea Local;Cdigo rea Local;Status
101telecom Servicos De Telecomunicacoes Ltda;31063800000185;SP;11;5201;0000;0999;11000;So Paulo;So Paulo;SPO;3827;1
3CORP TECHNOLOGY INFRAESTRUTURA DE TELECOM LTDA;04238297000189;SP;11;4922;1000;1999;11308;Itu;Itu;ITU;3537;1
3CORP TECHNOLOGY INFRAESTRUTURA DE TELECOM LTDA;04238297000189;SP;11;5405;0000;0999;11000;So Paulo;So Paulo;SPO;3827;1
3CORP TECHNOLOGY INFRAESTRUTURA DE TELECOM LTDA;04238297000189;SP;12;3100;0000;0999;11563;So Jos Dos Campos;So Jos dos Campos;SJC;3822;1
3CORP TECHNOLOGY INFRAESTRUTURA DE TELECOM LTDA;04238297000189;SP;13;3100;0000;0999;11592;Santos;Santos;STS;3807;1
3CORP TECHNOLOGY INFRAESTRUTURA DE TELECOM LTDA;04238297000189;SP;14;3101;0000;0999;11365;Marlia;Marlia;MIA;3591;1
3CORP TECHNOLOGY INFRAESTRUTURA DE TELECOM LTDA;04238297000189;SP;15;3101;0000;0999;11609;Sorocaba;Sorocaba;SOC;3846;1
3CORP TECHNOLOGY INFRAESTRUTURA DE TELECOM LTDA;04238297000189;SP;16;3110;0000;0999;11529;Ribeiro Preto;Ribeiro Preto;RPO;3752;1
3CORP TECHNOLOGY INFRAESTRUTURA DE TELECOM LTDA;04238297000189;SP;17;3110;0000;0999;11562;So Jos Do Rio Preto;So Jos do Rio Preto;SRR;3821;1
```


### Uso Básico

```bash
# Ative o ambiente teletools
$ source teletools/.venv/bin/activate

# Execute o cliente abr_loader
(teletools) $ abr_loader load-nsapn --help

 Usage: abr_loader load-nsapn [OPTIONS] INPUT_PATH

 Import ABR numbering plan data into PostgreSQL database.

 This command processes Brazilian numbering plan public files from ABR Telecom's NSAPN
 system. The input files should be ZIP archives (*.zip) downloaded from the official ABR
 portal containing CSV files with numbering data.

 Supported file types (auto-detected by filename prefix): 
    - STFC: Fixed telephony service numbering (complete data) 
    - SMP/SME: Mobile service numbering (subset of columns) 
    - CNG:  Non-geographic codes (0800, 0300, etc.) 
    - SUP: Public utility service numbering 
    - STFC-FATB: Fixed telephony outside basic tariff area
    
 Data sources:     
    https://easi.abrtelecom.com.br/nsapn/#/public/files/download/
 
 The import process includes: 
    - Automatic file type detection based on filename 
    - Automatic table creation with optimized schema 
    - ZIP file extraction and processing 
    - Chunked processing for memory efficiency 
    - Bulk insertions using PostgreSQL COPY FROM 
    - Comprehensive progress tracking and error handling 
    - Data type optimization and validation

 Args:     
    input_path: Path to ZIP file or directory containing ZIP files     
    drop_table: Whether to drop existing data after import

 Returns:     
    None: Results are logged to console and log file
    
 Raises:     
    typer.Exit: On file not found, database connection errors, or import failures

 Examples:     
    Import single ZIP file:
    $ abr_loader load-nsapn STFC_202401.zip
    
    Import directory of ZIP files:
    $ abr_loader load-nsapn /data/nsapn/
    
    Append data without truncating:
    $ abr_loader load-nsapn /data/nsapn/ --no-drop-table

╭─ Arguments ───────────────────────────────────────────────────────────────────────────────╮
│ *    input_path      TEXT  Path to input file or directory. If directory provided, all    │
│                            *.zip files will be processed recursively. Supports single     │
│                            files or batch processing.                                     │
│                            [required]                                                     │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────╮
│ --drop-table    --no-drop-table      Drop table after import. When enabled, imported data │
│                                      will be deleted after import. Use --no-drop-table to │
│                                      keep it after import.                                │
│                                      [default: no-drop-table]                             │
│ --help                               Show this message and exit.                          │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
```

### Importar um único arquivo

```bash
# Ative o ambiente teletools
$ source repositorios/teletools/.venv/bin/activate

# Importe um arquivo de numeração STFC
(teletools) $ abr_loader load-nsapn /data/cdr/arquivos_auxiliares/abr/numeracao/STFC_202501.zip

# Desative o ambiente virtual Python
(teletools) $ deactivate
$
```

### Importar todos os arquivos de um diretório

```bash
# Ative o ambiente teletools
$ source repositorios/teletools/.venv/bin/activate

# Importe todos os arquivos .zip de numeração contidos em um diretório
# O comando detecta automaticamente o tipo de cada arquivo (STFC, SMP, SME, CNG, SUP)
(teletools) $ abr_loader load-nsapn /data/cdr/arquivos_auxiliares/abr/numeracao/

# Desative o ambiente virtual Python
(teletools) $ deactivate
$
```

### Importar e manter tabelas temporárias

```bash
# Ative o ambiente teletools
$ source repositorios/teletools/.venv/bin/activate

# Importe arquivos e remova tabelas de staging após consolidação
(teletools) $ abr_loader load-nsapn /data/cdr/arquivos_auxiliares/abr/numeracao/ --no-drop-table

# Desative o ambiente virtual Python
(teletools) $ deactivate
$
```

### Processo de Importação

O comando `load-nsapn` executa as seguintes etapas:

1. **Preparação das tabelas de staging:**
   - Cria tabelas temporárias: `entrada.teletools_import_numeracao_stfc_smp_sme`, `entrada.teletools_import_numeracao_cng`, `entrada.teletools_import_numeracao_sup`
   - Trunca tabelas existentes para garantir importação limpa

2. **Detecção automática de tipo:**
   - Analisa o prefixo do nome do arquivo
   - Seleciona o esquema apropriado de colunas e tipos de dados

3. **Importação em chunks:**
   - Processa arquivos em blocos de 100.000 linhas
   - Usa PostgreSQL COPY FROM para inserções em lote de alta performance

4. **Consolidação de dados:**
   - Cria/atualiza tabela final `public.teletools_tb_numeracao`
   - Consolida dados de todas as tabelas de staging

5. **Atualização de prestadoras:**
   - Atualiza tabela de referência `public.teletools_tb_prestadoras`
   - Adiciona novas operadoras identificadas

6. **Limpeza:**
   - Remove tabelas de staging. Se `--no-drop-table` for especificado a tabela é mantida.

### Limitações Conhecidas

1. **Formato de arquivo fixo:** Requer formato CSV específico da ABR com delimitador ponto-e-vírgula
2. **Encoding:** Assume Latin-1 (padrão dos arquivos oficiais da ABR)
3. **Sem paralelização:** Processa arquivos sequencialmente
4. **PostgreSQL apenas:** Não suporta outros bancos de dados nativamente
5. **Dependência de nomes:** Detecção de tipo baseada em prefixo do nome do arquivo

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
