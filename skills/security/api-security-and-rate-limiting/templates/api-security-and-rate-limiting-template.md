# API Security and Rate Limiting — Work Template

Use this template when working on API security hardening, rate limit investigation, or Connected App restriction tasks.

## Scope

**Skill:** `api-security-and-rate-limiting`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer these before starting work:

- **API types in use:** (REST, SOAP, Bulk API 1.0, Bulk API 2.0, Streaming API, Platform Events, other)
- **Org edition:** (Developer, Professional, Enterprise, Unlimited, Performance)
- **Event Monitoring licensed:** (yes / no — determines granularity of API usage analysis)
- **Current issue type:** (rate limit exhaustion / 429 errors / security hardening / monitoring setup / Connected App restriction)
- **Connected App name(s) in scope:**
- **Integration source IPs or IP ranges:** (static / dynamic / unknown)

## Connected App Restriction Checklist

For each Connected App in scope:

| Setting | Current Value | Target Value | Notes |
|---|---|---|---|
| OAuth scopes granted | | api + refresh_token only (remove full, web) | |
| IP Relaxation policy | | Enforce login IP ranges on every request | |
| IP ranges configured | | List CIDR blocks | |
| Session timeout | | Minimum compatible with longest operation | |
| Refresh token policy | | Specific expiry (not "valid until revoked") | |

## Rate Limit Investigation

If investigating a limit incident:

- **Error observed:** (HTTP 429 / REQUEST_LIMIT_EXCEEDED / concurrent limit / Bulk API limit / other)
- **First occurrence timestamp:**
- **Frequency:** (once / recurring / continuous)
- **Top consumer (from Event Log Files or OAuth Usage):**
- **Remediation action:**

## Retry Strategy Checklist

If implementing or reviewing retry logic:

- [ ] 429 responses check the `Retry-After` header before calculating delay
- [ ] Exponential backoff is bounded (maximum retries defined, maximum wait defined)
- [ ] `REQUEST_LIMIT_EXCEEDED` errors fail fast and do NOT retry
- [ ] Retry attempts are logged with timestamp and attempt number
- [ ] Bulk API is used instead of REST for record volumes above 2,000 records per operation

## Monitoring Setup

- [ ] API Usage Metrics reviewed (Setup → API Usage Metrics)
- [ ] Organization.DailyApiRequestsUsed queried to confirm current consumption vs. limit
- [ ] Event Log Files queried for API event type (if Event Monitoring is licensed)
- [ ] Top API consumers identified by USER_ID_DERIVED and CONNECTED_APP_ID columns

## Notes

(Record any deviations from the standard pattern, org-specific constraints, or decisions made and why.)
