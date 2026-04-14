# LLM Anti-Patterns — Error Handling in Integrations

Common mistakes AI coding assistants make when generating or advising on integration error handling. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Throwing RetryableException for All Exceptions

**What the LLM generates:**
```apex
} catch (Exception e) {
    throw new EventBus.RetryableException(e.getMessage());
}
```

**Why it happens:** LLMs model RetryableException as the "correct" catch-all error handler for Platform Event triggers. It appears in most documentation examples as the mechanism for ensuring message delivery.

**Correct pattern:**
```apex
} catch (MyService.TransientException e) {
    throw new EventBus.RetryableException(e.getMessage()); // Transient: retry
} catch (Exception e) {
    // Permanent: write to DLQ, do NOT throw RetryableException
    insert new Integration_DLQ__c(Payload__c = JSON.serialize(event),
        Error_Message__c = e.getMessage(), Status__c = 'Pending_Retry');
    // Return normally — trigger continues processing other events
}
```

**Detection hint:** Any `catch (Exception e)` block in a Platform Event trigger that throws `RetryableException` without first checking if the error is transient.

---

## Anti-Pattern 2: No DLQ — Silently Discarding Failed Events

**What the LLM generates:**
```apex
} catch (Exception e) {
    System.debug('Integration error: ' + e.getMessage());
    // Continue processing
}
```

**Why it happens:** LLMs model error handling as catching exceptions and logging them. They don't model that failed integration events silently discarded cause permanent data loss and invisible data drift.

**Correct pattern:**
```
Failed integration events MUST be persisted to a DLQ:
- Custom object: Integration_DLQ__c
- Fields: Source, Event_Type, Payload (JSON), Error_Message, Retry_Count, Status
- Never silently discard — even "non-critical" events need an audit trail
```

**Detection hint:** catch blocks that only call `System.debug()` or log to a generic Logger without persisting to a DLQ object.

---

## Anti-Pattern 3: No Replay ID Tracking

**What the LLM generates:** Platform Event subscriber trigger code with no mechanism to store the last processed Replay ID.

**Why it happens:** LLMs generate Platform Event trigger code focused on business logic. They don't model the operational recovery requirement for storing Replay IDs to enable recovery from trigger suspension.

**Correct pattern:**
```apex
// After successful processing, store Replay ID
Integration_State__c state = Integration_State__c.getInstance();
state.Last_Replay_Id__c = event.ReplayId;
state.Last_Event_Id__c = event.Id; // Stable deduplication key
update state;
```

**Detection hint:** Platform Event trigger code with no reference to `ReplayId` property storage or a Custom Setting tracking the last processed position.

---

## Anti-Pattern 4: No Ops Notification on Integration Failure

**What the LLM generates:** DLQ implementation that writes records to a custom object but has no mechanism to alert the operations team when failures occur.

**Why it happens:** LLMs focus on the technical implementation (DLQ object creation) without modeling the operational process (someone needs to know there are failures to fix).

**Correct pattern:**
```apex
// After writing to DLQ, publish an error notification event
EventBus.publish(new Integration_Error__e(
    Error_Type__c = severity, // 'CRITICAL', 'WARNING', 'INFO'
    Source_System__c = 'OrderAPI',
    Message__c = 'Order integration failure — manual review required',
    Record_Count__c = 1
));
// Flow subscriber on Integration_Error__e routes to email/Slack/Case based on severity
```

**Detection hint:** DLQ implementation without a corresponding notification mechanism — failures go undetected.

---

## Anti-Pattern 5: No Circuit Breaker for Unstable External Systems

**What the LLM generates:** Apex callout code with retry logic but no circuit breaker — retrying the same failing external endpoint indefinitely until Salesforce API limits are exhausted.

**Why it happens:** LLMs implement retry logic (correct for transient failures) but don't model the circuit breaker pattern needed when the external system is consistently unavailable.

**Correct pattern:**
```
Circuit breaker states stored in Custom Setting:
- CLOSED: normal — calls go through
- OPEN: system down — skip all calls, write to DLQ, notify ops
  (opened when failure count > threshold, remains open for cooldown period)
- HALF_OPEN: testing recovery — attempt one call
  (success: CLOSE; failure: re-OPEN)
```

**Detection hint:** Retry/callout code that attempts the same external endpoint up to the max retry count with no circuit state check or automatic backoff to a OPEN/skip state.
