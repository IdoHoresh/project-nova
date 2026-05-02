import { renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useNovaSocket } from "../websocket";

// Minimal fake WebSocket: captures the most recently constructed instance
// so the test can drive onopen/onmessage directly.
class FakeWebSocket {
  static last: FakeWebSocket | null = null;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  close = vi.fn();
  constructor(public url: string) {
    FakeWebSocket.last = this;
  }
}

beforeEach(() => {
  // @ts-expect-error — installing a stub on the global object
  globalThis.WebSocket = FakeWebSocket;
  FakeWebSocket.last = null;
  vi.spyOn(console, "warn").mockImplementation(() => {});
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useNovaSocket", () => {
  it("appends a stamped event for valid frames", () => {
    const { result } = renderHook(() => useNovaSocket());
    const ws = FakeWebSocket.last!;
    act(() => {
      ws.onmessage?.({
        data: JSON.stringify({
          event: "perception",
          data: { score: 100, step: 3 },
        }),
      });
    });
    expect(result.current.events).toHaveLength(1);
    expect(result.current.events[0].event).toBe("perception");
    expect(result.current.events[0].ts).toMatch(/\d{4}-\d{2}-\d{2}T/);
  });

  it("drops frames that fail schema validation", () => {
    const { result } = renderHook(() => useNovaSocket());
    const ws = FakeWebSocket.last!;
    act(() => {
      ws.onmessage?.({
        data: JSON.stringify({
          event: "perception",
          data: { score: "not a number" },
        }),
      });
    });
    expect(result.current.events).toHaveLength(0);
    expect(console.warn).toHaveBeenCalledTimes(1);
  });

  it("rate-limits the warning per event name", () => {
    const { result } = renderHook(() => useNovaSocket());
    const ws = FakeWebSocket.last!;
    const bad = JSON.stringify({ event: "perception", data: {} });
    act(() => {
      ws.onmessage?.({ data: bad });
      ws.onmessage?.({ data: bad });
      ws.onmessage?.({ data: bad });
    });
    expect(result.current.events).toHaveLength(0);
    expect(console.warn).toHaveBeenCalledTimes(1);
  });

  it("drops malformed JSON without throwing", () => {
    const { result } = renderHook(() => useNovaSocket());
    const ws = FakeWebSocket.last!;
    expect(() =>
      act(() => {
        ws.onmessage?.({ data: "not json {" });
      }),
    ).not.toThrow();
    expect(result.current.events).toHaveLength(0);
  });
});
