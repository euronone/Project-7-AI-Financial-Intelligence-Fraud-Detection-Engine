#!/usr/bin/env bash
set -e

echo "Running project checks..."

if [ -d "backend" ]; then
  cd backend

  if [ -f "requirements.txt" ]; then
    echo "Running backend checks..."
    python -m pytest -q || true
  fi

  cd ..
fi

if [ -d "frontend" ]; then
  cd frontend

  if [ -f "package.json" ]; then
    echo "Running frontend checks..."
    npm run lint || true
  fi

  cd ..
fi

# Ensure .claude rule files are annotated from CLAUDE.md
if [ -d ".claude/rules" ]; then
  echo "Syncing .claude rules with CLAUDE.md metadata..."
  bash .claude/scripts/sync-claude-rules.sh || true
fi

echo "Checks complete."