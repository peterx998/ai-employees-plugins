#!/usr/bin/env bash
# validate-plugin.sh — Validate plugin structure integrity
# Usage: bash install/validate-plugin.sh [--plugin <name>]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_FILTER="${2:-}"

PLUGINS="customer-support influencer-outreach ad-creative shopify-growth b2b-sales agent-evaluation"
if [ -n "$PLUGIN_FILTER" ] && [ "$PLUGIN_FILTER" != "--plugin" ]; then
  PLUGINS="$PLUGIN_FILTER"
fi

echo "=== Plugin Validation ==="
ERRORS=0
WARNINGS=0

for plugin in $PLUGINS; do
  DIR="$REPO/$plugin"
  echo ""
  echo "Checking: $plugin"

  # Check plugin.json
  if [ ! -f "$DIR/.claude-plugin/plugin.json" ]; then
    echo "  ❌ MISSING: .claude-plugin/plugin.json"
    ERRORS=$((ERRORS + 1))
  else
    echo "  ✅ plugin.json exists"
  fi

  # Check skills/
  if [ ! -d "$DIR/skills" ]; then
    echo "  ❌ MISSING: skills/ directory"
    ERRORS=$((ERRORS + 1))
  else
    SKILL_COUNT=$(find "$DIR/skills" -name "SKILL.md" | wc -l)
    echo "  ✅ skills/ ($SKILL_COUNT SKILL.md files)"

    # Validate each SKILL.md has user_invocable
    for skill_file in "$DIR/skills"/*/SKILL.md; do
      if ! grep -q "user_invocable: true" "$skill_file" 2>/dev/null; then
        echo "  ⚠️  WARNING: $(basename $(dirname $skill_file))/SKILL.md missing 'user_invocable: true'"
        WARNINGS=$((WARNINGS + 1))
      fi
    done
  fi

  # Check commands/
  if [ -d "$DIR/commands" ]; then
    CMD_COUNT=$(find "$DIR/commands" -name "*.md" | wc -l)
    echo "  ✅ commands/ ($CMD_COUNT files)"

    # Check command namespacing
    for cmd_file in "$DIR/commands"/*.md; do
      if [ -f "$cmd_file" ]; then
        CMD_NAME=$(grep -oP '^name: \K.*' "$cmd_file" 2>/dev/null || echo "")
        if [ -n "$CMD_NAME" ] && ! echo "$CMD_NAME" | grep -q ":"; then
          echo "  ⚠️  WARNING: $cmd_file — command '$CMD_NAME' missing namespace prefix"
          WARNINGS=$((WARNINGS + 1))
        fi
      fi
    done
  else
    echo "  ⚠️  WARNING: no commands/ directory"
    WARNINGS=$((WARNINGS + 1))
  fi

  # Check .mcp.json
  if [ -f "$DIR/.mcp.json" ]; then
    echo "  ✅ .mcp.json exists"
  else
    echo "  ℹ️  no .mcp.json (optional)"
  fi

  # Check CONNECTORS.md
  if [ -f "$DIR/CONNECTORS.md" ]; then
    echo "  ✅ CONNECTORS.md exists"
  else
    echo "  ℹ️  no CONNECTORS.md (optional)"
  fi
done

echo ""
echo "=== Validation Complete ==="
echo "Errors: $ERRORS | Warnings: $WARNINGS"
[ $ERRORS -eq 0 ] && echo "✅ All plugins valid" || echo "❌ Fix errors above"
exit $ERRORS
