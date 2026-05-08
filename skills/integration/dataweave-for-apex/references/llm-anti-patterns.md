# LLM Anti-Patterns — DataWeave for Apex

Common mistakes AI coding assistants make when generating or advising on DataWeave for Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing DataWeave-for-Apex with MuleSoft Anypoint DataWeave

**What the LLM generates:** Apex examples that reference MuleSoft connectors, Anypoint Studio, or `mule:flow` constructs and then suggest the script "runs in Salesforce." The two products share a transformation language but are different runtimes.

**Why it happens:** Most public DataWeave material is MuleSoft-centric; the Apex variant is much newer (Summer '24 GA). LLMs blend the two.

**Correct pattern:**

In Apex, you only need a `.dwl` static resource and `Dataweave.Script`:

```apex
Dataweave.Script script = Dataweave.Script.createScript('My_DW');
Dataweave.Result result = script.execute(new Map<String, Object>{ 'payload' => input });
String output = result.getValueAsString();
```

No MuleSoft license. No Anypoint platform. No external runtime.

**Detection hint:** References to `flow:`, `dw:`, `mule:`, `Anypoint`, or "deploy to MuleSoft" in an Apex context are red flags.

---

## Anti-Pattern 2: Writing the script inline in Apex as a String

**What the LLM generates:** Code that constructs the DataWeave script as an Apex String and tries to execute it without registering a static resource:

```apex
// WRONG — there is no Dataweave.Script.fromString() API
Dataweave.Script script = Dataweave.Script.fromString('%dw 2.0...');
```

**Why it happens:** Other transformation libraries (e.g. Mustache, Handlebars) often allow inline script strings. LLMs assume DataWeave-for-Apex follows the same pattern.

**Correct pattern:**

The script must be registered as a static resource with content type `application/dw`. The Apex API exposes only the `createScript(String resourceName)` factory. Inline scripts are not supported.

**Detection hint:** Look for `fromString`, `compile`, or any call that takes the script body directly. If the example doesn't reference a static resource name, it's wrong.

---

## Anti-Pattern 3: Omitting the `default` clause and assuming DataWeave handles missing fields gracefully

**What the LLM generates:** A script like `{ revenue: payload.financials.revenue }` that throws at runtime when `financials` is null in some input rows.

**Why it happens:** LLMs treat DataWeave's path-navigation syntax as similar to JavaScript optional chaining (`?.`). DataWeave is stricter — missing intermediate keys produce nulls, but `as Number` on a null throws.

**Correct pattern:**

```dwl
{
    revenue: (payload.financials.revenue default 0) as Number
}
```

Always pair an `as <Type>` coercion with a `default` value when the source path is optional. For deeply nested paths, `default null` first, then coerce only if non-null.

**Detection hint:** Any `as Number`, `as Date`, or `as Boolean` without a preceding `default` is brittle to missing data.

---

## Anti-Pattern 4: Calling `createScript` inside a loop

**What the LLM generates:**

```apex
// WRONG — script-load overhead per iteration
for (Account a : accounts) {
    Dataweave.Script s = Dataweave.Script.createScript('Account_DW');
    Dataweave.Result r = s.execute(new Map<String, Object>{ 'payload' => JSON.serialize(a) });
    // ...
}
```

**Why it happens:** Pattern-matched from REST-call examples where each iteration genuinely needs a fresh client. DataWeave scripts are stateless and reusable.

**Correct pattern:**

Hoist `createScript` above the loop and, ideally, batch the input into one composite payload:

```apex
Dataweave.Script s = Dataweave.Script.createScript('Account_DW');
Dataweave.Result r = s.execute(new Map<String, Object>{
    'payload' => JSON.serialize(accounts)
});
List<Map<String,Object>> mapped = (List<Map<String,Object>>)
    JSON.deserializeUntyped(r.getValueAsString());
```

**Detection hint:** Grep for `createScript` inside any `for` loop body. Always a code smell.

---

## Anti-Pattern 5: Assuming any MIME type DataWeave supports works in Apex

**What the LLM generates:** Apex examples that declare `output application/yaml` or `input application/avro` because those types exist in MuleSoft DataWeave.

**Why it happens:** LLMs reach for the broader DataWeave 2.0 type catalog without checking which MIME types Salesforce's Apex implementation supports.

**Correct pattern:**

Stick to the supported set in Apex: `application/json`, `application/xml`, `application/csv`, `application/x-www-form-urlencoded`, `application/dw`, `text/plain`. For YAML/Avro/Parquet inputs, convert upstream or use a different tool. Confirm against the current Apex Reference for `Dataweave.Script` before adopting an exotic type.

**Detection hint:** Any `input` or `output` MIME type outside the six listed above warrants a verification check against the Apex Reference Guide.
