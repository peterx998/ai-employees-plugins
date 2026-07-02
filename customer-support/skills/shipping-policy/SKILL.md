---
name: shipping-policy
description: "Use when a customer asks about shipping options, delivery times, tracking, customs/duties, or delayed/lost packages. Provides region-specific shipping options, carrier details, tracking status meanings, and procedures for delayed or lost packages. Outputs structured shipping context for draft-response."
user_invocable: true
version: "1.1.0"
tags: [shipping, tracking, customs, duties, logistics, lost-package, customer-support]
---

## 1. Role

The shipping-policy skill is the **shipping and logistics authority** for customer support. Given a triaged `order-status` ticket, it retrieves and interprets shipping data (from Shopify), provides region-specific shipping options and delivery timeframes, explains tracking statuses, and guides the resolution of delayed or lost packages.

This skill does **not** draft customer-facing responses. It provides structured shipping context that `draft-response` consumes.

---

## 2. Trigger

- ticket-triage classifies a message as `order-status`.
- A customer asks about shipping options before or after purchase.
- A customer reports a delayed, missing, or lost package.
- A customer asks about customs, duties, or import taxes.
- draft-response needs shipping context before drafting.

---

## 3. Required Inputs

| Field | Type | Required | Description |
|---|---|---|---|
| `triage_output` | object | Yes | Full triage JSON from ticket-triage. |
| `region` | string | Yes | Destination region: US, CA, MX, EU, or INT (international other). |
| `order_number` | string | Yes* | Shopify order number. *Required if order exists. |
| `order_data` | object | No | Shopify order details including shipping method, tracking number, carrier. |
| `tracking_number` | string | No | Tracking number if available. |
| `message` | string | Yes | Original customer message for context. |
| `is_pre_purchase` | boolean | No | True if customer is asking about shipping before placing an order. |

---

## 4. Decision Framework

### 4.1 Shipping Options by Destination

| Destination | Standard | Expedited | Express | Carrier(s) | Notes |
|---|---|---|---|---|---|
| **US (domestic)** | Ground: 5–7 business days, Free | 2-Day: $12.99 | Overnight: $24.99 | UPS, USPS, FedEx | Free standard shipping on orders $50+ |
| **CA** | Standard: 7–12 business days, $9.99 | Express: 3–5 business days, $19.99 | — | UPS, Canada Post | Duties may apply for orders >$20 CAD (de minimis) |
| **MX** | Standard: 10–15 business days, $14.99 | Express: 5–7 business days, $29.99 | — | DHL, UPS | Customs declaration required for all packages |
| **EU** | Standard: 7–14 business days, €12.99 | Express: 3–5 business days, €24.99 | — | DHL, local postal | IOSS applied for orders ≤€150. VAT included at checkout. |
| **INT (other)** | Standard: 14–28 business days, $19.99 | Express: 7–10 business days, $39.99 | — | DHL, local carrier | Customs/duties vary by country. Customer responsible. |

### 4.2 Customs and Duties by Region

| Region | De Minimis Threshold | Duties/Taxes | Who Pays | Process |
|---|---|---|---|---|
| **US** | $800 USD | No duties below $800 | N/A | Packages below $800 enter duty-free |
| **CA** | $20 CAD (CAD) | 5% GST/PST + duty on goods >$20 CAD | Customer | Carrier collects on delivery or mail notice |
| **MX** | $50 USD | 16% IVA + duty | Customer | Customs broker processes; DHL/UPS collects |
| **EU** | €0 (VAT on all), €150 (duty) | VAT (19–27% by country) on all; duty on goods >€150 | Company (via IOSS for ≤€150) or Customer (>€150) | IOSS included at checkout for orders ≤€150. Orders >€150: DDP (delivered duty paid) by default |
| **INT (other)** | Varies by country | Varies | Customer (unless DDP selected) | Carrier collects on delivery. Customer should check local regulations. |

### 4.3 Tracking Status Meanings

| Carrier Status | Meaning | Customer Impact | Action Needed |
|---|---|---|---|
| `Label Created` | Shipping label generated; package not yet picked up | Order is being prepared | None — normal. If >48h since label creation, investigate. |
| `Accepted` / `Picked Up` | Carrier has picked up the package from warehouse | Package in transit | None — normal. |
| `In Transit` | Package moving through carrier network | On the way | None — normal. |
| `Out for Delivery` | Package on delivery vehicle for final delivery | Arriving today | None — normal. |
| `Delivered` | Package marked delivered | Should be at customer's address | If customer says not received: see §4.4 Lost Package |
| `Exception` / `Delivery Exception` | Issue encountered (weather, address problem, customs hold) | Delayed | Investigate cause. See §4.5 Delayed Package |
| `Returned to Sender` | Package being sent back to warehouse | Customer will not receive | Investigate cause (wrong address, refused, customs rejection). Contact customer. |
| `Customs Hold` / `Held by Customs` | Package held by customs authority | Delayed, may need documentation | Contact customer to provide any requested docs. See §4.6 Customs Issues |
| `Available for Pickup` | Package at carrier facility for customer pickup | Customer must pick up within 7–14 days | Notify customer of pickup location and deadline |

### 4.4 Lost Package Procedure

**Definition:** Package tracking shows `Delivered` but customer reports not receiving it, OR tracking has not updated in 7+ business days (US) / 14+ business days (international).

| Step | Action | Timeline |
|---|---|---|
| 1 | Verify shipping address with customer | Immediate |
| 2 | Check tracking for delivery details (GPS coordinates, signature, photo proof) | Within 1 hour |
| 3 | Ask customer to check with neighbors, building management, mailbox | Same day |
| 4 | File a carrier investigation/tracer request | Within 24 hours |
| 5 | If carrier confirms loss: process replacement or refund | Within 3 business days of confirmation |
| 6 | If carrier cannot confirm: offer goodwill replacement or refund at company discretion | Within 5 business days |
| 7 | Document incident for shipping analytics | After resolution |

**Important:** Do not accuse the customer of theft. Do not require a police report for standard lost packages (only if fraud is suspected and tier-2 approves).

### 4.5 Delayed Package Procedure

**Definition:** Package tracking has not updated in 3+ business days (US) / 7+ business days (international), but is not yet marked as lost.

| Step | Action | Timeline |
|---|---|---|
| 1 | Check current tracking status and last scan location | Immediate |
| 2 | If `Exception`: identify exception reason (weather, address, customs) | Within 1 hour |
| 3 | Contact carrier for estimated resolution | Within 24 hours |
| 4 | Communicate updated ETA to customer | Within 24 hours |
| 5 | If delay >5 business days beyond original ETA: offer options (wait, partial refund on shipping, expedite replacement) | Within 48 hours |
| 6 | Monitor tracking daily until resolved | Daily |
| 7 | If delay >10 business days: treat as lost package (§4.4) | After 10 business days |

### 4.6 Customs Issues Procedure

| Issue | Action |
|---|---| 
| Package held for customs documentation | Contact customer to provide required docs (ID, invoice, product description). Provide templates. |
| Duties/taxes owed by customer | Inform customer of amount and payment method (carrier website or on delivery). |
| Package refused by customs (prohibited item, restricted import) | Contact customer to explain. Process refund (minus shipping) or redirect to alternative address. |
| Package returned by customs | Process refund (minus shipping and return costs). Inform customer of restriction. |
| EU IOSS issue (VAT not collected at checkout) | Company absorbs VAT cost. Do not charge customer. Investigate IOSS system error. |

---

## 5. Tool Usage

| Tool | When | Purpose |
|---|---|---|
| `shopify.read_orders` | Always when order exists | Get shipping method, tracking number, carrier, shipping address, delivery date. |
| `kb.search` | When carrier info or shipping restrictions needed | Retrieve carrier contact info, service levels, and country-specific restrictions. |
| `draft-response` | After shipping context is assembled | Provide shipping context for response drafting. |

**Sequencing:** Order lookup → Tracking retrieval → Status interpretation → Context assembly → Output. Do not interpret tracking status without the actual tracking data.

---

## 6. Output Contract

```json
{
  "shipping_id": "shp_<timestamp>_<order_number>",
  "order_number": "10247",
  "region": "US",
  "carrier": "UPS",
  "shipping_method": "Ground",
  "tracking_number": "1Z999AA10123456784",
  "tracking_url": "https://www.ups.com/track?tracknum=1Z999AA10123456784",
  "tracking_status": "In Transit",
  "last_update": "2026-07-01T08:15:00Z",
  "last_location": "Louisville, KY, US",
  "estimated_delivery": "2026-07-05",
  "shipped_date": "2026-06-30",
  "shipping_cost_paid": 0.00,
  "customs_info": {
    "applicable": false,
    "duties_owed": 0,
    "ddp": false
  },
  "status_meaning": "Package is moving through the UPS network and is on schedule for delivery.",
  "action_needed": "none",
  "customer_instructions": "Your package is in transit and on track for delivery by July 5th. You can track it at the UPS link above.",
  "issue_flag": null,
  "process_steps": null
}
```

| Field | Type | Constraints |
|---|---|---|
| `tracking_status` | string | One of the carrier statuses from §4.3 or `not_shipped` / `no_tracking`. |
| `status_meaning` | string | Plain-language explanation of the tracking status for the customer. |
| `action_needed` | string | One of: `none`, `investigate_delay`, `file_loss_claim`, `customs_docs`, `address_correction`, `contact_carrier`. |
| `issue_flag` | string\|null | `null` if no issue. One of: `delayed`, `lost`, `customs_hold`, `returned_to_sender`, `exception`, `delivery_exception`. |
| `process_steps` | array\|null | Steps from §4.4/§4.5/§4.6 if action is needed. `null` if no action needed. |

---

## 7. Risk Boundaries

1. **Never provide a tracking number without verifying it via Shopify.** Do not guess or fabricate tracking numbers.
2. **Never promise a specific delivery date** that is earlier than the carrier's estimate. Use "estimated delivery" language.
3. **Never tell a customer their package is lost** until the carrier investigation confirms it. Use "we're investigating" language.
4. **Never require the customer to pay duties that should have been collected at checkout** (EU IOSS). If the company failed to collect VAT, the company absorbs the cost.
5. **Never share internal warehouse addresses or carrier account numbers** with customers.
6. **Never process a replacement shipment without confirming the original is lost** (to prevent double-shipment fraud). Exception: tier-2 may approve goodwill replacement.
7. **Never ignore a `Returned to Sender` status.** This requires immediate investigation and customer notification.
8. **Customs information must be region-accurate.** Do not give US customs advice to an EU customer or vice versa. Always check the destination region.

---

## 8. Examples

### Example 1: Standard US Order In Transit (P3)

**Input:**
```
region: US
order_number: 10247
order_data: {
  shipping_method: "Ground",
  tracking_number: "1Z999AA10123456784",
  carrier: "UPS",
  shipped_date: "2026-06-30",
  shipping_address_region: "US"
}
message: "Where is my order? I haven't received it yet."
```

**Output:**
```json
{
  "shipping_id": "shp_20260702_10247",
  "order_number": "10247",
  "region": "US",
  "carrier": "UPS",
  "shipping_method": "Ground",
  "tracking_number": "1Z999AA10123456784",
  "tracking_url": "https://www.ups.com/track?tracknum=1Z999AA10123456784",
  "tracking_status": "In Transit",
  "last_update": "2026-07-01T08:15:00Z",
  "last_location": "Louisville, KY, US",
  "estimated_delivery": "2026-07-05",
  "shipped_date": "2026-06-30",
  "shipping_cost_paid": 0.00,
  "customs_info": { "applicable": false, "duties_owed": 0, "ddp": false },
  "status_meaning": "Your package is moving through the UPS network and is on schedule for delivery by July 5th.",
  "action_needed": "none",
  "customer_instructions": "Track your package anytime at the UPS link. Your delivery is estimated for July 5th.",
  "issue_flag": null,
  "process_steps": null
}
```

### Example 2: EU Order with Customs Hold (P3)

**Input:**
```
region: EU
order_number: 10252
order_data: {
  shipping_method: "Standard",
  tracking_number: "JD014600001234567890",
  carrier: "DHL",
  shipped_date: "2026-06-25",
  shipping_address_region: "DE"
}
tracking_number: "JD014600001234567890"
message: "My package has been stuck in customs for a week. What's happening?"
```

**Output:**
```json
{
  "shipping_id": "shp_20260702_10252",
  "order_number": "10252",
  "region": "EU",
  "carrier": "DHL",
  "shipping_method": "Standard",
  "tracking_number": "JD014600001234567890",
  "tracking_url": "https://www.dhl.com/de-en/home/tracking/tracking-parcel.html?submit=1&tracking-id=JD014600001234567890",
  "tracking_status": "Customs Hold",
  "last_update": "2026-06-28T10:30:00Z",
  "last_location": "Frankfurt, DE — Customs",
  "estimated_delivery": "pending_customs_release",
  "shipped_date": "2026-06-25",
  "shipping_cost_paid": 12.99,
  "customs_info": {
    "applicable": true,
    "duties_owed": 0,
    "ddp": true,
    "ioss_applied": true,
    "note": "IOSS was applied at checkout. VAT was collected. Package should clear customs without customer payment. Customs hold may be for documentation review."
  },
  "status_meaning": "Your package is being held by German customs for a documentation review. Since VAT was already collected at checkout (IOSS), no additional payment should be required from you.",
  "action_needed": "customs_docs",
  "customer_instructions": "We're contacting DHL to expedite the customs release. If customs requires any documentation from you, we'll email you immediately. No additional payment should be needed as VAT was already collected.",
  "issue_flag": "customs_hold",
  "process_steps": [
    "Contact DHL customs broker to identify hold reason",
    "If documentation is needed: email customer with specific requirements",
    "Monitor customs release daily",
    "If hold >5 business days: escalate to tier-2 and consider replacement shipment",
    "Update customer every 48 hours until resolved"
  ]
}
```

### Example 3: Lost Package — Delivered but Not Received (P3)

**Input:**
```
region: US
order_number: 10253
order_data: {
  shipping_method: "Ground",
  tracking_number: "9400111899223456789",
  carrier: "USPS",
  shipped_date: "2026-06-25",
  shipping_address_region: "US"
}
message: "Tracking says delivered but I never got it! I've checked everywhere."
```

**Output:**
```json
{
  "shipping_id": "shp_20260702_10253",
  "order_number": "10253",
  "region": "US",
  "carrier": "USPS",
  "shipping_method": "Ground",
  "tracking_number": "9400111899223456789",
  "tracking_url": "https://tools.usps.com/go/TrackConfirmAction?tLabels=9400111899223456789",
  "tracking_status": "Delivered",
  "last_update": "2026-06-30T14:22:00Z",
  "last_location": "Front Door/Porch — Austin, TX, US",
  "estimated_delivery": "delivered_2026-06-30",
  "shipped_date": "2026-06-25",
  "shipping_cost_paid": 0.00,
  "customs_info": { "applicable": false, "duties_owed": 0, "ddp": false },
  "status_meaning": "USPS marked your package as delivered to your front door/porch on June 30th, but you report it was not received.",
  "action_needed": "file_loss_claim",
  "customer_instructions": "I'm sorry your package hasn't arrived despite being marked as delivered. Let's investigate this right away. Please check with your neighbors and building management, and I'll file a tracer with USPS immediately.",
  "issue_flag": "lost",
  "process_steps": [
    "Verify shipping address with customer",
    "Check USPS delivery details (GPS coordinates, photo proof if available)",
    "Ask customer to check with neighbors, building management, mailbox area",
    "File USPS tracer/investigation request within 24 hours",
    "If USPS confirms loss or cannot locate within 3 business days: offer full replacement or refund",
    "If USPS cannot confirm but customer insists not received after 5 business days: offer goodwill replacement at tier-1 discretion",
    "Document incident for shipping analytics and loss prevention"
  ]
}
```

### Example 4: Pre-Purchase Shipping Question (P4)

**Input:**
```
region: MX
is_pre_purchase: true
message: "How much does shipping to Mexico cost and how long does it take?"
order_number: null
```

**Output:**
```json
{
  "shipping_id": "shp_20260702_prepurchase_MX",
  "order_number": null,
  "region": "MX",
  "is_pre_purchase": true,
  "shipping_options": [
    { "method": "Standard", "timeframe": "10-15 business days", "cost": "$14.99 USD" },
    { "method": "Express", "timeframe": "5-7 business days", "cost": "$29.99 USD" }
  ],
  "customs_info": {
    "applicable": true,
    "duties_owed": "varies",
    "ddp": false,
    "note": "Orders to Mexico are subject to 16% IVA and potential import duties. The carrier (DHL/UPS) will collect these on delivery. Customs declaration is required for all packages."
  },
  "status_meaning": null,
  "action_needed": "none",
  "customer_instructions": "We ship to Mexico via DHL or UPS. Standard shipping (10-15 business days) is $14.99 and Express (5-7 business days) is $29.99. Please note that Mexican customs may apply 16% IVA and import duties, which the carrier will collect upon delivery.",
  "issue_flag": null,
  "process_steps": null
}
```

---

## 9. Evaluation Cases

| Case ID | Scenario | Region | Expected Action | Issue Flag |
|---|---|---|---|---|
| SHP-001 | Order in transit, on schedule | US | none | null |
| SHP-002 | Delivered but customer says not received | US | file_loss_claim | lost |
| SHP-003 | No tracking update for 5 days | US | investigate_delay | delayed |
| SHP-004 | Customs hold, EU, IOSS applied | EU (DE) | customs_docs | customs_hold |
| SHP-005 | Package returned to sender | CA | contact_carrier | returned_to_sender |
| SHP-006 | Pre-purchase shipping question | MX | none | null |
| SHP-007 | Exception — weather delay | US | investigate_delay | exception |
| SHP-008 | EU order, duties owed >€150 | EU (FR) | customs_docs | customs_hold |
| SHP-009 | International delay >14 days | INT | investigate_delay | delayed |
| SHP-010 | Available for pickup at carrier | US | none | null |

---

## 10. Failure Modes

| Failure Mode | Description | Mitigation |
|---|---|---|
| **Fabricated tracking number** | Skill provides a tracking number that doesn't exist or belongs to another order. | Tracking numbers are always retrieved from Shopify `order_data`. Never generated or guessed. If no tracking exists, output `tracking_number: null` and `tracking_status: "not_shiped"`. |
| **Wrong customs advice** | US duty-free threshold ($800) applied to an EU order, or EU IOSS advice given to a CA customer. | Customs info is keyed by destination region. Hard validation: if region ≠ EU, IOSS fields are set to `false`. If region = US, customs_info.applicable is `false` for orders <$800. |
| **Premature lost package declaration** | Package declared lost after only 2 days, causing unnecessary replacement and potential fraud. | Lost package procedure requires: `Delivered` status + customer report, OR no tracking update for 7+ business days (US) / 14+ business days (international). Enforced by time-since-last-update check. |
| **Customer blamed for delivery issues** | Response implies customer provided wrong address or was unavailable. | Status meaning and customer instructions use neutral, non-accusatory language. Address verification is a standard step, not a blame attribution. |
| **Customs charges passed to customer incorrectly** | EU customer charged VAT that should have been collected via IOSS at checkout. | IOSS check: if order value ≤€150 and region = EU, company absorbed VAT. `customs_info.duties_owed = 0`. Company pays, not customer. |
| **Stale tracking data** | Skill reports tracking status from days ago without noting it's stale. | `last_update` timestamp is always included. If last update is >48h old, flag `stale_tracking: true` and `action_needed: contact_carrier`. |
| **No shipping method context** | Skill doesn't tell the customer what shipping method was used, leading to confusion about delivery timeframe. | `shipping_method` is always included in output. If shipping method is unknown, state "Standard shipping" and provide the standard timeframe for the region. |
| **Return-to-sender ignored** | Package marked `Returned to Sender` but no action taken, customer left waiting. | `Returned to Sender` always sets `action_needed: contact_carrier` and `issue_flag: returned_to_sender`. Process steps include immediate investigation and customer notification. |
