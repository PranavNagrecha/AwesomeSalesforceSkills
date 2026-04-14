# LLM Anti-Patterns — Integration Pattern Selection

Common mistakes AI coding assistants make when generating or advising on Salesforce integration pattern selection. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Hub-and-Spoke Orchestration in Apex

**What the LLM generates:** An Apex trigger or Queueable that calls ERP System 1, then Shipping System 2, then Billing System 3 in sequence — implementing hub-and-spoke orchestration inside Salesforce.

**Why it happens:** LLMs model orchestration as a sequential call chain, and Apex is the most prominent Salesforce code execution context in training data. They don't model the distributed transaction constraint.

**Correct pattern:**
```
Hub-and-spoke orchestration with cross-system transactional integrity MUST live in middleware.
Salesforce role: endpoint (called by middleware via REST/SOAP) or event source (fires Platform Event).
Salesforce does NOT orchestrate cross-system transactions.
Middleware options: MuleSoft, Dell Boomi, Workato, Informatica.
```

**Detection hint:** Apex code that makes 2+ sequential callouts to different external systems with try/catch compensating logic for rollback.

---

## Anti-Pattern 2: Defaulting to Synchronous REST for High-Volume Batch

**What the LLM generates:** REST API integration logic for batch sync scenarios involving thousands or millions of records — using callouts or REST endpoints for record-by-record processing.

**Why it happens:** REST API is the default integration pattern in most LLM training data. LLMs don't apply the volume threshold analysis that routes high-volume scenarios to Bulk API 2.0.

**Correct pattern:**
```
Volume thresholds:
- Up to 2,000 records per transaction: REST API or SOAP API acceptable
- 2,001+ records per batch: Bulk API 2.0 required
- Bulk API 2.0 handles up to 150M records per 24-hour period
- Synchronous REST for 150K records would hit governor limits
```

**Detection hint:** REST API or SOAP API recommended for scenarios described as "batch," "nightly sync," or where volume mentions thousands or more records.

---

## Anti-Pattern 3: Recommending Synchronous Callout for High-Latency External Systems

**What the LLM generates:** "Use an Apex HTTP callout in a trigger to call the ERP system when the Opportunity closes. Wait for the response and update the Salesforce record with the ERP Order ID."

**Why it happens:** Synchronous request/reply is the intuitive model for "call system X, get result Y." LLMs don't consistently model the 120-second timeout constraint or the impact of trigger suspension on the user experience.

**Correct pattern:**
```
If external system latency > 60 seconds or is variable:
→ Use Fire-and-Forget pattern (async)
  1. Salesforce fires Platform Event on Opp close
  2. External system subscribes, creates Order, fires callback event
  3. Salesforce receives callback (Remote Call-In) and updates record with Order ID
Never use synchronous callout for external systems without SLA guarantees < 60s response.
```

**Detection hint:** Apex callout in a trigger or transaction that calls an "ERP," "SAP," "Oracle," or "legacy system" synchronously with a response expected in the same transaction.

---

## Anti-Pattern 4: Using Platform Events When Ordered Delivery Is Required

**What the LLM generates:** "Use Platform Events to sync Customer record updates from Salesforce to the external system in real-time. Each change fires an event."

**Why it happens:** Platform Events are prominently documented as the Salesforce event streaming mechanism. LLMs recommend them for all streaming/real-time scenarios without noting the ordering and delivery guarantees.

**Correct pattern:**
```
Platform Events do NOT guarantee ordered delivery or exactly-once delivery.
For ordering-sensitive scenarios (financial transactions, state machine transitions):
- Consider CDC (Change Data Capture) with client-side deduplication
- Or use synchronous Remote Call-In with idempotent external API
- Platform Events are appropriate for loose-coupling notifications
  where order is not critical and duplicate handling is built in
```

**Detection hint:** Platform Events recommended for financial transaction sync, state machine updates, or any scenario described as requiring "ordered" or "exactly-once" delivery.

---

## Anti-Pattern 5: Not Applying the Two-Axis Framework

**What the LLM generates:** Pattern recommendations based on "what sounds right" for the described scenario rather than applying the Salesforce canonical two-axis decision framework (integration type × timing).

**Why it happens:** LLMs don't consistently apply the structured decision framework. They pattern-match on surface features of the scenario description.

**Correct pattern:**
```
Always apply the two-axis framework first:
1. What is the integration type? Process / Data / Virtual
2. What is the timing? Synchronous (response required) / Asynchronous
3. Map to canonical pattern: Request/Reply | Fire-and-Forget | Batch Sync | Remote Call-In | UI Update | Data Virtualization
4. Apply secondary constraints: volume, transactional requirements, latency
Only then recommend a specific implementation mechanism.
```

**Detection hint:** Pattern recommendation given without explicit classification of integration type and timing requirement.
