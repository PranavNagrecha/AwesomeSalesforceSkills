# Gotchas — DataWeave for Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `Private` static-resource cache control re-parses every execution

**What happens:** A team registers their `.dwl` script with cache control set to `Private`. Each `Dataweave.Script.createScript('Name')` call re-parses the script body — the per-call CPU cost spikes. Performance tests pass at 10 calls per transaction; production fails at 50.

**When it occurs:** The IDE / CLI default is sometimes `Private`. Teams used to writing `Private` for personal data don't realize the cache flag here is about the script artifact, not the data flowing through it.

**How to avoid:** Set `cacheControl=Public` on the static resource's `.resource-meta.xml`. The script source is metadata, not user data — `Public` is the correct choice. A simple validation rule: if you see `Private` on a `.dwl` resource, it's almost certainly wrong.

---

## Gotcha 2: Heap consumed before script execution starts

**What happens:** A Queueable that processes a 8MB JSON payload via DataWeave hits `System.LimitException: Apex heap size too large` even though the payload itself fits comfortably in 12MB. The error happens *before* the transformation produces output.

**When it occurs:** DataWeave loads the entire input into memory and parses it into its internal AST before transformation begins. For JSON, the parsed AST can be 2–4× the source size. The output is also held in memory until `getValueAsString()` returns.

**How to avoid:** Treat the heap budget as `(input_size × 4) + output_size`. For payloads >2MB, split the work upstream (paginate the source) or move the transformation off-platform. DataWeave is not a streaming engine in the Apex runtime.

---

## Gotcha 3: `Dataweave.ExecuteException` collapses many failure modes

**What happens:** Production logs show `Dataweave.ExecuteException` with message `An error occurred during script execution`. The actual cause varies — malformed JSON, missing required field, numeric coercion failure, MIME-type mismatch — but the exception type is the same.

**When it occurs:** Any runtime failure inside the script execution. Apex code that catches `Dataweave.ExecuteException` and rethrows as a generic `IngestException` loses the diagnostic detail.

**How to avoid:** Always log `e.getMessage()` and the *first 500 characters* of the input payload before rethrowing. The DataWeave message is usually specific enough to debug from once you see it; without the input snippet you cannot reproduce.

---

## Gotcha 4: `as Number` coercion on currency fields shifts scale

**What happens:** A DataWeave script transforms `"revenue":"1000000.50"` from JSON via `revenue: row.revenue as Number`. The Apex side gets back a Decimal at scale 1 (`1000000.5`), not scale 2 as a Currency field expects. A subsequent `Decimal.equals()` comparison or `setScale(0)` rounds in unexpected directions.

**When it occurs:** Whenever the source string has fewer trailing zeros than the target field's scale. JSON numbers don't carry scale; DataWeave's `as Number` keeps the source's natural representation.

**How to avoid:** Round explicitly on the Apex side after the DataWeave call: `acct.AnnualRevenue = ((Decimal) parsed.revenue).setScale(2, System.RoundingMode.HALF_EVEN);`. Or format in DataWeave: `revenue: row.revenue as Number as String { format: "0.00" } as Number`. See `apex/apex-decimal-arithmetic-precision`.

---

## Gotcha 5: XML namespaces silently drop without explicit declaration

**What happens:** A SOAP payload uses namespace prefixes (`<soap:Envelope xmlns:soap="...">`). The DataWeave script written without `ns soap http://...` declarations sees no nodes — the script returns `[]` without an error.

**When it occurs:** Any time the source XML uses namespace prefixes other than the default. Many enterprise systems do; many DataWeave examples on the public internet don't.

**How to avoid:** Always inspect the raw XML for `xmlns:` attributes. Declare every namespace at the top of the `.dwl`:

```dwl
%dw 2.0
input payload application/xml
output application/json
ns soap http://schemas.xmlsoap.org/soap/envelope/
ns biz http://example.com/billing
---
payload.soap#Envelope.soap#Body.biz#Invoices.*biz#invoice map (inv) -> {...}
```

If the script returns empty results for a payload that obviously contains data, namespaces are the first thing to check.

---

## Gotcha 6: Apex test execution requires the static resource to exist in the test context

**What happens:** A Jest-style mocking expectation: a developer writes the Apex test, mocks the input, and expects the transformation to run. The test fails with `Dataweave.ScriptException: Script not found: Name_DW` — the static resource exists in the org but not in the test scratch sandbox.

**When it occurs:** When the Apex test runs in a CI scratch org without seed data, or when `@TestSetup` doesn't deploy the static resource alongside.

**How to avoid:** Static resources that ship with code go in `force-app/main/default/staticresources/` and are deployed by the same CLI command that deploys the Apex. Verify the resource is in `package.xml` if using metadata format. For data-loaded test setups, treat the static resource as part of the deployable artifact, not as test data.
