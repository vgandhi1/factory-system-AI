import { useEffect, useState } from "react";
import { api } from "../lib/api";

export default function ShiftSummary() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.shift().then(setData).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <p>Could not load shift summary ({err}).</p>;
  if (!data) return <p>Loading…</p>;

  return (
    <>
      <h1>Shift Handoff Summary</h1>

      <h2>Narrative</h2>
      <pre className="narrative">{data.narrative}</pre>

      <h2>Action items</h2>
      <ul>
        {data.action_items.map((a: string, i: number) => (
          <li key={i}>{a}</li>
        ))}
      </ul>

      <h2>Production vs target</h2>
      <table>
        <thead>
          <tr>
            <th>Line</th>
            <th>Good</th>
            <th>Scrap</th>
            <th>Target</th>
          </tr>
        </thead>
        <tbody>
          {data.production.map((p: any, i: number) => (
            <tr key={i}>
              <td>{p.line_id}</td>
              <td>{p.good}</td>
              <td>{p.scrap}</td>
              <td>{p.target}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
