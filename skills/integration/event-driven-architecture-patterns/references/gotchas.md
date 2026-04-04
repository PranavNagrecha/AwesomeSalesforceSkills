# Gotchas — Event-Driven Architecture Patterns

Non-obvious Salesforce platform behaviors that cause real production problems when selecting or mixing event-driven mechanisms.

## Gotcha 1: CDC Entity Limit Is Per-Org, Not Per-Channel

**What happens:** The free standard allocation for Change Data Capture is **5 entity selections** across the entire org. This is not per channel or per subscriber — it is a single org-wide count. When the sixth entity is selected in Setup, Salesforce blocks the selection with a license error. Teams that plan a CDC rollout across 10 objects without a CDC add-on license will hit this wall partway through enablement, and the rollout will stall.

**When it occurs:** During the initial CDC enablement phase when more than 5 objects (standard or custom) are selected in Setup under Integrations > Change Data Capture. The limit counts each selected entity once regardless of how many custom channels reference it.

**How to avoid:** Audit the full list of objects that need CDC coverage before committing to the pattern. If the count exceeds 5, either purchase the Change Data Capture add-on license or consider Platform Events with Apex trigger publishers as an alternative for lower-priority objects. Document the entity budget as part of the integration architecture decision.

---

## Gotcha 2: Streaming API Retention Is 24 Hours, Not 72 — and Limits Differ From Platform Events

**What happens:** Developers who are familiar with Platform Events (72-hour replay window) assume that the Streaming API (PushTopic) provides the same retention. It does not — PushTopic events are retained for **24 hours only**. A subscriber that goes offline Friday evening and returns Monday morning will find all its events gone, with no way to replay them. This produces silent data loss with no error from the Salesforce side.

Additionally, the throughput allocation for PushTopic (~50,000 events/day org-wide) is significantly lower than Platform Events (250,000/day on Enterprise+). High-volume scenarios that appear to work in sandbox often silently shed events in production.

**When it occurs:** Any time a CometD subscriber using a PushTopic channel is offline for more than 24 hours, or when event volume spikes above the streaming allocation during a bulk data load or mass update.

**How to avoid:** Use the 24-hour retention limit as a hard design constraint. If the integration must tolerate outages longer than 24 hours, CDC or Platform Events are the correct mechanisms. When evaluating PushTopic for any new integration, confirm that the event volume ceiling is acceptable and implement an independent reconciliation mechanism (e.g., a scheduled REST query to catch up) for any production scenario that could result in a gap.

---

## Gotcha 3: CDC Gap Events Require a Full-State Fetch — Ignoring Them Causes Silent Data Drift

**What happens:** When a CDC subscriber falls behind and the Salesforce event bus cannot deliver all events within the retention window, CDC sends a **gap event** instead of the individual change events. Gap events have `changeType` values prefixed with `GAP_` (e.g., `GAP_CREATE`, `GAP_UPDATE`, `GAP_DELETE`, `GAP_OVERFLOW`). A subscriber that only handles `CREATE`, `UPDATE`, `DELETE`, and `UNDELETE` and ignores `GAP_*` types will silently skip the gap notification, leaving the external system out of sync with no error logged.

**When it occurs:** When a subscriber was offline for an extended period, when the event bus experiences high load, or when the subscriber's replay position is too far behind the live tip to deliver individual events reliably. Also occurs when `GAP_OVERFLOW` fires after a bulk operation creates more change events than the gap event mechanism can individually represent.

**How to avoid:** All CDC subscriber code must explicitly handle `GAP_*` change types. The correct response to any gap event is to perform a full-state synchronization of the affected record(s) from the Salesforce REST API using the `recordIds` in the `ChangeEventHeader`. Treat the gap event as a signal to re-fetch, not as a change event to process. Code review checklists should include a `GAP_*` handling verification.

---

## Gotcha 4: Outbound Messages Require a SOAP Acknowledgment — Missing It Causes Infinite Retries

**What happens:** Outbound Messages use an at-least-once delivery model. Salesforce retries delivery until the external endpoint returns a SOAP acknowledgment envelope. If the endpoint returns HTTP 200 but the body is not the correct SOAP ack format, Salesforce treats it as a delivery failure and retries. This creates a retry storm against the external system that can last up to 24 hours, generating duplicate processing and flooding the receiver with the same message repeatedly.

**When it occurs:** When an external endpoint developer unfamiliar with SOAP implements a REST-style 200 OK response without the SOAP ack body, or when an endpoint returns a SOAP fault in the body. Both are treated as delivery failures by Salesforce.

**How to avoid:** Confirm that the external endpoint returns the exact SOAP acknowledgment structure Salesforce expects:
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notificationsResponse xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notificationsResponse>
  </soapenv:Body>
</soapenv:Envelope>
```
Test the endpoint before enabling the Workflow Rule in production. Add idempotency logic on the receiver side because at-least-once delivery guarantees duplicates will occur during normal retries.

---

## Gotcha 5: Platform Events Published in a Failed Transaction Are Still Delivered

**What happens:** Platform Events published with `EventBus.publish()` inside an Apex transaction are held until the transaction commits. If the transaction **rolls back** (DML exception, `Database.rollback()`, or an uncaught exception), the Platform Events published in that transaction are **also rolled back and not delivered**. However, Platform Events published with the `publishImmediately` option (available in certain Flow configurations) or via the REST API are **not** subject to transaction rollback — they fire regardless of whether the triggering transaction succeeds.

This creates a counterintuitive split behavior: Apex-published events tied to a DML transaction fail silently if the transaction rolls back. REST-published events or Flow-published events with immediate delivery succeed even if associated record saves fail.

**When it occurs:** When Apex transaction boundary control (savepoints, Database.rollback) is involved, or when an uncaught exception causes a transaction rollback after `EventBus.publish()` has already been called within the same transaction.

**How to avoid:** Design event publishing to occur after the transaction commits whenever transactional consistency between the record change and the event delivery is required. Use Apex after-commit patterns or consider CDC (which guarantees the event fires only after the DML commits) when record-and-event consistency is a hard requirement. Document the rollback behavior in the integration architecture so that downstream consumers understand that missing events may indicate a failed record operation, not a subscriber outage.
