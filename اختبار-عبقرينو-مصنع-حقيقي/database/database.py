from pathlib import Path
import sqlite3

DATABASE = Path(__file__).resolve().parent / "app.db"
SCHEMA = Path(__file__).resolve().parent / "schema.sql"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize():
    schema = SCHEMA.read_text(encoding="utf-8")

    with get_connection() as connection:
        connection.executescript(schema)
        connection.commit()

    return DATABASE


if __name__ == "__main__":
    path = initialize()
    print(f"Database initialized: {path}")
