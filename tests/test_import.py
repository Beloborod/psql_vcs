def test_import_no_crash():
    from psql_vcs import AuthArgs, PostgresMigrator, URLArgs

    try:
        PostgresMigrator(
            URLArgs("postgres://postgres:postgres@localhost/test_db")
        )
        PostgresMigrator(
            AuthArgs("test_db", "localhost", 5432, "postgres", "postgres")
        )
    except Exception:
        pass
