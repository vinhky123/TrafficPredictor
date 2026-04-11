import type { PredictResponse, RoadSegment } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function fetchSegments(): Promise<RoadSegment[]> {
  if (!API_URL) return [];

  try {
    const res = await fetch(`${API_URL}/api/segments`, {
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) return [];
    return (await res.json()) as RoadSegment[];
  } catch {
    return [];
  }
}

export async function postPredict(
  segmentIndex: number,
): Promise<PredictResponse> {
  if (!API_URL) {
    return { error: "Backend not available" };
  }

  try {
    const res = await fetch(`${API_URL}/api/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ segment_index: segmentIndex }),
      signal: AbortSignal.timeout(5000),
    });

    if (!res.ok) {
      return { error: `HTTP ${res.status}` };
    }

    return (await res.json().catch(() => ({}))) as PredictResponse;
  } catch {
    return { error: "Connection failed" };
  }
}
