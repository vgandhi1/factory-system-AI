// Tiny typed client for the FactoryOps API. Reads the base URL from the env the
// dashboard is built/run with (defaults to localhost for `npm run dev`).

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

export interface OEELine {
  line_id: string;
  availability: number;
  performance: number;
  quality: number;
  oee: number;
  downtime_s: number;
  good_qty: number;
  total_qty: number;
}

export interface DowntimeCat {
  line_id: string;
  category: string;
  planned: number;
  events: number;
  minutes: number;
}

export const api = {
  oee: () => get<{ lines: OEELine[] }>("/metrics/oee"),
  downtime: () =>
    get<{ by_category: DowntimeCat[]; by_kind: any[] }>("/metrics/downtime"),
  bottleneck: () => get<any>("/metrics/bottleneck"),
  defects: () => get<{ defects: any[] }>("/metrics/defects"),
  shift: () => get<any>("/shift/summary"),
  chat: async (question: string) => {
    const r = await fetch(`${BASE}/copilot/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!r.ok) throw new Error(`chat -> ${r.status}`);
    return r.json();
  },
};
