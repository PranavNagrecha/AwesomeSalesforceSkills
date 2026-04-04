# Flow Runtime Error Diagnosis — Incident Template

Use this template when investigating a Flow runtime error in production or sandbox.

---

## Incident Information

| Field | Value |
|---|---|
| Date / Time | ___ |
| Flow API Name | ___ |
| Flow Version (from fault email) | ___ |
| Flow Type (Record-Triggered / Auto-Launched / Screen) | ___ |
| Triggering record ID (if known) | ___ |
| Reported by | ___ |

---

## Fault Notification Email

Paste the relevant sections from the fault email:

```
Flow label: ___
Flow API name: ___
Flow version: ___
Failing element (API name): ___
Error message: ___
Element execution order (stack trace):
  1. ___
  2. ___
  3. ___
```

---

## Error Classification

| Error type from email | Likely cause |
|---|---|
| `NULL_REFERENCE` / `NullPointerException` | Variable from Get Records is null — missing null check |
| `INVALID_FIELD` | Field deleted or renamed — update Get/Create/Update element |
| `LIMIT_EXCEEDED: Too many SOQL queries` | Get Records inside a Loop — move outside loop |
| `LIMIT_EXCEEDED: Too many DML statements` | DML inside a Loop — collect and bulk DML outside loop |
| `CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY` | Validation rule, duplicate rule, or trigger failure |
| `FIELD_INTEGRITY_EXCEPTION` | Required field not set or invalid picklist value |
| Other: ___ | ___ |

---

## Root Cause Analysis

- **Failing element:** `___` (navigate to this in Flow Builder using Ctrl+F)
- **Variable involved:** `{!___}`
- **Root cause:** ___
- **Reproducing scenario:** ___

---

## Fix Plan

- [ ] Fix applied in version: ___
- [ ] Fix description: ___
- [ ] Null check added after Get Records: Yes / No / Not applicable
- [ ] Elements moved out of Loop: Yes / No / Not applicable
- [ ] Field reference corrected: Yes / No / Not applicable

---

## Fault Path Handler

- [ ] Fault path added to the previously-failing element
- **User-facing message:** `___` (use `{!$Flow.FaultMessage}` for technical detail in admin-facing flows)
- **Logging action:** (Platform Event / Custom Log record / Email) ___

---

## Testing

- [ ] Fix tested in sandbox with same record ID / scenario that triggered the original error
- [ ] Flow activates without error
- [ ] Debug mode trace reviewed — no unexpected null variables
- [ ] Active flow version confirmed — version ___ is active

---

## Post-Resolution

- [ ] Fault email routing confirmed (Setup > Process Automation Settings)
- [ ] Other flows checked for same pattern (SOQL in loop, missing null checks)
- [ ] Incident notes added to team runbook
