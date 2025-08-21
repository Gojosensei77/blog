import sqlite3
from typing import Any

import click
from flask import current_app, g


def get_database_connection() -> sqlite3.Connection:
    if "db_conn" not in g:
        g.db_conn = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db_conn.row_factory = sqlite3.Row
    return g.db_conn  # type: ignore[return-value]


def close_database_connection(_: Any | None = None) -> None:
    db_conn: sqlite3.Connection | None = g.pop("db_conn", None)
    if db_conn is not None:
        db_conn.close()


SCHEMA_SQL = """
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS feed;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  source_url TEXT UNIQUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE IF NOT EXISTS feed (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT UNIQUE NOT NULL,
  title TEXT,
  etag TEXT,
  modified TEXT,
  last_fetched TIMESTAMP
);
"""


def initialize_database() -> None:
    db_conn = get_database_connection()
    db_conn.executescript(SCHEMA_SQL)
    db_conn.commit()


@click.command("init-db")
def init_db_command() -> None:
    initialize_database()
    click.echo("Initialized the database.")


def init_app(app) -> None:
    app.teardown_appcontext(close_database_connection)
    app.cli.add_command(init_db_command)

    # Best-effort ensure schema pieces exist for running apps without re-init
    with app.app_context():
        db = get_database_connection()
        try:
            cols = [r[1] for r in db.execute("PRAGMA table_info(post)").fetchall()]
            if "source_url" not in cols:
                db.execute("ALTER TABLE post ADD COLUMN source_url TEXT")
                db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_post_source_url ON post(source_url)")
                db.commit()
        except Exception:
            pass
        try:
            db.execute(
                "CREATE TABLE IF NOT EXISTS feed (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE NOT NULL, title TEXT, etag TEXT, modified TEXT, last_fetched TIMESTAMP)"
            )
            db.commit()
        except Exception:
            pass

