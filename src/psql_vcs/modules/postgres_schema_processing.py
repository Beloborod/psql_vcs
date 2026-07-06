import logging
from psycopg import Error as PsycopgError
from psycopg.rows import dict_row
from psycopg import sql
from psycopg.types.json import Jsonb
from typing import cast, LiteralString
from collections import defaultdict
import results
from pydantic import PostgresDsn
from ..models import AuthArgs, URLArgs, CurrentSchema
from . import PostgresRequester


logger = logging.getLogger(__name__)


class PostgresMigrator:
    def __init__(self, args: AuthArgs | URLArgs):
        if isinstance(args, AuthArgs):
            self.main_migrations_dsn_obj = PostgresDsn.build(
                scheme="postgresql",
                host=args.migration_server_host,
                port=args.migration_server_port,
                username=args.migration_server_username,
                password=args.migration_server_password,
                path=args.migration_server_main_database
            )
            self.migrations_dsn_obj = PostgresDsn.build(
                scheme="postgresql",
                host=args.migration_server_host,
                port=args.migration_server_port,
                username=args.migration_server_username,
                password=args.migration_server_password,
                path=args.migration_server_migrations_database
            )
            self.test_dsn_obj = PostgresDsn.build(
                scheme="postgresql",
                host=args.migration_server_host,
                port=args.migration_server_port,
                username=args.migration_server_username,
                password=args.migration_server_password,
                path=args.migration_server_test_database
            )
            self.target_dsn_obj = PostgresDsn.build(
                scheme="postgresql",
                host=args.target_server_host,
                port=args.target_server_port,
                username=args.target_server_username,
                password=args.target_server_password,
                path=args.target_database
            )
            self.target_main_dns_obj = PostgresDsn.build(
                scheme="postgresql",
                host=args.target_server_host,
                port=args.target_server_port,
                username=args.target_server_username,
                password=args.target_server_password,
                path=args.target_server_main_database
            )
        else:
            self.main_migrations_dsn_obj = PostgresDsn(args.migrations_main_database_url) \
                if isinstance(args.migrations_main_database_url, str) else args.migrations_main_database_url
            self.migrations_dsn_obj = PostgresDsn(args.migrations_database_url) \
                if isinstance(args.migrations_database_url, str) else args.migrations_database_url
            self.test_dsn_obj = PostgresDsn(args.migrations_test_database_url) \
                if isinstance(args.migrations_test_database_url, str) else args.migrations_test_database_url
            self.target_dsn_obj = PostgresDsn(args.target_database_url) \
                if isinstance(args.target_database_url, str) else args.target_database_url
            self.target_main_dsn_obj = PostgresDsn(args.target_server_main_database_url) \
                if isinstance(args.target_server_main_database_url, str) else args.target_server_main_database_url

        self.migration_name = args.migration_name

        main_migrations_requester = PostgresRequester(self.target_main_dns_obj)
        with main_migrations_requester.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                        """
                        SELECT EXISTS (
                                   SELECT 1
                                   FROM pg_database
                                   WHERE datname = %s
                        );
                        """, (self.migrations_dsn_obj.path.lstrip('/'),)
                )
                exists = cursor.fetchone()[0]
                if not exists:
                    cursor.execute(
                        sql.SQL(
                            """
                            CREATE DATABASE {};
                            """
                        ).format(sql.Identifier(self.migrations_dsn_obj.path.lstrip('/')))
                    )

        requester = PostgresRequester(self.migrations_dsn_obj)
        with requester.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE SCHEMA IF NOT EXISTS migrations;
                    """)
                cursor.execute(
                    """
                    CREATE
                    EXTENSION IF NOT EXISTS "uuid-ossp";
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS migrations.schemas
                    (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        name CHARACTER VARYING (40) NOT NULL,
                        step SMALLINT NOT NULL,
                        schema JSONB NOT NULL UNIQUE,
                        sql_request CHARACTER VARYING NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW
                    (
                    )
                        );
                    """
                )



    def _extract_schema(self) -> dict:
        schema = {"tables": {}, "indexes": [], "foreign_keys": []}

        requester = PostgresRequester(self.target_dsn_obj)

        try:
            with requester.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT table_schema, table_name, column_name, data_type, character_maximum_length, 
                        numeric_precision, numeric_scale, datetime_precision,
                               is_nullable, column_default, ordinal_position
                        FROM information_schema.columns
                        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                          AND table_name NOT LIKE 'pg_%'
                        ORDER BY table_schema, table_name, ordinal_position
                    """)
                    tables = defaultdict(list)
                    for sch, tbl, col, dtype, max_char, precis, scale, date_precis, \
                            nullable, default, pos in cursor.fetchall():
                        tables[f"{sch}.{tbl}"].append({
                            "name": col,
                            "type": dtype.strip(),
                            "nullable": nullable == "YES",
                            "max_char": max_char if max_char else None,
                            "precision": precis if precis else None,
                            "scale": scale if scale else None,
                            "date_precision": date_precis if date_precis else None,
                            "default": default.strip() if default else None,
                            "position": pos
                        })
                    schema["tables"] = dict(tables)

                    cursor.execute("""
                        SELECT schemaname, tablename, indexname, indexdef
                        FROM pg_indexes
                        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                        ORDER BY schemaname, tablename, indexname
                    """)
                    for sch, tbl, idx_name, idx_def in cursor.fetchall():
                        clean_def = " ".join(idx_def.split()).replace("public.", "")
                        schema["indexes"].append({
                            "table": f"{sch}.{tbl}",
                            "name": idx_name,
                            "definition": clean_def
                        })

                    cursor.execute("""
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
                            AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
                        ORDER BY tc.table_schema, tc.table_name, tc.constraint_name, kcu.ordinal_position
                    """)
                    fks: defaultdict[str, dict[str, list | str | None]] = defaultdict(
                        lambda: {"columns": [], "ref_table": None, "ref_columns": [], "del_upd": None})
                    for row in cursor.fetchall():
                        key = f"{row[0]}.{row[1]}.{row[2]}"
                        fks[key]["columns"].append(row[3])
                        fks[key]["ref_table"] = f"{row[4]}.{row[5]}"
                        fks[key]["ref_columns"].append(row[6])
                        fks[key]["del_upd"] = f"{row[7]}.{row[8]}"
                    for v in fks.values():
                        v["columns"].sort()
                        v["ref_columns"].sort()

                    schema["foreign_keys"] = [
                        {"constraint_name": k, **v} for k, v in sorted(fks.items())
                    ]
                    schema["foreign_keys"] = [
                        {"constraint_name": k, **v} for k, v in fks.items()
                    ]
        except PsycopgError as e:
            raise RuntimeError(f"Connect or request failed: {e}") from None

        return schema

    def _save_schema_diff(self, schema: dict, sql_request: str) -> None:
        requester = PostgresRequester(self.migrations_dsn_obj)
        with requester.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO migrations.schemas (name, step, schema, sql_request)
                        VALUES
                            (
                                %s,
                                (
                                    SELECT COALESCE(MAX(step), -1) + 1
                                    FROM migrations.schemas
                                    WHERE name = %s
                                ),
                                %s,
                                %s
                            );
                    """, (self.migration_name, self.migration_name, Jsonb(schema), sql_request)
                )

    def _schema_compare(self, schema: dict) -> CurrentSchema:
        requester = PostgresRequester(self.migrations_dsn_obj)
        with requester.get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT name, step FROM migrations.schemas
                        WHERE schema = %s;
                    """, (Jsonb(schema),)
                )
                search_result = cursor.fetchone()
                if search_result is None:
                    raise RuntimeError("Scheme not found")

                cursor.execute(
                    """
                    SELECT MAX(step) as max_version FROM migrations.schemas
                        WHERE name = %s;
                    """, (search_result['name'],)
                )
                max_version = cursor.fetchone()['max_version']
                return CurrentSchema(search_result['name'], search_result['step'], max_version)

    def _generate_map(self, current_version: int, max_version: int) -> list[str]:
        requester = PostgresRequester(self.migrations_dsn_obj)
        if current_version < max_version:
            with requester.get_connection() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        SELECT step, sql_request
                        FROM migrations.schemas
                        WHERE name = %s
                          AND step > %s
                            AND step <= %s
                        ORDER BY step;
                        """, (self.migration_name, current_version, max_version)
                    )
                    search_result = cursor.fetchall()
                    if len(search_result) == 0:
                        raise RuntimeError("Can't find schemas for %s, started on %s and end on %s versions".format(
                            self.migration_name, current_version, max_version))
                    return [row['sql_request'] for row in search_result]
        else:
            logger.debug(f"Schema version {current_version} is already actual")
            return []

    def _get_migration_map_by_schema(self, schema: dict) -> list[str]:
        current_schema = self._schema_compare(schema)
        return self._generate_map(current_schema.current_version, current_schema.max_version)

    def _get_migration_map(self, start_version: int = 1, end_version: int | None = None) -> list[str]:
        requester = PostgresRequester(self.migrations_dsn_obj)
        if end_version is None:
            with requester.get_connection() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        SELECT MAX(step) as max_step FROM migrations.schemas
                            WHERE name = %s
                        """, (self.migration_name,)
                    )
                    search_result = cursor.fetchone()
                    end_version = search_result['max_step']
        return self._generate_map(start_version, end_version)

    def migrate_to_last_version(self) -> None:
        main_target_requester = PostgresRequester(self.target_main_dns_obj)
        with main_target_requester.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                        """
                        SELECT 1
                        FROM pg_database
                        WHERE datname = %s;
                        """, (self.target_dsn_obj.path.lstrip('/'),)
                )
                a = cursor.fetchone()
                if a is None:
                    initial_sql = self._get_migration_map(start_version=-1, end_version=0)
                    if not initial_sql:
                        raise RuntimeError(f"Can't find database for {self.migration_name}, after try to create - can't "
                                           f"find initial schema")
                    cursor.execute(
                        sql.SQL(
                            """
                            CREATE DATABASE {};
                            """
                        ).format(sql.Identifier(self.target_dsn_obj.path.lstrip('/')))
                    )
                    target_requester = PostgresRequester(self.target_dsn_obj)
                    with target_requester.get_connection() as target_connection:
                        with target_connection.cursor() as target_cursor:
                            for migration in initial_sql:
                                target_cursor.execute(cast(LiteralString, migration))

        schema = self._extract_schema()
        migration_map = self._get_migration_map_by_schema(schema)
        requester = PostgresRequester(self.target_dsn_obj)
        with requester.get_connection() as connection:
            with connection.cursor() as cursor:
                for migration in migration_map:
                    cursor.execute(cast(LiteralString, migration))

    def create_migration(self) -> None:
        migrations_requester = PostgresRequester(self.migrations_dsn_obj)
        with migrations_requester.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM migrations.schemas
                        WHERE name = %s
                          AND step = %s
                    )
                    """, (self.migration_name, 0)
                )
                exists = cursor.fetchone()[0]

        main_database_requester = PostgresRequester(self.main_migrations_dsn_obj)
        with main_database_requester.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                        """
                        SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE datname = %s
                          AND pid <> pg_backend_pid();
                        """, (self.test_dsn_obj.path.lstrip('/'),)
                )
                cursor.execute(
                    sql.SQL(
                        """
                        DROP DATABASE IF EXISTS {};
                        """
                    ).format(sql.Identifier(self.test_dsn_obj.path.lstrip('/')))
                )
                cursor.execute(
                    sql.SQL(
                        """
                        CREATE DATABASE {};
                        """
                    ).format(sql.Identifier(self.test_dsn_obj.path.lstrip('/')))
                )
        test_requester = PostgresRequester(self.test_dsn_obj)

        if exists:
            full_migration_chain = self._get_migration_map(-1)
            with test_requester.get_connection() as connection:
                with connection.cursor() as cursor:
                    for migration in full_migration_chain:
                        cursor.execute(cast(LiteralString, migration))

        diff = (results.db(self.test_dsn_obj.encoded_string()).
                schemadiff_as_sql(results.db(self.target_dsn_obj.encoded_string())))

        schema = self._extract_schema()

        if diff:
            self._save_schema_diff(schema, diff)
        else:
            logger.info("No changes made for %s", self.migration_name)

        with main_database_requester.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                        """
                        SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE datname = %s
                          AND pid <> pg_backend_pid();
                        """, (self.test_dsn_obj.path.lstrip('/'),)
                )
                cursor.execute(
                    sql.SQL(
                        """
                        DROP
                        DATABASE IF EXISTS {};
                        """
                    ).format(sql.Identifier(self.test_dsn_obj.path.lstrip('/')))
                )
