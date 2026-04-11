export type RoadSegment = {
  segment_index: number;
  name: string;
  shape: { lat: number; lng: number }[];
};

export type PredictResponse = {
  segment_index?: number;
  name?: string | null;
  current?: number;
  predict?: number[] | null;
  error?: string;
};
