#!/usr/bin/env bash
# install-codex.sh — Install all AI Employee skills to Codex CLI
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
CODEX_SKILLS="$HOME/.codex/skills"

echo "=== AI Employees — Codex Install ==="
echo ""

install_skill() {
    local plugin=$1
    local skill=$2
    local src="$REPO/${plugin}/skills/${skill}/SKILL.md"
    local dst="$CODEX_SKILLS/${skill}"

    if [ -f "$src" ]; then
        mkdir -p "$dst"
        cp "$src" "$dst/SKILL.md"
        echo "  ✅ ${plugin}/${skill}"
    else
        echo "  ⚠️  ${plugin}/${skill} — SKILL.md not found, skipping"
    fi
}

echo "Installing Customer Support skills..."
for skill in ticket-triage draft-response escalate-risk refund-policy shipping-policy; do
    install_skill "customer-support" "$skill"
done

echo ""
echo "Installing Influencer Outreach skills..."
for skill in creator-research draft-first-touch classify-reply follow-up usage-rights-check collaboration-policy; do
    install_skill "influencer-outreach" "$skill"
done

echo ""
echo "Installing Ad Creative skills..."
for skill in analyze-video segment-ugc score-segments compliance-review build-ad-brief hook-framework; do
    install_skill "ad-creative" "$skill"
done

echo ""
echo "Installing Shopify Growth skills..."
for skill in product-page-review seo-audit landing-page-brief faq-generate review-import-check; do
    install_skill "shopify-growth" "$skill"
done

echo ""
echo "Installing B2B Sales skills..."
for skill in qualify-lead draft-quote follow-up-inquiry summarize-buyer escalate-high-value product-policy distributor-fit-score; do
    install_skill "b2b-sales" "$skill"
done

echo ""
echo "Installing Evaluation skills..."
for skill in golden-set regression-test grayscale-release error-review; do
    install_skill "agent-evaluation" "$skill"
done

echo ""
echo "=== Done! ==="
echo "Skills installed to: $CODEX_SKILLS/"
echo ""
echo "Codex auto-discovers SKILL.md files in ~/.codex/skills/"
echo "Skills will activate automatically when relevant."
