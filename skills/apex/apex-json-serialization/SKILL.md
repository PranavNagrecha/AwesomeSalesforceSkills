---
name: apex-json-serialization
description: "Use when serializing Apex objects to JSON strings or deserializing JSON responses into Apex types — especially for callout payloads, integration parsing, and controlling null field output. Trigger keywords: 'suppress null fields JSON Apex', 'deserialize JSON into Apex class', 'JSON parse unknown shape', 'TypeException JSON deserialize', 'JSONGenerator streaming'. NOT for REST endpoint response shaping (use apex-rest-services), NOT for Apex remote actions returning JSON to LWC."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance Efficiency
  - Reliability
triggers:
  - "suppress null fields in JSON serialization Apex callout payload"
  - "deserialize JSON response into Apex wrapper class TypeException thrown"
  - "parse unknown JSON shape dynamically Map String Object"
  - "JSONGenerator JSONParser streaming large payload apex"
  - "JSON.deserializeUntyped cast fails class cast exception"
tags:
  - apex-json
  - serialization
  - json-parser
  - callouts
  - integration
  - json-generator
inputs:
  - "Apex object graph to serialize, or raw JSON string to deserialize"
  - "Expected output type (typed Apex class or untyped Map)"
  - "Whether null fields should be suppressed in output"
outputs:
  - "Serialized JSON string for callout payload or storage"
  - "Hydrated Apex object or Map<String,Object> from JSON response"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-19
---

# Apex JSON Serialization

Use this skill when converting Apex objects to JSON strings for outbound callouts or parsing JSON responses from external APIs into Apex types. Covers the full JSON class family: `JSON.serialize/deserialize`, `JSON.deserializeUntyped`, `JSONGenerator`, and `JSONParser`.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the JSON shape is known at compile time (use typed deserialization) or dynamic (use `deserializeUntyped` or `JSONParser`).
- Check heap constraints: large JSON payloads count toward the 6 MB sync / 12 MB async heap limit.
- Identify whether null fields in the output will cause downstream parsing failures — if so, use `suppressApexObjectNulls`.

---

## Core Concepts

### JSON.serialize and suppressApexObjectNulls

`JSON.serialize(obj)` converts any Apex object to a JSON string. By default it includes all fields, including those with null values. Pass `true` as the second argument — `JSON.serialize(obj, true)` — to suppress null fields recursively across the entire object graph. LLMs routinely omit this argument, producing bloated payloads that fail strict JSON schema validation on the receiving end.

`suppressApexObjectNulls` applies recursively to nested custom objects: if an outer object contains a non-null nested object that has null fields, those inner nulls are also suppressed. Static fields are **not** serialized by `JSON.serialize` — only public instance fields.

### JSON.deserialize and TypeException

`JSON.deserialize(jsonString, Type.class)` deserializes into a typed Apex object. Extra JSON fields that don't match the Apex type are silently ignored. However, a type mismatch on a field that *does* exist (e.g., JSON has a String where Apex expects an Integer) throws `System.TypeException` at runtime — it is not silently tolerated. Always wrap external-data deserialization in try/catch for `TypeException`.

`JSON.deserializeStrict(jsonString, Type.class)` (API v45+) rejects JSON with extra fields — use when schema adherence must be enforced.

### JSON.deserializeUntyped

`JSON.deserializeUntyped(jsonString)` returns `Object`, which at runtime is `Map<String, Object>` for JSON objects, `List<Object>` for arrays, or a primitive. You must cast explicitly:

```apex
Map<String, Object> root = (Map<String, Object>) JSON.deserializeUntyped(response);
List<Object> items = (List<Object>) root.get('items');
```

Use this when the JSON shape is not known at compile time or varies between responses.

### JSONGenerator and JSONParser

`JSONGenerator` writes JSON token by token — use for very large payloads or precise control over field ordering. Pattern: `JSON.createGenerator(prettyPrint)` → `writeStartObject/writeFieldName/writeString` → `getAsString()`.

`JSONParser` reads JSON token by token using `nextToken()` returning `JSONToken` enum values. `parser.readValueAs(SomeClass.class)` deserializes from the current parser position — useful for large heterogeneous arrays without loading the full structure into heap.

---

## Common Patterns

### Outbound callout payload with null suppression

**When to use:** Sending a structured Apex object as a POST body to a REST API that rejects null fields.

**How it works:**

```apex
public class OrderPayload {
    public String orderId;
    public Decimal amount;
    public String couponCode; // may be null
}
OrderPayload p = new OrderPayload();
p.orderId = '12345';
p.amount = 99.95;
// couponCode stays null — omitted from output
String body = JSON.serialize(p, true); // {"orderId":"12345","amount":99.95}
```

**Why not the alternative:** `JSON.serialize(p)` without the flag produces `{"orderId":"12345","amount":99.95,"couponCode":null}`, which fails strict schema validation.

### Deserializing a typed response safely

**When to use:** Parsing a known-shape JSON response from an HTTP callout.

**How it works:**

```apex
HttpResponse res = http.send(req);
try {
    MyResponseWrapper wrapper = (MyResponseWrapper) JSON.deserialize(
        res.getBody(), MyResponseWrapper.class
    );
} catch (JSONException e) {
    // malformed JSON
} catch (System.TypeException e) {
    // shape mismatch — log and surface to caller
}
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| JSON shape matches Apex class | `JSON.deserialize(str, MyClass.class)` | Typed, safe, readable |
| JSON shape unknown or varies | `JSON.deserializeUntyped(str)` + cast | Flexible, no compile-time type needed |
| Need to suppress null fields | `JSON.serialize(obj, true)` | Omits nulls recursively |
| Very large payload or streaming write | `JSONGenerator` | Controls memory and token order |
| Large heterogeneous JSON array | `JSONParser` + `readValueAs()` | Avoids loading full structure into heap |
| Strict schema enforcement on input | `JSON.deserializeStrict()` | Rejects extra fields |

---

## Recommended Workflow

1. **Determine direction**: serialize (Apex → JSON) or deserialize (JSON → Apex).
2. **For serialization**: create or reuse an Apex wrapper; decide if null suppression is needed; use `JSON.serialize(obj, suppressNulls)`.
3. **For typed deserialization**: define Apex class matching JSON shape; wrap `JSON.deserialize()` in try/catch for `TypeException`.
4. **For untyped deserialization**: use `JSON.deserializeUntyped()` and navigate `Map<String,Object>` / `List<Object>` with explicit casts.
5. **For streaming large payloads**: use `JSONGenerator` for writes, `JSONParser` for reads.
6. **Validate heap impact**: estimate payload size; payloads over 1 MB in sync context warrant chunking or async processing.
7. **Test error paths**: include a test passing unexpected JSON to confirm `TypeException` is caught without leaking stack traces.

---

## Review Checklist

- [ ] `suppressApexObjectNulls` (`true`) passed where null fields must be omitted
- [ ] `JSON.deserialize` wrapped in try/catch for `TypeException`
- [ ] `deserializeUntyped` result cast explicitly before use
- [ ] Static fields not expected in serialized output
- [ ] Large payloads sized against heap limit (6 MB sync / 12 MB async)
- [ ] `JSON.deserializeStrict` used where extra fields must be rejected

---

## Salesforce-Specific Gotchas

1. **suppressApexObjectNulls is recursive** — it suppresses nulls in nested custom objects, not just the top level. If you expect a nested object to include null fields for schema reasons, this flag silently drops them.
2. **TypeException on type mismatch, NOT on extra fields** — `JSON.deserialize` silently ignores extra JSON fields, but throws `TypeException` if a matching field has the wrong data type. Developers expect the extra-field tolerance to extend to type mismatches too.
3. **Static fields excluded from serialization** — only public instance fields are serialized. Static, transient, and `@TestVisible`-only fields are excluded silently.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Apex wrapper class | Typed class matching JSON shape for `JSON.deserialize` |
| Serialized JSON string | Body string for HTTP callout or storage |
| `check_apex_json_serialization.py` | Validator confirming required method coverage |

---

## Related Skills

- apex-rest-services — for shaping REST endpoint responses and `@RestResource` handlers
- callouts-and-http-integrations — for HTTP callout mechanics, Named Credentials, and timeout handling
- apex-wrapper-class-patterns — for designing wrapper classes used in JSON serialization
