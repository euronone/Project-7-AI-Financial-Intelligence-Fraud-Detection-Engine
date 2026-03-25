#!/usr/bin/env bash
set -e

# Sync marker for .claude rules to indicate they follow CLAUDE.md
RULES_DIR="$(dirname "$0")/../rules"

if [ ! -d "$RULES_DIR" ]; then
  echo "Rules directory not found: $RULES_DIR"
  exit 1
fi

for f in "$RULES_DIR"/*.md; do
  if [ ! -f "$f" ]; then
    continue
  fi

  # Add sync note if not present
  if ! grep -q "^\s*\*\*Source:\*\* CLAUDE.md" "$f"; then
    echo "Updating $f"
    tmp="${f}.tmp"
    echo "# Auto-sync metadata (source: CLAUDE.md, updated $(date -u +'%Y-%m-%dT%H:%M:%SZ'))" > "$tmp"
    echo "" >> "$tmp"
    echo "**Source:** CLAUDE.md" >> "$tmp"
    echo "" >> "$tmp"
    cat "$f" >> "$tmp"
    mv "$tmp" "$f"
  fi

done

echo "Sync complete."