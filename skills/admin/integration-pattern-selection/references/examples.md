# Examples — Integration Pattern Selection

## Example 1: Choosing Between Synchronous and Asynchronous for Order Integration

**Context:** When an Opportunity closes in Salesforce, an Order must be created in the ERP system. The stakeholder asks whether the integration should be synchronous (wait for ERP confirmation) or asynchronous (fire-and-forget).

**Problem:** The architect defaults to a synchronous Apex callout without applying the pattern framework. The ERP system sometimes takes 8-12 seconds to respond (large order processing). Occasionally it times out beyond 120 seconds, causing Apex callout failures and triggering rollbacks of the entire Opportunity close transaction.

**Solution:**
Apply the two-axis framework:
- Integration type: Process (triggering an ERP order creation)
- Timing: Does Salesforce need confirmation before completing the Opportunity close? Business says: No — confirmation is sent by email later.
- Decision: Fire-and-Forget pattern — Salesforce creates a Platform Event on Opportunity close; ERP subscribes to the event and creates the order; confirmation comes back via a separate Remote Call-In to update Salesforce with the Order ID

Pattern decision record:
```
Scenario: Opportunity Close → ERP Order Creation
Integration type: Process
Timing: Async (no synchronous response required by Salesforce)
Volume: ~50/day — low volume, Platform Events appropriate
Selected pattern: Remote Process Invocation — Fire-and-Forget
Implementation: Platform Event publish on Opportunity stage change trigger
Rationale: ERP response times exceed safe synchronous window (120s limit);
           confirmation not needed in the same transaction
Cross-system rollback needed: No
```

**Why it works:** Applying the framework surface the 120-second constraint that ruled out synchronous. Fire-and-Forget with Platform Events is the correct pattern and avoids the brittle synchronous timeout failure.

The same choice written as the linted decision record this skill produces
(`scripts/check_integration_pattern_selection.py --decision-record` is what checks it; the
field-by-field walkthrough is in `references/decision-record-examples.md`):

```yaml
---
record_id: ADR-INT-0009
requirement: >
  Create an Order in the ERP when an Opportunity is set to Closed Won. Confirmation of the
  ERP order number returns later and is not needed inside the closing transaction.
direction: bidirectional_or_decoupled
volume:
  per_day: 50
  per_request: 1
latency: near_realtime
idempotency: idempotency_key_required
who_knows_ids: salesforce_ids
ordering: at_least_once
chosen_pattern: platform_event
tree_questions_cited:
  - "integration-pattern-selection.md Q10 — Salesforce produces the 'deal closed' signal, so route to Q11"
  - "integration-pattern-selection.md Q11 — the subscriber is the ERP, an external system, so Platform Event plus a Pub/Sub API subscriber on the ERP side"
  - "integration-pattern-selection.md Q12 — at-least-once is acceptable, so the ERP side dedupes on the idempotency key"
  - "integration-pattern-selection.md Q13 — the ERP pushes the order number back over HTTP, so a custom REST endpoint receives the callback"
rejected:
  - alternative: apex_callout_named_credential
    reason: >
      Q1's synchronous branches assume a bounded response. Observed ERP response times of
      8-12 seconds, with occasional excursions past the transaction's cumulative callout
      ceiling, make the close of a deal depend on ERP availability.
  - alternative: continuation
    reason: >
      Nobody is watching a spinner — the close happens in a record-triggered context, and
      Continuation is not available in async or headless contexts.
auth:
  named_credential: ERP_Orders_NC
  external_credential: ERP_Orders_EC
owner: rev-ops-platform-team
review_date: 2027-05-01
---
```

The record is longer than the free-text block above it, and the extra length is the point:
`rejected` now carries reasons a reader can argue with, and `review_date` says when the
50-per-day figure gets re-measured.

---

## Example 2: High-Volume Product Price Sync

**Context:** The ERP sends updated product price lists to Salesforce nightly. The initial count is 150K price book entries to update.

**Problem:** The developer builds a synchronous REST API integration that updates Pricebook entries one at a time. At 100 API calls per Apex transaction, the batch job runs for hours and hits governor limits.

**Solution:**
Apply the two-axis framework:
- Integration type: Data (synchronizing price records)
- Timing: Async (nightly batch — no real-time response needed)
- Volume: 150K records → Bulk API 2.0 required
- Decision: Batch Data Synchronization pattern with Bulk API 2.0

Pattern decision record:
```
Scenario: ERP nightly product price sync
Integration type: Data
Timing: Async (scheduled nightly)
Volume: 150K records → Bulk API 2.0 required (threshold: >2,000 records)
Selected pattern: Batch Data Synchronization
Implementation: Bulk API 2.0 async CSV job; scheduled at 2am outside business hours
Rationale: 150K records exceeds REST API per-transaction limits;
           Bulk API 2.0 handles up to 150M records/24 hours
```

**Why it works:** Volume threshold analysis immediately identifies Bulk API 2.0 as the required mechanism. The synchronous REST approach would have hit governor limits.

---

## Anti-Pattern: Hub-and-Spoke Orchestration in Apex

**What practitioners do:** They build multi-system orchestration logic in an Apex trigger or scheduled Apex class — calling ERP to create an order, then calling a shipping system to create a shipment, then calling a billing system to open an invoice, with error handling that tries to compensate failed downstream calls.

**What goes wrong:** Salesforce Apex cannot roll back external system operations. If the billing system call fails after the ERP order was created successfully, the Apex transaction can roll back the Salesforce DML but cannot undo the ERP order. The state becomes inconsistent across systems.

**Correct approach:** Multi-system orchestration with transactional integrity must live in middleware (MuleSoft, Boomi). Salesforce is either a System API endpoint (called by middleware) or triggers middleware via Platform Events. Never implement cross-system compensating transaction logic in Apex.
