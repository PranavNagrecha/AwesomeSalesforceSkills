# Gotchas — DataRaptor Transform Optimization

Failure modes specific to Transform-type Omnistudio Data Mappers. Grounded in the
Apex Developer Guide, the Object Reference for the Salesforce Platform, the
Industries Common Resources Developer Guide, and Salesforce Help's Omnistudio
Data Mapper documentation (Summer '26, API 67.0).

Two structural facts underlie most of this list: a Transform issues no SOQL and
no DML of its own, and it spends the *calling* transaction's limits. So almost
every Transform failure is a limit consumed somewhere else and attributed here.

---

## Gotcha 1: You Are Probably Reading Documentation for the Other Runtime

**What happens:** an Apex snippet from a blog, from a colleague, or from a model
does not compile — or compiles and fails at runtime with a namespace error. The
code is correct; it is correct for a runtime the org is not on.

Omnistudio has two: the **managed package runtime** (the Vlocity lineage, a
custom data model, `vlocity_*` namespaces) and the **standard runtime**
(Salesforce standard objects, standard APIs). Salesforce Help carries two
parallel documentation trees — "Omnistudio Data Mappers (Managed Package)" and
"Omnistudio Data Mappers" — and migrating between them is a documented
three-phase project, now assisted by the Omnistudio Migration Assistant.

The differences that bite in this skill:

| | Managed package | Standard |
|---|---|---|
| Apex invocation | `vlocity_ins.DRGlobal.processObjectsJSON()` | `ConnectApi.OmniDesignerConnect.executeDataMapper()` |
| Apex from a formula | Function Definition + `VlocityOpenInterface` | `FUNCTION()` + `Callable` |
| Deployment | DataPacks | Metadata API, after enabling the Omnistudio Metadata setting |

**When it occurs:** constantly, because the managed package existed for years
longer and dominates every search result and every training corpus.

**How to avoid:** establish the runtime before reading anything, and check the
tree a page belongs to before trusting it. On Salesforce Help the managed-package
pages carry "(Managed Package)" in the title; the URL id prefixes differ too
(`sf.os_…` versus `xcloud.os_…`), though that is a weaker signal than the title.

---

## Gotcha 2: The Rename Fragments Every Search

**What happens:** searching "DataRaptor Transform" returns a mixture of current
documentation, superseded documentation, and community posts spanning both
runtimes, with no reliable way to tell them apart from the snippet.

Salesforce renamed DataRaptor to **Omnistudio Data Mapper**. The four types keep
their names — the Industries Common Resources Developer Guide lists
"Extract—Read data from Salesforce objects and JSON output or XML with field
mappings", "Turbo Extract—Read data from a single Salesforce object type, with
support for fields from related objects", "Transform—Perform intermediate data
transformations without reading from or writing to Salesforce", and "Load—Create
and update Salesforce data from JSON or XML input".

**When it occurs:** on every search, indefinitely. The old name is what
practitioners type and what a decade of material uses.

**How to avoid:** search both names deliberately and prefer the newer term when
reading Salesforce sources. When writing anything down for the team, name the
artifact and the runtime together — "a Transform Data Mapper on the standard
runtime" is unambiguous in a way that "a DataRaptor" is not.

---

## Gotcha 3: Multiple Input Lists Into One Output List Have No Guaranteed Order

**What happens:** a merged list renders in a different order between executions.
It is stable in the sandbox, stable in the first week of production, and then it
is not. QA cannot reproduce it and it gets closed as "works as designed", which
is accidentally accurate.

Salesforce's documentation for Transform mappings states that when several input
lists map to one output list, "the system does not guarantee the order of the
items in the output", and recommends: "use a formula to combine and filter the
lists instead of using direct mappings."

**When it occurs:** wherever three direct mappings share one Output JSON Path —
which is the most natural way to express "merge these" and the cheapest possible
configuration, because no expression is evaluated at all.

**How to avoid:** one formula, on the Formulas tab, with an explicit order —
`LIST(inputList1, inputList2, inputListNew)` — mapped to the output path through
Formula Result Path. Also declare the output type: "Make sure that the output
data type for your mapping is set to `List<Map>`."

This is one of the few cases in this skill where the correct answer costs more
than the wrong one. Pay it.

---

## Gotcha 4: The Transform Spends the Caller's CPU and Heap

**What happens:** a Transform that ran fine for a year starts failing after an
unrelated step is added to the Integration Procedure. Nothing about the Transform
changed.

A Transform inside a synchronous Integration Procedure runs in the calling Apex
transaction and draws on its allocation:

| Limit | Synchronous | Asynchronous |
|---|---|---|
| CPU time | 10,000 ms | 60,000 ms |
| Heap | 6 MB | 12 MB |
| SOQL queries | 100 | 200 |
| DML statements | 150 | 150 |

The Transform is frequently the last step and therefore the one that trips the
limit — which makes it the one that gets optimized, often for days, while the
9,000 ms spent before it goes unexamined.

**When it occurs:** whenever a transaction accumulates work over time, which is
every transaction that survives a year.

**How to avoid:** read the transaction total, not the step. If the Integration
Procedure spends 9,200 ms before reaching the Transform, no amount of mapping
tuning will fix this and the honest recommendation is to move the IP to an
asynchronous shape — which multiplies the CPU budget by six and doubles heap — or
to split the transaction.

---

## Gotcha 5: A Transform That Issues No SOQL Can Still Blow the SOQL Limit

**What happens:** `System.LimitException: Too many SOQL queries: 101`, thrown
from a Transform. The artifact is documented as performing "intermediate data
transformations without reading from or writing to Salesforce", so the exception
looks impossible.

The Transform did not query. A custom function it called, once per row, did.

**When it occurs:** at scale, and only at scale. Forty rows is forty queries and
passes; four hundred rows is four hundred and fails. The threshold sits between
the sandbox dataset and the production one, which is exactly where nobody tests.

**How to avoid:** two levels of fix, and the second is usually right.

1. **Remove the query.** If the lookup is against custom metadata,
   `Type__mdt.getAll()` costs no SOQL query at all, so the per-row query was
   never necessary even at one row.
2. **Remove the per-row invocation.** Move the enrichment into a single Apex step
   over the whole array, positioned before the Transform, so the Transform maps a
   field that is already present with the cheapest evaluator there is.

Detection is easy and worth automating: any SOQL inside a class implementing
`Callable` that a Transform formula invokes is a per-row query.

---

## Gotcha 6: Chained Transforms Hold One Full Copy Each

**What happens:** `System.LimitException: Apex heap size too large`, at a row
count that seems modest. Each individual Transform is small.

Every Transform in a chain materializes its complete output structure before the
next step reads it. Three chained Transforms over a wide payload hold three full
copies at peak, against 6 MB synchronously.

**When it occurs:** on wide payloads more than on long ones. A 180-field extract
that produces a 14-field output is carrying 166 fields through every copy.

**How to avoid:** in this order, because the first is usually worth ten times the
second.

1. **Project upstream.** Narrow the Extract's field list to what the output and
   the formulas actually read.
2. **Merge adjacent Transforms** that have no consumer between them. Two
   Transforms in sequence are one Transform with more mappings, and merging
   removes an entire materialization.

Merge only where the logic composes cleanly. A merged Transform that needs a
comment explaining its two halves has traded a performance win for a permanent
maintenance cost.

---

## Gotcha 7: CPU and Heap Failures Look Identical and Want Opposite Fixes

**What happens:** the heap remedy is applied to a CPU problem. Two Transforms are
merged into one, the materialization count drops, and the merged Transform is
exactly as slow as the two it replaced — because the cost was the expressions,
which merging does not reduce.

**When it occurs:** whenever the exception is summarised as "it hit a limit"
rather than read.

**How to avoid:** read the exception text, and branch on it:

| Exception names | The cost is | The fix is |
|---|---|---|
| CPU time | Expression evaluation × rows × mappings | Fewer and cheaper evaluators; bulk Apex instead of per-row |
| Heap | Materialized copies × rows × fields | Upstream projection; merge adjacent Transforms; async context |

Both are also relieved by simply having fewer rows in the transaction, which is
why paging upstream is the fix that works when neither of the above is enough.

---

## Gotcha 8: `OmniDataTransform` Is Documented as Internal-Use-Only

**What happens:** someone writes a script to bulk-fix mappings across 300 Data
Mappers by DML against the standard objects, and the org develops errors nobody
can trace back to it.

The Object Reference (Spring '21 / API 51.0 onwards) says of both
`OmniDataTransform` and `OmniDataTransformItem`:

> "For internal use only. This object and associated records are only for
> internal use. Don't perform any create, edit, or delete operations on this
> object."
>
> "Modifying or deleting this object's records may result in errors with your
> implementation."

**When it occurs:** when a bulk audit turns into a bulk remediation, which is a
natural progression and the exact point at which it becomes unsafe.

**How to avoid:** read for analysis, never write. A read-only census that ranks
Transforms by mapping count is a reasonable way to find the artifacts worth
profiling. Changes go through the designer or through the Metadata API.

<!-- UNVERIFIED: the field API names on these objects (Type, InputType,
     OutputType, and the relationship field on OmniDataTransformItem) could not
     be read — the Object Reference pages render the internal-use warning but not
     the field table to a plain fetch. Describe them in the target org before
     writing a query against them. -->

---

## Gotcha 9: The Designer Preview Is Not a Benchmark

**What happens:** a Transform is cleared of suspicion because it completes
instantly in the designer against a three-row sample.

Every cost that matters in a Transform scales: expression evaluation with
rows × mappings, materialization with rows × fields, per-row Apex with rows and
with a limit that has nothing to do with elapsed time. At three rows all of them
round to the fixed overhead.

The preview also runs outside the Integration Procedure, so it cannot show the
most common cause of a Transform failure — that the transaction was nearly out of
CPU before the Transform started.

**When it occurs:** at the beginning of every investigation, and it sends about
half of them in the wrong direction.

**How to avoid:** profile the enclosing Integration Procedure at production row
and field counts, reading two things at once: the IP's own timing output for the
Transform's share, and an Apex debug log for the transaction's CPU and heap
totals. The first says whether this artifact is worth optimizing; the second says
whether the transaction has room for it to matter.

---

## Gotcha 10: Metadata API Deployment Requires a Setting Nobody Turned On

**What happens:** a CI pipeline is built to deploy Omnistudio components with the
Metadata API and retrieves nothing.

Omnistudio Metadata covers the standard objects `OmniProcess` (OmniScript and
Integration Procedure), `OmniDataTransform` (Data Mapper), and `OmniUiCard`
(FlexCard) — and the **Omnistudio Metadata setting must be enabled** before the
Metadata API can deploy or retrieve them. Until it is on, the components are
invisible to the API.

**When it occurs:** on the first attempt to move Omnistudio out of DataPacks and
into a normal source pipeline, which is usually a migration milestone with a date
attached.

**How to avoid:** treat the setting as a prerequisite in the migration plan, not
as a troubleshooting step. And check the runtime first — on the managed package
runtime, DataPacks remain the deployment mechanism regardless of this setting.

---

## Gotcha 11: The Optimization With the Largest Verified Payoff Is Not in the Transform

**What happens:** two days are spent demoting formulas to direct mappings, for a
result inside measurement noise, while the Apex call site still uses the
managed-package method on an org that has moved to the standard runtime.

Salesforce documents `ConnectApi.OmniDesignerConnect.executeDataMapper` as
replacing `vlocity_ins.DRGlobal.processObjectsJSON()`, states that it "removes
the dependency on the managed package", and claims "up to 60% better performance
for Data Mapper calls from an Apex class compared to the previous method".

**When it occurs:** in every org that migrated runtime without revisiting its
Apex, which is most of them — the old call keeps working, so nothing forces the
change.

**How to avoid:** check the call site before the artifact, and do this swap
before taking a baseline profile. It changes the number every later measurement
is compared against, so a before-profile taken on the old call site is not
comparable to anything measured afterwards.

---

## Gotcha 12: "Bulk Mode" Is Not the Lever It Is Described As

**What happens:** an optimization plan is built around "switching the Transform to
bulk mode", and there is no such setting to switch.

Batch-size configuration is documented for Data Mapper **Load** — where records
are written to Salesforce and batching genuinely applies. A Transform writes
nothing, so its cost model is expressions and materialization, not batch size.
Advice that treats Transform and Load as having the same tuning surface is
conflating the two types.

**When it occurs:** when guidance written for one Data Mapper type is applied to
another, which is easy because they share a designer and a name.

**How to avoid:** the bulk question for a Transform is a different one: is the
*caller* invoking it once per record or once per array? On the standard runtime
`ConnectApi.DataMapperExecuteInputRepresentation.dataMapperInput` is a
`List<String>` — one call with N documents rather than N calls with one is the
bulkification that actually exists here.

<!-- UNVERIFIED: whether the Transform designer exposes any batch or bulk
     setting of its own in the current release could not be confirmed — the
     relevant Salesforce Help pages did not return their body text to a plain
     fetch. Check the designer in the target org rather than assuming either way.
     Batch Size is confirmed only for Data Mapper Load, as a record count. -->
