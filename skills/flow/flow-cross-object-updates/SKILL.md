---
name: flow-cross-object-updates
description: "Cross-object DML in Flow: updating parent from child or child from parent via Get/Update Records, lookup traversal in formulas, and bulkification. NOT for Apex cross-object updates. NOT for Process Builder (migrate-workflow-pb covers migration). Use when building flows that must write to a related record."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - flow
  - cross-object
  - get-records
  - update-records
  - bulkification
triggers:
  - "flow update parent from child record trigger"
  - "flow rollup sum contacts update account field"
  - "flow record-triggered get related records update"
  - "flow update child records without loop bulkification"
  - "flow formula dot traversal parent field lookup"
  - "flow cross object update too many soql dml"
inputs:
  - Parent/child object relationship (lookup or master-detail)
  - Trigger context (record-triggered, scheduled, platform event)
  - Bulk volume expected
outputs:
  - Flow design using Get Records + Update Records (no per-record loop DML)
  - Dot-notation traversal where a Get Records is unneeded
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-22
---

# Flow Cross Object Updates

Activate when a flow must read or write a record other than the one that triggered it. Getting the pattern right avoids SOQL-inside-loop disasters and preserves bulk behavior when 200 records arrive at once.

## Before Starting

- **Identify the relationship direction.** Child→parent (lookup traversal) and parent→child (Get Records for related list) behave differently.
- **Check bulk context.** Record-triggered flows run with up to 200 records per batch — every Get/Update inside a loop multiplies by 200.
- **Prefer formulas for read-only parent fields.** `$Record.Account.Name` is free; a Get Records call is not.

## Core Concepts

### Child → Parent read: dot-notation traversal

In a Contact-triggered flow, `{!$Record.Account.Industry}` resolves the lookup in memory — no SOQL. Traverse up to 5 levels.

### Child → Parent write: single Update Records

```
Update Records:
  Object: Account
  Filter: Id = {!$Record.AccountId}
  Fields to set: Last_Contact_Date__c = {!$Record.CreatedDate}
```

One DML per flow execution, regardless of batch size — Flow bulkifies automatically **as long as** the Update is outside a loop.

### Parent → Child: Get Records then Update Records

```
Get Records:
  Object: Contact
  Filter: AccountId = {!$Record.Id}
  Store: All records in collection `contacts`

Loop contacts:
  Assignment: each.Mailing_City__c = {!$Record.BillingCity}
  Add to collection: contactsToUpdate

Update Records (outside loop):
  Input collection: contactsToUpdate
```

**The Update Records is OUTSIDE the loop** — this is the single most important bulkification rule.

### Rollup-style aggregation

Salesforce has Rollup Summary only on master-detail. For lookups, use:

- `CollectionProcessor` (Count / Sum of a number collection) → single Update on parent
- Or Declarative Lookup Rollup Summaries (DLRS) — admin-friendly community app

## Common Patterns

### Pattern: "Last Activity" parent stamp

Record-triggered on Task create → Update Records on WhatId parent setting `Last_Task_Date__c = {!$Record.CreatedDate}`. One DML, fully bulk-safe.

### Pattern: Cascade status to children

Parent Account `Status__c` changes → Get Records (Contacts where AccountId = parent) → loop assign `Status__c` → Update outside loop.

### Pattern: Guard against recursion

Child → Parent update can retrigger a parent-triggered flow. Use an entry condition on the parent flow (`ISCHANGED(relevant field)`), or guard with a transient boolean custom setting.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Read parent field for decision | Dot-notation `$Record.Parent.Field` | No SOQL cost |
| Stamp a single field on parent | Update Records (no loop) | Bulkified by Flow engine |
| Update many children from parent change | Get Records → Loop assign → Update (outside loop) | Single DML regardless of count |
| Sum/count children | CollectionProcessor or DLRS | Rollup Summary lookup-incompatible |
| Update grandparent (Account → Opportunity → OpportunityLineItem) | Dot-traversal for read; separate Get+Update for writes | Nested updates aren't implicit |

## Recommended Workflow

1. Map the relationship direction and record volume expected.
2. Prefer dot-notation traversal for reads — avoid a Get Records when a formula suffices.
3. For writes, always keep Update Records OUTSIDE any Loop element.
4. Set entry conditions to prevent unneeded runs (ISCHANGED / ISNEW).
5. Add a Fault path on every Get/Update → Screen or custom error.
6. Test with 1, 2, and 200-record batches in a sandbox.
7. Verify SOQL/DML counts via Debug Logs — should be constant, not scaling.

## Review Checklist

- [ ] No Update/Create Records inside a Loop
- [ ] Dot-notation used where a Get Records is unneeded
- [ ] Entry conditions prevent unnecessary execution
- [ ] Fault paths present on every data element
- [ ] Bulk test (200 records) executed in sandbox
- [ ] SOQL and DML query counts verified constant

## Salesforce-Specific Gotchas

1. **Update Records inside Loop** — silent SOQL-101 killer when a batch arrives. No warning at design time; shows up only under load.
2. **Dot-notation returns null if intermediate lookup is empty** — always null-check: `IF(ISBLANK({!$Record.AccountId}), ..., {!$Record.Account.Name})`.
3. **Recursion between parent-triggered and child-triggered flows** — flow runs are not re-entrant by default, but cross-object updates can chain-trigger other flows. Monitor the flow execution stack in the debug log.
4. **Record-triggered flows on a child can't see parent field values that were just set by a before-trigger on the parent in the same transaction** — order-of-execution still applies.
5. **Scheduled paths lose context of original record** — if you rely on `$Record` in a scheduled path, pick up a fresh copy with Get Records.

## Output Artifacts

| Artifact | Description |
|---|---|
| Bulkified child→parent stamp flow | Reference implementation for "last activity" pattern |
| Parent→children cascade flow | Get + Loop-assign + Update-outside-loop skeleton |
| Fault-path subflow | Reusable error capture and notification |

## Related Skills

- `flow/flow-best-practices` — naming, fault paths, documentation
- `flow/flow-bulk-testing` — verifying 200-record safety
- `apex/apex-trigger-handler-pattern` — when to switch from Flow to Apex
