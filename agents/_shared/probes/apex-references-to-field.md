# Probe: apex-references-to-field

## Purpose

Enumerate Apex classes and triggers whose body references a given `<sObject>.<Field>` API name. Used anywhere an agent needs the blast radius of a field rename / delete / security-change.

## Arguments

| Arg | Type | Required | Notes |
|---|---|---|---|
| `object` | string | yes | sObject API name, e.g. `Account` |
| `field` | string | yes | Field API name, e.g. `Industry` or `Industry__c` |
| `include_managed` | boolean | no (default `false`) | Scan Apex in managed packages too |
| `limit_per_query` | integer | no (default `200`) | Tooling query LIMIT; loop for full coverage |

## Query

Two Tooling queries, looped for pagination:

```sql
SELECT Id, Name, NamespacePrefix, Body
FROM ApexClass
WHERE Body LIKE '%<field>%'
  AND (<managed_filter>)
LIMIT <limit_per_query> OFFSET <offset>
```

```sql
SELECT Id, Name, NamespacePrefix, TableEnumOrId, Body
FROM ApexTrigger
WHERE TableEnumOrId = '<object>'
  AND Body LIKE '%<field>%'
LIMIT <limit_per_query> OFFSET <offset>
```

Where `<managed_filter>` is `NamespacePrefix = null` when `include_managed == false`, otherwise omitted.

## Post-processing (word-boundary filter)

`LIKE '%<field>%'` produces false positives on substring matches (e.g. `Industry_Code__c` would match a search for `Industry`). After fetching, apply a regex filter:

```
\b<Object>\.<Field>\b
```

And also:

```
\bSObjectType\.<Object>\.fields\.<Field>\b
```

A row is a real reference iff at least one of those patterns matches its `Body`.

## Pagination

Salesforce Tooling API caps result sets. Loop with `OFFSET` until the returned row count is less than `limit_per_query`. If total exceeds 10,000 rows, stop and return `confidence: MEDIUM` with a truncation note — the org is over-scope for this probe.

## False-positive filters

- Substring matches (handled by word-boundary regex above).
- Managed-package classes when `include_managed == false` (handled by `NamespacePrefix = null`).
- Comment-only references — an agent MAY drop rows where the only match is inside a `/* ... */` or `//` comment block. This is an enhancement, not required.

## Returns

Array of records:

```json
{
  "kind": "ApexClass | ApexTrigger",
  "id": "01p...",
  "name": "AccountService",
  "namespace": null,
  "access_type": "read | write | unknown",
  "evidence_line": "acc.Industry = 'Tech';"
}
```

`access_type` classification:

- `write` — matched line contains an assignment (`<ref> = ...`) or appears inside DML payload construction (`new Account(Industry = ...)`).
- `read` — appears in a SOQL string, getter expression, or condition.
- `unknown` — the agent could not classify without AST parsing; flag for human review.

## Consumed by

- `field-impact-analyzer` — primary consumer
- `picklist-governor` — for picklist-field rename/delete blast radius
- `object-designer` — when proposing field consolidation
- `data-model-reviewer` — for cross-object dependency fan-out
