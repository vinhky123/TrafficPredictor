"use client";

import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import { Map as MapIcon } from "lucide-react";

import type { LocationItem } from "@/lib/types";

type Props = {
  locations: LocationItem[];
  active: LocationItem | null;
  center: [number, number];
};

const markerIcon = new L.Icon({
  iconUrl:
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24'%3E%3Cpath fill='%2306b6d4' d='M12 2c-3.87 0-7 3.13-7 7c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7m0 9.5a2.5 2.5 0 1 1 0-5a2.5 2.5 0 0 1 0 5'/%3E%3C/svg%3E",
  iconSize: [28, 28],
  iconAnchor: [14, 28],
  popupAnchor: [0, -26],
});

export default function MapPanel({ locations, active, center }: Props) {
  const zoom = useMemo(() => (active ? 14 : 12), [active]);
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

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

    const layer = L.layerGroup();
    locations.forEach((loc) => {
      const marker = L.marker([loc.coordinates.lat, loc.coordinates.lng], {
        icon: markerIcon,
      });
      marker.bindPopup(
        `<div style="min-width:180px">
          <div style="font-weight:600;margin-bottom:4px">${loc.name}</div>
          <div style="opacity:.75;font-size:12px">${loc.description || "Traffic monitoring point"}</div>
        </div>`,
      );
      marker.addTo(layer);
    });
    layer.addTo(map);

    return () => {
      layer.remove();
    };
  }, [locations]);

  return (
    <section className="relative h-full overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur">
      <div className="absolute left-4 top-4 z-[500] inline-flex items-center gap-2 rounded-xl border border-white/10 bg-zinc-950/70 px-3 py-2 text-xs text-zinc-200 backdrop-blur">
        <MapIcon className="h-4 w-4 text-cyan-300" />
        Interactive map
      </div>
      <div ref={containerRef} className="h-full w-full" />
    </section>
  );
}
