# Platform Events Integration — Work Template

Use this template when designing or reviewing a Platform Events integration that crosses the Salesforce boundary — external publishers pushing events in, or external subscribers consuming events out.

---

## Scope

**Skill:** `integration/platform-events-integration`

**Request summary:** (fill in what was asked — e.g., "design external subscriber for OrderShipped__e", "publish events from Node.js middleware")

**Direction:**
- [ ] External publisher → Salesforce (REST API)
- [ ] Salesforce → External subscriber (CometD or Pub/Sub API)
- [ ] Both

---

## Context Gathered

Answer these before designing:

| Question | Answer |
|---|---|
| Event name(s) | |
| Standard or High-Volume event? | |
| Max events per hour (publisher estimate) | |
| Required replay window (hours/days) | |
| Subscriber protocol: CometD or Pub/Sub API? | |
| Consumer technology / middleware stack | |
| Is idempotency required on subscriber? | |
| Replay on reconnect needed? (durable subscriber) | |

---

## Event Schema Design

| Field Name | Type | Purpose |
|---|---|---|
| `CorrelationId__c` | Text(255) | Idempotency key — publisher sets, subscriber checks |
| (no retention field) | — | Retention is fixed at 72h and NOT settable per event. Do not add one. |
| (add event-specific fields) | | |

---

## Publisher Design (External → Salesforce)

**Auth method:** [ ] JWT Bearer (server-to-server, recommended) [ ] Web Server flow [ ] User-Agent flow

**Endpoint:**
```
POST /services/data/vXX.0/sobjects/<EventName__e>/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Payload template:**
```json
{
  "CorrelationId__c": "<stable-unique-id>",
  "<Field1__c>": "<value>",
  "<Field2__c>": "<value>"
}
```

**Error handling:**
- On HTTP 401: refresh token and retry once
- On HTTP 429 (rate limit): back off with exponential retry
- On HTTP 503: retry with jitter; alert if persistent

---

## Subscriber Design (Salesforce → External)

**Protocol:** [ ] Pub/Sub API (gRPC) — preferred for new integrations [ ] CometD (Streaming API) — for existing middleware

**If CometD, endpoint version:** `/cometd/____` — on v64.0 and later the server can itself send a disconnect (auto-scaling, more frequent on Hyperforce), so record the reconnect handling: [ ] `/meta/disconnect` listener registered [ ] reconnect resumes from stored `replayId`, not `-1`

**Replay ID strategy:**

| Scenario | Replay ID Value | Rationale |
|---|---|---|
| First run (no stored ID) | `-2` (earliest) | Catch all events in retention window |
| Normal restart | Stored ID from durable store | Resume from last confirmed position |
| Intentional gap acceptance (document reason) | `-1` (latest) | Only if event loss is explicitly acceptable |

**Replay ID storage:** (describe where replay position is persisted — Redis, Postgres table, etc.)

**Idempotency check:** (describe how duplicate events are detected and skipped)

---

## Event Tier (legacy check, not a design choice)

New platform events are high volume by default; standard-volume custom platform
events can no longer be defined and are retired in Summer '27. Existing ones keep
working until that release.

| Property | Standard-Volume (legacy) | High-Volume (all new events) |
|---|---|---|
| Definable today | No | Yes |
| Publish allocation (org-wide/hour) | 100,000 EE/Perf/Unl | 250,000 EE/Perf/Unl; 50,000 Dev |
| Retention window | 24 hours | 72 hours |
| Retention configurable | No | No |
| Apex trigger subscriber | Yes | Yes |
| External subscriber | Yes | Yes |

**Existing events in scope:** [ ] All high-volume [ ] Some standard-volume (list them + migration date, Summer '27 deadline)

**Peak publish rate:** ______ /hour against the 250,000/hour org allocation. Add-on capacity needed? [ ] No [ ] Yes (+25,000/hour increments)

---

## Dead-Letter / Gap Recovery Strategy

If subscriber falls offline longer than the retention window, events cannot be replayed. Chosen recovery approach:

- [ ] Accept gap — subscriber requests full state sync via REST/Bulk API on reconnect
- [ ] Durable publisher-side store — publisher also writes payload to BigObject / external queue; subscriber backfills from there
- [ ] (NOT AVAILABLE — retention cannot be extended by any field or setting; if the design needs > 72h, pick one of the two options above)

---

## Review Checklist

- [ ] External publisher authenticates via OAuth 2.0 Connected App — no hard-coded credentials
- [ ] Subscriber persists `replayId` durably after successful processing (not before)
- [ ] First-start replay strategy is documented and tested
- [ ] Peak publish rate sized against the org-wide 250,000/hour allocation (50,000 Developer)
- [ ] `CorrelationId__c` or equivalent idempotency key field is present on the event schema
- [ ] Dead-letter / gap recovery strategy is defined for outages beyond retention window
- [ ] No field on the event schema purports to set retention — no such field exists
- [ ] CometD subscriber on `/cometd/64.0` or later listens on `/meta/disconnect` and reconnects
- [ ] Monitoring covers publisher failures (HTTP errors) and subscriber lag

---

## Notes and Deviations

(Record any deviations from the standard patterns above and the rationale for each.)
