# LLM Anti-Patterns — DataRaptor Transform Optimization

Mistakes AI assistants make when asked to speed up an Omnistudio Data Mapper
Transform. One cause dominates: OmniStudio spent most of its life as the Vlocity
managed package, so the training distribution is overwhelmingly managed-package
material, and a model asked about "OmniStudio" will confidently produce advice for
a runtime the org may have left years ago.

---

## Anti-Pattern 1: Managed-package Apex on a standard-runtime org

**What the LLM generates:**

```apex
Object result = vlocity_ins.DRGlobal.processObjectsJSON(
    'My_Transform', new List<Object>{ input });
```

or the `vlocity_cmt.` / `vlocity_ps.` variant, depending on which industry
namespace the training data happened to favour.

**Why it happens:** this is the API that existed for a decade and appears in
essentially every blog post, Stack Exchange answer, and tutorial about calling a
DataRaptor from Apex. Nothing in a request like "call my Transform from Apex"
signals which runtime the org is on.

**Correct pattern:** on the standard runtime,
`ConnectApi.OmniDesignerConnect.executeDataMapper(bundleName, apexInput)`.
Salesforce documents it as replacing `vlocity_ins.DRGlobal.processObjectsJSON()`,
states that "This Connect API removes the dependency on the managed package", and
claims "up to 60% better performance for Data Mapper calls from an Apex class
compared to the previous method".

The right move is to *ask which runtime* before answering, and to give both if the
answer is unknown. Guessing produces code that either does not compile or carries
a managed-package dependency the org is trying to remove.

**Detection hint:** any `vlocity_*` namespace in a recommendation, with no
accompanying question about the runtime.

---

## Anti-Pattern 2: Inventing a "bulk mode" toggle

**What the LLM generates:** advice to "enable bulk mode on the Transform" or "set
the Transform to process arrays rather than row-by-row", often with a confident
claim about the speed-up.

**Why it happens:** batch and bulk settings are real elsewhere in the Data Mapper
family — Batch Size is documented for **Load**, as a record count — and the four
types share a designer, a name, and most of their documentation. Generalising a
setting from one type to another is a small, plausible step.

**Correct pattern:** a Transform "perform[s] intermediate data transformations
without reading from or writing to Salesforce", so it has no records to batch. Its
costs are expression evaluation and materialization. The bulk question that does
exist is at the *caller*: on the standard runtime
`ConnectApi.DataMapperExecuteInputRepresentation.dataMapperInput` is a
`List<String>`, so one call with N documents beats N calls with one.

If you are unsure whether a designer setting exists in the current release, say
so and point at the designer. A named setting that does not exist sends someone
looking for a checkbox for an afternoon.

**Detection hint:** a specific speed-up multiplier attached to a setting whose
exact name and location the answer cannot state.

---

## Anti-Pattern 3: Fabricated performance multipliers

**What the LLM generates:** "row-by-row processing is 5–10× slower than bulk",
"formulas are roughly 20× cheaper than Apex expressions", "merging transforms
typically halves execution time".

**Why it happens:** performance advice reads as more useful with a number
attached, and numbers of this shape are pervasive in engineering writing. The
model is completing a genre, not reporting a measurement.

**Correct pattern:** the only performance figure in this area that traces to a
Salesforce source is the Connect API claim of "up to 60% better performance for
Data Mapper calls from an Apex class compared to the previous method". Everything
else has to come from the reader's own before/after profile — which is why the
workflow makes profiling step 2 and re-profiling step 7.

Directional guidance without a number is honest and still actionable: a direct
mapping is cheaper than a formula, which is cheaper than a call into Apex.

**Detection hint:** any multiplier or percentage with no source, especially one
ending in "×" attached to a comparison the reader cannot reproduce.

---

## Anti-Pattern 4: Three direct mappings to merge three lists

**What the LLM generates:**

```text
currentPolicies  → policies
pendingPolicies  → policies
quotedPolicies   → policies
```

**Why it happens:** it is the most direct expression of "merge these lists", it is
the cheapest configuration available (no expression is evaluated), and it appears
to work. A performance-focused prompt actively selects for it, because it *is* the
faster option.

**Correct pattern:** Salesforce documents that when several input lists map to one
output list, "the system does not guarantee the order of the items in the output",
and recommends: "use a formula to combine and filter the lists instead of using
direct mappings" — `LIST(inputList1, inputList2, inputListNew)` — with the output
data type set to `List<Map>`.

This is the case where the optimization advice is *wrong*: the formula is more
expensive and correct, the direct mapping is cheaper and nondeterministic. An
answer that recommends the direct mapping on performance grounds has optimized
into a bug.

**Detection hint:** two or more mapping rows sharing an Output JSON Path, in an
answer framed as a performance improvement.

---

## Anti-Pattern 5: A custom function with SOQL inside it

**What the LLM generates:**

```apex
global with sharing class RiskBandFunction implements Callable {
    global Object call(String action, Map<String, Object> args) {
        Map<String, Object> input = (Map<String, Object>) args.get('input');
        Risk_Band__mdt band = [SELECT Band__c FROM Risk_Band__mdt
                               WHERE Product_Code__c = :(String) input.get('productCode')
                               LIMIT 1];
        return band.Band__c;
    }
}
```

**Why it happens:** the function receives one row, so it is written to handle one
row, and a single query with `LIMIT 1` looks maximally efficient at that scope.
Bulkification does not apply at the scope the function can see.

**Correct pattern:** the function is invoked once per row, so a query inside it is
N queries against a limit of 100 — thrown from an artifact documented as not
reading from Salesforce, which makes the exception baffling.

Two fixes, and the second is usually right. Custom metadata read through
`Risk_Band__mdt.getAll()` costs no SOQL query at all, so the query was never
needed. Better still, move the enrichment out of the Transform entirely into one
Apex step over the whole array, so the Transform maps a field that is already
present.

**Detection hint:** SOQL inside a class implementing `Callable` (standard runtime)
or `VlocityOpenInterface` (managed package) that a Transform formula invokes.

---

## Anti-Pattern 6: Optimizing the Transform when the transaction is the problem

**What the LLM generates:** a detailed, well-organised mapping-level optimization
plan for a Transform that is the last step in an Integration Procedure which had
already spent 9,200 ms of its 10,000 ms CPU allowance.

**Why it happens:** the prompt names the Transform as the slow thing, because the
Transform is where the exception was thrown. The model optimizes the artifact it
was given. Asking whether the artifact is the right one is not a shape most
completions take.

**Correct pattern:** a Transform inside a synchronous Integration Procedure spends
the calling transaction's budget — 10,000 ms CPU and 6 MB heap synchronously,
60,000 ms and 12 MB asynchronously. If the transaction is nearly exhausted before
the Transform starts, no mapping change will help, and the useful answers are
different in kind: move the IP to an asynchronous shape, split the transaction, or
page the payload.

Ask for the transaction total before proposing mapping changes.

**Detection hint:** an optimization plan with no question about what ran before
the Transform, or one whose first step is not "profile".

---

## Anti-Pattern 7: Bulk-fixing mappings by DML against the standard objects

**What the LLM generates:** an Apex script or a data-loader plan that updates
`OmniDataTransformItem` records across many Data Mappers, to apply a mapping
change consistently.

**Why it happens:** the objects are queryable, the change is mechanical, and
scripting a mechanical change across 300 artifacts is exactly the kind of leverage
a model is good at proposing. The prohibition is a sentence on a documentation
page rather than a property of the API.

**Correct pattern:** the Object Reference says of `OmniDataTransform` and
`OmniDataTransformItem`: "For internal use only. This object and associated
records are only for internal use. Don't perform any create, edit, or delete
operations on this object", and "Modifying or deleting this object's records may
result in errors with your implementation."

Reading them to *find* work is a different activity and is fine. Changes go
through the designer or the Metadata API.

**Detection hint:** `insert`, `update`, `upsert`, or `delete` against an `Omni*`
standard object anywhere in a recommendation.

---

## Anti-Pattern 8: Claiming a JavaScript evaluator exists inside a Transform

**What the LLM generates:** an evaluator cost table listing "formula", "Apex", and
"JavaScript" as the three ways a Transform can compute a value, usually with
JavaScript characterised as slow and hard to test.

**Why it happens:** OmniStudio does involve custom JavaScript in other places —
FlexCards and OmniScript custom LWC territory — and a cost table wants a third
row. The table is a genre with a shape, and the shape gets filled.

**Correct pattern:** the documented extension point for custom logic in a Data
Mapper is Apex: `FUNCTION()` plus `Callable` on the standard runtime, a Function
Definition plus `VlocityOpenInterface` on the managed package. State the
evaluators you can source — direct mapping, Transform Map Values, formula, custom
function into Apex — and stop there.

Note the shape of the correction. The claim to avoid is "a JavaScript evaluator
exists"; the claim *not* to make in its place is "OmniStudio does not support
JavaScript", which is false in other contexts. Absence from a documented list is
not evidence of absence from the product.

**Detection hint:** a JavaScript row in a Data Mapper evaluator table, or any
performance claim about JavaScript inside a Transform.

---

## Anti-Pattern 9: Merging every adjacent Transform on principle

**What the LLM generates:** "collapse all chained Transforms into one" as a
blanket recommendation, applied to a chain whose steps are separately reused.

**Why it happens:** merging removes a materialization, which is a genuine and
explicable win, and blanket rules are easier to state than conditional ones.

**Correct pattern:** merging is right when two Transforms are adjacent and have no
consumer between them and their logic composes cleanly. It is wrong when a step is
reused by another Integration Procedure — merging then forces a duplicate — and it
is wrong when the merged artifact needs a comment explaining its two halves, which
trades a measurable performance win for an unmeasurable permanent maintenance
cost.

It is also the wrong fix entirely when the failure is CPU rather than heap: fewer
materializations do not reduce expression count, so the merged Transform is
exactly as slow as the two it replaced.

**Detection hint:** a merge recommendation with no question about reuse, and none
about whether the failure was heap or CPU.

---

## Anti-Pattern 10: Benchmarking in the designer preview

**What the LLM generates:** "run it in the preview to confirm the improvement",
offered as the verification step of an optimization plan.

**Why it happens:** the preview is the obvious place to run a Data Mapper, it
gives immediate feedback, and it is the tool a reader has open.

**Correct pattern:** the preview runs a small sample outside the Integration
Procedure. Every cost that matters here scales with rows, so at preview scale they
all round to fixed overhead — and the preview cannot show the most common cause of
a Transform failure, which is that the enclosing transaction was nearly out of CPU
before the Transform started.

Verification means re-profiling the Integration Procedure at production row and
field counts, reading the IP's timing output and an Apex debug log together, and
attributing each delta to a specific change.

**Detection hint:** a verification step that does not mention production row
counts, or one that measures the artifact rather than the transaction.
