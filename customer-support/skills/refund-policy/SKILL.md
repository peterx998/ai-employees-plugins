---
name: refund-policy
description: "Use when a customer requests a refund, return, or exchange, or when a triaged refund-return ticket needs policy evaluation. Provides region-specific (US/CA/MX/EU) refund windows, eligibility rules, non-refundable items, defective device handling, and refund process steps. Outputs structured eligibility decisions for draft-response."
user_invocable: true
version: "1.1.0"
tags: [refund, return, exchange, policy, region, defective, customer-support]
---

## 1. Role

The refund-policy skill is the **policy authority** for all refund, return, and exchange decisions. Given a triaged refund-return ticket, it evaluates the customer's eligibility based on region-specific rules, purchase date, product type, and defect status. It outputs a structured eligibility decision that the `draft-response` skill consumes to draft the customer-facing response.

This skill does **not** draft responses or communicate with customers. It provides policy decisions and process steps only.

---

## 2. Trigger

- ticket-triage classifies a message as `refund-return`.
- A human agent requests a policy lookup for a specific order.
- draft-response needs refund eligibility context before drafting.
- A refund exception request is being evaluated.

---

## 3. Required Inputs

| Field | Type | Required | Description |
|---|---|---|---|
| `triage_output` | object | Yes | Full triage JSON from ticket-triage. |
| `region` | string | Yes | Customer region: US, CA, MX, or EU. |
| `order_number` | string | Yes* | Shopify order number. *Required if available; if missing, flag `needs_order_lookup`. |
| `order_data` | object | No | Shopify order details (purchase date, items, amounts). |
| `product_sku` | string | No | Product SKU for non-refundable item check. |
| `defect_reported` | boolean | No | Whether the customer reported a defect. |
| `defect_description` | string | No | Description of the defect if reported. |
| `message` | string | Yes | Original customer message for context. |

---

## 4. Decision Framework

### 4.1 Region-Specific Policy Matrix

| Policy | US | CA | MX | EU |
|---|---|---|---|---|
| **Standard return window** | 30 days from delivery | 30 days from delivery | 15 days from delivery | 14 days from delivery (statutory right) |
| **Extended return window (members)** | 45 days | 45 days | 30 days | 30 days |
| **Refund method** | Original payment method | Original payment method | Original payment method or store credit | Original payment method |
| **Shipping cost refund** | Refunded if company error; not refunded for preference returns | Same as US | Not refunded | Refunded if company error; not refunded for preference returns |
| **Restocking fee** | None | None | 10% of item price | None (EU consumer law prohibits) |
| **Defective item return window** | No limit (within warranty period) | No limit (within warranty period) | 30 days from delivery | 2 years (EU statutory warranty) |
| **Return shipping label** | Free for defective; customer pays for preference returns | Free for defective; customer pays for preference returns | Customer pays all return shipping | Free for defective; company pays for preference returns (EU consumer law) |
| **Refund processing time** | 5–7 business days | 5–7 business days | 10–15 business days | 14 business days (statutory) |
| **Store credit option** | Available, +5% bonus | Available, +5% bonus | Available | Available |
| **Exchange option** | Available | Available | Available | Available |

### 4.2 Non-Refundable Items

The following items are **never eligible for refund or return**, regardless of region:

| Category | Items | Reason |
|---|---|---|
| Personal hygiene | Ear tips, nasal inserts, mouthpieces, brush heads | Hygiene/contamination risk |
| Consumables | Gel cartridges, serum pods, replacement pads | Consumed product cannot be returned |
| Opened skincare | Opened or used skincare products | Contamination risk |
| Custom/Personalized | Custom-engraved devices, personalized color combinations | Cannot be resold |
| Gift cards | Digital and physical gift cards | Non-refundable by policy |
| Final sale items | Items marked "final sale" at purchase | Explicitly non-refundable |

**Exception:** If a non-refundable item is **defective**, it may be eligible for replacement (not refund) at the company's discretion. Route to tier-2 for defective non-refundable item evaluation.

### 4.3 Defective Device Handling

| Scenario | Eligible For | Process |
|---|---|---|
| Defect within 30 days of delivery (all regions) | Full refund OR replacement | Free return label, no restocking fee, expedited processing |
| Defect within warranty period (after 30 days) | Replacement (preferred) or prorated refund | RMA process, warranty validation, free return label |
| Defect outside warranty period | Not eligible for standard refund/replacement | Route to tier-2 for goodwill evaluation. May offer discount on replacement. |
| Safety-related defect (overheating, electrical) | Full refund + replacement | Immediate escalation. Do NOT require customer to return device if safety risk. Route to escalate-risk. |
| Defective non-refundable item | Replacement only | Route to tier-2. No refund. |

### 4.4 Refund Eligibility Decision Flow

```
Refund/return request
  ├─ Is the item non-refundable? → Not eligible for refund. Check if defective → replacement only (tier-2).
  ├─ Is the item defective?
  │    ├─ Safety-related? → Full refund + replacement. Escalate to escalate-risk.
  │    ├─ Within warranty? → Replacement or prorated refund. Start RMA.
  │    └─ Outside warranty? → Not eligible. Route to tier-2 for goodwill evaluation.
  ├─ Is the request within the standard return window?
  │    ├─ Yes → Eligible for full refund. Start standard return process.
  │    └─ No → Check extended window (member?)
  │         ├─ Within extended window? → Eligible. Start return process.
  │         └─ Outside all windows? → Not eligible. Flag for human review / exception.
  ├─ Dispute language present? → P2. Route to tier-2. Suppress auto-deny.
  └─ Ambiguous? → Flag for human review.
```

---

## 5. Tool Usage

| Tool | When | Purpose |
|---|---|---|
| `shopify.read_orders` | Always when order_number or customer_email available | Get purchase date, delivery date, items, amounts for eligibility calculation. |
| `kb.search` | When product SKU or non-refundable check needed | Verify product categorization and refund eligibility. |
| `escalate-risk` | When safety-related defect detected | Escalate immediately. Do not process as standard return. |
| `draft-response` | After eligibility decision is made | Provide policy context for response drafting. |

**Sequencing:** Order lookup → Product/SKU verification → Eligibility calculation → Output decision. Do not make eligibility decisions without verified order data.

---

## 6. Output Contract

```json
{
  "policy_id": "pol_<timestamp>_<order_number>",
  "order_number": "10245",
  "region": "US",
  "decision": "eligible",
  "decision_reason": "Request is within 30-day standard return window for US. Item is not on non-refundable list. No defect reported — preference return.",
  "eligible_for": ["refund", "store_credit", "exchange"],
  "refund_amount": 149.00,
  "refund_currency": "USD",
  "refund_method": "original_payment",
  "shipping_cost_refund": false,
  "restocking_fee": 0,
  "return_window_days": 30,
  "days_since_delivery": 12,
  "return_label_cost": "customer_pays",
  "refund_processing_time": "5-7 business days",
  "process_steps": [
    "Generate return label and send to customer",
    "Customer ships item back within 14 days",
    "Warehouse receives and inspects item",
    "Refund processed within 5-7 business days of warehouse receipt"
  ],
  "exception_flag": false,
  "human_review_required": false,
  "notes": "Standard preference return within window. No complications."
}
```

| Field | Type | Constraints |
|---|---|---|
| `decision` | enum | One of: `eligible`, `not_eligible`, `eligible_with_exception`, `replacement_only` |
| `refund_amount` | number | Must match order data. `null` if not eligible. |
| `exception_flag` | boolean | `true` when request is outside standard window but may qualify for exception. |
| `human_review_required` | boolean | `true` for exceptions, disputes, defective non-refundable items, and out-of-warranty defects. |
| `process_steps` | array | 3–7 specific steps for completing the refund/return. |

---

## 7. Risk Boundaries

1. **Never auto-deny a refund without human review if dispute language is present.** If the customer threatens chargeback or uses legal language, route to tier-2. Do not send an automated denial.
2. **Never process a refund for a non-refundable item** without tier-2 approval. Non-refundable items can only receive replacements (if defective) with human approval.
3. **Never quote refund amounts without verified Shopify order data.** Do not estimate or guess amounts.
4. **Never override region-specific policies.** EU 14-day statutory right cannot be shortened. MX 15-day window cannot be extended without manager approval.
5. **Safety-related defects always escalate.** Do not process as a standard return. The device may need to be quarantined. Route to `escalate-risk` immediately.
6. **Never require a customer to return a potentially dangerous device.** If the defect poses a safety risk (overheating, electrical hazard), advise the customer to stop using it and do not require return shipping.
7. **Store credit bonus is optional, not guaranteed.** Present it as an option, not a default. The customer must choose.
8. **All exception decisions require human approval.** The skill can flag `eligible_with_exception` but cannot finalize an exception refund without a human agent's approval.

---

## 8. Examples

### Example 1: Standard US Return Within Window (P3)

**Input:**
```
region: US
order_number: 10245
order_data: { purchase_date: "2026-06-20", delivery_date: "2026-06-22", items: [{ sku: "GLOW-SKIN-01", name: "GlowSkin Facial Device", price: 149.00 }], total: 149.00 }
days_since_delivery: 12
defect_reported: false
message: "I'd like to return my GlowSkin. It works fine, just not for me."
```

**Output:**
```json
{
  "policy_id": "pol_20260702_10245",
  "order_number": "10245",
  "region": "US",
  "decision": "eligible",
  "decision_reason": "Standard preference return within 30-day US return window. Item not on non-refundable list. No defect reported.",
  "eligible_for": ["refund", "store_credit", "exchange"],
  "refund_amount": 149.00,
  "refund_currency": "USD",
  "refund_method": "original_payment",
  "shipping_cost_refund": false,
  "restocking_fee": 0,
  "return_window_days": 30,
  "days_since_delivery": 12,
  "return_label_cost": "customer_pays",
  "refund_processing_time": "5-7 business days",
  "process_steps": [
    "Generate prepaid return label and email to customer ($7.95 deducted from refund)",
    "Customer ships item back within 14 days of receiving label",
    "Warehouse receives and inspects item for completeness and condition",
    "Refund processed to original payment method within 5-7 business days of warehouse receipt"
  ],
  "exception_flag": false,
  "human_review_required": false,
  "notes": "Standard preference return. Offer store credit option with 5% bonus ($156.45)."
}
```

### Example 2: EU Return — Outside Standard Window but Within Statutory Right (P3)

**Input:**
```
region: EU
order_number: 10250
order_data: { purchase_date: "2026-06-15", delivery_date: "2026-06-18", items: [{ sku: "GLOW-SKIN-01", name: "GlowSkin Facial Device", price: 149.00 }], total: 159.00 (incl. shipping) }
days_since_delivery: 14
defect_reported: false
message: "I would like to return the device under my EU right of withdrawal."
```

**Output:**
```json
{
  "policy_id": "pol_20260702_10250",
  "order_number": "10250",
  "region": "EU",
  "decision": "eligible",
  "decision_reason": "EU statutory right of withdrawal allows 14 days from delivery. Request is on day 14 — within window. Company pays return shipping per EU consumer law.",
  "eligible_for": ["refund", "exchange"],
  "refund_amount": 159.00,
  "refund_currency": "EUR",
  "refund_method": "original_payment",
  "shipping_cost_refund": true,
  "restocking_fee": 0,
  "return_window_days": 14,
  "days_since_delivery": 14,
  "return_label_cost": "company_pays",
  "refund_processing_time": "14 business days",
  "process_steps": [
    "Generate free return label and email to customer",
    "Customer ships item back within 14 days",
    "Warehouse receives and inspects item",
    "Full refund (including original shipping) processed within 14 business days of warehouse receipt"
  ],
  "exception_flag": false,
  "human_review_required": false,
  "notes": "EU statutory withdrawal. Full refund including shipping. No restocking fee per EU law."
}
```

### Example 3: US Return Outside Window — Exception Request (P2)

**Input:**
```
region: US
order_number: 10246
order_data: { purchase_date: "2026-05-25", delivery_date: "2026-05-28", items: [{ sku: "GLOW-SKIN-01", name: "GlowSkin Facial Device", price: 149.00 }], total: 149.00 }
days_since_delivery: 35
defect_reported: false
message: "I want a full refund. The product doesn't work as advertised and 35 days isn't that far past your window."
```

**Output:**
```json
{
  "policy_id": "pol_20260702_10246",
  "order_number": "10246",
  "region": "US",
  "decision": "eligible_with_exception",
  "decision_reason": "Request is 5 days past the 30-day US standard return window. No membership on file for extended window. Customer cites product expectations mismatch. Exception possible with human approval.",
  "eligible_for": ["refund", "store_credit"],
  "refund_amount": 149.00,
  "refund_currency": "USD",
  "refund_method": "original_payment",
  "shipping_cost_refund": false,
  "restocking_fee": 0,
  "return_window_days": 30,
  "days_since_delivery": 35,
  "return_label_cost": "pending_exception_approval",
  "refund_processing_time": "5-7 business days post-approval",
  "process_steps": [
    "Submit exception request to support lead for review",
    "Support lead evaluates: purchase history, reason, product condition",
    "If approved: generate return label and process as standard return",
    "If denied: offer store credit or discount on future purchase as goodwill",
    "Communicate decision to customer within 48 hours"
  ],
  "exception_flag": true,
  "human_review_required": true,
  "notes": "5 days past window. Customer cites expectations mismatch — not defective. No dispute language yet but monitor. Do not auto-deny."
}
```

### Example 4: Defective Device — Safety-Related (P1/P2)

**Input:**
```
region: US
order_number: 10251
order_data: { purchase_date: "2026-06-10", delivery_date: "2026-06-12", items: [{ sku: "GLOW-SKIN-01", name: "GlowSkin Facial Device", price: 149.00 }], total: 149.00 }
days_since_delivery: 20
defect_reported: true
defect_description: "The device got extremely hot while charging and the plastic started melting. I unplugged it immediately."
message: "The device overheated while charging and the plastic is melting. This is a serious safety issue!"
```

**Output:**
```json
{
  "policy_id": "pol_20260702_10251",
  "order_number": "10251",
  "region": "US",
  "decision": "eligible",
  "decision_reason": "Safety-related defect reported (overheating, melting). Full refund and replacement authorized. Do not require return of potentially dangerous device. Escalate to escalate-risk immediately.",
  "eligible_for": ["refund", "replacement"],
  "refund_amount": 149.00,
  "refund_currency": "USD",
  "refund_method": "original_payment",
  "shipping_cost_refund": true,
  "restocking_fee": 0,
  "return_window_days": "n/a_defective",
  "days_since_delivery": 20,
  "return_label_cost": "company_pays",
  "refund_processing_time": "expedited_1-2 business days",
  "process_steps": [
    "ESCALATE TO escalate-risk IMMEDIATELY — safety defect",
    "Process full refund immediately (expedited 1-2 business days)",
    "Do NOT require customer to return the device — safety hazard",
    "Ship replacement device via expedited shipping at no cost",
    "Log incident in product safety registry",
    "Notify product team for investigation and potential recall assessment"
  ],
  "exception_flag": false,
  "human_review_required": true,
  "notes": "SAFETY DEFECT: overheating + melting. Do not require return. Expedite refund. Escalate to escalate-risk for medical-review routing if any injury reported."
}
```

---

## 9. Evaluation Cases

| Case ID | Scenario | Region | Expected Decision | Human Review |
|---|---|---|---|---|
| REF-001 | Standard return, 12 days, US | US | eligible | No |
| REF-002 | Return after 35 days, US | US | eligible_with_exception | Yes |
| REF-003 | EU statutory withdrawal, day 14 | EU | eligible | No |
| REF-004 | MX return, 20 days (past 15-day window) | MX | eligible_with_exception | Yes |
| REF-005 | Defective device, overheating | US | eligible (safety) | Yes (escalate) |
| REF-006 | Non-refundable item (opened skincare) | US | not_eligible | No |
| REF-007 | Defective non-refundable item | EU | replacement_only | Yes |
| REF-008 | Member return, 40 days, US | US | eligible (extended) | No |
| REF-009 | Return after 60 days, no defect | CA | not_eligible | Yes (goodwill) |
| REF-010 | Chargeback threat, 10 days | US | eligible (expedite) | Yes (tier-2) |

---

## 10. Failure Modes

| Failure Mode | Description | Mitigation |
|---|---|---|
| **Auto-deny without exception review** | System denies refund because it's 1 day past window, ignoring context. | Any request within 7 days of the window end triggers `eligible_with_exception` flag and human review. Never auto-deny. |
| **Wrong region policy applied** | US 30-day window applied to an EU customer (should be 14 days). | Region is a required input. Policy matrix is keyed by region. Validation check: if region is EU, statutory rights always take precedence. |
| **Safety defect processed as standard return** | Overheating device handled as a normal return, missing the escalation. | Keyword detection for safety terms (overheating, melting, sparking, smoking, burning). Safety defects always route to escalate-risk. |
| **Non-refundable item refunded** | Opened skincare product refunded because the system didn't check the SKU. | SKU verification against non-refundable list before any eligibility decision. If SKU is on the list, decision is `not_eligible` (or `replacement_only` if defective). |
| **Refund amount mismatch** | Quoted refund amount doesn't match Shopify order total (e.g., excludes tax). | Refund amount is calculated from Shopify `order_data.total` which includes tax and shipping. Never calculate manually. |
| **Return label not provided** | Customer is told to return the item but no label or instructions are given. | Process steps always include label generation as step 1. If return label cost is `company_pays`, label is prepaid. If `customer_pays`, label is generated but cost is deducted from refund. |
| **Store credit forced** | Customer is given store credit instead of their preferred refund method. | Store credit is presented as an option, not a default. The `eligible_for` array lists all options. Customer's preference is respected. |
| **Restocking fee applied in EU** | 10% restocking fee applied to an EU return, violating consumer law. | EU entries in the policy matrix have `restocking_fee: 0` hardcoded. EU consumer law prohibits restocking fees for statutory withdrawals. |
