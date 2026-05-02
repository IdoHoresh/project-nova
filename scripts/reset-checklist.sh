#!/usr/bin/env bash
# Resets the pre-commit checklist after a successful commit.
# All items go back to unchecked so the checklist is fresh for next time.
#
# Wired into .pre-commit-config.yaml as the "reset-checklist" local hook
# at the post-commit stage. Pattern adopted from the Gibor app workflow.

set -euo pipefail

CHECKLIST=".claude/pre-commit-checklist.md"

if [ ! -f "$CHECKLIST" ]; then
  exit 0
fi

# Replace all checked items with unchecked (BSD-sed compatible — no -i suffix).
# macOS sed and GNU sed both accept this form when the suffix is empty.
sed -i.bak 's/- \[x\]/- [ ]/g' "$CHECKLIST"
rm -f "$CHECKLIST.bak"

echo "Checklist reset for next commit."
