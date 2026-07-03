# Experiments — Run Directory

Isolated experiment runs with safe prune semantics.

Adapted from kunchenguid/treehouse: each run is isolated, dirty/unmerged
runs are protected from pruning, and only completed/archived runs are cleaned.

## Directory Structure

```
experiments/runs/
├── active/          # Currently running experiments (DO NOT DELETE)
│   └── <agent>/
│       ├── findings.json
│       ├── pr_body.md
│       └── run.log
├── archived/        # Completed, merged experiments (safe to prune)
│   └── <agent>-<timestamp>/
│       ├── findings.json
│       ├── pr_body.md
│       └── run.log
├── failed/          # Failed experiments with P1 regression (preserved for RCA)
│   └── <agent>-<timestamp>/
│       └── findings.json
├── disposable/      # Temporary experiments, auto-cleaned
│   └── <worktree-path> -> symlink to treehouse worktree
└── README.md
```

## Prune Rules

When running `python scripts/agent_gate.py` or CI cleanup:

✓ Safe to delete:
  - active/ runs older than 24h with PASS verdict
  - archived/ runs older than 7 days
  - disposable/ symlinks to removed worktrees

✗ DO NOT delete:
  - active/ with FAIL or NEEDS_REVIEW verdict
  - active/ from last 24 hours
  - failed/ directory (contains P1 regression evidence)
  - Any run with unmerged changes
  - Any run referenced in a pending PR

## Worktree Integration

When using `scripts/run_in_treehouse.sh`, the disposable/ directory
contains symlinks to treehouse worktree paths:

```bash
# Create isolated run
bash scripts/run_in_treehouse.sh --keep customer-support \
  python scripts/agent_gate.py --agent customer-support

# Worktree location: ../.treehouse-pool/customer-support/
# Symlink: experiments/runs/disposable/customer-support -> ../.treehouse-pool/customer-support/
```

## Auto-prune on Gate Completion

`scripts/agent_gate.py` will:
1. Move run from active/ to archived/ on PASS
2. Move run from active/ to failed/ on FAIL with P1 regression
3. Leave run in active/ for NEEDS_REVIEW
