from typing import LiteralString

CREATE_SCHEMA_MIGRATIONS: LiteralString = """CREATE SCHEMA IF NOT EXISTS 
migrations;"""

CREATE_EXTENSION_UUID: LiteralString = """CREATE EXTENSION IF NOT EXISTS 
    "uuid-ossp";"""

CREATE_TABLE_SCHEMAS: LiteralString = """CREATE TABLE IF NOT EXISTS 
                                             migrations.schemas
                (
                    id UUID PRIMARY KEY
                    DEFAULT uuid_generate_v4(),
                    name CHARACTER VARYING (40) NOT NULL,
                    step SMALLINT NOT NULL, schema JSONB NOT NULL UNIQUE,
                    sql_request CHARACTER VARYING NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                               """

SELECT_COLUMNS_INFO: LiteralString = """SELECT table_schema,table_name,
                                               column_name,data_type,
                                               character_maximum_length,
                                               numeric_precision,numeric_scale,
                                               datetime_precision,is_nullable,
                                               column_default,ordinal_position
                                        FROM information_schema.columns
                                        WHERE table_schema
                                          NOT IN (
                                                  'pg_catalog',
                                                  'information_schema'
                                                )
                                        AND table_name NOT LIKE 'pg_%'
                                        ORDER BY
                                          table_schema,
                                          table_name,
                                          ordinal_position;"""

SELECT_SCHEMAS_INFO: LiteralString = """SELECT schemaname, tablename,
                                               indexname, indexdef
                                        FROM pg_indexes
                                        WHERE schemaname NOT IN
                                            (
                                             'pg_catalog',
                                             'information_schema'
                                                )
                                        ORDER BY
                                            schemaname,
                                            tablename,
                                            indexname;"""

SELECT_TABLE_INFO: LiteralString = """
                        SELECT
                            tc.table_schema, tc.table_name, tc.constraint_name,
                            kcu.column_name,
                            ccu.table_schema AS fk_schema,
                            ccu.table_name AS fk_table,
                            ccu.column_name AS fk_column,
                            pc.confdeltype as pc_del_type,
                            pc.confupdtype as pc_upd_type
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                          ON tc.constraint_name = kcu.constraint_name
                         AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage ccu
                          ON ccu.constraint_name = tc.constraint_name
                        JOIN pg_constraint pc
                          ON pc.conname = tc.constraint_name
                        WHERE tc.constraint_type = 'FOREIGN KEY'
                            AND tc.table_schema NOT IN
                                ('pg_catalog', 'information_schema')
                        ORDER BY tc.table_schema, tc.table_name,
                                 tc.constraint_name, kcu.ordinal_position;
                    """

SELECT_ALL_MIGRATIONS: LiteralString = """SELECT * FROM migrations.schemas;"""
