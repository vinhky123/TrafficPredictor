import type { PredictResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function postPredict(
  lat: number,
  lng: number,
): Promise<PredictResponse> {
  if (!API_URL) {
    return { error: "NEXT_PUBLIC_API_URL is not configured (demo mode)." };
  }

  const res = await fetch(`${API_URL}/api/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ location: { lat, lng } }),
  });

  const json = (await res.json().catch(() => ({}))) as PredictResponse;
  if (!res.ok) return { ...json, error: json.error || `HTTP ${res.status}` };
  return json;
}
