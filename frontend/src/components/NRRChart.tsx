import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { NRRMonth } from "../types";

function formatMonth(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload as NRRMonth & { monthLabel: string };
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-title">
        Base {label} → measured {formatMonth(p.measurement_month)}
      </div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-swatch" style={{ background: "var(--brand)" }} />
        <span className="chart-tooltip-name">NRR</span>
        <span className="chart-tooltip-value">{p.nrr_pct.toFixed(1)}%</span>
      </div>
      <div className="chart-tooltip-sub">{p.base_customers} base customers</div>
    </div>
  );
}

export function NRRChart({ data }: { data: NRRMonth[] }) {
  const chartData = data.map((d) => ({ ...d, monthLabel: formatMonth(d.base_month) }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
        <CartesianGrid stroke="var(--grid-line)" vertical={false} />
        <XAxis
          dataKey="monthLabel"
          tick={{ fill: "var(--ink-muted)", fontSize: 11 }}
          axisLine={{ stroke: "var(--axis-line)" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "var(--ink-muted)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `${v}%`}
          domain={[70, 110]}
        />
        <ReferenceLine y={100} stroke="var(--axis-line)" strokeDasharray="3 3" />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="nrr_pct"
          stroke="var(--brand)"
          strokeWidth={2}
          dot={{ r: 3, fill: "var(--brand)" }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
