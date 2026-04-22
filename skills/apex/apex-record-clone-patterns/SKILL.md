---
name: apex-record-clone-patterns
description: "SObject.clone(preserveId, isDeepClone, preserveReadonly, preserveAutonumber): shallow vs deep clone semantics, related-record replication, clone with parent repointing, autonumber preservation. NOT for data migration (use bulk-api-and-large-data-loads). NOT for record snapshots (use field-history-tracking)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
tags:
  - apex
  - clone
  - sobject
  - deep-clone
  - autonumber
triggers:
  - "sobject clone apex deep shallow preserveid"
  - "clone record with child records related list"
  - "clone preserveautonumber same number new record"
  - "clone record readonly fields createddate systemmodstamp"
  - "duplicate opportunity with line items apex"
  - "clone account with contacts children apex"
inputs:
  - Record(s) to clone
  - Whether children/related records must travel
  - Whether readonly/system fields must be preserved
outputs:
  - Clone invocation code
  - Relationship reparenting plan
  - Insert strategy
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-22
---

# Apex Record Clone Patterns

Activate when duplicating an sObject record in Apex — one record with a new Id, a record with its children, or a snapshot with preserved audit fields. The `SObject.clone()` method has four boolean flags that control deep-vs-shallow, Id preservation, readonly-field behavior, and autonumber handling. Each has failure modes if misread.

## Before Starting

- **Define scope.** Just the record, or the record + children? Clone does NOT walk relationships by default.
- **Decide Id preservation.** Cloning for insert → `preserveId=false` (default). Cloning for in-memory work → `preserveId=true`.
- **Audit-field expectations.** `CreatedDate`, `LastModifiedDate`, etc. are readonly; `preserveReadonly=true` requires `CreateAuditFields` user permission.

## Core Concepts

### Method signature

```
public SObject clone(Boolean preserveId, Boolean isDeepClone, Boolean preserveReadonly, Boolean preserveAutonumber)
```

All four default to `false`. Typical invocations:

```
Account copy = acc.clone();                       // shallow, no Id, no readonly, new autonumber
Account copy = acc.clone(false, false, false, true);  // preserve autonumber
Account copy = acc.clone(true);                   // keep Id (for in-memory diffing)
```

### Flags in detail

| Flag | Meaning |
|---|---|
| `preserveId` | Clone has the same Id as original (rarely useful — can't `insert` a record with Id) |
| `isDeepClone` | Copies field values regardless of type (but NOT related records) |
| `preserveReadonly` | Copies `CreatedDate`, `CreatedById`, `LastModifiedDate`, `SystemModstamp`. Requires `CreateAuditFields` perm |
| `preserveAutonumber` | Clone carries the same autonumber value |

### "Deep clone" does NOT clone children

`isDeepClone=true` is a misnomer — it preserves formula/aggregate field values in the in-memory copy. It does NOT fetch and clone child records.

### Cloning children requires explicit query + reparent

```
Opportunity opp = [SELECT Id, Name, (SELECT Id, Product2Id, Quantity, UnitPrice FROM OpportunityLineItems) FROM Opportunity WHERE Id = :srcId];
Opportunity newOpp = opp.clone(false, false, false, false);
newOpp.Name = 'Copy of ' + opp.Name;
insert newOpp;
List<OpportunityLineItem> newLines = new List<OpportunityLineItem>();
for (OpportunityLineItem oli : opp.OpportunityLineItems) {
    OpportunityLineItem copy = oli.clone();
    copy.OpportunityId = newOpp.Id;
    newLines.add(copy);
}
insert newLines;
```

### Readonly-field preservation

```
Account a = [SELECT Id, Name, CreatedDate FROM Account WHERE Id = :id];
Account copy = a.clone(false, false, true, false);
insert copy;  // CreatedDate preserved — only if running user has CreateAuditFields permission
```

Perm gate: Setup → System Permissions → "Set Audit Fields upon Record Creation" must be enabled and permission assigned.

## Common Patterns

### Pattern: "Copy of" with new autonumber

```
Case c = [SELECT Id, Subject, Origin FROM Case WHERE Id = :id];
Case copy = c.clone();            // CaseNumber autonumber regenerated
copy.Subject = 'Copy of ' + c.Subject;
insert copy;
```

### Pattern: Deep copy of Opportunity with line items

(See "Cloning children" code above.)

### Pattern: Bulk clone 1→N

```
List<Account> src = [SELECT Id, Name FROM Account WHERE ...];
List<Account> copies = new List<Account>();
for (Account a : src) {
    for (Integer i = 0; i < 5; i++) {
        Account c = a.clone();
        c.Name = a.Name + ' v' + i;
        copies.add(c);
    }
}
insert copies;
```

### Pattern: Clone via `Database.insert` with duplicate-rule bypass

```
Database.DMLOptions dmo = new Database.DMLOptions();
dmo.DuplicateRuleHeader.AllowSave = true;
List<Database.SaveResult> srs = Database.insert(copies, dmo);
```

## Decision Guidance

| Scenario | Flags |
|---|---|
| Duplicate a record, new Id, new autonumber | `clone()` |
| Duplicate a record, preserve autonumber | `clone(false, false, false, true)` |
| In-memory copy for comparison (no insert) | `clone(true, false, false, false)` |
| Data migration preserving CreatedDate | `clone(false, false, true, false)` + user perm |
| Duplicate record + children | query children, clone, reparent, insert parent first |

## Recommended Workflow

1. Identify whether children need to travel. If yes, query the subselect in the source SOQL.
2. Clone the parent with the flags you need (usually `clone()` is sufficient).
3. Insert the parent first to obtain the new Id.
4. Clone each child, set the foreign key to the new parent Id, insert in bulk.
5. For audit-field preservation, verify the running user has `CreateAuditFields`.
6. Test with duplicate rules enabled AND disabled.
7. Document the clone's semantic relationship to the source (e.g., store a `Cloned_From__c` lookup for traceability).

## Review Checklist

- [ ] Child records explicitly queried + reparented (clone does NOT do this)
- [ ] Autonumber preservation decision intentional
- [ ] Audit-field preservation paired with `CreateAuditFields` permission
- [ ] Bulk clone keeps DML inside limits
- [ ] Clone traceability (e.g., source-record lookup) persisted
- [ ] Duplicate rule behavior considered

## Salesforce-Specific Gotchas

1. **`clone()` does NOT recursively clone children.** `isDeepClone=true` preserves formula values but doesn't fetch relationships.
2. **`preserveId=true` followed by `insert` throws — you cannot insert with an Id.** Only useful for in-memory diffing/asserting.
3. **`preserveReadonly=true` without `CreateAuditFields` silently ignores audit fields** — the new record gets `SYSTEM.now()` timestamps, not the originals.
4. **OpportunityLineItem clone requires a Price Book Entry that exists on the target Opportunity** — cloning across pricebooks needs repointing.
5. **Record Type Id is not cleared by clone** — ensure target record type is valid for the cloned picklist values.

## Output Artifacts

| Artifact | Description |
|---|---|
| Clone utility class | Reusable parent + children cloner |
| Traceability field | `Cloned_From__c` lookup to source |
| Permission doc | Note `CreateAuditFields` requirement for audit-preserving clones |

## Related Skills

- `apex/apex-record-relationships` — relationship traversal for deep copies
- `data/bulk-api-and-large-data-loads` — volume cloning via ETL
- `data/external-id-strategy` — matching source/target across orgs
