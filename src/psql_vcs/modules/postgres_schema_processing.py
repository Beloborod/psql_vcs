"""Core project logic with PostgreSQL schema processing
"""

import logging
from collections import defaultdict
from dataclasses import asdict
from json import dump, load
from typing import LiteralString, cast

import results
from psycopg import Error as PsycopgError
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import PostgresDsn

from ..models import AuthArgs, CurrentSchema, URLArgs
from ..models.shcema_description import ForeignKeyInfo
from ..sql import (
    CHECK_DATABASE,
    CREATE_DATABASE,
    CREATE_EXTENSION_UUID,
    CREATE_SCHEMA_MIGRATIONS,
    CREATE_TABLE_SCHEMAS,
    DISCONNECT_FROM_DB,
    DROP_DATABASE,
    FIND_MAP,
    FIND_MAX_VERSION,
    FIND_MIGRATION,
    FIND_MIGRATION_VERSION,
    INSERT_NEW_MIGRATION,
    LOAD_MIGRATION,
    SELECT_ALL_MIGRATIONS,
    SELECT_COLUMNS_INFO,
    SELECT_SCHEMAS_INFO,
    SELECT_TABLE_INFO,
)
from . import PostgresRequester

logger = logging.getLogger(__name__)


class PostgresMigrator:
    def __init__(self, args: AuthArgs | URLArgs) -> None:
        """
        Initialize Postgres Migrator, create migrations db if not exists.

        :param args: Creds for connect to database(s)
        :type args: AuthArgs | URLArgs
        :rtype: None
        """
        self.main_migrations_dsn_obj: PostgresDsn
        self.migrations_dsn_obj: PostgresDsn
        self.test_dsn_obj: PostgresDsn
        self.target_dsn_obj: PostgresDsn
        self.target_main_dsn_obj: PostgresDsn

        if isinstance(args, AuthArgs):
            self.main_migrations_dsn_obj = PostgresDsn.build(
                scheme="postgresql",
                host=args.migration_server_host.__str__(),
                port=args.migration_server_port,
                username=args.migration_server_username,
                password=args.migration_server_password,
                path=args.migration_server_main_database,
            )
            self.migrations_dsn_obj = PostgresDsn.build(
                scheme="postgresql",
                host=args.migration_server_host.__str__(),
                port=args.migration_server_port,
                username=args.migration_server_username,
                password=args.migration_server_password,
                path=args.migration_server_migrations_database,
            )
            self.test_dsn_obj = PostgresDsn.build(
                scheme="postgresql",
                host=args.migration_server_host.__str__(),
                port=args.migration_server_port,
                username=args.migration_server_username,
                password=args.migration_server_password,
                path=args.migration_server_test_database,
            )
            self.target_dsn_obj = PostgresDsn.build(
                scheme="postgresql",
                host=args.target_server_host.__str__(),
                port=args.target_server_port,
                username=args.target_server_username,
                password=args.target_server_password,
                path=args.target_database,
            )
            self.target_main_dsn_obj = PostgresDsn.build(
                scheme="postgresql",
                host=args.target_server_host.__str__(),
                port=args.target_server_port,
                username=args.target_server_username,
                password=args.target_server_password,
                path=args.target_server_main_database,
            )
        else:
            self.main_migrations_dsn_obj = args.dsn_migration_main_database
            self.migrations_dsn_obj = args.dsn_migrations_database
            self.test_dsn_obj = args.dsn_migrations_test_database
            self.target_dsn_obj = args.dsn_target_database
            self.target_main_dsn_obj = args.dsn_target_main_database

        self.migration_name = args.migration_name
        self.__create_migrations_db()

    @staticmethod
    def _get_db_name(dns_obj: PostgresDsn) -> str:
        path = dns_obj.path
        if path is None:
            raise RuntimeError("Path is None")
        return path

    def __create_migrations_db(self) -> None:
        """
        Create migrations database if not exists.

        :rtype: None
        """
        with PostgresRequester(
            self.main_migrations_dsn_obj
        ) as main_migrations_requester:
            with main_migrations_requester.cursor() as cursor:
                cursor.execute(
                    CHECK_DATABASE,
                    (self._get_db_name(self.migrations_dsn_obj).lstrip("/"),),
                )
                exists = cursor.fetchone()
                if exists:
                    exists = exists[0]
                else:
                    raise PsycopgError("SQL request error")
                if not exists:
                    cursor.execute(
                        sql.SQL(CREATE_DATABASE).format(
                            sql.Identifier(
                                self._get_db_name(
                                    self.migrations_dsn_obj
                                ).lstrip("/")
                            )
                        )
                    )

        with PostgresRequester(self.migrations_dsn_obj) as requester:
            with requester.cursor() as cursor:
                cursor.execute(CREATE_SCHEMA_MIGRATIONS)
                cursor.execute(CREATE_EXTENSION_UUID)
                cursor.execute(CREATE_TABLE_SCHEMAS)

    def _extract_schema(self) -> dict:
        """
        Extract schema in specific format from target database.

        :return: Schema in specific format
        :rtype: dict
        """
        schema: dict = {"tables": {}, "indexes": [], "foreign_keys": []}

        try:
            with PostgresRequester(self.target_dsn_obj) as requester:
                with requester.cursor() as cursor:
                    cursor.execute(SELECT_COLUMNS_INFO)
                    tables = defaultdict(list)
                    for (
                        sch,
                        tbl,
                        col,
                        dtype,
                        max_char,
                        precis,
                        scale,
                        date_precis,
                        nullable,
                        default,
                        pos,
                    ) in cursor.fetchall():
                        tables[f"{sch}.{tbl}"].append(
                            {
                                "name": col,
                                "type": dtype.strip(),
                                "nullable": nullable == "YES",
                                "max_char": max_char if max_char else None,
                                "precision": precis if precis else None,
                                "scale": scale if scale else None,
                                "date_precision": (
                                    date_precis if date_precis else None
                                ),
                                "default": (
                                    default.strip() if default else None
                                ),
                                "position": pos,
                            }
                        )
                    schema["tables"] = dict(tables)

                    cursor.execute(SELECT_SCHEMAS_INFO)
                    for sch, tbl, idx_name, idx_def in cursor.fetchall():
                        clean_def = " ".join(idx_def.split()).replace(
                            "public.", ""
                        )
                        schema["indexes"].append(
                            {
                                "table": f"{sch}.{tbl}",
                                "name": idx_name,
                                "definition": clean_def,
                            }
                        )

                    cursor.execute(SELECT_TABLE_INFO)
                    fks: defaultdict[str, ForeignKeyInfo] = defaultdict(
                        ForeignKeyInfo
                    )
                    for row in cursor.fetchall():
                        key = f"{row[0]}.{row[1]}.{row[2]}"
                        fks[key].columns.append(row[3])
                        fks[key].ref_table = f"{row[4]}.{row[5]}"
                        fks[key].ref_columns.append(row[6])
                        fks[key].del_upd = f"{row[7]}.{row[8]}"
                    for v in fks.values():
                        v.columns.sort()
                        v.ref_columns.sort()

                    schema["foreign_keys"] = [
                        {"constraint_name": k, **asdict(v)}
                        for k, v in sorted(fks.items())
                    ]
                    schema["foreign_keys"] = [
                        {"constraint_name": k, **asdict(v)}
                        for k, v in fks.items()
                    ]
        except PsycopgError as e:
            raise RuntimeError(f"Connect or request failed: {e}") from None

        return schema

    def _save_schema_diff(self, schema: dict, sql_request: str) -> None:
        """
        Add to migrations database new chain link with difference between last
        available shema and new version.

        :param schema: Database schema in specific format
        :type schema: dict
        :param sql_request: SQL script to make new schemas version from
            last available in migrations chain
        :type sql_request: str
        :rtype: None
        """
        with PostgresRequester(self.migrations_dsn_obj) as requester:
            with requester.cursor() as cursor:
                cursor.execute(
                    INSERT_NEW_MIGRATION,
                    (
                        self.migration_name,
                        self.migration_name,
                        Jsonb(schema),
                        sql_request,
                    ),
                )

    def _schema_compare(self, schema: dict) -> CurrentSchema:
        """
        Compare current schema of target database with available in migrations
        database Return name of chain group, current version in chain and max
        available version.

        :param schema: Current schema in specific format
        :type schema: dict
        :return: Name of chain group, current version in chain and max
            available version
        :rtype: CurrentSchema
        """
        with PostgresRequester(self.migrations_dsn_obj) as requester:
            with requester.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    FIND_MIGRATION,
                    (Jsonb(schema),),
                )
                search_result = cursor.fetchone()
                if search_result is None:
                    raise RuntimeError("Scheme not found")

                cursor.execute(
                    FIND_MAX_VERSION,
                    (search_result["name"],),
                )
                result = cursor.fetchone()
                if result is None:
                    raise RuntimeError("Scheme not found")
                max_version = result["max_version"]
                return CurrentSchema(
                    search_result["name"], search_result["step"], max_version
                )

    def _generate_map(
        self, current_version: int, max_version: int
    ) -> list[str]:
        """
        Generate migration map - list of SQL scripts to migrate
        database between current and max version

        :param current_version: Current database version
        :type current_version: int
        :param max_version: Max (or needed) database version
        :type max_version: int
        :return: List of SQL scripts for make migrations
        :rtype: list[str]
        """
        if current_version < max_version:
            with PostgresRequester(self.migrations_dsn_obj) as requester:
                with requester.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        FIND_MAP,
                        (self.migration_name, current_version, max_version),
                    )
                    search_result = cursor.fetchall()
                    if len(search_result) == 0:
                        raise RuntimeError(
                            "Can't find schemas for {}, started on "
                            "{} and end on {} versions".format(
                                self.migration_name,
                                current_version,
                                max_version,
                            )
                        )
                    return [row["sql_request"] for row in search_result]
        else:
            logger.debug(f"Schema version {current_version} is already actual")
            return []

    def _get_migration_map_by_schema(self, schema: dict) -> list[str]:
        """
        Generate migration map by specified schema in specific format.

        :param schema: Schema in specific format
        :type schema: dict
        :return: List of SQL scripts for make migrations
        :rtype: list[str]
        """
        current_schema = self._schema_compare(schema)
        return self._generate_map(
            current_schema.current_version, current_schema.max_version
        )

    def _get_migration_map(
        self, start_version: int = 1, end_version: int | None = None
    ) -> list[str]:
        """
        Generate migration map for target database, with specified start and
        end version.

        :param start_version: First version to start migration
        :type start_version: int
        :param end_version: End version to end migration, use lastest if
            specified like None
        :type end_version: int | None
        :return: List of SQL scripts for make migrations
        :rtype: list[str]
        """
        if end_version is None:
            with PostgresRequester(self.migrations_dsn_obj) as requester:
                with requester.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        FIND_MAX_VERSION,
                        (self.migration_name,),
                    )
                    search_result = cursor.fetchone()
                    if not search_result:
                        raise RuntimeError("Schema not found")
                    end_version = search_result["max_version"]
        return self._generate_map(start_version, end_version)

    def migrate_to_last_version(self) -> None:
        """
        Make migrations for target database to latest version, create database
        if not exists.

        :rtype: None
        """
        with PostgresRequester(
            self.target_main_dsn_obj
        ) as main_target_requester:
            with main_target_requester.cursor() as cursor:
                cursor.execute(
                    CHECK_DATABASE,
                    (self._get_db_name(self.target_dsn_obj).lstrip("/"),),
                )
                exists = cursor.fetchone()
                if exists:
                    exists = exists[0]
                else:
                    raise PsycopgError("SQL request error")
                if not exists:
                    initial_sql = self._get_migration_map(
                        start_version=-1, end_version=0
                    )
                    if not initial_sql:
                        raise RuntimeError(
                            f"Can't find database for "
                            f"{self.migration_name}, "
                            f"after try to create - can't "
                            f"find initial schema"
                        )
                    cursor.execute(
                        sql.SQL(CREATE_DATABASE).format(
                            sql.Identifier(
                                self._get_db_name(self.target_dsn_obj).lstrip(
                                    "/"
                                )
                            )
                        )
                    )
                    with PostgresRequester(
                        self.target_dsn_obj
                    ) as target_requester:
                        with target_requester.cursor() as target_cursor:
                            for migration in initial_sql:
                                target_cursor.execute(
                                    cast(LiteralString, migration)
                                )

        schema = self._extract_schema()
        migration_map = self._get_migration_map_by_schema(schema)
        with PostgresRequester(self.target_dsn_obj) as requester:
            with requester.cursor() as cursor:
                for migration in migration_map:
                    cursor.execute(cast(LiteralString, migration))

    def create_migration(self) -> None:
        """Add migration in chain, add tag if specified, or use database
        name. If no migrations for this chain group exists - create
        first script to create database, otherwise find difference
        between last available version in chain and current instance of
        target database and add it to migrations database.

        :rtype: None
        """
        with PostgresRequester(
            self.migrations_dsn_obj
        ) as migrations_requester:
            with migrations_requester.cursor() as cursor:
                cursor.execute(
                    FIND_MIGRATION_VERSION,
                    (self.migration_name, 0),
                )
                exists = cursor.fetchone()
                if exists:
                    exists = exists[0]
                else:
                    raise PsycopgError("SQL request error")

        with PostgresRequester(
            self.main_migrations_dsn_obj
        ) as main_database_requester:
            with main_database_requester.cursor() as cursor:
                cursor.execute(
                    DISCONNECT_FROM_DB,
                    (self._get_db_name(self.test_dsn_obj).lstrip("/"),),
                )
                cursor.execute(
                    sql.SQL(DROP_DATABASE).format(
                        sql.Identifier(
                            self._get_db_name(self.test_dsn_obj).lstrip("/")
                        )
                    )
                )
                cursor.execute(
                    sql.SQL(CREATE_DATABASE).format(
                        sql.Identifier(
                            self._get_db_name(self.test_dsn_obj).lstrip("/")
                        )
                    )
                )

        if exists:
            full_migration_chain = self._get_migration_map(-1)
            with PostgresRequester(self.test_dsn_obj) as test_requester:
                with test_requester.cursor() as cursor:
                    for migration in full_migration_chain:
                        cursor.execute(cast(LiteralString, migration))

        diff = results.db(
            self.test_dsn_obj.encoded_string()
        ).schemadiff_as_sql(results.db(self.target_dsn_obj.encoded_string()))

        schema = self._extract_schema()

        if diff:
            self._save_schema_diff(schema, diff)
        else:
            logger.info("No changes made for %s", self.migration_name)

        with PostgresRequester(
            self.main_migrations_dsn_obj
        ) as main_database_requester:
            with main_database_requester.cursor() as cursor:
                cursor.execute(
                    DISCONNECT_FROM_DB,
                    (self._get_db_name(self.test_dsn_obj).lstrip("/"),),
                )
                cursor.execute(
                    sql.SQL(DROP_DATABASE).format(
                        sql.Identifier(
                            self._get_db_name(self.test_dsn_obj).lstrip("/")
                        )
                    )
                )

    def save_migrations(self, file: str) -> None:
        """
        Save current migrations database to file.

        :param file: File name / path with name to save migrations
            database data
        :type file: str
        :rtype: None
        """
        with PostgresRequester(
            self.migrations_dsn_obj
        ) as migrations_requester:
            with migrations_requester.cursor(row_factory=dict_row) as cursor:
                cursor.execute(SELECT_ALL_MIGRATIONS)
                all_schemas = cursor.fetchall()
        with open(file, "w") as f:
            dump(all_schemas, f, default=str)

    def load_migrations(self, file: str) -> None:
        """
        Load migrations database from file to migrations database.

        :param file: File name / path with name to load migrations
            database data
        :type file: str
        :rtype: None
        """
        with open(file, "r") as f:
            data = load(f)
        with PostgresRequester(
            self.migrations_dsn_obj
        ) as migrations_requester:
            with migrations_requester.cursor(row_factory=dict_row) as cursor:
                for schema in data:
                    cursor.execute(
                        LOAD_MIGRATION,
                        (
                            schema["id"],
                            schema["name"],
                            schema["step"],
                            Jsonb(schema["schema"]),
                            schema["sql_request"],
                            schema["created_at"],
                        ),
                    )
