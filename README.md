# About project
The project was created to support an easy-to-develop PostgreSQL database migration system.
The library allows for automatic change tracking, creation of SQL scripts for migration, and migration to the latest database version, including creating a database if it doesn't exist.

> [!CAUTION]
> Library based on [results](https://github.com/djrobstep/results), so generated SQL code for migration inherits problems that are or may be in this library

# Installation
```
pip install psql_vcs
```

# Usage
Firstly you need to create migration files. 

Migrations are created in a PostgreSQL database, allowing you to freely separate the servers where the migration database is stored and the servers where these migrations are applied.

Connecting to the server is accomplished by instantiating one of two classes, depending on your preferred connection method.
You can connect by specifying the host, port, username, and password using AuthArgs, or use URLArgs to connect via a URL string with the PostgreSQL schema (such as postgres://login:password@host:port/database).

## Initialization example with AuthArgs

```python
from psql_vcs import PostgresMigrator, AuthArgs

migrator = PostgresMigrator(
    AuthArgs(
        target_server_host='localhost',
        target_server_port=5432,
        target_server_username='username',
        target_server_password='password',
        target_database='my_db'
    )
)
```



## Initialization example with URLArgs

```python
from psql_vcs import PostgresMigrator, URLArgs

migrator = PostgresMigrator(
    URLArgs(
        target_database_url="postgres://username:password@localhost:5432/my_db"
    )
)
```

## Additional

You can also specify connection details for the target database separately.
Also, sometimes you need to create a test database, for example, to generate a migration script (to compare the latest existing schema with the new target). By default, the server storing migration records is used for this. However, like the connection to the target database, this can be specified separately.

```python
from psql_vcs import AuthArgs

args = AuthArgs(
    target_database = "my_db",
    target_server_host = "localhost",
    target_server_port = 5432,
    target_server_username = "username",
    target_server_password = "password",
    target_server_main_database = "postgres",
    migration_server_host = "localhost",
    migration_server_port = 5432,
    migration_server_username = "username",
    migration_server_password = "password",
    migration_server_main_database = "postgres",
    migration_server_migrations_database = "my_migrations",
    migration_server_test_database = "my_test_for_migrations",
    migration_name = "special_tag"
)
```
```python
from psql_vcs import URLArgs

args = URLArgs(
    target_database_url = "postgres://username:password@localhost:5432/my_db",
    migrations_database_url = "postgres://username:password@localhost:5432/my_mirations",
    migrations_main_database_url = "postgres://username:password@localhost:5432/postgres",
    migration_server_test_database = "postgres://username:password@localhost:5432/my_migrations_test",
    target_server_main_database_url = "postgres://username:password@localhost:5432/postgres",
    migration_name = "special_tag"
)
```

If you don't define specific links, default values are used according to the following rules:
- The username and password are taken from the target database.
- The name of the "primary" database is postgres.
- The name of the database with migrations is psql_vcs_migrations_db.
- The name of the database for creating test schemas is psql_vcs_test_db (always deleted after use).

Additionally, each connection argument class has a migration_name argument: by default, the unique "key" linking a migration chain is determined by the name of the database for which these migrations are compiled.
However, if you plan to use migrations with a single schema on multiple servers containing databases with different names but the same schema, you can define a tag for such a migration chain.