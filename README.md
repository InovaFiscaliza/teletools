[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/InovaFiscaliza/teletools)

<details>
    <summary>Sumário</summary>
    <ol>
        <li><a href="#-teletools">Teletools</a></li>
        <li><a href="#bibliotecas-e-ferramentas">Bibliotecas e ferramentas</a></li>
        <li><a href="#instalação">Instalação</a></li>
        <li><a href="#uso-básico">Uso básico</a></li>
        <li><a href="#fontes-de-dados">Fontes de dados</a></li>
        <li><a href="#referências">Referências</a></li>
    </ol>
</details>


# <img align="left" src="https://raw.githubusercontent.com/InovaFiscaliza/teletools/0daa0d46077d5164df1f3c62e7061fb821bd4546/images/teletools_logo_53_40.png"> Teletools


Teletools é um conjunto de bibliotecas e ferramentas de apoio para pré-processamento e análise de arquivos CDR (Detalhes de Registros de Chamadas) de operadoras brasileiras.


## Bibliotecas e ferramentas

### Bibliotecas Python

| Biblioteca    | Descrição                                                               |
| ------------- | ----------------------------------------------------------------------- |
| cipher        | Biblioteca para criptografar e descriptografar arquivos no formato .gpg |
| [database](docs/database_api_index.md)      | Biblioteca para conexão e operações a banco de dados auxiliares de CDR. |
| preprocessing | Biblioteca para limpeza e preparação de dados                           |
| utils         | Biblioteca com ferramentas diversas e comuns                            |

### Ferramentas de Linha de Comando

| Ferramenta    | Descrição                                                                                |
| ------------- | ---------------------------------------------------------------------------------------- |
| [Cipher](docs/cipher_cli.md)    | Cliente de linha de comando para criptografar e descriptografar arquivos no formato .gpg |
| [ABR Loader](docs/abr_loader.md)    | Cliente de linha de comando para importação de dados da ABR Telecom (portabilidade e numeração) |

### Infraestrutura

| Aplicação     | Descrição |
| ------------- | --------- | 
| [CDR Stage Database](docs/cdr_stage.md) | Banco de dados PostgreSQL conteinerizado e customizado para pré-processamento e análise de CDR |


## Instalação

As bibliotecas e ferramentas foram desenvolvidas para serem executadas em um servidor rodando Redhat Enterprise Linux 9, contudo, embora não testado, podem ser executadas em computadores com outras distribuições Linux ou Windows que atendam aos pré-requisitos. 

### Pré-requisitos para instalação:

- Python 3.13+ com gerenciador de pacotes [UV](https://docs.astral.sh/uv/)
- Instância de banco de dados [Teletools CDR Stage Database](docs/cdr_stage.md)
- [GnuPG](https://www.gnupg.org/download/index.html) ou [Gpg4win](https://gpg4win.org/download.html)

### Procedimento para instalação:

**Em um projeto Python gerenciado pelo UV:**
```bash
$ uv add teletools
```

**Em um ambiente virtual Python gerenciado pelo UV:**
```bash
# Crie o ambiente virtual
$ uv venv ~/teletools --python=3.13

# Ative o ambiente virtual
$ source ~/teletools/bin/activate

# Instale teletools
(teletools) $ uv pip install teletools
```
💡 Utilize essa opção para utilizar os clientes de linha de comando

## Uso básico

### Biblioteca database - Consulta de Dados ABR

```python
from teletools.database.abr_database import query_numbers_carriers

# Consultar informações de operadoras para uma lista de números
numbers = [11987654321, 11912345678, 21987654321]
result = query_numbers_carriers(numbers, reference_date='2024-12-15')

# Acessar nomes de colunas e dados
columns = result['column_names']  # ('nu_terminal', 'nome_prestadora', ...)
data = result['results']          # Lista de tuplas com resultados

# Processar resultados
for row in data:
    print(f"Número: {row[0]}, Operadora: {row[1]}, Portado: {row[2]}")
```

> **Documentação completa:** [docs/database.md](docs/database.md)

### Cliente cipher_cli - Criptografia de Arquivos

```bash
# Ative o ambiente teletools
$ source ~/teletools/bin/activate

# Execute o cliente cipher_cli
(teletools) $ cipher_cli --help

  Usage: cipher_cli [OPTIONS] COMMAND [ARGS]...

 File encryption and decryption CLI tool using RSA keys.

╭─ Options ────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────╮
│ encrypt   Encrypt files using RSA public key.                                            │
│ decrypt   Decrypt files using RSA private key.                                           │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```


### Cliente abr_loader - Importação de Dados ABR Telecom

```bash
# Ative o ambiente teletools
$ source ~/teletools/bin/activate

# Execute o cliente abr_loader
(teletools) $ abr_loader --help

 Usage: abr_loader [OPTIONS] COMMAND [ARGS]...

 ABR Database Loader - Import Brazilian telecom portability and numbering plan data.

╭─ Options ────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────╮
│ load-pip          Import ABR portability data into PostgreSQL database.                  │
│ load-nsapn        Import ABR numbering plan data into PostgreSQL database.               │
│ test-connection   Test database connection and validate configuration.                   │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```

**Exemplos rápidos:**

```bash
# Importar dados de portabilidade (PIP)
(teletools) $ abr_loader load-pip /dados/portabilidade/relatorio_202501.csv.gz

# Importar plano de numeração (NSAPN)
(teletools) $ abr_loader load-nsapn /dados/numeracao/STFC_202501.zip

# Testar conexão com banco de dados
(teletools) $ abr_loader test-connection
```

> **Documentação completa:** [docs/abr_loader.md](docs/abr_loader.md)

<!-- REFERENCES -->

## Fontes de Dados

Os arquivos de dados da ABR Telecom utilizados por esta biblioteca devem ser baixados dos sistemas oficiais:

### Sistema PIP - Portal de Informações da Portabilidade

- **Acesso:** Restrito a prestadoras de telecomunicações e servidores da Anatel
- **Conteúdo:** Relatórios de bilhetes de portabilidade concluídos
- **Formato:** CSV comprimido (*.csv.gz)
- **Uso:** Comando `abr_loader load-pip`

### Sistema NSAPN - Novo Sistema de Administração dos Planos de Numeração

- **Acesso:** Público via [Portal EASI ABR Telecom](https://easi.abrtelecom.com.br/nsapn/#/public/files)
- **Conteúdo:** Planos de numeração por tipo de serviço
- **Formato:** CSV comprimido (*.zip)
- **Uso:** Comando `abr_loader load-nsapn`

**Tipos de serviços disponíveis no NSAPN:**

| Serviço | Descrição | URL de Download |
|---------|-----------|-----------------|
| CNG | Códigos Não Geográficos (0800, 0300, etc.) | [Download CNG](https://easi.abrtelecom.com.br/nsapn/#/public/files/download/cng) |
| SME | Serviço Móvel Especializado | [Download SME](https://easi.abrtelecom.com.br/nsapn/#/public/files/download/sme) |
| SMP | Serviço Móvel Pessoal | [Download SMP](https://easi.abrtelecom.com.br/nsapn/#/public/files/download/smp) |
| STFC | Serviço Telefônico Fixo Comutado | [Download STFC](https://easi.abrtelecom.com.br/nsapn/#/public/files/download/stfc) |
| STFC-FATB | STFC Fora da Área de Tarifa Básica | [Download STFC-FATB](https://easi.abrtelecom.com.br/nsapn/#/public/files/download/stfc-fatb) |
| SUP | Serviços de Utilidade Pública | [Download SUP](https://easi.abrtelecom.com.br/nsapn/#/public/files/download/sup) |

> **Importante:** Os arquivos contêm dados oficiais da ANATEL e são atualizados regularmente. Sempre baixe as versões mais recentes para garantir dados precisos.

> **Documentação detalhada:** Para instruções completas sobre extração e importação de dados, consulte [docs/abr_loader.md](docs/abr_loader.md).

## Documentação Adicional

- **[Teletools ABR Loader](docs/abr_loader.md)** - Cliente de importação de dados ABR Telecom (PIP e NSAPN)
- **[Teletools Database API](docs/database.md)** - Biblioteca Python para consulta de dados de telecomunicações
- **[Teletools CDR Stage Database](docs/cdr_stage.md)** - Banco de dados PostgreSQL conteinerizado para análise de CDR

## Referências

* [UV Short Guide](https://www.saaspegasus.com/guides/uv-deep-dive/)
