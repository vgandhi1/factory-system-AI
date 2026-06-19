import { useEffect, useState } from "react";
import { api } from "../lib/api";

function pct(x: number) {
  return `${(x * 100).toFixed(1)}%`;
}

export default function Trends() {
  const [t, setT] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.trends().then(setT).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <p>Could not load trends ({err}).</p>;
  if (!t) return <p>Loading…</p>;

  return (
    <>
      <h1>Quality Trends</h1>

      <div className="grid">
        <div className="card">
          <div className="muted">First-pass yield</div>
          <div className={`kpi ${t.first_pass_yield >= 0.9 ? "good" : "bad"}`}>
            {pct(t.first_pass_yield)}
          </div>
        </div>
        <div className="card">
          <div className="muted">Scrap rate</div>
          <div className={`kpi ${t.scrap_rate <= 0.1 ? "good" : "bad"}`}>
            {pct(t.scrap_rate)}
          </div>
        </div>
        <div className="card">
          <div className="muted">Total inspected</div>
          <div className="kpi">{t.total_inspected}</div>
        </div>
        <div className="card">
          <div className="muted">Corrections pending retrain</div>
          <div className="kpi">{t.corrections_pending_training}</div>
        </div>
      </div>

      <h2>Defects by type</h2>
      {t.by_class.length === 0 ? (
        <p className="muted">No defects recorded yet. Run some images on the Inspect tab.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Defect type</th>
              <th>Count</th>
            </tr>
          </thead>
          <tbody>
            {t.by_class.map((c: any, i: number) => (
              <tr key={i}>
                <td>{c.defect_type}</td>
                <td>{c.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
