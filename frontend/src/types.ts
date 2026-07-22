export interface MRRWaterfallMonth {
  month_start: string;
  new_mrr: number;
  expansion_mrr: number;
  contraction_mrr: number;
  reactivation_mrr: number;
  churn_mrr: number;
  net_new_mrr: number;
  ending_mrr: number;
  active_customers: number;
}

export interface CohortRetentionRow {
  cohort_month: string;
  cohort_size: number;
  month_number: number;
  retained_customers: number;
  retention_pct: number;
  retained_mrr: number;
}

export interface NRRMonth {
  base_month: string;
  measurement_month: string;
  base_customers: number;
  base_mrr_total: number;
  retained_mrr_total: number;
  nrr_pct: number;
}

export interface LTVCohort {
  cohort_month: string;
  cohort_size: number;
  avg_observed_revenue_per_customer: number;
  avg_starting_mrr: number;
  blended_monthly_churn_rate: number;
  formulaic_ltv_estimate: number | null;
}

export interface SummaryKPIs {
  latest_month: string;
  ending_mrr: number;
  active_customers: number;
  net_new_mrr_latest_month: number;
  latest_nrr_pct: number | null;
  trailing_12mo_new_mrr: number;
  trailing_12mo_churn_mrr: number;
  total_customers_ever: number;
  total_cohorts: number;
}

export interface BenchmarkQueryResult {
  name: string;
  before_median_ms: number;
  after_median_ms: number;
  speedup_x: number;
}
