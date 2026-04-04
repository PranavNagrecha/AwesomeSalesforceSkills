# Pause Elements and Wait Events — Work Template

Use this template when designing or reviewing a flow that uses a Pause (Wait) element.

---

## Scope

**Skill:** `pause-elements-and-wait-events`

**Request summary:** (fill in what the user asked for — e.g., "Add a 3-day reminder pause to the onboarding flow", "Replace polling with a platform event wait")

---

## Context Gathered

Answer these before designing the Pause element:

- **Flow type:** [ ] Auto-launched [ ] Screen flow (user-initiated pause) — NOT record-triggered with scheduled path need
- **Resume trigger type:** [ ] Alarm (time-based) [ ] Platform Event (event-driven) [ ] Both
- **Alarm details (if applicable):**
  - Base date field: `{! }` — (must be a Date or DateTime field that is always populated)
  - Offset amount and unit: _____ [ ] Hours [ ] Days [ ] Months
  - Business hours enforcement needed: [ ] Yes [ ] No
- **Platform event details (if applicable):**
  - Platform event API name: `_______________`
  - Resume condition fields and values:
    - Field: `_______________` Operator: `=` Value: `{! }`
    - Field: `_______________` Operator: `=` Value: `{! }` (add more rows as needed)
  - Record variable to capture payload: `{! }` (leave blank if event payload not needed)
- **Timeout watchdog needed:** [ ] Yes — Alarm offset: _____ hours [ ] No (explain why permanent wait is acceptable)
- **Expected concurrent paused interview volume:** _____ (compare to org limit)
- **Known constraints:** (e.g., business hours, external system SLA, record ownership rules)
- **User context on resume:** [ ] Running user [ ] Automated Process user (platform event resume)

---

## Approach

Which pattern from SKILL.md applies?

- [ ] **Multi-Day Reminder / Escalation** — multiple Alarm wait events, loop back on reminder path
- [ ] **Event-Driven Handoff** — Platform Event wait event with correlation ID resume condition
- [ ] **Hybrid** — both Alarm and Platform Event wait events (first-wins race)
- [ ] **Custom** — describe: _______________

Why this pattern over alternatives:

---

## Pause Element Design

```
Pause Element: "[ name this element clearly ]"
  |
  ├── Wait Event 1 — [ Alarm | Platform Event ]
  │     [ Alarm: Base date field = {!  }, Offset = N [Hours|Days|Months] ]
  │     [ Platform Event: EventName__e, Conditions: Field__c = {!  } ]
  │     [ Stores event in variable: {!  } ]
  │     Output path: → [ describe downstream action ]
  │
  ├── Wait Event 2 — [ Alarm | Platform Event ]
  │     [ ... ]
  │     Output path: → [ describe downstream action ]
  │
  └── Fault path → [ error handler / notification ]
```

---

## Resume Condition Verification

For each Platform Event wait event, verify uniqueness of the resume condition combination:

| Event Field | Operator | Flow Variable | Uniqueness Guarantee |
|---|---|---|---|
| `___Field__c` | `=` | `{! }` | (explain why this combination uniquely identifies this interview) |

---

## Testing Plan

| Scenario | How to Test | Expected Outcome |
|---|---|---|
| Alarm fires at correct time | Set offset to 0 days on test record; wait ~15 min | Interview completes; alarm output path executed |
| Platform event resumes correct interview | Publish test event via Apex: `EventBus.publish(...)` with correct field values | Only the target interview resumes; event payload captured in variable |
| Platform event with wrong field values does NOT resume interview | Publish event with non-matching field values | Interview remains paused; no spurious resume |
| Timeout watchdog fires if event never arrives | Do not publish the platform event; wait for alarm | Timeout output path executed; error handler runs |
| Fault path fires on resume error | Simulate DML failure in resume path (e.g., required field missing) | Fault path executes; interview does not remain in failed state silently |

---

## Checklist

Work through these before marking the design complete:

- [ ] Flow type is auto-launched or screen flow — not a record-triggered flow where a scheduled path would suffice
- [ ] Each Platform Event wait event has at least one resume condition that uniquely links the event to this interview's record
- [ ] Alarm base date field is always populated on the record at the time of pause
- [ ] Fault path is connected from the Pause element to a meaningful error handler
- [ ] A timeout Alarm wait event is present alongside every Platform Event wait event
- [ ] Async interview volume estimated and confirmed acceptable against org limit
- [ ] Testing plan does not rely on Flow Builder debug — uses real event triggers or manual Alarm timing
- [ ] Flow version activation strategy is documented for deployments while interviews may be paused

---

## Notes

Record any deviations from the standard pattern and why:

- Deviation: _______________  Reason: _______________
