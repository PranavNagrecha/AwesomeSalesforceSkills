# Well-Architected Notes — Flow Formula And Expression Patterns

## Relevant Pillars

This skill primarily serves Reliability and Performance, with strong Maintainability undercurrents that strengthen Operational Excellence.

- **Reliability** — NULL-safe formula authoring directly removes a class of P1 runtime failures: `Comparison value cannot be null` Decision errors, silent NULL writes via Update Records, and downstream NULL propagation that surfaces as broken email sends or empty Display Text. Picklist comparison correctness (`ISPICKVAL` vs `=`) eliminates a silent locale bug that breaks the moment a translation pack lands. These are not theoretical — they are the most common Flow runtime failures in mature orgs.
- **Performance** — Lazy re-evaluation of Formula resources is the single largest performance trap in Flow. A formula referenced six times inside a 200-iteration loop runs 1,200 times. Caching expensive formulas in Assignment-backed variables converts O(N×M) work into O(N) work and keeps flows under the documented CPU ceiling of 10,000 ms synchronous / 60,000 ms asynchronous (`apexdev.txt` L19578). UNVERIFIED (2026-09-05): the lazy-re-evaluation behaviour itself — that Flow does not memoise a Formula resource between references — is not stated anywhere in `api_meta.txt`, `apexdev.txt` or the App Limits cheat sheet. It is the observed and universally-reported behaviour, and every recommendation here rests on it, but this corpus does not confirm it.
- **Security** — Conditional, and the condition is an org switch. `api_meta.txt` L116855–L116858, `FlowSettings.doesFormulaEnforceDataAccess`: *"Indicates whether formula resources and formula fields in a flow enforce **record-level** security (true) or not (false). Corresponds to the Enforce Data Access in Flow Formulas critical update. Available in API version 48.0 and later."* Two corrections to what this file said before 2026-09-05: it is **record-level**, not field-level, and it is **a setting**, not a guarantee. A formula in an org where the switch is off does not enforce it at all. Never let formula output be the only gate on security-sensitive logic, and diff this setting between source and target org before deploying.
- **Scalability** — A correctly-structured formula chain scales linearly with record count; an incorrectly-structured one (lazy re-eval inside loops) scales quadratically and breaches governors at modest scale.
- **Operational Excellence** — Composed formula resources are easier to debug (each layer can be inspected in Flow Debug independently). Cached-variable refactors are easier to audit and review than formulas referenced from N elements. Both reduce mean-time-to-diagnose for production formula bugs.

## Architectural Tradeoffs

### Tradeoff 1: Inline formula vs reusable Formula resource

- **Inline (in a Decision condition or Screen-component property):** Faster to author, no naming overhead, no resource list clutter. Cost: cannot be reused; if the same expression appears in 3 places it's authored and maintained 3 times.
- **Reusable Formula resource:** Single source of truth, one place to fix. Cost: every reference re-evaluates the entire expression (lazy). Six references inside a loop = six evaluations per iteration.

**Decision rule:** If used 1-2 times AND not inside a loop, inline. If used 3+ times OR inside a loop, declare as Formula resource. If used inside a loop AND non-trivial, declare AND cache in Assignment variable.

### Tradeoff 2: Formula resource vs Apex Invocable

- **Formula resource:** Declarative, no Apex test required, accessible to admins. Cost: no try/catch, no logging, a single expression whose length ceiling is undocumented (Gotcha 4), lazy evaluation, no rich type coercion (no Map / Set / List).
- **Apex Invocable:** Programmatic, fully testable, supports complex logic. Cost: requires Apex skills, requires test coverage, harder for admins to maintain.

**Decision rule:** If the expression fits in a single readable formula AND inputs are typed scalars/records, use Formula resource. If logic exceeds 3 levels of nested IF/CASE, requires loops over collections, or needs error handling, push to Invocable.

### Tradeoff 3: Composition depth vs flatness

- **Flat formula resource:** One large expression. Easy to read top-to-bottom. Cost: an undetermined length ceiling (see `references/gotchas.md` Gotcha 4 — the grounded figure is 3,900 source characters for formula *fields*, `apexdev.txt` L28144, and no bound at all is documented for `FlowFormula`); one change risks regression across many use cases.
- **Composed chain (FormulaA → FormulaB → FormulaC):** Each layer focused and reusable. Cost: changes in deep layers are non-obvious to reviewers; each `{!...}` reference triggers another lazy evaluation cascade.

**Decision rule:** Compose at ~3,000 chars defensively — short enough that whichever ceiling turns out to apply is irrelevant. Stay within 3 layers max. Beyond 3 layers, switch to Apex Invocable. The composition mechanic is grounded: the guide's own flow sample composes `<formulas>` by name (`api_meta.txt` L73357–L73362).

### Tradeoff 4: Cached Assignment vs lazy Formula reference

- **Lazy Formula reference:** Always returns the latest computation (responsive to input changes within an iteration). Cost: re-evaluation cost per reference.
- **Cached variable:** Single evaluation per iteration. Cost: if upstream inputs change later in the iteration, the cached value is stale.

**Decision rule:** Cache when (a) inputs do not change within the iteration AND (b) reference count × loop size > ~500. Otherwise leave as lazy formula.

### Tradeoff 5: TODAY() (running-user TZ) vs $Flow.CurrentDate (org default TZ)

- **TODAY():** Aligns with the user's perspective. Same flow run for users in different TZs returns different values near midnight.
- **$Flow.CurrentDate:** Deterministic per org. Matches Workflow / Process Builder / Scheduled Apex semantics.

**Decision rule:** Pick deliberately and document. For audit/log lines that must align across users, prefer `$Flow.CurrentDate`. For user-facing "is this today?" checks, prefer `TODAY()`.

### Tradeoff 6: Defensive NULL guards in every formula vs strict upstream contracts

- **Defensive guards (BLANKVALUE everywhere):** Survives upstream refactors. Cost: longer formulas, possible double-guarding.
- **Strict upstream contracts:** Inputs are guaranteed non-null by the caller. Cost: any new caller that violates the contract introduces silent bugs.

**Decision rule:** Default to defensive guards on every nullable input. The cost of a single `BLANKVALUE` wrap is trivial; the cost of a P1 NULL-propagation bug is hours of diagnostics.

## Anti-Patterns This Skill Helps Avoid

1. **NULL-tainted formula referenced by a Decision condition.** Breaks production with `Comparison value cannot be null`. The skill enforces `BLANKVALUE` on every nullable input.
2. **`=` against a picklist label.** Silent locale bug, fails the day translations land. The skill enforces `ISPICKVAL` / `INCLUDES`.
3. **Formula resource referenced N times inside a loop body.** Quadratic CPU. The skill enforces Assignment-cached variables for any non-trivial formula referenced 3+ times in a loop.
4. **Single formula resource that has organically grown past readability.** The skill enforces composition at ~3,000 chars defensively rather than arguing about an undocumented ceiling.
5. **REGEX inside a loop body.** P0 CPU hot-spot. The skill flags REGEX usage and forces a cache-or-precompute decision.
6. **Implicit Date-to-Text coercion in a multi-locale org.** Non-deterministic output. The skill enforces explicit `TEXT()` casts.
7. **Naive `=` against a multi-select picklist.** Only matches when the value is the SOLE selected value. The skill enforces `INCLUDES`.
8. **Flow formula that uses `PRIORVALUE` or `ISCHANGED`.** Deploy error — those are Validation Rule / Workflow primitives. The skill teaches the `$Record__Prior` substitute.
9. **Composed formula chain 5+ layers deep.** Becomes opaque to reviewers and slow to evaluate. The skill caps composition at 3 layers and routes deeper logic to Apex Invocable.
10. **Hand-formatting numbers with `LEFT/MID/RIGHT/TEXT/MOD` chains.** Hard to read, hard to maintain. The skill recommends pushing complex formatting to Apex.
11. **Dividing a Percent field by 100 inside a formula.** `Amount * (Discount_Percent__c / 100)` returns 1/100th of the intended value — the platform already expresses percent fields divided by 100 in formulas. The skill enforces direct multiplication and fractional range bounds.
12. **Relying on `TEXT(picklist)` to render labels.** Returns API names. The skill enforces an explicit label-mapping pattern.
13. **A `<formulas>` block with no `<dataType>`.** It becomes a Number formula (`api_meta.txt` L70609) and fails at the consuming element, not at the formula. The skill's checker fails the build on it.
14. **A Number or Currency formula with no `<scale>`.** The guide states no default (L70618–L70622); the stored value can differ from what the record displays. The checker warns.
15. **`filterFormula` and `filters` both set on `<start>`.** Both deploy; the guide never says which the runtime honours. The skill treats unreadability as the defect.
16. **A formula or text template referencing a resource name that does not exist in the flow.** A deploy failure whose message names the flow, not the reference. The checker resolves every `{!name}` against the flow's own resources.
17. **Shipping a formula-heavy flow across orgs without diffing Process Automation Settings.** Four documented `FlowSettings` switches change formula behaviour with no XML change (`api_meta.txt` L116855–L116915).

## Maintainability Considerations

- **Naming.** Formula resources should be named in camelCase that describes the return type and intent: `isStrategicAccount` (Boolean), `effectiveDiscountAmount` (Number), `formattedCustomerHeader` (Text). Names should let a reviewer guess return type without opening the resource.
- **Documentation.** Use the Description field on each Formula resource to record: return type, nullable inputs, intended call sites (especially loop-body callers), TZ contract for date formulas. The Description is the only persistent comment surface for formulas.
- **Composition naming.** Composed chains should encode the composition: `effectiveDiscountAmount` references `baseDiscountFraction` and `tierMultiplier`. Reviewer sees the dependency without opening each layer.
- **Migration safety.** When changing a Formula resource's expression, run Flow Debug with at least three input shapes: all-null, all-populated, edge boundary (zero, empty string, picklist with no value).

## Official Sources Used

Grounded in the extracted PDF corpus. Line numbers are `grep -n` hits against the files in
`scratchpad/`; the PDFs are the citable artefacts.

- **Metadata API Developer Guide — `FlowFormula`, L70596–L70622** — `dataType` enum and its Number default, `expression` required, `scale` scoped to Number/Currency. Supports Gotchas 41 and 42, `references/metadata-examples.md` §1, and the "Formula resource vs Apex Invocable" tradeoff's premise that a formula resource has no typed contract beyond these three fields. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Metadata API Developer Guide — `FlowStart`, L72390–L72404** — `filterFormula` (API 55.0+), `filterLogic`, `filters`, with no exclusivity statement between them. Supports Gotcha 45 and the entry-condition row of the Decision Guidance table. Same PDF.
- **Metadata API Developer Guide — `FlowSettings`, L116849–L116915** — `doesEnforceApexCpuTimeLimit`, `doesFormulaEnforceDataAccess`, `doesFormulaGenerateHtmlOutput`, `enableFlowBREncodedFixEnabled`, `enableFlowFormulasFixEnabled`. Supports the Security pillar bullet above (and its correction), Gotchas 26 and 43. Same PDF.
- **Metadata API Developer Guide — `FlowTextTemplate` L72820–L72831 and `FlowRule` L71301–L71325** — `isViewedAsPlainText` default `false` = rich text; `conditionLogic` limited to `and`/`or`/advanced logic. Supports Gotcha 44 and the "inline decision formula" tradeoff in `references/metadata-examples.md` §4. Same PDF.
- **Metadata API Developer Guide — `FlowTest` and subtypes, L73960–L74400** — `.flowtest` suffix, API 55.0+, `elementApiName` limited to `Start`/`Finish`, the assertion/condition grammar, and the guide's own sample. Supports the Maintainability position that a formula change should fail a test rather than a customer. Same PDF.
- **Object Reference — `FormulaFunctionAllowedType`, L149310–L149400, and `FormulaFunction`, L149240–L149303** — restricted `Type` picklist `FLOW | VALIDATION | VISUALFORCE`; `ExampleString`; the note that the older per-context booleans were removed in API 48.0. This is the org-side substitute for the unfetchable help article and underpins every "is this function legal here" claim in the package. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Object Reference — compound fields, L2936–L2937** — only `ISBLANK`, `ISCHANGED`, `ISNULL` work on compound fields; `BLANKVALUE`, `CASE`, `NULLVALUE`, `PRIORVALUE` and comparison operators do not. Supports Gotcha 47 and bounds Tradeoff 6's "defensive guards everywhere" default. Same PDF.
- **Apex Developer Guide — formula length, L28143–L28144** — 3,900 source characters including spaces, return characters and comments; a separate compile-size limit exists but is unnumbered. Supports Gotcha 4 and Tradeoff 3. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Developer Guide — governor limits table, L19540–L19580** — CPU 10,000 ms synchronous / 60,000 ms asynchronous. Supports the Performance pillar bullet and Tradeoff 4's caching threshold. Same PDF.

Not grounded in this corpus, and marked UNVERIFIED at each point of use:

- **Formula Operators and Functions** — https://help.salesforce.com/s/articleView?id=sf.customize_functions.htm — the semantics of every formula function this skill discusses. Named but not reproduced at `apexdev.txt` L28148. Unfetchable.
- Salesforce Help — Flow Formula Resource — https://help.salesforce.com/s/articleView?id=platform.flow_ref_resources_formula.htm
- Salesforce Help — Flow $Flow Global Variables — https://help.salesforce.com/s/articleView?id=platform.flow_ref_resources_systemvariables.htm — the only source for `$Flow.CurrentDate`, `$Flow.FaultMessage` and `$Flow.InterviewStartTime`, none of which appear in `api_meta.txt`.
- Salesforce Help — Understanding Salesforce Percentage Fields in Flows — the table that separates the two conventions: referencing a percent field *into a formula* "Divides by 100 — 100 becomes 1", passing a value *into* the field "Doesn't change — 100 remains 100" (verified 2026-08-13; not present in the PDF corpus) — https://help.salesforce.com/s/articleView?id=000380436&language=en_US&type=1
- Salesforce Developers — Examples of Validation Rules: Sample Number Validation Rules — https://developer.salesforce.com/docs/atlas.en-us.usefulValidationRules.meta/usefulValidationRules/fields_useful_validation_formulas_number.htm
- Salesforce Architects — Well-Architected Framework — https://architect.salesforce.com/well-architected
