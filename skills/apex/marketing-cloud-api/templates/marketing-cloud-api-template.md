# Marketing Cloud API — Work Template

Use this template when working on tasks involving Marketing Cloud Engagement REST or SOAP API calls.

## Scope

**Skill:** `marketing-cloud-api`

**Request summary:** (fill in — e.g., "inject contacts into onboarding journey on Opportunity close", "bulk sync Account data to DE nightly", "fire triggered send on Case creation")

**Out of scope:** Salesforce core REST/SOAP APIs, MCAE/Pardot APIs, Marketing Cloud Connect CRM sync, Marketing Cloud data loader

## Credentials and Endpoints

| Item | Value |
|---|---|
| MC Installed Package name | (fill in) |
| Tenant-specific subdomain | `{{subdomain}}` (from Installed Package API Integration component) |
| Auth endpoint | `https://{{subdomain}}.auth.marketingcloudapis.com/v2/token` |
| REST base URL | `https://{{subdomain}}.rest.marketingcloudapis.com` |
| Client ID storage location | Custom Metadata / Named Credential (never hardcoded) |

## Target Resource

| Item | Value |
|---|---|
| Resource type | [ ] Journey   [ ] Triggered Send   [ ] Data Extension |
| Resource ExternalKey or EventDefinitionKey | (fill in) |
| Target Business Unit MID | (fill in — credentials are BU-scoped) |
| DE field schema / journey entry source fields | (list field names exactly as configured in MC) |

## Context Gathered

- **Journey entry source field names (exact, case-sensitive):**
  - (list each field name as it appears in the entry source settings)
- **TriggeredSendDefinition status confirmed:** [ ] Active/Running  [ ] Not verified
- **DE primary key field(s) for upsert idempotency:** (fill in)
- **Volume / batch size expectation:** (e.g., 50 rows real-time vs 5,000 rows nightly batch)
- **Known constraints or rate limit considerations:** (fill in)

## Approach

**Pattern selected:**

- [ ] Journey injection via `/interaction/v1/events`
- [ ] Triggered send via `/messaging/v1/messageDefinitionSends/key:{ExternalKey}/send`
- [ ] Synchronous DE row upsert via `/hub/v1/dataevents/key:{ExternalKey}/rowset`
- [ ] Async DE bulk insert via `/hub/v1/dataeventsasync/key:{ExternalKey}/rowset` + requestId polling

**Reason for pattern choice:** (fill in — e.g., "bulk nightly sync of 3,000 rows → async endpoint")

## Implementation Steps

1. [ ] Retrieve Client ID, Client Secret, subdomain from credential store
2. [ ] Acquire OAuth 2.0 token via POST `/v2/token` with `grant_type=client_credentials`
3. [ ] Implement token caching with expiry check (re-acquire ~2 min before `expires_in`)
4. [ ] Build request payload using exact field names from target resource schema
5. [ ] Make API call with `Authorization: Bearer {{access_token}}` header
6. [ ] Handle response: log full response body; 201 for journey injection ≠ confirmed entry
7. [ ] For async DE: store `requestId` and poll `GET /hub/v1/dataeventsasync/{requestId}` for completion
8. [ ] Verify end-to-end: check Journey Builder contact history or DE row count in MC

## Checklist

- [ ] Credentials stored in Custom Metadata or Named Credentials — not hardcoded
- [ ] Token is cached and reused; not requested per record or per loop iteration
- [ ] EventDefinitionKey is from the journey entry source settings (format: `APIEvent-...`), not the journey key
- [ ] All `Data` field names in journey injection payload match entry source schema exactly (case-sensitive)
- [ ] TriggeredSendDefinition confirmed in Active/Running status before first send
- [ ] Bulk DE operations use async endpoint; requestId is stored and polled
- [ ] Full API response body is logged for debugging
- [ ] End-to-end verification done in MC (Journey Builder contact history or DE row count)

## Notes

(Record any deviations from the standard pattern, edge cases discovered, or BU-specific behavior observed.)
