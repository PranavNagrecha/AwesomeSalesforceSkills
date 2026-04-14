# Examples — Error Handling in Integrations

## Example 1: Trigger Suspension Due to Permanent Error Misclassified as Transient

**Context:** An Order integration uses Platform Events. The trigger throws `EventBus.RetryableException` on every exception, including schema validation failures when the external system returns malformed JSON.

**Problem:** A deployment on the external side introduces a new required field that the Salesforce subscriber doesn't handle. The malformed payloads hit the subscriber. Because RetryableException is thrown for all errors, the platform retries 9 times. After 9 failures, the trigger is suspended — all 200 new order events published in the next hour queue up but are not processed.

**Solution:**
Differentiate transient vs permanent errors:
```apex
} catch (JSONException e) {
    // Permanent: malformed JSON cannot be fixed by retrying
    // Write to DLQ, alert ops, do NOT throw RetryableException
    insert new Integration_DLQ__c(
        Event_Type__c = 'OrderEvent__e',
        Payload__c = rawPayload,
        Error_Message__c = 'JSON parse failure: ' + e.getMessage(),
        Status__c = 'Pending_Retry'
    );
    // Fire error notification event
    EventBus.publish(new Integration_Error__e(
        Error_Type__c = 'PERMANENT',
        Message__c = 'OrderEvent JSON parse failure — manual review required'
    ));
    // Return normally — do NOT throw RetryableException
}
```

**Why it works:** Only transient exceptions (network timeout, temporary 503) trigger RetryableException. Permanent data errors write to DLQ and notify ops. The trigger is not suspended for bad payloads.

---

## Example 2: Circuit Breaker Preventing API Limit Exhaustion

**Context:** An integration calls an external billing API on every Invoice record creation. The billing API has an SLA of 99.5% uptime, meaning it is unavailable for ~44 minutes/month. During downtime, the integration hammers the API with retries until Salesforce API limits are exhausted.

**Solution:**
Circuit breaker implementation using Custom Setting:
```apex
Integration_Circuit_Breaker__c cb = Integration_Circuit_Breaker__c.getInstance('BillingAPI');

if (cb.State__c == 'OPEN') {
    if (cb.Open_Until__c > Datetime.now()) {
        // Circuit is OPEN — skip call, write to DLQ, return
        insert new Integration_DLQ__c(Status__c = 'Circuit_Open');
        return;
    } else {
        // Cooldown expired: move to HALF_OPEN
        cb.State__c = 'HALF_OPEN';
        update cb;
    }
}

// Make the call
try {
    callBillingAPI(invoice);
    // Success: CLOSE circuit, reset counter
    cb.State__c = 'CLOSED';
    cb.Failure_Count__c = 0;
    update cb;
} catch (System.CalloutException e) {
    cb.Failure_Count__c = (cb.Failure_Count__c ?? 0) + 1;
    if (cb.Failure_Count__c >= 5) {
        cb.State__c = 'OPEN';
        cb.Open_Until__c = Datetime.now().addMinutes(10);
        // Notify ops
    }
    update cb;
}
```

**Why it works:** The circuit breaker stops API calls during external downtime, prevents API limit exhaustion, and provides a self-healing cooldown mechanism. DLQ accumulates failed invoices for processing after the circuit closes.

---

## Anti-Pattern: No DLQ — Failed Events Are Silently Discarded

**What practitioners do:** They build Platform Event subscribers that catch exceptions, log to debug, and return normally. Failed events are not retried and not stored anywhere.

**What goes wrong:** Integration failures are invisible to operations. Records never sync to the external system. Data drifts silently between systems. The issue is only discovered when a customer calls about a missing order weeks later.

**Correct approach:** Permanent errors must be written to a DLQ object — never silently discarded. A DLQ provides: (1) an audit trail of all failures, (2) retry capability, and (3) a visible signal for operations to investigate.
