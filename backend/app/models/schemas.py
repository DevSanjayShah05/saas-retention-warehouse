from datetime import date

from pydantic import BaseModel


class MRRWaterfallMonth(BaseModel):
    month_start: date
    new_mrr: float
    expansion_mrr: float
    contraction_mrr: float
    reactivation_mrr: float
    churn_mrr: float
    net_new_mrr: float
    ending_mrr: float
    active_customers: int


class CohortRetentionRow(BaseModel):
    cohort_month: date
    cohort_size: int
    month_number: int
    retained_customers: int
    retention_pct: float
    retained_mrr: float


class NRRMonth(BaseModel):
    base_month: date
    measurement_month: date
    base_customers: int
    base_mrr_total: float
    retained_mrr_total: float
    nrr_pct: float


class LTVCohort(BaseModel):
    cohort_month: date
    cohort_size: int
    avg_observed_revenue_per_customer: float
    avg_starting_mrr: float
    blended_monthly_churn_rate: float
    formulaic_ltv_estimate: float | None = None


class SummaryKPIs(BaseModel):
    latest_month: date
    ending_mrr: float
    active_customers: int
    net_new_mrr_latest_month: float
    latest_nrr_pct: float | None
    trailing_12mo_new_mrr: float
    trailing_12mo_churn_mrr: float
    total_customers_ever: int
    total_cohorts: int


class BenchmarkQueryResult(BaseModel):
    name: str
    before_median_ms: float
    after_median_ms: float
    speedup_x: float
