# LLM Anti-Patterns — Formula Field Performance and Limits

Common mistakes AI coding assistants make when generating or advising on formula field performance and limits. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting a Custom Index on a Formula Field

**What the LLM generates:** "Request a custom index on `Formula_Field__c` from Salesforce Support to speed up your SOQL queries."

**Why it happens:** LLMs know that custom indexes fix SOQL full-table-scan problems on standard and custom fields. They generalize this advice to all field types without knowing that formula fields are excluded from indexing because they have no stored value.

**Correct pattern:**

```
Formula fields cannot be indexed — they have no stored database value.
The correct fix is to materialize the formula result into a stored field
(Number, Checkbox, Text, etc.) using a Record-Triggered Flow, then
request a custom index on the stored field.
```

**Detection hint:** Look for any advice that mentions "custom index" alongside a `__c` field that is defined as a formula in the schema. Verify the field type before recommending an index.

---

## Anti-Pattern 2: Asserting That Triggers Fire When Formula-Dependent Data Changes

**What the LLM generates:** "You can detect when `Days_Open__c` (a formula using `TODAY()`) changes by comparing `Trigger.old` and `Trigger.new` values in your trigger."

**Why it happens:** LLMs model triggers as reacting to field-value changes. They do not model the distinction between stored and calculated fields. A formula referencing `TODAY()` or a parent object's field never writes a change to the row, so no trigger event fires.

**Correct pattern:**

```
Triggers and Change Data Capture cannot detect formula-field changes
because formula fields have no stored value — no DML write occurs when
the formula result would change. To react to a formula value change,
store the formula result in a real field using a Flow or Scheduled Apex,
then write trigger or CDC logic against the stored field.
```

**Detection hint:** Any code that compares `Trigger.old.FormulaField__c != Trigger.new.FormulaField__c` for a field whose type is Formula is suspicious. The comparison may not reflect changes caused by parent record updates or time passage.

---

## Anti-Pattern 3: Treating Compile Size as Source Character Count

**What the LLM generates:** "Your formula is 850 characters, well under the 5,000 character limit, so you have plenty of room to add more logic."

**Why it happens:** LLMs see a character count and a limit and perform a straightforward comparison. They are not aware that Salesforce's 5,000-character compile-size limit applies to the expanded compiled representation, not the source text. Cross-object field references are particularly expensive in compiled form.

**Correct pattern:**

```
The 5,000-character formula limit applies to compiled size, not source size.
A formula with 850 source characters can fail the limit if it contains
multiple cross-object field references (e.g., Account.Owner.Profile.Name).
The only reliable way to verify compiled size is to attempt a save in the
formula editor — Salesforce reports the error if the compiled limit is exceeded.
Workaround: split large formulas using helper formula fields to reduce
per-field compiled character usage.
```

**Detection hint:** Any claim that a formula is "safe" because its visible source character count is below 5,000 without verifying via a save attempt in the editor.

---

## Anti-Pattern 4: Recommending a Formula Field for SOQL Filtering Without a Performance Caveat

**What the LLM generates:** "Create a formula field `Is_Overdue__c = CloseDate < TODAY()` and filter your SOQL query with `WHERE Is_Overdue__c = true`."

**Why it happens:** The LLM correctly constructs the formula logic and the SOQL syntax. It does not model the query planner behavior that results from filtering on a non-indexed formula field. The recommendation is syntactically correct and functionally correct, but is architecturally wrong at scale.

**Correct pattern:**

```sql
-- For small objects (< 50k records): formula field in WHERE is acceptable.
-- For medium/large objects: materialize the formula into a stored field.

-- Wrong at scale:
SELECT Id FROM Opportunity WHERE Is_Overdue_Formula__c = true

-- Correct at scale (stored field + Flow sync + optional custom index):
SELECT Id FROM Opportunity WHERE Is_Overdue__c = true
```

**Detection hint:** Any SOQL WHERE clause that references a field with `_Formula__c` in the name, or any field whose metadata type is Formula. Run the Query Plan Tool before accepting the recommendation.

---

## Anti-Pattern 5: Skipping the Backfill Step When Introducing a Stored Mirror Field

**What the LLM generates:** "Create a new Checkbox field `Is_High_Value__c` and build a Record-Triggered Flow to populate it. Now use `WHERE Is_High_Value__c = true` in your SOQL."

**Why it happens:** The LLM correctly identifies the materialization pattern. It models the schema change and the Flow in isolation and does not model the state of existing records. It assumes the new field will contain correct values, but all records created before the Flow was activated have null or default values in the new field.

**Correct pattern:**

```apex
// After creating the stored field and deploying the Flow,
// always run a backfill to populate existing records:

public class BackfillIsHighValueBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id, Is_High_Value_Formula__c FROM Opportunity');
    }
    public void execute(Database.BatchableContext bc, List<Opportunity> scope) {
        for (Opportunity o : scope) {
            o.Is_High_Value__c = o.Is_High_Value_Formula__c;
        }
        update scope;
    }
    public void finish(Database.BatchableContext bc) {}
}
```

**Detection hint:** Any recommendation that introduces a stored mirror field and deploys a Flow without an explicit backfill step. Check for `SELECT COUNT() FROM ObjectName WHERE StoredField__c = null` as a post-deployment verification query — if it returns non-zero, the backfill is incomplete.

---

## Anti-Pattern 6: Confusing the 10 Cross-Object Formula Spanning Limit With Lookup Depth

**What the LLM generates:** "You can safely reference up to 10 lookup levels deep in a single formula (e.g., A.B.C.D.E.F.G.H.I.J is fine)."

**Why it happens:** The LLM maps "10 spanning relationships" to a depth-of-10 traversal in a single chain. The actual limit is 10 unique relationship objects across the entire formula, counting all reference paths. A formula with five different two-hop cross-object references may already be at or near the limit even though no single chain is deep.

**Correct pattern:**

```
The 10 cross-object formula spanning limit counts unique relationship
objects traversed anywhere in the formula, not the depth of any single
lookup chain. A formula referencing Account.Owner, Account.Owner.Profile,
Contract.Account, Contract.Pricebook2, and Opportunity.Campaign each
contributes to the count. Formulas that aggregate from many parent objects
can hit this limit quickly. Use a Flow-managed stored field to bypass it.
```

**Detection hint:** Any claim that a formula can traverse "up to 10 levels" in a single chain, or any formula design that references more than 5-6 distinct parent objects without an explicit spanning-limit check.
