# REST API Patterns — Work Template

Use this template when designing, implementing, or reviewing a Salesforce REST API integration.

---

## Scope

**Skill:** `rest-api-patterns`

**Request summary:** (describe what the integration needs to accomplish)

**Target org edition:** (Developer / Professional / Enterprise / Unlimited — affects daily API limit)

**API version to use:** v_____ .0   _(must be v56.0 or higher; recommend v60.0+)_

---

## Context Gathered

Answer these before selecting a pattern:

- **Auth mechanism:** OAuth flow in use and whether a valid access token is available
- **Operation type:** Single CRUD / Composite parent-child / Bulk insert / Paginated query / Upsert by External ID
- **Record volume per call:** _____ records  _(>2,000 → consider Bulk API 2.0)_
- **Atomicity required:** Yes / No  _(affects `allOrNone` choice on Composite)_
- **External ID field available for upsert:** Yes / No

---

## Endpoint Selection

| Step | HTTP Verb | Endpoint | Notes |
|------|-----------|----------|-------|
| 1 | | | |
| 2 | | | |

**Base URL:** `https://<instance>.salesforce.com/services/data/v_____.0/`

---

## Request Design

### Authentication Header

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Request Body (if applicable)

```json
{
  // TODO: paste request body here
}
```

---

## Composite Request (if applicable)

```json
{
  "allOrNone": true,
  "compositeRequest": [
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Account/",
      "referenceId": "Step1",
      "body": {}
    },
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Contact/",
      "referenceId": "Step2",
      "body": {
        "AccountId": "@{Step1.id}"
      }
    }
  ]
}
```

**`allOrNone` rationale:** (explain why true or false was chosen)

---

## Pagination Loop (if applicable)

- Initial query URL: `GET /services/data/v63.0/query/?q=<SOQL>`
- Loop condition: continue while `done == false`
- Next page URL: `<instance_url>` + `nextRecordsUrl` from response
- Buffer strategy: (stream to file / accumulate in memory / process per page)

---

## Error Handling Strategy

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| 200 | Success (also Composite outer) | Inspect each subrequest `httpStatusCode` |
| 201 | Record created | Read `id` from response body |
| 204 | Update/delete succeeded | No response body |
| 300 | Multiple matches on External ID upsert | Fix duplicate records; retry |
| 400 | Bad request | Log `[{message, errorCode, fields}]`; fix payload |
| 401 | Unauthorized / token expired | Refresh token; retry once |
| 403 | Forbidden (insufficient scope) | Check Connected App OAuth scopes |
| 404 | Record not found | Log and skip, or fall back to POST |
| 429 | Rate limit exceeded | Read `Retry-After` header; back off and retry |
| 500 | Salesforce internal error | Log; retry with exponential back-off |
| 503 | Concurrent limit or maintenance | Back off; check org status |

---

## API Limit Estimate

| Metric | Value |
|--------|-------|
| Org edition | |
| Estimated daily API calls needed | |
| Daily API limit for this edition | |
| Headroom percentage | |
| Concurrent long-running requests (>20s) at peak | |

---

## Review Checklist

- [ ] API version is v56.0 or higher and stored in configuration, not hard-coded.
- [ ] `Authorization: Bearer <token>` is present on every request.
- [ ] 401 responses trigger a token refresh and single retry.
- [ ] Paginated queries loop until `done: true` using `nextRecordsUrl`.
- [ ] Composite responses are inspected per-subrequest for `httpStatusCode`.
- [ ] `allOrNone` setting is explicitly chosen and documented.
- [ ] Record volume per call is within resource limits (≤25 for Composite, ≤200 for sObject Tree).
- [ ] HTTP 429 handling reads `Retry-After` before retrying.
- [ ] Daily API limit projection is within safe headroom for the org edition.
- [ ] Error responses parse `[{message, errorCode, fields}]` rather than relying on HTTP status alone.

---

## Notes

(Record any deviations from the standard pattern and the reason for each deviation.)
