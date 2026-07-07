"""Contains postgres connection wrapper"""

from psycopg import connect, Connection, OperationalError
from psycopg_pool import ConnectionPool
from pydantic import PostgresDsn


class PostgresRequester:
    def __init__(self, database_url: str | PostgresDsn) -> None:
        """
        Initializes PostgresRequester with safely close all connections
        and pools before exit of execution

        :param database_url: URL string to connect to Postgres database
        :type database_url: str | PostgresDsn
        """
        if isinstance(database_url, str):
            database_url = PostgresDsn(database_url)

        self._dsn = database_url.encoded_string()

        try:
            with connect(self._dsn, connect_timeout=5) as conn:
                conn.execute("SELECT 1")
        except OperationalError as e:
            raise RuntimeError(f"Failed to connect to database: {e}") from None

        self._pool = ConnectionPool(
            self._dsn, min_size=2, max_size=10, max_idle=300, max_lifetime=3600
        )
        self._no_trigger_pool = ConnectionPool(
            self._dsn, min_size=1, max_size=4, max_idle=300, max_lifetime=3600
        )

    def __del__(self) -> None:
        """
        Close all connections and pools before exit of execution

        :rtype: None
        """
        if hasattr(self, "_pool"):
            self._pool.close()
        if hasattr(self, "_no_trigger_pool"):
            self._no_trigger_pool.close()

    def __repr__(self) -> str:
        """
        Prevent write sensitive data in logs

        :return: Representation of class
        :rtype: str
        """
        return (
            f"<PostgresRequester "
            f"host={self._dsn.split('@')[-1].split('/')[0]} "
            f"password=***>"
        )

    def get_connection(self) -> Connection:
        """
        Get single connection to Postgres database from connection pool

        :return: Postgres connection from pool
        :rtype: Connection
        """
        connection = self._pool.getconn()
        connection.autocommit = True
        return connection
