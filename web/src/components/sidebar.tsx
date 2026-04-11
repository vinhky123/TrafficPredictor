"use client";

import { useMemo, useState } from "react";
import { ChevronRight, Search } from "lucide-react";

import type { LocationItem, PredictResponse } from "@/lib/types";
import { postPredict } from "@/lib/api";

type Props = {
  locations: LocationItem[];
  active: LocationItem | null;
  onSelect: (loc: LocationItem) => void;
};

function speedBadge(speed?: number) {
  if (speed == null || Number.isNaN(speed))
    return { label: "—", cls: "bg-white/5 text-zinc-200 ring-white/10" };
  if (speed < 15)
    return {
      label: `${speed} km/h`,
      cls: "bg-rose-500/15 text-rose-200 ring-rose-500/30",
    };
  if (speed < 25)
    return {
      label: `${speed} km/h`,
      cls: "bg-amber-500/15 text-amber-200 ring-amber-500/30",
    };
  return {
    label: `${speed} km/h`,
    cls: "bg-emerald-500/15 text-emerald-200 ring-emerald-500/30",
  };
}

export function Sidebar({ locations, active, onSelect }: Props) {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<PredictResponse | null>(null);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return locations;
    return locations.filter((l) => l.name.toLowerCase().includes(s));
  }, [locations, q]);

  async function runPredict(loc: LocationItem) {
    setLoading(true);
    setData(null);
    try {
      const resp = await postPredict(loc.coordinates.lat, loc.coordinates.lng);
      setData(resp);
    } finally {
      setLoading(false);
    }
  }

  const badge = speedBadge(data?.current);

  return (
    <aside className="flex h-full flex-col gap-4 rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur">
      <div className="space-y-1">
        <div className="text-sm font-semibold">Locations</div>
        <div className="text-xs text-zinc-400">
          Pick a hotspot to see current speed + forecast.
        </div>
      </div>

      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search location…"
          className="w-full rounded-xl border border-white/10 bg-zinc-950/40 px-9 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 outline-none ring-0 focus:border-cyan-400/40"
        />
      </div>

      <div className="flex-1 space-y-2 overflow-auto pr-1">
        {filtered.map((loc) => {
          const isActive = active?.name === loc.name;
          return (
            <button
              key={loc.name}
              onClick={() => onSelect(loc)}
              className={[
                "group flex w-full items-center justify-between gap-3 rounded-xl border p-3 text-left transition",
                isActive
                  ? "border-cyan-400/30 bg-cyan-400/10"
                  : "border-white/10 bg-white/5 hover:bg-white/10",
              ].join(" ")}
            >
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">{loc.name}</div>
                <div className="truncate text-xs text-zinc-400">
                  {loc.description || "Traffic monitoring point"}
                </div>
              </div>
              <ChevronRight className="h-4 w-4 text-zinc-400 transition group-hover:translate-x-0.5" />
            </button>
          );
        })}
        {filtered.length === 0 && (
          <div className="rounded-xl border border-white/10 bg-zinc-950/30 p-4 text-sm text-zinc-400">
            No locations found.
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-white/10 bg-zinc-950/30 p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="space-y-0.5">
            <div className="text-xs text-zinc-400">Selected</div>
            <div className="truncate text-sm font-semibold">
              {active?.name || "—"}
            </div>
          </div>
          <span
            className={`inline-flex items-center rounded-full px-3 py-1 text-xs ring-1 ${badge.cls}`}
          >
            {badge.label}
          </span>
        </div>

        <div className="mt-3">
          <button
            disabled={!active || loading}
            onClick={() => active && runPredict(active)}
            className="inline-flex w-full items-center justify-center rounded-xl bg-cyan-400/15 px-3 py-2 text-sm font-medium text-cyan-200 ring-1 ring-cyan-400/30 transition hover:bg-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Fetching…" : "Fetch forecast"}
          </button>
        </div>

        {data?.error && (
          <div className="mt-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-200">
            {data.error}
            <div className="mt-1 text-[11px] text-rose-200/70">
              Set <code className="rounded bg-black/30 px-1">NEXT_PUBLIC_API_URL</code> to
              connect the API.
            </div>
          </div>
        )}

        {data?.predict && data.predict.length > 0 && (
          <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-xl border border-white/10 bg-white/5 p-3">
              <div className="text-zinc-400">Next 10 min</div>
              <div className="mt-1 text-sm font-semibold">
                {Math.round((data.predict[0] + data.predict[1]) / 2)} km/h
              </div>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-3">
              <div className="text-zinc-400">Next 60 min</div>
              <div className="mt-1 text-sm font-semibold">
                {Math.round(
                  data.predict.reduce((a, b) => a + b, 0) /
                    data.predict.length,
                )}{" "}
                km/h
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
