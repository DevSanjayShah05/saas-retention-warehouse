import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MRRWaterfallMonth } from "../types";

function formatMonth(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

function formatUSD(n: number) {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

const SERIES: { key: keyof MRRWaterfallMonth; label: string; color: string }[] = [
  { key: "new_mrr", label: "New", color: "var(--series-new)" },
  { key: "expansion_mrr", label: "Expansion", color: "var(--series-expansion)" },
  { key: "reactivation_mrr", label: "Reactivation", color: "var(--series-reactivation)" },
  { key: "contraction_mrr", label: "Contraction", color: "var(--series-contraction)" },
  { key: "churn_mrr", label: "Churn", color: "var(--series-churn)" },
];

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-title">{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="chart-tooltip-row">
          <span className="chart-tooltip-swatch" style={{ background: p.color }} />
          <span className="chart-tooltip-name">{p.name}</span>
          <span className="chart-tooltip-value">
            {p.value >= 0 ? "+" : ""}
            {formatUSD(p.value)}
          </span>
        </div>
      ))}
    </div>
  );
}

export function MRRWaterfallChart({ data }: { data: MRRWaterfallMonth[] }) {
  const chartData = data.map((d) => ({
    ...d,
    monthLabel: formatMonth(d.month_start),
  }));

  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }} barCategoryGap={4}>
        <CartesianGrid stroke="var(--grid-line)" vertical={false} />
        <XAxis
          dataKey="monthLabel"
          tick={{ fill: "var(--ink-muted)", fontSize: 11 }}
          axisLine={{ stroke: "var(--axis-line)" }}
          tickLine={false}
          interval={2}
        />
        <YAxis
          tick={{ fill: "var(--ink-muted)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--border)" }} />
        <Legend
          formatter={(value) => <span style={{ color: "var(--ink-secondary)", fontSize: 12 }}>{value}</span>}
          iconType="square"
          iconSize={10}
        />
        {SERIES.map((s) => (
          <Bar key={s.key} dataKey={s.key} name={s.label} stackId="mrr" fill={s.color} radius={0} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
