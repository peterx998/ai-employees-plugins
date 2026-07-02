---
name: ticket-triage
description: Use when a new customer support ticket comes in and needs categorization, priority assignment (P1-P4), and routing. Classifies issues as bug, how-to, billing, account, medical-risk, order-status, or policy-question for cross-border e-commerce support.
user_invocable: true
version: "1.0.0"
tags: [customer-support, triage, e-commerce]
---

# Ticket Triage

Categorize, prioritize, and route incoming customer support inquiries.

## Categories

| Category | Signal Words |
|----------|-------------|
| **Medical Risk** | Allergy, irritation, adverse reaction, rash, bleeding |
| **Order Status** | Where is, tracking, when will, shipped, stuck |
| **Refund/Return** | Return, refund, money back, cancel order |
| **Product Usage** | How to, setting, needle, serum, cartridge |
| **Warranty** | Broken, not working, defect, warranty, replace |
| **Billing** | Charged, invoice, payment, price, discount |

## Priority

- **P1 (Critical)**: Medical risk — escalate immediately to human
- **P2 (High)**: Device defect, stuck order >14 days, refund dispute
- **P3 (Medium)**: Usage question, tracking inquiry, warranty claim
- **P4 (Low)**: General inquiry, accessory question

## Routing

| Route to | When |
|----------|------|
| Medical Review (human) | Any P1 medical risk |
| Tier 1 Agent | P3-P4: usage, tracking, FAQ |
| Tier 2 Agent | P2: defects, refunds |
| Escalation (human) | Failed resolution, legal threat |
