interface StatTileProps {
  label: string;
  value: string;
  delta?: string;
  deltaTone?: "good" | "warning" | "critical" | "neutral";
  caption?: string;
}

const toneColor: Record<string, string> = {
  good: "var(--status-good)",
  warning: "var(--status-warning)",
  critical: "var(--status-critical)",
  neutral: "var(--ink-secondary)",
};

export function StatTile({ label, value, delta, deltaTone = "neutral", caption }: StatTileProps) {
  return (
    <div className="stat-tile">
      <div className="stat-tile-label">{label}</div>
      <div className="stat-tile-value">{value}</div>
      {(delta || caption) && (
        <div className="stat-tile-footer">
          {delta && (
            <span className="stat-tile-delta" style={{ color: toneColor[deltaTone] }}>
              {delta}
            </span>
          )}
          {caption && <span className="stat-tile-caption">{caption}</span>}
        </div>
      )}
    </div>
  );
}
