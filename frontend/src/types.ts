export type LocationItem = {
  name: string;
  description?: string;
  coordinates: { lat: number; lng: number };
};

export type PredictResponse = {
  name?: string | null;
  current?: number;
  predict?: number[] | null;
  error?: string;
};

