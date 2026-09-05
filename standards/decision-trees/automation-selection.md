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
    ├── Yes, but the field is OwnerId (or an acknowledgement, or an SLA
    │        clock) on a Case or a Lead                               → Q13
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

## Native rule engines on Case and Lead (Q13–Q15)

Reached from Q2, because the platform ships a rule engine for exactly one
same-record write: the owner of a new Case or Lead, plus the acknowledgement and
the SLA clock that hang off it. These are configuration, not automation you
build, and they are **object-limited**: assignment and auto-response rules exist
only on Lead and Case, escalation rules and entitlement processes only on Case.
On any other object this whole branch is unavailable — go back to Q3 and set
`OwnerId` in a before-save Flow or in Apex. The full comparison, including
territories and lead scoring, is in `admin/assignment-rules` →
`references/routing-selector.md`.

```
Q13. Which native rule engine on Case or Lead owns this write?
     ├── The first owner comes from an ordered criteria table
     │   of field values                                          → Assignment Rules · `admin/assignment-rules`
     ├── The record is already in a queue and must reach whichever
     │   agent is online and under capacity                       → Omni-Channel · `admin/omni-channel-routing-setup`
     ├── The submitter must be acknowledged by email as the
     │   record is created                                        → Auto-Response Rules · `admin/assignment-rules`
     ├── The record arrives from an inbound intake channel        → Q14
     ├── Something must happen because time has passed            → Q15
     └── Not Case or Lead, or the criteria need code              → Q3

Q14. Which intake channel creates the Case?
     ├── Customer email to a monitored routing address            → Email-to-Case · `admin/email-to-case-configuration`
     ├── An HTML form posted from a public website                → Web-to-Case · `admin/case-management-setup`
     └── More than one channel, or no channel inventory yet       → `admin/case-management-setup` first,
                                                                    then re-enter at Q13 for the owner write

Q15. What does the passage of time have to do?
     ├── Re-route or notify when an open Case ages past a
     │   threshold                                                → Escalation Rules · `admin/escalation-rules`
     ├── Track a contractual response or resolution target on a
     │   clock that can pause outside business hours              → Entitlement milestones · `admin/entitlements-and-milestones`
     └── Neither — it is a recurring job on a wall clock          → see Q10
```

### Why each leaf, and where it sits in the save order

Line references below are to the Apex Developer Guide's *Triggers and Order of
Execution* list; positions are the guide's own numbering.

- **Assignment Rules** (`admin/assignment-rules`) — take this leaf when the first
  owner is a function of field values on the new record. The engine is an
  ordered criteria table an admin maintains in Setup; a Flow that sets `OwnerId`
  re-implements that table as branching logic and loses the entry-order audit
  trail. Assignment rules run at **position 9** of the save order (apexdev.txt
  L15449), after all after triggers and *before* after-save record-triggered
  flows at position 14 (L15470) — so a before-save Flow that sets `OwnerId` is
  simply overwritten when the rule fires. For inserts from Apex or the API the
  rule fires only when the caller asks for it
  (`Database.DMLOptions.assignmentRuleHeader.useDefaultRule`), which is the most
  common "the rule didn't run" cause.
- **Omni-Channel** (`admin/omni-channel-routing-setup`) — take this leaf when the
  question is *who is free*, not *which team*. Assignment rules pick a queue and
  never a person inside it, and an Apex round-robin ignores presence entirely;
  Omni-Channel is the only native mechanism that reads presence status and
  capacity weight. It sits **on top of** the assignment rule rather than instead
  of it: the rule lands the Case in the queue, Omni-Channel pushes it to an
  agent. Point it at every Case with no rule underneath and the criteria audit
  trail disappears.
- **Auto-Response Rules** (`admin/assignment-rules`, templates in
  `admin/email-templates-and-alerts`) — take this leaf for the acknowledgement
  only. It runs at **position 10** (apexdev.txt L15450), immediately after the
  assignment rule, and is evaluated in the same pass — so an acknowledgement is
  only as reliable as the assignment rule above it, and it cannot be bolted on
  to a channel the rule does not cover. The sender must never be an
  Email-to-Case routing address, or every reply creates a Case.
- **Web-to-Case and Email-to-Case** (`admin/email-to-case-configuration`,
  `admin/case-management-setup`) — take this leaf when the question is intake,
  not routing. These channels decide what the record looks like when it reaches
  position 9, and they carry their own limits and failure modes (Web-to-Case's
  daily cap and shared pending-request queue; Email-to-Case threading and
  discard-vs-bounce). Ownership belongs in the assignment rule reading
  `Case.Origin` per address, not in the channel's own owner field, which writes
  a single org-level default that a second routing address overwrites.
- **Escalation Rules** (`admin/escalation-rules`) — take this leaf when nothing
  changed and time alone must trigger the reaction. Escalation rules run at
  **position 12** (apexdev.txt L15461) and then on their own timer against
  business hours; a scheduled Flow polling for aged Cases re-implements that
  engine, and it will not honour the per-entry `businessHoursSource` or the
  `escalationStartTime` choice between case creation and last modification.
- **Entitlement milestones** (`admin/entitlements-and-milestones`) - take this
  leaf when the target is contractual and must be *tracked and reported*, not
  just acted on. Entitlement rules run at **position 15** (apexdev.txt L15471),
  the only one of these engines that runs *after* after-save record-triggered
  flows (position 14, L15470), so a Flow in the same save can still influence
  what the process sees. Note the dependency the other channels create: neither
  Email-to-Case nor Web-to-Case supplies an entitlement, so a case-intake design
  that stops at the channel tracks nothing until something assigns one.

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
- `admin/assignment-rules` — Lead/Case ownership on create is a rule engine, not a Flow; its `references/routing-selector.md` covers rules vs Omni-Channel vs Flow vs Apex vs territories
- `admin/omni-channel-routing-setup` — Q13's availability/capacity leaf; runs on top of an assignment rule, not instead of it
- `admin/escalation-rules` — Q15's time-based re-route leaf (Case only)
- `admin/entitlements-and-milestones` — Q15's SLA-clock leaf; the only engine that runs after after-save flows
- `admin/email-to-case-configuration` — Q14's email intake leaf
- `admin/case-management-setup` — Q14's Web-to-Case leaf and the channel inventory the whole branch assumes
- `admin/email-templates-and-alerts` — the template an Auto-Response Rule sends

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
- Apex Developer Guide — Triggers and Order of Execution (assignment rules position 9, auto-response rules 10, escalation rules 12, after-save record-triggered flows 14, entitlement rules 15): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
