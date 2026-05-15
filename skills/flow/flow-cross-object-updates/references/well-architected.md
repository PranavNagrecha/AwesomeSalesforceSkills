# Well-Architected Notes — Flow Cross-Object Updates

## Relevant Pillars

Cross-object writes from Flow are deceptively simple — the platform
makes them easy enough that practitioners build them without
thinking through the architectural consequences. Four pillars carry
weight; the dominant one is Scalability because Flow's
auto-bulkification is real but conditional.

- **Scalability** — Flow auto-bulkifies cross-object DML only when
  the element is *outside a Loop*. The single most common scaling
  failure in Flow is "Update Records inside Loop" — see
  `examples.md` anti-pattern. Designing for 1-record bulk volume is
  trivial; designing for 200 is the actual requirement on any
  record-triggered flow that fires on standard SObjects.
- **Reliability** — Cross-object updates introduce the classic
  ping-pong recursion (parent flow stamps child, child flow stamps
  parent, repeat until platform kills the transaction at recursion
  depth 16). Without explicit guards, two innocuously-correct flows
  built by different teams compose into an outage.
- **Security** — Flows run in system context by default, which means
  a community-user-triggered flow can write fields the user has no
  permission to see. This is a real, recurring security finding in
  most orgs; the mitigation (`System Context with Sharing` + explicit
  FLS checks) requires per-flow configuration, not a tenant-wide
  default.
- **Operational Excellence** — Cross-object writes are
  *runtime-discoverable*: the only way to find every cross-object
  write in an org is to inspect every flow. Documenting the
  parent↔child write graph in a place ops can audit (a custom
  metadata type, a shared spreadsheet, a Confluence page) is the
  difference between "we can diagnose the recursion in 10 minutes"
  and "we have to read every flow in the org."

## Architectural Tradeoffs

The defining tradeoff is **Flow vs Apex for the cross-object write**:

| Dimension | Flow (cross-object write) | Apex Trigger Handler |
|---|---|---|
| Time-to-build | Hours | Day+ (including tests) |
| Auto-bulkification | Yes, with caveats | Manual but explicit |
| Recursion guard | Manual (transient flag) | Static-bool / TriggerControl |
| Mode (sharing/FLS) | Per-flow property | `with sharing` / `Security.stripInaccessible` |
| Debug-ability | Flow Debug log; reasonable | Apex Debug Log; gold standard |
| Cross-team change risk | Lower (visible in Flow Builder) | Higher (requires code review) |
| Best for | Single owner, well-bounded scope | Complex logic, high volume, deep nesting |

The "right" answer is rarely "Flow for everything" or "Apex for
everything" — it's "Flow for the simple cases, Apex for the
complex ones, with a clear handoff rule." The handoff rule that
works in practice: **switch to Apex when the cross-object write
needs to enforce non-trivial CRUD/FLS, when the recursion guard
needs to span multiple flows/triggers, or when bulk volume
consistently exceeds 1,000 records per transaction.**

A second tradeoff: **Get Records vs dot-notation traversal**.
Dot-notation (`{!$Record.Account.Industry}`) reads up to 5 levels
of lookups in memory — zero SOQL cost. Get Records issues a SOQL
query, which is bulkified but still chews a SOQL slot. For
*read-only* parent fields, always prefer dot-notation. For
*reads where you'll subsequently filter or aggregate* (e.g., "all
related Contacts where MailingState = 'CA'"), Get Records is the
only option; dot-notation can't iterate.

A third tradeoff: **single trigger flow with multiple Decisions vs
multiple narrowly-scoped flows on the same object**. The first
keeps logic colocated and easier to debug; the second has clearer
ownership and easier ISCHANGED/ISNEW guarding. Salesforce's official
guidance leaned toward "one record-triggered flow per object per
trigger context" but that pattern produces god-flows; the modern
consensus (per Architect Day 2025 sessions) is "small flows, named
clearly, with strict entry conditions." For cross-object updates
specifically, narrow-scoped flows make the recursion guard work
easier — each flow's entry condition can be tight enough to
exclude the changes the *other* flow produces.

## Anti-Patterns

1. **Update Records inside a Loop element.** Single largest cause of
   Flow governor-limit failures. See `examples.md` anti-pattern.
2. **Get Records when dot-notation suffices.** Wastes a SOQL slot
   per read. Dot-notation traverses up to 5 levels of lookups in
   memory; only fall back to Get Records when the data needed is
   beyond traversal scope (related child records, or > 5 lookups
   deep).
3. **Trusting Flow's default sharing mode.** Defaults vary by
   release. Set the flow's "How to Run" property explicitly,
   especially for flows triggered by community/portal users.
4. **Bidirectional parent↔child writes with no recursion guard.**
   Eventually loops until the platform kills the transaction at
   recursion depth 16. Use entry conditions tight enough to break
   the cycle, or a transient flag during the first pass.
5. **Reading a child-modified field in a parent flow without
   guarding ISCHANGED.** Same issue as the parent↔child loop, in
   a slightly different costume.

## Official Sources Used

- Flow Builder Reference — Update Records element:
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_update_records.htm
- Flow Builder Reference — Bulkification in Record-Triggered Flows:
  https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger.htm
- Apex Developer Guide — Order of Execution:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Flow Builder Reference — How a Flow Runs in System or User Context:
  https://help.salesforce.com/s/articleView?id=sf.flow_concepts_running_context.htm
- Salesforce Well-Architected — Adaptable (Resilient):
  https://architect.salesforce.com/well-architected/adaptable/resilient
