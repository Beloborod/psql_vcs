"""Contains postgres connection wrapper."""

from collections.abc import Iterator
from contextlib import contextmanager

from psycopg import Connection, Cursor, OperationalError, connect
from psycopg.rows import RowFactory, tuple_row
from psycopg_pool import ConnectionPool
from pydantic import PostgresDsn

from ..sql import TRY_CONNECTION


class PostgresRequester:
    def __init__(self, database_url: str | PostgresDsn) -> None:
        """Initializes PostgresRequester with safely close all connections and
        pools before exit of execution.

        :param database_url: URL string to connect to Postgres database
        :type database_url: str | PostgresDsn
        """
        if isinstance(database_url, str):
            database_url = PostgresDsn(database_url)

        self._dsn = database_url.encoded_string()

        try:
            with connect(self._dsn, connect_timeout=5) as conn:
                conn.execute(TRY_CONNECTION)
        except OperationalError as e:
            raise RuntimeError(f"Failed to connect to database: {e}") from None

        self._pool = ConnectionPool(
            self._dsn, min_size=2, max_size=10, max_idle=300, max_lifetime=3600
        )

    def __repr__(self) -> str:
        """Prevent write sensitive data in logs.

        :return: Representation of class
        :rtype: str
        """
        return (
            f"<PostgresRequester "
            f"host={self._dsn.split('@')[-1].split('/')[0]} "
            f"password=***>"
        )

    def close(self) -> None:
        """Closes connection to Postgres.

        :rtype: None
        """
        self._pool.close()

    def __enter__(self) -> "PostgresRequester":
        """Context manager __enter__.

        :return: self
        :rtype: PostgresRequester
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager __exit__.

        :param exc_type: Exception type
        :param exc_val: Exception value
        :param exc_tb: Exception traceback
        :rtype: None
        """
        self.close()

    @contextmanager
    def connection(self) -> Iterator[Connection]:
        """Context manager connection to Postgres.

        :rtype: Iterator[Connection]
        """
        with self._pool.connection() as conn:
            conn.autocommit = True
            yield conn

    @contextmanager
    def cursor(
        self,
        *,
        row_factory: RowFactory = tuple_row,
    ) -> Iterator[Cursor]:
        """Context manager cursor to Postgres.

        :param row_factory: RowFactory instance
        :type row_factory: RowFactory
        :rtype: Iterator[Cursor]
        """
        with self._pool.connection() as conn:
            conn.autocommit = True
            with conn.cursor(row_factory=row_factory) as cursor:
                yield cursor
