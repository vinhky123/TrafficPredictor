"use client";

import { useEffect, useRef, useState } from "react";
import { SseClient, type SseUpdate } from "@/lib/sse";

export function useRealtime(url: string) {
  const [latestUpdate, setLatestUpdate] = useState<SseUpdate | null>(null);
  const [connected, setConnected] = useState(false);
  const clientRef = useRef<SseClient | null>(null);

  useEffect(() => {
    if (!url) return;

    const client = new SseClient(url);
    clientRef.current = client;

    client.onConnect = () => setConnected(true);
    client.onDisconnect = () => setConnected(false);
    client.onMessage = (update) => setLatestUpdate(update);

    client.connect();

    return () => {
      client.disconnect();
      clientRef.current = null;
      setConnected(false);
      setLatestUpdate(null);
    };
  }, [url]);

  return { latestUpdate, connected };
}
