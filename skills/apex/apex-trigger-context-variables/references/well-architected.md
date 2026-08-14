# Well-Architected Notes — Apex Trigger Context Variables

## Relevant Pillars

The context-variable rules are tactical, but the choice of how to
*structure* code around them is architectural — and that choice
disproportionately shows up in two pillars: Scalability and
Operational Excellence. Reliability matters too because misuse
throws runtime exceptions that roll back the entire DML batch.

- **Scalability** — Every context-variable access pattern must
  scale identically at 1 record and 200 records. The single biggest
  scaling bug in this skill's domain is branching on `Trigger.size`
  to take a "single-record fast path" — the bulk path then has
  zero production test coverage until the day a Data Loader job
  hits, and it explodes. The mutability rules also matter for
  scale: stamping in `before` events costs zero extra DML; stamping
  in `after` events with `List<SObject>` + `update` costs one
  extra DML and re-fires every trigger downstream.
- **Operational Excellence** — Routing logic via inline
  `if (Trigger.isBefore && Trigger.isInsert)` cascades in the
  trigger body produces a code shape that is hostile to debugging,
  testing, and onboarding. A canonical `TriggerHandler` subclass
  with one virtual per event is *operationally* superior because
  each event's logic is independently unit-testable, the dispatch
  is centralized, and adding a new event is a localized change. The
  context variables themselves are a poor primitive for ops; the
  framework around them is what teams actually operate on.
- **Reliability** — The two runtime failure modes
  (`System.NullPointerException` from accessing a context variable
  in the wrong event, and `System.FinalException: Record is read-only`
  from mutating in an `after`-context) both roll back the entire
  DML transaction. A single mis-routed line can fail a 200-record
  Data Loader batch and surface to the user as a wall of toasts.
  Defensive structure (event-specific handler methods, no
  cross-event helpers that take `Trigger.new`/`Trigger.old` as
  raw parameters) is the cheapest reliability gain in the area.
- **Security** — Lower weight here. Sharing and FLS enforcement
  belong to the handler class the trigger delegates to (its
  `with sharing` declaration, `Security.stripInaccessible` calls
  before DML), not to the context variables themselves — **a
  `.trigger` runs in system mode at every `apiVersion` and cannot
  declare a sharing or access mode**, and Summer '26 did not change
  that. What the *handler's* missing keyword means did change: at
  **67.0+** a bare class runs `with sharing` with database
  operations defaulting to user mode; at **66.0 and below** it runs
  without sharing in system mode. The gate is the `.cls-meta.xml`,
  not the org's release — and under a `TriggerHandler` base class
  it is every link in the chain, not just the subclass you opened:
  one class saved at 67.0+ pulls the rest to `with sharing`.
  Canonical table in
  [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md)
  § *Apex security idiom by API version*. Because the trigger is
  always system mode, the recursion guard *itself* (e.g., a static
  `Set<Id>` of processed ids) is a security-adjacent concern —
  leaking it across a single transaction can let a low-privilege
  user trigger privileged operations the trigger meant to skip.

## Architectural Tradeoffs

The defining choice is **raw trigger body with inline context-var
switching vs canonical `TriggerHandler` framework**. Both can use
the same context variables; they differ in how the dispatch is
expressed and where the recursion / bypass logic lives.

| Dimension | Raw trigger + inline switching | Canonical `TriggerHandler` framework |
|---|---|---|
| Lines per trigger | 50–300 (grows per event added) | 1 (`new XTriggerHandler().run();`) |
| Event routing | `if (Trigger.isBefore && Trigger.isInsert) {...}` cascades | Virtual methods (`beforeInsert()` etc.), dispatched once in base class |
| Recursion guard | Hand-rolled per trigger | `TriggerHandler.skipOnce()` + depth counter (free) |
| Runtime bypass | Hand-rolled (Custom Setting check in trigger body) | `TriggerControl` via `Trigger_Setting__mdt` + Custom Permission |
| Cross-event helper sharing | Easy (call from inline) | Slightly harder (helpers live in subclass or selectors) |
| Onboarding cost | Each trigger reads differently | Same shape across every object |
| Testability per event | Mocking the global `Trigger` context is painful | Each virtual is callable in isolation |
| Best for | One-off, single-event triggers; legacy code | Anything beyond a single event, every greenfield handler |

The recommended position: **default to `templates/apex/TriggerHandler.cls`
and `templates/apex/TriggerControl.cls` for every new trigger**.
Inline switching is only justified for a single-event trigger that
will never grow, and in practice "will never grow" is almost always
wrong — within a year someone adds an `after insert` to do related-record
creation, and the `if` cascade begins.

A secondary tradeoff: **iterate `Trigger.new` vs iterate
`Trigger.newMap.values()`**. The two return the same records;
`Trigger.new` preserves DML input order while `Trigger.newMap`
iteration order is unspecified. For field stamping or diff work,
prefer `Trigger.new` — the deterministic order makes test failures
reproducible. Switch to `Trigger.newMap` only when the next line
needs the Id as a Map key.

A tertiary tradeoff: **`Trigger.size` vs `Trigger.new.size()`**.
The values agree in non-delete events. Prefer `Trigger.new.size()`
because the call site reads as "the count of inserting / updating
records I'm iterating," which is what most code actually means.
`Trigger.size` is unambiguous only in delete events (where
`Trigger.new` is null and you'd use `Trigger.old.size()`).

## Anti-Patterns

1. **Branching on `Trigger.size` for single vs bulk paths.** Both
   branches need test coverage; in practice only the single-record
   branch gets coverage because unit tests insert one record. The
   bulk branch ships untested. Bulkify unconditionally — there's
   no governor budget saved by "skipping" the bulk-safe code path
   on a 1-record DML.
2. **Inline context-var switching as the only dispatch mechanism.**
   Produces 200-line trigger bodies that resist refactoring. Use
   the `TriggerHandler` virtuals; let the base class own the
   `Trigger.isBefore` × `Trigger.isInsert` decision tree once.
3. **Sharing a single helper method that takes `Trigger.new` as a
   parameter across all events.** The helper either crashes in
   delete contexts (where `Trigger.new` is null) or has to defensively
   check `Trigger.isDelete ? Trigger.old : Trigger.new` at every
   call site. Pass the right collection at the call site, or split
   the helper.
4. **Manual recursion guards via ad-hoc `static Boolean isFirstRun`
   flags scattered across handlers.** Each handler's guard works
   in isolation; together they interleave incorrectly when one
   trigger's DML fires another trigger that fires the first again.
   Use the centralized `TriggerHandler.skipOnce()` + depth counter
   in the canonical template.
5. **Treating `Trigger.newMap` as "a Map for convenience" in
   `before insert`.** It doesn't exist there — the records have no
   Ids yet. Iterate `Trigger.new` directly; key by external Id if
   you need a within-batch lookup.

## Official Sources Used

- Apex Developer Guide — Trigger Context Variables:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_context_variables.htm
- Apex Developer Guide — Triggers:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers.htm
- Apex Developer Guide — Triggers and Order of Execution:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Apex Developer Guide — Bulk Triggers / Bulk Design Patterns:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_bulk.htm
- Salesforce Well-Architected — Adaptable (Resilient):
  https://architect.salesforce.com/well-architected/adaptable/resilient
- Salesforce Well-Architected — Trusted (Secure):
  https://architect.salesforce.com/well-architected/trusted/secure
