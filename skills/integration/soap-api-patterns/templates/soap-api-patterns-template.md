# SOAP API Patterns — Work Template

Use this template when working on a SOAP API integration task.

---

## Scope

**Skill:** `integration/soap-api-patterns`

**Request summary:** (fill in what the user asked for)

**Integration type:** [ ] New implementation   [ ] Review / audit   [ ] Troubleshoot

---

## Context Gathered

Answer these before proceeding:

- **WSDL type:** [ ] Enterprise (org-specific, strongly typed)   [ ] Partner (generic, any org)
- **Consumer platform:** [ ] Java (WSC)   [ ] .NET (Visual Studio)   [ ] Other: ___
- **Authentication method:** [ ] login() username/password   [ ] OAuth JWT Bearer   [ ] OAuth Web Server
- **API version in use:** `v____.0` (minimum v56.0 required)
- **Target org edition:** ___  (determines daily API limit)
- **Operations needed:** [ ] query   [ ] create   [ ] update   [ ] upsert   [ ] delete   [ ] Metadata API

---

## WSDL and Endpoint Configuration

| Setting | Value |
|---|---|
| WSDL type | Enterprise / Partner |
| Login endpoint | `https://login.salesforce.com/services/Soap/c/<version>` (enterprise) or `.../u/<version>` (partner) |
| Service endpoint (post-login) | `<serverUrl from LoginResult>` — DO NOT hardcode |
| API version | `v63.0` (Spring '25) or specify: `v____.0` |

---

## Authentication Flow

```
1. Call login() at the standard login endpoint
2. Extract sessionId from LoginResult
3. Extract serverUrl from LoginResult
4. Switch ALL subsequent calls to serverUrl
5. Include sessionId in SessionHeader on every call
6. On INVALID_SESSION_ID fault → re-authenticate and retry
```

**Session timeout in this org:** ___ minutes (confirm in Setup > Session Settings)

---

## Operations Checklist

### Query

- [ ] `query()` call sends SOQL to the serverUrl (not login endpoint)
- [ ] Response `isDone()` / `done` flag is checked after every `query()` call
- [ ] `queryMore()` is called with the `queryLocator` until `isDone()` returns `true`
- [ ] Session expiry during pagination is handled (re-authenticate + restart query)

### DML (create / update / upsert / delete)

- [ ] Batch size is ≤ 200 records per call
- [ ] Every `SaveResult[]` / `UpsertResult[]` entry is inspected for `isSuccess()`
- [ ] Failed records are routed to a retry queue or dead-letter table — never silently discarded
- [ ] For upsert: External ID field is defined, indexed, and unique per integration system

---

## Session Expiry Handler

```
On INVALID_SESSION_ID fault:
  1. Log the event with timestamp and current operation
  2. Call login() again with stored credentials
  3. Update sessionId and serverUrl from new LoginResult
  4. Retry the failed operation from the beginning (not from mid-batch)
```

---

## Review Checklist (Mode 2)

Copy from SKILL.md and check off as you audit:

- [ ] WSDL type is appropriate for the consumer (enterprise = single org; partner = multi-org/ISV)
- [ ] Post-login calls use `serverUrl` from `LoginResult`, not a hardcoded endpoint
- [ ] API version in endpoint URL is v56.0 or above
- [ ] Enterprise WSDL was regenerated after the last org schema change
- [ ] `INVALID_SESSION_ID` is handled with re-authentication
- [ ] All `SaveResult[]` / `UpsertResult[]` arrays are inspected per record
- [ ] `queryMore()` is called when `done` is `false`
- [ ] Credentials and security tokens are sourced from environment or secrets manager — not source code
- [ ] Daily API call volume estimate fits within the org edition limit
- [ ] Compound fields (Address, Geolocation) handled as nested complex types

---

## Troubleshooting Notes

| Symptom | Probable Cause | Resolution |
|---|---|---|
| `INVALID_SESSION_ID` | Session expired or wrong header | Re-authenticate, update SessionHeader |
| `UNSUPPORTED_API_VERSION` | Retired API version in endpoint URL | Update to v56.0+ |
| Custom field always null | Enterprise WSDL is stale | Regenerate WSDL and rebuild stubs |
| Calls fail on sandbox/EU | Hardcoded instance hostname | Use serverUrl from LoginResult |
| `LOGIN_MUST_USE_SECURITY_TOKEN` | Token not appended to password | Concatenate token directly to password string |
| Partial records missing | SaveResult[] not inspected | Add per-record result iteration |

---

## Notes

(Record any deviations from the standard pattern and the reason.)
