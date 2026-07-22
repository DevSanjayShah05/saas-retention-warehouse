import { useEffect, useState } from "react";
import "./App.css";
import { api } from "./api";
import { BenchmarkTable } from "./components/BenchmarkTable";
import { CohortHeatmap } from "./components/CohortHeatmap";
import { EndingMRRChart } from "./components/EndingMRRChart";
import { LTVTable } from "./components/LTVTable";
import { MRRWaterfallChart } from "./components/MRRWaterfallChart";
import { NRRChart } from "./components/NRRChart";
import { StatTile } from "./components/StatTile";
import type {
  BenchmarkQueryResult,
  CohortRetentionRow,
  LTVCohort,
  MRRWaterfallMonth,
  NRRMonth,
  SummaryKPIs,
} from "./types";

function formatUSD(n: number) {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function formatMonth(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

export default function App() {
  const [summary, setSummary] = useState<SummaryKPIs | null>(null);
  const [waterfall, setWaterfall] = useState<MRRWaterfallMonth[]>([]);
  const [cohorts, setCohorts] = useState<CohortRetentionRow[]>([]);
  const [nrr, setNrr] = useState<NRRMonth[]>([]);
  const [ltv, setLtv] = useState<LTVCohort[]>([]);
  const [benchmark, setBenchmark] = useState<BenchmarkQueryResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.summary(), api.mrrWaterfall(), api.cohortRetention(15), api.nrr(), api.ltv(), api.benchmark()])
      .then(([s, w, c, n, l, b]) => {
        setSummary(s);
        setWaterfall(w);
        setCohorts(c);
        setNrr(n);
        setLtv(l);
        setBenchmark(b);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-inner">
          <div>
            <h1 className="brand-title">
              Cohort <span className="brand-amp">&amp;</span> Ledger
            </h1>
            <p className="brand-tagline">A SaaS revenue &amp; retention analytics warehouse.</p>
          </div>
          {summary && (
            <div className="app-header-meta">
              as of <strong>{formatMonth(summary.latest_month)}</strong>
            </div>
          )}
        </div>
      </header>

      <main className="app-main">
        {loading && <div className="state-banner">Loading warehouse…</div>}
        {error && (
          <div className="state-banner state-banner-error">
            Could not reach the API at the configured backend URL. Is the FastAPI server running? ({error})
          </div>
        )}

        {summary && (
          <section className="stat-grid">
            <StatTile label="Ending MRR" value={formatUSD(summary.ending_mrr)} caption="latest month" />
            <StatTile
              label="Net new MRR"
              value={formatUSD(summary.net_new_mrr_latest_month)}
              deltaTone={summary.net_new_mrr_latest_month >= 0 ? "good" : "critical"}
              caption="latest month"
            />
            <StatTile label="Active customers" value={summary.active_customers.toLocaleString()} />
            <StatTile
              label="Net Revenue Retention"
              value={summary.latest_nrr_pct != null ? `${summary.latest_nrr_pct.toFixed(1)}%` : "—"}
              deltaTone={
                summary.latest_nrr_pct != null ? (summary.latest_nrr_pct >= 100 ? "good" : "warning") : "neutral"
              }
              caption="trailing 12mo"
            />
            <StatTile
              label="Trailing 12mo new MRR"
              value={formatUSD(summary.trailing_12mo_new_mrr)}
              deltaTone="good"
            />
            <StatTile
              label="Trailing 12mo churned MRR"
              value={formatUSD(Math.abs(summary.trailing_12mo_churn_mrr))}
              deltaTone="critical"
            />
          </section>
        )}

        <section className="panel">
          <div className="panel-header">
            <h2>MRR waterfall</h2>
            <p>Monthly movement by component — new, expansion, reactivation, contraction, churn.</p>
          </div>
          <MRRWaterfallChart data={waterfall} />
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Ending MRR trend</h2>
            <p>Cumulative recurring revenue, month over month.</p>
          </div>
          <EndingMRRChart data={waterfall} />
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Cohort retention</h2>
            <p>
              % of each signup-month cohort still paying, by months since signup. Cohort denominator includes trial
              signups that never converted — see README methodology.
            </p>
          </div>
          <CohortHeatmap data={cohorts} />
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Net Revenue Retention</h2>
            <p>Trailing 12-month NRR: of the MRR held by a base month's customers, how much survives a year later.</p>
          </div>
          <NRRChart data={nrr} />
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>LTV by cohort</h2>
            <p>
              Observed net revenue-to-date (right-censored for recent cohorts) alongside a formulaic ARPU / churn-rate
              estimate.
            </p>
          </div>
          <LTVTable data={ltv} />
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Indexing strategy — measured benchmark</h2>
            <p>
              Real before/after query latency (25 runs each) on a scratch copy of the warehouse, for the access
              patterns this API actually uses. See README for the full methodology and honest read on where indexes
              do and don't help in a columnar engine.
            </p>
          </div>
          <BenchmarkTable data={benchmark} />
        </section>
      </main>

      <footer className="app-footer">
        Cohort &amp; Ledger — synthetic dataset, fixed seed. Not real customer data. See README for data gaps and
        methodology.
      </footer>
    </div>
  );
}
