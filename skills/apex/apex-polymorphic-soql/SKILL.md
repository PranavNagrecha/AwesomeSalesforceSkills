---
name: apex-polymorphic-soql
description: "Polymorphic SOQL with TYPEOF: querying Task.WhatId, Task.WhoId, ContentDocumentLink.LinkedEntityId, FeedItem.ParentId; fallback to Type filters; indexing and selectivity. NOT for Activity object model (use activity-and-task-patterns). NOT for general SOQL (use apex-soql-patterns)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
tags:
  - apex
  - soql
  - typeof
  - polymorphic
  - whatid
  - linkedentityid
triggers:
  - "soql typeof what when account opportunity"
  - "polymorphic lookup query salesforce what.name fails"
  - "contentdocumentlink linkedentityid polymorphic query"
  - "typeof where clause syntax soql"
  - "polymorphic id type filter what.type"
  - "apex query all attachments across object types"
inputs:
  - Polymorphic field and its possible target objects
  - Fields needed per target type
  - Selectivity / index requirements
outputs:
  - TYPEOF query template
  - Type-filtered fallback queries
  - Indexing strategy for polymorphic filters
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Apex Polymorphic SOQL

Activate when writing SOQL against polymorphic fields — `Task.WhatId`, `Task.WhoId`, `Event.WhatId`, `ContentDocumentLink.LinkedEntityId`, `FeedItem.ParentId`, `Note.ParentId`. Polymorphic fields reference multiple object types; field access requires `TYPEOF` or `Type` filters, and the platform's indexing rules are different from normal lookup fields.

## Before Starting

- **Know which fields are polymorphic.** Not many: Task/Event WhatId/WhoId, ContentDocumentLink.LinkedEntityId, FeedItem.ParentId, Note.ParentId, EmailMessageRelation.RelationId, a few others.
- **Decide: TYPEOF or Type filter?** TYPEOF returns per-type projected fields in one query. `WhereType` filter narrows to one type then accesses its fields normally.
- **Plan selectivity.** `WhatId = :id` is selective; `What.Type = 'Account'` is a filter, not an index.

## Core Concepts

### TYPEOF syntax

```
SELECT Id, Subject,
  TYPEOF What
    WHEN Account THEN Name, Industry
    WHEN Opportunity THEN Amount, StageName
    ELSE Name
  END
FROM Task
WHERE ActivityDate = TODAY
```

Per-row, the query returns fields of the matched target type. `ELSE` is optional — include it to cover unmatched cases.

### Type filter fallback

```
SELECT Id, What.Name FROM Task WHERE What.Type = 'Account'
```

Post-filter, `What.Name` is safe because every match is an Account. Less flexible than TYPEOF but simpler.

### Common polymorphic fields

- `Task.WhatId` — Account, Opportunity, custom, ...
- `Task.WhoId` — Contact or Lead
- `ContentDocumentLink.LinkedEntityId` — any object with content enabled
- `FeedItem.ParentId` — any feed-enabled object
- `Note.ParentId` / `NoteAndAttachment.ParentId` — legacy

### Indexing

Polymorphic field equality on Id is selective (indexed). Filtering on `.Type` is a non-indexed filter — apply after an Id-selective filter.

## Common Patterns

### Pattern: TYPEOF with common-parent field

```
SELECT Id, Subject, What.Name, What.Type FROM Task WHERE Id IN :ids
```

`What.Name` works because Name is on every polymorphic target's parent. Avoids TYPEOF ceremony for common fields.

### Pattern: TYPEOF for type-specific fields

Use when you need Industry (Account), Amount (Opportunity), etc. Only TYPEOF can project per-type fields.

### Pattern: Two-step query

Query IDs and types; partition; re-query per type with full field lists. Useful when downstream logic per type is complex.

## Decision Guidance

| Need | Pattern |
|---|---|
| Just Id, Type, Name | Flat query with `What.Name` |
| Per-type fields in one pass | TYPEOF WHEN |
| One specific type only | `WHERE What.Type = 'Account'` |
| Complex per-type processing | Query once, partition in Apex, re-query per type |

## Recommended Workflow

1. Identify the polymorphic field and its possible target objects.
2. Decide per-type fields required.
3. If varied per type, use TYPEOF; if one type only, use Type filter.
4. Ensure Id or other selective filter is present — Type alone is non-selective.
5. Apex-side: iterate results and use `instanceof` or `.getSObjectType()` to dispatch.
6. Test with rows of each target type present.
7. Measure query plan if performance-critical.

## Review Checklist

- [ ] Query uses TYPEOF or Type filter for per-type fields
- [ ] Selective filter (Id, date range) present
- [ ] ELSE branch on TYPEOF handles unmapped types
- [ ] Apex iteration uses `getSObjectType()` or `instanceof` for dispatch
- [ ] Tests seed at least two target-type rows
- [ ] Query plan reviewed for polymorphic selectivity

## Salesforce-Specific Gotchas

1. **Not all polymorphic fields support TYPEOF.** Task, Event, ContentDocumentLink, FeedItem, Note do; verify for newer objects.
2. **`Schema.SObjectType.Task.fields.WhatId.getReferenceTo()`** returns the full list of possible target types at runtime.
3. **TYPEOF cannot be used in subqueries** (inner queries within SELECT list). Plan accordingly.

## Output Artifacts

| Artifact | Description |
|---|---|
| Polymorphic query library | Reusable TYPEOF queries per field |
| Target-type catalog | Field → list of possible objects |
| Dispatcher helper | Apex utility routing by record type |

## Related Skills

- `admin/activity-and-task-patterns` — Activity object model
- `apex/apex-soql-patterns` — SOQL patterns generally
- `data/large-data-volume-patterns` — selectivity and indexing
