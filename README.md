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
- [GnuPG]((https://www.gnupg.org/download/index.html)) ou [Gpg4win](https://gpg4win.org/download.html)

### Bibliotecas para desenvolvimento

```bash
# Adicione teletools ao projeto em desenvolvimento
$ uv add teletools
```
### Ferramentas de linha de comando

```bash
# Crie um ambiente virtual uv
$ uv venv /opt/cdr/tools/teletools --python 3.13

# Ative o ambiente
$ source /opt/cdr/tools/teletools/bin/activate

# Instale o teletools
(teletools) $ uv pip install teletools
Using Python 3.13.3 environment at: teletools
Resolved 18 packages in 1.07s
Installed 1 package in 41ms
 + teletools==0.1.0
```

<!-- REFERENCES -->

## Fontes de Dados

Todos os arquivos de dados da ABR Telecom utilizados por esta biblioteca devem ser baixados do portal oficial:

| Tipo de Serviço | Descrição | URL de Download |
| --- | --- | --- |
| **CNG** | Código Nacional de Gratuidade | https://easi.abrtelecom.com.br/nsapn/#/public/files/download/cng |
| **SME** | Serviço Móvel Especializado | https://easi.abrtelecom.com.br/nsapn/#/public/files/download/sme |
| **SMP** | Serviço Móvel Pessoal | https://easi.abrtelecom.com.br/nsapn/#/public/files/download/smp |
| **STFC** | Serviço Telefônico Fixo Comutado | https://easi.abrtelecom.com.br/nsapn/#/public/files/download/stfc |
| **STFC-FATB** | STFC fora da ATB | https://easi.abrtelecom.com.br/nsapn/#/public/files/download/stfc-fatb |

> **Importante**: Estes arquivos contêm dados oficiais de numeração de telecomunicações brasileiras e são atualizados regularmente pela ANATEL.

## Referências

* [UV Short Guide](https://www.saaspegasus.com/guides/uv-deep-dive/)
