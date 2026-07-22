import { useMemo, useState } from "react";
import type { CohortRetentionRow } from "../types";

const SEQ_STEPS = [
  "var(--seq-100)",
  "var(--seq-150)",
  "var(--seq-200)",
  "var(--seq-250)",
  "var(--seq-300)",
  "var(--seq-350)",
  "var(--seq-400)",
  "var(--seq-450)",
  "var(--seq-500)",
  "var(--seq-550)",
  "var(--seq-600)",
  "var(--seq-650)",
  "var(--seq-700)",
];

function stepForPct(pct: number): number {
  // 0% -> lightest step, 100% -> darkest step
  const idx = Math.round((pct / 100) * (SEQ_STEPS.length - 1));
  return Math.min(SEQ_STEPS.length - 1, Math.max(0, idx));
}

function formatMonth(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

export function CohortHeatmap({ data, maxCohorts = 18 }: { data: CohortRetentionRow[]; maxCohorts?: number }) {
  const [hovered, setHovered] = useState<CohortRetentionRow | null>(null);

  const { cohortMonths, maxMonthNumber, grid, sizeByCohort } = useMemo(() => {
    const months = Array.from(new Set(data.map((d) => d.cohort_month))).sort();
    const recent = months.slice(-maxCohorts);
    const maxMn = Math.max(...data.map((d) => d.month_number), 0);
    const g = new Map<string, Map<number, CohortRetentionRow>>();
    const sizes = new Map<string, number>();
    for (const row of data) {
      if (!recent.includes(row.cohort_month)) continue;
      if (!g.has(row.cohort_month)) g.set(row.cohort_month, new Map());
      g.get(row.cohort_month)!.set(row.month_number, row);
      sizes.set(row.cohort_month, row.cohort_size);
    }
    return { cohortMonths: recent, maxMonthNumber: maxMn, grid: g, sizeByCohort: sizes };
  }, [data, maxCohorts]);

  return (
    <div className="heatmap-wrap">
      <div className="heatmap-scroll">
        <table className="heatmap-table">
          <thead>
            <tr>
              <th className="heatmap-corner">Cohort</th>
              <th className="heatmap-corner-size">Size</th>
              {Array.from({ length: maxMonthNumber + 1 }, (_, i) => (
                <th key={i} className="heatmap-col-head">
                  M{i}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {cohortMonths.map((cm) => (
              <tr key={cm}>
                <td className="heatmap-row-head">{formatMonth(cm)}</td>
                <td className="heatmap-row-size">{sizeByCohort.get(cm)}</td>
                {Array.from({ length: maxMonthNumber + 1 }, (_, mn) => {
                  const cell = grid.get(cm)?.get(mn);
                  if (!cell) {
                    return <td key={mn} className="heatmap-cell heatmap-cell-empty" />;
                  }
                  const step = stepForPct(cell.retention_pct);
                  const textDark = step < 7;
                  return (
                    <td
                      key={mn}
                      className="heatmap-cell"
                      style={{
                        background: SEQ_STEPS[step],
                        color: textDark ? "#0b0b0b" : "#ffffff",
                      }}
                      onMouseEnter={() => setHovered(cell)}
                      onMouseLeave={() => setHovered(null)}
                    >
                      {cell.retention_pct.toFixed(0)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="heatmap-footer">
        <div className="heatmap-legend">
          <span className="heatmap-legend-label">Retention %</span>
          <div className="heatmap-legend-ramp">
            {SEQ_STEPS.map((c, i) => (
              <span key={i} style={{ background: c }} />
            ))}
          </div>
          <span className="heatmap-legend-label">0 → 100</span>
        </div>
        {hovered && (
          <div className="heatmap-hover-detail">
            <strong>{formatMonth(hovered.cohort_month)}</strong> cohort, month {hovered.month_number}:{" "}
            {hovered.retained_customers} / {hovered.cohort_size} retained ({hovered.retention_pct.toFixed(1)}%),{" "}
            {hovered.retained_mrr.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 })}{" "}
            MRR
          </div>
        )}
      </div>
    </div>
  );
}
