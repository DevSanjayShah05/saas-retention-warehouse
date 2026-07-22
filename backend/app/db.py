"""
Read-only connection to the DuckDB warehouse built by warehouse/ (dbt).

The backend never computes analytics in Python -- every number returned by
the API comes straight out of a SQL view/query against the marts/analytics
schemas that dbt built. This module just owns the connection.
"""

from pathlib import Path
import os

import duckdb

_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "warehouse" / "warehouse.duckdb"
DB_PATH = Path(os.environ.get("WAREHOUSE_DB_PATH", _DEFAULT_DB_PATH))

_connection: duckdb.DuckDBPyConnection | None = None


def get_connection() -> duckdb.DuckDBPyConnection:
    global _connection
    if _connection is None:
        if not DB_PATH.exists():
            raise FileNotFoundError(
                f"Warehouse DuckDB file not found at {DB_PATH}. "
                "Run `python scripts/load_raw_incremental.py` and `dbt build` "
                "(from warehouse/) first, per the README setup instructions."
            )
        _connection = duckdb.connect(str(DB_PATH), read_only=True)
    return _connection


def query_df(sql: str, params: list | None = None):
    """Run a SQL query against the warehouse and return a pandas-free list of dict rows."""
    con = get_connection()
    cursor = con.execute(sql, params or [])
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(cols, row)) for row in rows]
