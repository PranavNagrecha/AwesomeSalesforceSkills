# Severity Rubric + Finding-Code Convention

Every audit finding emitted by the router carries **exactly one severity** and **exactly one finding code**. Both are strict — downstream tooling (dashboards, CI gates, rollups) depends on them.

## Severity enum

| Severity | Meaning | Examples |
|---|---|---|
| **P0** | The org is broken or will break imminently under normal operation. A data load, a scheduled job, a user click, or a deploy will fail or produce incorrect data. Requires fix before any other audit action. | Inactive user is a required approver. Validation rule references a deleted field. Dashboard running user is inactive. |
| **P1** | The org works today but will break under predictable pressure (scale, off-hours deploys, new contributors). Or: real user-facing UX / governance damage is happening but isn't stopping the business yet. Fix in the current sprint. | Validation rule missing an integration bypass. Picklist dependency chain > 2 deep. Report with no filter on a 10M-row object. |
| **P2** | Hygiene / cosmetics / long-term maintainability. Not fixing this quarter does not harm the org. Bundle into a cleanup sprint. | Validation error message under 10 chars. Stale report never run in 12 months. Record-type description blank. |

### Severity escalation

A rule MAY escalate its own severity when context demands it. Classifiers declare escalation conditions explicitly in their rule tables, e.g. "P0 if on an object with > 1M records, else P1". Escalations must still resolve to exactly one of P0/P1/P2 — there is no P0+.

### What the enum is NOT

- **Not** a numeric score (no "P0.5"). Severity is discrete.
- **Not** a blocker flag (no "CRITICAL"). Callers who want a blocker do `any P0 findings? -> block`.
- **Not** an info / warn / debug level. If it doesn't deserve P2, it doesn't belong in the findings table — move it to Process Observations.

## Finding-code convention

Every finding carries a code of the form:

```
<DOMAIN>_<SUBJECT>_<CONDITION>
```

All upper-case, underscore-separated, no severity suffix (severity lives in its own field).

| Classifier domain | Prefix | Example |
|---|---|---|
| `validation_rule` | `VR_` | `VR_MISSING_BYPASS` |
| `picklist` | `PICKLIST_` | `PICKLIST_NO_GVS` |
| `approval_process` | `APPROVAL_` | `APPROVAL_INACTIVE_APPROVER` |
| `record_type_layout` | `RT_` | `RT_ORPHAN` |
| `report_dashboard` | `REPORT_` / `DASHBOARD_` | `DASHBOARD_INACTIVE_RUNNING_USER` |

### Constraints

1. Codes are stable. Once a code ships, it does NOT change meaning between versions. If the check changes, the code changes (e.g. `VR_MISSING_BYPASS` → `VR_MISSING_BYPASS_V2`).
2. Codes are unique across all classifiers. The `<DOMAIN>` prefix guarantees this.
3. Codes are short — ideally < 30 chars total. They appear in finding tables, dashboards, CI logs.
4. Codes are not prose. `VR_MISSING_BYPASS` is good; `VALIDATION_RULE_IS_MISSING_A_BYPASS_SETTING` is not.

### Why stable codes matter for 40-year durability

Every audit run produces structured findings. Teams that run the router weekly will track trends — "how many P0 VR_MISSING_BYPASS findings did we have in Q1 vs Q2?" — and those trends break if codes drift. The classifier markdown files are the source of truth for the code → description mapping; the router guarantees it emits no codes outside that catalog.

## Process Observations vs Findings

Both land in the output envelope, but they're different:

| | Findings | Process Observations |
|---|---|---|
| **Required evidence** | Yes — every finding cites a specific row/id | Not required — can be a pattern observation |
| **Severity** | P0 / P1 / P2 | None |
| **Actionable** | Usually — has a suggested fix | Sometimes — may just flag a smell |
| **Machine-consumable** | Yes — structured rows | No — prose bullets |
| **Example** | `VR_MISSING_BYPASS` on rule `Opportunity.Stage_Required` | "17 validation rules on Opportunity — consider consolidation" |

Rule of thumb: if it fits a one-subject-one-check shape with a mechanical remediation, it's a finding. If it's a pattern the auditor noticed while running the checks, it's a Process Observation.
