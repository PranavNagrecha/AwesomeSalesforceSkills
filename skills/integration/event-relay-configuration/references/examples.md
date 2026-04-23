# Event Relay — Examples

## Example 1: CDC → EventBridge → Lambda (Order Sync)

**Goal:** every Order change in Salesforce propagates to an ERP via Lambda.

**Setup:**
- High-Volume channel: `/data/OrderChangeEvent`.
- AWS Connection targeting `sf-prod-bus` in `us-east-1`.
- Filter: `ChangeEventHeader.changeType != 'GAP_OVERFLOW'`.
- Replay: `LATEST` at go-live; watermark stored in Lambda's DynamoDB.

**Ops:**
- Alert on lag > 3 min.
- Lambda is idempotent keyed by `(recordId, commitTimestamp)`.

---

## Example 2: Platform Event With Filter

**Channel:** `/event/PaymentFailed__e` (high-volume).

**Filter:** `Tier__c = 'Enterprise'` — only relay events for the tier that
requires immediate escalation.

**Downstream:** EventBridge rule routes to a Step Function that opens a
PagerDuty incident.

---

## Example 3: Controlled Resume After Outage

AWS had a 40-minute outage. Event Relay was auto-paused. Procedure:

1. Identify last `replayId` processed by Lambda.
2. Pause Event Relay in Setup.
3. Update replay to the known `replayId`.
4. Resume. Lambda's idempotency prevents duplicates.

---

## Anti-Pattern: "Just Set Replay To EARLIEST"

After an outage, a team resumed with `EARLIEST`. Relay replayed 68 hours
of backlog, spiked AWS costs, and duplicated non-idempotent downstream
writes. Fix: always replay from a known watermark, and make consumers
idempotent.
