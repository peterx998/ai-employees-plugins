---
name: escalate-risk
description: Use when a customer support interaction triggers risk escalation — medical adverse reaction, legal threat, social media threat, or refund dispute exceeding authority threshold. Packages context for human review.
user_invocable: true
version: "1.0.0"
tags: [customer-support, escalation, risk-management]
---

# Escalate Risk

Package customer issues for human escalation.

## Escalation Triggers

| Trigger | Priority | Action |
|---------|----------|--------|
| Adverse reaction reported | Critical | Immediate human review |
| Legal threat | Critical | Do not reply, escalate immediately |
| Social media threat | High | Escalate to brand team |
| Regulatory inquiry | High | Escalate to compliance |
| Refund dispute exceeding threshold | Medium | Escalate to finance |
| Repeated unresolved issue (3+ contacts) | Medium | Escalate to senior support |
