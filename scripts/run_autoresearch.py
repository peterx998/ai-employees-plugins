#!/usr/bin/env python3
"""
run_autoresearch.py — Autonomous experiment loop runner.

Adapted from karpathy/autoresearch's experiment loop:
  1. Run baseline evaluation
  2. Propose one small change to a SKILL.md or command
  3. Apply change (git commit)
  4. Run evaluation
  5. Compare score
  6. Keep if improved + hard constraint passed
  7. Discard if worse or hard constraint failed (git reset)
  8. Log to results.tsv
  9. Repeat (max N experiments, max $M cost)

Key differences from karpathy/autoresearch:
  - We modify SKILL.md / command .md files (not Python training code)
  - We use Golden Set pass rate (not val_bpb)
  - We have hard constraints (P1 medical, fee-request, compliance)
  - We have stricter budget controls (cost per session)
  - We do NOT run indefinitely — max 30 experiments per session
  - We generate a PR for human review after each session

Usage:
  python scripts/run_autoresearch.py --agent customer-support --tag cs-jul02
  python scripts/run_autoresearch.py --agent customer-support --report-only
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# Import evaluation runner
sys.path.insert(0, str(Path(__file__).parent))
from run_eval import run_evaluation, SCORING_RUBRICS, HARD_CONSTRAINTS


# ─── Budget Configuration ───

BUDGETS = {
    "customer-support": {"max_experiments": 30, "max_cost": 5.00, "timeout": 300},
    "influencer-outreach": {"max_experiments": 25, "max_cost": 4.00, "timeout": 300},
    "ad-creative": {"max_experiments": 20, "max_cost": 6.00, "timeout": 480},
    "shopify-growth": {"max_experiments": 20, "max_cost": 4.00, "timeout": 300},
    "b2b-sales": {"max_experiments": 20, "max_cost": 3.00, "timeout": 300},
}


def git_cmd(args, cwd=None):
    """Run a git command and return output."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd or os.getcwd(),
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def get_short_hash():
    """Get current git short hash."""
    out, _, _ = git_cmd(["rev-parse", "--short", "HEAD"])
    return out


def create_experiment_branch(tag):
    """Create an experiment branch."""
    branch_name = f"autoresearch/{tag}"
    out, err, rc = git_cmd(["checkout", "-b", branch_name])
    if rc != 0:
        # Branch might already exist
        git_cmd(["checkout", branch_name])
    return branch_name


def run_baseline(agent_name, golden_set_path=None):
    """Run baseline evaluation and return score."""
    print("\n--- Running Baseline ---")
    scorecard = run_evaluation(
        agent_name=agent_name,
        golden_set_path=golden_set_path,
        output_path=f"experiments/scorecards/{agent_name}/baseline.json",
    )
    return scorecard


def log_result(agent_name, commit, skill_modified, score, hard_pass, cost, status, description):
    """Log experiment result to TSV."""
    tsv_path = f"experiments/{agent_name}-results.tsv"

    # hard_pass as float
    hard_val = 1.0 if hard_pass else 0.0

    row = f"{commit}\t{agent_name}\t{skill_modified}\t{score:.4f}\t{hard_val:.1f}\t{cost:.2f}\t{status}\t{description}\n"

    with open(tsv_path, "a", encoding="utf-8") as f:
        f.write(row)

    print(f"  Logged: {row.strip()}")


def get_changed_files(base_commit):
    """Get list of files changed since base_commit."""
    out, _, rc = git_cmd(["diff", "--name-only", base_commit])
    if rc != 0:
        return []
    return [f.strip() for f in out.split("\n") if f.strip()]


def get_diff_stats(base_commit):
    """Get diff stats (insertions, deletions) since base_commit."""
    out, _, rc = git_cmd(["diff", "--stat", base_commit])
    if rc != 0:
        return 0, 0
    # Parse last line like "3 files changed, 10 insertions(+), 5 deletions(-)"
    lines = out.strip().split("\n")
    if not lines or not lines[-1]:
        return 0, 0
    last = lines[-1]
    insertions = 0
    deletions = 0
    if "insertion" in last:
        parts = last.split("insertion")
        insertions = int(parts[0].strip().split()[-1]) if parts[0].strip().split() else 0
    if "deletion" in last:
        parts = last.split("deletion")
        deletions = int(parts[0].strip().split()[-1]) if parts[0].strip().split() else 0
    return insertions, deletions


def compare_scores(baseline_score, new_score, baseline_hard, new_hard, has_changes, insertions, deletions):
    """Decide whether to keep or discard the change.

    Rules:
    1. No file changes → discard (no-op experiment)
    2. Hard constraint failed → discard
    3. Score improved + hard constraint passed → keep
    4. Score equal + complexity decreased (more deletions than insertions) → keep (simplification win)
    5. Score equal + no complexity decrease → discard (no-op)
    6. Score worse → discard
    """
    # Rule 1: No changes made
    if not has_changes:
        return "discard", "No file changes detected — no-op experiment"

    # Rule 2: Hard constraint failed
    if not new_hard:
        return "discard", "Hard constraint failed — auto-discard"

    if baseline_hard and not new_hard:
        return "discard", "Hard constraint regression — auto-discard"

    # Rule 3: Score improved
    if new_score > baseline_score:
        return "keep", f"Score improved: {baseline_score:.4f} → {new_score:.4f}"

    # Rule 4: Score equal + simplification (more deletions than insertions)
    if new_score == baseline_score and deletions > insertions:
        return "keep", f"Score equal, complexity decreased (-{insertions}+{deletions}) — simplification win"

    # Rule 5: Score equal, no simplification
    if new_score == baseline_score:
        return "discard", "Score equal, no simplification — no-op"

    # Rule 6: Score worse
    return "discard", f"Score regressed: {baseline_score:.4f} → {new_score:.4f}"


def generate_session_report(agent_name, tag, experiments):
    """Generate a human-readable session report."""
    report_path = f"experiments/sessions/session-{tag}.md"
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)

    kept = [e for e in experiments if e["status"] == "keep"]
    discarded = [e for e in experiments if e["status"] == "discard"]
    crashed = [e for e in experiments if e["status"] == "crash"]

    total_cost = sum(e["cost"] for e in experiments)

    report = f"""# Autoresearch Session Report

| Field | Value |
|-------|-------|
| Agent | {agent_name} |
| Tag | {tag} |
| Date | {datetime.utcnow().isoformat()}Z |
| Total experiments | {len(experiments)} |
| Kept | {len(kept)} |
| Discarded | {len(discarded)} |
| Crashed | {len(crashed)} |
| Total cost | ${total_cost:.2f} |

## Kept Changes

"""
    for e in kept:
        report += f"- `{e['commit']}` — {e['skill_modified']} — score: {e['score']:.4f} — {e['description']}\n"

    report += f"\n## Discarded Changes\n\n"
    for e in discarded:
        report += f"- `{e['commit']}` — {e['skill_modified']} — {e['description']}\n"

    report += f"""
## Next Steps

1. Review the kept changes in the PR
2. Run full regression test on merged changes
3. Start grayscale release if regression passes
4. Monitor for 48 hours before full rollout
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nSession report: {report_path}")
    return report_path


def main():
    parser = argparse.ArgumentParser(description="Run autoresearch experiment loop")
    parser.add_argument("--agent", required=True, help="Agent name")
    parser.add_argument("--tag", help="Run tag (e.g., cs-jul02)")
    parser.add_argument("--report-only", action="store_true", help="Only generate report from existing results")
    parser.add_argument("--max-experiments", type=int, help="Override max experiments")
    parser.add_argument("--max-cost", type=float, help="Override max cost")
    args = parser.parse_args()

    if args.report_only:
        # Generate report from existing TSV
        tsv_path = f"experiments/{args.agent}-results.tsv"
        if not Path(tsv_path).exists():
            print(f"No results found: {tsv_path}")
            sys.exit(1)

        experiments = []
        with open(tsv_path) as f:
            next(f)  # skip header
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 8:
                    experiments.append({
                        "commit": parts[0],
                        "agent": parts[1],
                        "skill_modified": parts[2],
                        "score": float(parts[3]),
                        "hard_pass": parts[4] == "1.0",
                        "cost": float(parts[5]),
                        "status": parts[6],
                        "description": parts[7],
                    })

        generate_session_report(args.agent, args.tag or "report", experiments)
        return

    # Normal experiment loop
    budget = BUDGETS.get(args.agent, {"max_experiments": 20, "max_cost": 5.0, "timeout": 300})
    max_experiments = args.max_experiments or budget["max_experiments"]
    max_cost = args.max_cost or budget["max_cost"]

    tag = args.tag or f"{args.agent.split('-')[0]}-{datetime.utcnow().strftime('%b%d').lower()}"

    print(f"=== Autoresearch: {args.agent} ===")
    print(f"Tag: {tag}")
    print(f"Budget: {max_experiments} experiments, ${max_cost:.2f} max cost")

    # Setup
    branch = create_experiment_branch(tag)
    print(f"Branch: {branch}")

    # Record base commit for safe reset
    base_commit, _, _ = git_cmd(["rev-parse", "HEAD"])
    print(f"Base commit: {base_commit[:7]}")

    # Baseline
    baseline = run_baseline(args.agent)
    baseline_score = baseline["overall_score"]
    baseline_hard = baseline["hard_constraint_passed"]

    log_result(
        agent_name=args.agent,
        commit=get_short_hash(),
        skill_modified="baseline",
        score=baseline_score,
        hard_pass=baseline_hard,
        cost=0.0,
        status="keep",
        description="baseline run",
    )

    # Experiment loop
    experiments = [{"commit": get_short_hash(), "agent": args.agent, "skill_modified": "baseline",
                     "score": baseline_score, "hard_pass": baseline_hard, "cost": 0.0,
                     "status": "keep", "description": "baseline run"}]

    total_cost = 0.0
    crash_count = 0

    print(f"\n--- Starting Experiment Loop (max {max_experiments}) ---")

    for i in range(max_experiments):
        if total_cost >= max_cost:
            print(f"\n⚠️  Budget exhausted: ${total_cost:.2f} >= ${max_cost:.2f}")
            break

        if crash_count >= 3:
            print(f"\n⚠️  3 consecutive crashes — stopping")
            break

        print(f"\n--- Experiment {i+1}/{max_experiments} ---")

        # NOTE: In a real autonomous run, the Agent (LLM) would:
        # 1. Analyze failed cases from baseline scorecard
        # 2. Propose a change to one SKILL.md or command
        # 3. Apply the change
        # 4. Commit
        #
        # This script provides the EVALUATION harness.
        # The Agent loop is orchestrated by the program.md instructions.

        # Detect what changed since base_commit
        changed_files = get_changed_files(base_commit)
        insertions, deletions = get_diff_stats(base_commit)
        has_changes = len(changed_files) > 0

        if has_changes:
            # Identify skill_modified from changed files
            skill_modified = ", ".join(changed_files)
            print(f"  Changed files: {skill_modified}")
            print(f"  Diff: +{insertions} -{deletions}")
        else:
            print(f"  No file changes detected since base commit")
            skill_modified = "none"

        try:
            scorecard = run_evaluation(
                agent_name=args.agent,
                output_path=f"experiments/scorecards/{args.agent}/exp-{i+1}.json",
                fail_on_no_output=False,  # Autoresearch uses expected as baseline
            )

            new_score = scorecard["overall_score"]
            new_hard = scorecard["hard_constraint_passed"]
            commit = get_short_hash()
            cost = 0.15  # Estimated cost per experiment (placeholder)

            decision, reason = compare_scores(
                baseline_score, new_score, baseline_hard, new_hard,
                has_changes, insertions, deletions
            )

            if decision == "keep":
                log_result(args.agent, commit, skill_modified, new_score, new_hard, cost, "keep", reason)
                experiments.append({"commit": commit, "agent": args.agent, "skill_modified": skill_modified,
                                   "score": new_score, "hard_pass": new_hard, "cost": cost,
                                   "status": "keep", "description": reason})
                baseline_score = new_score  # Update baseline for next comparison
                # Update base_commit to current HEAD so next experiment compares against this
                base_commit, _, _ = git_cmd(["rev-parse", "HEAD"])
                crash_count = 0
            else:
                log_result(args.agent, commit, skill_modified, new_score, new_hard, cost, "discard", reason)
                experiments.append({"commit": commit, "agent": args.agent, "skill_modified": skill_modified,
                                   "score": new_score, "hard_pass": new_hard, "cost": cost,
                                   "status": "discard", "description": reason})
                # Reset to known base_commit, not HEAD~1 (which could be wrong)
                git_cmd(["reset", "--hard", base_commit])
                crash_count = 0

            total_cost += cost

        except Exception as e:
            print(f"  ❌ CRASH: {e}")
            crash_count += 1
            log_result(args.agent, "0000000", skill_modified, 0.0, False, 0.0, "crash", str(e)[:100])
            experiments.append({"commit": "0000000", "agent": args.agent, "skill_modified": skill_modified,
                               "score": 0.0, "hard_pass": False, "cost": 0.0,
                               "status": "crash", "description": str(e)[:100]})

    # Generate session report
    generate_session_report(args.agent, tag, experiments)

    print(f"\n=== Session Complete ===")
    print(f"Experiments: {len(experiments)}")
    print(f"Kept: {len([e for e in experiments if e['status'] == 'keep'])}")
    print(f"Discarded: {len([e for e in experiments if e['status'] == 'discard'])}")
    print(f"Total cost: ${total_cost:.2f}")


if __name__ == "__main__":
    main()
