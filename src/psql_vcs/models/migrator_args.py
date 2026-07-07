"""Contains Args classes, used for connect main Migrator class to databases
"""

from ipaddress import IPv4Address
from pydantic import PostgresDsn
from dataclasses import dataclass


@dataclass
class AuthArgs:
    """
    Describe Authorize arguments to connect
    
    :param target_database: Database to get schema or make migrations
    :type target_database: str
    
    :param target_server_host: IP address of server with target database
    :type target_server_host: str | IPv4Address
    
    :param target_server_port: Port of server with target database
    :type target_server_port: int
    
    :param target_server_username: Username of server with target database
    :type target_server_username: str
    
    :param target_server_password: Password of server with target database
    :type target_server_password: str
    
    :param target_server_main_database: Main database of server with target database to create 
    :type target_server_main_database: str | None = None
    target database if not exists

    :param migration_server_host: IP address of server with migrations database
    :type migration_server_host: str | IPv4Address | None = None

    :param migration_server_port: Port of server with migrations database
    :type migration_server_port: int | None = None

    :param migration_server_username: Username of server with migrations database
    :type migration_server_username: str | None = None

    :param migration_server_password: Password of server with migrations database
    :type migration_server_password: str | None = None

    :param migration_server_main_database: Main database of server with migrations database to create
    :type migration_server_main_database: str | None = None
    migrations database if not exists

    :param migration_server_migrations_database: Database with migrations
    :type migration_server_migrations_database: str | None = None

    :param migration_server_test_database: Database to restore migrations chain,
    :type migration_server_test_database: str | None = None
     to find diff with current target database schemas

    :param migration_name: Tag to specify grouped chain of migrations
    :type migration_name: str | None = None
    """
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

    def __post_init__(self) -> None:
        """
        Set default values for arguments

        :rtype: None
        """
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

    def __repr__(self) -> str:
        """
        Prevent write sensitive data in logs

        :return: Representation of class
        :rtype: str
        """
        return f'<AuthArgs {id(self)}>'


@dataclass
class URLArgs:
    """
    Describe URL arguments to connect

    :param target_database_url: Database url to get schema or make migrations
    :type target_database_url: str | PostgresDsn

    :param migrations_database_url: Database url for database with migrations
    :type migrations_database_url: str | PostgresDsn | None = None

    :param migrations_main_database_url: Main database url of server with migrations database to create
    :type migrations_main_database_url: str | PostgresDsn | None = None
     migrations database if not exists

    :param migration_server_test_database: Database url to restore migrations chain,
    :type migration_server_test_database: str | None = None
     to find diff with current target database schemas

    :param target_server_main_database_url: Main database url of server with target database to create
    :type target_server_main_database_url: str | PostgresDsn | None = None
    target database if not exists

    :param migration_name: Tag to specify grouped chain of migrations
    :type migration_name: str | None = None
    """
    target_database_url: str | PostgresDsn
    migrations_database_url: str | PostgresDsn | None = None
    migrations_main_database_url: str | PostgresDsn | None = None
    migration_server_test_database: str | None = None
    target_server_main_database_url: str | PostgresDsn | None = None
    migration_name: str | None = None

    def __post_init__(self) -> None:
        """
        Set default values for arguments

        :rtype: None
        """
        if self.migration_name is None:
            dsn = PostgresDsn(self.target_database_url) \
                if isinstance(self.target_database_url, str) else self.target_database_url
            self.migration_name = dsn.path.lstrip('/')

        if type(self.target_database_url) is str:
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

    def __repr__(self) -> str:
        """
        Prevent write sensitive data in logs

        :return: Representation of class
        :rtype: str
        """
        return f'<URLArgs {id(self)}>'
