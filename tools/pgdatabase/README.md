# Teletools database

Teletools database é um conjunto de arquivos para a construção de uma solução conteinerizada para execução de um banco de dados PostgreSQL customizado para o pré-processamento de dados para tratamento de arquivos CDR (Detalhes de Registros de Chamadas) de operadoras brasileiras. 

## Sobre

Teletools database constroi uma imagem customizada de um banco de dados PostgreSQL a partir da [imagem oficial Docker](https://hub.docker.com/_/postgres) com as extensões requeridas para processamento dos dados extraídos de diversas fontes.

Teletools database contém ainda uma versão web da ferramenta de adminstração para PostgreSQL [pgAdmin 4](https://hub.docker.com/r/dpage/pgadmin4).

## 🚀 Configuração

### Pré-requisitos

- docker: versão 28 ou superior

### Configuração do Ambiente

Clone o repositório e construa a imagem customizada:

```bash
# Clonar o repositório
git clone https://github.com/InovaFiscaliza/teletools
cd teletools/pgdatabase

# Construir a imagem customizada
docker build -t postgrescdr .
```

Crie os usuários para os serviços
```bash
# Criar o grupo postgres com GID 999
sudo groupadd -g 999 postgres
# Criar o usuário postgres com UID 999
sudo useradd -u 999 postgres -g postgres

# Criar o grupo pgadmin com GID 5050
sudo groupadd -g 5050 pgadmin
# Criar o usuário pgadmin com UID 999
sudo useradd -u 5050 pgadmin -g pgadmin
```
⚠️ **Atenção** os usuários e grupos devem ser criados com os UID e GID especificados, caso contrário os serviços dos conteineres não persistirão os dados.

Crie dos diretórios de dados e ajuste as permissões
```bash
# Criar os diretórios
mkdir -p /data/postgresql/data
mkdir -p /data/postgresql/pgadmin

# Configurar proprietário e permissões
sudo chown -R postgres /data/postgresql/data
sudo chown -R pgadmin /data/postgresql/pgadmin
sudo chmod -R g+s /data/postgresql/data
sudo chmod -R g+s /data/postgresql/pgadmin
```
Crie o arquivo de variáveis de ambiente (`.env`)
```
POSTGRES_USER=<postgres_admin_username>
POSTGRES_PASSWORD=<postgres_admin_username>
POSTGRES_DB=<postgres_default_database>
PGADMIN_DEFAULT_EMAIL=<pgadmin_admin_user_email>
PGADMIN_DEFAULT_PASSWORD=<pgadmin_admin_user_password>
PGADMIN_LISTEN_ADDRESS=0.0.0.0
```
| Variável                   | Descrição                                                       |
| -------------------------- | --------------------------------------------------------------- |
| `POSTGRES_USER`            | Cria o superusuário com o nome especificado                     |
| `POSTGRES_PASSWORD`        | Define a senha do superusuário do PostgreSQL                    |
| `POSTGRES_DB`              | Cria o banco de dados padrão com o nome especificado            |
| `PGADMIN_DEFAULT_EMAIL`    | Cria a conta inicial de administrador com o e-mail especificado |
| `PGADMIN_DEFAULT_PASSWORD` | Cria a senha inicial do administrador                           |
| `PGADMIN_LISTEN_ADDRESS  ` | Especifica o endereço que o serviços ficará escutando           |

Execute o docker compose
```bash
# Executar docker compose
docker compose up -d
```
### Acesso ao PostgreSQL

Após a configuração o banco de dados PostgreSQL pode ser acessado através do pgAdmin (web ou desktop) ou de outra ferramenta para gerenciamento de banco de dados.

Para acessar através do pgAdmin web acesse o endereço http://<host_de_instalação>:5050 e utilize o e-mail e senha do pgAdmin informados no arquivo de configuração (`PGADMIN_DEFAULT_EMAIL` e `PGADMIN_DEFAULT_PASSWORD`)

Configure a conexão ao servidor PostgreSQL com os seguintes parâmetros:

| Parâmetro            | Valor                |
| -------------------- | ---------------------|
| Host name/address    | <host_de_instalação> |
| Port                 | 5432                 |
| Maintenance database | `POSTGRES_DB`        |
| Username             | `POSTGRES_USER`      |
| Password             | `POSTGRES_PASSWORD`  |


![pgAdmin Register - Server](../images/postgre_connect.png "pgAdmin Register - Server")


### Instalação das extensões

Conecte no banco de dados e execute o SQL
```sql
-- Instalar extensões
CREATE EXTENSION amcheck;
CREATE EXTENSION btree_gin;
CREATE EXTENSION file_fdw;
CREATE EXTENSION fuzzystrmatch;
CREATE EXTENSION ogr_fdw;
CREATE EXTENSION pg_stat_statements;
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_raster;
CREATE EXTENSION system_stats;
CREATE EXTENSION tablefunc;
CREATE EXTENSION unaccent;
```
### Configuração dos parâmetros de performance

Edite o arquivo de configuração do PostgreSQL 
```bash
sudo su - postgres
cd /data/postresql/data
cp postgresql.conf postgresql.conf.bkp.$(date +%Y%m%d_%H%M%S)
nano postgresql.conf
```
Verifique os parâmetros listados e os ajuste, se necessário.

|Parâmetro                      |Descrição                                                                                         |Valor padrão|Valor ajustado|
|-------------------------------|--------------------------------------------------------------------------------------------------|------------|--------------|
|autovacuum                     |Starts the autovacuum subprocess.                                                                 |on          |on            |
|autovacuum_vacuum_cost_limit   |Vacuum cost amount available before napping, for                                                  |-1          |2000          |
|autovacuum_max_workers         |Sets the maximum number of simultaneously running autovacuum worker processes.                    |3           |6             |
|autovacuum_vacuum_scale_factor |Number of tuple updates or deletes prior to vacuum as a fraction of reltuples.                    |0.2         |0.2           |
|checkpoint_timeout             |Sets the maximum time between automatic WAL checkpoints.                                          |300         |1800s         |
|deadlock_timeout               |Sets the time to wait on a lock before checking for deadlock.                                     |1000        |2s            |
|default_statistics_target      |Sets the default statistics target.                                                               |100         |1000          |
|effective_cache_size           |Sets the planner's assumption about the total size of the data caches.                            |524288      |6GB           |
|effective_io_concurrency       |Number of simultaneous requests that can be handled efficiently by the disk subsystem.            |16          |200           |
|geqo_threshold                 |Sets the threshold of FROM items beyond which GEQO is used.                                       |12          |16            |
|huge_pages                     |Use of huge pages on Linux or Windows.                                                            |try         |try           |
|jit                            |Allow JIT compilation.                                                                            |on          |off           |
|listen_addresses               |Sets the host name or IP address(es) to listen to.                                                |*           |*             |
|log_min_duration_statement     |Sets the minimum execution time above which all statements will be logged.                        |-1          |10000         |
|maintenance_work_mem           |Sets the maximum memory to be used for maintenance operations.                                    |65536       |4GB           |
|max_connections                |Sets the maximum number of concurrent connections.                                                |100         |100           |
|max_locks_per_transaction      |Sets the maximum number of locks per transaction.                                                 |64          |256           |
|max_parallel_workers           |Sets the maximum number of parallel workers that can be active at one time.                       |8           |16            |
|max_parallel_workers_per_gather|Sets the maximum number of parallel processes per executor node.                                  |2           |8             |
|max_wal_size                   |Sets the WAL size that triggers a checkpoint.                                                     |1024        |64GB          |
|min_wal_size                   |Sets the minimum size to shrink the WAL to.                                                       |80          |2GB           |
|parallel_setup_cost            |Sets the planner's estimate of the cost of starting up worker processes for parallel query.       |1000        |200.0         |
|parallel_tuple_cost            |Sets the planner's estimate of the cost of passing each tuple (row) from worker to leader backend.|0.1         |0.1           |
|random_page_cost               |Sets the planner's estimate of the cost of a nonsequentially fetched disk page.                   |4           |1.1           |
|shared_buffers                 |Sets the number of shared memory buffers used by the server.                                      |2097152     |20GB          |
|synchronous_commit             |Sets the current transaction's synchronization level.                                             |on          |local         |
|temp_buffers                   |Sets the maximum number of temporary buffers used by each session.                                |1024        |4096          |
|wal_level                      |Sets the level of information written to the WAL.                                                 |replica     |minimal       |
|work_mem                       |Sets the maximum memory to be used for query workspaces.                                          |4096        |2GB           |

### Configuração do banco de dado CDR

#### Criação dos grupos e usuários

Crie o grupo de usuários
```sql
-- Criar grupo de usuários
CREATE ROLE cdr_database_users WITH
	NOLOGIN
	NOSUPERUSER
	NOCREATEDB
	NOCREATEROLE
	INHERIT
	NOREPLICATION
	NOBYPASSRLS
	CONNECTION LIMIT -1;
COMMENT ON ROLE cdr_database_users IS 'Grupo de usuários do banco de dados CDR';
```
Crie os usuários
```sql
-- Criar usuários
DO $$
DECLARE
    user_name TEXT := '<user_name>';
    user_password TEXT := '<user_password>';
    user_full_name TEXT := '<user_full_name>';
BEGIN
    -- Criar a role
    EXECUTE format('CREATE ROLE %I WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION NOBYPASSRLS CONNECTION LIMIT -1 PASSWORD %L', 
                   user_name, user_password);
    
    -- Conceder privilégios
    EXECUTE format('GRANT cdr_database_users TO %I', user_name);
    
    -- Adicionar comentário
    EXECUTE format('COMMENT ON ROLE %I IS %L', user_name, user_full_name);
END $$;
```

### Criação dos esquemas do banco de dados CDR

Ajuste as permissões do banco de dados
```sql
-- Definir a lista de esquemas e seus comentários
DO $$
DECLARE
    schema_record RECORD;
    schemas_list TEXT[][] := ARRAY[
        ['entrada', 'Esquema para armazenamento dos dados de entrada.'],
        ['mapas', 'Esquema para armazenamento de mapas.'],
        ['public', 'Esquema público padrão do PostgreSQL.']
        -- Adicione mais esquemas aqui conforme necessário
    ];
BEGIN
    -- Iterar sobre cada esquema na lista
    FOR i IN 1..array_length(schemas_list, 1) LOOP
        DECLARE
            schema_name TEXT := schemas_list[i][1];
            schema_comment TEXT := schemas_list[i][2];
        BEGIN
            -- Criar o esquema
            EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I AUTHORIZATION pg_database_owner', schema_name);
            RAISE NOTICE 'Esquema % criado', schema_name;
            
            -- Adicionar comentário ao esquema
            EXECUTE format('COMMENT ON SCHEMA %I IS %L', schema_name, schema_comment);
            
            -- Conceder permissões ao esquema
            EXECUTE format('GRANT USAGE ON SCHEMA %I TO PUBLIC', schema_name);
            EXECUTE format('GRANT ALL ON SCHEMA %I TO cdr_database_users', schema_name);

            -- Conceder permissões para objetos no esquema
            EXECUTE format('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I TO cdr_database_users', schema_name);
            EXECUTE format('GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %I TO cdr_database_users', schema_name);
            EXECUTE format('GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA %I TO cdr_database_users', schema_name);

            -- Alterar permissões padrão para objetos futuros no esquema
            EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA %I GRANT ALL ON TABLES TO cdr_database_users', schema_name);
            EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA %I GRANT ALL ON SEQUENCES TO cdr_database_users', schema_name);
            EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA %I GRANT EXECUTE ON FUNCTIONS TO cdr_database_users', schema_name);
            EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA %I GRANT USAGE ON TYPES TO cdr_database_users', schema_name);
            
            RAISE NOTICE 'Permissões configuradas para o esquema %', schema_name;
        END;
    END LOOP;
END $$;
```

Opcionalmente, baixe, altere e execute o [script](sql/create_schemas.sql).


---

## 👤 Autores

**Ronaldo S.A. Batista**
- Email: <eu@ronaldo.tech>

**Maxwel de Souza Freitas**
- Email: maxwel@maxwelfreitas.com.br

**Carlos Cesar Lanzoni**
- Email: carlos.cesar@anatel.gov.br
---

**Versão:** 0.1.0
**Última atualização:** 2025-10-31
**Status:** Em desenvolvimento ativo