# Error Handling In Integrations — Work Template

Use this template when designing or reviewing integration error handling in a Salesforce project.

## Scope

**Skill:** `error-handling-in-integrations`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer these before designing error handling:

- **Integration pattern in use:** (Platform Events / REST API callout / CDC / Bulk API)
- **Current error visibility:** (How are failures currently surfaced — debug logs only? Alerts? Nothing?)
- **Recovery requirement:** (Must failed messages be replayed? Can they be discarded? SLA for recovery?)
- **External system stability:** (Is the external endpoint reliable? Any known downtime patterns? SLA uptime?)
- **Message volume:** (Events per hour at peak? Relevant for DLQ retry job governor limit sizing)

---

## DLQ Object Schema

```
Object: Integration_DLQ__c
Fields:
- Source_System__c (Text 100)   — which external system or integration type
- Event_Type__c (Text 100)      — Platform Event API name or integration category
- Payload__c (Long Text Area)   — full JSON payload for replay
- Error_Message__c (Text Area)  — exception message and class
- Retry_Count__c (Number)       — current number of retry attempts
- Status__c (Picklist)          — Pending_Retry | Failed_Max_Retries | Resolved
- Last_Attempted__c (DateTime)  — timestamp of most recent retry attempt
```

---

## Platform Event Trigger Error Routing

```apex
// Pattern: RetryableException for transient, DLQ for permanent
trigger <EventName>Trigger on <EventName>__e (after insert) {
    for (<EventName>__e event : Trigger.new) {
        try {
            <ServiceClass>.processEvent(event);
            // Store Replay ID on success
            Integration_State__c state = Integration_State__c.getInstance();
            state.Last_Replay_Id__c = event.ReplayId;
            update state;
        } catch (<ServiceClass>.TransientException e) {
            // Transient: let platform retry (up to 9 times)
            throw new EventBus.RetryableException('Transient: ' + e.getMessage());
        } catch (Exception e) {
            // Permanent: write to DLQ, do NOT throw RetryableException
            insert new Integration_DLQ__c(
                Source_System__c = '<SourceSystem>',
                Event_Type__c = '<EventName>',
                Payload__c = JSON.serialize(event),
                Error_Message__c = e.getMessage(),
                Status__c = 'Pending_Retry',
                Retry_Count__c = 0
            );
            // Notify ops
            EventBus.publish(new Integration_Error__e(
                Error_Type__c = 'PERMANENT',
                Source_System__c = '<SourceSystem>',
                Message__c = '<EventName> processing failure — manual review required',
                Record_Count__c = 1
            ));
        }
    }
}
```

---

## DLQ Scheduled Retry Job

```apex
// Scheduled Apex: retry Pending_Retry DLQ records
public class IntegrationDLQRetryJob implements Schedulable, Database.Batchable<SObject> {
    public static final Integer MAX_RETRIES = 5;

    public void execute(SchedulableContext sc) {
        Database.executeBatch(this, 10); // small batch for governor headroom
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id, Source_System__c, Event_Type__c, Payload__c, Retry_Count__c
            FROM Integration_DLQ__c
            WHERE Status__c = 'Pending_Retry'
            AND Retry_Count__c < :MAX_RETRIES
            ORDER BY CreatedDate ASC
        ]);
    }

    public void execute(Database.BatchableContext bc, List<Integration_DLQ__c> scope) {
        List<Integration_DLQ__c> updates = new List<Integration_DLQ__c>();
        for (Integration_DLQ__c record : scope) {
            try {
                // TODO: invoke the retry handler for this Source_System__c / Event_Type__c
                // <ServiceClass>.retryFromDLQ(record);
                record.Status__c = 'Resolved';
            } catch (Exception e) {
                record.Retry_Count__c = (record.Retry_Count__c ?? 0) + 1;
                if (record.Retry_Count__c >= MAX_RETRIES) {
                    record.Status__c = 'Failed_Max_Retries';
                    // Escalate to ops
                }
            }
            record.Last_Attempted__c = Datetime.now();
            updates.add(record);
        }
        update updates;
    }

    public void finish(Database.BatchableContext bc) {}
}
```

---

## Circuit Breaker — Custom Setting Schema

```
Object: Integration_Circuit_Breaker__c (Hierarchy Custom Setting)
Fields:
- State__c (Text)        — CLOSED | OPEN | HALF_OPEN
- Failure_Count__c (Number) — consecutive failures since last CLOSE
- Open_Until__c (DateTime)  — time when OPEN → HALF_OPEN transition occurs
- Threshold__c (Number)     — failure count that trips the breaker (default: 5)
- Cooldown_Minutes__c (Number) — minutes circuit stays OPEN (default: 10)
```

Circuit breaker usage pattern:

```apex
Integration_Circuit_Breaker__c cb = Integration_Circuit_Breaker__c.getInstance('<IntegrationName>');

if (cb.State__c == 'OPEN') {
    if (cb.Open_Until__c > Datetime.now()) {
        // Still open — skip, write to DLQ, return
        insert new Integration_DLQ__c(Status__c = 'Pending_Retry', /* ... */);
        return;
    }
    cb.State__c = 'HALF_OPEN';
    update cb;
}

try {
    callExternalSystem(); // one attempt in HALF_OPEN
    cb.State__c = 'CLOSED';
    cb.Failure_Count__c = 0;
    update cb;
} catch (System.CalloutException e) {
    cb.Failure_Count__c = (cb.Failure_Count__c ?? 0) + 1;
    if (cb.Failure_Count__c >= cb.Threshold__c) {
        cb.State__c = 'OPEN';
        cb.Open_Until__c = Datetime.now().addMinutes((Integer)cb.Cooldown_Minutes__c);
        // Notify ops
    }
    update cb;
    insert new Integration_DLQ__c(Status__c = 'Pending_Retry', /* ... */);
}
```

---

## Trigger Suspension Recovery Runbook

1. **Confirm suspension:** Setup > Platform Events > [Event Name] > Subscribers > check trigger status shows "Suspended".
2. **Identify last good Replay ID:** Query `Integration_State__c.getInstance().Last_Replay_Id__c`.
3. **Fix root cause:** Deploy corrected trigger code or configuration before re-enabling.
4. **Re-enable with replay:** Setup > Platform Events > [Event Name] > Subscribers > Resume > set Replay Option to "From ID" and enter the stored Replay ID.
5. **Verify:** Monitor trigger execution and DLQ records after re-enabling. Confirm new events process successfully.
6. **Post-mortem:** Document root cause and update `TransientException` / permanent error classification in trigger code.

---

## Cross-Channel Notification Design

| Failure Severity | Notification Channel | Mechanism |
|---|---|---|
| CRITICAL (data loss risk) | Slack + Case creation | Integration_Error__e → Flow → Named Credential callout + Case insert |
| WARNING (DLQ accumulating) | Email alert | Integration_Error__e → Flow Email Alert |
| INFO (single failure, retrying) | DLQ record only | No external notification |

Flow subscriber on `Integration_Error__e`:
- Decision: Route by `Error_Type__c`
- CRITICAL branch: HTTP callout to Slack + create Case (Priority = High)
- WARNING branch: Email Alert to integration-ops@company.com
- INFO branch: No action (DLQ record is sufficient audit trail)

---

## Review Checklist

- [ ] RetryableException used only for transient errors (not permanent)
- [ ] DLQ pattern implemented for permanent failures — Integration_DLQ__c
- [ ] Each event processed in individual try/catch (batch isolation — one bad event does not block others)
- [ ] Replay ID stored in Custom Setting on every successful Platform Event
- [ ] Trigger suspension recovery runbook documented and shared with ops team
- [ ] Cross-channel error notification designed and tested
- [ ] Circuit breaker designed for external systems with known instability
- [ ] DLQ retry job configured with max retry limit (default: 5) and escalation on Failed_Max_Retries
- [ ] DLQ Payload__c field security reviewed — restrict access to integration team only

---

## Notes

(Record any deviations from the standard pattern and the rationale)
