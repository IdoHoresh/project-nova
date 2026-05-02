import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
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
