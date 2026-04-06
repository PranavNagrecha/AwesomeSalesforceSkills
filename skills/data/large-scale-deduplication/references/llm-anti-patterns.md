# LLM Anti-Patterns — Large Scale Deduplication

Common mistakes AI coding assistants make when generating or advising on large-scale Salesforce deduplication.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating a Merge Loop That Ignores the 10-Call Per Transaction Limit

**What the LLM generates:** A for loop inside a standard Apex class (or an execute-anonymous block) that calls `Database.merge()` for every pair in a large list — e.g., iterating over 500 records and calling merge on each one.

**Why it happens:** LLMs know `Database.merge()` exists and know that loops are the natural pattern for bulk processing. They do not reliably apply the 10-calls-per-transaction governor limit unless it is explicitly in context.

**Correct pattern:**

```apex
// WRONG — will throw LimitException after 10 calls
for (Dedup_Pair__c pair : largePairList) {
    Database.merge(new Account(Id = pair.Master_Id__c),
                   new Account(Id = pair.Losing_Id__c), false);
}

// CORRECT — use Batch Apex with batch size = 10
// Database.executeBatch(new DedupMergeBatch(), 10);
// Each execute() block receives 10 records and calls merge exactly 10 times
```

**Detection hint:** Look for `Database.merge()` inside a `for` loop without a counter guard checking against 10. Any unconstrained loop over a merge call in a non-batch context is wrong.

---

## Anti-Pattern 2: Applying Database.merge() to Custom Objects

**What the LLM generates:** Code that calls `Database.merge(masterCustomObj, loserCustomObj, false)` for a custom object like `Account_Branch__c` or `Product_Catalog__c`.

**Why it happens:** LLMs generalize from Account/Contact/Lead merge examples to assume `Database.merge()` works on any SObject. The compile-time restriction to standard objects is not consistently applied.

**Correct pattern:**

```apex
// WRONG — compile error for custom objects
Database.merge(new MyCustomObject__c(Id = masterId),
               new MyCustomObject__c(Id = loserId), false);

// CORRECT — manual survivorship for custom objects
// 1. Copy fields from loser to master
// 2. Re-parent child records (update lookup fields)
// 3. Delete the loser record
MyCustomObject__c loser = [SELECT Id, Field1__c, Field2__c FROM MyCustomObject__c WHERE Id = :loserId];
MyCustomObject__c master = [SELECT Id FROM MyCustomObject__c WHERE Id = :masterId];
master.Field1__c = (master.Field1__c == null) ? loser.Field1__c : master.Field1__c;
update master;
delete loser;
```

**Detection hint:** Any `Database.merge()` call where the SObject type ends in `__c` is always wrong. Flag it immediately.

---

## Anti-Pattern 3: Recommending Standard Duplicate Jobs for Million-Record Retroactive Cleanup

**What the LLM generates:** "Use Salesforce's built-in Duplicate Jobs feature to find and merge all your historical duplicates across your entire org." Presented as a complete solution for millions of records.

**Why it happens:** Duplicate Jobs are the "official" Salesforce deduplication feature and appear in training data prominently. LLMs do not reliably surface the per-run record processing cap or the distinction between ongoing hygiene and retroactive bulk cleanup.

**Correct pattern:**

```
For retroactive deduplication of millions of records:
- Use Bulk API 2.0 to export all records with key matching fields
- Run matching logic externally (Python, SQL, or third-party tool)
- Produce (master_id, losing_id) pair list
- Merge via Batch Apex or third-party tool (DemandTools, Cloudingo)

Reserve Duplicate Jobs for:
- Ongoing post-go-live hygiene (recently modified records)
- Lower-volume sweeps as part of regular data stewardship
```

**Detection hint:** Any recommendation to use Duplicate Jobs as the primary mechanism for a one-time cleanup of millions of pre-existing records should be flagged and replaced with the Bulk API + external matching pattern.

---

## Anti-Pattern 4: Omitting Automation Bypass Before Bulk Merge

**What the LLM generates:** A batch Apex merge job with no mention of disabling or bypassing Flows, triggers, or workflow rules before running.

**Why it happens:** LLMs focus on the merge logic itself and do not consistently surface the operational pre-condition that automation must be evaluated and gated before running bulk merges at volume.

**Correct pattern:**

```
Before running any bulk merge batch in production:
1. Audit active Flows and Apex triggers on the target object
2. Add a Custom Permission bypass flag to automation that should not fire during bulk merges
   (e.g., IF(!$Permission.Bulk_Merge_Bypass) at the start of the Flow or trigger)
3. Grant the bypass permission to the running user for the batch job
4. Re-enable and revoke the bypass after the batch completes
```

**Detection hint:** Any bulk merge recommendation that does not include a step for evaluating and gating automation is incomplete. Add a pre-merge automation audit step.

---

## Anti-Pattern 5: Ignoring Downstream ID Dependencies Before Merging

**What the LLM generates:** A complete dedup strategy (matching, survivorship, batch merge) with no mention of external systems that hold the losing record IDs.

**Why it happens:** LLMs reason within the Salesforce boundary. The concern about external data warehouses, marketing automation platforms, ERP integrations, or analytics tools that stored Salesforce IDs is a cross-system architectural concern that LLMs do not surface by default.

**Correct pattern:**

```
Before executing any merge batch:
1. Identify all external systems integrated with the target object
2. For each system: determine whether it uses Salesforce REST API record lookups
   (gets the ID redirect) or stores IDs in a database and queries by them (gets zero rows)
3. For systems that do not follow redirects: plan an ID refresh or re-sync after merges complete
4. For data warehouses: update ETL pipelines to re-map old IDs to master IDs using
   the MergeHistory or EntitySubscription data if available
```

**Detection hint:** A dedup strategy recommendation that does not include a step for auditing external ID dependencies should be flagged as incomplete for any org with active integrations.
