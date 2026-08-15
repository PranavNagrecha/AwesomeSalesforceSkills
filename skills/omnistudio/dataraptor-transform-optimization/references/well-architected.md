# Well-Architected Notes — DataRaptor Transform Optimization

## Relevant Pillars

- **Performance** — Primary pillar, with an unusual property: a Transform has no
  budget of its own. It spends the calling transaction's CPU time and heap, and
  it issues no SOQL or DML itself, so almost every limit it trips was consumed
  somewhere else. That makes "optimize the Transform" the wrong first instruction
  most of the time. The design discipline is to measure the transaction before
  the artifact, and to know which of the two failure modes you are in — CPU wants
  fewer and cheaper expressions, heap wants fewer materializations and a narrower
  payload, and applying either remedy to the other problem produces no
  improvement at all.

- **Reliability** — The list-ordering behaviour is a reliability concern
  masquerading as a performance one. Mapping several input lists to one output
  list is the cheapest configuration available and has no guaranteed order; the
  `LIST()` formula costs an expression and is deterministic. Nondeterminism that
  is stable in a sandbox and stable for the first weeks of production is the
  worst defect profile there is, and it is reached by following performance
  advice. Correctness constrains optimization here rather than the reverse.

- **Operational Excellence** — Two runtimes with two Apex APIs, two extension
  mechanisms, two deployment models, and two parallel documentation trees is an
  operational fact before it is a technical one. A team that has not written down
  which runtime it is on will keep re-litigating every question, because half the
  material they find describes the other one. The single highest-value artifact
  this skill produces is not an optimized Transform — it is a recorded answer to
  "which runtime, and how is this invoked".

- **Adaptable / Maintainable** — Every optimization here has a maintenance price
  and some of them are bad trades. Merging two Transforms removes a
  materialization and can produce an artifact that needs a paragraph of
  explanation. Hoisting logic into bulk Apex removes N boundary crossings and
  moves logic out of the layer admins can read. The measurable win is easy to
  quote and the maintenance cost is not, which biases every one of these
  decisions toward the change. State the cost when you propose the change.

## Architectural Trade-offs

**Formula versus custom Apex function.** A formula runs in the Transform engine,
stays visible to whoever opens the designer, and needs no deployment to change. A
custom function can express anything but crosses into Apex once per row, carries
its own test and deployment burden, and takes the logic out of the layer the
artifact advertises. The threshold is whether the requirement *needs* code —
dynamic sObject access, regex, crypto, an external lookup — not whether it can be
written in code. Everything expressible as a formula should be one.

**Per-row custom function versus one bulk Apex step.** The per-row function keeps
the enrichment inside the Transform, where it reads as part of the mapping. It
pays the boundary crossing N times and, if it queries, consumes N queries against
a limit the Transform appears not to touch. A single Apex step over the whole
array collapses both to one and reduces the Transform's mapping to a direct copy —
at the cost of moving the logic to a separate artifact with its own lifecycle, and
of a step in the Integration Procedure whose ordering now matters. Above a few
dozen rows the bulk step wins decisively; below that it is over-engineering.

**Merging chained Transforms versus keeping them separate.** Merging removes an
intermediate materialization, which is the largest single win available on a chain
failing with heap. It also destroys reuse — a step consumed by a second
Integration Procedure cannot be merged away without duplicating it — and can
produce an artifact whose two halves need explaining. Merge adjacent steps with no
consumer between them whose logic composes cleanly, and leave the rest alone.

**Upstream projection versus downstream tuning.** Narrowing the Extract's field
list cuts every materialization in the chain proportionally and is usually worth
more than every mapping change combined. It couples the Extract to the current
output requirement, so the next field the output needs is a change in two places
instead of one. That coupling is real and it is worth paying: a payload carrying
166 unused fields through three copies is a cost paid on every execution forever.

**Synchronous versus asynchronous Integration Procedure.** Moving to an
asynchronous shape multiplies the CPU budget by six and doubles heap, and is
frequently the honest answer when a transaction is genuinely large. It is not an
optimization — nothing got faster — and it changes the user-facing contract from
"the screen waits" to "the result arrives later", which is a product decision.
Propose it as one.

**Managed package versus standard runtime.** The standard runtime removes a
managed-package dependency, unlocks Metadata API deployment of Omnistudio
components, and gives the faster documented Apex entry point. Migration is a
documented three-phase project — now assisted by the Omnistudio Migration
Assistant — and is not something to embark on because a Transform is slow. The
useful move within this skill is narrower and free: if the org has *already*
migrated, make sure the Apex call sites moved with it.

## Anti-Patterns

1. **Optimizing the artifact before measuring the transaction.** A Transform that
   is the last step in a transaction already at 9,200 ms of its 10,000 ms
   allowance cannot be fixed by tuning mappings.

2. **Applying the heap remedy to a CPU problem, or the reverse.** Merging reduces
   materializations, not expression count. Read the exception before choosing.

3. **Merging several input lists with direct mappings.** Cheapest and
   nondeterministic — "the system does not guarantee the order of the items in
   the output". Use a `LIST()` formula.

4. **SOQL inside a per-row custom function.** N queries against a limit of 100,
   thrown from an artifact documented as not reading from Salesforce. Custom
   metadata `getAll()` costs no query; a bulk Apex step costs one invocation.

5. **Writing to `OmniDataTransform` or `OmniDataTransformItem`.** "For internal
   use only… Don't perform any create, edit, or delete operations on this
   object." Read for analysis; change through the designer or Metadata API.

6. **Managed-package Apex on a standard-runtime org.** `vlocity_ins.DRGlobal` still
   works and keeps a dependency the org is trying to remove — while the
   documented replacement claims up to 60% better performance.

7. **Benchmarking in the designer preview.** Three rows measure fixed overhead
   and nothing that scales, and the preview runs outside the transaction where
   the real constraint lives.

8. **Quoting performance multipliers with no source.** "5–10× slower" reads as
   authoritative and is not measurable by the reader. Give direction, and make
   them profile.

9. **Blanket "merge all chains" advice.** Ignores reuse, ignores readability, and
   is the wrong fix entirely when the failure is CPU.

## Official Sources Used

- Industries Common Resources Developer Guide — Data Mapper (the four types verbatim: "Extract—Read data from Salesforce objects and JSON output or XML with field mappings", "Turbo Extract—Read data from a single Salesforce object type, with support for fields from related objects", "Transform—Perform intermediate data transformations without reading from or writing to Salesforce", "Load—Create and update Salesforce data from JSON or XML input") — https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/omnistudio_data_mapper_apis.htm
- Object Reference for the Salesforce Platform — `OmniDataTransform` ("For internal use only. This object and associated records are only for internal use. Don't perform any create, edit, or delete operations on this object"; "Modifying or deleting this object's records may result in errors with your implementation"; documented from Spring '21 / API 51.0 through Summer '26 / API 67.0) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_omnidatatransform.htm
- Object Reference for the Salesforce Platform — `OmniDataTransformItem` (same internal-use-only statement) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_omnidatatransformitem.htm
- Apex Developer Guide — Execution Governors and Limits (10,000 ms synchronous / 60,000 ms asynchronous CPU time; 6 MB / 12 MB heap; 100 / 200 SOQL queries; 150 DML statements — the allocations a Transform inherits from its calling transaction) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide — Custom Metadata Types in Apex (`getAll()` costs no SOQL query — the fix for a per-row lookup inside a custom function) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_metadata_types.htm
- Salesforce Help — Omnistudio Data Mapper Calls From Apex (`ConnectApi.OmniDesignerConnect.executeDataMapper(bundleName, apexInput)`; "This API replaces the `vlocity_ins.DRGlobal.processObjectsJSON()` method"; "This Connect API removes the dependency on the managed package"; "up to 60% better performance for Data Mapper calls from an Apex class compared to the previous method"; `ConnectApi.DataMapperExecuteInputRepresentation` with `dataMapperInput` (`List<String>`), `inputType`, and `options`; `ConnectApi.DataMapperExecuteOptionsRepresentation` with `locale`, `ignoreCache`, `shouldSendLegacyResponse`; `ConnectApi.DataMapperExecuteOutputRepresentation` with `response`) — https://help.salesforce.com/s/articleView?id=sf.os_dataraptor_calls_from_apex_47779.htm&language=en_US&type=5
- Salesforce Help — Omnistudio Data Mapper Transform Data Mappings (the Input JSON Path / Output JSON Path / Formula / Formula Result Path columns; "the system does not guarantee the order of the items in the output"; "use a formula to combine and filter the lists instead of using direct mappings"; `LIST(inputList1, inputList2, inputListNew)`; "Make sure that the output data type for your mapping is set to `List<Map>`"; Transform Map Values key-value substitution) — https://help.salesforce.com/s/articleView?id=sf.os_dataraptor_transform_data_mappings_46630.htm&language=en_US&type=5
- Salesforce Help — Omnistudio Data Mappers (the standard-runtime tree; the four types; the rename from DataRaptor; access control via Sharing Settings and Sharing Sets or Profiles and Permission Sets) — https://help.salesforce.com/s/articleView?id=xcloud.os_omnistudio_dataraptors_45587.htm&language=en_US&type=5
- Salesforce Help — Omnistudio Data Mappers (Managed Package) (the managed-package tree, kept distinct from the above) — https://help.salesforce.com/s/articleView?id=sf.os_dataraptors.htm&language=en_US&type=5
- Salesforce Help — Enable Omnistudio Metadata API Support (Omnistudio Metadata covers the `OmniProcess`, `OmniDataTransform`, and `OmniUiCard` standard objects; the setting must be enabled before Metadata API deploy or retrieve) — https://help.salesforce.com/s/articleView?id=sf.os_enable_omnistudio_metadata_api_support.htm&language=en_US&type=5
- Salesforce Help — Deploying Omnistudio Components Between Orgs or Migrating from Omnistudio for Managed Packages (the managed package → standard runtime migration as a three-phase process) — https://help.salesforce.com/s/articleView?id=xcloud.os_deploy_or_migrate.htm&language=en_US&type=5
- Salesforce Developers Blog — Automate Your Move to the Omnistudio Standard Runtime with the New Migration Assistant — https://developer.salesforce.com/blogs/2025/12/automate-your-move-to-the-omnistudio-standard-runtime-with-the-new-migration-assistant
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

### Claims deliberately not made

**No JavaScript evaluator is described.** An earlier version of this skill listed
JavaScript alongside formulas and Apex as a Transform evaluator. No Salesforce
source consulted here documents one, so the claim has been removed. The removal is
not a claim in the other direction: "not in the documented list" is not "absent
from the product", and OmniStudio does involve custom JavaScript in other contexts
(FlexCards, custom LWC). If you need to know, check the designer in the target
org.

**No per-row or bulk speed multipliers are quoted.** The only performance figure
here that traces to Salesforce is the "up to 60%" claim for the Connect API entry
point. Figures such as "row-by-row is 5–10× slower" appeared in an earlier version
of this skill with no source and have been removed rather than re-sourced.

**No Transform batch or bulk setting is asserted or denied.** Batch Size is
documented for Data Mapper **Load**, as a record count. Whether the Transform
designer exposes any batch setting of its own in the current release could not be
confirmed — the relevant Salesforce Help pages did not return body text to a plain
fetch. See the inline marker in [`gotchas.md`](gotchas.md), Gotcha 12.

**Field API names on the Omnistudio standard objects are not quoted.** The Object
Reference pages render the internal-use-only warning but not the field table to a
plain fetch, so the census query in [`examples.md`](examples.md), Example 4, is
marked illustrative. Describe the objects in the target org before relying on it.
