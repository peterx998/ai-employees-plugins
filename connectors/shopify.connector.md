# Shopify Connector Contract

**Version:** 1.0.0  
**Last Updated:** 2026-07-02  
**Owner:** Platform Team  
**Connector Type:** E-Commerce (Shopify Admin API)  

---

## 1. Overview

The Shopify connector enables AI agents to retrieve order, product, and customer information from a Shopify store, and to update tracking information (with human approval). It integrates with the Shopify Admin REST/GraphQL API using a private app access token.

---

## 2. Capabilities

| Capability | Description | Permission Level | Human Approval Required? |
|---|---|---|---|
| `get_order` | Retrieve a single order by order ID | **Read-Only (RO)** | No |
| `search_orders` | Search orders using Shopify filters | **Read-Only (RO)** | No |
| `get_product` | Retrieve product details by product ID | **Read-Only (RO)** | No |
| `get_customer` | Retrieve customer details by customer ID | **Read-Only (RO)** | No |
| `update_tracking` | Update order tracking/shipping info | **Write-Send (WS)** | **Yes — ALWAYS** |

---

## 3. Permission Levels

### 3.1 Read-Only Operations

```yaml
get_order:
  permission: RO
  description: "Retrieve a single order including line items, fulfillment status, and shipping details."
  input:
    order_id: string (required)
    fields: array<string> (optional)  # e.g., ["id", "status", "line_items", "tracking_number"]
  output:
    order:
      id: string
      order_number: string
      status: string          # open, closed, cancelled
      financial_status: string  # paid, pending, refunded, etc.
      fulfillment_status: string  # fulfilled, unfulfilled, partial
      line_items: array<LineItem>
      shipping_address: Address  # PII — handle per privacy policy
      tracking_number: string (nullable)
      tracking_url: string (nullable)
      created_at: string (ISO 8601)
      updated_at: string (ISO 8601)
  rate_limit: "2 requests per second (Shopify rate limit)"
  human_approval: false
  data_minimization: |
    Request only the fields needed for the task. Do NOT request payment_details,
    credit_card, or billing_address unless explicitly required.

search_orders:
  permission: RO
  description: "Search orders using Shopify order query filters."
  input:
    query: string (required)  # e.g., "status:open financial_status:paid"
    max_results: integer (optional, default: 25, max: 250)
  output:
    orders: array<OrderSummary>
  rate_limit: "2 requests per second (Shopify rate limit)"
  human_approval: false

get_product:
  permission: RO
  description: "Retrieve product details including variants, inventory, and images."
  input:
    product_id: string (required)
  output:
    product:
      id: string
      title: string
      description: string
      variants: array<Variant>
      inventory_quantity: integer
      images: array<string>  # URLs
      status: string  # active, draft, archived
  rate_limit: "2 requests per second (Shopify rate limit)"
  human_approval: false

get_customer:
  permission: RO
  description: "Retrieve customer details. PII — handle per privacy policy."
  input:
    customer_id: string (required)
  output:
    customer:
      id: string
      email: string          # PII — do not include in external outputs or logs
      phone: string (nullable)  # PII
      first_name: string     # PII
      last_name: string      # PII
      orders_count: integer
      total_spent: string    # decimal
      default_address: Address  # PII
  rate_limit: "2 requests per second (Shopify rate limit)"
  human_approval: false
  data_minimization: |
    Only request customer data when necessary for the task (e.g., to verify
    order history or shipping address). Do not retrieve customer data for
    analytics or reporting — use aggregated data instead.
```

### 3.2 Write-Send Operations

```yaml
update_tracking:
  permission: WS
  description: "Update tracking information for an order's fulfillment. HUMAN APPROVAL REQUIRED."
  input:
    order_id: string (required)
    fulfillment_id: string (required)
    tracking_number: string (required)
    tracking_url: string (optional)
    carrier: string (optional)  # e.g., "UPS", "FedEx", "DHL"
  output:
    fulfillment:
      id: string
      status: string
      tracking_number: string
      tracking_url: string
      updated_at: string (ISO 8601)
  rate_limit: "2 requests per second (Shopify rate limit)"
  human_approval: true  # ALWAYS REQUIRED — NO EXCEPTIONS
  notes: |
    - Incorrect tracking numbers cause significant customer confusion.
    - Agent prepares the tracking update and submits to human review queue.
    - Human reviewer verifies the tracking number before approval.
    - This operation CANNOT be executed by an agent autonomously.
```

---

## 4. Required Environment Variables

| Variable | Description | Required? | Example |
|---|---|---|---|
| `SHOPIFY_SHOP_DOMAIN` | Shopify store domain (without .myshopify.com) | Yes | `mystore` |
| `SHOPIFY_ACCESS_TOKEN` | Shopify Admin API access token (private app) | Yes | `shpat_xxxxxxxxxxxxxxxxxxxxxxxx` |

### 4.1 Required API Scopes

```
read_orders          # Read order data
read_products        # Read product data
read_customers       # Read customer data
write_fulfillments   # Update tracking (used only with human approval)
```

### 4.2 Environment Setup

```bash
# .env or environment configuration
SHOPIFY_SHOP_DOMAIN=your-store
SHOPIFY_ACCESS_TOKEN=shpat_your_access_token
```

---

## 5. Safety Rules

### 5.1 Never Modify Orders

```
SAFETY RULE: NEVER MODIFY ORDERS
- Agents MUST NOT modify order contents, status, financial status, or
  customer details.
- Agents may only READ order data (get_order, search_orders).
- The only write operation available is update_tracking, which requires
  human approval.
- Order modification (cancel, refund, edit items) is PROHIBITED for all agents.
- Violation of this rule results in immediate agent suspension.
```

### 5.2 Never Issue Refunds Automatically

```
SAFETY RULE: NEVER ISSUE REFUNDS AUTOMATICALLY
- Agents MUST NOT issue refunds through the Shopify API.
- The refund capability is NOT available to agents via this connector.
- All refund requests must be escalated to human review:
  - Refunds > $500: P1 escalation (15 min SLA)
  - Refunds $100-$500: P2 escalation (1 hour SLA)
  - Refunds < $100: P3 escalation (4 hour SLA)
- Human reviewers process refunds through the Shopify admin directly.
```

### 5.3 Customer Data Minimization

```
SAFETY RULE: CUSTOMER DATA MINIMIZATION
- Request only the fields needed for the current task.
- Do NOT request or store: payment_details, credit_card, billing_address
  (unless explicitly required for the task).
- Customer email and phone are PII — do not include in external outputs or logs.
- Shipping address is PII — only include when necessary for shipping-related tasks.
- Do not aggregate customer data across multiple orders for profiling.
- Customer data accessed by agents is transient — not persisted in agent state.
```

### 5.4 Rate Limit Awareness

| Limit | Value | Handling |
|---|---|---|
| REST API rate limit | 2 requests/second (40 requests/20 sec bucket) | Implement leaky bucket algorithm |
| GraphQL API rate limit | Query cost-based (1000 points/min) | Calculate query cost, throttle accordingly |
| Bulk operations | 1 concurrent bulk operation per app | Queue bulk requests |

**Rate Limit Error Handling:**
```python
# Pseudocode for Shopify rate limit handling
def handle_shopify_api_error(response):
    if response.status_code == 429:
        # Rate limited — check Retry-After header
        retry_after = float(response.headers.get('Retry-After', 2.0))
        time.sleep(retry_after)
        return retry(response)
    elif response.status_code == 423:
        # Shop is locked (billing issues)
        log_error("SHOPIFY_SHOP_LOCKED")
        alert_ops_team()
        return None
```

---

## 6. Prohibited Operations

The following operations are **not available** through this connector, regardless of permissions:

| Operation | Reason |
|---|---|
| `create_order` | Orders are created by customers via storefront only |
| `modify_order` | Order modification requires admin access; agents never modify |
| `cancel_order` | Cancellation requires human review and admin action |
| `issue_refund` | Refunds require human review and admin action |
| `delete_order` | Deletion is not available; orders are archived by admins |
| `create_product` | Product creation requires merchant admin |
| `modify_product` | Product modification requires merchant admin |
| `delete_customer` | Customer data deletion requires admin + DSR process |
| `modify_customer` | Customer modification requires admin access |

---

## 7. Data Handling

### 7.1 What Agents May Read

- Order status, items, fulfillment status, tracking info
- Product details (title, description, variants, inventory)
- Customer order history (for support context only)

### 7.2 What Agents Must NOT Do

- Access payment or credit card information
- Export customer lists or order data
- Modify any data except tracking (with human approval)
- Access orders unrelated to the current customer inquiry
- Store customer data beyond the active task duration

---

## 8. Integration with Human Review

### 8.1 Read → Assess → Draft/Escalate Workflow

```
1. Agent retrieves order details (get_order)
2. Agent retrieves product details if needed (get_product)
3. Agent retrieves customer context if needed (get_customer)
4. Agent assesses the situation:
   - Standard inquiry → draft response via Gmail connector
   - Refund request → escalate to human review (P1/P2/P3 based on amount)
   - Tracking update needed → prepare update_tracking request for human approval
   - Medical/adverse reaction → P1 escalation, suppress auto-reply
5. For tracking updates:
   - Agent prepares update_tracking payload
   - Submits to human review queue
   - Human reviewer verifies tracking number
   - If approved, system executes update_tracking
```

---

## 9. Mock Data

For testing and development, use the mock Shopify data at:
```
connectors/mock/mock-shopify-orders.json
```

This file contains 3 sample orders (US, Canada, EU) with fake addresses for testing agent workflows.

---

## 10. Error Codes

| Error Code | Description | Agent Action |
|---|---|---|
| `SHOPIFY_AUTH_FAILED` | Access token invalid or expired | Log error, alert ops, stop processing |
| `SHOPIFY_RATE_LIMITED` | Rate limit exceeded (429) | Backoff per Retry-After header, retry |
| `SHOPIFY_SHOP_LOCKED` | Shop is locked (423) | Log, alert ops, queue tasks for later |
| `SHOPIFY_ORDER_NOT_FOUND` | Order ID does not exist | Log, return "order not found" to agent |
| `SHOPIFY_PRODUCT_NOT_FOUND` | Product ID does not exist | Log, return "product not found" to agent |
| `SHOPIFY_CUSTOMER_NOT_FOUND` | Customer ID does not exist | Log, return "customer not found" to agent |
| `SHOPIFY_TRACKING_UPDATE_REJECTED` | Tracking update attempted without approval | Log violation, block, alert security |
| `SHOPIFY_REFUND_BLOCKED` | Refund operation attempted by agent | Log violation, block, alert security |

---

## 11. References

- Shopify Admin REST API: https://shopify.dev/docs/api/admin-rest
- Shopify Admin GraphQL API: https://shopify.dev/docs/api/admin-graphql
- policies/tool-permissions.md — Permission level definitions
- policies/privacy-and-pii.md — PII handling rules
- policies/human-review.md — Escalation for refunds and high-value cases
