# psql_vcs - PostgreSQL Version Control System
[![English](https://img.shields.io/badge/Language-English-blue)](README.md)
[![Russian](https://img.shields.io/badge/Language-Русский-green)](README.ru-RU.md)

## About project
The project was created to support an easy-to-develop PostgreSQL database migration system.
The library allows for automatic change tracking, creation of SQL scripts for migration, and migration to the latest database version, including creating a database if it doesn't exist.

> [!CAUTION]
> Library based on [results](https://github.com/djrobstep/results), so generated SQL code for migration inherits problems that are or may be in this library
---

- [Installation](#installation)
- [Usage](#usage)
  - [AuthArgs](#initialization-example-with-authargs)
  - [URLArgs](#initialization-example-with-urlargs)
  - [Additional](#additional)
- [Create migrations](#create-migrations)
- [Make migrations](#make-migrations)
- [Sync migrations](#sync-migrations-between-projects--servers)
- [Contributing](#contributing)

---

## Installation
```
pip install psql_vcs
```

---

## Usage
Firstly you need to create migration files. 

Migrations are created in a PostgreSQL database, allowing you to freely separate the servers where the migration database is stored and the servers where these migrations are applied.

Connecting to the server is accomplished by instantiating one of two classes, depending on your preferred connection method.
You can connect by specifying the host, port, username, and password using AuthArgs, or use URLArgs to connect via a URL string with the PostgreSQL schema (such as postgres://login:password@host:port/database).

### Initialization example with AuthArgs

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

### Initialization example with URLArgs

```python
from psql_vcs import PostgresMigrator, URLArgs

migrator = PostgresMigrator(
    URLArgs(
        target_database_url="postgres://username:password@localhost:5432/my_db"
    )
)
```

### Additional

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

---

## Create migrations
To create a migration, use the create_migraton method.
```python
from psql_vcs import PostgresMigrator, URLArgs

migrator = PostgresMigrator(URLArgs("..."))

migrator.create_migration()
```
If this is the first method call for the selected database/tag (the migration_name argument), a "zero" file will be created, containing code for creating the current database from scratch.

Essentially, the only difference is that the current migration file will be called when creating the database (if no database exists when running migrations) and will serve as the primary one for the correct operation of subsequent migrations.

---

## Make migrations
To migrate to the latest version, use the migrate_to_last_version method.
```python
from psql_vcs import PostgresMigrator, URLArgs

migrator = PostgresMigrator(URLArgs("..."))

migrator.migrate_to_last_version()
```
The method will compare the current target_base schema with the schemas stored in the migration list. If migration_name is passed, only the corresponding migrations will be compared.

The corresponding SQL commands will then be executed to bring the database up to date.

---

## Sync migrations between projects / servers
If you can't connect to the server storing migrations from the target server where the migration is running (or vice versa), or if you want to separate the architecture of saving and running migrations, you can save the migration history to a file and restore it on the desired server.
To do this, first save the migrations to a file:
```python
from psql_vcs import PostgresMigrator, URLArgs

migrator = PostgresMigrator(URLArgs("..."))

migrator.save_migrations('migrations.pkl')
```
Now you can transfer this file to the target server, sync it via the Git repository, etc.

And restore the migrations on the target server for further use:
```python
from psql_vcs import PostgresMigrator, URLArgs

migrator = PostgresMigrator(URLArgs("..."))

migrator.load_migrations('migrations.pkl')
```

---

> [!NOTE]
> The load_migrations method, like the migrate_to_last_version method, allows you to call them constantly, for example, when starting a project, to bring the database up to date, and will not raise an exception if migrations have already been restored or the database has already been brought to the latest version.

---

## Contributing

When working with a repository, set up a pre-commit to automatically generate code before submitting a pull request.

``` bash
pip install with pre-commit
```

You can use a Makefile to install test dependencies in .venv and run tests.

First, install the dependencies:
``` bash
make prepare
```

Then you can run tests:
``` bash
make test
```

You can also install the current version of a package with change tracking in .venv:
``` bash
make develop
```

And a pre-built package:
``` bash
make build
```
