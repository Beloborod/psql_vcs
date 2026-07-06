from ipaddress import IPv4Address
from pydantic import PostgresDsn
from dataclasses import dataclass


@dataclass
class AuthArgs:
    target_database: str
    target_server_host: str | IPv4Address
    target_server_port: int
    target_server_username: str
    target_server_password: str
    target_server_main_database: str | None = None
    migration_server_host: str | IPv4Address | None = None
    migration_server_port: int | None = None
    migration_server_username: str | None = None
    migration_server_password: str | None = None
    migration_server_main_database: str | None = None
    migration_server_migrations_database: str | None = None
    migration_server_test_database: str | None = None
    migration_name: str | None = None

    def __post_init__(self):
        if self.migration_name is None:
            self.migration_name = self.target_database

        if self.migration_server_host is None:
            self.migration_server_host = self.target_server_host
        if self.migration_server_port is None:
            self.migration_server_port = self.target_server_port
        if self.migration_server_username is None:
            self.migration_server_username = self.target_server_username
        if self.migration_server_password is None:
            self.migration_server_password = self.target_server_password
        if self.migration_server_main_database is None:
            self.migration_server_main_database = 'postgres'
        if self.migration_server_migrations_database is None:
            self.migration_server_migrations_database = 'psql_vcs_migrations_db'
        if self.migration_server_test_database is None:
            self.migration_server_test_database = 'psql_vcs_test_db'
        if self.target_server_main_database is None:
            self.target_server_main_database = 'postgres'

    def __repr__(self):
        return f'<AuthArgs {id(self)}>'


@dataclass
class URLArgs:
    target_database_url: str | PostgresDsn
    migrations_database_url: str | PostgresDsn | None = None
    migrations_main_database_url: str | PostgresDsn | None = None
    migration_server_test_database: str | None = None
    target_server_main_database_url: str | PostgresDsn | None = None
    migration_name: str | None = None

    def __post_init__(self):
        if self.migration_name is None:
            dsn = PostgresDsn(self.target_database_url) \
                if isinstance(self.target_database_url, str) else self.target_database_url
            self.migration_name = dsn.path

        if self.target_database_url is str:
            self.target_database_url = PostgresDsn(self.target_database_url)

        self.migrations_test_database_url = PostgresDsn(str(self.target_database_url).replace(
            self.target_database_url.path, '/psql_vcs_test_db' if self.migration_server_test_database is None else
            '/' + self.migration_server_test_database))

        if self.migrations_database_url is None:
            self.migrations_database_url = PostgresDsn(str(self.target_database_url).replace(
                self.target_database_url.path, '/psql_vcs_migrations_db'))
        if self.migrations_main_database_url is None:
            self.migrations_main_database_url = PostgresDsn(str(self.target_database_url).replace(
                self.target_database_url.path, '/postgres'))
        if self.target_server_main_database_url is None:
            self.target_server_main_database_url = PostgresDsn(str(self.target_database_url).replace(
                self.target_database_url.path, '/postgres'))

    def __repr__(self):
        return f'<URLArgs {id(self)}>'
