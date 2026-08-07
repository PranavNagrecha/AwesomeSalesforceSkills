# Decision Tree — Automation Selection (Flow vs Apex)

Which automation tool should I use?
**Flow · Apex · Agentforce · Approvals · Platform Events · Batch · External**

This is the canonical **flow vs apex** routing tree. Use it BEFORE
activating any skill that proposes a specific technology. Route once,
then pick the skill. Compare with `flow-pattern-selector` (picks which
type of Flow once you've decided on Flow) and `async-selection` (picks
which async Apex once you've decided on Apex).

---

## Strategic defaults (Salesforce's own guidance)

> Workflow Rules and Process Builder reached **end of support on 31 December
> 2025**. Existing rules and processes still run and can still be activated,
> deactivated, and edited — but they get no fixes and no enhancements, so build
> nothing new in them. New automation should be built in Flow, escalating to
> Apex only when Flow cannot meet the requirement. Agentforce replaces
> conversational user interfaces where the user's intent is ambiguous.

Defaults ranked most-to-least preferred for *new* work:

1. **Flow (record-triggered / screen / autolaunched)** — declarative, debuggable, admin-maintainable.
2. **Flow + Invocable Apex action** — when Flow covers orchestration but one step needs code.
3. **Apex (trigger + handler + service)** — when Flow's limits or expressiveness is insufficient.
4. **Agentforce topic + actions** — when the user expresses intent in natural language.
5. **Platform Events / CDC subscribers** — when the event producer and consumer are decoupled.
6. **External (MuleSoft, middleware)** — when orchestration crosses systems or is long-running.

---

## Decision tree

```
START: User or system needs to react to something.

Q1. What triggers the work?
    ├── A record change                                                 → Q2
    ├── A user clicking a button or filling a form                      → Q7
    ├── A natural-language request from a user                          → Agentforce topic + invocable Apex action
    ├── A scheduled clock ("every night at 2am")                        → Q10
    ├── An external system pushing data in                              → Q11
    └── An internal process emitting an event                           → Q12

Q2. Does the logic run in under ~10s and touch only fields on the record itself?
    ├── Yes  → Before-save record-triggered Flow
    └── No   → Q3

Q3. Does the logic require any of:
      - a loop whose per-record work would breach the per-transaction
        governor limits Flow shares with Apex (10 s CPU, 100 SOQL,
        150 DML statements, 10,000 DML rows, 50,000 rows queried)
      - callouts that need retry/backoff, chaining, or binary payloads
      - complex exception handling with rollback (savepoints)
      - recursive DML on the same object
      - a deployable unit under an enforced coverage gate with
        assertion-style tests (Apex needs 75% org-wide to deploy; Flow
        has no coverage gate at all)
      - custom exception types exposed to calling code
    ├── Yes  → Apex (trigger + handler + service layer)
    └── No   → Q4
    NOTE: one straightforward callout is NOT on this list. A single callout
    keeps you in Flow and resolves at Q6.

Q4. Does the logic need to cross objects (DML on related records, send email, create tasks)?
    ├── No   → After-save record-triggered Flow
    └── Yes  → Q5

Q5. Is the orchestration shape "linear with 1–2 decisions"?
    ├── Yes  → After-save record-triggered Flow
    └── No   → Q6

Q6. Does one specific step need code (regex, crypto, complex math, callout)
    but the orchestration is still simple?
    ├── Yes  → Flow + InvocableMethod Apex action
    └── No   → Apex (graduate to service layer)

Q7. Is the trigger a button on a record page or list view?
    ├── Yes (record page)    → Q8
    └── Yes (list view mass) → Q9

Q8. Can the action complete in under 10s without custom UI?
    ├── Yes  → Screen Flow with Quick Action OR simple Headless Quick Action (Flow)
    └── No   → LWC calling imperative Apex (see templates/lwc/patterns/imperativeApexPattern.js)

Q9. Does it need per-row input from the user?
    ├── No   → Screen Flow launched from List View (for < 200 records)
    └── Yes  → LWC + Apex for a custom bulk action UI

Q10. Scheduled job. Does it process > 50k records or run > 5 minutes?
     ├── Yes  → Batch Apex (see skills/apex/batch-apex-patterns)
     ├── 10k–50k, stateless, deterministic → Queueable with chained dispatch
     └── No   → Schedule-triggered Flow (simpler; one interview per record
                returned by the flow's query, org-wide cap of 250,000
                interviews per 24 h — or user licenses × 200, whichever is
                greater. The 50k routing line is this repo's opinion, not a
                platform limit; see flow-pattern-selector Q6.)

Q11. External system → Salesforce data flow. Producer-controlled?
     ├── Must write into standard objects with logic     → REST API + Apex custom endpoint
     ├── Producer can publish events                     → Platform Event subscriber (Apex or Flow)
     ├── Large volume, one-way replication               → Bulk API 2.0 + ETL
     └── Producer keeps ownership; Salesforce only reads → External Objects / Salesforce Connect

Q12. Internal event fan-out. Same-transaction or decoupled?
     ├── Same transaction, same object → Record-triggered Flow
     ├── Same transaction, other object → After-save Flow OR Apex service
     ├── Decoupled, within Salesforce   → Platform Event (immediate delivery)
     ├── Decoupled, external subscriber → Pub/Sub API + Platform Event/CDC
     └── Replication/audit elsewhere    → Change Data Capture
```

---

## Cheat sheet

| Requirement | First choice | Second choice | Never |
|---|---|---|---|
| Set a default value before save | Before-save Flow | — | Apex, Workflow Rule |
| Update related records after save | After-save Flow | Apex after-insert trigger | Process Builder |
| Call an HTTP API | Flow → Invocable Apex → `HttpClient` | Named Credential callout from Apex directly | Callout from Flow HTTP Callout action without retry/timeout review |
| Natural-language user request | Agentforce topic + action | Chatbot with custom LWC | Hard-coded button tree |
| Process 2M records nightly | Batch Apex | Queueable chain | Scheduled Flow |
| React to a record commit from 2 clouds | Platform Event | CDC + Apex trigger | Flow subscribing to CDC (supported but limited) |
| Mass reparent / reassign | Apex batch + `Database.DMLOptions` (set per record via `sObject.setOptions(...)`) | Data Loader for one-offs | Flow (the 24 h interview allocation will bite) |
| Approval chain | Approval Process → Flow post-approval | Flow with branching | Apex custom approval |

---

## Flow vs Apex — the honest boundary

You graduate from Flow to Apex when ANY of these is true:

- You would write > 15 Flow elements before reaching the first decision.
- You need a testable unit under an enforced coverage gate with
  assertion-style tests. Apex will not deploy to production below 75%
  org-wide coverage; Flow has no equivalent gate. (Same gate as Q3 — the
  two must not disagree.)
- You need a transaction rollback on a specific error class.
- You need to produce platform events conditionally on DML success.
- You need to do any cryptographic, regex, or binary operation.
- You are hitting `per-transaction SOQL query limit` or `DML statement limit` in Flow.
- You need to share the logic with 2+ call sites in different contexts.

Do NOT graduate to Apex because:

- "Flow is slow" — it isn't, for before-save operations.
- "Apex is cleaner" — subjective. Maintenance cost usually wins for admin-owned teams.
- "We already have an Apex framework" — that's a sunk cost, not a requirement.

---

## Anti-patterns

- **Workflow Rules / Process Builder for anything new.** Both hit end of
  support on 31 December 2025 — no fixes, no enhancements. They still
  execute, which is exactly why they rot silently. Migrate on the next
  touch of the object.
- **"One Flow per field."** Scales badly. Consolidate into one record-triggered
  flow per object with entry criteria decisions.
- **Apex for pure field defaulting.** Before-save Flow does this cheaper.
- **Agentforce when a button works.** Agents are for ambiguous intent — not
  for replacing a deterministic UI.
- **Calling Apex from Flow just to avoid Flow syntax.** If Flow can do it in
  one Assignment + one Update, use Flow.

---

## Related skills

- `admin/flow-for-admins` — declarative-first automation decisions
- `flow/record-triggered-flow-patterns` — the Flow of choice for this tree
- `apex/trigger-framework` — where to go when Flow isn't enough
- `apex/async-apex` — paired with the async selection tree below
- `agentforce/agentforce-agent-creation` — conversational automation
- `architect/platform-selection-guidance` — org-wide strategic defaults

## Related templates

- `templates/apex/TriggerHandler.cls` — when the tree resolves to Apex
- `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` — when it resolves to Flow
- `templates/agentforce/AgentActionSkeleton.cls` — when it resolves to Agentforce

## Official Sources Used

- Apex Developer Guide — Execution Governors and Limits (10 s sync CPU, 100 SOQL, 150 DML statements, 10,000 DML rows, 50,000 query rows): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide — Code Coverage ("unit tests must cover at least 75% of your Apex code, and those tests must pass"): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_code_coverage_intro.htm
- Salesforce Help — General Flow Limits (the 2,000 executed-elements limit was removed in API version 57.0; it applied in 56.0 and earlier): https://help.salesforce.com/s/articleView?language=en_US&id=sf.flow_considerations_limit.htm&type=5
- Salesforce Help — Schedule-Triggered Flow Considerations (250,000 interviews per 24 hours, or user licenses × 200, whichever is greater; one interview per queried record; batch size 200): https://help.salesforce.com/s/articleView?language=en_US&id=platform.flow_considerations_trigger_schedule.htm&type=5
- Salesforce Help — Workflow Rules & Process Builder End of Support (31 December 2025; existing automation keeps running): https://help.salesforce.com/s/articleView?id=001096524&language=en_US&type=1
- Apex Developer Guide — Setting DML Options (`Database.DMLOptions` applied with `sObject.setOptions(...)`): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_dml_database_dmloptions.htm
