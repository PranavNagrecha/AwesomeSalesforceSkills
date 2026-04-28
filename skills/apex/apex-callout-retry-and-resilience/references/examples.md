# Examples — Apex Callout Retry and Resilience

Three end-to-end scenarios. Each shows the policy, the code shape (referencing `templates/apex/HttpClient.cls`, not duplicating it), and the test approach.

## Scenario 1 — Idempotent Payment Retry (Stripe-style)

### Problem

A Salesforce-initiated charge to a payment processor occasionally fails with 503. The processor supports `Idempotency-Key`. We must NOT double-charge a customer.

### Policy

- Sync first attempt + up to 2 sync retries with 200ms / 800ms backoff (under the 120s cap with 10s timeouts).
- If still failing, enqueue Queueable retry: 30s, 5min, 30min.
- Idempotency-Key = `Payment__c.Id` + first attempt timestamp, stored in `Payment__c.Idempotency_Key__c` so every retry sends the same value.
- After 5 total attempts, write to `Failed_Callout__c` and notify ops via Platform Event.

### Shape

```apex
public with sharing class PaymentChargeService {
    public static void charge(Id paymentId) {
        Payment__c p = [SELECT Id, Amount__c, Idempotency_Key__c
                        FROM Payment__c WHERE Id = :paymentId];
        if (String.isBlank(p.Idempotency_Key__c)) {
            p.Idempotency_Key__c = paymentId + ':' + System.now().getTime();
            update p;
        }
        if (CalloutCircuitBreaker.isOpen('payment-api')) {
            throw new CalloutException('Circuit open for payment-api');
        }
        CalloutResult r = ResilientHttpClient.post(
            'callout:Payment_API/charges',
            buildPayload(p),
            new Map<String, String>{'Idempotency-Key' => p.Idempotency_Key__c},
            new RetryPolicy(3, new List<Integer>{200, 800, 2000})
        );
        if (!r.isSuccess() && r.isRetryable()) {
            System.enqueueJob(new PaymentChargeQueueable(paymentId, 1));
        } else if (!r.isSuccess()) {
            DeadLetter.write('payment-api', p, r);
        }
    }
}
```

### Test

`MockHttpResponseGenerator` returns: 503, 503, 200. Assert exactly 3 callouts, payment marked Paid, idempotency key unchanged across retries.

---

## Scenario 2 — Webhook Publisher with Circuit Breaker

### Problem

A trigger publishes Account changes to a partner webhook. The partner endpoint flaps under load. We must NOT keep hammering when it's clearly down — we damage the partner and burn our 100-callout budget.

### Policy

- Async via Queueable launched from trigger handler (no sync callouts from triggers anyway).
- Circuit breaker: 5 failures within 60s opens the breaker for 30s, then transitions to HALF-OPEN with 1 probe.
- No Idempotency-Key needed (webhook is informational; downstream is fine with dupes).
- After 3 failed attempts on a single event, dead-letter it. Do NOT block the trigger.

### Shape

```apex
public class PartnerWebhookQueueable implements Queueable, Database.AllowsCallouts {
    private Id accountId;
    private Integer attempt;
    public PartnerWebhookQueueable(Id accountId, Integer attempt) {
        this.accountId = accountId; this.attempt = attempt;
    }
    public void execute(QueueableContext c) {
        if (CalloutCircuitBreaker.isOpen('partner-webhook')) {
            DeadLetter.write('partner-webhook', accountId, 'circuit_open');
            return;
        }
        CalloutResult r = ResilientHttpClient.post(
            'callout:Partner_Webhook/notify',
            buildPayload(accountId), null, RetryPolicy.singleAttempt());
        if (r.isSuccess()) {
            CalloutCircuitBreaker.recordSuccess('partner-webhook');
        } else {
            CalloutCircuitBreaker.recordFailure('partner-webhook');
            if (attempt < 3) {
                System.enqueueJob(new PartnerWebhookQueueable(
                    accountId, attempt + 1));
            } else {
                DeadLetter.write('partner-webhook', accountId, r);
            }
        }
    }
}
```

### Test

Mock returns 5 consecutive 503s. Assert circuit transitions to OPEN after 5 failures, the 6th call short-circuits without issuing a callout, dead-letter row written.

---

## Scenario 3 — Third-party Search API Timeout Handling

### Problem

A Lightning page calls an Apex `@AuraEnabled` method that hits a third-party search API. P95 is 800ms but P99 spikes to 8s. Users cancel after 3s. We need fast-fail with a retry, not a long hang.

### Policy

- Sync (user-facing). 2 attempts max, with 2.5s timeout each. Total upper bound: 5s.
- 408 / 504 / network-timeout retry once. 400 / 401 / 422 fail fast.
- No circuit breaker (read-only, low volume per user). No idempotency (read-only).
- On exhaustion, return a structured "search temporarily unavailable" envelope, NOT an exception that crashes the LWC.

### Shape

```apex
@AuraEnabled
public static SearchResult search(String query) {
    RetryPolicy policy = new RetryPolicy(2, new List<Integer>{0, 250});
    CalloutResult r = ResilientHttpClient.get(
        'callout:Search_API/q?text=' + EncodingUtil.urlEncode(query, 'UTF-8'),
        null, policy, 2500 /* timeoutMs */);
    if (r.isSuccess()) return SearchResult.parse(r.body);
    return SearchResult.unavailable(r.lastStatusCode);
}
```

### Test

Mock sequence: 504, 200. Assert two callouts, parsed result returned. Second test: 504, 504. Assert `SearchResult.unavailable` returned (no exception thrown to LWC).
