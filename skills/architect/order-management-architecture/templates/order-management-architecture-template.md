# Order Management Architecture — Decision Template

Use this template when designing or reviewing an OMS architecture engagement. Fill every section before producing deliverables.

---

## Scope

**Skill:** `order-management-architecture`

**Request summary:** (fill in what the architect or stakeholder asked for)

**Commerce variant:** [ ] B2B only  [ ] B2C only  [ ] B2B + B2C

---

## Fixed Constraints (Gather First)

| Constraint | Value | Verified? |
|---|---|---|
| OMS routing variant | Connected Commerce / Growth | [ ] |
| OCI provisioned? | Yes / No / Planned (Phase N) | [ ] |
| Number of fulfillment locations | | [ ] |
| Peak order volume (orders/hour) | | [ ] |
| Returns volume (returns/day) | | [ ] |
| Refund gate: status that triggers ensure-refunds | | [ ] |

> **STOP:** If OCI is not provisioned and multi-location routing is required, document this as a blocking dependency before proceeding with routing design.

---

## Fulfillment Location Topology

| Location Name | OCI Location ID | SKU Population | Can Ship B2C? | Can Ship B2B? |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

---

## Routing Architecture Decision

**Routing variant selected:** Connected Commerce Order Routing / Growth Order Routing

**Rationale:**

**Routing trigger event:**
- [ ] `OrderSummaryCreatedEvent` platform event subscription
- [ ] Record-Triggered Flow on OrderSummary Status change
- [ ] Manual agent action
- [ ] Other: ___________

**Fewest-splits action wired?** [ ] Yes  [ ] No — if No, document alternative routing logic:

**OCI reservation failure handling:**
- [ ] Retry queue via Platform Event (`RetryRouting__e` or equivalent)
- [ ] Process Exception record after N retries
- [ ] Manual operations queue
- [ ] Other: ___________

**Maximum retry count before escalation:** _____

---

## Returns Architecture Decision

**Return initiation channel:**
- [ ] Storefront self-service (`submit-return` via Connect API)
- [ ] Service agent in OMS console
- [ ] Both

**ReturnOrder status machine:**

| Status | Owner | Transition Trigger | Notes |
|---|---|---|---|
| Submitted | System | submit-return API call | Customer notification sent |
| In Transit | Warehouse | Carrier tracking update or manual | |
| Received | Warehouse | Barcode scan / manual confirmation | |
| Closed | Finance / System | Post-refund | Refund issued at this step |

**Status that triggers ensure-refunds invocation:** ___________

**Refund failure handling:**
- [ ] Process Exception record for manual retry
- [ ] Automatic retry via scheduled batch
- [ ] Alert to finance team
- [ ] Other: ___________

---

## Governor Limit Analysis

| Transaction Profile | Key Operations | Estimated Limit Consumption | Headroom |
|---|---|---|---|
| Single order routing (peak) | OCI query + Flow + FulfillmentOrder DML | | |
| Bulk routing (post-maintenance batch) | N orders × above | | |
| Single return + refund | submit-return + ensure-refunds callout | | |
| Batch returns processing | M returns/hour × refund callouts | | |

> Target: all profiles must stay below 50% of relevant governor limits (SOQL queries: 100/tx, DML: 150/tx, callouts: 100/tx).

---

## Well-Architected Review

| Pillar | Question | Assessment | Action Required |
|---|---|---|---|
| Reliability | What happens when OCI is slow or returning errors? | | |
| Reliability | What happens when the payment gateway is down during ensure-refunds? | | |
| Performance | What is the expected routing latency at peak volume? | | |
| Performance | Does batch returns processing stay within callout limits? | | |
| Adaptability | Can new fulfillment locations be added without rebuilding routing Flows? | | |
| Adaptability | Can return policies (e.g., refund gate status) be changed without code deployment? | | |

---

## Review Checklist

Copy from SKILL.md and verify each item before sign-off:

- [ ] Routing variant confirmed and documented
- [ ] OCI provisioning confirmed before multi-location routing design approved
- [ ] Routing trigger and orchestration Flow designed — fewest-splits action wired
- [ ] OCI reservation failure path (retry or fallback) explicitly designed
- [ ] Returns state machine documented with explicit status transitions and team ownership
- [ ] `ensure-refunds` wired to ReturnOrder status transition, not to return creation
- [ ] Governor limit analysis covers routing transaction profile at peak volume
- [ ] New fulfillment location onboarding process documented

---

## Deliverables

| Artifact | Owner | Status |
|---|---|---|
| OMS Architecture Decision Record | | [ ] Draft [ ] Final |
| Fulfillment Location Topology | | [ ] Draft [ ] Final |
| Routing Flow Design Diagram | | [ ] Draft [ ] Final |
| Returns State Machine Diagram | | [ ] Draft [ ] Final |
| Governor Limit Analysis | | [ ] Draft [ ] Final |

---

## Notes and Deviations

(Record any deviations from the standard patterns documented in SKILL.md and the rationale for each deviation.)
