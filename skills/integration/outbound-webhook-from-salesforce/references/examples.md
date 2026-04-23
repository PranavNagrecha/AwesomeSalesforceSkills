# Outbound Webhook — Examples

## Example 1: Apex Queueable + Delivery Object

**Trigger:** Opportunity ClosedWon fires Platform Event `OpportunityClosedWon__e`.

**Pipeline:**
1. Apex trigger on event inserts `WebhookDelivery__c` (Pending, payload, endpoint).
2. Queueable picks up Pending rows, POSTs with HMAC signature.
3. On 2xx, mark Sent. On 5xx/408/429, increment attempts, schedule next
   attempt per backoff.
4. After 6 attempts, mark Failed; alert ops.

---

## Example 2: Flow HTTP Callout For Low-Volume Admin Integration

**Use case:** admin-owned internal tool pings Slack webhook on account
escalation.

**Flow:**
- Record-Triggered Flow on Account `Escalated__c` change.
- Scheduled Path 0-min invokes HTTP Callout action.
- On fault path, create `WebhookDelivery__c` with Failed + error.
- Manual replay via button.

**Why:** admin owns; volume ≤ 100/day; Slack is tolerant of occasional
loss.

---

## Example 3: HMAC Signing In Apex

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:External_Webhook');
req.setMethod('POST');
req.setBody(body);
Long ts = DateTime.now().getTime() / 1000;
req.setHeader('X-Timestamp', String.valueOf(ts));
String toSign = ts + '.' + body;
Blob mac = Crypto.generateMac('HmacSHA256',
  Blob.valueOf(toSign),
  Blob.valueOf(secretFromNamedCredential));
req.setHeader('X-Signature', 'sha256=' + EncodingUtil.convertToHex(mac));
```

---

## Anti-Pattern: Callout Inside Trigger

After-insert trigger called `Http.send()` synchronously. Callouts in
triggers require `@future(callout=true)` or Queueable; the team was also
blowing past CPU by waiting on network. Fix: enqueue a Queueable; return
from the trigger fast.
