#!/usr/bin/env bash
# install-skills-only.sh — Copy SKILL.md files only (fast, lightweight)
# Usage: bash install/install-skills-only.sh --target hermes|codex
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:---target}"
RUNTIME=""

# Parse args
for arg in "$@"; do
  case "$arg" in
    --target) shift;;
    hermes|codex) RUNTIME="$arg";;
    *) ;;
  esac
done

if [ -z "$RUNTIME" ]; then
  echo "Usage: bash install-skills-only.sh hermes|codex"
  exit 1
fi

if [ "$RUNTIME" = "hermes" ]; then
  DEST="$HOME/.hermes/skills/business"
else
  DEST="$HOME/.codex/skills"
fi

echo "=== AI Employees — Skill-only Install ($RUNTIME) ==="
echo "Destination: $DEST"
echo ""

PLUGINS="customer-support influencer-outreach ad-creative shopify-growth b2b-sales agent-evaluation"
TOTAL=0

for plugin in $PLUGINS; do
  echo "Installing $plugin skills..."
  for skill_dir in "$REPO/$plugin/skills"/*/; do
    skill_name=$(basename "$skill_dir")
    src="$skill_dir/SKILL.md"
    if [ -f "$src" ]; then
      if [ "$RUNTIME" = "hermes" ]; then
        mkdir -p "$DEST/$skill_name"
        cp "$src" "$DEST/$skill_name/SKILL.md"
      else
        mkdir -p "$DEST/$skill_name"
        cp "$src" "$DEST/$skill_name/SKILL.md"
      fi
      echo "  ✅ $skill_name"
      TOTAL=$((TOTAL + 1))
    fi
  done
done

echo ""
echo "=== Done: $TOTAL skills installed to $DEST ==="
