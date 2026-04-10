# MCAE (Pardot) API v5 — Work Template

Use this template when working on an MCAE API v5 integration task: creating or updating Prospects, querying Visitor Activities, configuring Form Handlers, or diagnosing API authentication issues.

## Scope

**Skill:** `mcae-pardot-api`

**Request summary:** (fill in what the user asked for — e.g., "Create Prospects from e-commerce checkout events via API")

---

## Context Gathered

Answer these before writing any code:

- **API version confirmed:** [ ] v5 (`https://pi.pardot.com/api/v5/objects/...`) — NOT v3/v4
- **Pardot Business Unit ID:** `0Uv_______________` (from Account Engagement Settings > Account Settings)
- **OAuth Connected App configured:** [ ] Yes — client_id and client_secret available
- **Target object:** [ ] Prospect  [ ] Visitor  [ ] VisitorActivity  [ ] FormHandler
- **Operation type:** [ ] Read (GET)  [ ] Create (POST)  [ ] Update (PATCH)  [ ] Delete (DELETE)  [ ] List/Query
- **Known constraints:** (e.g., rate limit tier, BU edition, custom field API names)
- **Failure modes to watch for:** (check gotchas.md — upsert behavior, pagination, header requirements)

---

## Authentication Setup

```
Token endpoint:  https://login.salesforce.com/services/oauth2/token
                 (or https://{myDomain}.my.salesforce.com/services/oauth2/token for sandbox/custom domain)
Grant type:      client_credentials (server-to-server) OR authorization_code (user-context)
Required scopes: pardot_api (minimum), refresh_token (if token renewal needed)

Required headers on every MCAE API request:
  Authorization: Bearer {access_token}
  Pardot-Business-Unit-Id: {buId}
  Content-Type: application/json
```

---

## Request Plan

**Endpoint:** `https://pi.pardot.com/api/v5/objects/{object}`

**Method:** (GET / POST / PATCH / DELETE)

**Query parameters:**
| Parameter | Value | Notes |
|---|---|---|
| fields | (e.g., id,email,firstName,lastName,createdAt) | Always specify; do not use * |
| (filter field) | (e.g., email=user@example.com) | |
| orderBy | (e.g., createdAt) | For list operations |
| nextPageMark | (from previous response) | For paginated list operations |

**Request body (POST/PATCH):**
```json
{
  "email": "required-for-prospect-upsert@example.com",
  "firstName": "",
  "lastName": "",
  "company": "",
  "customField__pc": ""
}
```

---

## Pagination Plan

(Complete this section for any list/query operation)

- [ ] Using `nextPageMark` cursor — NOT page or offset parameters
- [ ] Loop exits when `nextPageMark` is absent from response
- [ ] `nextPageMark` value from previous response is passed as query param in next request
- [ ] Handling `totalResults` from response envelope for progress reporting (optional)

```
while nextPageMark present in response:
    include nextPageMark in next request params
    extend results with response.values
    update nextPageMark from response
stop when nextPageMark absent
```

---

## Approach

(Which pattern from SKILL.md applies? Why?)

- [ ] Upsert Prospect by Email — for create/update from external system
- [ ] Paginated Visitor Activity Export — for engagement history retrieval
- [ ] Form Handler POST — for browser-based form submission without server credentials
- [ ] Point lookup by Salesforce CRM ID — for matching Prospect to Lead/Contact

---

## Review Checklist

Tick each item before marking the integration complete:

- [ ] API v5 base URL used (`https://pi.pardot.com/api/v5/objects/...`), not v3 or v4
- [ ] `Pardot-Business-Unit-Id` header present on every request — not just the token call
- [ ] OAuth token obtained from Salesforce (`login.salesforce.com`), not from `pi.pardot.com`
- [ ] Pagination uses `nextPageMark` cursor; no `page=` or `offset=` parameters
- [ ] Prospect email uniqueness understood — POST upserts silently; check returned `id` if create vs. update matters
- [ ] Visitor Activity `type` field treated as integer; `typeName` requested explicitly if human-readable label needed
- [ ] Error response `details` array inspected for field-level validation errors, not just top-level message
- [ ] Token refresh logic implemented (if long-running integration)
- [ ] Client credentials stored securely (Named Credentials / environment variables), not hardcoded
- [ ] `check_mcae_pardot_api.py` run against integration source code — no warnings

---

## Notes

(Record any deviations from the standard pattern and why — e.g., using a sandbox OAuth endpoint, custom domain, non-standard field names)
