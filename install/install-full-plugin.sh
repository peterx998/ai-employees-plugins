#!/usr/bin/env bash
# install-full-plugin.sh — Install complete plugin structure (skills + commands + manifest + mcp + connectors)
# Usage: bash install/install-full-plugin.sh --target hermes|codex [--plugin customer-support]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME=""
PLUGIN_FILTER=""

for arg in "$@"; do
  case "$arg" in
    hermes|codex) RUNTIME="$arg";;
    --plugin) ;;
    customer-support|influencer-outreach|ad-creative|shopify-growth|b2b-sales|agent-evaluation) PLUGIN_FILTER="$arg";;
  esac
done

if [ -z "$RUNTIME" ]; then
  echo "Usage: bash install-full-plugin.sh hermes|codex [--plugin <name>]"
  exit 1
fi

if [ "$RUNTIME" = "hermes" ]; then
  DEST="$HOME/.hermes/plugins"
else
  DEST="$HOME/.codex/plugins"
fi

echo "=== AI Employees — Full Plugin Install ($RUNTIME) ==="
echo "Destination: $DEST"
echo ""

PLUGINS="customer-support influencer-outreach ad-creative shopify-growth b2b-sales agent-evaluation"
if [ -n "$PLUGIN_FILTER" ]; then
  PLUGINS="$PLUGIN_FILTER"
fi

TOTAL=0

for plugin in $PLUGINS; do
  echo "Installing $plugin (full)..."
  SRC="$REPO/$plugin"
  DST="$DEST/$plugin"

  mkdir -p "$DST"

  # Copy .claude-plugin/plugin.json
  if [ -f "$SRC/.claude-plugin/plugin.json" ]; then
    mkdir -p "$DST/.claude-plugin"
    cp "$SRC/.claude-plugin/plugin.json" "$DST/.claude-plugin/plugin.json"
    echo "  ✅ manifest"
  fi

  # Copy .mcp.json
  if [ -f "$SRC/.mcp.json" ]; then
    cp "$SRC/.mcp.json" "$DST/.mcp.json"
    echo "  ✅ mcp config"
  fi

  # Copy CONNECTORS.md
  if [ -f "$SRC/CONNECTORS.md" ]; then
    cp "$SRC/CONNECTORS.md" "$DST/CONNECTORS.md"
    echo "  ✅ connectors doc"
  fi

  # Copy commands/
  if [ -d "$SRC/commands" ]; then
    cp -r "$SRC/commands" "$DST/commands"
    CMD_COUNT=$(find "$DST/commands" -name "*.md" | wc -l)
    echo "  ✅ commands ($CMD_COUNT)"
  fi

  # Copy skills/
  if [ -d "$SRC/skills" ]; then
    cp -r "$SRC/skills" "$DST/skills"
    SKILL_COUNT=$(find "$DST/skills" -name "SKILL.md" | wc -l)
    echo "  ✅ skills ($SKILL_COUNT)"
  fi

  # Copy schemas/ if exists
  if [ -d "$SRC/schemas" ]; then
    cp -r "$SRC/schemas" "$DST/schemas"
    echo "  ✅ schemas"
  fi

  # Copy evals/ if exists
  if [ -d "$SRC/evals" ]; then
    cp -r "$SRC/evals" "$DST/evals"
    echo "  ✅ evals"
  fi

  # Copy examples/ if exists
  if [ -d "$SRC/examples" ]; then
    cp -r "$SRC/examples" "$DST/examples"
    echo "  ✅ examples"
  fi

  TOTAL=$((TOTAL + 1))
  echo ""
done

echo "=== Done: $TOTAL plugins fully installed to $DEST ==="
