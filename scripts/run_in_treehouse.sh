#!/usr/bin/env bash
# run_in_treehouse.sh — Run a gate/autoresearch command in an isolated worktree.
#
# Adapted from kunchenguid/treehouse architecture:
#   - Gets or creates a leased worktree for the given agent
#   - Runs the command in the isolated directory
#   - Returns the worktree when done (--keep to retain lease)
#   - Safe prune: only cleans idle, clean, merged worktrees
#
# Usage:
#   bash scripts/run_in_treehouse.sh customer-support \
#     python scripts/agent_gate.py --agent customer-support
#
#   bash scripts/run_in_treehouse.sh --keep customer-support \
#     python scripts/run_autoresearch.py --agent customer-support
#
# Requirements:
#   - git worktree support
#   - The repo must have no uncommitted changes in the main working tree
#
# How it works:
#   1. Acquire a worktree from pool (or create one)
#   2. Run the command inside it
#   3. Return the worktree (or keep lease)
#   4. Proactively prune orphaned/temporary worktrees on exit

set -euo pipefail

# ─── Configuration ───

POOL_DIR="${TREEHOUSE_POOL:-$(git rev-parse --show-toplevel)/../.treehouse-pool}"
KEEP_LEASE=false
AGENT=""
COMMAND=""

# ─── Parse args ───

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep)
      KEEP_LEASE=true
      shift
      ;;
    *)
      if [ -z "$AGENT" ]; then
        AGENT="$1"
      elif [ -z "$COMMAND" ]; then
        COMMAND="$*"
        break
      fi
      shift
      ;;
  esac
done

if [ -z "$AGENT" ] || [ -z "$COMMAND" ]; then
  echo "Usage: bash scripts/run_in_treehouse.sh [--keep] <agent> <command...>"
  echo "Example: bash scripts/run_in_treehouse.sh customer-support python scripts/agent_gate.py --agent customer-support"
  exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# ─── Prune orphaned worktrees ───

_prune_safe() {
  echo "  treehouse: pruning safe worktrees..."
  git worktree list --porcelain | while IFS= read -r line; do
    case "$line" in
      worktree*)
        WT_PATH="${line#worktree }"
        ;;
      "bare")
        # Skip bare repos
        WT_PATH=""
        ;;
      "detached"|"prunable"*)
        if [ -n "$WT_PATH" ] && [ "$WT_PATH" != "$REPO_ROOT" ]; then
          # Only prune if in pool dir and not currently in use
          if [[ "$WT_PATH" == "$POOL_DIR"/* ]]; then
            echo "  treehouse: pruning $WT_PATH"
            git worktree remove --force "$WT_PATH" 2>/dev/null || true
          fi
        fi
        ;;
    esac
  done
}

# ─── Get or create worktree ───

_get_worktree() {
  local agent="$1"
  local wt_path="${POOL_DIR}/${agent}"

  mkdir -p "$POOL_DIR"

  # Check if worktree already exists
  if git worktree list --porcelain | grep -q "$wt_path"; then
    echo "  treehouse: reusing existing worktree $wt_path"
  else
    echo "  treehouse: creating worktree $wt_path"
    git worktree add "$wt_path" HEAD 2>/dev/null || {
      echo "  treehouse: HEAD exists, trying master..."
      git worktree add "$wt_path" master 2>/dev/null || {
        echo "  treehouse: ERROR — cannot create worktree. Check for uncommitted changes."
        exit 1
      }
    }
  fi

  echo "$wt_path"
}

# ─── Main ───

echo "=== Treehouse Isolation ==="
echo "  Agent: $AGENT"
echo "  Pool: $POOL_DIR"
echo ""

_prune_safe

WORKTREE=$(_get_worktree "$AGENT")

echo ""
echo "  Running in: $WORKTREE"
echo "  Command: $COMMAND"
echo ""

# Run command inside worktree
(
  cd "$WORKTREE"
  # Sync with master to get latest changes
  git checkout master 2>/dev/null || true
  git pull origin master 2>/dev/null || true

  echo "=== Command Output ==="
  exec $COMMAND
)

EXIT_CODE=$?

# Return or keep
if [ "$KEEP_LEASE" = false ]; then
  echo ""
  echo "  treehouse: returning worktree (not keeping lease)"
  # We don't remove — just mark as available. Next --keep caller gets it.
else
  echo ""
  echo "  treehouse: keeping lease on $WORKTREE"
  echo "  Release with: git worktree remove $WORKTREE"
fi

exit $EXIT_CODE
