export type SseUpdate = {
  type: "update";
  data: {
    timestamp: string;
    segments: Array<{
      segment_index: number;
      current: number | null;
      predict: number[] | null;
    }>;
  };
};

export class SseClient {
  private url: string;
  private eventSource: EventSource | null = null;
  private reconnectAttempt = 0;
  private readonly baseDelay = 1000;
  private readonly maxDelay = 30000;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private disposed = false;

  public onMessage: ((update: SseUpdate) => void) | null = null;
  public onError: ((err: Event) => void) | null = null;
  public onConnect: (() => void) | null = null;
  public onDisconnect: (() => void) | null = null;

  constructor(url: string) {
    this.url = url;
  }

  connect() {
    this.disposed = false;
    this.doConnect();
  }

  private doConnect() {
    if (this.disposed) return;

    this.eventSource = new EventSource(this.url);

    this.eventSource.onopen = () => {
      this.reconnectAttempt = 0;
      this.onConnect?.();
    };

    this.eventSource.addEventListener("update", (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as SseUpdate["data"];
        this.onMessage?.({ type: "update", data });
      } catch {
        // ignore malformed data
      }
    });

    this.eventSource.onerror = (ev: Event) => {
      this.eventSource?.close();
      this.eventSource = null;
      this.onDisconnect?.();
      this.onError?.(ev);
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect() {
    if (this.disposed) return;

    const delay = Math.min(
      this.baseDelay * Math.pow(2, this.reconnectAttempt),
      this.maxDelay,
    );
    this.reconnectAttempt++;

    this.timer = setTimeout(() => this.doConnect(), delay);
  }

  disconnect() {
    this.disposed = true;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    this.eventSource?.close();
    this.eventSource = null;
    this.onDisconnect?.();
  }
}
