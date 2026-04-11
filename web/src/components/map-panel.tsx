"use client";

import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import { Map as MapIcon } from "lucide-react";

import type { RoadSegment } from "@/lib/types";

type Props = {
  segments: RoadSegment[];
  active: RoadSegment | null;
  center: [number, number];
  onSelect: (seg: RoadSegment) => void;
};

function segmentColor(seg: RoadSegment, isActive: boolean): string {
  if (isActive) return "#22d3ee";
  return "#64748b";
}

export default function MapPanel({ segments, active, center, onSelect }: Props) {
  const zoom = useMemo(() => (active ? 15 : 13), [active]);
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      zoomControl: true,
      attributionControl: true,
    }).setView(center, zoom);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    mapRef.current = map;
  }, [center, zoom]);

  useEffect(() => {
    mapRef.current?.setView(center, zoom, { animate: true });
  }, [center, zoom]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (layerRef.current) {
      layerRef.current.remove();
    }

    const layer = L.layerGroup();

    segments.forEach((seg) => {
      if (!seg.shape || seg.shape.length < 2) return;

      const latlngs: L.LatLngExpression[] = seg.shape.map((p) => [p.lat, p.lng]);
      const isActive = active?.segment_index === seg.segment_index;

      const polyline = L.polyline(latlngs, {
        color: segmentColor(seg, isActive),
        weight: isActive ? 6 : 3,
        opacity: isActive ? 1 : 0.7,
      });

      polyline.bindPopup(
        `<div style="min-width:180px">
          <div style="font-weight:600;margin-bottom:4px">${seg.name || `Segment #${seg.segment_index}`}</div>
          <div style="opacity:.75;font-size:12px">Index: ${seg.segment_index}</div>
        </div>`,
      );

      polyline.on("click", () => onSelect(seg));
      polyline.addTo(layer);
    });

    layer.addTo(map);
    layerRef.current = layer;

    return () => {
      layer.remove();
    };
  }, [segments, active, onSelect]);

  return (
    <section className="relative h-full overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur">
      <div className="absolute left-4 top-4 z-[500] inline-flex items-center gap-2 rounded-xl border border-white/10 bg-zinc-950/70 px-3 py-2 text-xs text-zinc-200 backdrop-blur">
        <MapIcon className="h-4 w-4 text-cyan-300" />
        {segments.length} road segments
      </div>
      <div ref={containerRef} className="h-full w-full" />
    </section>
  );
}
