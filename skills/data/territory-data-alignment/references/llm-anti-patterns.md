# LLM Anti-Patterns — Territory Data Alignment

Common mistakes AI coding assistants make when generating or advising on Territory Data Alignment.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Legacy Territory Objects Instead of ETM Objects

**What the LLM generates:** SOQL or DML against `Territory`, `AccountTerritoryAssignment`, or `UserTerritory` — the Legacy Territory Management objects that were deprecated with ETM (Territory Management 2.0).

**Why it happens:** Legacy territory management predates ETM, and older Salesforce documentation, Stack Overflow answers, and training examples use the legacy object names. LLMs trained on broad web corpora carry this bias and conflate the two systems.

**Correct pattern:**

```soql
-- WRONG (Legacy TM)
SELECT Id, TerritoryId FROM AccountTerritoryAssignment WHERE AccountId = :accountId

-- CORRECT (ETM / Territory Management 2.0)
SELECT Id, Territory2Id, AssociationCause
FROM ObjectTerritory2Association
WHERE ObjectId = :accountId
  AND Territory2.Territory2Model.State = 'Active'
```

**Detection hint:** Any mention of `AccountTerritoryAssignment`, `UserTerritory` (without the `2`), or `Territory` (without the `2`) when the org context specifies ETM or Territory Management 2.0.

---

## Anti-Pattern 2: Assuming AssociationCause Can Be Updated After Insert

**What the LLM generates:** An UPDATE DML statement attempting to change the `AssociationCause` field on an existing `ObjectTerritory2Association` row from `Territory` to `Manual` (or vice versa).

**Why it happens:** LLMs pattern-match from general junction object behavior and assume all fields are mutable. `AssociationCause` behaves like a write-once discriminator, which is unusual and not well-represented in training data.

**Correct pattern:**

```apex
// WRONG — cannot update AssociationCause
update new ObjectTerritory2Association(Id = existingId, AssociationCause = 'Manual');

// CORRECT — delete the existing row and insert a new one with the desired AssociationCause
delete [SELECT Id FROM ObjectTerritory2Association WHERE Id = :existingId];
insert new ObjectTerritory2Association(
    ObjectId = accountId,
    Territory2Id = territoryId,
    AssociationCause = 'Manual'
);
```

**Detection hint:** Any `update` or `Database.update` call targeting an `ObjectTerritory2Association` row with `AssociationCause` in the field list.

---

## Anti-Pattern 3: Writing to a Territory2 from a Non-Active Model

**What the LLM generates:** An insert script or SOQL subquery that references `Territory2Id` values without first confirming the parent `Territory2Model.State = 'Active'`. The generated code often hardcodes a Territory2Model ID from a dev or sandbox environment.

**Why it happens:** LLMs generate plausible-looking IDs and queries but do not model the stateful constraint that only one territory model can be Active at a time or that writes to non-Active models fail.

**Correct pattern:**

```soql
-- Pre-flight check before any insert operation
SELECT Id, Name, State
FROM Territory2Model
WHERE State = 'Active'
LIMIT 1
-- Assert exactly one row is returned and its Id matches the target model
```

```apex
// Guard in Apex migration code
List<Territory2Model> activeModels = [
    SELECT Id, State FROM Territory2Model WHERE State = 'Active' LIMIT 1
];
if (activeModels.isEmpty()) {
    throw new IllegalStateException('No active Territory2Model found. Aborting insert.');
}
```

**Detection hint:** Any hardcoded `Territory2ModelId` or `Territory2Id` without an accompanying `Territory2Model.State = 'Active'` filter or pre-flight query.

---

## Anti-Pattern 4: Using Synchronous SOQL NOT IN Subquery for Large Coverage Gap Analysis

**What the LLM generates:** A synchronous SOQL query using `NOT IN (SELECT ObjectId FROM ObjectTerritory2Association ...)` intended to run in an Apex execute anonymous block or a standard report, without any consideration of governor limits.

**Why it happens:** The NOT IN subquery pattern is the natural SQL idiom for set difference. LLMs apply it directly without accounting for Salesforce's 50,000-row subquery limit in synchronous execution contexts.

**Correct pattern:**

```
// WRONG — will fail with SOQL exception for orgs with >50K territory associations
List<Account> gaps = [
    SELECT Id FROM Account
    WHERE Id NOT IN (SELECT ObjectId FROM ObjectTerritory2Association
                     WHERE Territory2.Territory2Model.State = 'Active')
];

// CORRECT for large orgs — use Bulk API 2.0 query to export association set,
// then compare externally (Python set difference, Data Loader export + Excel)
// OR use a Batch Apex approach that pages through accounts in chunks of 2,000
// and checks each chunk against a pre-queried Set<Id> of covered accounts.
```

**Detection hint:** A synchronous `NOT IN` subquery on `ObjectTerritory2Association` in any Apex context without an explicit comment about governor limit handling or a batch/async pattern.

---

## Anti-Pattern 5: Assuming Track Territory Assignment History Is Enabled by Default

**What the LLM generates:** A SOQL query against `Territory2ModelHistory` or `UserTerritory2AssignmentHistory` presented as a reliable audit mechanism, without any mention that the Track Territory Assignment History feature must be explicitly enabled in Setup before records are written.

**Why it happens:** LLMs learn that Salesforce objects named `*History` automatically track field changes (standard field history tracking). They generalize this pattern to ETM history objects, not knowing that ETM assignment history is an opt-in feature with its own Setup toggle and does not behave like standard field history tracking.

**Correct pattern:**

```
// WRONG — assumes history records exist for all assignments
SELECT ObjectId, Field, OldValue, NewValue, CreatedById, CreatedDate
FROM Territory2ModelHistory
WHERE CreatedDate = LAST_N_DAYS:30

// CORRECT — first verify the feature is enabled and history has been accumulating
// 1. In Setup → Territory Settings → verify "Track Territory Assignment History" is On
// 2. Note the enablement date — history records only exist from that date forward
// 3. Query with a date range that starts no earlier than the enablement date
// 4. If the result set is empty, the feature may not be enabled or the date range
//    predates enablement
```

**Detection hint:** Any query against `Territory2ModelHistory` or `UserTerritory2AssignmentHistory` presented as a complete solution without a prerequisite check on whether the Track Territory Assignment History feature is enabled.

---

## Anti-Pattern 6: Omitting Deduplication Before Bulk Inserts Into ObjectTerritory2Association

**What the LLM generates:** A bulk insert script that loads all rows from a source CSV or query result into `ObjectTerritory2Association` without checking for existing rows. The generated code assumes a unique constraint will prevent duplicates or that the platform will deduplicate.

**Why it happens:** Many standard Salesforce junction objects do enforce uniqueness (e.g., `GroupMember`). LLMs generalize this behavior to all junction objects. `ObjectTerritory2Association` does not enforce a unique constraint on (ObjectId, Territory2Id) — duplicates are accepted and silently stored.

**Correct pattern:**

```python
# Pseudo-code for idempotent bulk insert

# Step 1: export existing associations
existing = query("SELECT ObjectId, Territory2Id FROM ObjectTerritory2Association "
                 "WHERE Territory2.Territory2Model.State = 'Active'")
existing_set = {(r['ObjectId'], r['Territory2Id']) for r in existing}

# Step 2: filter source data
net_new = [r for r in source_data
           if (r['ObjectId'], r['Territory2Id']) not in existing_set]

# Step 3: insert only net-new rows
bulk_insert("ObjectTerritory2Association", net_new)
```

**Detection hint:** Any bulk insert script for `ObjectTerritory2Association` that does not include a prior query against existing rows or an explicit deduplication step.
