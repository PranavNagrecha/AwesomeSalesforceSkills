# Middleware Integration Patterns — Work Template

Use this template when evaluating whether middleware is required and selecting an iPaaS vendor for a Salesforce integration project.

## Scope

**Skill:** `middleware-integration-patterns`

**Request summary:** (describe the integration scenario: source system, target system, data/events involved, trigger)

---

## Step 1: Middleware Necessity Assessment

Answer each question. If all answers are "No," middleware is likely unnecessary — use native Salesforce capabilities.

| Requirement | Present in this scenario? | Notes |
|---|---|---|
| Protocol conversion required (JMS, MQ, AS2, JDBC, SFTP, RFC) | Yes / No | |
| Cross-system orchestration: fanout to 3+ backends in one business unit | Yes / No | |
| Durable message queuing: target may be offline; messages must not be lost | Yes / No | |
| Transactional guarantee across two or more non-Salesforce systems | Yes / No | |
| Complex transformation (aggregation, splitting, enrichment, canonical model) | Yes / No | |
| Volume or latency requires Bulk API or async processing outside Apex governor limits | Yes / No | |

**Decision:** Middleware required? Yes / No

**If No:** Document which native capability will be used instead (Platform Event + Apex, Flow HTTP Callout, External Services, Pub/Sub API subscriber).

---

## Step 2: Integration Pattern Selection

Which pattern applies to this scenario?

- [ ] **Event-Driven Fanout** — Salesforce event triggers coordinated writes to multiple backends
- [ ] **Protocol Conversion** — Source or target uses a non-HTTP protocol
- [ ] **Store-and-Forward / Reliable Delivery** — Target may be offline; guaranteed delivery required
- [ ] **Request-Reply with Transformation** — Salesforce needs a synchronous response from an external system after transformation
- [ ] **Scheduled Batch / ETL** — Large volume, time-windowed data movement with transformation

---

## Step 3: Existing License Inventory

| Vendor | Current license held? | Contract expiry | Notes |
|---|---|---|---|
| MuleSoft Anypoint | Yes / No | | |
| Dell Boomi | Yes / No | | |
| Workato | Yes / No | | |
| Informatica IICS | Yes / No | | |
| Other: ________ | Yes / No | | |

**If an existing license covers this use case: use it. Do not introduce a second iPaaS.**

---

## Step 4: Vendor Scorecard (complete only if no existing license or existing platform is inadequate)

Score each criterion 1–3 (1 = poor fit, 2 = acceptable, 3 = strong fit) for each candidate vendor.

| Criterion | Weight | MuleSoft | Boomi | Workato | Informatica |
|---|---|---|---|---|---|
| Salesforce connector coverage (APIs needed) | High | | | | |
| Protocol support (legacy, non-HTTP) | High if needed | | | | |
| Real-time event latency (sub-5-min required?) | High if needed | | | | |
| Transformation capability (DataWeave, mapping) | Medium | | | | |
| Team skills match | Medium | | | | |
| Total cost of ownership | Medium | | | | |
| API governance / catalog | Low unless multi-consumer | | | | |
| **Total** | | | | | |

**Selected vendor:** ________________

**Rationale:** (2–3 sentences explaining why this vendor scored highest for the scenario)

---

## Step 5: Error Handling Design

| Element | Design Decision |
|---|---|
| Retry policy | (e.g., 3 retries, exponential backoff: 1 min / 5 min / 30 min) |
| Dead-letter queue | (name, persistence strategy, alert trigger) |
| Compensating transaction | (which steps are compensable, rollback action for each) |
| Correlation ID | (Salesforce record Id / UUID, propagation path) |
| Alerting | (who is alerted, on what condition, via what channel) |

---

## Step 6: Checklist Before Implementation

- [ ] Middleware necessity confirmed and documented
- [ ] Native Salesforce capability alternatives evaluated and ruled out
- [ ] Existing iPaaS license checked
- [ ] Vendor selected with documented rationale
- [ ] Salesforce connector capability confirmed (API type, edition, real-time latency)
- [ ] Error handling, dead-letter queue, and compensating transaction designed
- [ ] Correlation ID propagation planned
- [ ] Related skills consulted: mulesoft-salesforce-connector (if MuleSoft), api-led-connectivity (if multi-consumer governance needed)

---

## Notes

(Record any deviations from the standard pattern, open questions, or decisions pending stakeholder input.)
