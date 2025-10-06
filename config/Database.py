import logging
import os
from contextlib import contextmanager
from typing import Any
from urllib.parse import quote_plus

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()

REQUIRED_KEYS = {"host", "user", "password", "database"}
DEFAULT_SQLALCHEMY_URI = "sqlite:///:memory:"


def get_db_config() -> dict[str, Any]:
    return {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "port": int(os.getenv("DB_PORT", 3306)),
    }


def _config_is_complete(config: dict[str, Any]) -> bool:
    return all(config.get(key) for key in REQUIRED_KEYS)


@contextmanager
def connect_db(config: dict[str, Any]):
    if not _config_is_complete(config):
        logging.info("Database configuration is incomplete; skipping connection attempt.")
        yield None
        return

    logging.info(
        "Attempting to connect to database %s at %s:%s ...",
        config["database"],
        config["host"],
        config["port"],
    )
    conn = None
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            logging.info("Database connection established successfully.")
            yield conn
        else:
            logging.warning("Failed to establish database connection.")
            yield None
    except Error as exc:
        logging.error("Database connection error: %s", exc)
        yield None
    finally:
        if conn and conn.is_connected():
            conn.close()
            logging.info("Database connection closed.")


def check_db_connection(config: dict[str, Any]) -> bool:
    """Return True if a connection can be established, False otherwise."""
    with connect_db(config) as connection:
        return connection is not None


def get_tables(config: dict[str, Any]) -> list[str]:
    """Return a list of tables or an empty list when unavailable."""
    with connect_db(config) as connection:
        if not connection:
            return []
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                return [table[0] for table in cursor.fetchall()]
        except Error as exc:
            logging.error("Error fetching tables: %s", exc)
            return []


def build_sqlalchemy_uri(config: dict[str, Any] | None = None) -> str:
    resolved_config = config or get_db_config()
    if not _config_is_complete(resolved_config):
        return DEFAULT_SQLALCHEMY_URI

    user = resolved_config["user"]
    password = quote_plus(str(resolved_config.get("password", "")))
    host = resolved_config["host"]
    port = resolved_config.get("port", 3306)
    database = resolved_config["database"]
    return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
