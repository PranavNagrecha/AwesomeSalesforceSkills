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
  - "a DataWeaveResource script (dw/<Name>.dwl plus .dwl-meta.xml) with explicit input/output MIME types"
  - "Apex caller using `Dataweave.Script` and `dwscript.execute()`"
  - "test fixture covering the input payload variants and the failure modes (empty input, malformed JSON, oversize payload)"
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-19
---

# DataWeave for Apex

Activate when an Apex method needs to transform between structured formats (CSV ⇄ JSON ⇄ XML ⇄ SObject) and the alternatives — hand-rolled loops over `JSON.deserializeUntyped()`, `Dom.Document` traversal, or pulling in a static-resource library — are producing fragile, hard-to-read code. The skill produces a DataWeave script deployed as `DataWeaveResource` metadata, the Apex `DataWeave.Script` caller, and a test fixture; it also rules the feature *out* when the transformation is trivial enough that built-in Apex parsing is the right answer.

---

## Before Starting

Gather this context before working on anything in this domain:

- The **source MIME type** and a literal sample of the input payload (3–5 records is enough). Without a sample you cannot author the DataWeave script confidently.
- The **target MIME type** and the desired output shape, including which fields are required vs optional and whether nested arrays should be flattened.
- Whether the script will be **invoked from a Queueable / Batch / sync trigger** — DataWeave-for-Apex consumes script-execution heap and CPU like any Apex; bulk transforms inside a synchronous trigger are usually the wrong place.
- Confirm the version floors: `DataWeaveResource` exists from API 58.0 (`api_meta.txt` 264 L52120) and the calling Apex class must be at API 53.0 or later (`apexdev.txt` 264 L26984); the class's API version also selects the DataWeave syntax — 2.5 at 61.0 and earlier, 2.8 at 62.0, 2.9 at 63.0+ (L26905–26908). UNVERIFIED (2026-10-20): the Summer '24 GA date is not stated in the corpus.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is the largest input payload, and is the caller synchronous, Queueable or Batch?" | DataWeave holds the whole input and its parsed form on the Apex heap before producing output (gotcha 2) | A heap budget per caller, or a decision to paginate or transform off-platform |
| "Does the source XML use namespace prefixes?" | Undeclared namespaces return an empty result with no error (gotcha 5) | `ns` declarations for every prefix in the raw payload |
| "Which numeric fields land in Currency or fixed-scale Decimal fields?" | `as Number` keeps the source's scale, not the target field's (gotcha 4) | Explicit `setScale` or a format in the script |
| "What date/time format does the receiving system expect?" | The default ISO-8601 output may not match it (short list: date/time formatting) | A `format` on every outbound date |
| "Which source fields are optional, and what should the output carry when one is missing?" | A missing field surfaces as the same `System.DataWeaveScriptException` as every other runtime script error (gotcha 3) | `default` values and a test with the field absent |
| "What will support see when a transform fails in production?" | `DataWeaveScriptException` collapses many causes into one type (gotcha 3) | Logging of the message and an input excerpt before rethrow |
| "Does the `dw/` script deploy with the Apex and its tests, in every CI org?" | `createScript` loads only a `.dwl` already deployed to the org as metadata (gotchas 1, 6) | The `dw/` folder in the same source tree and deployment as the class |

A proper configuration fixes the payload ceiling, the type rules and the failure trail before the first production payload, rather than after the first heap exception.

---

## Core Concepts

### What DataWeave for Apex is, and is not

DataWeave for Apex (the `DataWeave` namespace: `DataWeave.Script`, `DataWeave.Result`) is a Salesforce-native, in-platform implementation of the DataWeave 2.0 transformation language. It is not a runtime call to a MuleSoft instance, and the Salesforce org does not need a MuleSoft license to use it. The DataWeave engine runs inside the Apex transaction's resource envelope: heap, CPU, and the standard Apex governor limits all apply. There is no external network call.

It IS:
- A way to author transformation scripts in DataWeave 2.0 syntax and execute them from Apex.
- Useful for many-field reshapes, nested-array flattening, format conversions (CSV ↔ JSON ↔ XML), and schema-mapping payloads from external systems.

It is NOT:
- A bridge to MuleSoft Anypoint at runtime (those are different products with different deployment models).
- A way to escape governor limits — it runs inside the Apex limits envelope.
- The right tool for transformations that are 5 lines of Apex; the registration and call overhead exceeds the benefit on trivial cases.

### Authoring and registering a script

A DataWeave script is `DataWeaveResource` metadata — a `.dwl` file in the `dw` folder (`api_meta.txt` 264 L52116), paired with a `.dwl-meta.xml` carrying the required `apiVersion` and optional `isGlobal` (L52129–52138) — and starts with a strict header that declares input/output MIME types:

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

The file name is what Apex passes to `createScript()`, which "loads a DataWeave 2.0 script from the .dwl metadata file that is deployed in an org" (262: `apexrefguide.txt` L155951); the platform also generates `DataWeaveScriptResource.<Name>`, usable instead of the string name (`apexdev.txt` 264 L26875–26877). `DataWeaveResource` has no cache-control setting — its fields are `apiVersion`, `isGlobal` and `isProtected` (`api_meta.txt` 264 L52127–52142). An org holds at most 50 scripts of up to 100,000 characters each (`apexdev.txt` 264 L26985–26986).

```xml
<!-- force-app/main/default/dw/Account_Mapping_DW.dwl-meta.xml — shape from apexdev.txt 264 L26931-26936 -->
<DataWeaveResource xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>68.0</apiVersion>
    <isGlobal>false</isGlobal>
</DataWeaveResource>
```

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

The corpus names three content types DataWeave in Apex does not support — `application/flatfile`, `application/xlsx`, `application/avro` (`apexdev.txt` 264 L26979–26982) — and its own samples use `application/csv`, `application/apex` (L26921–26922), `application/java` and `application/json` (262: `apexrefguide.txt` L155906–155907). Types this package's examples use:

- `application/json`
- `application/xml`
- `application/csv`
- `application/x-www-form-urlencoded`
- `application/dw` (DataWeave native — useful for chaining)
- `text/plain`

UNVERIFIED (2026-10-20): the corpus publishes no positive list of supported types; `application/x-www-form-urlencoded`, `application/dw`, `text/plain`, YAML and Parquet are neither confirmed nor excluded — test them in a scratch org before relying on them.

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
| Reusable across many Apex callers | DataWeave script (`DataWeaveResource` in `dw/`) | Single source of truth for the mapping spec |

---

## Recommended Workflow

1. Get a literal sample of the input and a literal sample of the desired output. Without samples, do not write a script.
2. Decide whether DataWeave is justified — apply the table above. If the Apex equivalent is under ~30 lines and read-once, write Apex.
3. Author the `.dwl` script in a scratch org's Developer Console or VS Code with the DataWeave extension. Iterate on the sample inputs until the output matches.
4. Save as `force-app/main/default/dw/<Name>_DW.dwl` with its `.dwl-meta.xml` (`apiVersion`, `isGlobal`) — `DataWeaveResource` metadata (`api_meta.txt` 264 L52116), not a static resource.
5. Wrap the call in an Apex service class so the resource name is in one place: `MyMappingService.transform(inputJson)`. The class should also handle the empty-input, malformed-input, and `System.DataWeaveScriptException` cases (`apexdev.txt` 264 L26887–26888).
6. Write Apex tests with literal payload strings as fixtures. Assert on the Apex-deserialized output, not on the raw JSON, so structural drift surfaces as a compile error rather than a string mismatch.
7. Add a check that script-load failures fall back gracefully. UNVERIFIED (2026-10-20): the corpus does not name the exception `createScript` throws for a missing script; prefer the generated `DataWeaveScriptResource.<Name>` class, whose referenced script the platform will not let anyone delete (`apexdev.txt` 264 L26877–26878).

---

## Review Checklist

- The `.dwl` header declares input MIME types matching every key in the Apex `execute` map.
- The `output` MIME type matches what the Apex caller expects (`getValueAsString()` for text formats).
- `default` clauses cover every optional field in the source payload — DataWeave's null-handling is strict.
- The Apex caller catches `System.DataWeaveScriptException`, the documented type for runtime script errors (`apexdev.txt` 264 L26887–26888); `Dataweave.ExecuteException` and `Dataweave.ScriptException` appear nowhere in the Apex guides.
- Tests cover at minimum: golden-path payload, empty input array, missing optional field, malformed input, and one large (>1MB) input to confirm heap behavior.
- The script lives in `dw/` as `DataWeaveResource` metadata, not under `staticresources/` (`api_meta.txt` 264 L52116).

---

## Salesforce-Specific Gotchas

- **Heap accounting** — DataWeave loads the entire input into memory before processing. A 5MB JSON input plus the parsed AST plus the output can exceed the 10 MB synchronous heap easily (25 MB async); DataWeave runs under "the same heap and CPU limits" as the calling Apex (`apexdev.txt` 264 L26823–26824). Those figures are a Winter '27 release-level change for every org, not an API-version gate (`apexdev.txt` 264 L19780; Summer '26 was 6 MB / 12 MB); profile under representative volumes before deploying to a synchronous path.
- **Not a static resource** — `DataWeaveResource` has no cache-control field (`api_meta.txt` 264 L52127–52142), so the older advice to set a static resource's cache control to `Public` does not apply. The org cap is 50 scripts (`apexdev.txt` 264 L26985).
- **Numeric type coercion** — DataWeave's `Number` is a single type; the Apex side gets back a Decimal that may have a different scale than the source JSON. Combine with `apex-decimal-arithmetic-precision` rounding when feeding currency fields.
- **Date/time formatting** — DataWeave's default ISO-8601 output is `2026-05-07T12:00:00Z`; if the receiving system expects `2026-05-07T12:00:00.000+0000`, format explicitly with `as String { format: "yyyy-MM-dd'T'HH:mm:ss.SSSZ" }`.
- **Tests need the deployed script** — `createScript` loads a `.dwl` already deployed to the org (262: `apexrefguide.txt` L155951); in a fresh CI scratch org, deploy `force-app/main/default/dw/` with the classes.
- **`System.DataWeaveScriptException` is the kitchen-sink** — runtime script errors are exposed to Apex as this one type (`apexdev.txt` 264 L26887–26888). Malformed input, missing required field, MIME-type mismatch, and division-by-zero in the script all surface as the same exception. Inspect `getMessage()` for the specific cause; do not assume a single failure mode.

---

## Output Artifacts

- `force-app/main/default/dw/<Name>_DW.dwl` — the script.
- `force-app/main/default/dw/<Name>_DW.dwl-meta.xml` — `DataWeaveResource` with `apiVersion` and `isGlobal`.
- `force-app/main/default/classes/<Name>MappingService.cls` — the Apex service that calls `DataWeave.Script.createScript` (or `new DataWeaveScriptResource.<Name>_DW()`) and exposes a typed result.
- `force-app/main/default/classes/<Name>MappingServiceTest.cls` — fixture-driven tests over golden-path and failure-mode payloads.

---

## Related Skills

- `apex/apex-json-serialization` — when the transformation is small enough that JSON-only Apex is the right answer.
- `apex/apex-decimal-arithmetic-precision` — for currency/quantity fields that come through DataWeave with surprising scale.
- `architect/mulesoft-anypoint-architecture` — when the transformation belongs *outside* Salesforce on an existing MuleSoft platform.
- `integration/middleware-integration-patterns` — for the "do this in MuleSoft vs do this in Apex" decision at the architecture level.
- `integration/bulk-api-2-patterns` — when the data volume rules Apex out entirely.
