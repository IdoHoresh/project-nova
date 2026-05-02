import { describe, expect, it } from "vitest";
import { rewordFirstPerson, truncate } from "../reword";

describe("rewordFirstPerson", () => {
  it("passes through text that already reads first-person", () => {
    const input = "I see a 16 in the corner. I'll consolidate down.";
    expect(rewordFirstPerson(input)).toBe(input);
  });

  it("rewrites third-person 'Nova' to first-person", () => {
    expect(rewordFirstPerson("Nova should swipe down to merge the 4s.")).toBe(
      "I should swipe down to merge the 4s.",
    );
  });

  it("rewrites 'the agent' to 'I'", () => {
    expect(rewordFirstPerson("The agent will swipe right.")).toBe(
      "I will swipe right.",
    );
  });

  it("rewrites 'her' / 'she' / 'their' when nova-referring", () => {
    expect(rewordFirstPerson("She picks down because it merges 4s.")).toBe(
      "I pick down because it merges 4s.",
    );
  });

  it("preserves capitalization at sentence start after rewrite", () => {
    expect(rewordFirstPerson("nova will consolidate.")).toBe(
      "I will consolidate.",
    );
  });

  it("does not over-rewrite — leaves third-person references to game tiles alone", () => {
    expect(
      rewordFirstPerson("The 16 in the corner is locking in. Nova merges down."),
    ).toBe("The 16 in the corner is locking in. I merge down.");
  });

  it("returns empty string unchanged", () => {
    expect(rewordFirstPerson("")).toBe("");
  });
});

describe("truncate", () => {
  it("returns text unchanged when under limit", () => {
    expect(truncate("short", 10)).toBe("short");
  });

  it("appends ellipsis when over limit", () => {
    const text = "a".repeat(50);
    const out = truncate(text, 20);
    expect(out.length).toBe(20);
    expect(out.endsWith("…")).toBe(true);
  });

  it("breaks at word boundary when possible within last 12 chars of limit", () => {
    const text = "the quick brown fox jumps over the lazy dog";
    const out = truncate(text, 25);
    expect(out.endsWith("…")).toBe(true);
    // Should cut at the previous space, not mid-word
    expect(out).not.toMatch(/\w…$/);
  });
});
