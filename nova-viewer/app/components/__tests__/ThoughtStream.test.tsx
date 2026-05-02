import { describe, expect, it } from "vitest";
import { useEffect, useState } from "react";
import { render, screen, act } from "@testing-library/react";
import { ThoughtStream } from "../ThoughtStream";
import type { StreamEntry } from "@/lib/stream/types";

const baseTs = "2026-05-02T14:31:02Z";

const entries: StreamEntry[] = [
  {
    kind: "decision",
    id: "decision-0",
    ts: baseTs,
    text: "I'll consolidate down.",
    action: "swipe_down",
    confidence: "medium",
  },
  {
    kind: "memory_recalled",
    id: "memory_recalled-1",
    ts: baseTs,
    text: "I remember something.",
    count: 1,
  },
  {
    kind: "mode_flip",
    id: "mode_flip-2",
    ts: baseTs,
    from: "react",
    to: "tot",
    text: "Slow down.",
  },
  {
    kind: "tot_block",
    id: "tot_block-3",
    ts: baseTs,
    lead: "Let me weigh.",
    branches: [
      { action: "swipe_up", value: 0.31, reasoning: "exposed", status: "complete" },
      { action: "swipe_down", value: 0.58, reasoning: "consolidates", status: "complete" },
    ],
    selected: { action: "swipe_down", trailer: "Going with down." },
  },
  {
    kind: "trauma",
    id: "trauma-4",
    ts: baseTs,
    text: "Killed me before.",
    count: 1,
  },
  {
    kind: "game_over",
    id: "game_over-5",
    ts: baseTs,
    finalScore: 512,
    maxTile: 64,
    catastrophic: false,
    lesson: "Avoid the corner.",
  },
];

describe("<ThoughtStream />", () => {
  it("renders one element per entry, ordered chronologically", () => {
    render(<ThoughtStream entries={entries} />);
    // ToT branches are also rendered as <li>s nested inside the ToT block's
    // inner <ul>. Filter to top-level entry items only.
    const items = screen
      .getAllByRole("listitem")
      .filter((el) => !el.closest("ul ul"));
    expect(items).toHaveLength(6);
    expect(items[0]).toHaveTextContent("consolidate down");
    expect(items[5]).toHaveTextContent("Avoid the corner");
  });

  it("renders ToT branches with the winner marked", () => {
    render(<ThoughtStream entries={[entries[3]]} />);
    expect(screen.getByText(/Going with down/)).toBeInTheDocument();
    // The winning branch (swipe_down with value 0.58) gets the ✓ marker.
    expect(screen.getByText(/0\.58/)).toBeInTheDocument();
    expect(screen.getByText(/✓/)).toBeInTheDocument();
  });

  it("renders the type chip for each non-routine entry", () => {
    render(<ThoughtStream entries={entries} />);
    expect(screen.getByText("RECALLED")).toBeInTheDocument();
    expect(screen.getByText("MODE")).toBeInTheDocument();
    expect(screen.getByText("DELIBERATING")).toBeInTheDocument();
    expect(screen.getByText("TRAUMA")).toBeInTheDocument();
    expect(screen.getByText("GAME OVER")).toBeInTheDocument();
  });

  it("renders an empty placeholder when there are no entries", () => {
    render(<ThoughtStream entries={[]} />);
    expect(screen.getByText(/waiting for nova/i)).toBeInTheDocument();
  });
});

describe("<ThoughtStream /> — auto-scroll", () => {
  it("scrolls the container to the bottom on new entries when sticky", () => {
    // Mock scrollTo so we can observe it.
    const scrollToCalls: number[] = [];
    Element.prototype.scrollTo = function (this: Element, ...args: unknown[]) {
      const opts = args[0] as { top?: number };
      if (opts?.top !== undefined) scrollToCalls.push(opts.top);
    } as unknown as Element["scrollTo"];

    function Harness() {
      const [n, setN] = useState(1);
      const list: StreamEntry[] = Array.from({ length: n }, (_, i) => ({
        kind: "decision",
        id: `decision-${i}`,
        ts: baseTs,
        text: `move ${i}`,
        action: "swipe_down",
        confidence: "medium",
      }));
      useEffect(() => {
        // Simulate growing list
        const t = setTimeout(() => setN((v) => v + 1), 0);
        return () => clearTimeout(t);
      }, [n]);
      return <ThoughtStream entries={list} />;
    }

    render(<Harness />);
    // After mount + 1 effect run, expect at least one scroll call.
    return act(async () => {
      await new Promise((r) => setTimeout(r, 10));
      expect(scrollToCalls.length).toBeGreaterThan(0);
    });
  });
});

describe("<ThoughtStream /> — fade-in motion", () => {
  it("each entry has the animate-stream-fade class", () => {
    render(<ThoughtStream entries={entries} />);
    const items = screen.getAllByRole("listitem").filter((el) => !el.closest("ul ul"));
    for (const it of items) {
      expect(it.className).toContain("animate-stream-fade");
    }
  });

  it("trauma entry additionally carries the trauma-wash class", () => {
    render(<ThoughtStream entries={[entries[4]]} />);
    const items = screen.getAllByRole("listitem");
    expect(items[0].className).toContain("animate-stream-trauma");
  });
});

describe("<ThoughtStream /> — jump-to-live chip", () => {
  it("shows the chip when not stuck and there are unseen new entries", async () => {
    function Harness() {
      const [n, setN] = useState(2);
      const list: StreamEntry[] = Array.from({ length: n }, (_, i) => ({
        kind: "decision",
        id: `decision-${i}`,
        ts: baseTs,
        text: `move ${i}`,
        action: "swipe_down",
        confidence: "medium",
      }));
      // Trigger a synthetic scroll-up to detach, then add new entries.
      useEffect(() => {
        const id = setTimeout(() => {
          const list = document.querySelector("div.overflow-y-auto") as HTMLDivElement | null;
          if (list) {
            // Force detach: simulate scrolled-up state.
            Object.defineProperty(list, "scrollHeight", { value: 1000, configurable: true });
            Object.defineProperty(list, "clientHeight", { value: 200, configurable: true });
            Object.defineProperty(list, "scrollTop", { value: 0, writable: true, configurable: true });
            list.dispatchEvent(new Event("scroll"));
          }
          setN((v) => v + 1);
        }, 0);
        return () => clearTimeout(id);
      }, []);
      return <ThoughtStream entries={list} />;
    }

    render(<Harness />);
    await act(async () => {
      await new Promise((r) => setTimeout(r, 30));
    });
    expect(screen.queryByText(/jump to live/i)).toBeInTheDocument();
  });
});
