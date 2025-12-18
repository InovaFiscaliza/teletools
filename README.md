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

## Documentação Adicional

- **[Teletools CDR Stage Database](docs/cdr_stage.md)** - Banco de dados PostgreSQL conteinerizado para análise de CDR
- **[Teletools ABR Loader](docs/abr_loader.md)** - Cliente de importação de dados ABR Telecom (PIP e NSAPN)
- **[Teletools Database API](docs/database.md)** - Biblioteca Python para consulta de dados de telecomunicações


## Referências

* [UV Short Guide](https://www.saaspegasus.com/guides/uv-deep-dive/)
