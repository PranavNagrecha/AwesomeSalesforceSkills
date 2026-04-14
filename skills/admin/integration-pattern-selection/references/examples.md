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
