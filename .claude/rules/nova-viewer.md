---
description: Rules for the Next.js + React brain panel (nova-viewer)
paths:
  - 'nova-viewer/app/**/*.{ts,tsx}'
  - 'nova-viewer/lib/**/*.{ts,tsx}'
  - 'nova-viewer/**/*.test.{ts,tsx}'
---

# nova-viewer Rules

> Read this before editing any file in `nova-viewer/`. Path-scoped
> companion to `CLAUDE.md`. If a rule here contradicts CLAUDE.md, this
> file wins for nova-viewer paths. **Also read `nova-viewer/AGENTS.md`
> before writing new files** — Next.js 16 + React 19 ship breaking
> changes that contradict older training data.

## Environment

- Package manager: **`pnpm`, never `npm`.** The viewer ships
  `pnpm-lock.yaml` + `pnpm-workspace.yaml`. `npm install` will crash
  on the existing pnpm-shaped `node_modules`. See gotcha #8 in
  CLAUDE.md.
- Node target: whatever `pnpm` resolves from the workspace
- Stack: Next.js 16.2.4, React 19.2.4, Tailwind 4, Framer Motion 12,
  vitest + RTL + jsdom

## Code style

- TypeScript strict mode. `npx tsc --noEmit` must be clean.
- ESLint zero warnings (`pnpm run lint`).
- Functional components only. No class components anywhere in this
  codebase — don't introduce one.
- Discriminated unions over `any` / `unknown` casts. The
  `AgentEvent` catch-all (`{event: string; data: unknown}`) is
  acknowledged tech debt scheduled for removal in Week 0 Day 1
  (gotcha #9). Until then, use `as data as <T>` casts in derived
  reducers — but flag any new code that depends on the catch-all.
- Tailwind 4 utility classes; avoid inline `style={{}}` unless
  animating.
- `useEffect` must have a cleanup function on every subscription
  (WebSocket, interval, event listener). Leaking listeners is the
  most common bug class in this codebase.
- Pure-function reducers (`lib/stream/deriveStream.ts` style) are
  the preferred pattern for event → view-state derivation. Test
  them in isolation; they should not import React.
- vitest for tests, never jest. Use `vi.fn()`, `vi.mock()`,
  `vi.useFakeTimers()`.

## Component conventions

- Components live in `nova-viewer/app/components/`
- Co-locate a `.test.tsx` file next to each component if it has any
  non-trivial behavior
- Props interfaces named `${ComponentName}Props`
- Default-export the component; named-export the props interface so
  parent components can compose
- Animations via Framer Motion's `motion.div` + `AnimatePresence`,
  not raw CSS transitions, when sequencing matters

## Bus contract

- The viewer subscribes via `useNovaSocket` in `lib/websocket.ts` and
  derives view state in `lib/stream/`
- All event shapes typed in `lib/types.ts`, mirrored from
  `nova-agent/src/nova_agent/bus/protocol.py`
- If you add a new event type to the agent, you MUST add the matching
  TS type to `lib/types.ts` in the same PR

## Quality gate

Before commit (or use `/check-viewer`):

```bash
pnpm test && npx tsc --noEmit && pnpm run lint
```

All three must be clean. No `--no-verify` skipping.
