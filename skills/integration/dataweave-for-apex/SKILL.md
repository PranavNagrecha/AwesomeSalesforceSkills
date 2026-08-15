---
name: dataweave-for-apex
description: "Use when transforming structured data inside Apex — CSV → JSON, XML → SObject list, JSON → flattened CSV, or schema-mapping a third-party payload to a Salesforce model — and the existing options (`JSON.deserialize`, `Dom.Document` traversal) are too fragile. NOT for MuleSoft Anypoint DataWeave running off-platform (use architect/mulesoft-anypoint-architecture) — use apex/apex-json-serialization."
category: integration
salesforce-version: "Summer '24+"
well-architected-pillars:
  - Performance
  - Reliability
triggers:
  - "transform csv to json inside apex without external library"
  - "use dataweave script in apex to reshape payload"
  - "system dataweave apex execute script static resource"
  - "apex transform xml payload to sobject list"
  - "apex flatten nested json to csv with dataweave"
  - "DataWeave for Apex governor limits MIME type"
tags:
  - integration
  - apex
  - dataweave
  - transformation
  - data-mapping
  - mime-types
inputs:
  - "the source payload format (CSV, JSON, XML, application/x-www-form-urlencoded) and a sample"
  - "the target shape (Apex List<SObject>, Map<String,Object>, output payload format)"
  - "whether the script must be reused across multiple call sites or is a one-off"
outputs:
  - "a registered DataWeave static-resource script with explicit input/output MIME types"
  - "Apex caller using `Dataweave.Script` and `dwscript.execute()`"
  - "test fixture covering the input payload variants and the failure modes (empty input, malformed JSON, oversize payload)"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# DataWeave for Apex

Activate when an Apex method needs to transform between structured formats (CSV ⇄ JSON ⇄ XML ⇄ SObject) and the alternatives — hand-rolled loops over `JSON.deserializeUntyped()`, `Dom.Document` traversal, or pulling in a static-resource library — are producing fragile, hard-to-read code. The skill produces a DataWeave script registered as a static resource, the Apex `Dataweave.Script` caller, and a test fixture; it also rules the feature *out* when the transformation is trivial enough that built-in Apex parsing is the right answer.

---

## Before Starting

Gather this context before working on anything in this domain:

- The **source MIME type** and a literal sample of the input payload (3–5 records is enough). Without a sample you cannot author the DataWeave script confidently.
- The **target MIME type** and the desired output shape, including which fields are required vs optional and whether nested arrays should be flattened.
- Whether the script will be **invoked from a Queueable / Batch / sync trigger** — DataWeave-for-Apex consumes script-execution heap and CPU like any Apex; bulk transforms inside a synchronous trigger are usually the wrong place.
- Confirm the org is on **API version 61.0+** (Summer '24 or later). DataWeave-for-Apex went GA in Summer '24 after pilots in earlier releases.

---

## Core Concepts

### What DataWeave for Apex is, and is not

DataWeave for Apex (`System.Dataweave` / `Dataweave.Script`) is a Salesforce-native, in-platform implementation of the DataWeave 2.0 transformation language. It is not a runtime call to a MuleSoft instance, and the Salesforce org does not need a MuleSoft license to use it. The DataWeave engine runs inside the Apex transaction's resource envelope: heap, CPU, and the standard Apex governor limits all apply. There is no external network call.

It IS:
- A way to author transformation scripts in DataWeave 2.0 syntax and execute them from Apex.
- Useful for many-field reshapes, nested-array flattening, format conversions (CSV ↔ JSON ↔ XML), and schema-mapping payloads from external systems.

It is NOT:
- A bridge to MuleSoft Anypoint at runtime (those are different products with different deployment models).
- A way to escape governor limits — it runs inside the Apex limits envelope.
- The right tool for transformations that are 5 lines of Apex; the registration and call overhead exceeds the benefit on trivial cases.

### Authoring and registering a script

A DataWeave script is a static resource with a `.dwl` suffix and a strict header that declares input/output MIME types:

```dwl
%dw 2.0
input payload application/json
output application/json
---
payload map (item, idx) -> {
    accountName: item.name,
    revenue: item.financials.revenue default 0,
    ownerExternalId: item.owner.externalId
}
```

The static resource's name is what Apex uses to reference it. Cache control should be `Public` so the platform can cache the parsed script across executions.

### Invoking from Apex

```apex
Dataweave.Script myScript = Dataweave.Script.createScript('Account_Mapping_DW');
String inputJson = '[{"name":"Acme","financials":{"revenue":1000000},"owner":{"externalId":"E-1"}}]';
Dataweave.Result result = myScript.execute(
    new Map<String, Object>{ 'payload' => inputJson }
);
String outputJson = result.getValueAsString();
```

`execute` accepts a `Map<String, Object>` whose keys correspond to the `input <name>` declarations in the `.dwl` header. The result exposes `getValue()` (typed) and `getValueAsString()` (serialized).

### Supported input and output MIME types

DataWeave for Apex supports a subset of the full DataWeave MIME catalog. The reliably-available types are:

- `application/json`
- `application/xml`
- `application/csv`
- `application/x-www-form-urlencoded`
- `application/dw` (DataWeave native — useful for chaining)
- `text/plain`

Less common DataWeave types (Avro, YAML, Parquet) are not currently supported in Apex. Confirm against the current Apex Reference before assuming.

---

## Common Patterns

### CSV → SObject list

```dwl
%dw 2.0
input payload application/csv header=true
output application/json
---
payload map (row, idx) -> {
    Name: row.name,
    Industry: row.industry,
    AnnualRevenue: row.revenue as Number
}
```

Apex caller deserializes the JSON output into `List<Account>` via `(List<Account>) JSON.deserialize(out, List<Account>.class)`.

### XML → flattened JSON

```dwl
%dw 2.0
input payload application/xml
output application/json
---
{
    contracts: payload.envelope.contracts.*contract map (c) -> {
        id: c.@id,
        partyName: c.party.name,
        amount: c.amount as Number
    }
}
```

The `*contract` syntax handles "one or many" XML repeats safely; `@id` reads the attribute.

### Multi-input merge

A script can declare multiple inputs:

```dwl
%dw 2.0
input accounts application/json
input owners application/json
output application/json
---
accounts map (a) -> {
    name: a.name,
    ownerName: (owners filter ($.id == a.ownerId))[0].name default "Unassigned"
}
```

Apex passes both: `myScript.execute(new Map<String, Object>{ 'accounts' => accountsJson, 'owners' => ownersJson });`.

---

## Decision Guidance

| Situation | Choice | Rationale |
|---|---|---|
| 3-field-map JSON reshape | `JSON.deserializeUntyped` + plain Apex | Script overhead exceeds benefit on trivial cases |
| 30-field-map with conditionals and defaults | DataWeave-for-Apex | Script reads as the spec; Apex equivalent is 200 lines of Map manipulation |
| XML with deeply nested structure | DataWeave-for-Apex | DOM traversal in Apex is verbose and brittle to schema drift |
| CSV → SObject list (large file) | Bulk API 2.0 + ingest, not Apex | Apex CPU and heap are not the right place for >10k-row CSV |
| Apex Bulk Trigger transformation | Apex (not DataWeave) | Trigger CPU budget is too small to justify script-load overhead per execution |
| Reusable across many Apex callers | DataWeave script (static resource) | Single source of truth for the mapping spec |

---

## Recommended Workflow

1. Get a literal sample of the input and a literal sample of the desired output. Without samples, do not write a script.
2. Decide whether DataWeave is justified — apply the table above. If the Apex equivalent is under ~30 lines and read-once, write Apex.
3. Author the `.dwl` script in a scratch org's Developer Console or VS Code with the DataWeave extension. Iterate on the sample inputs until the output matches.
4. Save as a static resource named with a `_DW` suffix (convention) and cache control `Public`.
5. Wrap the call in an Apex service class so the resource name is in one place: `MyMappingService.transform(inputJson)`. The class should also handle the empty-input, malformed-input, and `Dataweave.ExecuteException` cases.
6. Write Apex tests with literal payload strings as fixtures. Assert on the Apex-deserialized output, not on the raw JSON, so structural drift surfaces as a compile error rather than a string mismatch.
7. Add a check that script-load failures fall back gracefully — `createScript` throws `Dataweave.ScriptException` if the resource is missing or malformed.

---

## Review Checklist

- The `.dwl` header declares input MIME types matching every key in the Apex `execute` map.
- The `output` MIME type matches what the Apex caller expects (`getValueAsString()` for text formats).
- `default` clauses cover every optional field in the source payload — DataWeave's null-handling is strict.
- The Apex caller catches `Dataweave.ExecuteException` (runtime errors during transformation) separately from `Dataweave.ScriptException` (script-loading errors).
- Tests cover at minimum: golden-path payload, empty input array, missing optional field, malformed input, and one large (>1MB) input to confirm heap behavior.
- The static resource cache control is `Public`, not `Private` — the latter forces re-parse on every execution.

---

## Salesforce-Specific Gotchas

- **Heap accounting** — DataWeave loads the entire input into memory before processing. A 5MB JSON input plus the parsed AST plus the output can exceed 12MB heap easily; profile under representative volumes before deploying to a synchronous path.
- **Static resource cache control** — Defaulting to `Private` causes the script to re-parse on every execution, eating CPU. Set `Public` unless there's a documented reason.
- **Numeric type coercion** — DataWeave's `Number` is a single type; the Apex side gets back a Decimal that may have a different scale than the source JSON. Combine with `apex-decimal-arithmetic-precision` rounding when feeding currency fields.
- **Date/time formatting** — DataWeave's default ISO-8601 output is `2026-05-07T12:00:00Z`; if the receiving system expects `2026-05-07T12:00:00.000+0000`, format explicitly with `as String { format: "yyyy-MM-dd'T'HH:mm:ss.SSSZ" }`.
- **Test coverage for static resources** — Apex tests can reference the static resource by name only if it exists in the org. In a fresh CI scratch org without seed data, ensure the resource is in `force-app/main/default/staticresources/`.
- **`Dataweave.ExecuteException` is the kitchen-sink** — Malformed input, missing required field, MIME-type mismatch, and division-by-zero in the script all surface as the same exception. Inspect `getMessage()` for the specific cause; do not assume a single failure mode.

---

## Output Artifacts

- `force-app/main/default/staticresources/<Name>_DW.dwl` — the script.
- `force-app/main/default/staticresources/<Name>_DW.resource-meta.xml` — content type `application/dw`, cache control `Public`.
- `force-app/main/default/classes/<Name>MappingService.cls` — the Apex service that calls `Dataweave.Script.createScript` and exposes a typed result.
- `force-app/main/default/classes/<Name>MappingServiceTest.cls` — fixture-driven tests over golden-path and failure-mode payloads.

---

## Related Skills

- `apex/apex-json-serialization` — when the transformation is small enough that JSON-only Apex is the right answer.
- `apex/apex-decimal-arithmetic-precision` — for currency/quantity fields that come through DataWeave with surprising scale.
- `architect/mulesoft-anypoint-architecture` — when the transformation belongs *outside* Salesforce on an existing MuleSoft platform.
- `integration/middleware-integration-patterns` — for the "do this in MuleSoft vs do this in Apex" decision at the architecture level.
- `integration/bulk-api-2-patterns` — when the data volume rules Apex out entirely.
