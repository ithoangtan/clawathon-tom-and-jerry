from __future__ import annotations

"""MySQL connection factory for the audit and feedback stores."""

import pymysql
import pymysql.cursors


def get_connection() -> pymysql.Connection:
    """Return a new pymysql connection using application settings.

    Caller is responsible for calling ``.close()`` (or using as context manager).
    Uses DictCursor so rows are returned as plain dicts.
    """
    from app.config import get_settings

    cfg = get_settings()
    return pymysql.connect(
        host=cfg.db_host,
        port=cfg.db_port,
        user=cfg.db_user,
        password=cfg.db_password,
        database=cfg.db_name,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def ensure_index(conn: pymysql.Connection, table: str, index_name: str, columns: str) -> None:
    """Create *index_name* on *table* if it doesn't already exist.

    MySQL doesn't support CREATE INDEX IF NOT EXISTS, so we check
    information_schema first.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM information_schema.statistics "
            "WHERE table_schema = DATABASE() AND table_name = %s AND index_name = %s",
            (table, index_name),
        )
        if cur.fetchone()["n"] == 0:
            cur.execute(f"CREATE INDEX {index_name} ON {table} ({columns})")
