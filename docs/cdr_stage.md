> **[← Voltar para Teletools](../README.md)**

<details>
    <summary>Sumário</summary>
    <ol>
        <li><a href="#teletools-cdr-stage-database">Teletools CDR Stage Database</a></li>
        <li><a href="#visão-geral">Visão Geral</a></li>
        <li><a href="#pré-requisitos">Pré-requisitos</a></li>
        <li><a href="#instalação-e-configuração">Instalação e Configuração</a></li>
        <li><a href="#acesso-ao-banco-de-dados">Acesso ao Banco de Dados</a></li>
        <li><a href="#configuração-do-banco-de-dados-cdr">Configuração do Banco de Dados CDR</a></li>
        <li><a href="#contribuindo">Contribuindo</a></li>
        <li><a href="#licença">Licença</a></li>
        <li><a href="#contato-e-suporte">Contato e Suporte</a></li>
        <li><a href="#-autores">👤 Autores</a></li>
    </ol>
</details>

# Teletools CDR Stage Database

Teletools CDR Stage Database é um banco de dados PostgreSQL conteinerizado e customizado para pré-processamento e análise de dados de CDR (Call Detail Records - Detalhes de Registros de Chamadas) de operadoras de telecomunicações brasileiras.

## Visão Geral

Teletools CDR Stage Database fornece uma infraestrutura completa e otimizada para análise de dados de telecomunicações, construída sobre PostgreSQL com extensões especializadas. O ambiente é totalmente conteinerizado usando Docker, facilitando implantação e manutenção.

A solução é baseada na [Imagem Oficial Docker do PostgreSQL](https://hub.docker.com/_/postgres) e inclui [pgAdmin 4](https://hub.docker.com/r/dpage/pgadmin4) para administração web do banco de dados.

### Características Principais

- ✅ **Ambiente Conteinerizado**: Deploy simplificado com Docker Compose
- ✅ **Extensões Especializadas**: PostGIS, pg_stat_statements, fuzzystrmatch e outras
- ✅ **Alta Performance**: Configurações otimizadas para processamento de grandes volumes
- ✅ **Administração Web**: Interface pgAdmin 4 integrada
- ✅ **Controle de Acesso**: Sistema de roles com permissões granulares
- ✅ **Persistência de Dados**: Volumes configuráveis para dados e backups

## Pré-requisitos

- Docker versão 28 ou superior
- Sistema operacional Linux (testado em RHEL9)
- Permissões de administrador (sudo) para criação de usuários e diretórios

## Instalação e Configuração

### Clonagem do Repositório e Construção da Imagem Docker customizada

**Clone o repositório e navegue até o diretório:**

```bash
# Clone o repositório
git clone https://github.com/InovaFiscaliza/teletools
cd teletools/tools/cdrstage
```

**Construa a imagem customizada do PostgreSQL:**

```bash
# Construir a imagem com as extensões necessárias
docker build -t postgrescdr .
```

A construção da imagem instalará automaticamente todas as extensões PostgreSQL necessárias para processamento de dados CDR.

### Criação de Usuários e Grupos do Sistema

**Crie os usuários e grupos para os serviços:**

```bash
# Criar grupo e usuário postgres (UID/GID 999)
sudo groupadd -g 999 postgres
sudo useradd -u 999 postgres -g postgres

# Criar grupo e usuário pgadmin (UID/GID 5050)
sudo groupadd -g 5050 pgadmin
sudo useradd -u 5050 pgadmin -g pgadmin
```

⚠️ **Importante**: Os valores de UID e GID devem ser exatamente como especificados. Caso contrário, os containers não conseguirão persistir dados corretamente.

### Criação dos Diretórios de Dados

**Crie os diretórios e configure permissões:**

```bash
# Criar diretórios para dados persistentes
sudo mkdir -p /data/postgresql/data
sudo mkdir -p /data/postgresql/pgadmin

# Configurar proprietários
sudo chown -R postgres:postgres /data/postgresql/data
sudo chown -R pgadmin:pgadmin /data/postgresql/pgadmin

# Configurar permissões com setgid
sudo chmod -R g+s /data/postgresql/data
sudo chmod -R g+s /data/postgresql/pgadmin
```

⚠️ **Personalização**: Se desejar usar diretórios diferentes, edite o arquivo `docker-compose.yaml` antes de prosseguir:

```yaml
# Exemplo: usando /opt/postgresql para armazenamento
services:
  postgres:    
    volumes:
      - /opt/postgresql/data:/var/lib/postgresql/18/docker
  
  pgadmin:
    volumes:
      - /opt/postgresql/pgadmin:/var/lib/pgadmin
```

### Configuração das Variáveis de Ambiente

**Crie o arquivo `.env` no diretório `tools/cdrstage`:**

```bash
# Arquivo: teletools/tools/cdrstage/.env

# Configurações do PostgreSQL
POSTGRES_USER=postgres_admin
POSTGRES_PASSWORD=senha_super_segura
POSTGRES_DB=cdr_database

# Configurações do pgAdmin
PGADMIN_DEFAULT_EMAIL=admin@empresa.com.br
PGADMIN_DEFAULT_PASSWORD=senha_admin_pgadmin
PGADMIN_LISTEN_ADDRESS=0.0.0.0
```

**Descrição das variáveis:**

| Variável                     | Descrição                                                    |
|------------------------------|--------------------------------------------------------------|
| `POSTGRES_USER`              | Nome do superusuário do PostgreSQL                           |
| `POSTGRES_PASSWORD`          | Senha do superusuário do PostgreSQL                          |
| `POSTGRES_DB`                | Nome do banco de dados padrão criado na inicialização        |
| `PGADMIN_DEFAULT_EMAIL`      | E-mail para login inicial no pgAdmin                         |
| `PGADMIN_DEFAULT_PASSWORD`   | Senha para login inicial no pgAdmin                          |
| `PGADMIN_LISTEN_ADDRESS`     | Endereço de escuta do pgAdmin (0.0.0.0 = todas interfaces)  |

### Inicialização dos Containers

**Execute o Docker Compose:**

```bash
# Iniciar os serviços em background
docker compose up -d
```

**Verifique o status dos containers:**

```bash
# Verificar containers em execução
docker compose ps

# Visualizar logs (opcional)
docker compose logs -f
```

Os serviços estarão disponíveis nas seguintes portas:
- **PostgreSQL**: 5432 (padrão)
- **pgAdmin**: 8080 (ou conforme configurado no docker-compose.yaml)

## Acesso ao Banco de Dados

### Acesso via pgAdmin Web

**Acesse o pgAdmin através do navegador:**

```
http://<host_de_instalação>:8080
```

**Credenciais de login:**
- E-mail: valor definido em `PGADMIN_DEFAULT_EMAIL`
- Senha: valor definido em `PGADMIN_DEFAULT_PASSWORD`

### Configuração da Conexão PostgreSQL

**Registre o servidor PostgreSQL no pgAdmin:**

1. No menu principal, clique em **Add New Server**
2. Na aba **General**:
   - Name: `CDR Stage Database` (ou nome de sua preferência)

3. Na aba **Connection**, configure:

| Parâmetro              | Valor                                   |
|------------------------|-----------------------------------------|
| Host name/address      | `<host_de_instalação>` ou `localhost`   |
| Port                   | `5432`                                  |
| Maintenance database   | Valor de `POSTGRES_DB`                  |
| Username               | Valor de `POSTGRES_USER`                |
| Password               | Valor de `POSTGRES_PASSWORD`            |

![pgAdmin Register - Server](https://raw.githubusercontent.com/InovaFiscaliza/teletools/0daa0d46077d5164df1f3c62e7061fb821bd4546/images/postgre_connect.png)

**Teste a conexão** clicando em **Save**. Se as configurações estiverem corretas, o servidor aparecerá no painel lateral do pgAdmin.

## Configuração do Banco de Dados CDR

### Instalação das Extensões PostgreSQL


**Conecte ao banco de dados e execute o seguinte SQL:**

```sql
-- Instalar extensões necessárias para processamento CDR
CREATE EXTENSION IF NOT EXISTS amcheck;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS ogr_fdw;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pgstattuple;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
CREATE EXTENSION IF NOT EXISTS system_stats;
CREATE EXTENSION IF NOT EXISTS tablefunc;
CREATE EXTENSION IF NOT EXISTS unaccent;
```

**Descrição das extensões principais:**

| Extensão                | Descrição                                              |
|-------------------------|--------------------------------------------------------|
| `postgis`               | Suporte a dados geoespaciais e operações GIS          |
| `pg_stat_statements`    | Monitoramento de performance de consultas              |
| `fuzzystrmatch`         | Funções de matching aproximado de strings              |
| `unaccent`              | Remove acentuação de texto                             |
| `file_fdw`              | Acesso a arquivos externos como tabelas                |

### Otimização de Parâmetros de Performance

**Edite o arquivo de configuração do PostgreSQL:**

```bash
# Conectar ao container como usuário postgres
sudo su - postgres
cd /data/postgresql/data

# Criar backup da configuração
cp postgresql.conf postgresql.conf.bkp.$(date +%Y%m%d_%H%M%S)

# Editar configuração
nano postgresql.conf
```

**Parâmetros recomendados para processamento CDR:**

| Parâmetro                       | Valor Padrão | Valor Recomendado | Descrição                                                  |
|---------------------------------|--------------|-------------------|------------------------------------------------------------|
| `shared_buffers`                | 2GB          | 20GB              | Memória compartilhada para cache de dados                  |
| `effective_cache_size`          | 4GB          | 6GB               | Estimativa do cache total disponível                       |
| `maintenance_work_mem`          | 64MB         | 4GB               | Memória para operações de manutenção                       |
| `work_mem`                      | 4MB          | 2GB               | Memória para operações de ordenação                        |
| `max_wal_size`                  | 1GB          | 64GB              | Tamanho máximo do WAL antes de checkpoint                  |
| `min_wal_size`                  | 80MB         | 2GB               | Tamanho mínimo do WAL                                      |
| `checkpoint_timeout`            | 300s         | 1800s             | Tempo máximo entre checkpoints automáticos                 |
| `max_connections`               | 100          | 100               | Número máximo de conexões simultâneas                      |
| `max_parallel_workers`          | 8            | 16                | Máximo de workers paralelos ativos                         |
| `max_parallel_workers_per_gather`| 2           | 8                 | Workers paralelos por executor                             |
| `effective_io_concurrency`      | 16           | 200               | Requisições simultâneas ao subsistema de disco             |
| `random_page_cost`              | 4.0          | 1.1               | Custo de página não sequencial (SSD)                       |
| `default_statistics_target`     | 100          | 1000              | Precisão das estatísticas do planner                       |
| `autovacuum_vacuum_cost_limit`  | -1           | 2000              | Limite de custo do autovacuum                              |
| `autovacuum_max_workers`        | 3            | 6                 | Workers paralelos do autovacuum                            |
| `wal_level`                     | replica      | logical           | Nível de informação no WAL                                 |
| `synchronous_commit`            | on           | local             | Nível de sincronização de commits                          |

⚠️ **Nota**: Ajuste os valores de acordo com os recursos disponíveis no seu servidor. Os valores acima são adequados para servidores com 32GB+ de RAM e armazenamento SSD.

**Reinicie o PostgreSQL após as alterações:**

```bash
# Dentro do container
docker compose restart postgres
```

### Criação de Esquemas, Roles e Permissões
```sql
-- =======================================
-- Script idempotente para criação/atualização de roles e grants
-- =======================================
-- Este script:
-- - Cria roles se não existirem, ou altera atributos se existirem.
-- - Grants são idempotentes (GRANT múltiplas vezes não causa erro).
-- - ALTER DEFAULT PRIVILEGES sobrescreve existentes para o role.
-- - Para SUPERUSER: Altera se necessário.
-- Rode como superusuário (ex.: admin).

-- =======================================
-- Definição dos esquemas e suas descrições
-- =======================================
-- Tabela temporária para armazenar os esquemas
CREATE TEMP TABLE IF NOT EXISTS temp_schemas (
    name TEXT PRIMARY KEY,
    description TEXT
);

-- Limpa e popula a tabela com os esquemas
TRUNCATE temp_schemas;
INSERT INTO temp_schemas (name, description) VALUES
    ('dw', 'Esquema temporário para armazenamento de dados disponíveis no DW_ANATEL'),
    ('entrada', 'Esquema para armazenamento dos dados de entrada.'),
    ('mapas', 'Esquema para armazenamento de mapas.'),
    ('public', 'Esquema público padrão do PostgreSQL.');

-- Criação dos esquemas
DO $$
DECLARE
    schema_rec RECORD;
BEGIN
    FOR schema_rec IN SELECT name, description FROM temp_schemas
    LOOP
        -- Criar esquema se não existir
        IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = schema_rec.name) THEN
            EXECUTE format('CREATE SCHEMA %I', schema_rec.name);
        END IF;
        
        -- Definir comentário no esquema
        EXECUTE format('COMMENT ON SCHEMA %I IS %L', schema_rec.name, schema_rec.description);
    END LOOP;
END $$;

-- =======================================
-- Definição das funções auxiliares
-- =======================================
-- Função auxiliar para verificar se role existe (usada em DO)
CREATE OR REPLACE FUNCTION role_exists(role_name TEXT) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name);
END;
$$ LANGUAGE plpgsql;

-- Função auxiliar para obter lista de nomes de esquemas
CREATE OR REPLACE FUNCTION get_schema_names() RETURNS TEXT[] AS $$
BEGIN
    RETURN ARRAY(SELECT name FROM temp_schemas ORDER BY name);
END;
$$ LANGUAGE plpgsql;

-- =======================================
-- Criação/Atualização dos grupos (roles)
-- =======================================

-- cdr_user_ler
DO $$
BEGIN
    IF NOT role_exists('cdr_user_ler') THEN
        CREATE ROLE cdr_user_ler
           NOLOGIN
           NOSUPERUSER
           NOCREATEDB
           NOCREATEROLE
           NOREPLICATION
           NOBYPASSRLS;
    ELSE
        -- Altera atributos se necessário (ex.: garantir NOSUPERUSER, etc.)
        ALTER ROLE cdr_user_ler NOLOGIN;
        ALTER ROLE cdr_user_ler NOSUPERUSER;
        ALTER ROLE cdr_user_ler NOCREATEDB;
        ALTER ROLE cdr_user_ler NOCREATEROLE;
        ALTER ROLE cdr_user_ler NOREPLICATION;
        ALTER ROLE cdr_user_ler NOBYPASSRLS;
    END IF;
END $$;

-- cdr_user_gravar
DO $$
BEGIN
    IF NOT role_exists('cdr_user_gravar') THEN
        CREATE ROLE cdr_user_gravar
           NOLOGIN
           NOSUPERUSER
           NOCREATEDB
           NOCREATEROLE
           NOREPLICATION
           NOBYPASSRLS;
    ELSE
        ALTER ROLE cdr_user_gravar NOLOGIN;
        ALTER ROLE cdr_user_gravar NOSUPERUSER;
        ALTER ROLE cdr_user_gravar NOCREATEDB;
        ALTER ROLE cdr_user_gravar NOCREATEROLE;
        ALTER ROLE cdr_user_gravar NOREPLICATION;
        ALTER ROLE cdr_user_gravar NOBYPASSRLS;
    END IF;
END $$;

-- cdr_user_super
DO $$
BEGIN
    IF NOT role_exists('cdr_user_super') THEN
        CREATE ROLE cdr_user_super NOLOGIN SUPERUSER;
    ELSE
        ALTER ROLE cdr_user_super NOLOGIN;
        ALTER ROLE cdr_user_super SUPERUSER;  -- Garante superusuário
    END IF;
END $$;

-- =======================================
-- Grants para cdr_user_ler: Apenas leitura (SELECT em tables e views)
-- =======================================
-- Para cada esquema existente
DO $$
DECLARE
    schema_name TEXT;
BEGIN
    FOREACH schema_name IN ARRAY get_schema_names() LOOP
        EXECUTE format('GRANT USAGE ON SCHEMA %I TO cdr_user_ler', schema_name);
        EXECUTE format('GRANT SELECT ON ALL TABLES IN SCHEMA %I TO cdr_user_ler', schema_name);
        EXECUTE format('GRANT SELECT ON ALL SEQUENCES IN SCHEMA %I TO cdr_user_ler', schema_name);
        -- Para views: SELECT já cobre, pois views são tratadas como tables para grants
    END LOOP;
END $$;

-- Para tabelas/views futuras (default privileges) - sobrescreve se existirem
DO $$
DECLARE
    schema_name TEXT;
BEGIN
    FOREACH schema_name IN ARRAY get_schema_names() LOOP
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT SELECT ON TABLES TO cdr_user_ler', schema_name);
    END LOOP;
END $$;

-- =======================================
-- Grants para cdr_user_gravar: Leitura + Gravação + Criação/Alteração/Apagamento de tabelas e dados
-- =======================================
-- Para cada esquema existente
DO $$
DECLARE
    schema_name TEXT;
BEGIN
    FOREACH schema_name IN ARRAY get_schema_names() LOOP
        EXECUTE format('GRANT USAGE, CREATE ON SCHEMA %I TO cdr_user_gravar', schema_name);  -- CREATE para criar/alterar/drop tables no schema
        EXECUTE format('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I TO cdr_user_gravar', schema_name);  -- ALL inclui SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES
        EXECUTE format('GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %I TO cdr_user_gravar', schema_name);  -- ALL para sequences (USAGE, SELECT)
    END LOOP;
END $$;

-- Para tabelas/views futuras (default privileges) - sobrescreve se existirem
DO $$
DECLARE
    schema_name TEXT;
BEGIN
    FOREACH schema_name IN ARRAY get_schema_names() LOOP
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL PRIVILEGES ON TABLES TO cdr_user_gravar', schema_name);
    END LOOP;
END $$;

-- =======================================
-- Grants para cdr_user_super: Como é SUPERUSER, herda tudo, mas concedemos explicitamente para schemas
-- =======================================
-- Para cada esquema existente (USAGE e CREATE para completude, mas SUPERUSER ignora restrições)
DO $$
DECLARE
    schema_name TEXT;
BEGIN
    FOREACH schema_name IN ARRAY get_schema_names() LOOP
        EXECUTE format('GRANT ALL ON SCHEMA %I TO cdr_user_super', schema_name);  -- ALL inclui USAGE, CREATE, etc.
    END LOOP;
END $$;

-- Para objetos existentes (tables, sequences) - SUPERUSER pode acessar tudo, mas para explicitar
DO $$
DECLARE
    schema_name TEXT;
BEGIN
    FOREACH schema_name IN ARRAY get_schema_names() LOOP
        EXECUTE format('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I TO cdr_user_super', schema_name);
        EXECUTE format('GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %I TO cdr_user_super', schema_name);
    END LOOP;
END $$;

-- Para objetos futuros - SUPERUSER ignora, mas para consistência (sobrescreve se existirem)
DO $$
DECLARE
    schema_name TEXT;
BEGIN
    FOREACH schema_name IN ARRAY get_schema_names() LOOP
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL PRIVILEGES ON TABLES TO cdr_user_super', schema_name);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL PRIVILEGES ON SEQUENCES TO cdr_user_super', schema_name);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL PRIVILEGES ON FUNCTIONS TO cdr_user_super', schema_name);  -- Para funções
    END LOOP;
END $$;

-- Limpeza: Remove as funções auxiliares e tabela temporária (opcional, mas mantém o DB limpo)
DROP FUNCTION IF EXISTS role_exists(TEXT);
DROP FUNCTION IF EXISTS get_schema_names();
DROP TABLE IF EXISTS temp_schemas;
```

#### Criação dos usuários

Criar usuário super (administrador do banco de dados)
```sql
-- =======================================
-- Script idempotente para criação/atualização de usuários
-- =======================================
-- Este script:
-- - Cria usuários se não existirem, ou altera atributos se existirem.
-- - Grants são idempotentes (GRANT múltiplas vezes não causa erro).
-- Rode como superusuário (ex.: admin).

-- =======================================
-- Criação/Atualização do usuário específico e grant do grupo super
-- =======================================
DO $$
DECLARE
    user_name TEXT := 'super_usuario_aqui';
    user_password TEXT := 'senha_do_usuario_aqui';  -- Defina a senha aqui se necessário
    user_description TEXT := 'Usuário para acesso ao banco de dados CDR - Superusuário';
BEGIN
    IF NOT role_exists(user_name) THEN
        IF user_password IS NOT NULL THEN
            EXECUTE format('CREATE ROLE %I WITH LOGIN PASSWORD %L INHERIT CONNECTION LIMIT -1', user_name, user_password);
        ELSE
            EXECUTE format('CREATE ROLE %I WITH LOGIN INHERIT CONNECTION LIMIT -1', user_name);
        END IF;
    ELSE
        -- Altera se necessário (ex.: garantir LOGIN e INHERIT)
        EXECUTE format('ALTER ROLE %I LOGIN', user_name);
        EXECUTE format('ALTER ROLE %I INHERIT', user_name);
        EXECUTE format('ALTER ROLE %I CONNECTION LIMIT -1', user_name);
        -- Atualiza senha se definida
        IF user_password IS NOT NULL THEN
            EXECUTE format('ALTER ROLE %I PASSWORD %L', user_name, user_password);
        END IF;
    END IF;
    
    EXECUTE format('COMMENT ON ROLE %I IS %L', user_name, user_description);  -- Sobrescreve comentário se existir
    
    -- Grant do grupo: Idempotente, mas revoga se já existir para garantir
    EXECUTE format('REVOKE cdr_user_super FROM %I', user_name);
    EXECUTE format('GRANT cdr_user_super TO %I', user_name);
END $$;
```
Criar usuário para gravar (pode consultar, incluir e excluir objetos)
```sql
-- =======================================
-- Criação/Atualização do usuário específico e grant do grupo gravar
-- =======================================
DO $$
DECLARE
    user_name TEXT := 'usuario_gravar_aqui';
    user_password TEXT := 'senha_do_usuario_aqui';  -- Defina a senha aqui se necessário
    user_description TEXT := 'Usuário para acesso ao banco de dados CDR - Gravar';
BEGIN
    IF NOT role_exists(user_name) THEN
        IF user_password IS NOT NULL THEN
            EXECUTE format('CREATE ROLE %I WITH LOGIN PASSWORD %L INHERIT CONNECTION LIMIT -1', user_name, user_password);
        ELSE
            EXECUTE format('CREATE ROLE %I WITH LOGIN INHERIT CONNECTION LIMIT -1', user_name);
        END IF;
    ELSE
        -- Altera se necessário (ex.: garantir LOGIN e INHERIT)
        EXECUTE format('ALTER ROLE %I LOGIN', user_name);
        EXECUTE format('ALTER ROLE %I INHERIT', user_name);
        EXECUTE format('ALTER ROLE %I CONNECTION LIMIT -1', user_name);
        -- Atualiza senha se definida
        IF user_password IS NOT NULL THEN
            EXECUTE format('ALTER ROLE %I PASSWORD %L', user_name, user_password);
        END IF;
    END IF;
    
    EXECUTE format('COMMENT ON ROLE %I IS %L', user_name, user_description);  -- Sobrescreve comentário se existir
    
    -- Grant do grupo: Idempotente, mas revoga se já existir para garantir
    EXECUTE format('REVOKE cdr_user_super FROM %I', user_name);
	EXECUTE format('REVOKE cdr_user_gravar FROM %I', user_name);
    EXECUTE format('GRANT cdr_user_gravar TO %I', user_name);
END $$;
```
Criar usário de leitura (pode apenas fazer consultas)
```sql
-- =======================================
-- Criação/Atualização do usuário específico e grant do grupo ler
-- =======================================
DO $$
DECLARE
    user_name TEXT := 'usuario_ler_aqui';
    user_password TEXT := NULL;  -- Defina a senha aqui se necessário
    user_description TEXT := 'Usuário para acesso ao banco de dados CDR - Ler';
BEGIN
    IF NOT role_exists(user_name) THEN
        IF user_password IS NOT NULL THEN
            EXECUTE format('CREATE ROLE %I WITH LOGIN PASSWORD %L INHERIT CONNECTION LIMIT -1', user_name, user_password);
        ELSE
            EXECUTE format('CREATE ROLE %I WITH LOGIN INHERIT CONNECTION LIMIT -1', user_name);
        END IF;
    ELSE
        -- Altera se necessário (ex.: garantir LOGIN e INHERIT)
        EXECUTE format('ALTER ROLE %I LOGIN', user_name);
        EXECUTE format('ALTER ROLE %I INHERIT', user_name);
        EXECUTE format('ALTER ROLE %I CONNECTION LIMIT -1', user_name);
        -- Atualiza senha se definida
        IF user_password IS NOT NULL THEN
            EXECUTE format('ALTER ROLE %I PASSWORD %L', user_name, user_password);
        END IF;
    END IF;
    
    EXECUTE format('COMMENT ON ROLE %I IS %L', user_name, user_description);  -- Sobrescreve comentário se existir
    
    -- Grant do grupo: Idempotente, mas revoga se já existir para garantir
    EXECUTE format('REVOKE cdr_user_super FROM %I', user_name);
	EXECUTE format('REVOKE cdr_user_gravar FROM %I', user_name);
	EXECUTE format('REVOKE cdr_user_ler FROM %I', user_name);
    EXECUTE format('GRANT cdr_user_ler TO %I', user_name);
END $$;
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

## 👤 Autores

**Ronaldo S.A. Batista**
- Email: <eu@ronaldo.tech>

**Maxwel de Souza Freitas**
- Email: maxwel@maxwelfreitas.com.br

**Carlos Cesar Lanzoni**
- Email: carlos.cesar@anatel.gov.br
---

**Versão:** 0.0.2
**Última atualização:** 2025-12-17
**Status:** Em desenvolvimento ativo