#!/usr/bin/env bash
# Nova Flash quota statusline: calls used today + countdown to midnight Pacific reset.
# Counts tot_branch events from today's run dirs (each = 1 Gemini LLM call).

TODAY=$(date +%Y-%m-%d)
RUN_BASE="/Users/idohoresh/Desktop/a/nova-agent/runs"

BRANCHES=$(find "${RUN_BASE}/${TODAY}"* -name "events.jsonl" 2>/dev/null \
  -exec grep -c '"tot_branch"' {} \; 2>/dev/null \
  | awk '{s+=$1} END {print s+0}')

# Each tot_branch = 1 Gemini call (ToT evaluation).
# Add ~25% for decision + reflection calls not captured in events.jsonl.
APPROX=$(( BRANCHES + BRANCHES / 4 ))
BAR_FILL=$(( APPROX * 10 / 10000 ))
[ $BAR_FILL -gt 10 ] && BAR_FILL=10

NOW=$(date +%s)
# Midnight Pacific (PDT = UTC-7 in May). BSD date (macOS).
MIDNIGHT=$(TZ='America/Los_Angeles' date -j -v+1d -v0H -v0M -v0S +%s 2>/dev/null)
REMAINING=$(( MIDNIGHT - NOW ))
[ $REMAINING -lt 0 ] && REMAINING=0
H=$(( REMAINING / 3600 ))
M=$(( (REMAINING % 3600) / 60 ))

printf "⚡ ~%d/10K  ⏱ %dh%02dm" "$APPROX" "$H" "$M"
