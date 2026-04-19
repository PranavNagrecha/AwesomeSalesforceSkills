# Gotchas — Apex JSON Serialization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: suppressApexObjectNulls applies recursively to nested objects

**What happens:** `JSON.serialize(obj, true)` strips null fields not just from the top-level object but from every nested custom Apex object in the graph. If a nested object is expected to include null fields (e.g., for JSON schema compliance or to signal explicit absence), those nulls are silently dropped.

**When it occurs:** Any time you use `JSON.serialize(obj, true)` with nested wrapper classes that contain null fields.

**How to avoid:** If specific nested nulls must appear in the output, either set those fields to a sentinel value before serializing, or use `JSONGenerator` to write the exact structure you need.

---

## Gotcha 2: TypeException on type mismatch, not on extra fields

**What happens:** `JSON.deserialize` silently ignores JSON fields that have no matching Apex field. But if a JSON field *does* match an Apex field by name and the JSON type is wrong (e.g., JSON has `"amount": "99.95"` as a String, Apex expects `Decimal`), it throws `System.TypeException` — not a catchable `JSONException`.

**When it occurs:** Any time an external API changes a field's type, or sends error responses in a different schema than success responses (e.g., `amount` field absent or string in error case).

**How to avoid:** Always wrap `JSON.deserialize` on external data in try/catch for `System.TypeException`. For fields that vary in type across responses, use `Map<String, Object>` in the Apex wrapper to defer type resolution.

---

## Gotcha 3: Static and transient fields are excluded from JSON.serialize output

**What happens:** `JSON.serialize` only serializes public instance fields. Static fields, transient fields, and private fields (even those annotated `@TestVisible`) are excluded without error or warning.

**When it occurs:** When a developer places computed values or configuration in static fields expecting them to appear in the serialized output.

**How to avoid:** Move data that must appear in the JSON to public instance fields. If static data must be included, copy it to an instance field before serializing.

---

## Gotcha 4: JSON.deserializeUntyped returns Object, not Map — explicit cast required

**What happens:** `JSON.deserializeUntyped` is typed as returning `Object`. Accessing it directly causes a `NullPointerException` or compile error. The runtime type is `Map<String,Object>` for JSON objects or `List<Object>` for JSON arrays, but you must cast explicitly.

**When it occurs:** Any call to `JSON.deserializeUntyped` where the result is used without casting.

**How to avoid:** Always cast immediately: `Map<String,Object> root = (Map<String,Object>) JSON.deserializeUntyped(jsonString);`. For arrays: `List<Object> items = (List<Object>) JSON.deserializeUntyped(jsonArray);`.

---

## Gotcha 5: JSONParser cursor must be advanced before readValueAs

**What happens:** `JSONParser.readValueAs(Type.class)` deserializes starting at the **current** token position, not the start of the next token. Calling it before advancing the cursor with `nextToken()` deserializes from the wrong position and produces null or malformed objects.

**When it occurs:** When using `JSONParser` in a loop to process array elements, especially in combination with `nextToken()` calls to scan for a specific field name.

**How to avoid:** Advance the cursor to the start of the object/value token before calling `readValueAs`. Use `parser.nextToken()` and check `parser.getCurrentToken()` before deserializing.
