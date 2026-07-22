import type {
  BenchmarkQueryResult,
  CohortRetentionRow,
  LTVCohort,
  MRRWaterfallMonth,
  NRRMonth,
  SummaryKPIs,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`Request failed: ${path} (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  summary: () => get<SummaryKPIs>("/api/summary"),
  mrrWaterfall: () => get<MRRWaterfallMonth[]>("/api/mrr/waterfall"),
  cohortRetention: (maxMonthNumber = 12) =>
    get<CohortRetentionRow[]>(`/api/cohorts/retention?max_month_number=${maxMonthNumber}`),
  nrr: () => get<NRRMonth[]>("/api/nrr"),
  ltv: () => get<LTVCohort[]>("/api/ltv"),
  benchmark: () => get<BenchmarkQueryResult[]>("/api/benchmark"),
};
