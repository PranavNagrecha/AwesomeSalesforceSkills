# Gotchas — Solution Design Patterns

Non-obvious Salesforce platform behaviors that cause real problems when making automation layer decisions.

## Gotcha 1: Flow Runs Before Apex Triggers in Before-Save Order — Most Developers Expect the Opposite

**What happens:** A developer builds a before-save Record-Triggered Flow that sets a field value, and an Apex before trigger that also sets the same field. The Apex trigger's value is overwritten by Flow — which runs *before* the Apex before trigger in the official order of execution.

**The actual before-save order:**
1. System validation (required fields, field type enforcement)
2. Before-save Record-Triggered Flows ← Flow fires here
3. Before Apex triggers ← Apex fires here, *after* Flow
4. Record saved to database

**When it occurs:** Any time both a before-save Flow and an Apex before trigger write to the same field on the same object. The Apex trigger sees the value Flow wrote, and can overwrite it. But if the design assumption was that Apex runs first, the result is wrong.

**How to avoid:** Designate exactly one automation layer as the canonical writer for each field. If Apex needs to set a field, do not also set it in a before-save Flow. Document which layer owns which fields on objects that have both Flow and Apex triggers.

---

## Gotcha 2: Flow Cannot Make Synchronous HTTP Callouts After Record Save

**What happens:** An architect designs a Record-Triggered Flow (after save) to call an external REST API in the same transaction. The Flow is built using a custom Apex action that makes the callout. At runtime, Salesforce throws `System.CalloutException: You have uncommitted work pending. Please commit or rollback before calling out.`

**Why it happens:** After a record save, the platform has uncommitted DML in memory. HTTP callouts are blocked when there is uncommitted DML to prevent partial state from being visible to external systems. This restriction applies to Flow invoking Apex actions that make callouts, not just to Apex code directly.

**Common misconception:** Developers assume that wrapping the callout in an Apex action called from Flow bypasses the restriction. It does not — the restriction is enforced at the transaction level, regardless of what invoked the callout.

**How to avoid:**
- For after-save callouts: Fire a Platform Event from the Flow. An Apex Platform Event trigger receives the event in a fresh transaction context and makes the callout there.
- For before-save callouts: Not possible at all from a record-triggered context. Design the callout to occur in a separate async transaction (Queueable, `@future`).
- Never put a callout in the same after-save transaction as the record DML, in any layer.

---

## Gotcha 3: Record-Triggered Flow and Apex Triggers Share the Same SOQL and DML Governor Limits

**What happens:** An org has both a Record-Triggered Flow and an Apex trigger on the Account object. The Flow does a Get Records query and the Apex trigger also does a SOQL query. In isolation, each uses 1 SOQL query out of the 100 allowed per transaction. Together they use 2. When Flow contains a loop with a Get Records inside the loop body (an anti-pattern), each loop iteration uses an additional SOQL query — and those queries count against the same 100-limit shared with Apex.

**Why it matters for design:** Teams that build Flow in isolation from Apex code do not know how many SOQL queries the other automation layer is consuming. When both scale up, the shared limit is hit before either team expects it.

**How to avoid:**
- Before adding SOQL queries in Flow or Apex, check the total SOQL budget already consumed by other automations on the object. Use debug logs with `LIMIT_USAGE_FOR_NS` to see consumption.
- Never put a Get Records (SOQL) element inside a Flow loop. Collect IDs first, then query outside the loop using a collection.
- When an object has both a complex Flow and a complex Apex trigger, assign one layer ownership of all SOQL queries for a given use case and pass data to the other layer rather than querying independently.

---

## Gotcha 4: Custom Metadata Queries Are Cached — But Only After the First Access in a Transaction

**What happens:** A developer uses Custom Metadata Types (CMDT) for routing config because "CMDT queries don't count against SOQL limits." They write code that queries the same CMDT type five times across five separate Apex methods in one transaction, expecting zero SOQL usage. In reality, the first query counts against the SOQL limit. Subsequent queries for the same type in the same transaction hit the cache and do not count.

**The nuance:** CMDT records are cached per transaction after first access. The first access in a transaction consumes one SOQL query. If the same CMDT type is queried again in the same transaction (even from a different class), the cached result is returned — no additional SOQL cost.

**How to avoid:**
- Query CMDT once per transaction and store the result in a static variable (Apex) or pass it as a collection to subflows (Flow).
- Do not use CMDT as a free substitute for all config storage. It reduces SOQL cost after the first query, but it does not eliminate the first query. It also does not support row-level security — all profiles can query all CMDT records.

---

## Gotcha 5: The 2,000-Element Flow Interview Limit Is Per Interview, Not Per Flow Definition

**What happens:** A Flow is designed with a loop that iterates over records. When the record count exceeds a threshold, the Flow interview throws `The flow tried to execute a flow interview that has exceeded the maximum number of executed elements: 2000`.

**The misunderstanding:** The limit applies to the number of *elements executed in a single interview* — not to the number of elements defined in the Flow. A 5-element Flow that loops 500 times executes 2,500 element invocations and hits the limit.

**When it occurs:** Loops without proper exit conditions, or loops over large collections (e.g., all Contacts related to an Account) in a Flow that fires on Account update where one Account has 400+ related Contacts.

**How to avoid:**
- Keep loops in Flow small — use Flows for per-record or small collection logic, not bulk batch processing.
- If bulk processing is needed (hundreds or thousands of records per transaction), use Scheduled Apex or Batch Apex instead of a Scheduled Flow with a large loop.
- Monitor element count during testing by enabling Flow debug logs and reviewing interview execution trees.

---

## Gotcha 6: Process Builder Actions Still Fire Even Though Process Builder Is Deprecated

**What happens:** An architect migrates automation to Flow but leaves an old Process Builder active, assuming it has no effect since it predates modern automation. The Process Builder still fires on `after save`, and its actions (field updates, child record creation) overlap with the new Flow's actions. Both execute in the same transaction — causing duplicate records, unexpected field overwrites, or governor limit exhaustion.

**Why it occurs:** Deprecation of Process Builder for *new* automation does not deactivate existing active Process Builders. Every active Process Builder continues to execute on every matching record save until it is explicitly deactivated.

**How to avoid:**
- When migrating to Flow, explicitly deactivate (and eventually delete) the Process Builder being replaced. Do not rely on the new Flow "taking over" — both will run simultaneously until the old one is deactivated.
- Use Setup → Process Automation → Process Builder to audit all active Process Builders and map each one to its migration status.
- After deactivating a Process Builder, monitor the org for 48 hours for unexpected behavior changes before deleting it.
