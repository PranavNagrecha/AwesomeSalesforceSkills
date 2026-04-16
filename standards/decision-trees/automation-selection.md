# Decision Tree — Automation Selection

Which automation tool should I use?
**Flow · Apex · Agentforce · Approvals · Platform Events · Batch · External**

Use this tree BEFORE activating any skill that proposes a specific technology.
Route once, then pick the skill.

---

## Strategic defaults (Salesforce's own guidance)

> Salesforce has retired Workflow Rules and Process Builder. New automation
> should be built in Flow, escalating to Apex only when Flow cannot meet the
> requirement. Agentforce replaces conversational user interfaces where the
> user's intent is ambiguous.

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
      - loops over 2,000+ records in-transaction
      - HTTP callouts
      - complex exception handling with rollback
      - recursive DML on the same object
      - unit tests with 90%+ coverage requirements
      - custom exception types exposed to calling code
    ├── Yes  → Apex (trigger + handler + service layer)
    └── No   → Q4

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
     └── No   → Scheduled Flow (simpler, but 2,000 record cap per interview)

Q11. External system → Salesforce data flow. Producer-controlled?
     ├── Must write into standard objects with logic     → REST API + Apex custom endpoint
     ├── Producer can publish events                     → Platform Event subscriber (Apex or Flow)
     ├── Large volume, one-way replication               → Bulk API 2.0 + ETL
     └── Producer is Salesforce itself → "Data I don't own" → External Objects / Salesforce Connect

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
| Mass reparent / reassign | Apex batch + `Database.setOptions` | Data Loader for one-offs | Flow (record limit will bite) |
| Approval chain | Approval Process → Flow post-approval | Flow with branching | Apex custom approval |

---

## Flow vs Apex — the honest boundary

You graduate from Flow to Apex when ANY of these is true:

- You would write > 15 Flow elements before reaching the first decision.
- You need a testable unit with > 75% coverage and assertion-style tests.
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

- **Workflow Rules / Process Builder for anything new.** Both are retired.
  Migrate on the next touch of the object.
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
- `flow/record-triggered-flows` — the Flow of choice for this tree
- `apex/trigger-framework` — where to go when Flow isn't enough
- `apex/async-apex` — paired with the async selection tree below
- `agentforce/agent-creation` — conversational automation
- `architect/platform-selection-guidance` — org-wide strategic defaults

## Related templates

- `templates/apex/TriggerHandler.cls` — when the tree resolves to Apex
- `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` — when it resolves to Flow
- `templates/agentforce/AgentActionSkeleton.cls` — when it resolves to Agentforce
