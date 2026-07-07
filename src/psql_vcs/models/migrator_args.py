"""Contains Args classes, used for connect main Migrator class
to databases
"""

from ipaddress import IPv4Address
from typing import Any
from pydantic import PostgresDsn, BaseModel, field_validator, ValidationError


class AuthArgs(BaseModel):
    def __init__(self, target_database: str,
                 target_server_host: str | IPv4Address,
                 target_server_port: int,
                 target_server_username: str,
                 target_server_password: str,
                 target_server_main_database: str | None = None,
                 migration_server_host: str | IPv4Address | None = None,
                 migration_server_port: int | None = None,
                 migration_server_username: str | None = None,
                 migration_server_password: str | None = None,
                 migration_server_main_database: str | None = None,
                 migration_server_migrations_database: str | None = None,
                 migration_server_test_database: str | None = None,
                 migration_name: str | None = None, **data: Any) -> None:
        """
        Describe Authorize arguments to connect

        :param target_database: Database to get schema or make migrations
        :type target_database: str

        :param target_server_host: IP address of server with target database
        :type target_server_host: str | IPv4Address

        :param target_server_port: Port of server with target database
        :type target_server_port: int

        :param target_server_username: Username of server with
        target database
        :type target_server_username: str

        :param target_server_password: Password of server with
        target database
        :type target_server_password: str

        :param target_server_main_database: Main database of server with
        target database to create target database if not exists
        :type target_server_main_database: str | None = None

        :param migration_server_host: IP address of server with
        migrations database
        :type migration_server_host: str | IPv4Address | None = None

        :param migration_server_port: Port of server with
        migrations database
        :type migration_server_port: int | None = None

        :param migration_server_username: Username of server with
        migrations database
        :type migration_server_username: str | None = None

        :param migration_server_password: Password of server with
        migrations database
        :type migration_server_password: str | None = None

        :param migration_server_main_database: Main database of server
        with migrations database to create migrations database if not exists
        :type migration_server_main_database: str | None = None

        :param migration_server_migrations_database: Database
        with migrations
        :type migration_server_migrations_database: str | None = None

        :param migration_server_test_database: Database to restore
        migrations chain to find diff with current target database schemas
        :type migration_server_test_database: str | None = None

        :param migration_name: Tag to specify grouped chain of migrations
        :type migration_name: str | None = None
        """
        super().__init__(**data)

        self.target_database = target_database
        self._target_server_host = target_server_host
        self.target_server_port = target_server_port
        self.target_server_username = target_server_username
        self.target_server_password = target_server_password
        self._target_server_main_database = target_server_main_database
        self._migration_server_host = migration_server_host
        self._migration_server_port = migration_server_port
        self._migration_server_username = migration_server_username
        self._migration_server_password = migration_server_password
        self._migration_server_main_database = (
            migration_server_main_database)
        self._migration_server_migrations_database = (
            migration_server_migrations_database)
        self._migration_server_test_database = (
            migration_server_test_database)
        self._migration_name = migration_name

    @field_validator(
        '_target_server_host',
        '_migration_server_host',
    )
    @classmethod
    def _validate_host(cls, v: str | IPv4Address) -> str:
        if isinstance(v, str):
            IPv4Address(v)
        return v.__str__()

    @property
    def target_server_host(self) -> str:
        return self._target_server_host.__str__()

    @property
    def migration_name(self) -> str:
        if self._migration_name is None:
            return self.target_database
        else:
            return self._migration_name

    @property
    def migration_server_host(self) -> str:
        if self._migration_server_host is None:
            return self.target_server_host
        elif isinstance(self._migration_server_host, IPv4Address):
            return self._migration_server_host.__str__()
        else:
            return self._migration_server_host

    @property
    def migration_server_port(self) -> int:
        if self._migration_server_port is None:
            return self.target_server_port
        else:
            return self._migration_server_port

    @property
    def migration_server_username(self) -> str:
        if self._migration_server_username is None:
            return self.target_server_username
        else:
            return self._migration_server_username

    @property
    def migration_server_password(self) -> str:
        if self._migration_server_password is None:
            return self.target_server_password
        else:
            return self._migration_server_password

    @property
    def migration_server_main_database(self) -> str:
        if self._migration_server_main_database is None:
            return 'postgres'
        else:
            return self._migration_server_main_database

    @property
    def migration_server_migrations_database(self) -> str:
        if self._migration_server_migrations_database is None:
            return 'psql_vcs_migrations_db'
        else:
            return self._migration_server_migrations_database

    @property
    def migration_server_test_database(self) -> str:
        if self._migration_server_test_database is None:
            return 'psql_vcs_test_db'
        else:
            return self._migration_server_test_database

    @property
    def target_server_main_database(self) -> str:
        if self._target_server_main_database is None:
            return 'postgres'
        else:
            return self._target_server_main_database

    def __repr__(self) -> str:
        """
        Prevent write sensitive data in logs

        :return: Representation of class
        :rtype: str
        """
        return f'<AuthArgs {id(self)}>'


class URLArgs(BaseModel):
    def __init__(self, target_database_url: str,
                 migrations_database_url: str | None = None,
                 migrations_main_database_url: str | None = None,
                 migration_server_test_database: str | None = None,
                 target_server_main_database_url: str | None = None,
                 migration_name: str | None = None,
                 **data: Any) -> None:
        """
        Describe URL arguments to connect

        :param target_database_url: Database url to get schema or
        make migrations
        :type target_database_url: str

        :param migrations_database_url: Database url for database
        with migrations
        :type migrations_database_url: str | None = None

        :param migrations_main_database_url: Main database url of server
        with migrations database to create migrations database if not exists
        :type migrations_main_database_url: str | None = None

        :param migration_server_test_database: Database name to restore
        migrations chain, to find diff with current target database schemas
        :type migration_server_test_database: str | None = None

        :param target_server_main_database_url: Main database url of server
        with target database to create target database if not exists
        :type target_server_main_database_url: str | None = None


        :param migration_name: Tag to specify grouped chain of migrations
        :type migration_name: str | None = None
        """
        super().__init__(**data)
        self._target_database_url = target_database_url
        self._migrations_database_url = migrations_database_url
        self._migrations_main_database_url = migrations_main_database_url
        self._migration_server_test_database = migration_server_test_database
        self._target_server_main_database_url = target_server_main_database_url
        self._migration_name = migration_name

    @field_validator('_target_database_url',
                     '_migrations_database_url',
                     '_migrations_main_database_url',
                     '_target_server_test_database'
                     )
    @classmethod
    def _validate_pg_url(cls, v: str) -> str:
        dsn = PostgresDsn(v)
        if dsn.path is None:
            raise ValidationError('Database name is required')
        return v

    @property
    def dsn_target_database(self) -> PostgresDsn:
        return PostgresDsn(self._target_database_url)

    @property
    def dsn_migrations_database(self) -> PostgresDsn:
        return PostgresDsn(self.migrations_database_url)

    @property
    def dsn_migration_main_database(self) -> PostgresDsn:
        return PostgresDsn(self.migrations_main_database_url)

    @property
    def dsn_migrations_test_database(self) -> PostgresDsn:
        return PostgresDsn(self.migrations_test_database_url)

    @property
    def dsn_target_main_database(self) -> PostgresDsn:
        return PostgresDsn(self.target_server_main_database_url)

    @property
    def target_database(self) -> str:
        path = self.dsn_target_database.path
        if path is None:
            raise ValidationError('Database name is required')
        return path

    @property
    def migration_name(self) -> str:
        if self._migration_name is None:
            return self.target_database.lstrip('/')
        else:
            return self._migration_name

    @property
    def migrations_test_database_url(self) -> str:
        return PostgresDsn(
            self._target_database_url.replace(
                self.target_database, '/psql_vcs_test_db'
                if self._migration_server_test_database is None
                else '/' + self._migration_server_test_database
            )
        ).encoded_string()

    @property
    def migrations_database_url(self) -> str:
        if self._migrations_database_url is None:
            return PostgresDsn(
                self._target_database_url.replace(
                    self.target_database,
                    '/psql_vcs_migrations_db'
                )
            ).encoded_string()
        else:
            return self._migrations_database_url

    @property
    def migrations_main_database_url(self) -> str:
        if self._migrations_main_database_url is None:
            return PostgresDsn(
                self._target_database_url.replace(
                    self.target_database, '/postgres'
                )
            ).encoded_string()
        else:
            return self._migrations_main_database_url

    @property
    def target_server_main_database_url(self) -> str:
        if self._target_server_main_database_url is None:
            return PostgresDsn(
                self._target_database_url.replace(
                    self.target_database, '/postgres'
                )
            ).encoded_string()
        else:
            return self._target_server_main_database_url

    def __repr__(self) -> str:
        """
        Prevent write sensitive data in logs

        :return: Representation of class
        :rtype: str
        """
        return f'<URLArgs {id(self)}>'
