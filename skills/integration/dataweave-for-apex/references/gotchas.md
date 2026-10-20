# Gotchas — DataWeave for Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The script is `DataWeaveResource` metadata, not a static resource

**What happens:** A team stores the `.dwl` under `staticresources/` with a `.resource-meta.xml` and tunes its cache control. `createScript('Name')` does not read static resources: it "loads a DataWeave 2.0 script from the .dwl metadata file that is deployed in an org" (262: `apexrefguide.txt` L155951), and DataWeave scripts are created "as metadata" (`apexdev.txt` 264 L26822–26823).

**When it occurs:** When guidance written for static resources — including this package's earlier advice to set `cacheControl=Public` — is applied to DataWeave. `DataWeaveResource` has no cache-control field: its fields are `apiVersion` (required), `isGlobal` and `isProtected` (`api_meta.txt` 264 L52127–52142).

**How to avoid:** Put `<Name>.dwl` and `<Name>.dwl-meta.xml` in `force-app/main/default/dw/` — the `.dwl` suffix and `dw` folder are the type's location (`api_meta.txt` 264 L52116). Set `isGlobal` to `true` only when another namespace must call the generated class (L52138). Budget against the org cap of 50 scripts and 100,000 characters per script (`apexdev.txt` 264 L26985–26986).

---

## Gotcha 2: Heap consumed before script execution starts

**What happens:** A Queueable that processes a 8MB JSON payload via DataWeave hits `System.LimitException: Apex heap size too large` even though the payload itself fits comfortably in the 25 MB asynchronous heap (Winter '27 release, `apexdev.txt` 264 L19780; 12 MB through Summer '26). The error happens *before* the transformation produces output.

**When it occurs:** DataWeave loads the entire input into memory and parses it into its internal AST before transformation begins. For JSON, the parsed AST can be 2–4× the source size (UNVERIFIED (2026-10-19): the multiplier is not stated in `apexdev.txt` 264, which says only that DataWeave enforces the same heap and CPU limits as Apex, L26823–26824 — measure with `Limits.getHeapSize()`). The output is also held in memory until `getValueAsString()` returns.

**How to avoid:** Treat the heap budget as `(input_size × 4) + output_size`. For payloads >2MB, split the work upstream (paginate the source) or move the transformation off-platform. DataWeave is not a streaming engine in the Apex runtime.

---

## Gotcha 3: `System.DataWeaveScriptException` collapses many failure modes

**What happens:** Production logs show `System.DataWeaveScriptException` — the one type that "runtime script exceptions that occur within DataWeave are exposed to Apex with" (`apexdev.txt` 264 L26887–26888) — with a generic message (illustrative; UNVERIFIED (2026-10-20): the exact message text is not documented). The actual cause varies — malformed JSON, missing required field, numeric coercion failure, MIME-type mismatch — but the exception type is the same.

**When it occurs:** Any runtime failure inside the script execution. Apex code that catches `DataWeaveScriptException` and rethrows as a generic `IngestException` loses the diagnostic detail.

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

## Gotcha 6: Apex tests need the `dw/` script deployed with the class

**What happens:** A developer writes the Apex test, mocks the input, and expects the transformation to run. The test fails because the script exists in the developer's org but was never deployed to the CI scratch org. UNVERIFIED (2026-10-20): the exception type and message `createScript` raises for a missing script are not documented in the corpus.

**When it occurs:** When the CI deploy omits `force-app/main/default/dw/`, or when someone expects `@TestSetup` to create the script — it cannot, because `createScript` loads only a `.dwl` already deployed to the org as metadata (262: `apexrefguide.txt` L155951).

**How to avoid:** Keep `dw/` in the same source tree and deployment as the Apex, and list `DataWeaveResource` in `package.xml` when deploying in metadata format (sample at `api_meta.txt` 264 L52175–52184). Calling the generated `DataWeaveScriptResource.<Name>` class instead of `createScript('<Name>')` makes the dependency explicit, and a script referenced that way "can't be deleted" (`apexdev.txt` 264 L26877–26878).
