# Marketing Integration Patterns — Work Template

Use this template when designing, reviewing, or implementing an integration between an external system and Salesforce Marketing Cloud.

## Scope

**Skill:** `marketing-integration-patterns`

**Request summary:** (fill in what the user asked for — e.g., "design integration for order confirmation emails from e-commerce platform")

---

## Context Gathered

Answer these before selecting a pattern:

- **Source system:** (e.g., Salesforce CRM, e-commerce platform, ERP, mobile app backend)
- **Message type:** (transactional single-send / Journey enrollment / bulk audience sync / CRM data sync)
- **Latency requirement:** (real-time <5s / near-real-time <60s / batch 15min+ / nightly)
- **Daily contact volume and peak burst rate:** (e.g., 10,000 sends/day, 500 concurrent bursts)
- **Installed Package with API Integration:** (exists / needs to be created / unknown)
- **Triggered Send Definition External Key (if applicable):** ___________
- **Journey eventDefinitionKey (if applicable):** `APIEvent-` ___________
- **SFTP path and Data Extension field API names (if applicable):** ___________
- **MC Connect installed in org:** (yes / no / unknown)

---

## Pattern Selection

Based on the context above, select the integration pattern:

| Pattern | Use When |
|---|---|
| Triggered Send (REST) | Single transactional message per event, sub-second delivery, no branching needed |
| Journey Injection — synchronous (`/events`) | Single contact enrolled in multi-step Journey, real-time trigger |
| Journey Injection — async batch (`/events/async`) | Up to 100 contacts per call, near-real-time bulk enrollment |
| SFTP File Drop + Automation Studio Import | Bulk audience sync (millions of records), 15min+ latency acceptable |
| MC Connect Synchronized Data Extensions | Salesforce CRM is the data source, no custom API code preferred |

**Selected pattern:** ___________

**Reason for selection:** ___________

---

## Authentication Checklist

- [ ] Installed Package exists in Marketing Cloud Setup with API Integration component
- [ ] `clientId` and `clientSecret` are stored in a secrets manager / environment variable (not hardcoded)
- [ ] Tenant-specific auth endpoint identified: `https://<subdomain>.auth.marketingcloudapis.com/v2/token`
- [ ] Token acquisition tested; `access_token` and `rest_instance_url` confirmed in response
- [ ] Token caching implemented (refresh before 20-minute expiry, not per-call)
- [ ] Required scopes confirmed:
  - [ ] Triggered Send: `Email > Send Email`
  - [ ] Journey Injection: `Journeys > Execute`
  - [ ] Data Extension operations: `Data > Data Extensions > Read/Write`

---

## Integration Endpoint Reference

Fill in based on selected pattern:

### Triggered Send
```
POST https://<rest_instance_url>/messaging/v1/messageDefinitionSends/key:<ExternalKey>/send
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "To": {
    "Address": "<subscriber-email>",
    "SubscriberKey": "<subscriber-key>",
    "ContactAttributes": {
      "SubscriberAttributes": {
        "<AttributeName>": "<value>"
      }
    }
  }
}
```

External Key: ___________
TSD Status (must be Active): ___________

### Journey Injection — Single Contact
```
POST https://<rest_instance_url>/interaction/v1/events
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "ContactKey": "<subscriber-key>",
  "EventDefinitionKey": "APIEvent-<UUID>",
  "Data": {
    "<AttributeName>": "<value>"
  }
}
```

eventDefinitionKey: `APIEvent-` ___________

### Journey Injection — Async Batch (max 100 contacts)
```
POST https://<rest_instance_url>/interaction/v1/events/async
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "EventDefinitionKey": "APIEvent-<UUID>",
  "contacts": [
    {
      "ContactKey": "<subscriber-key>",
      "Data": { "<AttributeName>": "<value>" }
    }
    // ... up to 100 entries
  ]
}
```

### SFTP + Automation Studio
- SFTP host: ___________
- SFTP path: ___________
- File naming pattern: ___________
- Data Extension name: ___________
- Import mode (Add and Update / Overwrite): ___________
- Automation Studio automation name: ___________

---

## Error Handling Plan

| HTTP Status | Meaning | Handling |
|---|---|---|
| 202 Accepted | Request queued (async) or sent (triggered) | Log requestId; poll for async completion |
| 400 Bad Request | Invalid payload, inactive TSD, wrong eventDefinitionKey | Log full response body; alert on-call; do not retry without fix |
| 401 Unauthorized | Token expired or invalid credentials | Refresh token and retry once |
| 429 Too Many Requests | Rate limit exceeded | Exponential backoff with jitter; surface metric |
| 500 / 503 | Transient server error | Retry with backoff up to 3 times; dead-letter after exhaustion |

**Dead-letter destination:** ___________

**Alerting threshold:** ___________

---

## Pre-Launch Validation Checklist

- [ ] Triggered Send Definition is in Active status
- [ ] Journey is Published and Entry Source is Active
- [ ] `eventDefinitionKey` confirmed from Entry Source properties panel (starts with `APIEvent-`)
- [ ] Async batch calls enforce ≤ 100 contacts per request
- [ ] SFTP column headers match Data Extension field API names exactly (case-sensitive)
- [ ] Token is cached; re-authentication does not happen per API call
- [ ] Non-2xx responses are logged with full response body
- [ ] Rate limit handling (HTTP 429) is implemented with exponential backoff
- [ ] MC Connect SDEs are used (read-only) as sources, not targets, in Marketing Cloud SQL
- [ ] Integration tested with a subscriber not already in All Subscribers list (verify creation behavior)

---

## Notes

Record any deviations from the standard pattern, edge cases discovered during testing, or operational decisions made during implementation:

- ___________
