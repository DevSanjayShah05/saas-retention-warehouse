"""
Cohort & Ledger — indexing strategy benchmark.

Measures real before/after query latency for the query patterns the
FastAPI backend actually runs (cohort lookups filtered by cohort_month,
customer lookups by customer_id, invoice lookups by customer_id/date range)
against the DuckDB warehouse, with and without indexes on the marts.

DuckDB is a columnar OLAP engine -- it doesn't need B-tree indexes for the
big analytical scans that already run as single-pass aggregations over
in-memory columnar data (those are fast regardless). Where indexes *do* help
is point/range lookups on a dimension's natural key, which is the access
pattern the API's per-customer and per-cohort endpoints use. This script
measures exactly that, honestly -- including cases where the index makes
little difference, which is itself useful documented signal.

Usage:
    python scripts/benchmark_indexes.py [--db path/to/warehouse.duckdb]
"""

import argparse
import shutil
import statistics
import tempfile
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "warehouse" / "warehouse.duckdb"

N_RUNS = 25

QUERIES = [
    (
        "point lookup: single customer's full invoice history",
        """
        select invoice_id, invoice_date, amount_due, amount_paid
        from main_marts.fact_invoices
        where customer_id = 'CUST-01500'
        order by invoice_date
        """,
    ),
    (
        "point lookup: single customer's current dim row",
        """
        select customer_id, industry, employee_band, is_current
        from main_marts.dim_customer
        where customer_id = 'CUST-01500' and is_current = true
        """,
    ),
    (
        "range scan: one cohort's monthly retention rows",
        """
        select cohort_month, month_number, retention_pct
        from main_analytics.cohort_retention
        where cohort_month = date '2024-03-01'
        order by month_number
        """,
    ),
    (
        "range scan: one customer's MRR movement history",
        """
        select month_start, mrr, movement_type
        from main_marts.fact_subscription_events
        where customer_id = 'CUST-01500'
        order by month_start
        """,
    ),
    (
        "join: invoices x current dim_customer for one industry",
        """
        select fi.invoice_id, fi.amount_paid
        from main_marts.fact_invoices fi
        inner join main_marts.dim_customer dc
            on dc.customer_id = fi.customer_id and dc.is_current
        where dc.industry = 'Healthcare'
        """,
    ),
]

INDEXES = [
    "create index if not exists idx_fact_invoices_customer_id on main_marts.fact_invoices (customer_id)",
    "create index if not exists idx_dim_customer_customer_id on main_marts.dim_customer (customer_id)",
    "create index if not exists idx_dim_customer_industry on main_marts.dim_customer (industry)",
    "create index if not exists idx_fact_sub_events_customer_id on main_marts.fact_subscription_events (customer_id)",
    "create index if not exists idx_cohort_retention_cohort_month on main_analytics.cohort_retention (cohort_month)",
]


def time_query(con, sql, n=N_RUNS):
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        con.execute(sql).fetchall()
        times.append((time.perf_counter() - t0) * 1000.0)
    return {
        "median_ms": round(statistics.median(times), 4),
        "p95_ms": round(sorted(times)[int(0.95 * len(times)) - 1], 4),
        "min_ms": round(min(times), 4),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    # Benchmark against a scratch copy, never the live warehouse file: the
    # indexes created here are a one-off diagnostic, and dbt's table-rebuild
    # (drop/rename swap) strategy on the next `dbt run` doesn't play well
    # with indexes left sitting on those tables in this DuckDB version.
    # DuckDB bakes the catalog name (derived from the file's basename at the
    # time dbt built it) into every view's compiled SQL, so the scratch copy
    # must keep the same basename as the source file or view lookups
    # ("warehouse.main_marts.foo") won't resolve against the copy's catalog.
    tmp_dir = Path(tempfile.mkdtemp(prefix="cohort_ledger_bench_"))
    scratch_db = tmp_dir / Path(args.db).name
    shutil.copy(args.db, scratch_db)

    con = duckdb.connect(str(scratch_db), read_only=False)

    # cohort_retention is a view; materialize a physical copy so we can index it
    con.execute("drop table if exists main_analytics.cohort_retention_bench")
    con.execute("create table main_analytics.cohort_retention_bench as select * from main_analytics.cohort_retention")
    bench_queries = [
        (name, sql.replace("main_analytics.cohort_retention", "main_analytics.cohort_retention_bench"))
        for name, sql in QUERIES
    ]

    print(f"Benchmarking against {args.db} ({N_RUNS} runs/query)\n")
    print("=" * 78)
    print("BEFORE indexes")
    print("=" * 78)
    before = {}
    for name, sql in bench_queries:
        r = time_query(con, sql)
        before[name] = r
        print(f"  {name:55s} median={r['median_ms']:>8.4f}ms  p95={r['p95_ms']:>8.4f}ms")

    print()
    print("Creating indexes...")
    bench_indexes = [
        ix.replace("main_analytics.cohort_retention", "main_analytics.cohort_retention_bench")
        for ix in INDEXES
    ]
    for ix in bench_indexes:
        con.execute(ix)

    print()
    print("=" * 78)
    print("AFTER indexes")
    print("=" * 78)
    after = {}
    for name, sql in bench_queries:
        r = time_query(con, sql)
        after[name] = r
        delta = before[name]["median_ms"] - r["median_ms"]
        pct = (delta / before[name]["median_ms"] * 100) if before[name]["median_ms"] else 0
        print(f"  {name:55s} median={r['median_ms']:>8.4f}ms  p95={r['p95_ms']:>8.4f}ms  ({pct:+.1f}%)")

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for name in before:
        b, a = before[name]["median_ms"], after[name]["median_ms"]
        pct = ((b - a) / b * 100) if b else 0
        speedup = (b / a) if a else float("inf")
        print(f"  {name:55s} {b:>9.4f}ms -> {a:>9.4f}ms  ({speedup:.2f}x, {pct:+.1f}%)")

    con.close()
    shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
