// Client for the VisionGuard inference API.
const BASE =
  process.env.NEXT_PUBLIC_INFERENCE_URL || "http://localhost:8001";

export interface Detection {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: number[];
}

export interface DetectResult {
  detection_id: number;
  model: string;
  using_custom_model: boolean;
  latency_ms: number;
  meets_latency_target: boolean;
  detections: Detection[];
  heatmap: string | null;
  similar_defects: any[];
}

async function jget<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

export const api = {
  detectFile: async (file: File): Promise<DetectResult> => {
    const fd = new FormData();
    fd.append("file", file);
    const r = await fetch(`${BASE}/detect`, { method: "POST", body: fd });
    if (!r.ok) throw new Error(`detect -> ${r.status}`);
    return r.json();
  },
  detectRef: async (image_ref: string): Promise<DetectResult> => {
    const r = await fetch(`${BASE}/detect/ref`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_ref }),
    });
    if (!r.ok) throw new Error(`detect/ref -> ${r.status}`);
    return r.json();
  },
  correct: async (payload: {
    detection_id: number;
    verdict: string;
    inspector?: string;
    corrected_boxes?: any[];
  }) => {
    const r = await fetch(`${BASE}/corrections`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) throw new Error(`corrections -> ${r.status}`);
    return r.json();
  },
  trends: () => jget<any>("/trends"),
  recent: () => jget<{ detections: any[] }>("/detections?limit=20"),
};
