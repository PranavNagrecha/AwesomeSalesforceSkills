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
| Mode (sharing/FLS) | Per-flow property | Trigger: fixed `without sharing`, per-operation access mode; handler: sharing keyword + `Security.stripInaccessible` — version-gated, see note |
| Debug-ability | Flow Debug log; reasonable | Apex Debug Log; gold standard |
| Cross-team change risk | Lower (visible in Flow Builder) | Higher (requires code review) |
| Best for | Single owner, well-bounded scope | Complex logic, high volume, deep nesting |

**Note on the Apex "Mode" row.** Sharing and access mode are two
independent axes, and collapsing them into one is the usual mistake.

*The sharing declaration is fixed.* A `.trigger` file can't carry an explicit
sharing declaration, and always runs implicitly in a `without sharing` context
— bypassing the current user's sharing rules. The Apex Developer Guide states
this with no version qualifier, and no keyword can be added to the trigger to
change it. Note the scope of that sentence carefully: what is fixed is the
*declaration*, not the record visibility of every operation inside the
trigger. The access mode of each database operation can still override it —
see below.

*Access mode is not fixed.* Database operations in the trigger body — SOQL
queries, SOSL queries, DML statements, and `Database` methods — run in **user
mode unless system mode is explicitly specified**. A query with no access-mode
clause therefore behaves as `WITH USER_MODE`: object- and field-level
permissions are enforced, and user mode reapplies the running user's record
sharing, effectively enforcing a `with sharing` context in the trigger body.
That default is gated on the `apiVersion` in the trigger's
`.trigger-meta.xml`, the same way the handler's is gated on its
`.cls-meta.xml` — the guide's worked trigger example is labeled *API version
67.0 and later*. To opt out per operation, use `WITH SYSTEM_MODE`, `as
system`, or `AccessLevel.SYSTEM_MODE`. Worth stating to a reviewer, because it
is the axis people expect to move and it doesn't: under `WITH SYSTEM_MODE` the
object- and field-level checks are bypassed, but record sharing stays governed
by the trigger's own `without sharing` context, so all records remain visible
regardless of the running user.

The handler class the trigger delegates to is gated the same way, on the
`apiVersion` in its `.cls-meta.xml` rather than the org's release: at
**67.0+** (Summer '26) a handler with *no* sharing keyword runs `with sharing`
and its SOQL/DML default to user mode; at **66.0 and below** both default the
other way, so a handler pinned to 58.0 in a Summer '26 org keeps the old
behavior. Canonical table:
[`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md)
§ *Apex security idiom by API version*.

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

Guides read as extracted text; every line number below is a `grep -n` into that
extract. PDF URLs are the canonical form of the same documents.

- **Metadata API Developer Guide**, `Flow` / `FlowStart` / `FlowRecordUpdate` /
  `FlowRecordLookup` / `FlowTest` sections —
  <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf>.
  Supports: the two Update Records modes and that `object` is Required (L71264–71292);
  `doesRequireRecordChangedToMeetCriteria` and `filterFormula` as the cycle-breakers
  (L72322–72326, L72390–72393); `getFirstRecordOnly` / `limit` /
  `assignNullValuesIfNoRecordsFound` preconditions (L71100–71110, L71153–71163,
  L71177–71185); `runInMode` semantics and version floor, which corrects this package's
  earlier "system context by default" claim (L68374–68390); `FlowTest` shape, suffix and
  `testType` (L73976–73980, L74041–74050, L74303–74308).
- **Metadata API Developer Guide**, `CustomField` section — same PDF. Supports: roll-up
  summaries require a master-detail relationship (`summaryForeignKey`, L43648–43650);
  `summaryOperation` values and the `summarizedField` rule (L43636–43638, L43651–43666);
  `deleteConstraint` values with `SetNull` as the default (L43347–43357);
  `reparentableMasterDetail` and `relationshipOrder` (L43582–43597);
  `writeRequiresMasterRead` and its restrictive default (L43724–43738).
- **Metadata API Developer Guide**, `deploy()` call — same PDF. Supports the
  MasterDetail↔Lookup deploy hazards in `gotchas.md` Gotcha 6: unsupported under
  `checkOnly`, and permanent deletion of detail records from the Recycle Bin
  (L4177–4213).
- **Apex Developer Guide**, *Triggers and Order of Execution* —
  <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf>.
  Supports: a flow's DML re-enters the save procedure (L15468); after-save flows at step
  14 (L15470); roll-up recalculation at steps 16–17 with the parent and grandparent
  re-saved (L15471–15477); and the recursive-save skip of steps 9–17 that makes a
  roll-up untrustworthy mid-transaction (L15414–15415).
- **Apex Developer Guide**, *Execution Governors and Limits* — same PDF. Supports every
  number quoted in this package: 100 SOQL and 150 DML per synchronous transaction
  (L19542, L19550), 10,000 records processed by DML (L19556), stack depth 16 for
  recursive trigger firing (L19559), 10,000 ms synchronous CPU (L19579).
- **Apex Developer Guide**, *Debug Log Levels* / flow event types — same PDF. Supports
  the ping-pong verification in `references/metadata-examples.md` § 10:
  `FLOW_CREATE_INTERVIEW_BEGIN` logs the definition and version ID (L38759–38761),
  `FLOW_START_INTERVIEWS_BEGIN`/`_END` log "Requests" (L38856–38861),
  `FLOW_ELEMENT_BEGIN` logs the element name (L38768–38770), and `LIMIT_USAGE_FOR_NS`
  closes the log (L38275).
- **Bulk API 2.0 Developer Guide**, *Organize Data to Minimize Lock Contention* —
  <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_asynch.pdf>.
  Supports `gotchas.md` Gotcha 7: a child insert locks its parent for the transaction,
  sorting the load by parent Id is the mitigation (L2688–2707), plus the Bulk API 1.0
  retry and serial-mode behaviour (L4997–5010).
- **Salesforce App Limits Cheat Sheet**, SOQL relationship limits —
  <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf>.
  Supports the correction to this package's "5 levels of traversal" claim: the five-level
  ceiling is documented for SOQL child-to-parent relationships (L1143–1146), and the Flow
  figure is a help.salesforce.com claim carrying an UNVERIFIED marker in `SKILL.md`.
- **Salesforce Well-Architected — Adaptable (Resilient)** —
  <https://architect.salesforce.com/well-architected/adaptable/resilient>. Supports the
  Reliability framing above: two independently correct automations composing into a loop.

- **Apex Developer Guide**, *Using the with sharing, without sharing, and inherited
  sharing Keywords* § Implementation in Apex Triggers — same PDF. Supports the "Mode" row
  of the Flow-vs-Apex table above: "Apex triggers can't have an explicit sharing
  declaration. Triggers always run implicitly in a without sharing context", and database
  operations in the trigger body "run in user mode unless system mode is explicitly
  specified. User mode overrides the trigger's without sharing context"
  (`apexdev.txt` L4880–4886).

### Sources previously listed here that could not be re-verified

The bullets below are help.salesforce.com articles. help.salesforce.com cannot be
fetched from this repo, so nothing in this package rests on them any longer; the claims
they used to support have either been re-grounded above or carry an UNVERIFIED marker
beside them.

- Flow Builder Reference — Update Records element (`sf.flow_ref_elements_update_records`)
- Flow Builder Reference — Bulkification in Record-Triggered Flows (`sf.flow_concepts_trigger`)
- Flow Builder Reference — How a Flow Runs in System or User Context (`sf.flow_concepts_running_context`)
- Summer '26 Release Notes — Database Operations Run in User Mode by Default (API 67.0);
  the API-version gate itself is recorded in `agents/_shared/AGENT_CONTRACT.md`
