# Event-Driven Architecture Patterns — Decision Worksheet

Use this template when selecting an event-driven mechanism for a Salesforce integration requirement.

## Scope

**Skill:** `integration/event-driven-architecture-patterns`

**Request summary:** (describe the integration scenario in 1-2 sentences)

---

## Context Gathered

Answer these questions before applying the decision matrix:

- **Trigger source:** (DML on a record / business process / Workflow Rule / external system publishing)
- **Subscriber technology:** (Apex trigger / Flow / CometD external client / Pub/Sub API gRPC client / SOAP endpoint / LWC empApi)
- **Payload requirement:** (custom domain fields / automatic field deltas / SOQL-selected fields / fixed SOAP fields)
- **Required retention window:** (< 24h / 24-72h / > 72h)
- **Estimated event volume per day:**
- **Org edition and CDC entity allocation used:**
- **Is SOAP required on the receiver side?:** (yes / no)

---

## Decision Matrix — Applied

Mark each cell as Supported (S), Not Supported (N), or Not Applicable (—) for this use case:

| Requirement | Platform Events | CDC | PushTopic | Outbound Messages |
|---|---|---|---|---|
| Trigger source can fire this mechanism | | | | |
| Subscriber protocol is supported | | | | |
| Payload type is available | | | | |
| Retention window is sufficient | | | | |
| Throughput ceiling is sufficient | | | | |
| Org edition supports it | | | | |

**Mechanisms eliminated and reason:**

1. (mechanism) — (reason eliminated)
2. (mechanism) — (reason eliminated)

---

## Recommendation

**Chosen mechanism:** (Platform Events / CDC / Streaming API PushTopic / Outbound Messages)

**Primary reason:** (1-2 sentences)

**Key tradeoff accepted:** (what does this choice give up vs the next-best alternative?)

**Risk to validate before implementation:** (the most likely thing to go wrong based on gotchas.md)

---

## Implementation Skill Pointer

Route to:
- [ ] `integration/platform-events-integration` — for external pub/sub via CometD or Pub/Sub API
- [ ] `apex/platform-events-apex` — for Apex publisher/subscriber
- [ ] `integration/change-data-capture-integration` — for CDC external subscription setup
- [ ] `integration/streaming-api-and-pushtopic` — for PushTopic CometD setup
- [ ] `architect/platform-selection-guidance` — if broader platform feature selection is still open

---

## Notes

(Record any deviations from standard patterns, org-specific constraints, or open questions.)
