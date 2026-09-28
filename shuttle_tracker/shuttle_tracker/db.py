"""SQLite helpers. Plain sqlite3 keeps the project easy to explain and debug."""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def db_path():
    return os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "shuttle.db"))


def get_conn():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with open(os.path.join(BASE_DIR, "schema.sql")) as f:
        schema = f.read()
    conn = get_conn()
    conn.executescript(schema)
    conn.commit()
    conn.close()
