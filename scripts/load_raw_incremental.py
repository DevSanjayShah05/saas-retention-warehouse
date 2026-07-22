"""
Cohort & Ledger — incremental raw loader.

Loads the CSVs in data/raw/ into the `raw` schema of the DuckDB warehouse
using MERGE-style upserts keyed on each table's natural/primary key, not a
full-refresh drop-and-reload. This is what the nightly GitHub Actions
workflow calls to simulate a new batch landing from an upstream
source (e.g. a Stripe/Chargebee export) arriving incrementally.

Idempotent: running it twice with unchanged CSVs is a no-op after the first
run (upserts match on PK, nothing changes, 0 rows affected).

Usage:
    python scripts/load_raw_incremental.py [--db path/to/warehouse.duckdb]
"""

import argparse
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DEFAULT_DB = ROOT / "warehouse" / "warehouse.duckdb"

# table_name -> (csv filename, primary key columns)
TABLES = {
    "plans_history": ("plans_history.csv", ["plan_id"]),
    "customers": ("customers.csv", ["customer_id"]),
    "customers_history": ("customers_history.csv", ["customer_id", "version_no"]),
    "subscriptions": ("subscriptions.csv", ["subscription_id"]),
    "plan_changes": ("plan_changes.csv", ["change_id"]),
    "invoices": ("invoices.csv", ["invoice_id"]),
    "payments": ("payments.csv", ["payment_id"]),
    "usage_monthly": ("usage_monthly.csv", ["customer_id", "subscription_id", "usage_month"]),
}


def load_table(con: duckdb.DuckDBPyConnection, table: str, csv_file: str, pk_cols: list[str]) -> dict:
    csv_path = RAW_DIR / csv_file
    stage = f"stage_{table}"

    con.execute(f"CREATE OR REPLACE TEMP TABLE {stage} AS SELECT * FROM read_csv_auto('{csv_path}', header=true)")

    exists = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='raw' AND table_name=?",
        [table],
    ).fetchone()[0]

    if not exists:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS raw")
        con.execute(f"CREATE TABLE raw.{table} AS SELECT * FROM {stage}")
        n = con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]
        return {"table": table, "mode": "initial_load", "rows_after": n, "rows_upserted": n}

    before = con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]

    join_cond = " AND ".join([f"t.{c} = s.{c}" for c in pk_cols])
    # delete-then-insert upsert (DuckDB has no native MERGE in this version)
    con.execute(f"DELETE FROM raw.{table} t USING {stage} s WHERE {join_cond}")
    con.execute(f"INSERT INTO raw.{table} SELECT * FROM {stage}")

    after = con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]
    return {"table": table, "mode": "incremental_upsert", "rows_before": before, "rows_after": after, "rows_upserted": con.execute(f"SELECT count(*) FROM {stage}").fetchone()[0]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    print(f"Loading raw tables into {db_path} ...")
    t0 = time.time()
    results = []
    for table, (csv_file, pk_cols) in TABLES.items():
        r = load_table(con, table, csv_file, pk_cols)
        results.append(r)
        print(f"  {table:20s} [{r['mode']:18s}] rows_after={r['rows_after']:>8,d}")
    con.close()
    print(f"Done in {time.time() - t0:.2f}s")
    return results


if __name__ == "__main__":
    main()
