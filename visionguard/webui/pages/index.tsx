import { useState } from "react";
import { api, DetectResult } from "../lib/api";

const CLASS_OPTIONS = ["surface", "dimension", "color", "missing_component", "none"];

export default function Inspect() {
  const [result, setResult] = useState<DetectResult | null>(null);
  const [imageRef, setImageRef] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [corrected, setCorrected] = useState<Record<number, string>>({});
  const [saved, setSaved] = useState<string | null>(null);

  async function run(fn: () => Promise<DetectResult>) {
    setBusy(true);
    setErr(null);
    setSaved(null);
    setCorrected({});
    try {
      setResult(await fn());
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function submit(verdict: string) {
    if (!result) return;
    const boxes = result.detections.map((d, i) => ({
      class_name: corrected[i] ?? d.class_name,
      bbox: d.bbox,
    }));
    try {
      const r = await api.correct({
        detection_id: result.detection_id,
        verdict,
        corrected_boxes: verdict === "confirm" ? [] : boxes,
      });
      setSaved(`Logged correction #${r.correction_id} (${verdict}).`);
    } catch (e) {
      setErr(String(e));
    }
  }

  return (
    <>
      <h1>Defect Inspection</h1>

      <div className="card">
        <div className="row">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) run(() => api.detectFile(f));
            }}
          />
          <span className="muted">or</span>
          <input
            type="text"
            placeholder="minio://defects/P-000931.png"
            value={imageRef}
            onChange={(e) => setImageRef(e.target.value)}
            style={{ minWidth: 280 }}
          />
          <button
            className="secondary"
            disabled={busy || !imageRef}
            onClick={() => run(() => api.detectRef(imageRef))}
          >
            Detect by ref
          </button>
        </div>
        {busy && <p className="muted">Running inference…</p>}
        {err && <p style={{ color: "var(--bad)" }}>{err}</p>}
      </div>

      {result && (
        <>
          <div className="row">
            <span className="badge">model: {result.model}</span>
            {!result.using_custom_model && (
              <span className="badge warn">
                fallback model — train + deploy a real one
              </span>
            )}
            <span
              className="badge"
              style={{ color: result.meets_latency_target ? "var(--good)" : "var(--bad)" }}
            >
              {result.latency_ms} ms
            </span>
          </div>

          <h2>Explainability (CAM heatmap)</h2>
          {result.heatmap ? (
            <img className="heatmap" src={result.heatmap} alt="CAM heatmap" />
          ) : (
            <p className="muted">
              No heatmap (EigenCAM unavailable — model backbone layer could not be
              hooked).
            </p>
          )}

          <h2>Detections — verify or correct</h2>
          {result.detections.length === 0 && (
            <p className="muted">No defects detected (pass).</p>
          )}
          {result.detections.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Model says</th>
                  <th>Confidence</th>
                  <th>Corrected label</th>
                </tr>
              </thead>
              <tbody>
                {result.detections.map((d, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td>{d.class_name}</td>
                    <td>{(d.confidence * 100).toFixed(1)}%</td>
                    <td>
                      <select
                        value={corrected[i] ?? d.class_name}
                        onChange={(e) =>
                          setCorrected({ ...corrected, [i]: e.target.value })
                        }
                      >
                        {CLASS_OPTIONS.map((c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div className="row" style={{ marginTop: 16 }}>
            <button onClick={() => submit("confirm")}>✓ Confirm correct</button>
            <button className="secondary" onClick={() => submit("correct")}>
              Submit corrections
            </button>
            <button className="secondary" onClick={() => submit("reject")}>
              ✗ Reject (false detection)
            </button>
          </div>
          {saved && <p style={{ color: "var(--good)" }}>{saved}</p>}

          {result.similar_defects.length > 0 && (
            <>
              <h2>Similar past defects</h2>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Class</th>
                    <th>Similarity</th>
                    <th>When</th>
                  </tr>
                </thead>
                <tbody>
                  {result.similar_defects.map((s) => (
                    <tr key={s.id}>
                      <td>{s.id}</td>
                      <td>{s.top_class}</td>
                      <td>{(s.similarity * 100).toFixed(1)}%</td>
                      <td>{s.created_at?.slice(0, 19).replace("T", " ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </>
      )}
    </>
  );
}
