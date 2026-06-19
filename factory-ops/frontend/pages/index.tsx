import { useEffect, useState } from "react";
import { api, OEELine, DowntimeCat } from "../lib/api";

function pct(x: number) {
  return `${(x * 100).toFixed(1)}%`;
}
function color(x: number) {
  if (x >= 0.7) return "var(--good)";
  if (x >= 0.5) return "var(--warn)";
  return "var(--bad)";
}

function Bar({ value }: { value: number }) {
  return (
    <div className="bar">
      <span style={{ width: pct(value), background: color(value) }} />
    </div>
  );
}

export default function Dashboard() {
  const [oee, setOee] = useState<OEELine[]>([]);
  const [downtime, setDowntime] = useState<DowntimeCat[]>([]);
  const [defects, setDefects] = useState<any[]>([]);
  const [bottleneck, setBottleneck] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.oee(), api.downtime(), api.defects(), api.bottleneck()])
      .then(([o, d, q, b]) => {
        setOee(o.lines);
        setDowntime(d.by_category);
        setDefects(q.defects);
        setBottleneck(b.bottleneck_line);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  if (err)
    return (
      <p>
        Could not reach API ({err}). Is <code>docker compose up</code> running?
      </p>
    );

  return (
    <>
      <h1>Operational Dashboard</h1>

      {bottleneck && (
        <p>
          <span className="badge">BOTTLENECK</span> {bottleneck.line_id} is
          limiting throughput at <strong>{pct(bottleneck.oee)}</strong> OEE.
        </p>
      )}

      <h2>OEE by line</h2>
      <div className="grid">
        {oee.map((l) => (
          <div className="card" key={l.line_id}>
            <div className="line">{l.line_id}</div>
            <div className="oee" style={{ color: color(l.oee) }}>
              {pct(l.oee)}
            </div>
            <Bar value={l.availability} />
            <div className="metric-row">
              <span>Availability</span>
              <span>{pct(l.availability)}</span>
            </div>
            <Bar value={l.performance} />
            <div className="metric-row">
              <span>Performance</span>
              <span>{pct(l.performance)}</span>
            </div>
            <Bar value={l.quality} />
            <div className="metric-row">
              <span>Quality</span>
              <span>{pct(l.quality)}</span>
            </div>
            <div className="metric-row" style={{ marginTop: 12 }}>
              <span>Good / total</span>
              <span>
                {l.good_qty} / {l.total_qty}
              </span>
            </div>
          </div>
        ))}
      </div>

      <h2>Downtime by category</h2>
      <table>
        <thead>
          <tr>
            <th>Line</th>
            <th>Category</th>
            <th>Type</th>
            <th>Events</th>
            <th>Minutes</th>
          </tr>
        </thead>
        <tbody>
          {downtime.map((d, i) => (
            <tr key={i}>
              <td>{d.line_id}</td>
              <td>{d.category}</td>
              <td>{d.planned ? "planned" : "unplanned"}</td>
              <td>{d.events}</td>
              <td>{d.minutes}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Top defects</h2>
      <table>
        <thead>
          <tr>
            <th>Line</th>
            <th>Defect type</th>
            <th>Count</th>
          </tr>
        </thead>
        <tbody>
          {defects.map((d, i) => (
            <tr key={i}>
              <td>{d.line_id}</td>
              <td>{d.defect_type}</td>
              <td>{d.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
