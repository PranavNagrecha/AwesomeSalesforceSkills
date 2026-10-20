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

**Endpoint:** Tooling API (`/services/data/vXX/tooling/query`). The `ApexClass` and `ApexTrigger` sObjects are Tooling-API-only.

**Critical constraint:** `Body` is NOT a filterable column on `ApexClass` or `ApexTrigger`. You cannot use `WHERE Body LIKE '%x%'` — Salesforce rejects the query with `field 'Body' can not be filtered in a query call`. Fetch the full body and filter client-side.

Two Tooling queries, looped for pagination:

```sql
SELECT Id, Name, NamespacePrefix, Body
FROM ApexClass
WHERE NamespacePrefix = null
LIMIT 200 OFFSET 0
```

```sql
SELECT Id, Name, NamespacePrefix, TableEnumOrId, Body
FROM ApexTrigger
WHERE TableEnumOrId = 'Account'
LIMIT 200 OFFSET 0
```

Then **client-side**, filter the returned rows where `Body` contains the field name using the word-boundary regex below. This is the only safe pattern — `Body` is effectively a "blob" column from SOQL's perspective.

When `include_managed = true`, omit the `NamespacePrefix = null` filter. When `object` is not specified for the `ApexTrigger` query, drop the `WHERE TableEnumOrId` clause and filter client-side.

## Post-processing (word-boundary filter)

`LIKE '%<field>%'` produces false positives on substring matches (e.g. `Industry_Code__c` would match a search for `Industry`). After fetching, apply word-boundary regexes. Apex rarely writes `Object.Field` — it normally names a field bare — so the qualified patterns alone miss most real references. A row is a real reference iff **at least one** of these patterns matches its `Body`; record which one as `match_class`:

| `match_class` | Pattern (case-insensitive) | Notes |
|---|---|---|
| `qualified` | `\b<Object>\.<Field>\b` | Exact `Opportunity.Discount__c` (e.g. `Opportunity.Discount__c.getDescribe()`). |
| `describe` | `\bSObjectType\.<Object>\.fields\.<Field>\b` | Schema token access. |
| `soql` | `\b<Field>\b` inside a SOQL/SOSL literal whose `FROM` clause names `<Object>` | Find each inline `\[\s*(SELECT\|FIND)[\s\S]*?\]` and each string literal matching `(?i)'[^']*\bFROM\s+<Object>\b[^']*'` (dynamic SOQL); search `\b<Field>\b` inside that span only. Covers SELECT lists, WHERE, ORDER BY, and `Database.query` strings. |
| `dynamic` | `'<Field>'` or `"<Field>"` | String-literal access: `record.put('Discount__c', x)`, `sobj.get('Discount__c')`, map keys `'Discount__c' => 0.3`. The object is implied, not stated: report as **dynamic, confirm manually** (check the surrounding variable or `Schema.SObjectType` is `<Object>`). |
| `typed-dot` | `\b(\w+)\.<Field>\b` where `\1` is a variable declared as `<Object>` | e.g. `opp.Discount__c` with `Opportunity opp` or `List<Opportunity> ... for (Opportunity opp : ...)`. Needs a declaration scan: collect `\b<Object>\s+(\w+)\b` and `<Object>\s*\[\]`/`List<<Object>>`/`for (<Object> (\w+) :` names, then match `\.<Field>`. Best-effort; a var of another type or a `var`/`Object` declaration is missed. |

Examples (`object = Opportunity`, `field = Discount__c`):

| Body snippet | Match? | Class |
|---|---|---|
| `Opportunity.Discount__c.getDescribe()` | match | `qualified` |
| `Schema.SObjectType.Opportunity.fields.Discount__c` | match | `describe` |
| `[SELECT Id, Discount__c FROM Opportunity WHERE Discount__c > 0.2]` | match | `soql` |
| `new Map<String,Object>{ 'Discount__c' => 0.3 }` | match | `dynamic` (confirm manually) |
| `Opportunity opp = ...; if (opp.Discount__c > 0.2) {...}` | match | `typed-dot` (best-effort) |
| `Discount_Code__c = 'x';` or `[SELECT Id FROM Account WHERE Discount__c > 1]` | no match | substring blocked by `\b`; the `soql` span names `Account`, not `Opportunity` |

**False-positive note.** The bare-name classes (`soql` scoped by `FROM`, `dynamic`, `typed-dot`) will match the same field API name on a *different* object (`Quote.Discount__c`) when the object cannot be pinned from the span. Always return `match_class` with each row so the consuming agent can rank: `qualified`/`describe`/`soql` are high confidence, `typed-dot` medium, `dynamic` lowest until confirmed.

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
  "match_class": "qualified | describe | soql | dynamic | typed-dot",
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
