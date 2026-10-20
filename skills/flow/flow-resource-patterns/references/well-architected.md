# Well-Architected Notes — Flow Resource Patterns

## Relevant Pillars

Picking the right resource type for each piece of data in a flow is
the most consequential design decision an admin makes after the
"Flow vs Apex" question itself. The choice cuts across five Salesforce
Well-Architected pillars; the dominant ones are Operational Excellence
and Reliability because resource selection determines how the flow
behaves under change.

- **Operational Excellence** — A flow whose data layer is well-typed
  (Constants for shared literals, Formulas for derived values, named
  Variables for state, prefixed for type at a glance) is auditable.
  Future admins running the References panel on a Constant or
  Formula see every consumer; future admins reading an Assignment
  chain need to mentally simulate the data flow. Type discipline at
  the resource level is the single highest-leverage Operational
  Excellence investment in a Flow.
- **Reliability** — (UNVERIFIED (2026-10-20): activation-time constants and per-reference formula re-evaluation are not in the corpus) Constants resolved at activation, Formulas
  re-evaluated per reference, and Variables holding cached snapshots
  fail differently when their inputs change mid-flow. Wrong resource
  choice → stale derived values, "the screen shows X but the record
  has Y," and intermittent test failures that survive code review.
  Resource selection is a reliability discipline, not a style choice.
- **Scalability** — Formula re-evaluation cost compounds inside
  Loops. A heavy Formula referenced six times per iteration over 200
  records is 1,200 evaluations — enough to push Apex CPU time on a
  record-triggered flow into the 10,000-ms CPU limit zone (apexdev 264 L19782; UNVERIFIED (2026-10-20) that Formula evaluations count). The
  scalability lever is "cache a hot Formula into a Variable at the
  top of the Loop body" — see `gotchas.md` Gotcha 2.
- **Security** — Choice resources tied to Record Choice Sets issue
  SOQL at flow run-time using the running user's permissions IF the
  flow runs in user context, but bypass FLS entirely if the flow
  runs in system context: `SystemModeWithSharing` "doesn't respect object
  permissions, field-level access, or other permissions of the running
  user" and `SystemModeWithoutSharing` "can access all data"
  (api_meta 264 L70912-70921). The data exposed by a screen flow's choice
  set is the same data that's available to the flow's chosen
  context. Mis-scoping a flow's run context (`System Context with
  Sharing` vs `User Context` vs `System Context Without Sharing`)
  makes Record Choice Sets a vector for surfacing data the user
  shouldn't see. The skill at `flow/flow-runtime-context-and-sharing`
  covers context selection; this skill assumes you've already chosen
  the right context.
- **Adaptable** — Constants and `$Label` references for shared
  values (region names, threshold numbers, environment-specific
  Ids) are the cheapest path to a flow that survives translation,
  re-branding, or org migration. Hardcoded literals scattered across
  Decisions and Assignments are the cheapest path to a flow that
  doesn't.

## Architectural Tradeoffs

The dominant tradeoff is **resource type per value purpose**. The
matrix below resolves the choice for the common cases:

| Value purpose | Right resource | Why | Cost of wrong choice |
|---|---|---|---|
| Hardcoded literal reused 2+ times (record-type Id, region code, threshold) | **Constant** | Constant value is a literal (api_meta 264 L72921-72923); UNVERIFIED (2026-10-20): activation-time resolution and the References panel are not in the corpus. Single edit site | Hardcoded literals scattered across elements → 4 places to edit for one business change |
| Hardcoded value used exactly once (a default in a single Assignment) | **Inline literal** | Constant adds a layer with no payback | Over-abstraction; Resources panel cluttered |
| Mutable state that needs to persist across multiple elements | **Variable** | Held in memory until the flow ends or the variable is reassigned | Formula recomputes every reference (slow if expensive), Constant rejects non-literal values |
| Derived value computed from inputs, referenced 2+ times outside a loop | **Formula** | Always-current, no cache invalidation bugs, zero canvas elements | Variable + Assignment chain holds stale values when inputs change mid-flow |
| Derived value computed inside a Loop, referenced 2+ times per iteration | **Formula cached into Variable at top of loop body** | Single evaluation per iteration instead of N | Raw Formula reference: N evaluations per iteration → CPU governor risk on 200-record batches |
| Multiple records / values of one type | **Collection Variable** | Bulkified Get Records output, eligible for Collection Filter / Collection Sort / Loop, fed into bulk DML | Looping over single-record Get Records calls: N SOQL operations → SOQL governor |
| Single related record (e.g., the parent Account of $Record) | **SObject Variable** populated by Get Records (or dot-notation traversal if ≤5 lookups deep; UNVERIFIED (2026-10-20): the depth figure is not in the corpus) | Null-safe in subsequent assignments if guarded with ISBLANK | Treating an SObject as never-null: NullPointerException-style errors in scheduled paths |
| Hardcoded option list shown on a screen (Yes/No, region picker with 3 options) | **Choice** (one per option) | Self-contained, no SOQL, no metadata dependency | Record Choice Set: unnecessary SOQL + cache concerns. Picklist Choice Set: requires a real field to exist |
| Options shown on a screen that mirror a picklist field's values | **Picklist Choice Set** | Reflects admin-maintained picklist with no flow change needed (with the reactivation caveat — see Gotcha 5, UNVERIFIED (2026-10-20); the guide says the choice set is generated at run time, api_meta 264 L72965-72966) | Hardcoded Choice list: drifts from the picklist as values are added/retired |
| Options shown on a screen sourced from live records | **Record Choice Set** with explicit filter + limit | Always current, bounded by SOQL | Unfiltered Record Choice Set on a high-cardinality object: the first 200 rows of an arbitrary order (limit is at most 200, api_meta 264 L73017-73018), not 5,000 |
| Options shown on a screen derived from in-flow data (already fetched + filtered) | **Collection Choice Set** fed by an SObject Collection | Single source of truth — no second SOQL | Record Choice Set with redundant filter: duplicates the filtering logic and risks drift |
| Email body, screen long-text, complex formatted string | **Text Template** | Previewable in the builder, merge fields validated at save, no Assignment-chain string concatenation | Assignment chain building strings: 5 elements to do what 1 Text Template does, no preview |

A second tradeoff: **Choice vs Picklist Choice Set vs Record Choice
Set vs Collection Choice Set**. The selection rule that works in
practice:

- *Static list ≤ 5 options that won't change* → Choice (one per option).
- *List that mirrors a picklist field* → Picklist Choice Set.
- *List sourced from live records, not already in memory* → Record Choice Set.
- *List already loaded into a Collection Variable* → Collection Choice Set.

The wrong fork here usually shows up as duplicated filtering logic
(Record Choice Set re-filtering a collection the flow already has)
or as drift between a hardcoded Choice list and a picklist that
later gained new values.

A third tradeoff: **Formula recomputation vs Variable caching**. The
naive default is "Formula everywhere" because it's cleaner. The
naive default fails when the formula is non-trivial AND referenced
many times inside a Loop. The override rule: cache when (the
formula body has > 1 IF / CASE branch, REGEX, or a date-math chain)
AND (referenced 2+ times per loop iteration). For everything else,
prefer Formula for the always-current guarantee.

## Anti-Patterns

1. **Global Variable for transient derived values.** Variable +
   Assignment chain for `Discounted_Amount = Amount * (1 - Rate)`
   when the inputs may change mid-flow. The cached Variable holds
   the old value the moment Amount or Rate is updated. Use a
   Formula instead — see `examples.md` anti-pattern.
2. **Hardcoded literals in element fields when a Constant fits.**
   Same string or number in 3+ Decision/Assignment fields produces
   a "find all references" exercise on every business change.
   Promote to Constant.
3. **Loop + Decision + Assignment when a Collection Filter fits.**
   8-element subgraph for a job the Collection Filter element does
   in 1. The Loop pattern made sense pre-Summer '23; the platform
   has the right primitive now.
4. **Record Choice Set with no filter or limit.** Unbounded SOQL
   feeding a screen picklist. Acceptable on tiny reference objects
   (a handful of regions, a small lookup table); never acceptable
   on Account, Contact, Opportunity, or any high-cardinality object.
5. **Picklist Choice Set without a reactivation runbook** (UNVERIFIED (2026-10-20): see Gotcha 5). Picklist
   Choice Set caches metadata at activation. Without an ops process
   to deactivate-and-reactivate flows after picklist changes,
   screen flows silently fall behind the source-of-truth picklist
   values.

## Official Sources Used

The Salesforce Help URLs below describe the Flow resource model
(Variables, Constants, Formulas, Choices, Picklist Choice Sets,
Record Choice Sets, Collection Choice Sets, Text Templates) and the
elements that consume them (Assignment, Decision, Loop, Collection
Filter, Get Records, Update Records). Salesforce Help is the
authoritative source for each resource's behavior and binding rules.

- Metadata API Developer Guide 264 — FlowChoice L72461-72484, FlowConstant L72909-72923, FlowDynamicChoiceSet L72965-73060, FlowFormula L73291-73315, FlowTextTemplate L75562-75572, FlowVariable isInput/isOutput L75629-75655, FlowAssignmentOperator L72347-72380, runInMode L70907-70927
- Flow Reference — Resources:
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_resources.htm
- Flow Reference — Variable:
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_resources_variable.htm
- Flow Reference — Formula:
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_resources_formula.htm
- Flow Reference — Constant:
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_resources_constant.htm
- Flow Reference — Choice (and Picklist / Record / Collection Choice Sets):
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_resources_choice.htm
- Flow Builder — Collection Filter element:
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_collection_filter.htm
- Flow Builder — How a Flow Runs in System or User Context:
  https://help.salesforce.com/s/articleView?id=sf.flow_concepts_running_context.htm
- Salesforce Architects — Well-Architected (Operational Excellence):
  https://architect.salesforce.com/well-architected/
