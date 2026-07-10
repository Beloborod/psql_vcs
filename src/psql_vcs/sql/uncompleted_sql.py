from typing import LiteralString

CHECK_DATABASE: LiteralString = """
                                SELECT EXISTS (
                                    SELECT 1
                                    FROM pg_database
                                    WHERE datname = %s
                                );
                                """

CREATE_DATABASE: LiteralString = """CREATE DATABASE {};"""

INSERT_NEW_MIGRATION: LiteralString = """
                    INSERT INTO migrations.schemas
                        (name, step, schema, sql_request)
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
                    """

FIND_MIGRATION: LiteralString = """
                    SELECT name, step FROM migrations.schemas
                        WHERE schema = %s;
                    """

FIND_MAX_VERSION: LiteralString = """
                    SELECT MAX(step) as max_version FROM migrations.schemas
                        WHERE name = %s;
                    """

FIND_MAP: LiteralString = """
                        SELECT step, sql_request
                        FROM migrations.schemas
                        WHERE name = %s
                          AND step > %s
                            AND step <= %s
                        ORDER BY step;
                        """

FIND_MIGRATION_VERSION: LiteralString = """
                    SELECT EXISTS (
                        SELECT 1
                        FROM migrations.schemas
                        WHERE name = %s
                          AND step = %s
                    );
                    """

DISCONNECT_FROM_DB: LiteralString = """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s
                      AND pid <> pg_backend_pid();
                    """

DROP_DATABASE: LiteralString = """DROP DATABASE IF EXISTS {};"""

LOAD_MIGRATION: LiteralString = """INSERT INTO migrations.schemas
                           (id, name, step, schema, sql_request, created_at)
                           VALUES (%s, %s, %s, %s, %s, %s)
                               ON CONFLICT DO NOTHING"""
