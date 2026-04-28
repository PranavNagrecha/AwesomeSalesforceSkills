# Well-Architected Notes — Flow Formula And Expression Patterns

## Relevant Pillars

This skill primarily serves Reliability and Performance, with strong Maintainability undercurrents that strengthen Operational Excellence.

- **Reliability** — NULL-safe formula authoring directly removes a class of P1 runtime failures: `Comparison value cannot be null` Decision errors, silent NULL writes via Update Records, and downstream NULL propagation that surfaces as broken email sends or empty Display Text. Picklist comparison correctness (`ISPICKVAL` vs `=`) eliminates a silent locale bug that breaks the moment a translation pack lands. These are not theoretical — they are the most common Flow runtime failures in mature orgs.
- **Performance** — Lazy re-evaluation of Formula resources is the single largest performance trap in Flow. A formula referenced six times inside a 200-iteration loop runs 1,200 times. Caching expensive formulas in Assignment-backed variables converts O(N×M) work into O(N) work and keeps flows under the 10-second sync CPU governor. The 5,000-character single-formula limit forces composition into smaller, individually-evaluable pieces — also a performance win.
- **Security** — Indirect. Formula evaluation respects field-level security on referenced fields (a formula reading a field the running user cannot see returns NULL); authors must avoid relying on formula output to gate security-sensitive logic.
- **Scalability** — A correctly-structured formula chain scales linearly with record count; an incorrectly-structured one (lazy re-eval inside loops) scales quadratically and breaches governors at modest scale.
- **Operational Excellence** — Composed formula resources are easier to debug (each layer can be inspected in Flow Debug independently). Cached-variable refactors are easier to audit and review than formulas referenced from N elements. Both reduce mean-time-to-diagnose for production formula bugs.

## Architectural Tradeoffs

### Tradeoff 1: Inline formula vs reusable Formula resource

- **Inline (in a Decision condition or Screen-component property):** Faster to author, no naming overhead, no resource list clutter. Cost: cannot be reused; if the same expression appears in 3 places it's authored and maintained 3 times.
- **Reusable Formula resource:** Single source of truth, one place to fix. Cost: every reference re-evaluates the entire expression (lazy). Six references inside a loop = six evaluations per iteration.

**Decision rule:** If used 1-2 times AND not inside a loop, inline. If used 3+ times OR inside a loop, declare as Formula resource. If used inside a loop AND non-trivial, declare AND cache in Assignment variable.

### Tradeoff 2: Formula resource vs Apex Invocable

- **Formula resource:** Declarative, no Apex test required, accessible to admins. Cost: no try/catch, no logging, single 5,000-char expression cap, lazy evaluation, no rich type coercion (no Map / Set / List).
- **Apex Invocable:** Programmatic, fully testable, supports complex logic. Cost: requires Apex skills, requires test coverage, harder for admins to maintain.

**Decision rule:** If the expression fits in a single readable formula AND inputs are typed scalars/records, use Formula resource. If logic exceeds 3 levels of nested IF/CASE, requires loops over collections, or needs error handling, push to Invocable.

### Tradeoff 3: Composition depth vs flatness

- **Flat formula resource:** One large expression. Easy to read top-to-bottom. Cost: caps at 5,000 characters; one change risks regression across many use cases.
- **Composed chain (FormulaA → FormulaB → FormulaC):** Each layer focused and reusable. Cost: changes in deep layers are non-obvious to reviewers; each `{!...}` reference triggers another lazy evaluation cascade.

**Decision rule:** Compose at ~3,500 chars defensively. Stay within 3 layers max. Beyond 3 layers, switch to Apex Invocable.

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
4. **Single formula resource that has organically grown to 4,800 chars.** One more edit and the deploy fails. The skill enforces composition at ~3,500 chars defensively.
5. **REGEX inside a loop body.** P0 CPU hot-spot. The skill flags REGEX usage and forces a cache-or-precompute decision.
6. **Implicit Date-to-Text coercion in a multi-locale org.** Non-deterministic output. The skill enforces explicit `TEXT()` casts.
7. **Naive `=` against a multi-select picklist.** Only matches when the value is the SOLE selected value. The skill enforces `INCLUDES`.
8. **Flow formula that uses `PRIORVALUE` or `ISCHANGED`.** Deploy error — those are Validation Rule / Workflow primitives. The skill teaches the `$Record__Prior` substitute.
9. **Composed formula chain 5+ layers deep.** Becomes opaque to reviewers and slow to evaluate. The skill caps composition at 3 layers and routes deeper logic to Apex Invocable.
10. **Hand-formatting numbers with `LEFT/MID/RIGHT/TEXT/MOD` chains.** Hard to read, hard to maintain. The skill recommends pushing complex formatting to Apex.
11. **Treating Percent fields as decimals.** `Amount * Discount_Percent__c` is wrong; must be `Amount * (Discount_Percent__c / 100)`.
12. **Relying on `TEXT(picklist)` to render labels.** Returns API names. The skill enforces an explicit label-mapping pattern.

## Maintainability Considerations

- **Naming.** Formula resources should be named in camelCase that describes the return type and intent: `isStrategicAccount` (Boolean), `effectiveDiscountAmount` (Number), `formattedCustomerHeader` (Text). Names should let a reviewer guess return type without opening the resource.
- **Documentation.** Use the Description field on each Formula resource to record: return type, nullable inputs, intended call sites (especially loop-body callers), TZ contract for date formulas. The Description is the only persistent comment surface for formulas.
- **Composition naming.** Composed chains should encode the composition: `effectiveDiscountAmount` references `baseDiscountFraction` and `tierMultiplier`. Reviewer sees the dependency without opening each layer.
- **Migration safety.** When changing a Formula resource's expression, run Flow Debug with at least three input shapes: all-null, all-populated, edge boundary (zero, empty string, picklist with no value).

## Official Sources Used

- Salesforce Help — Formula Operators and Functions — https://help.salesforce.com/s/articleView?id=sf.customize_functions.htm
- Salesforce Help — Flow Formula Resource — https://help.salesforce.com/s/articleView?id=platform.flow_ref_resources_formula.htm
- Salesforce Help — Flow $Flow Global Variables — https://help.salesforce.com/s/articleView?id=platform.flow_ref_resources_systemvariables.htm
- Salesforce Help — Flow Resources Reference — https://help.salesforce.com/s/articleView?id=sf.flow_ref_resources.htm&type=5
- Salesforce Help — Flow Decision Element — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_decision.htm&type=5
- Salesforce Help — ISPICKVAL Formula Function — https://help.salesforce.com/s/articleView?id=sf.functions_ispickval.htm
- Salesforce Help — INCLUDES Formula Function — https://help.salesforce.com/s/articleView?id=sf.functions_includes.htm
- Salesforce Help — BLANKVALUE Formula Function — https://help.salesforce.com/s/articleView?id=sf.functions_blankvalue.htm
- Salesforce Help — TEXT Formula Function — https://help.salesforce.com/s/articleView?id=sf.functions_text.htm
- Salesforce Help — Date and DateTime Formula Functions — https://help.salesforce.com/s/articleView?id=sf.formula_using_date_datetime.htm
- Salesforce Architects — Well-Architected Framework — https://architect.salesforce.com/well-architected
