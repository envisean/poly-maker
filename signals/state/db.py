"""DuckDB connection + idempotent migration for the signal state store."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import duckdb

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def connect(path: str = "data/state.duckdb", read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open (or create) the state database. Parent dir is created if needed."""
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(path, read_only=read_only)


def init_schema(conn: duckdb.DuckDBPyConnection, schema_sql: Optional[str] = None) -> None:
    """Apply the schema. Idempotent — safe to call on every boot."""
    sql = schema_sql if schema_sql is not None else _SCHEMA_PATH.read_text()
    conn.execute(sql)
