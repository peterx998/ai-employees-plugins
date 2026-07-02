#!/usr/bin/env bash
# sync-runtime-adapters.sh — Generate runtime-specific adapter configs
# Usage: bash install/sync-runtime-adapters.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Syncing Runtime Adapters ==="

PLUGINS="customer-support influencer-outreach ad-creative shopify-growth b2b-sales agent-evaluation"

for plugin in $PLUGINS; do
  SRC="$REPO/$plugin"

  # Generate Hermes .hermes.md per plugin (if not exists)
  if [ ! -f "$SRC/.hermes.md" ]; then
    cat > "$SRC/.hermes.md" <<EOF
# $plugin

Hermes: this plugin provides $plugin AI employee skills.
Use \`/skill <name>\` to load individual skills.
EOF
    echo "  ✅ $plugin/.hermes.md"
  fi

  # Generate Codex AGENTS.md per plugin (if not exists)
  if [ ! -f "$SRC/AGENTS.md" ]; then
    cat > "$SRC/AGENTS.md" <<EOF
# $plugin — Codex Instructions

This plugin provides $plugin AI employee skills.
SKILL.md files with \`user_invocable: true\` are auto-discovered by Codex.
EOF
    echo "  ✅ $plugin/AGENTS.md"
  fi
done

echo ""
echo "=== Runtime adapters synced ==="
