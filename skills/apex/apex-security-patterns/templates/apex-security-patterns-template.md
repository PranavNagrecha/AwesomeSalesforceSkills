# Apex Security Review Worksheet

## Execution Context

| Item | Value |
|---|---|
| Entry point | Aura / REST / Invocable / Trigger / Queueable / Batch |
| Declared sharing | `with` / `without` / `inherited` |
| Should caller visibility be honored? | Yes / No |
| Read enforcement | `WITH USER_MODE` / `WITH SECURITY_ENFORCED` / Describe / Other |
| Write enforcement | `stripInaccessible` / Describe / Other |

## Review Questions

- [ ] Is the sharing declaration explicit and defensible?
- [ ] Are record access and CRUD/FLS treated as separate concerns?
- [ ] Does every user-facing read path enforce object and field access?
- [ ] Does every user-facing write path sanitize fields before DML?
- [ ] Are dynamic fields or object names validated through Schema describe or allowlists?
- [ ] Is any `without sharing` usage narrow, documented, and necessary?

## Findings

| Severity | Finding | Remediation |
|---|---|---|
| | | |
| | | |

## Final Recommendation

Summarize the required sharing model, read enforcement pattern, and write enforcement pattern for this code path.
