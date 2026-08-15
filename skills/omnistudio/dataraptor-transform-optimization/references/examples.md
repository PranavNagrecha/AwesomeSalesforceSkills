# Examples — DataRaptor Transform Optimization

Worked optimizations for Transform-type Omnistudio Data Mappers. Salesforce
renamed DataRaptor to **Omnistudio Data Mapper**; "DataRaptor Transform" and
"Data Mapper Transform" are the same artifact. Where behaviour differs between
the **managed package runtime** and the **standard runtime**, both are shown —
that difference is the single largest source of wrong advice in this area.

Apex and JSON below use names taken from Salesforce documentation. Anything not
verifiable against a Salesforce source is marked inline.

---

## Example 1: The one-line change that beats every mapping tweak

**Context:** an Apex service calls a Transform to reshape a payload before
handing it to a partner API. The org has moved to the standard runtime; the Apex
was written years earlier.

**Problem:** the Transform itself is already minimal — twelve direct mappings and
one formula. Every mapping-level optimization on the table is worth
milliseconds. The call site is worth more than all of them combined.

### Before — the managed-package call

```apex
// Works, and carries a managed-package dependency the org has otherwise removed.
public with sharing class PartnerPayloadService {

    public static String reshape(String inputJson) {
        Map<String, Object> input = (Map<String, Object>) JSON.deserializeUntyped(inputJson);

        Object result = vlocity_ins.DRGlobal.processObjectsJSON(
            'Partner_Payload_Transform',
            new List<Object>{ input }
        );

        return JSON.serialize(result);
    }
}
```

### After — the standard-runtime Connect API

Salesforce documents `ConnectApi.OmniDesignerConnect.executeDataMapper` as
replacing `vlocity_ins.DRGlobal.processObjectsJSON()`, states that it "removes
the dependency on the managed package", and claims "up to 60% better performance
for Data Mapper calls from an Apex class compared to the previous method".

```apex
public with sharing class PartnerPayloadService {

    private static final String BUNDLE = 'Partner_Payload_Transform';

    public static String reshape(String inputJson) {

        ConnectApi.DataMapperExecuteInputRepresentation apexInput =
            new ConnectApi.DataMapperExecuteInputRepresentation();

        // dataMapperInput is a List<String> of JSON documents, not a
        // List<Object> of deserialized maps. Passing one element runs the
        // Transform once; passing N runs it over N inputs in one call, which is
        // the whole bulkification story for an Apex caller.
        apexInput.dataMapperInput = new List<String>{ inputJson };
        apexInput.inputType       = 'JSON';

        ConnectApi.DataMapperExecuteOptionsRepresentation options =
            new ConnectApi.DataMapperExecuteOptionsRepresentation();
        // ignoreCache = true forces a fresh execution. Leave it false (or unset)
        // unless you are deliberately bypassing the cache — see
        // omnistudio/omnistudio-cache-strategies.
        options.ignoreCache = false;
        apexInput.options   = options;

        ConnectApi.DataMapperExecuteOutputRepresentation out =
            ConnectApi.OmniDesignerConnect.executeDataMapper(BUNDLE, apexInput);

        // response is a List<String>: one JSON document per input document.
        return out.response.isEmpty() ? null : out.response[0];
    }
}
```

**Why it works:**

- The managed-package namespace disappears from the call site, which is a
  prerequisite for ever uninstalling the package.
- Salesforce's own performance claim for the swap is larger than anything the
  mapping list can yield on an already-minimal Transform.
- `dataMapperInput` being a `List<String>` makes the bulk shape obvious: one call
  with N documents rather than N calls with one.

**Do this before profiling anything else.** It changes the baseline, so a
before-profile taken on the old call site is not comparable to anything measured
afterwards.

<!-- UNVERIFIED: DataMapperExecuteOptionsRepresentation is documented with
     locale, ignoreCache, and shouldSendLegacyResponse. Whether additional
     option properties exist in the current release, and the exact behaviour of
     shouldSendLegacyResponse, was not confirmed against a fetchable Salesforce
     page. Check the ConnectApi reference for your org's API version. -->

---

## Example 2: Merging lists — where the cheap mapping is the wrong one

**Context:** a Transform merges three input lists — current policies, pending
policies, and newly quoted policies — into one output list for a FlexCard.

**Problem:** the FlexCard renders them in an order that changes between
executions. QA cannot reproduce it, because at three rows per list it usually
looks stable.

### Wrong — three direct mappings into one output path

```text
Input JSON Path            Output JSON Path      Formula   Formula Result Path
─────────────────────────  ────────────────────  ────────  ───────────────────
currentPolicies            policies
pendingPolicies            policies
quotedPolicies             policies
```

This is the cheapest possible configuration: no expression is evaluated at all.
It is also unspecified. Salesforce's documentation for multiple input lists
mapping to a single output list is explicit that "the system does not guarantee
the order of the items in the output".

Unspecified is not the same as random. It is frequently stable in a sandbox and
frequently stable in production too — right up until the payload shape changes
and it is not. That is the worst failure profile a defect can have.

### Right — one formula, deterministic order

Salesforce's own remedy is to "use a formula to combine and filter the lists
instead of using direct mappings", and gives the shape:

```text
Formulas tab
────────────
Formula Name:    mergedPolicies
Formula:         LIST(currentPolicies, pendingPolicies, quotedPolicies)

Mappings tab
────────────
Input JSON Path   Output JSON Path   Formula          Formula Result Path
────────────────  ─────────────────  ───────────────  ───────────────────
                  policies           mergedPolicies   policies
```

And the output type has to be declared: "Make sure that the output data type for
your mapping is set to `List<Map>`."

**Why it works:** `LIST()` composes the three inputs in the order you wrote them,
so the output order is a property of the definition rather than of the runtime.

**The trade, stated plainly:** the formula costs an expression evaluation the
direct mappings did not. This is one of the few places in this skill where the
correct answer is the more expensive one. Take it anyway — a nondeterministic
list order is a bug that will be diagnosed three times before someone finds this
page.

---

## Example 3: The per-row Apex function, and the bulk replacement

**Context:** a Transform enriches each policy row with a risk band computed by an
Apex class, invoked from a formula through a custom function.

**Problem:** at 40 rows it is fine. At 400 rows the Integration Procedure fails
with `System.LimitException: Too many SOQL queries: 101` — from an artifact that,
by definition, "perform[s] intermediate data transformations without reading from
or writing to Salesforce". The Transform issued no queries. The function it
called did, once per row.

### Wrong — the per-row custom function

```apex
/**
 * Invoked once per row from a Transform formula.
 * Standard runtime: FUNCTION() + Callable.
 * Managed package:  Function Definition + VlocityOpenInterface.
 */
global with sharing class RiskBandFunction implements Callable {

    global Object call(String action, Map<String, Object> args) {
        Map<String, Object> input = (Map<String, Object>) args.get('input');
        String productCode = (String) input.get('productCode');

        // One query. Per row. The Transform runs this 400 times and the
        // transaction's SOQL allowance is 100.
        Risk_Band__mdt band = [
            SELECT Band__c FROM Risk_Band__mdt
            WHERE Product_Code__c = :productCode LIMIT 1
        ];

        return band.Band__c;
    }
}
```

Two independent defects, and only one of them is the query count. The second is
that `Risk_Band__mdt` is **custom metadata**, which
`Risk_Band__mdt.getAll()` reads without consuming a SOQL query at all. The
per-row SOQL was never necessary even at one row.

### Better — same shape, no query

```apex
global with sharing class RiskBandFunction implements Callable {

    // Loaded once per transaction. Custom metadata getAll() costs no SOQL query.
    // A plain static field with a lazy loader — NOT an Apex property whose
    // getter references itself, which recurses until the stack blows.
    private static Map<String, String> bandsByProduct;

    private static Map<String, String> bands() {
        if (bandsByProduct == null) {
            bandsByProduct = new Map<String, String>();
            for (Risk_Band__mdt b : Risk_Band__mdt.getAll().values()) {
                bandsByProduct.put(b.Product_Code__c, b.Band__c);
            }
        }
        return bandsByProduct;
    }

    global Object call(String action, Map<String, Object> args) {
        Map<String, Object> input = (Map<String, Object>) args.get('input');
        return bands().get((String) input.get('productCode'));
    }
}
```

The SOQL limit is gone. The per-row invocation overhead is not — 400 calls into
Apex still cost 400 crossings of the boundary.

### Best — one Apex step over the whole array

Where the enrichment is genuinely code-shaped, take it out of the Transform and
make it one step in the Integration Procedure that receives the whole array:

```apex
/**
 * One invocation for the whole payload. Called as a single Remote Action /
 * Apex step in the Integration Procedure, positioned BEFORE the Transform,
 * so the Transform receives rows that already carry riskBand and can map it
 * with a direct mapping — the cheapest evaluator there is.
 */
global with sharing class RiskBandEnricher implements Callable {

    global Object call(String action, Map<String, Object> args) {
        Map<String, Object> input = (Map<String, Object>) args.get('input');

        List<Object> rows = (List<Object>) input.get('policies');
        if (rows == null || rows.isEmpty()) {
            return input;
        }

        Map<String, String> bands = new Map<String, String>();
        for (Risk_Band__mdt b : Risk_Band__mdt.getAll().values()) {
            bands.put(b.Product_Code__c, b.Band__c);
        }

        for (Object o : rows) {
            Map<String, Object> row = (Map<String, Object>) o;
            row.put('riskBand', bands.get((String) row.get('productCode')));
        }

        return input;
    }
}
```

**Why it works:** one boundary crossing instead of N, one metadata load instead
of N, and the Transform is reduced to a direct mapping of a field that is already
present. The Transform gets faster because it stopped doing the expensive thing,
not because its mappings were tuned.

**When not to do this:** if the enrichment is one arithmetic expression, a
formula in the Transform is simpler and the Apex step is over-engineering. The
threshold is whether the logic needs code — dynamic sObject access, regex,
crypto, an external lookup — not whether it *can* be written in code.

---

## Example 4: Reading the chain without writing to it

**Context:** an org with roughly 300 Data Mappers. You need to find the
Transform chains worth auditing.

**Problem:** the obvious approach is to query the standard objects, and the
obvious next step — "let's just fix the mappings with a script" — is the one the
documentation forbids.

The Object Reference on `OmniDataTransform` and `OmniDataTransformItem`
(available since Spring '21 / API 51.0) states:

> "For internal use only. This object and associated records are only for
> internal use. Don't perform any create, edit, or delete operations on this
> object."
>
> "Modifying or deleting this object's records may result in errors with your
> implementation."

**Reading them to find work is a different activity from writing them**, and the
warning is about create, edit, and delete. A read-only census is a reasonable use
of a few minutes; a bulk rewrite is not, at any level of confidence.

```apex
/**
 * Read-only census of Transform-type Data Mappers, ordered by mapping count.
 * Finds the artifacts worth profiling. Performs NO DML against the Omnistudio
 * standard objects, deliberately and permanently.
 */
public with sharing class DataMapperCensus {

    public class Row {
        public String name;
        public Integer itemCount;
    }

    public static List<Row> transformsByMappingCount() {
        Map<Id, Row> byId = new Map<Id, Row>();

        // Field names below are not quoted from Salesforce documentation —
        // confirm them against your org's describe before relying on this.
        for (AggregateResult ar : [
                SELECT OmniDataTransformId dtId, COUNT(Id) total
                FROM OmniDataTransformItem
                WITH USER_MODE
                GROUP BY OmniDataTransformId
                ORDER BY COUNT(Id) DESC
                LIMIT 50]) {
            Row r = new Row();
            r.itemCount = Integer.valueOf(ar.get('total'));
            byId.put((Id) ar.get('dtId'), r);
        }

        return byId.values();
    }
}
```

<!-- UNVERIFIED: the field API names on OmniDataTransform and
     OmniDataTransformItem (including OmniDataTransformId, and any Type,
     InputType, OutputType or version fields) could not be read from the Object
     Reference — the pages render the internal-use warning but not the field
     table to a plain fetch. Run a describe against the target org before using
     the query above; treat the shape as illustrative, not authoritative. -->

**What to do with the census:** mapping count is a proxy for audit value, not for
slowness. The Transforms worth profiling are the ones with many mappings *and* a
place in a hot Integration Procedure. Combine the census with the IP's own timing
output before spending an afternoon on the wrong artifact.

---

## Example 5: Projecting upstream instead of tuning downstream

**Context:** an Integration Procedure extracts Accounts with a large field set,
runs three chained Transforms, and returns 14 fields to a FlexCard.

**Problem:** every one of the three Transforms materializes a full copy of the
wide payload. The Integration Procedure fails on heap at around 900 accounts, and
every mapping-level optimization attempted so far has moved the failure point by
a few dozen rows.

**Wrong instinct:** optimize the Transforms. They are not the problem — they are
where the problem becomes visible.

**Right:** narrow the payload at the Extract, before anything materializes it.

```text
BEFORE
  Extract  ── 180 fields × 900 rows ─┐
  Transform 1  (full copy) ──────────┤
  Transform 2  (full copy) ──────────┤  three wide copies live at peak
  Transform 3  (full copy) ──────────┘
  Output   ── 14 fields

AFTER
  Extract  ── 16 fields × 900 rows ──┐
  Transform 1+2 (merged, one copy) ──┤  one narrow copy, one merge
  Transform 3  (one copy) ───────────┘
  Output   ── 14 fields
```

Two changes, in this order:

1. **Project.** List the fields the output actually contains, add any field a
   formula reads, and cut the Extract to that set. Roughly a tenfold reduction in
   every copy.
2. **Merge.** Transforms 1 and 2 had no consumer between them, so they are one
   Transform with more mappings. That removes an entire materialization.

**Why it works:** heap failures respond to fewer and smaller copies. Nothing in
the mapping list addresses either.

**The check that tells you which fix you need:** read the exception. A
`LimitException` naming heap wants this treatment. One naming CPU time wants the
opposite — fewer and cheaper expressions — and applying the heap remedy to a CPU
problem produces a merged Transform that is exactly as slow as the two it
replaced.

---

## Anti-Pattern: profiling in the designer preview

**What people do:** run the Transform in the designer's preview against a
three-row sample, see it complete instantly, and conclude the Transform is not
the bottleneck.

**What goes wrong:** three rows measure the fixed overhead and nothing else. The
costs that matter here are all per-row or per-copy — expression evaluation scales
with rows × mappings, materialization scales with rows × fields, and a per-row
Apex function scales with rows and consumes a limit that has nothing to do with
elapsed time. None of them is visible at three rows.

Worse, the preview runs outside the Integration Procedure, so it does not show
the thing that most often turns a fine Transform into a failing one: that it is
the last step in a transaction which had already spent 9,000 ms of its 10,000 ms
CPU allowance.

**Correct approach:** profile the enclosing Integration Procedure at production
row and field counts, from two sources at once — the IP's own timing output for
the Transform's share, and an Apex debug log for the transaction's CPU and heap
totals. The first tells you whether this artifact is worth optimizing; the second
tells you whether the transaction has room for it to matter.

**Detection hint:** any performance conclusion about a Transform that cites the
designer preview, or any row count in a benchmark that is smaller than the
production row count.
