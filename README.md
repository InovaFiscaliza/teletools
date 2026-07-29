# <img align="left" src="https://raw.githubusercontent.com/InovaFiscaliza/teletools/0daa0d46077d5164df1f3c62e7061fb821bd4546/images/teletools_logo_53_40.png"> Teletools

![Status](https://img.shields.io/badge/status-descontinuado%20%2F%20arquivado-red)
![Sucessor](https://img.shields.io/badge/sucessor-teleutils-blue)

> **Projeto oficialmente descontinuado e arquivado.** O `teletools` foi um protótipo/prova de conceito e **não receberá mais atualizações, correções de bugs ou novas funcionalidades**. A solução foi substituída por uma reescrita completa no pacote **`teleutils`**. A documentação abaixo registra o estado final congelado do protótipo e é mantida estritamente para **estudo, consulta técnica, auditoria e aprendizado**.

## Sumário

[Status do Projeto e Migracao](#status-do-projeto-e-migracao)

[Visao Geral](#visao-geral)

<details>
<summary><a href="#arquitetura-do-prototipo">Arquitetura do Prototipo</a></summary>

- [Componentes principais](#componentes-principais)
- [Fluxo de execucao](#fluxo-de-execucao)
- [Estrutura final do projeto](#estrutura-final-do-projeto)
</details>

<details>
<summary><a href="#referencia-da-api-congelada">Referencia da API Congelada</a></summary>

- [Pacote raiz](#pacote-raiz)
- [Modulo teletools.preprocessing](#modulo-teletoolspreprocessing)
- [Modulo teletools.cipher](#modulo-teletoolscipher)
- [Modulo teletools.database](#modulo-teletoolsdatabase)
- [Modulo teletools.utils](#modulo-teletoolsutils)
- [Interfaces de linha de comando](#interfaces-de-linha-de-comando)
</details>

<details>
<summary><a href="#engenharia-de-dados-e-banco">Engenharia de Dados e Banco</a></summary>

- [Fontes de dados ABR Telecom](#fontes-de-dados-abr-telecom)
- [Schemas e tabelas principais](#schemas-e-tabelas-principais)
- [Estrategias de performance](#estrategias-de-performance)
</details>

<details>
<summary><a href="#historico-consolidado-da-branch-principal">Historico Consolidado da Branch Principal</a></summary>

- [Linha de versoes e tags](#linha-de-versoes-e-tags)
- [Pull Requests e merges identificados](#pull-requests-e-merges-identificados)
- [Evolucao funcional observada](#evolucao-funcional-observada)
</details>

[Configuracao e Dependencias](#configuracao-e-dependencias)

[Como Instalar e Executar o Prototipo (Somente Referencia)](#como-instalar-e-executar-o-prototipo-somente-referencia)

[Limitacoes Conhecidas](#limitacoes-conhecidas)

[Substituicao pelo teleutils](#substituicao-pelo-teleutils)

[Licenca](#licenca)

## Status do Projeto e Migracao

Este repositório está congelado no estado final da branch principal (`main`), com tag `v1.0.1`.

Resumo do status:
- Repositório descontinuado e arquivado.
- Sem manutenção ativa.
- Sem compromisso de compatibilidade futura.
- Sucessor oficial: `teleutils`.

## Visao Geral

`teletools` foi concebido para apoiar rotinas de pré-processamento e análise de dados de telecomunicações, especialmente CDRs (Call Detail Records), com foco em:
- Normalização de números telefônicos brasileiros.
- Criptografia/descriptografia de arquivos com GPG.
- Carga e consulta de dados ABR Telecom em PostgreSQL.

No estado congelado, o pacote combina biblioteca Python e CLIs:
- `teletools.preprocessing`
- `teletools.cipher`
- `teletools.database`
- `teletools.utils`
- `cipher_cli` e `abr_loader` (pontos de entrada em scripts)

## Arquitetura do Prototipo

### Componentes principais

| Componente | Responsabilidade | Arquivo/modulo de referencia |
|---|---|---|
| Camada de normalização | Validação/normalização de números (ANATEL + E.164) | `teletools.preprocessing._number_format` |
| Camada de criptografia | Criptografia/descriptografia de arquivo/pasta com GPG | `teletools.cipher._file_cipher` |
| Camada de ingestão ABR | Importação de PIP e NSAPN em banco | `teletools.database._abr_portabilidade`, `teletools.database._abr_numeracao` |
| Camada de consulta | Resolução de operadora com designação + portabilidade | `teletools.database.abr_database` |
| Infra e utilitários | Configuração de conexão, operações SQL e logger | `teletools.database._database_config`, `teletools.utils` |
| Interfaces CLI | Operação por terminal para cifragem e carga | `teletools.cipher.cipher_cli`, `teletools.database.abr_loader` |

### Fluxo de execucao

1. Ingestão:
    `abr_loader load-pip` e/ou `abr_loader load-nsapn` importam dados ABR para tabelas de importação e atualizam tabelas finais.
2. Consulta:
    `query_numbers_carriers` carrega números em staging (`entrada.teletools_numbers_to_query`) e resolve operadora considerando histórico de portabilidade até data de referência.
3. Pré-processamento auxiliar:
    `normalize_number` e `normalize_number_pair` padronizam entradas de números.
4. Segurança de arquivos:
    `cipher_cli encrypt/decrypt` ou funções do módulo `cipher` para arquivos sensíveis.

### Estrutura final do projeto

Pastas e artefatos relevantes no congelamento:
- `src/teletools/`: código-fonte principal.
- `docs/`: documentação das APIs e CLIs.
- `tools/cdrstage/`: infraestrutura Docker para banco de apoio CDR Stage.
- `pyproject.toml`: metadados, dependências e scripts.
- `tests/`: suíte mínima com arquivo de exemplo.

## Referencia da API Congelada

Organização inspirada em documentação modular: componentes, funções públicas e finalidade operacional.

### Pacote raiz

Importações públicas:
- `teletools.cipher`
- `teletools.database`
- `teletools.preprocessing`
- `teletools.utils`

### Modulo teletools.preprocessing

Objetivo: normalização de números telefônicos brasileiros com regras ANATEL e padrões E.164.

Funções públicas:

| Função | Assinatura congelada | Retorno | Descrição |
|---|---|---|---|
| `normalize_number` | `normalize_number(subscriber_number, national_destination_code="")` | `tuple[str, bool]` | Normaliza número único e informa validade. |
| `normalize_number_pair` | `normalize_number_pair(number_a, number_b, national_destination_code="")` | `tuple[str, bool, str, bool]` | Normaliza par de números com inferência contextual de DDD. |

Pontos técnicos:
- Uso de regex extensas para cobertura SMP, STFC, SME, SUP e CNG.
- Remoção de prefixos de chamada (`90`, `9090`, `00`, `0`).
- Retorno do valor original quando inválido.

### Modulo teletools.cipher

Objetivo: criptografia e descriptografia de arquivos/pastas via GPG.

Funções públicas:

| Função | Assinatura congelada | Retorno | Descrição |
|---|---|---|---|
| `encrypt_file_or_folder` | `encrypt_file_or_folder(public_key_file, input_file_or_folder, output_folder=None)` | `None` | Criptografa arquivo único ou todos os arquivos de uma pasta. |
| `decrypt_file_or_folder` | `decrypt_file_or_folder(private_key_file, input_file_or_folder, output_folder=None)` | `None` | Descriptografa arquivo `.gpg` único ou pasta com `.gpg`. |

Pontos técnicos:
- Integração com `python-gnupg`.
- Criação automática de diretório de saída.
- Execução não-recursiva em diretórios.
- Tratamento de erro para chaves/caminhos inexistentes.

### Modulo teletools.database

Objetivo: consulta de operadora por número considerando designação e portabilidade histórica.

Função pública:

| Função | Assinatura congelada | Retorno | Descrição |
|---|---|---|---|
| `query_numbers_carriers` | `query_numbers_carriers(numbers_to_query, reference_date=None)` | `dict` com `column_names` e `results` | Resolve operadora e indicadores de portabilidade/designação para lote de números. |

Pontos técnicos:
- Aceita data de referência em múltiplos formatos (`YYYY-MM-DD`, `DD/MM/YYYY`, `YYYYMMDD`).
- Prepara DataFrame intermediário com `cn` e `prefixo` para otimizar consulta.
- Usa tabela temporária de apoio persistente por execução e `COPY` para inserção rápida.
- Processa tudo em conexão única para reduzir risco de lock em DDL/DML.

### Modulo teletools.utils

Objetivo: utilidades transversais para inspeção de dados e logging.

Funções públicas:

| Função | Assinatura congelada | Retorno | Descrição |
|---|---|---|---|
| `inspect_file` | `inspect_file(file, nrows=5, encoding="utf8")` | `None` | Exibe primeiras linhas de arquivos texto, `.gz` e `.zip`. |
| `setup_logger` | `setup_logger(log_file="log.log")` | `logging.Logger` | Configura logger com saída em console e arquivo. |

### Interfaces de linha de comando

Scripts configurados em `pyproject.toml`:

| Comando | Ponto de entrada | Finalidade |
|---|---|---|
| `cipher_cli` | `teletools.cipher.cipher_cli:main` | Criptografar/descriptografar arquivos e pastas com chaves GPG. |
| `abr_loader` | `teletools.database.abr_loader:main` | Importar dados ABR (`load-pip`, `load-nsapn`) e testar conexão (`test-connection`). |

## Engenharia de Dados e Banco

### Fontes de dados ABR Telecom

O protótipo foi desenhado para duas fontes principais:
- PIP (histórico de bilhetes de portabilidade concluídos).
- NSAPN (faixas de numeração pública por serviço).

Documentação complementar:
- `docs/abr_loader.md`
- `docs/database_api_index.md`
- `docs/cdr_stage.md`

### Schemas e tabelas principais

No estado final do código, os schemas e tabelas centrais incluem:

| Categoria | Nome |
|---|---|
| Schema de importação | `entrada` |
| Schema alvo | `public` |
| Histórico de portabilidade | `public.teletools_tb_portabilidade_historico` |
| Prestadoras | `public.teletools_tb_prestadoras` |
| Numeração consolidada | `public.teletools_tb_numeracao` |
| Tabela de staging de consulta | `entrada.teletools_numbers_to_query` |

### Estrategias de performance

Práticas implementadas no protótipo:
- Processamento em chunks (`CHUNK_SIZE = 100000`).
- Inserção em massa com PostgreSQL `COPY`.
- Conversões de tipos para reduzir uso de memória (`category`, `Int16`, `Int32`, `int8`).
- Criação/recriação controlada de tabelas de staging.
- Consulta com `LATERAL JOIN` para resolução de designação e portabilidade.

## Historico Consolidado da Branch Principal

### Linha de versoes e tags

Tags identificadas no repositório:
- `v0.0.1`
- `v1.0.0`
- `v1.0.1` (estado final congelado)

### Pull Requests e merges identificados

Merges registrados na branch principal:
- `Merge pull request #1 from InovaFiscaliza/database`
- `Merge pull request #2 from InovaFiscaliza/database`
- `Merge pull request #3 from InovaFiscaliza/dev`
- `Merge pull request #6 from InovaFiscaliza/dev`
- `Merge pull request #7 from InovaFiscaliza/dev`

Observação: o histórico também contém merge commit de sincronização (`chore: Merge remote changes`).

### Evolucao funcional observada

Tendências principais até o congelamento:
- Forte evolução do módulo `database` (ingestão, performance, staging e query final).
- Consolidação da API pública de consulta em `query_numbers_carriers`.
- Maturação das CLIs (`abr_loader` e `cipher_cli`) com documentação de uso.
- Ampliação da documentação modular em `docs/`.
- Bumps de versão e estabilização final em `v1.0.1`.

## Configuracao e Dependencias

Metadados do pacote (estado final):
- Nome: `teletools`
- Versão: `1.0.1`
- Backend de build: `hatchling`
- Python requerido: `>=3.11`

Dependências declaradas:
- `duckdb`
- `pandas`
- `psycopg2-binary`
- `python-dotenv`
- `python-gnupg`
- `sqlalchemy`
- `tqdm`
- `typer`

Observação de contexto histórico:
- Parte da documentação operacional cita Python 3.13+ e fluxo com `uv`.
- O metadado de empacotamento publicado em `pyproject.toml` mantém compatibilidade formal em `>=3.11`.

## Como Instalar e Executar o Prototipo (Somente Referencia)

> Esta seção é mantida apenas para reprodução histórica e investigação técnica.

Instalação do pacote:

```bash
uv add teletools
```

Ou em ambiente virtual:

```bash
uv venv ~/teletools --python=3.13
source ~/teletools/bin/activate
uv pip install teletools
```

Comandos principais:

```bash
cipher_cli --help
abr_loader --help
abr_loader test-connection
```

Documentação complementar local:
- `docs/cipher_api_index.md`
- `docs/database_api_index.md`
- `docs/preprocessing_api_index.md`
- `docs/utils_api_index.md`
- `docs/cipher_cli.md`
- `docs/abr_loader.md`
- `docs/cdr_stage.md`

## Limitacoes Conhecidas

Como protótipo arquivado, este repositório apresenta limitações práticas:
- Não há roadmap ativo de correções.
- Suíte de testes mínima para o escopo atual.
- Possíveis inconsistências entre documentação histórica e ambientes modernos.
- Dependência de contexto operacional específico (fontes ABR, banco PostgreSQL e chaves GPG).

## Substituicao pelo teleutils

O `teletools` foi substituído por um novo pacote, **`teleutils`**, desenvolvido do zero para absorver as reestruturações arquiteturais necessárias.

Diretriz de uso:
- Novos desenvolvimentos: usar `teleutils`.
- Integrações legadas: consultar este README apenas como base histórica.
- Auditoria e aprendizado: utilizar a referência congelada desta documentação e os arquivos em `docs/`.

## Licenca

Este repositório permanece sob a licença definida no arquivo `LICENSE`, porém em estado **descontinuado/arquivado**.
