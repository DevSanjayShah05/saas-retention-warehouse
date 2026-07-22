import type { BenchmarkQueryResult } from "../types";

export function BenchmarkTable({ data }: { data: BenchmarkQueryResult[] }) {
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>Query pattern</th>
            <th>Before (median, 25 runs)</th>
            <th>After (median, 25 runs)</th>
            <th>Speedup</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.name}>
              <td>{row.name}</td>
              <td className="num">{row.before_median_ms.toFixed(4)} ms</td>
              <td className="num">{row.after_median_ms.toFixed(4)} ms</td>
              <td className="num">
                <span
                  className={
                    "benchmark-badge " + (row.speedup_x >= 1.1 ? "benchmark-badge-good" : "benchmark-badge-neutral")
                  }
                >
                  {row.speedup_x.toFixed(2)}x
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
