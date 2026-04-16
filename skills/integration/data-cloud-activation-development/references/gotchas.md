# Gotchas — Data Cloud Activation Development

## Gotcha 1: Missing HMAC Key Silently Stops Payload Delivery

**What happens:** After creating a webhook Data Action Target without an HMAC-SHA256 secret key, no webhook payloads are ever delivered to the endpoint. No error appears in Data Cloud, no delivery failure is logged, and the endpoint receives no traffic.

**When it occurs:** When the HMAC key field is left blank during Data Action Target creation, or when the key is cleared after initial setup.

**How to avoid:** Always configure the HMAC secret key during Data Action Target creation. Verify delivery by inserting a test DMO record that meets the Streaming Insight condition and checking the target endpoint's access log.

---

## Gotcha 2: Data Cloud-Triggered Flows Fire on Insert Only — Not Update

**What happens:** A Data Cloud-Triggered Flow designed to react to profile changes never fires when existing unified profile records are updated with new attribute values.

**When it occurs:** When the DMO trigger event is a row update (e.g., a calculated insight recalculating a score on an existing Individual record) rather than a new row insertion.

**How to avoid:** Understand that the trigger is strictly DMO row insertion. For update-triggered automation, either design the DMO population pattern to always insert new rows (immutable event log pattern), use Calculated Insights to detect deltas, or trigger via a separate mechanism.

---

## Gotcha 3: 15-Minute HMAC Propagation Delay After Key Rotation

**What happens:** After regenerating or changing the HMAC secret key, the receiver begins rejecting all webhook payloads for up to 15 minutes because the platform is still signing with the old key during the propagation window.

**When it occurs:** During planned security key rotation. The change is accepted by the platform UI immediately but takes time to propagate.

**How to avoid:** Plan HMAC key rotations for low-traffic periods. During the rotation window, implement the receiver to temporarily accept both old and new signatures. Alert on signature verification failures to detect the transition.

---

## Gotcha 4: No Auto-Retry on Data Action Target Delivery Failure

**What happens:** If the webhook endpoint returns a 5xx error or is unreachable during the delivery window, the event is not retried. After the 4-day retention window, the event is permanently lost.

**When it occurs:** Whenever the target endpoint has downtime, rate limits, or returns errors during the delivery attempt.

**How to avoid:** Design idempotent receivers that can handle delayed or out-of-order delivery. Implement an external dead-letter queue (AWS SQS, Azure Service Bus) for failed deliveries. Monitor the 4-day retention window and implement alerting when delivery failures are detected.

---

## Gotcha 5: Activation Target vs. Data Action Target Naming Confusion

**What happens:** A webhook configured under "Activation Targets" fires in batch with segment export payloads rather than individual event-level payloads. The developer expects near-real-time per-event webhooks but receives periodic bulk exports.

**When it occurs:** When the webhook is created under the wrong Setup menu — "Activation Targets" (segment-level) vs. "Data Action Targets" (event-level).

**How to avoid:** For event-driven webhook integration, always use "Data Action Targets" in Data Cloud Setup. "Activation Targets" are for segment membership batch publishing to external channels (ad platforms, SFTP, Marketing Cloud segments).
