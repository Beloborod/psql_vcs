# psql_vcs - PostgreSQL Version Control System
[![English](https://img.shields.io/badge/Language-English-blue)](README.md)
[![Russian](https://img.shields.io/badge/Language-Русский-green)](README.ru-RU.md)

## О проекте
Проект создан для поддержки простой в разработке системы миграции баз данных PostgreSQL.
Библиотека позволяет автоматически отслеживать изменения, создавать SQL-скрипты для миграции и осуществлять миграцию на последнюю версию базы данных, включая создание базы данных, если она не существует.

> [!CAUTION]
> Библиотека основана на [results](https://github.com/djrobstep/results), поэтому сгенерированный SQL-код для миграции наследует проблемы, которые есть или могут быть в этой библиотеке.
---

## Установка
```
pip install psql_vcs
```

---

## Использование
Сначала необходимо создать файлы миграции.

Миграции создаются в базе данных PostgreSQL, что позволяет свободно разделять серверы, где хранится база данных миграций, и серверы, на которых эти миграции применяются.

Подключение к серверу осуществляется путем создания экземпляра одного из двух классов, в зависимости от предпочтительного метода подключения.
Вы можете подключиться, указав хост, порт, имя пользователя и пароль с помощью AuthArgs, или использовать URLArgs для подключения через строку URL со схемой PostgreSQL (например, postgres://login:password@host:port/database).

### Пример инициализации с AuthArgs

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

### Пример инициализации с URLArgs

```python
from psql_vcs import PostgresMigrator, URLArgs

migrator = PostgresMigrator(
    URLArgs(
        target_database_url="postgres://username:password@localhost:5432/my_db"
    )
)
```

### Дополнительные параметры

Вы также можете указать данные для подключения к целевому серверу отдельно.

Также библиотеке иногда необходимо создавать тестовую базу данных, например, для генерации скрипта миграции (для сравнения последней существующей схемы с новой целевой). По умолчанию для этого используется сервер, хранящий записи миграции. Однако, как и подключение к целевой базе данных, это можно указать отдельно.

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

Если вы не указываете конкретные ссылки, используются значения по умолчанию в соответствии со следующими правилами:
- Имя пользователя и пароль берутся из данных целевой базы.

- Имя «основной» базы данных — postgres.

- Имя базы данных с миграциями — psql_vcs_migrations_db.

- Имя базы данных для создания тестовых схем — psql_vcs_test_db (всегда удаляется после использования).

Кроме того, каждый аргумент класса подключения имеет аргумент migration_name: по умолчанию уникальный «ключ», связывающий цепочку миграций, определяется именем базы данных, для которой создаются эти миграции.

Однако, если вы планируете использовать миграции с одной схемой на нескольких серверах, содержащих базы данных с разными именами, но одной и той же схемой, вы можете определить тег для такой цепочки миграций.

---

## Создание миграций
Для создания миграции используйте метод create_migration.

```python
from psql_vcs import PostgresMigrator, URLArgs

migrator = PostgresMigrator(URLArgs("..."))

migrator.create_migration()
```
Если это первый вызов метода для выбранной базы данных/тега (аргумент migration_name), будет создан «нулевой» файл, содержащий код для создания текущей базы данных с нуля.
По сути, единственное отличие заключается в том, что текущий файл миграции будет вызываться при создании базы данных (если база данных не существует при выполнении миграций) и будет служить основным для корректной работы последующих миграций.

---

## Выполнение миграций
Для миграции на последнюю версию используйте метод migrate_to_last_version()
```python
from psql_vcs import PostgresMigrator, URLArgs

migrator = PostgresMigrator(URLArgs("..."))

migrator.migrate_to_last_version()
```
Этот метод сравнивает текущую схему target_base со схемами, хранящимися в списке миграций. Если передан параметр migration_name, будут сравниваться только соответствующие миграции.

Затем будут выполнены соответствующие SQL-команды для обновления базы данных.

---

## Синхронизация миграций между проектами / серверами
Если вы не можете подключиться к серверу, хранящему миграции, с целевого сервера, где выполняется миграция (или наоборот), или если вы хотите разделить архитектуру сохранения и выполнения миграций, вы можете сохранить историю миграций в файл и восстановить ее на нужном сервере.

Для этого сначала сохраните миграции в файл:
```python
from psql_vcs import PostgresMigrator, URLArgs

migrator = PostgresMigrator(URLArgs("..."))

migrator.save_migrations('migrations.pkl')
```
Теперь вы можете перенести этот файл на целевой сервер, синхронизировать его через репозиторий Git и т.д.

И восстановить миграции на целевом сервере для дальнейшего использования:
```python
from psql_vcs import PostgresMigrator, URLArgs

migrator = PostgresMigrator(URLArgs("..."))

migrator.load_migrations('migrations.pkl')
```

---

> [!NOTE]
> Метод load_migrations, как и метод migrate_to_last_version, позволяет постоянно вызывать их, например, при запуске проекта, для поддержания схем базы данных в актуальном состоянии, без возникновения исключений, если миграции уже были восстановлены или база данных уже была приведена к последней версии.