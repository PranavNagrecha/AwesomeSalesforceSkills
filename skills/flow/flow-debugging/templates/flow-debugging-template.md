# Flow Debugging — Work Template

Use this template when diagnosing a broken, silent, or misbehaving Salesforce Flow.

---

## 1. Scope

**Flow name / API name:** (fill in)

**Flow type:** [ ] Record-triggered (before-save) [ ] Record-triggered (after-save) [ ] Screen [ ] Scheduled [ ] Autolaunched

**Symptom:**
- [ ] Flow is not firing at all
- [ ] Flow fires but takes the wrong path
- [ ] Flow produces wrong output / wrong field values
- [ ] Flow fails with a fault email
- [ ] Flow fails silently (no email, no visible error)
- [ ] Other: ______

**Environment:** [ ] Sandbox (debug mode available) [ ] Production (Interview Log + fault email only)

**Reported by / ticket:** (fill in)

---

## 2. First Check: Is the Right Version Active?

- [ ] Opened flow in Flow Builder
- [ ] Confirmed active version number: ___
- [ ] Confirmed no more recent version exists that is inactive

---

## 3. Entry Conditions Review (record-triggered flows only)

| Check | Finding |
|---|---|
| Trigger object | |
| Trigger event (create / update / create+update) | |
| Entry condition evaluation (every save / only when updated to meet) | |
| Entry conditions (field = value filters) | |
| Run As setting (system context / user context) | |

- [ ] Entry conditions match the expected triggering scenario
- [ ] "Only when updated to meet" vs "every save" is correct for the use case

---

## 4. Fault Email Analysis (if applicable)

**Fault email received:** [ ] Yes [ ] No

If yes, record:

| Field | Value |
|---|---|
| Flow API name from email | |
| Element name from email | |
| Error category (e.g., FIELD_INTEGRITY_EXCEPTION) | |
| Error detail message | |

**Mapped root cause:**

- [ ] Required field not populated
- [ ] Validation rule blocking DML
- [ ] Duplicate rule triggered
- [ ] Insufficient access on related record
- [ ] Element misconfiguration (FLOW_ELEMENT_ERROR)
- [ ] Other: ______

---

## 5. Debug Session Plan

**Only complete if debugging in sandbox:**

Matching record field values to set in debug:

| Field | Value to set |
|---|---|
| | |
| | |

- [ ] "Roll back changes after the debug run" is checked (for after-save flows with DML)
- [ ] Run As is set to a user that reproduces the failing scenario (if the issue is user-specific)

Debug session result:

| Element | Outcome | Variable values / decision branch taken |
|---|---|---|
| | | |
| | | |
| Failing element | | |

---

## 5b. Capture Rig (production, or any data-dependent bug)

| Setting | Value used | Confirmed from the log header? |
|---|---|---|
| `Workflow` category level | | [ ] header reads `WORKFLOW,<level>` |
| Other categories | | [ ] all `NONE` except Validation |
| `TracedEntityId` (the saving user) | | |
| `StartDate` / `ExpirationDate` | | [ ] window <= the reproduction |
| `ApexLog.LogLength` of the captured log | | [ ] under 20,971,520 (not truncated) |

Event sequence read from the log:

| Line | Event | Element | What it told you |
|---|---|---|---|
| | `FLOW_START_INTERVIEWS_BEGIN` | n/a | flow started / did not start |
| | `FLOW_ELEMENT_FAULT` or `FLOW_ELEMENT_ERROR` | | the localising line |
| | `FLOW_RULE_DETAIL` | | branch that went wrong |
| | `FLOW_VALUE_ASSIGNMENT` | | value at the branch point |
| | `*_LIMIT_USAGE` | | limit pressure, if any |

Failure class: [ ] caught fault [ ] uncaught error [ ] wrong branch [ ] limit [ ] never started

---

## 6. Interview Records Review (when the log has expired)

- [ ] Queried `FlowInterview` on `InterviewStatus` / `Error` / `CurrentElement`
- [ ] Screen flow only: queried `FlowInterviewLog` + `FlowInterviewLogEntry`
      (these hold screen-flow interviews only; zero rows for other flow types is expected)
- [ ] Checked `FlowRecordRelation` for the record tied to a paused interview
- [ ] Identified the last element executed before the fault

Interview findings: (fill in)

---

## 7. Root Cause Summary

**Root cause identified:** (describe in one sentence)

**Layer:** [ ] Entry conditions [ ] Flow element configuration [ ] Data / validation rule [ ] Permission / sharing [ ] External dependency (Apex, integration)

---

## 8. Fix Applied

**Change made:** (describe)

**Verified by:** [ ] Debug session [ ] Flow Test Suite [ ] Manual testing in sandbox [ ] Interview Log in production after re-activation

---

## 9. Regression Check

- [ ] `FlowTest` written that reproduces the ORIGINAL failure (fails on the pre-fix flow)
- [ ] `sf flow run test` after fix — all assertions pass
- [ ] `python3 scripts/check_flow_debugging.py --manifest-dir <src> --strict` passes
- [ ] Trace flag deleted or expired
- [ ] Related flows and automation reviewed for side effects
- [ ] No paused interviews affected by version activation

---

## Notes

(Record any deviations from the standard pattern, unusual platform behaviors observed, or decisions made during the debugging session.)
