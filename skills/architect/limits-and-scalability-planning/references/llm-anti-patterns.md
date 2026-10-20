# LLM Anti-Patterns — Limits and Scalability Planning

Common mistakes AI coding assistants make when generating or advising on Salesforce governor limits and scalability planning.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Citing Outdated or Incorrect Governor Limit Values

**What the LLM generates:** "Salesforce allows a maximum of 100 SOQL queries per transaction" or "The DML limit is 100 statements per transaction" when the actual limits are 100 SOQL queries (synchronous) but 200 in async context, and 150 DML statements (synchronous) / 150 (async).

**Why it happens:** Training data includes limit values from many Salesforce releases. Limits have changed over time (e.g., async SOQL limit was raised), and LLMs often conflate synchronous and asynchronous contexts or cite deprecated numbers.

**Correct pattern:**

```text
Always specify the execution context when citing limits:
- Synchronous: 100 SOQL queries, 150 DML statements, 10,000 ms CPU
- Asynchronous (Batch, Queueable, Future): 200 SOQL queries, 150 DML, 60,000 ms CPU
- Source: Apex Developer Guide 264 "Per-Transaction Apex Limits" (L19747-19782)
```

**Detection hint:** Check any specific numeric limit cited against the current Salesforce Governor Limits documentation. Flag if the number does not match or the sync/async context is missing.

---

## Anti-Pattern 2: Ignoring Org-Wide Limits in Favor of Per-Transaction Limits Only

**What the LLM generates:** Scalability advice that focuses exclusively on per-transaction governor limits (SOQL, DML, CPU) while ignoring org-wide limits like the 24-hour API request allocation, daily async Apex execution limit (250,000 or number of licenses x 200, whichever is greater), daily Bulk API batches, or data storage limits.

**Why it happens:** Per-transaction governor limits dominate Apex training data because they cause the most visible runtime errors. Org-wide daily limits and storage caps are less frequently discussed in code-centric content.

**Correct pattern:**

```text
Scalability planning must address BOTH transaction-level AND org-level limits:

Transaction-level: SOQL, DML, CPU, heap, callouts per execution
Org-level (daily/rolling):
  - API request allocation (based on edition + user licenses)
  - Async Apex executions (250,000 or licenses x 200; the opt-in elastic beta adds up to 2 million
    more for Batch, Queueable and future in production orgs only — scheduled stays capped,
    apexdev 264 L19937-19953, L20222, L20237)
  - Bulk API batches (15,000 per rolling 24h, shared by Bulk API and Bulk API 2.0;
    lim 264 L301-302)
  - Data storage (per edition, per license type)
  - File storage (separate allocation)
  - Platform Event publish allocations

Use the Limits REST resource (/services/data/vXX.0/limits/) to query current consumption.
```

**Detection hint:** Search for scalability recommendations that only mention "governor limits" without referencing API allocation, storage, or daily async caps.

---

## Anti-Pattern 3: Recommending Batch Apex as a Universal Scalability Solution

**What the LLM generates:** "If you are hitting governor limits, move the logic to Batch Apex" as a blanket recommendation without assessing whether the problem is actually a transaction-volume issue versus a design issue (e.g., queries in loops, unnecessary record processing).

**Why it happens:** Batch Apex is the most widely documented pattern for handling large data volumes. LLMs default to it without evaluating whether the root cause is poor query design, missing indexes, or an architecture that should use Platform Events or Change Data Capture instead.

**Correct pattern:**

```text
Before recommending Batch Apex, diagnose the root cause:
1. Queries in loops? Fix the code pattern first.
2. Non-selective queries on large objects? Add custom indexes and rewrite WHERE clauses.
3. Processing millions of records on a schedule? Batch Apex is appropriate.
4. Real-time event processing at scale? Consider Platform Events + trigger subscribers.
5. Cross-object aggregation? Consider async SOQL or reporting snapshots.

Batch Apex itself has limits: 5 queued-or-active jobs, the 250K (or licenses x 200)
24-hour async execution budget that start/execute/finish all draw from, and each
execute() still has per-transaction limits within its scope (apexdev 264 L19936,
L19985, L20001).
```

**Detection hint:** Flag "use Batch Apex" recommendations that do not include a root-cause analysis or consideration of the 5-concurrent-job limit and daily async cap.

---

## Anti-Pattern 4: Understating the Impact of Data Skew on Scalability

**What the LLM generates:** Generic data model advice that ignores ownership skew, lookup skew, and parent-child skew scenarios. For example, recommending a single "System Admin" user as the default owner for millions of records, or not flagging a lookup field that points 80% of child records to the same parent.

**Why it happens:** Data skew is a Salesforce-specific concept tied to internal database locking and sharing recalculation. General database training data does not cover Salesforce's row-lock contention on parent records or the sharing rule recalculation delays caused by ownership skew.

**Correct pattern:**

```text
Address three skew types in scalability reviews:

1. Ownership skew: No single user should own more than 10,000 records on a
   private-OWD object (LDV best practices 264 L1033). Use queue-based ownership or distribute across service accounts.

2. Lookup skew: Avoid a single parent record being referenced by >10,000 child
   records via lookup when the parent object has sharing rules or triggers.

3. Account data skew: Accounts with >10,000 child Contacts, Opportunities, or
   Cases cause lock contention during sharing recalculation and DML operations
   (LDV best practices 264 L1052: no parent with more than 10,000 children).

Mitigation: redistribute ownership, split parent records, or move to public OWD
where sharing recalculation is not needed.
```

**Detection hint:** Search for ownership or lookup recommendations that assign all records to a single user or queue without a volume threshold warning. Flag any data model with a 1:N ratio exceeding 10,000 on private-OWD objects.

---

## Anti-Pattern 5: Confusing Platform Event Limits with Standard Object DML Limits

**What the LLM generates:** "Platform Events are not subject to governor limits" or "You can publish unlimited Platform Events in a single transaction" when in fact publishing is metered: 250,000 event messages per rolling hour in Enterprise, Unlimited and Performance (50,000 in Developer), a separate 24-hour delivery allocation for external subscribers, and per-transaction `EventBus.publish` limits (Platform Events Developer Guide 264 L7071, L7141; Apex Developer Guide 264 L19801, L19838).

**Why it happens:** Platform Events are marketed as a way to decouple from synchronous governor limits, which LLMs interpret as "no limits." The actual allocation model (hourly entitlement based on edition, high-volume event bus as a paid add-on) is less represented in training data.

**Correct pattern:**

```text
Platform Event allocations (high-volume events, the default since API 45.0, PE L237):
- Per-transaction: publish-after-commit EventBus.publish counts as a DML
  statement (150); publish-immediately has its own 150 calls (apexdev 264
  L19801, L19838)
- Publishing: 250,000 per rolling hour EE/UE/PXE, 50,000 Developer (PE L7141)
- Delivery to API subscribers (Pub/Sub, CometD, empApi, relays): 50,000 UE,
  25,000 EE, 10,000 DE per rolling 24h, summed across clients (PE L7071);
  Apex trigger and flow subscribers do not count (PE L7039-7041)
- Payload: 1 MB max per event (PE L7000)
- Concurrent CometD clients: 2,000 UE/PXE, 1,000 EE, across all channels (PE L6972)

Add-on license (per add-on):
- +100,000 deliveries/day and +25,000 publishes/hour (PE L7231-7233)

Always verify the org's current entitlement using /services/data/vXX.0/limits/
```

**Detection hint:** Flag any claim that Platform Events have "no limits" or "unlimited throughput", any "daily = hourly x 24" arithmetic, and any 250,000 figure labelled as a delivery (rather than hourly publishing) allocation.

---

## Anti-Pattern 6: Proposing Custom Object Proliferation Without Checking Org Limits

**What the LLM generates:** Data model recommendations that freely add custom objects, custom fields, and relationship fields without mentioning org-wide metadata limits. For example, proposing 10 new custom objects when the org is already at 2,900 of 3,000.

**Why it happens:** LLMs treat the data model as infinitely extensible because most Salesforce examples involve a few objects. The hard limits on custom objects, custom fields per object, and relationship fields are rarely mentioned in training data.

**Correct pattern:**

```text
Before proposing new custom objects or fields, check org metadata limits.
UNVERIFIED (2026-10-20): every count below is from Salesforce Help "General
Limits", not in the Winter '27 corpus; SKILL.md carries a conflicting 800
custom-object figure. Read the org's edition allocation before relying on any.
- Custom objects: 200 (PE), 2,000 (EE/UE) — query via Tooling API or Setup
- Custom fields per object: 500 (Enterprise), 800 (Unlimited/Performance) — by
  edition, NOT by Shield or any add-on
- Relationship fields per object: 40 maximum
- Roll-up summary fields per object: 25 maximum
- Custom indexes: request via Salesforce Support for non-standard indexes

Use the EntityDefinition and FieldDefinition Tooling API objects to audit
current consumption before proposing additions.
```

**Detection hint:** Flag data model proposals that add 5+ custom objects without referencing current org metadata consumption or edition-specific limits.

---

## Anti-Pattern 7: Treating "Delete the Unused Fields" as an Immediate Fix for a Full Field Allocation

**What the LLM generates:** Asked "we're at the 500-field limit on Account, what do we do?", the model answers "delete unused fields to free up slots" and stops there — implying the headroom is available as soon as the delete is confirmed.

**Why it happens:** Deleting a field in Setup looks final and the field disappears from the field list, so the training signal is "deleted means gone." The soft-delete grace period lives in a separate help topic that code-centric content rarely quotes.

**Correct pattern:**

UNVERIFIED (2026-10-20): the soft-delete window, the 75% Purge threshold, the error strings and the permissions below are from Salesforce Help field-deletion topics that are not in the Winter '27 corpus.

```text
A deleted custom field is soft-deleted. Until hard delete completes (or 15 days
elapse, whichever comes first) it still consumes:
  - a slot in the object's 500/800 custom field allocation
  - a slot in the allocation for its field type — 40 relationship fields,
    25 roll-up summary fields

Symptoms of an allocation exhausted by soft-deleted fields:
  "Unable to access page"
  "No clean data columns available for custom fields"

To reclaim sooner: object's Deleted Fields page -> Erase (marks ready for the
hard-delete background job), then Purge (starts it). Purge appears only at 75%+
of the object's field allocation, Salesforce Classic, EE/PE/UE. Requires
Customize Application; Purge also requires View All Data.
```

**Detection hint:** Flag any field-limit remediation that promises immediate headroom from deletion, or that omits the 15-day window from a release-timeline recommendation.
