import "@testing-library/jest-dom/vitest";

// jsdom doesn't implement Element.scrollTo. Components that call it during
// effects (e.g. ThoughtStream's sticky-bottom auto-scroll) would crash all
// other tests. Provide a no-op default; individual tests can replace it.
if (typeof Element !== "undefined" && !Element.prototype.scrollTo) {
  Element.prototype.scrollTo = function () {} as Element["scrollTo"];
}
