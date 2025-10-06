from config.Database import DEFAULT_SQLALCHEMY_URI, build_sqlalchemy_uri


def test_build_sqlalchemy_uri_returns_default_when_config_incomplete():
    uri = build_sqlalchemy_uri({"host": None, "user": None, "password": None, "database": None, "port": 3306})
    assert uri == DEFAULT_SQLALCHEMY_URI


def test_build_sqlalchemy_uri_builds_mysql_string():
    uri = build_sqlalchemy_uri(
        {
            "host": "db",
            "user": "user",
            "password": "secret",
            "database": "app",
            "port": 3306,
        }
    )
    assert uri == "mysql+mysqlconnector://user:secret@db:3306/app"
