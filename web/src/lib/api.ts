import type { PredictResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function postPredict(
  lat: number,
  lng: number,
): Promise<PredictResponse> {
  if (!API_URL) {
    return { speed: 0, error: "Backend not available" };
  }

  try {
    const res = await fetch(`${API_URL}/api/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ location: { lat, lng } }),
      signal: AbortSignal.timeout(5000),
    });

    if (!res.ok) {
      return { speed: 0, error: `HTTP ${res.status}` };
    }

    const json = (await res.json().catch(() => ({}))) as PredictResponse;
    return json;
  } catch (error) {
    return { speed: 0, error: "Connection failed" };
  }
}
