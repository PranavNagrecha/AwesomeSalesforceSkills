# Decision Tree — Flow Pattern Selection

Once `automation-selection.md` has routed you to **Flow**, which *kind* of Flow do you build?
**Before-Save Record-Triggered · After-Save Record-Triggered · Scheduled-Path · Autolaunched · Screen · Scheduled Flow · Orchestration · Platform-Event-Triggered**

Use this tree AFTER the automation-selection tree has said "Flow", and BEFORE activating a Flow skill.

---

## Strategic defaults

1. **Same-record field derivation** → Before-Save record-triggered. Cheapest element; no DML.
2. **Cross-record or related-record work** → After-Save record-triggered.
3. **SLA / reminders / time-delayed actions** → After-Save record-triggered with a Scheduled Path.
4. **User-facing wizard / guided data entry** → Screen flow.
5. **Called by other flows or Apex** → Autolaunched flow with API version pinned.
6. **Nightly / weekly batch work** → Scheduled flow (Flow Trigger Explorer) with bounded record count.
7. **Human approval workflow with multiple stages** → Orchestration.
8. **Reacting to a decoupled domain event** → Platform-Event-triggered flow.

---

## Decision tree

```
START: Entry requirement classified as "Flow" by automation-selection.md.

Q1. What fires the flow?
    ├── A record INSERT or UPDATE                                       → Q2
    ├── A user interaction (button / tab / utility bar / URL)           → Screen flow
    ├── Another flow or Apex calling it                                 → Autolaunched flow
    ├── A clock (nightly, hourly, monthly)                              → Q6
    ├── A Platform Event on the event bus                               → Platform-Event-triggered flow
    └── A human completing a stage (approval / review / sign-off)       → Orchestration

Q2. Do you only set fields on the SAME record that triggered the flow?
    ├── Yes  → Q3
    └── No   → Q4

Q3. Do you need any DML, callouts, or cross-object lookups?
    ├── No   → Before-Save record-triggered flow (run 90–98% cheaper than After-Save)
    └── Yes  → After-Save record-triggered flow

Q4. Do you need the action to happen strictly after the triggering DML commits
    (e.g. create a child record, post to Chatter, send an email)?
    ├── Yes  → After-Save record-triggered flow
    └── No   → Reconsider Before-Save vs After-Save with Q3

Q5. Does the action need to happen at a specific time RELATIVE to the record
    (e.g. "30 days after Close Date", "1 hour before SLA breach")?
    ├── Yes  → After-Save record-triggered flow with Scheduled Path (entry criteria gates the schedule)
    └── No   → Same record-triggered flow fires inline

Q6. Is the cadence daily / weekly / monthly AND does it process a bounded
    record set (< 50k) with a predictable query?
    ├── Yes, < 250k rows and runs under 10min        → Scheduled flow
    ├── Yes, > 250k rows or need chunked processing  → Apex Scheduled + Batchable (escalate out of Flow)
    └── No, cadence is event-driven, not clock-driven → re-route at Q1

Q7. Screen flow sub-branch: is the user PAUSING mid-flow (days/weeks between steps)?
    ├── No, completes in one session                 → Standard screen flow
    └── Yes, resumes later                           → Orchestration OR screen flow + pause element
                                                       (see `flow-transactional-boundaries` for boundary
                                                       implications — pause breaks the transaction)

Q8. Autolaunched sub-branch: is the caller Apex (@InvocableMethod/Flow.Interview.callFlow)?
    ├── Yes, called from Apex  → Autolaunched flow; see `flow-invocable-from-apex`
    └── Yes, called from another flow (subflow)      → Autolaunched flow; see `subflows-and-reusability`

Q9. Platform-Event sub-branch: is the event defined as High-Volume or Standard?
    ├── High-Volume  → Platform-Event-triggered flow, but beware replay + ordering semantics
    └── Standard     → Platform-Event-triggered flow with back-pressure guardrails
                       (see `flow-platform-events-integration`)
```

---

## Cross-type guidance

### Performance ranking (cheapest to most expensive, same work)

1. Before-Save record-triggered (no DML, no SOQL on the record itself)
2. After-Save record-triggered (adds DML)
3. Autolaunched (adds Interview context)
4. Screen flow (adds UI render + session)
5. Orchestration (adds stage state persistence)

Rule of thumb: **a Before-Save flow that does field derivation is 10–50× cheaper per
record than an After-Save flow doing the same work.** Use Before-Save whenever the
work stays on the triggering record.

### When to split a single requirement across multiple Flow types

| Requirement | Pattern |
|---|---|
| Derive fields THEN create a child record | Before-Save (fields) + After-Save (child create) |
| Screen wizard THAT takes long to complete | Screen flow + Orchestration for multi-day workflows |
| Record-triggered work THAT must be async | After-Save + Scheduled Path (1 minute delay) |
| Scheduled cleanup THAT touches many records | Scheduled flow (if < 250k) or Apex Batchable |
| Decoupled event fan-out | Platform-Event-triggered flow + publisher flow |

### Transaction boundary summary

| Flow Type                          | New transaction? | Governor limits shared with? |
|------------------------------------|------------------|------------------------------|
| Before-Save record-triggered       | No (inline)      | Triggering DML               |
| After-Save record-triggered        | No (inline)      | Triggering DML + other after-save automations |
| After-Save with Scheduled Path     | Yes              | Fresh limits                 |
| Autolaunched from Apex             | No               | Calling Apex transaction     |
| Autolaunched from another flow     | No               | Parent flow transaction      |
| Screen flow                        | Per-commit       | Each DML is its own batch    |
| Screen flow with pause element     | Yes after pause  | Fresh limits after resume    |
| Scheduled flow                     | Yes              | Fresh limits                 |
| Platform-Event-triggered           | Yes              | Fresh limits                 |
| Orchestration stage                | Per stage        | Each stage is fresh          |

See `skills/flow/flow-transactional-boundaries` for the full analysis.

### Don't-do list

- **Don't use Before-Save for DML work.** The element set doesn't support it and the pattern is unsafe.
- **Don't nest autolaunched inside a Before-Save record-triggered flow** — the child flow runs in the same limited context.
- **Don't schedule a flow that queries > 250k records.** Flow scheduled execution has a soft limit; escalate to Batchable Apex.
- **Don't use a screen flow pause element to fake "wait for external call".** Use a Platform Event subscriber instead.
- **Don't chain more than 2 after-save record-triggered flows on the same object** — the transaction limit stacks fast.

---

## Skills to activate after this tree

| Branch                            | Activate skill                                       |
|-----------------------------------|------------------------------------------------------|
| Before-Save record-triggered      | `skills/flow/record-triggered-flow-patterns`         |
| After-Save record-triggered       | `skills/flow/record-triggered-flow-patterns`         |
| After-Save + Scheduled Path       | `skills/flow/record-triggered-flow-patterns` + `skills/flow/scheduled-flows` |
| Autolaunched (from flow)          | `skills/flow/subflows-and-reusability`               |
| Autolaunched (from Apex)          | `skills/flow/flow-invocable-from-apex`               |
| Screen flow                       | `skills/flow/screen-flows`                           |
| Scheduled flow                    | `skills/flow/scheduled-flows`                        |
| Orchestration                     | `skills/flow/orchestration-flows`                    |
| Platform-Event-triggered          | `skills/flow/flow-platform-events-integration`       |
| Transaction boundary question     | `skills/flow/flow-transactional-boundaries`          |

Shared follow-ups for every branch:
- `skills/flow/fault-handling` — every flow needs a fault path
- `skills/flow/flow-bulkification` — every record-triggered flow needs bulk-safe design
- `skills/flow/flow-testing` — every flow needs coverage

---

## Official Sources Used

- Salesforce Help — Flow Trigger Types: https://help.salesforce.com/s/articleView?id=sf.flow_ref_triggers.htm
- Salesforce Help — Decide Whether to Build a Flow or an Apex Trigger: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger.htm
- Salesforce Architects — Enterprise Automation Guide: https://architect.salesforce.com/design/architecture-framework/well-architected
- Salesforce Developer — Flow Runtime: https://developer.salesforce.com/docs/atlas.en-us.salesforce_vpm_guide.meta/salesforce_vpm_guide/
