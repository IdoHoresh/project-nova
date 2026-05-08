#!/usr/bin/env bash
# Build NotebookLM source bundles for Project Nova.
#
# Produces 9 markdown files under ./notebooklm-bundles/ that you upload as
# sources to a NotebookLM notebook. Each bundle is a different facet of the
# project (code, decisions, plans, research, etc.) so NotebookLM citations
# attribute cleanly per subsystem.
#
# Usage:
#   ./scripts/build-notebooklm-bundles.sh
#
# Requirements:
#   - npx (Node 18+) for repomix
#   - run from repo root (script enforces this)

set -euo pipefail

# Resolve repo root (parent of scripts/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

OUT_DIR="${REPO_ROOT}/notebooklm-bundles"
REPOMIX_VERSION="^0.3.0"

echo "==> Project Nova NotebookLM bundle builder"
echo "    repo: ${REPO_ROOT}"
echo "    out:  ${OUT_DIR}"
echo

# Sanity check: must be at the repo root with the expected layout.
for required in nova-agent nova-viewer docs CLAUDE.md ARCHITECTURE.md LESSONS.md; do
  if [[ ! -e "${REPO_ROOT}/${required}" ]]; then
    echo "ERROR: missing ${required} at repo root — are you running from the right place?" >&2
    exit 1
  fi
done

# Clean + recreate output dir.
rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

# Helper: append a file to a bundle with a clear delimiter so NotebookLM can
# cite individual files inside one source.
append_file() {
  local bundle="$1"
  local file="$2"
  local rel
  rel="${file#${REPO_ROOT}/}"
  {
    printf '\n\n---\n\n'
    printf '# FILE: %s\n\n' "${rel}"
    cat "${file}"
  } >> "${bundle}"
}

# Helper: append every file matching a glob (sorted, stable order).
append_glob() {
  local bundle="$1"
  shift
  local pattern
  for pattern in "$@"; do
    # shellcheck disable=SC2206
    local matches=( ${pattern} )
    for f in "${matches[@]}"; do
      [[ -f "${f}" ]] && append_file "${bundle}" "${f}"
    done
  done
}

# Helper: write a header at the top of a bundle.
write_header() {
  local bundle="$1"
  local title="$2"
  local description="$3"
  {
    printf '# %s\n\n' "${title}"
    printf '%s\n\n' "${description}"
    printf 'Generated: %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    printf 'Git: %s @ %s\n' "$(git branch --show-current)" "$(git rev-parse --short HEAD)"
  } > "${bundle}"
}

# ---------------------------------------------------------------------------
# Bundle 01 — root context (architecture, lessons, rules, top-level docs)
# ---------------------------------------------------------------------------
B01="${OUT_DIR}/01-root-context.md"
echo "[1/9] root context"
write_header "${B01}" \
  "Project Nova — Root Context" \
  "Top-level context: architecture overview, lessons learned, project conventions, security policy, review standards, and Claude Code workflow rules. Start here when exploring the project in NotebookLM."

append_glob "${B01}" \
  "${REPO_ROOT}/README.md" \
  "${REPO_ROOT}/CLAUDE.md" \
  "${REPO_ROOT}/ARCHITECTURE.md" \
  "${REPO_ROOT}/LESSONS.md" \
  "${REPO_ROOT}/REVIEW.md" \
  "${REPO_ROOT}/SECURITY.md" \
  "${REPO_ROOT}/.claude/rules/*.md"

# ---------------------------------------------------------------------------
# Bundle 02 — nova-agent (Python cognitive architecture)
# ---------------------------------------------------------------------------
echo "[2/9] nova-agent code (repomix)"
npx --yes "repomix@${REPOMIX_VERSION}" \
  -c "${REPO_ROOT}/.repomix/agent.config.json" \
  > /dev/null

# ---------------------------------------------------------------------------
# Bundle 03 — nova-viewer (Next.js brain panel)
# ---------------------------------------------------------------------------
echo "[3/9] nova-viewer code (repomix)"
npx --yes "repomix@${REPOMIX_VERSION}" \
  -c "${REPO_ROOT}/.repomix/viewer.config.json" \
  > /dev/null

# ---------------------------------------------------------------------------
# Bundle 04 — product strategy
# ---------------------------------------------------------------------------
B04="${OUT_DIR}/04-product-strategy.md"
echo "[4/9] product strategy"
write_header "${B04}" \
  "Project Nova — Product Strategy" \
  "Strategic dossier: methodology (the cognitive-audit thesis), product roadmap, personas and use cases, competitive landscape, scientific foundations, and the external-review brief. Use this to understand WHY the cognitive architecture is built the way it is."

append_glob "${B04}" \
  "${REPO_ROOT}/docs/product/README.md" \
  "${REPO_ROOT}/docs/product/methodology.md" \
  "${REPO_ROOT}/docs/product/product-roadmap.md" \
  "${REPO_ROOT}/docs/product/personas-and-use-cases.md" \
  "${REPO_ROOT}/docs/product/scientific-foundations.md" \
  "${REPO_ROOT}/docs/product/competitive-landscape.md" \
  "${REPO_ROOT}/docs/product/casterai-deep-dive.md" \
  "${REPO_ROOT}/docs/product/backlog.md" \
  "${REPO_ROOT}/docs/product/external-review-brief.md"

# ---------------------------------------------------------------------------
# Bundle 05 — Architecture Decision Records
# ---------------------------------------------------------------------------
B05="${OUT_DIR}/05-decisions-adrs.md"
echo "[5/9] decisions / ADRs"
write_header "${B05}" \
  "Project Nova — Architecture Decision Records" \
  "Every load-bearing architectural and product decision, with the alternatives considered and consequences. ADRs are written BEFORE the implementation commit."

append_glob "${B05}" \
  "${REPO_ROOT}/docs/decisions/README.md" \
  "${REPO_ROOT}/docs/decisions/0000-template.md" \
  "${REPO_ROOT}/docs/decisions/[0-9][0-9][0-9][0-9]-*.md"

# ---------------------------------------------------------------------------
# Bundle 06 — plans + specs
# ---------------------------------------------------------------------------
B06="${OUT_DIR}/06-plans-and-specs.md"
echo "[6/9] plans + specs"
write_header "${B06}" \
  "Project Nova — Implementation Plans & Specs" \
  "Design specs and step-by-step implementation plans authored before each multi-step feature. Includes both the original docs/specs/ tree and the per-feature superpowers plan/spec pairs."

append_glob "${B06}" \
  "${REPO_ROOT}/docs/specs/*.md" \
  "${REPO_ROOT}/docs/superpowers/specs/*.md" \
  "${REPO_ROOT}/docs/superpowers/plans/*.md"

# ---------------------------------------------------------------------------
# Bundle 07 — onboarding / learn
# ---------------------------------------------------------------------------
B07="${OUT_DIR}/07-learn-onboarding.md"
echo "[7/9] learn / onboarding"
write_header "${B07}" \
  "Project Nova — Onboarding & Explainer Series" \
  "The 01–09 'learn' series: plain-English walkthrough of what Project Nova is, the cognitive pieces, memory, emotion, the decision loop, the brain-panel tour, reading the code, glossary, and security."

append_glob "${B07}" \
  "${REPO_ROOT}/docs/learn/*.md"

# ---------------------------------------------------------------------------
# Bundle 08 — research + pilot adjudications
# ---------------------------------------------------------------------------
B08="${OUT_DIR}/08-research-and-pilots.md"
echo "[8/9] research + pilots"
write_header "${B08}" \
  "Project Nova — External Research & Pilot Adjudications" \
  "External red-team reviews (Claude vs Gemini rounds + synthesis), C1 ablation results, internal pilot adjudications (256-corner abandonment, 128-snake collapse, 512-wall), and the v2.2-epsilon spec."

append_glob "${B08}" \
  "${REPO_ROOT}/docs/external-review/*.md" \
  "${REPO_ROOT}/docs/external-review/*.py" \
  "${REPO_ROOT}/docs/internal/*.md" \
  "${REPO_ROOT}/docs/internal/*.txt"

# ---------------------------------------------------------------------------
# Bundle 09 — handoffs (session-to-session continuity logs)
# ---------------------------------------------------------------------------
B09="${OUT_DIR}/09-handoffs-history.md"
echo "[9/9] handoffs history"
write_header "${B09}" \
  "Project Nova — Session Handoff History" \
  "Context-checkpoint handoffs written before each /clear: architectural intent, edge-case warnings, rejected alternatives, and what's next. Read chronologically to follow the project's evolution."

append_glob "${B09}" \
  "${REPO_ROOT}/docs/superpowers/handoffs/*.md"

# ---------------------------------------------------------------------------
# Index README inside the bundle dir.
# ---------------------------------------------------------------------------
INDEX="${OUT_DIR}/README.md"
cat > "${INDEX}" <<'EOF'
# Project Nova — NotebookLM Source Bundles

Upload every `*.md` file in this directory as a separate source to a single
NotebookLM notebook. Each bundle is one facet of the project; keeping them
separate lets NotebookLM cite cleanly per subsystem.

## Recommended notebook setup

1. Create a new NotebookLM notebook named "Project Nova".
2. Upload these 9 files as sources (drag-and-drop the whole folder works).
3. Suggested first prompt:
   *"You are an analyst onboarding to Project Nova. Use 01-root-context.md
   and 04-product-strategy.md to summarise the thesis in 200 words. Cite
   sources."*
4. For Audio Overview / podcast: focus on bundles 01, 04, 07.
5. For technical deep-dive: focus on bundles 02, 03, 05, 06.
6. For "what changed and why": bundles 05 (ADRs) and 09 (handoffs).

## Bundle index

| # | File | Contents |
|---|------|----------|
| 01 | `01-root-context.md`       | CLAUDE.md, ARCHITECTURE.md, LESSONS.md, README.md, REVIEW.md, SECURITY.md, .claude/rules/ |
| 02 | `02-nova-agent-code.md`    | Python cognitive architecture (src + tests + configs) |
| 03 | `03-nova-viewer-code.md`   | Next.js 16 brain panel (app + lib + configs) |
| 04 | `04-product-strategy.md`   | docs/product/ — methodology, roadmap, personas, science, competitive landscape |
| 05 | `05-decisions-adrs.md`     | docs/decisions/ — every ADR |
| 06 | `06-plans-and-specs.md`    | docs/specs/ + docs/superpowers/{plans,specs}/ |
| 07 | `07-learn-onboarding.md`   | docs/learn/ — 01–09 plain-English explainer series |
| 08 | `08-research-and-pilots.md`| docs/external-review/ + docs/internal/ — red-team rounds, ablations, pilot adjudications |
| 09 | `09-handoffs-history.md`   | docs/superpowers/handoffs/ — session-to-session continuity logs |

## Refreshing

After material changes to the codebase or docs, re-run:

```bash
./scripts/build-notebooklm-bundles.sh
```

Then re-upload the changed bundles to NotebookLM (NotebookLM does not auto-sync
from local files — refresh is manual).

## Excluded on purpose

- `.env*`, secrets, lockfiles, node_modules, build artifacts, runs/, data/local/
- nova-game APK build artifacts (Unity, binary)
- Patches and pnpm overrides

If you need any of these inside NotebookLM, add the path to the relevant
`.repomix/*.config.json` `include` list and rebuild.
EOF

# ---------------------------------------------------------------------------
# Summary report.
# ---------------------------------------------------------------------------
echo
echo "==> Bundle stats"
printf "%-40s %10s %12s\n" "FILE" "SIZE" "WORDS"
printf "%-40s %10s %12s\n" "----" "----" "-----"
total_words=0
for f in "${OUT_DIR}"/*.md; do
  size=$(wc -c < "${f}" | tr -d ' ')
  words=$(wc -w < "${f}" | tr -d ' ')
  total_words=$((total_words + words))
  printf "%-40s %10s %12s\n" "$(basename "${f}")" "${size}" "${words}"
done
printf "%-40s %10s %12s\n" "TOTAL" "" "${total_words}"
echo
echo "==> Done. Upload the 9 *.md files to NotebookLM."
echo "    NotebookLM source-size limit: 500,000 words per source."
