# Gotchas — Change Data Capture Integration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `changedFields` Is Only Available via Pub/Sub API — Not CometD

**What happens:** A CometD subscriber expects the `ChangeEventHeader.changedFields` bitmap to be present in the message body, but the field is absent. The subscriber either throws a null pointer exception or silently processes all fields as changed.

**When it occurs:** When the subscriber is built against Pub/Sub API documentation but is actually connecting via CometD (or vice versa). This is easy to miss because the JSON payload structure looks similar for both protocols.

**How to avoid:** Confirm the subscriber protocol before designing delta logic. If you need `changedFields`, `nulledFields`, or `diffFields` in the header, you must use Pub/Sub API (gRPC, API version 54.0+) or an Apex trigger. CometD delivers the full set of current field values but does not include field-level delta headers.

---

## Gotcha 2: Gap Events Silently Drop Changed Field Data

**What happens:** The subscriber receives a gap event but processes it as a normal change event. Because the body contains no field values, the external record is updated with empty or null data — or the subscriber crashes attempting to read fields that do not exist.

**When it occurs:** Any time Salesforce cannot produce a full change event: the payload exceeds 1 MB (common on objects with hundreds of fields or long text areas), a bulk database-level operation bypasses the application server, or an internal error occurs. These are not rare edge cases on high-volume orgs.

**How to avoid:** Always check `ChangeEventHeader.changeType` for the `GAP_` prefix (`GAP_CREATE`, `GAP_UPDATE`, `GAP_DELETE`, `GAP_UNDELETE`, `GAP_OVERFLOW`) before accessing field values. On a gap event, use the `recordIds` array in the header to fetch current record state from REST API. Mark affected records as dirty in the external system and reconcile using `commitTimestamp` to avoid overwriting a newer subsequent change.

---

## Gotcha 3: Custom Channel Entity Selections Are Invisible in the Setup UI

**What happens:** A practitioner audits which objects have CDC enabled by checking Setup > Integrations > Change Data Capture. Objects assigned to custom channels do not appear on this page. The practitioner concludes CDC is only enabled for the few objects visible in Setup, missing an accurate picture of actual event volume and entity coverage.

**When it occurs:** Any time custom channels (PlatformEventChannel + PlatformEventChannelMember) are used, which is required for multiple-subscriber isolation, event enrichment, or event filtering. This includes channels deployed via packages.

**How to avoid:** Always audit full entity coverage using Tooling API:
```sql
SELECT QualifiedApiName, EventChannel FROM PlatformEventChannelMember
```
The Setup page is authoritative only for the default `ChangeEvents` channel. Note also that AppExchange released managed package selections do not count toward the 5-entity allocation but still appear in the Tooling API query results.

---

## Gotcha 4: Event Delivery Allocation Is Cumulative Across All API Subscribers

**What happens:** An org deploys a second CometD or Pub/Sub API subscriber for a new integration. Both subscribers receive the same events. The combined delivery count doubles, and the org hits the daily delivery allocation unexpectedly, causing subscriber disconnection.

**When it occurs:** Each CometD or Pub/Sub API client independently counts against the org's daily delivery allocation. The default allocation is 50,000 events per 24 hours (Performance/Unlimited Edition), 25,000 (Enterprise), 10,000 (Developer Edition). Two subscribers on the same channel each consuming 30,000 events totals 60,000 — exceeding the Unlimited/Performance default.

**How to avoid:** Design for a single authoritative bridge subscriber per integration bus where possible. Use custom channels with server-side filtering to reduce the per-subscriber event volume. If multiple subscribers are unavoidable, purchase the CDC add-on (moves to a monthly usage model with 3M/month per add-on unit). Monitor allocation usage via Setup > Event Manager or the REST API before adding new subscribers.

---

## Gotcha 5: Subscribers Offline for More Than 72 Hours Cannot Replay CDC Events

**What happens:** An integration service restarts after a long outage or maintenance window exceeding 72 hours. The subscriber tries to replay using the stored replay ID, but the events have been purged. Depending on the client implementation, this may silently deliver no events (leaving the external system stale) or throw an error.

**When it occurs:** The CDC event bus retains events for exactly 72 hours. This is fixed — Salesforce Shield extends the retention window only for Platform Events via Event Monitoring, not for CDC events. Any subscriber that is offline for more than 72 hours will have an irrecoverable gap in the event stream.

**How to avoid:** Design a recovery path for every CDC subscriber: when the subscriber reconnects with a replay ID that falls outside the retention window, trigger a full Bulk API 2.0 re-sync of the affected objects, then re-subscribe at tip (`-1`). Monitor subscriber health so outages are detected and escalated well before the 72-hour window closes.

---

## Gotcha 6: Formula Field Recalculations Do Not Fire CDC Events

**What happens:** An Account formula field is recalculated (e.g., because a child Opportunity changed). The external system expects to receive an Account CDC event reflecting the new formula value, but no event is published.

**When it occurs:** Any time a formula field, roll-up summary, or cross-object formula updates its stored value due to a change in a related record. CDC only captures explicit DML changes on the object that holds the field — it does not observe formula recalculations driven by child records.

**How to avoid:** Do not rely on CDC to propagate formula or roll-up summary field updates to external systems. If the external system needs the derived value, either fetch it on demand via REST API or use a Flow/Process Builder that explicitly updates a stored field on the parent record when the child changes (which will produce a CDC event for the stored field update).
