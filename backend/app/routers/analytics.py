from fastapi import APIRouter, HTTPException, Query

from app.db import query_df
from app.models.schemas import (
    BenchmarkQueryResult,
    CohortRetentionRow,
    LTVCohort,
    MRRWaterfallMonth,
    NRRMonth,
    SummaryKPIs,
)

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/mrr/waterfall", response_model=list[MRRWaterfallMonth])
def mrr_waterfall(
    start: str | None = Query(None, description="YYYY-MM-DD lower bound (inclusive)"),
    end: str | None = Query(None, description="YYYY-MM-DD upper bound (inclusive)"),
):
    sql = "select * from main_analytics.mrr_waterfall_monthly where 1=1"
    params = []
    if start:
        sql += " and month_start >= ?"
        params.append(start)
    if end:
        sql += " and month_start <= ?"
        params.append(end)
    sql += " order by month_start"
    return query_df(sql, params)


@router.get("/cohorts/retention", response_model=list[CohortRetentionRow])
def cohort_retention(
    cohort_month: str | None = Query(None, description="Filter to a single cohort, YYYY-MM-DD"),
    max_month_number: int = Query(24, ge=1, le=48),
):
    sql = "select * from main_analytics.cohort_retention where month_number <= ?"
    params = [max_month_number]
    if cohort_month:
        sql += " and cohort_month = ?"
        params.append(cohort_month)
    sql += " order by cohort_month, month_number"
    return query_df(sql, params)


@router.get("/nrr", response_model=list[NRRMonth])
def nrr_monthly():
    return query_df("select * from main_analytics.nrr_monthly order by base_month")


@router.get("/ltv", response_model=list[LTVCohort])
def ltv_by_cohort():
    return query_df("select * from main_analytics.ltv_by_cohort order by cohort_month")


@router.get("/summary", response_model=SummaryKPIs)
def summary():
    latest = query_df(
        "select month_start, ending_mrr, active_customers, net_new_mrr "
        "from main_analytics.mrr_waterfall_monthly order by month_start desc limit 1"
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No data in warehouse")
    latest = latest[0]

    trailing_12 = query_df(
        "select sum(new_mrr) as new_mrr, sum(churn_mrr) as churn_mrr "
        "from main_analytics.mrr_waterfall_monthly "
        "where month_start >= (select max(month_start) from main_analytics.mrr_waterfall_monthly) - interval 12 month"
    )[0]

    latest_nrr = query_df(
        "select nrr_pct from main_analytics.nrr_monthly order by base_month desc limit 1"
    )
    latest_nrr_pct = latest_nrr[0]["nrr_pct"] if latest_nrr else None

    totals = query_df(
        "select count(distinct customer_id) as total_customers, "
        "count(distinct date_trunc('month', signup_date)) as total_cohorts "
        "from main_marts.dim_customer where is_current"
    )[0]

    return {
        "latest_month": latest["month_start"],
        "ending_mrr": latest["ending_mrr"],
        "active_customers": latest["active_customers"],
        "net_new_mrr_latest_month": latest["net_new_mrr"],
        "latest_nrr_pct": latest_nrr_pct,
        "trailing_12mo_new_mrr": trailing_12["new_mrr"] or 0,
        "trailing_12mo_churn_mrr": trailing_12["churn_mrr"] or 0,
        "total_customers_ever": totals["total_customers"],
        "total_cohorts": totals["total_cohorts"],
    }


# Static, pre-computed benchmark numbers from scripts/benchmark_indexes.py --
# see README "Indexing strategy" section for the full methodology and the
# raw before/after run this is sourced from. Not re-run per-request: it's a
# one-off diagnostic over the warehouse, not a live analytics query.
_BENCHMARK_RESULTS = [
    {"name": "point lookup: single customer's full invoice history", "before_median_ms": 0.6060, "after_median_ms": 0.2287, "speedup_x": 2.65},
    {"name": "point lookup: single customer's current dim row", "before_median_ms": 0.2476, "after_median_ms": 0.2482, "speedup_x": 1.00},
    {"name": "range scan: one cohort's monthly retention rows", "before_median_ms": 0.2442, "after_median_ms": 0.2533, "speedup_x": 0.96},
    {"name": "range scan: one customer's MRR movement history", "before_median_ms": 0.2784, "after_median_ms": 0.1956, "speedup_x": 1.42},
    {"name": "join: invoices x current dim_customer for one industry", "before_median_ms": 1.7279, "after_median_ms": 1.7431, "speedup_x": 0.99},
]


@router.get("/benchmark", response_model=list[BenchmarkQueryResult])
def benchmark():
    return _BENCHMARK_RESULTS
