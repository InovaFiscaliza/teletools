<details>
    <summary>Table of Contents</summary>
    <ol>
        <li><a href="#teletools">Teletools</a></li>
        <li><a href="#bibliotecas-e-ferramentas">Bibliotecas e ferramentas</a></li>
        <li><a href="#instalação">Instalação</a></li>
        <li><a href="#referências">Referências</a></li>
    </ol>
</details>


# <img align="left" src="https://raw.githubusercontent.com/InovaFiscaliza/teletools/0daa0d46077d5164df1f3c62e7061fb821bd4546/images/teletools_logo_53_40.png"> Teletools

<p>
Teletools é um conjunto de bibliotecas e ferramentas de apoio para pré-processamento e análise de arquivos CDR (Detalhes de Registros de Chamadas) de operadoras brasileiras.</p>


## Bibliotecas e ferramentas

| Biblioteca    | Descrição                                                               |
| ------------- | ----------------------------------------------------------------------- |
| cipher        | Biblioteca para criptografar e descriptografar arquivos no formato .gpg |
| database      | Biblioteca para conexão e operações a banco de dados auxiliares de CDR  |
| preprocessing | Biblioteca para limpeza e preparação de dados                           |
| utils         | Biblioteca com ferramentas diversas e comuns                            |

| Ferramenta    | Descrição                                                                                |
| ------------- | ---------------------------------------------------------------------------------------- |
| cipher_cli    | Cliente de linha de comando para criptografar e descriptografar arquivos no formato .gpg |
| abr_loader    | Cliente de linha de comando para importação de dados da ABR Telecom                      |

| Aplicações    | Descrição                                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------------------------- |
| cdrstage      | Conjunto de arquivos de configuração para execução conteinerizada do gerenciador de banco de dados PostgreSQL |


## Instalação

As bibliotecas e ferramentas foram desenvolvidas para serem executadas em um computador Linux, contudo, embora não testado, podem ser executadas em computadores Windows que atendam aos pré-requisitos. 

### Pré-requisitos para instalação:

- Python 3.13+ com gerenciador de pacotes [UV](https://docs.astral.sh/uv/)
- Instância de banco de dados [PostgreSQL customizado](tools/cdrstage/README.md) para pré-processamento e análise de arquivos CDR em execução.
- Variáveis de ambiente ou arquivo `.vev` com informações de conexão ao banco de dados PostgreSQL.
- [GnuPG]((https://www.gnupg.org/download/index.html)) ou [Gpg4win](https://gpg4win.org/download.html)

### Configuração das variáveis de ambiente

Esta biblioteca requer credenciais de conexão com o banco de dados para funcionar. Você precisará configurar variáveis de ambiente contendo tais informações:

| Variável                   | Descrição                                     |
| -------------------------- | --------------------------------------------- |
| `TELETOOLS_DB_HOST`        | Endereço do servidor de banco de dados        |
| `TELETOOLS_DB_PORT`        | Porta de acesso ao servidor de banco de dados |
| `TELETOOLS_DB_NAME`        | Nome do banco de dados                        |
| `TELETOOLS_DB_USER`        | Usuário para autenticação                     | 
| `TELETOOLS_DB_PASSWORD`    | Senha do usuário                              | 

Utilize um dos diferentes métodos a seguir para configurar as variáveis:

1. Usando arquivo .env (método recomendado)

```bash
# Crie o arquivo ~/.teletools.env
$ nano ~/.teletools.env

# Adicione as variáveis no seguinte formato
# (sem aspas, a menos que o valor contenha espaços ou caracteres especiais):
TELETOOLS_DB_HOST=endereco_do_servidor_de_banco_de_dados
TELETOOLS_DB_PORT=porta_do_servidor_de_banco_de_dados
TELETOOLS_DB_NAME=nome_do_banco_de_dados
TELETOOLS_DB_USER=nome_do_usuario_do_banco_de_dados
TELETOOLS_DB_PASSWORD=senha_do_usuario_do_banco_de_dados

# Por segurança, restrinja as permissões do arquivo:
$ chmod 600 ~/.teletools.env
```

2. Exportando no terminal (sessão temporária)

```bash
# Se você precisa das variáveis apenas para a sessão atual do terminal, use o comando export:
$ export TELETOOLS_DB_HOST="endereco_do_servidor_de_banco_de_dados"
$ export TELETOOLS_DB_PORT="porta_do_servidor_de_banco_de_dados"
$ export TELETOOLS_DB_NAME="nome_do_banco_de_dados"
$ export TELETOOLS_DB_USER="nome_do_usuario_do_banco_de_dados"
$ export TELETOOLS_DB_PASSWORD="senha_do_usuario_do_banco_de_dados"
```
Observação: Estas variáveis estarão disponíveis apenas enquanto o terminal estiver aberto. Ao fechar, será necessário exportá-las novamente.

3. Configuração permanente no perfil do usuário

```bash
# Abra o arquivo ~/.bashrc
$ nano ~/.bashrc

# Adicione as linhas export ao final do arquivo:
$ export TELETOOLS_DB_HOST="endereco_do_servidor_de_banco_de_dados"
$ export TELETOOLS_DB_PORT="porta_do_servidor_de_banco_de_dados"
$ export TELETOOLS_DB_NAME="nome_do_banco_de_dados"
$ export TELETOOLS_DB_USER="nome_do_usuario_do_banco_de_dados"
$ export TELETOOLS_DB_PASSWORD="senha_do_usuario_do_banco_de_dados"

# Para aplicar as mudanças imediatamente na sessão atual sem precisar fechar e reabrir o terminal, execute:
$ source ~/.bashrc
```

### Bibliotecas para desenvolvimento

```bash
# Adicione teletools ao projeto em desenvolvimento
$ uv add teletools
```
### Ferramentas de linha de comando

```bash
# Crie um ambiente virtual uv
$ uv venv ~/teletools --python 3.13

# Ative o ambiente
$ source ~/teletools/bin/activate

# Instale o teletools
(teletools) $ uv pip install teletools
```
## Uso básico

### Cliente de criptografia

```bash
# Ative o ambiente teletools
$ source ~/teletools

# Execute o cliente cipher_cli
(teletools) $ cipher_cli --help

 Usage: cipher_cli [OPTIONS] COMMAND [ARGS]...

 File encryption and decryption CLI tool using RSA keys.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ encrypt   Encrypt files using RSA public key.                                │
│ decrypt   Decrypt files using RSA private key.                               │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### Cliente de importação de arquivos da ABR Telecom

```bash
# Ative o ambiente teletools
$ source ~/teletools

# Execute o cliente abr_loader
(teletools) $ abr_loader --help

 Usage: abr_loader [OPTIONS] COMMAND [ARGS]...

 ABR Database Loader - Import Brazilian telecom portability and numbering plan
 data.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ load-pip          Import ABR portability data into PostgreSQL database.      │
│ load-nsapn        Import ABR numbering plan data into PostgreSQL database.   │
│ test-connection   Test database connection and validate configuration.       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

<!-- REFERENCES -->

## Fontes de Dados

Os arquivos de dados da ABR Telecom utilizados por esta biblioteca devem ser baixados dos sistemas PIP, Portal de Informações da Portabilidade e NSAPN, Novo Sistema de Administração dos Planos de Numeração.

- Os arquivos de portabilidade devem ser extraídos do sistema PIP, de acesso restrito a prestadoras de telecomunicações e servidores da Anatel. 
- Os arquivos do NSAPN devem ser obtidos na área de download público do site da [Entidade Administradora do Sistema Informatizado](https://easi.abrtelecom.com.br/nsapn/#/public/files)
- Podem ser importados os arquivos de numeração dos serviços:
  - Códigos não geográficos (CNG);
  - Serviço Móvel Especializado (SME);
  - Serviço Móvel Pessoal (SMP);
  - Serviço Telefônico Fixo Comutado (STFC);
  - Serviço Telefônico Fixo Comutado, Fora da ATB (STFC-FATB); e
  - Serviços de Utilidade Pública (SUP).

> **Importante**: Os arquivos do NSAPN contêm dados oficiais de numeração de telecomunicações brasileiras e são atualizados regularmente pela ANATEL.

## Referências

* [UV Short Guide](https://www.saaspegasus.com/guides/uv-deep-dive/)
