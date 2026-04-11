"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { Activity, MapPin, Zap } from "lucide-react";

import { Sidebar } from "@/components/sidebar";
import { fetchSegments } from "@/lib/api";
import type { RoadSegment } from "@/lib/types";

const MapPanel = dynamic(() => import("@/components/map-panel"), {
  ssr: false,
  loading: () => (
    <div className="grid h-full place-items-center rounded-2xl border border-white/10 bg-white/5 text-sm text-zinc-400">
      Loading map…
    </div>
  ),
});

const HCMC_CENTER: [number, number] = [10.776889, 106.695278];

export default function Home() {
  const [segments, setSegments] = useState<RoadSegment[]>([]);
  const [active, setActive] = useState<RoadSegment | null>(null);

  useEffect(() => {
    fetchSegments().then(setSegments).catch(() => setSegments([]));
  }, []);

  const center = useMemo<[number, number]>(() => {
    if (!active || !active.shape.length) return HCMC_CENTER;
    const lats = active.shape.map((p) => p.lat);
    const lngs = active.shape.map((p) => p.lng);
    return [
      (Math.min(...lats) + Math.max(...lats)) / 2,
      (Math.min(...lngs) + Math.max(...lngs)) / 2,
    ];
  }, [active]);

  const handleSelect = useCallback((seg: RoadSegment) => setActive(seg), []);

  return (
    <>
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(1000px_600px_at_20%_-10%,rgba(56,189,248,0.18),transparent),radial-gradient(900px_600px_at_90%_10%,rgba(168,85,247,0.16),transparent)]" />

      <header className="relative z-10 border-b border-white/10 bg-zinc-950/60 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-white/10 ring-1 ring-white/10">
              <Zap className="h-5 w-5 text-cyan-300" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wide">
                Traffic Predictor
              </div>
              <div className="text-xs text-zinc-400">
                Ho Chi Minh City road segment speed + forecast
              </div>
            </div>
          </div>

          <div className="hidden items-center gap-2 text-xs text-zinc-300 md:flex">
            <span className="inline-flex items-center gap-1 rounded-full bg-white/5 px-3 py-1 ring-1 ring-white/10">
              <MapPin className="h-3.5 w-3.5" />
              Leaflet
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-white/5 px-3 py-1 ring-1 ring-white/10">
              <Activity className="h-3.5 w-3.5" />
              {segments.length} segments
            </span>
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto grid h-[calc(100%-73px)] max-w-7xl grid-cols-1 gap-4 px-4 py-4 lg:grid-cols-[380px_1fr]">
        <Sidebar segments={segments} active={active} onSelect={handleSelect} />
        <MapPanel
          segments={segments}
          active={active}
          center={center}
          onSelect={handleSelect}
        />
      </main>
    </>
  );
}
