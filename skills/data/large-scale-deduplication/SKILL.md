---
name: large-scale-deduplication
description: "Strategies and tooling for large-scale data deduplication in Salesforce: tuning matching rules for high-volume orgs, batch merge jobs, third-party dedup tools (DemandTools, Cloudingo), surviving record selection logic, and post-merge validation. Use when cleaning millions of duplicate records, automating merges beyond UI limits, or designing enterprise dedup workflows. NOT for duplicate rule configuration (use admin/duplicate-management). NOT for standard Duplicate Management UI setup. NOT for single-record field-resolution questions (use data/record-merge-implications)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I merge thousands of duplicate accounts in Salesforce"
  - "matching rule tuning for large data volumes"
  - "batch deduplication job for Salesforce contacts"
  - "surviving record selection logic for merges"
  - "bulk merge apex limits deduplication at scale"
  - "third-party dedup tool DemandTools Cloudingo comparison"
tags:
  - deduplication
  - merge
  - matching-rules
  - batch-processing
  - data-quality
inputs:
  - "Object(s) to deduplicate (Account, Contact, Lead, or custom)"
  - "Estimated duplicate record count and total org volume"
  - "Survivorship criteria (which record wins and why)"
  - "Whether third-party tooling is available or in scope"
  - "Downstream system dependencies on surviving record IDs"
outputs:
  - "Batch deduplication strategy document"
  - "Apex batch merge job scaffold (if Apex approach chosen)"
  - "Survivorship scoring logic recommendation"
  - "Post-merge validation query set"
  - "Third-party tool evaluation checklist"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Large Scale Deduplication

Use this skill when an org has tens of thousands to millions of duplicate records and needs a programmatic strategy to identify, prioritize, and merge them safely. It covers Apex batch merge patterns, Bulk API–based duplicate identification, surviving record scoring logic, matching rule tuning for high-volume orgs, third-party tool selection, and post-merge validation. It does not cover standard Duplicate Management UI configuration — use `admin/duplicate-management` for that.

---

## Before Starting

Gather this context before designing or executing any large-scale dedup project:

- **Volume estimate** — how many total records on the target object, and how many are estimated duplicates? Volume determines whether Apex batches, third-party tools, or a hybrid approach is appropriate.
- **Survivorship rules** — who or what decides which record survives? Without explicit survivorship criteria, merges feel arbitrary and destroy user trust.
- **Downstream ID dependencies** — which external systems, integrations, or data warehouses hold Salesforce record IDs? Merging records deletes losing-record IDs. Systems that stored those IDs will receive redirects on subsequent API calls only if they follow HTTPS redirects correctly.
- **Apex `Database.merge()` limit** — each call accepts exactly one master record and up to two losing records (max 3 records total per call). This is a hard governor limit. Plan your batch logic accordingly.
- **Automation exposure** — Flows, Apex triggers, and workflow rules fire on the master record update and on the losing record delete during a merge. Disable or gate automation that would cause unintended side effects at volume.

---

## Core Concepts

### Apex Database.merge() Limits

`Database.merge()` is the only Apex DML statement for merging records. It supports three Salesforce standard objects: Account, Contact, and Lead. Limits:

- **Max 3 records per call** — one master + up to 2 losing records.
- **Max 10 merge calls per transaction** — each `Database.merge()` call counts against this governor limit.
- **DML rows** — each merge counts as one DML row for the master update plus one DML row per losing record deletion.
- At scale, a batch Apex job must chunk duplicate pairs or sets and stay within per-transaction limits. A single batch execution block that processes 200 scope records could call `Database.merge()` up to 10 times (the per-transaction limit), so effective throughput is roughly 20–30 records merged per batch chunk.

Custom objects do not support `Database.merge()`. For custom object deduplication at scale, use a combination of SOQL to identify duplicates and standard delete + field copy DML instead.

### Bulk API 2.0 for Duplicate Identification

Identifying duplicate pairs across millions of records cannot be done efficiently with SOQL alone (full-table self-joins are not supported in SOQL). The recommended pattern for ID discovery:

1. Export all records for the target object using Bulk API 2.0 query jobs — this retrieves the full ID + key-field dataset efficiently without hitting SOQL row limits.
2. Perform matching logic outside Salesforce (Python script, Data Loader with external DB, or a third-party tool) to produce a CSV of (master\_id, losing\_id) duplicate pairs.
3. Feed the resulting pairs back into Salesforce via a batch Apex job or a third-party merge tool.

Bulk API 2.0 supports up to 150 million records per query job and is the appropriate extraction mechanism for LDV dedup work.

### Matching Rule Selectivity at High Volume

Standard Salesforce Matching Rules use fuzzy and exact matchers on indexed fields. At large data volumes, matching rule selectivity has a direct performance impact:

- **Non-selective matching rules** (e.g., fuzzy match on a single common-value field like `City`) will perform full-table scans during real-time duplicate detection, causing save latency and potential timeouts.
- For LDV orgs, restrict matching rules to **highly selective indexed fields** — Email, Phone, External ID, or composite key fields — to keep evaluation fast.
- Retroactive deduplication of existing records using standard matching rules is not recommended at volume. Standard Duplicate Jobs (introduced in Summer '20 for orgs with Salesforce for Sales) can scan for existing duplicates against matching rules, but they have record caps per run and are not designed for millions of records.
- For retroactive work above the Duplicate Jobs limit, export and match externally using Bulk API 2.0.

### Surviving Record Selection Logic

Survivorship logic determines which record becomes the master. Poorly designed survivorship is the most common cause of user trust failures after a dedup project. Common scoring criteria:

| Criterion | Logic |
|---|---|
| Field completeness | Score each record by the number of non-null key fields; highest score wins |
| Most recent activity | Master = record with the most recent `LastActivityDate` |
| System of record origin | Prefer records sourced from a CRM migration or authoritative integration over UI-created records (use an External ID or source field) |
| Record age | Prefer the oldest `CreatedDate` as master for continuity of history |
| Related record count | Prefer the record with the most Opportunities, Cases, or Activities — it has the most relational history |

These criteria can be combined into a weighted score calculated in Apex or pre-computed during the Bulk API export phase.

### Third-Party Dedup Tools

For enterprise-scale deduplication (100K+ record sets, or cross-object matching), third-party tools handle complexity that Apex alone cannot:

- **DemandTools (Validity)** — desktop + cloud tool; provides matching algorithm configuration, survivorship rule builder, merge queue management, and audit logs. Widely used for Account/Contact/Lead dedup in enterprise orgs.
- **Cloudingo** — cloud-native SaaS; connects directly to org via OAuth, provides scheduled dedup jobs, survivorship rules, and field merge configuration. Handles high-volume jobs with retry logic.
- **Duplicate Check for Salesforce (Plauti)** — AppExchange native; integrates with Salesforce Duplicate Management but extends it for bulk processing and cross-object matching.

Third-party tools bypass the `Database.merge()` governor limits by using the Salesforce Merge REST API endpoint (`/services/data/vXX.0/sobjects/{SObject}/{Id}/merge`) directly, which still enforces a 3-record-per-call limit but allows higher throughput through parallel API calls.

---

## Common Patterns

### Batch Apex Merge Pattern

**When to use:** Duplicate pairs have already been identified (via Bulk API export + external matching or via a third-party identification step) and the org does not have third-party merge tooling. Suitable for up to ~50K duplicate pairs in a batch queue.

**How it works:**

1. Store identified duplicate pairs in a custom object or CSV-loaded Custom Metadata / Custom Setting rows: `(MasterId, LosingId)`.
2. A Batch Apex job queries the staging object in chunks.
3. In `execute()`, call `Database.merge()` for each pair. Catch partial errors with `Database.MergeResult` and log failures.
4. After each batch, the staging records are deleted or marked as processed.

```apex
global class DedupMergeBatch implements Database.Batchable<SObject>, Database.Stateful {
    global Integer processed = 0;
    global Integer failed = 0;

    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, Master_Id__c, Losing_Id__c FROM Dedup_Pair__c WHERE Status__c = \'Pending\''
        );
    }

    global void execute(Database.BatchableContext bc, List<Dedup_Pair__c> scope) {
        // Process up to 10 merges per transaction (governor limit)
        Integer mergeCount = 0;
        for (Dedup_Pair__c pair : scope) {
            if (mergeCount >= 10) break; // respect per-transaction limit
            Account master = new Account(Id = pair.Master_Id__c);
            Account loser  = new Account(Id = pair.Losing_Id__c);
            Database.MergeResult result = Database.merge(master, loser, false);
            if (result.isSuccess()) {
                pair.Status__c = 'Merged';
                processed++;
            } else {
                pair.Status__c = 'Failed';
                pair.Error__c  = result.getErrors()[0].getMessage();
                failed++;
            }
            mergeCount++;
        }
        update scope;
    }

    global void finish(Database.BatchableContext bc) {
        // Send summary email or log to custom object
    }
}
```

**Why not a single transaction:** `Database.merge()` is limited to 10 calls per transaction. Any attempt to merge more than ~20–30 records in one execution context hits this limit and throws a governor exception.

### Field Completeness Survivorship Scorer

**When to use:** No authoritative system-of-record field exists and survivorship must be data-driven based on field population.

**How it works:**

Pre-compute a completeness score for each record during the Bulk API export phase. Fields are assigned weights based on business importance:

```python
# Python scoring example (runs outside Salesforce during export phase)
FIELD_WEIGHTS = {
    'Email': 3,
    'Phone': 2,
    'BillingStreet': 1,
    'BillingCity': 1,
    'Website': 1,
    'AnnualRevenue': 2,
    'NumberOfEmployees': 1,
}

def score_record(record):
    return sum(weight for field, weight in FIELD_WEIGHTS.items()
               if record.get(field))

# Record with higher score becomes master
pairs = sorted(duplicate_group, key=score_record, reverse=True)
master, *losers = pairs
```

The resulting (master\_id, loser\_id) pairs are uploaded as a staging dataset for the merge batch.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Under 10K duplicate pairs, Account/Contact/Lead only | Batch Apex with Database.merge() + staging object | No additional tooling needed; manageable via governor limits |
| 10K–500K duplicate pairs, standard objects | Third-party tool (DemandTools or Cloudingo) | Handles volume, retry logic, and audit trails that Apex alone cannot provide reliably |
| Over 500K pairs or custom objects | Third-party tool + Bulk API 2.0 extraction with external matching engine | Maximum throughput; external matching avoids SOQL self-join limitations |
| Matching logic is complex (fuzzy name + address) | Export via Bulk API 2.0 and match externally (Python/Postgres) | SOQL fuzzy matching is limited; external tools offer better accuracy |
| Org has active automation (triggers, flows) | Disable or gate automation before running merge batch | Automation fires on every merge update/delete; at volume this causes timeouts or unwanted behavior |
| Custom objects with duplicates | Field copy + delete pattern (no Database.merge() for custom) | Database.merge() is unsupported on custom objects |

---

## Recommended Workflow

1. **Scope the project** — export a record count and sample of suspected duplicates for the target object using Bulk API 2.0. Confirm estimated duplicate volume. Identify survivorship criteria with the data steward or business owner. Document the downstream systems that hold Salesforce IDs.
2. **Design survivorship rules** — choose and document which record becomes the master based on field completeness scoring, system of record origin, activity recency, or related record count. Encode these rules in a scoring function (Apex or external script).
3. **Extract and match** — export all target records via Bulk API 2.0. Run matching logic (exact key, fuzzy name+address, or composite) using either Salesforce's native Duplicate Jobs feature (for smaller volumes) or an external matching engine. Produce a (master\_id, losing\_id) pair list.
4. **Disable automation** — identify Flows, Apex triggers, and workflow rules on the target object. Disable or add bypass flags for automation that would produce unintended side effects during the merge batch. Communicate the maintenance window.
5. **Execute merges** — load the pair list into a staging custom object. Run the Batch Apex merge job (or third-party tool) in a sandbox first. Validate a sample of merged records. Then run in production during low-traffic hours.
6. **Post-merge validation** — run SOQL queries to confirm child records were re-parented correctly (Opportunities, Cases, Activities). Check that losing record IDs redirect properly. Re-enable automation.
7. **Establish ongoing controls** — configure Duplicate Rules to prevent new duplicates from entering the org. Set up a periodic Duplicate Jobs run or scheduled third-party scan to catch ongoing drift.

---

## Review Checklist

- [ ] Survivorship rules documented and reviewed by the data steward
- [ ] Downstream systems and integrations that hold Salesforce IDs identified
- [ ] Automation (flows, triggers, workflow rules) disabled or bypassed for the merge run
- [ ] Staging object or pair list loaded and validated in sandbox
- [ ] Batch job tested in sandbox on a representative sample before production run
- [ ] Post-merge child record re-parenting verified via SOQL
- [ ] Losing record ID redirects confirmed for integrated systems
- [ ] Ongoing duplicate prevention controls in place (Duplicate Rules, scheduled scans)

---

## Salesforce-Specific Gotchas

1. **`Database.merge()` is limited to 10 calls per transaction** — exceeding this limit throws a governor limit exception, not a soft error. Batch Apex jobs must restrict the `execute()` block to 10 merge calls maximum. Scope size of 200 does not mean 200 merges per batch chunk.

2. **`Database.merge()` does not support custom objects** — attempting to call `Database.merge()` with a custom object SObject throws a compile error. For custom object deduplication, the pattern is: copy field values to the surviving record → re-parent child records manually via DML → delete the losing records.

3. **Losing record IDs are permanently deleted, not archived** — external systems that stored the losing ID receive an HTTP 301 redirect from the Salesforce REST API only if they call the record lookup endpoint. Systems using SOQL or stored IDs without a lookup step will silently return no data. Audit all integrations before running large merge batches.

4. **Standard Duplicate Jobs have a per-run record cap** — Duplicate Jobs (available in orgs with Salesforce for Sales features) are limited in how many records they process per run and are not designed for retroactive dedup of millions of records. For volumes above ~100K duplicate pairs, use Bulk API 2.0 extraction and external matching.

5. **Matching rule fuzzy evaluation at scale causes save latency** — non-selective fuzzy matching rules on large objects add significant overhead to every save operation on that object. Tune matching rules to use selective indexed fields (Email, External ID) before running a mass data load or import that would trigger matching rule evaluation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Deduplication strategy document | Scope, object targets, survivorship rules, tooling selection, and rollout plan |
| Duplicate pair staging CSV | (master\_id, losing\_id) pairs produced by the matching phase, ready for batch load |
| Batch Apex merge job | Apex batch class that processes the staging object and logs merge results |
| Post-merge SOQL validation set | Queries confirming child record re-parenting and duplicate pair elimination |
| Ongoing prevention config | Duplicate Rule and Duplicate Jobs configuration to prevent future drift |

---

## Related Skills

- admin/duplicate-management — standard Duplicate Management UI setup, matching rule configuration, duplicate rule design. Use this BEFORE large-scale dedup to prevent ongoing duplicate creation.
- data/record-merge-implications — field resolution rules, child record re-parenting behavior, and Apex merge semantics for individual or small-batch merges.
- data/data-quality-and-governance — broader data quality framework, validation rules, and governance controls.
- data/custom-index-requests — custom index design for the identifier fields used in matching rules.
