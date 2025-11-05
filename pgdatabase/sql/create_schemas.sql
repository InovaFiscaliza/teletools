-- Define a lista de esquemas e seus comentários
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
    -- Itera sobre cada esquema na lista
    FOR i IN 1..array_length(schemas_list, 1) LOOP
        DECLARE
            schema_name TEXT := schemas_list[i][1];
            schema_comment TEXT := schemas_list[i][2];
        BEGIN
            -- Cria o esquema
            EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I AUTHORIZATION pg_database_owner', schema_name);
            RAISE NOTICE 'Esquema % criado', schema_name;
            
            -- Adiciona comentário ao esquema
            EXECUTE format('COMMENT ON SCHEMA %I IS %L', schema_name, schema_comment);
            
            -- Concede permissões ao esquema
            EXECUTE format('GRANT USAGE ON SCHEMA %I TO PUBLIC', schema_name);
            EXECUTE format('GRANT ALL ON SCHEMA %I TO cdr_database_users', schema_name);

            -- Concede permissões para objetos no esquema
            EXECUTE format('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I TO cdr_database_users', schema_name);
            EXECUTE format('GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %I TO cdr_database_users', schema_name);
            EXECUTE format('GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA %I TO cdr_database_users', schema_name);
            EXECUTE format('GRANT ALL PRIVILEGES ON ALL TYPES IN SCHEMA %I TO cdr_database_users', schema_name);
            
            -- Altera permissões padrão para objetos futuros no esquema
            EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA %I GRANT ALL ON TABLES TO cdr_database_users', schema_name);
            EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA %I GRANT ALL ON SEQUENCES TO cdr_database_users', schema_name);
            EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA %I GRANT EXECUTE ON FUNCTIONS TO cdr_database_users', schema_name);
            EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA %I GRANT USAGE ON TYPES TO cdr_database_users', schema_name);
            
            RAISE NOTICE 'Permissões configuradas para o esquema %', schema_name;
        END;
    END LOOP;
END $$;