import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MRRWaterfallMonth } from "../types";

function formatMonth(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

function formatUSD(n: number) {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const p = payload[0];
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-title">{label}</div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-swatch" style={{ background: "var(--brand)" }} />
        <span className="chart-tooltip-name">Ending MRR</span>
        <span className="chart-tooltip-value">{formatUSD(p.value)}</span>
      </div>
    </div>
  );
}

export function EndingMRRChart({ data }: { data: MRRWaterfallMonth[] }) {
  const chartData = data.map((d) => ({ ...d, monthLabel: formatMonth(d.month_start) }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
        <defs>
          <linearGradient id="mrrFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--brand)" stopOpacity={0.35} />
            <stop offset="100%" stopColor="var(--brand)" stopOpacity={0.02} />
          </linearGradient>
        </defs>
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
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: "var(--axis-line)" }} />
        <Area
          type="monotone"
          dataKey="ending_mrr"
          stroke="var(--brand)"
          strokeWidth={2}
          fill="url(#mrrFill)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
