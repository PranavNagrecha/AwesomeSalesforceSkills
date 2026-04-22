# LLM Anti-Patterns — Apex Record Clone Patterns

Common mistakes AI coding assistants make when cloning sObjects.

## Anti-Pattern 1: Expecting `isDeepClone` to clone children

**What the LLM generates:**

```
Opportunity newOpp = opp.clone(false, true, false, false);
insert newOpp;
// User expects OpportunityLineItems to be cloned too — they aren't.
```

**Why it happens:** The flag is named misleadingly.

**Correct pattern:**

```
"Deep clone" refers to in-memory formula/field preservation, NOT
recursive relationship cloning. To clone children:

1. Query parent + children subselect
2. Clone parent → insert → get new parent Id
3. For each child, clone(), set lookup to new parent Id, add to list
4. Insert children in bulk

Skipping step 3's clone and inserting the child directly references
the original parent Id.
```

**Detection hint:** `clone(_, true, _, _)` on a parent sObject with an expectation that child lists populate.

---

## Anti-Pattern 2: `preserveId=true` then insert

**What the LLM generates:**

```
Account copy = acc.clone(true);
insert copy;  // DUPLICATE_VALUE or similar
```

**Why it happens:** Model doesn't know preserveId is for in-memory use.

**Correct pattern:**

```
Salesforce won't let you insert a record with a pre-set Id —
that's the database's job. preserveId=true is for:

- Asserting equality after mutation in tests
- Building in-memory graph structures

For an insertable clone: clone() or clone(false, ...).
```

**Detection hint:** `clone(true, ...)` followed by `insert`.

---

## Anti-Pattern 3: `preserveReadonly=true` without the permission

**What the LLM generates:**

```
// Data-migration script preserving CreatedDate
Account copy = src.clone(false, false, true, false);
insert copy;
// CreatedDate silently replaced with System.now() on the new record
```

**Why it happens:** Model assumes the flag grants the capability.

**Correct pattern:**

```
preserveReadonly requires:

1. Org feature "Set Audit Fields upon Record Creation" enabled
   (Setup → User Interface → enable Create Audit Fields)
2. Running user has the "Set Audit Fields upon Record Creation"
   permission (profile or permset)

Without both, the clone inserts with fresh audit fields. Verify:

System.debug(UserInfo.getUserType() + ' ' +
  FeatureManagement.checkPermission('CreateAuditFields'));

And test the expectation explicitly.
```

**Detection hint:** Script uses `clone(_, _, true, _)` without documenting the audit-fields permission requirement.

---

## Anti-Pattern 4: Cloning OpportunityLineItem across pricebooks without repointing

**What the LLM generates:**

```
OpportunityLineItem copy = oli.clone();
copy.OpportunityId = newOpp.Id;  // but newOpp is on a different Pricebook
insert copy;   // FIELD_INTEGRITY_EXCEPTION
```

**Why it happens:** Model sees `clone()` as a pure copy.

**Correct pattern:**

```
OpportunityLineItem has a PricebookEntryId that ties it to the
parent Opportunity's Pricebook2Id. If cloning across pricebooks:

1. Map original PricebookEntryId → equivalent entry in target pricebook
2. Set copy.PricebookEntryId to the target pricebook entry
3. Then insert

If same pricebook, no extra step. But ALWAYS ensure target
Opportunity.Pricebook2Id matches the line items' pricebook.
```

**Detection hint:** Opportunity + line item clone across opportunities with differing Pricebook2Id.

---

## Anti-Pattern 5: No `Cloned_From__c` traceability

**What the LLM generates:** Clone, insert, move on — no record of the source.

**Why it happens:** Model focuses on the copy mechanics.

**Correct pattern:**

```
Operational support teams need to trace: "which record is this
a copy of?" Add a lookup (or External_Id text) field:

Account copy = src.clone();
copy.Cloned_From__c = src.Id;   // custom lookup
insert copy;

Six months later, someone investigating why a record has odd data
can jump back to the source in one click. Without this, clones
are untraceable after the Apex context ends.
```

**Detection hint:** Clone-and-insert with no source-reference field assignment.
