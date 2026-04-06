# LLM Anti-Patterns — Roll-Up Summary Alternatives

Common mistakes AI coding assistants make when generating or advising on alternatives to native Roll-Up Summary fields.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting Native Roll-Up Summary on Lookup Relationships

**What the LLM generates:** "Add a Roll-Up Summary field on Account to count related Tasks" or "Create a Roll-Up Summary on Account to sum Invoice__c amounts" without noting that native Roll-Up Summary fields only work on master-detail relationships, not lookups.

**Why it happens:** Roll-Up Summary is the most common aggregation pattern in Salesforce training data. LLMs recommend it without verifying the relationship type, which must be master-detail for native roll-up support.

**Correct pattern:**

```text
Native Roll-Up Summary requirements:
- ONLY works on Master-Detail relationships
- Parent object must be the master
- Maximum 25 roll-up summary fields per object

For Lookup relationships, use alternatives:
1. Declarative Lookup Rollup Summary (DLRS) — AppExchange, open source
2. Record-Triggered Flow with aggregate Get Records
3. Apex trigger with AggregateResult query
4. Scheduled Flow for periodic recalculation
5. Report formula or dashboard lens (read-only, no stored field)
```

**Detection hint:** Flag "Roll-Up Summary" recommendations on objects connected via lookup relationships. Check the relationship type before recommending native roll-ups. Look for Task, Event, or custom objects with lookup (not master-detail) to the parent.

---

## Anti-Pattern 2: Writing Non-Bulkified Apex Rollup Triggers

**What the LLM generates:** Apex trigger code that queries the aggregate inside a loop or fires a separate SOQL aggregate query for each record in the trigger context, hitting governor limits during bulk operations.

**Why it happens:** Single-record examples dominate training data. LLMs generate code that works for one record but fails for 200 (the standard trigger batch size).

**Correct pattern:**

```text
Bulkified Apex rollup trigger pattern:

trigger InvoiceLineItemTrigger on Invoice_Line_Item__c (after insert, after update, after delete, after undelete) {
    // Collect all affected parent IDs
    Set<Id> parentIds = new Set<Id>();
    for (Invoice_Line_Item__c item : Trigger.isDelete ? Trigger.old : Trigger.new) {
        parentIds.add(item.Invoice__c);
    }
    if (Trigger.isUpdate) {
        for (Invoice_Line_Item__c item : Trigger.old) {
            parentIds.add(item.Invoice__c); // include old parent if reparented
        }
    }

    // Single aggregate query for ALL affected parents
    Map<Id, AggregateResult> totals = new Map<Id, AggregateResult>();
    for (AggregateResult ar : [
        SELECT Invoice__c parentId, SUM(Amount__c) total
        FROM Invoice_Line_Item__c
        WHERE Invoice__c IN :parentIds
        GROUP BY Invoice__c
    ]) {
        totals.put((Id)ar.get('parentId'), ar);
    }

    // Update parents in bulk
    List<Invoice__c> updates = new List<Invoice__c>();
    for (Id parentId : parentIds) {
        Decimal total = totals.containsKey(parentId)
            ? (Decimal)totals.get(parentId).get('total') : 0;
        updates.add(new Invoice__c(Id = parentId, Total_Amount__c = total));
    }
    update updates;
}
```

**Detection hint:** Flag Apex rollup triggers with SOQL inside a `for` loop. Look for `[SELECT ... FROM ... WHERE Id = :singleId]` patterns inside trigger iteration.

---

## Anti-Pattern 3: Recommending DLRS Without Mentioning Deployment and Maintenance Overhead

**What the LLM generates:** "Install DLRS from the AppExchange and configure your rollup" without mentioning that DLRS uses Apex triggers or scheduled jobs under the hood, requires Salesforce admin management of rollup definitions, and has known scaling limitations with very high data volumes.

**Why it happens:** DLRS is a popular open-source solution and appears frequently in training data as a simple alternative. Its operational requirements (managed package updates, scheduled job monitoring, debugging trigger failures) are underrepresented.

**Correct pattern:**

```text
DLRS considerations:

Advantages:
- Declarative rollup configuration (no custom code)
- Works on lookup relationships
- Supports COUNT, SUM, MIN, MAX, AVG, FIRST, LAST, CONCATENATE

Operational overhead:
- Managed package: requires AppExchange installation and periodic updates
- Real-time mode: deploys an Apex trigger per child object — counts toward
  org limit of triggers per object
- Scheduled mode: runs as a scheduled Apex job — counts against daily async limit
- Debug complexity: errors appear in DLRS-managed trigger context, not your code
- Scale limit: real-time mode can struggle with >100K child records per parent

When to choose DLRS vs Flow vs Apex:
- DLRS: fast setup, moderate volume, admin-managed
- Flow: native, no package dependency, moderate complexity
- Apex trigger: full control, high volume, developer-managed
```

**Detection hint:** Flag DLRS recommendations that do not mention managed package overhead, trigger deployment, or volume considerations.

---

## Anti-Pattern 4: Using Flow Rollups Without Handling Delete and Undelete Events

**What the LLM generates:** A record-triggered Flow that recalculates a parent total on after-save (insert/update) but does not handle record deletion or undelete, leaving the parent total incorrect when child records are deleted.

**Why it happens:** Flow examples in training data predominantly show insert and update scenarios. Delete-triggered Flows and undelete handling are less commonly demonstrated.

**Correct pattern:**

```text
Complete Flow-based rollup requires ALL trigger events:

1. After Insert: recalculate parent total (new child added)
2. After Update: recalculate parent total (child amount changed)
   Also handle reparenting: if parent lookup changed, recalculate
   BOTH the old parent and the new parent
3. After Delete: recalculate parent total (child removed)
   Note: the Flow must fire on "A record is deleted"
4. After Undelete: recalculate parent total (child restored from Recycle Bin)

Flow implementation:
- Use Get Records to aggregate: get all children of the parent,
  then use a Loop + Assignment to calculate the sum
- OR use a single Get Records with a formula resource for COUNT
- Update the parent record with the calculated value
- Place the Update element OUTSIDE any loop
```

**Detection hint:** Flag Flow-based rollup implementations that only handle insert/update events. Check for missing "record is deleted" trigger configuration.

---

## Anti-Pattern 5: Ignoring Timing and Consistency Issues with Async Rollup Approaches

**What the LLM generates:** "Use a scheduled Flow to recalculate rollups every hour" without noting that the parent field will be stale between calculation runs, which may cause issues for validation rules, reports, and integrations that read the rollup value.

**Why it happens:** Scheduled approaches are presented as simpler alternatives. The consistency gap (stale data between runs) is an operational concern not covered in feature tutorials.

**Correct pattern:**

```text
Rollup timing approaches and tradeoffs:

Real-time (trigger/Flow after-save):
- Parent updated immediately after child DML
- Consistent: downstream logic sees current value
- Performance cost: additional DML per child transaction
- Best for: fields used in validation rules, integrations, or user-facing totals

Scheduled (batch/scheduled Flow):
- Parent updated on a schedule (hourly, daily, etc.)
- Stale between runs: reports and validation rules see old value
- Lower transaction cost: batch updates parent in bulk
- Best for: analytics-only fields, dashboard metrics, non-critical totals

Hybrid:
- Real-time for critical rollups (amount, count)
- Scheduled for expensive rollups (distinct count, complex filters)
- Document which rollups are real-time vs scheduled
```

**Detection hint:** Flag scheduled rollup recommendations where the rollup field is used in validation rules, trigger conditions, or real-time integrations. Check for consistency requirements.
