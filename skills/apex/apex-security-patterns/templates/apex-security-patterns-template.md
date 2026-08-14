# Apex Security Review Worksheet

## Execution Context

| Item | Value |
|---|---|
| Entry point | Aura / REST / Invocable / Trigger / Queueable / Batch |
| Class `apiVersion` (from `.cls-meta.xml`) | e.g. `67.0` — fill this first; it sets the default access mode |
| Default access mode implied by that version | User mode (67.0+) / System mode (≤66.0) |
| Declared sharing | `with` / `without` / `inherited` / none (67.0+ defaults to `with`) |
| Should caller visibility be honored? | Yes / No |
| Read enforcement | `WITH USER_MODE` / `AccessLevel.USER_MODE` / Describe / Other |
| Write enforcement | `stripInaccessible` / `as user` / `AccessLevel.USER_MODE` / Describe / Other |
| Elevation opt-out, if any | `WITH SYSTEM_MODE` / `AccessLevel.SYSTEM_MODE` + `// reason:` |

## Review Questions

- [ ] Is the sharing declaration explicit and defensible?
- [ ] Are record access and CRUD/FLS treated as separate concerns?
- [ ] Does every user-facing read path enforce object and field access?
- [ ] Does every user-facing write path sanitize fields before DML?
- [ ] Are dynamic fields or object names validated through Schema describe or allowlists?
- [ ] Is any `without sharing` usage narrow, documented, and necessary?
- [ ] Was the `apiVersion` read before judging enforcement, rather than a default assumed?
- [ ] If the entry point is a Trigger, were both axes judged separately? (The implicit `without sharing` context cannot be declared away, but it governs row visibility only for operations that run in system mode; trigger-body operations follow the version-gated default access mode — user mode at 67.0+ enforces sharing for that operation — and can opt out per operation.)
- [ ] Does any `WITH SECURITY_ENFORCED` remain? It is removed at API 67.0 — migrate to `WITH USER_MODE`.

## Findings

| Severity | Finding | Remediation |
|---|---|---|
| | | |
| | | |

## Final Recommendation

Summarize the required sharing model, read enforcement pattern, and write enforcement pattern for this code path.
