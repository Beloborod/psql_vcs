from ipaddress import IPv4Address
from pydantic import PostgresDsn
from dataclasses import dataclass


@dataclass
class AuthArgs:
    migration_server_host: str | IPv4Address
    migration_server_port: int
    migration_server_username: str
    migration_server_password: str
    target_database: str
    target_server_host: str | IPv4Address | None = None
    target_server_port: int | None = None
    target_server_username: str | None = None
    target_server_password: str | None = None
    migration_server_main_database: str | None = None
    migration_server_migrations_database: str | None = None
    migration_server_test_database: str | None = None
    target_server_main_database: str | None = None
    migration_name: str | None = None

    def __post_init__(self):
        if self.target_server_host is None:
            self.target_server_host = self.migration_server_host
        if self.target_server_port is None:
            self.target_server_port = self.migration_server_port
        if self.target_server_username is None:
            self.target_server_username = self.migration_server_username
        if self.target_server_password is None:
            self.target_server_password = self.migration_server_password
        if self.migration_server_main_database is None:
            self.migration_server_main_database = 'postgres'
        if self.migration_server_migrations_database is None:
            self.migration_server_migrations_database = 'psql_vcs_migrations_db'
        if self.migration_server_test_database is None:
            self.migration_server_test_database = 'psql_vcs_test_db'
        if self.target_server_main_database is None:
            self.target_server_main_database = self.migration_server_main_database
        if self.migration_name is None:
            self.migration_name = self.target_database

    def __repr__(self):
        return f"<AuthArgs {id(self)}>"


@dataclass
class URLArgs:
    migrations_main_database_url: str | PostgresDsn
    migrations_database_url: str | PostgresDsn
    migrations_test_database_url: str | PostgresDsn
    target_database_url: str | PostgresDsn
    target_server_main_database_url: str | PostgresDsn
    migration_name: str | None = None

    def __post_init__(self):
        if self.migration_name is None:
            dsn = PostgresDsn(self.target_database_url) \
                if isinstance(self.target_database_url, str) else self.target_database_url
            self.migration_name = dsn.path

    def __repr__(self):
        return f"<URLArgs {id(self)}>"
