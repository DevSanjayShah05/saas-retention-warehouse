import type { LTVCohort } from "../types";

function formatMonth(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

function formatUSD(n: number) {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

export function LTVTable({ data }: { data: LTVCohort[] }) {
  const recent = [...data].slice(-12).reverse();
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>Cohort</th>
            <th>Size</th>
            <th>Observed revenue / customer (to date)</th>
            <th>Starting MRR / customer</th>
            <th>Blended churn / mo</th>
            <th>Formulaic LTV estimate</th>
          </tr>
        </thead>
        <tbody>
          {recent.map((row) => (
            <tr key={row.cohort_month}>
              <td>{formatMonth(row.cohort_month)}</td>
              <td className="num">{row.cohort_size}</td>
              <td className="num">{formatUSD(row.avg_observed_revenue_per_customer)}</td>
              <td className="num">{formatUSD(row.avg_starting_mrr)}</td>
              <td className="num">{(row.blended_monthly_churn_rate * 100).toFixed(2)}%</td>
              <td className="num">{row.formulaic_ltv_estimate ? formatUSD(row.formulaic_ltv_estimate) : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
