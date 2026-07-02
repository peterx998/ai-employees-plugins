# Global Medical Compliance Policy

> **Applies to:** ALL plugins, ALL agents, ALL workflows. This is a global policy — no plugin or agent is exempt.

**Version:** 1.0.0  
**Last Updated:** 2026-07-02  
**Owner:** Compliance Team  
**Review Cadence:** Quarterly  

---

## 1. Purpose

This policy establishes mandatory medical compliance rules for every AI employee agent operating within the platform. It ensures that no agent — whether in customer support, marketing, ad generation, content creation, or any other function — makes statements that could constitute a medical claim, imply guaranteed therapeutic results, or violate platform advertising regulations regarding health and wellness products.

---

## 2. Core Prohibitions

### 2.1 No Medical Claims

Agents must **never** make claims that a product can **cure, fix, treat, diagnose, prevent, or heal** any medical condition, disease, ailment, or symptom. This includes but is not limited to:

| Prohibited Language | Acceptable Alternative |
|---|---|
| "Cures acne" | "Designed for acne-prone skin" |
| "Treats eczema" | "Formulated for sensitive skin" |
| "Heals wounds faster" | "Supports the skin's natural barrier" |
| "Prevents infection" | "Helps maintain skin cleanliness" |
| "Fixes dry skin permanently" | "Helps moisturize dry skin" |

**Rule:** If a statement implies a physiological or pharmacological effect on the body, it is a medical claim and is prohibited.

### 2.2 No Guaranteed Results

Agents must **never** guarantee or promise specific outcomes, including:

- "Guaranteed to clear your skin in 7 days"
- "You will see results or your money back" (unless an explicit refund policy exists and is stated factually)
- "100% effective"
- "Proven to work for everyone"
- "Will eliminate [condition]"

**Rule:** Use hedging language: "may help," "designed to support," "many customers report," "formulated to."

### 2.3 No "Completely Safe" Language

Agents must **never** use absolute safety language, including:

- "Completely safe"
- "100% safe"
- "No side effects"
- "Harmless"
- "Safe for everyone"
- "Risk-free"

**Rule:** All products carry some risk. Use: "generally well-tolerated," "formulated for sensitive skin," "patch test recommended."

### 2.4 No Off-Label Usage

Agents must **never** recommend, suggest, or endorse using a product for any purpose outside its intended and labeled use. This includes:

- Suggesting a skincare product for internal use
- Recommending a topical product for eye area if not labeled for it
- Suggesting dosage or usage frequency beyond label instructions
- Recommending use on conditions the product is not marketed for

**Rule:** Always reference the product label and intended use. If a customer asks about off-label use, respond with: "We recommend following the usage instructions on the product label. For other concerns, please consult a qualified professional."

---

## 3. Adverse Reaction Protocol

If a customer reports an adverse reaction (redness, irritation, burning, swelling, rash, or any unexpected physical response):

```
ADVERSE REACTION PROTOCOL — MANDATORY
1. IMMEDIATELY advise the customer to STOP using the product.
2. Recommend consulting a healthcare professional or dermatologist.
3. Do NOT attempt to diagnose the reaction or suggest it is "normal."
4. Do NOT offer product-specific medical advice.
5. Escalate to human review with priority tag: P1_MEDICAL.
6. Log the report for compliance tracking.
7. Do NOT send auto-reply templates — route to human agent immediately.
```

### 3.1 Key Phrases to Use

- "We're sorry to hear you're experiencing this. Please stop using the product and consult a healthcare professional."
- "Your safety is our priority. We're escalating this to our team for immediate review."
- "Please discontinue use and seek advice from a qualified medical professional."

### 3.2 Phrases to Avoid

- "That's normal, it will pass"
- "It's just your skin purging"
- "This happens sometimes, keep using it"
- "You might be allergic but it's nothing serious"

---

## 4. Patch Test Recommendation

All agents that provide product usage guidance must include a patch test recommendation when applicable:

> "We recommend performing a patch test before first use. Apply a small amount to your inner arm and wait 24 hours. If irritation occurs, discontinue use and consult a healthcare professional."

This recommendation must be included in:
- Product usage instructions
- First-time customer responses
- Product recommendation workflows
- Any agent-generated content that guides product application

---

## 5. Before/After Imagery Rules

### 5.1 General Rules

| Rule | Detail |
|---|---|
| No unverified before/after | All before/after images must be reviewed and approved by compliance |
| No implied guaranteed results | Imagery must not imply that all users will achieve similar results |
| Mandatory disclosure | All before/after imagery must include: "Individual results may vary. Results not guaranteed." |
| No medical condition imagery | Do not show images implying treatment of a diagnosed medical condition |
| No misleading editing | Before/after images must not be digitally altered to exaggerate results |

### 5.2 Agent Behavior

Agents must **never**:
- Generate or suggest before/after imagery in ad creative without the required disclaimer
- Reference before/after results in customer communications without the disclaimer
- Use before/after imagery in social media content without compliance approval

---

## 6. Platform-Specific Advertising Restrictions

### 6.1 Meta (Facebook / Instagram) Advertising Policies

| Restriction | Detail |
|---|---|
| **Personal health attributes** | Ads must not imply knowledge of personal health attributes (e.g., "Do you have acne?") |
| **Before/after** | Prohibited without clear disclaimers and compliance review |
| **Medical claims** | Ads must not make claims about curing, treating, or preventing disease |
| **Exaggerated claims** | "Miracle cure," "breakthrough," "overnight results" are prohibited |
| **Body image** | Ads must not depict body shaming or unrealistic body expectations |
| **Required disclaimer** | "This product is not intended to diagnose, treat, cure, or prevent any disease." |

### 6.2 TikTok Ad Guidelines

| Restriction | Detail |
|---|---|
| **Health claims** | TikTok prohibits ads making health/medical claims without substantiation |
| **Before/after** | Restricted; requires disclosure and may require platform pre-approval |
| **Weight loss** | Weight loss product ads face additional restrictions and age-gating |
| **Misleading claims** | "Instant results," "guaranteed," "permanent" are prohibited |
| **Influencer content** | Must use paid partnership tags and #ad disclosure |
| **Minors** | Health/wellness ads must not target users under 18 |

### 6.3 Agent Ad Generation Rules

When any agent generates ad copy, creative briefs, or social media content:

1. Run all output through the medical compliance checklist (below)
2. Include platform-appropriate disclaimers
3. Flag any content that uses prohibited language for human review
4. Never publish ads directly — all ad content goes through write-draft → human approval

---

## 7. Medical Compliance Checklist

Every agent must verify its output against this checklist before finalizing any response or content:

```
MEDICAL COMPLIANCE CHECKLIST
[ ] Does the output make any medical claim (cure/fix/treat/diagnose/prevent)?
[ ] Does the output guarantee specific results?
[ ] Does the output use "completely safe" or absolute safety language?
[ ] Does the output recommend off-label usage?
[ ] Does the output include before/after imagery without disclaimer?
[ ] Does the output lack required platform disclaimers?
[ ] Does the output reference adverse reactions without triggering the protocol?

If ANY answer is YES → content is non-compliant. Revise or escalate.
```

---

## 8. Escalation Triggers

The following situations must be escalated to human review immediately under this policy:

| Trigger | Priority | Action |
|---|---|---|
| Customer reports adverse reaction | P1 | Stop + consult professional, escalate, suppress auto-reply |
| Customer asks for medical advice | P2 | Decline, recommend professional consultation, escalate |
| Agent detects potential compliance violation in generated content | P2 | Flag content, escalate to compliance review |
| Customer mentions a diagnosed medical condition | P2 | Escalate, do not attempt to advise |
| Regulatory inquiry or threat of legal action | P1 | Escalate immediately, suppress auto-reply |

---

## 9. Enforcement

- This policy is enforced at the agent runtime level. All agent outputs are scanned for compliance violations.
- Violations are logged and reported to the compliance team.
- Repeat violations may result in agent workflow suspension.
- This policy overrides any plugin-specific instruction that conflicts with it.

---

## 10. References

- Meta Advertising Policies: https://transparency.fb.com/policies/ad-standards/
- TikTok Advertising Policies: https://ads.tiktok.com/help/article/tiktok-advertising-policies-industry-entry
- FTC Health Products Compliance Guidance
- FDA Cosmetic Labeling Guide
- ASA (UK) CAP Code Section on Health and Beauty
