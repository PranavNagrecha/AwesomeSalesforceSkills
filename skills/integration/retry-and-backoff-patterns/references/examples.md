# Examples — Retry and Backoff Patterns

## Example 1: Queueable Retry Chain with Exponential Backoff and Jitter

**Context:** An Apex integration sends order data to an external ERP via REST. The ERP occasionally returns HTTP 503 (Service Unavailable) under load. The original callout was in a trigger and has been moved to a Queueable.

**Problem:** Without retry logic, a 503 response causes the record to be silently skipped. Developers add a for-loop retry in the same transaction, which hammers the endpoint 3 times in milliseconds and still fails under load.

**Solution:**

```apex
public class OrderSyncJob implements Queueable, Database.AllowsCallouts {

    private static final Integer BASE_DELAY_SECONDS = 2;
    private static final Integer MAX_RETRIES = 4;

    private Id orderId;
    private Integer retryCount;
    private String idempotencyKey;

    public OrderSyncJob(Id orderId, Integer retryCount, String idempotencyKey) {
        this.orderId = orderId;
        this.retryCount = retryCount;
        this.idempotencyKey = idempotencyKey;
    }

    public void execute(QueueableContext ctx) {
        // Check circuit breaker before attempting callout
        Circuit_Breaker_Config__mdt cbConfig = Circuit_Breaker_Config__mdt.getInstance('ERP_Integration');
        if (cbConfig != null && cbConfig.Is_Open__c) {
            Datetime coolDownUntil = cbConfig.Opened_At__c.addMinutes((Integer)cbConfig.Cool_Down_Minutes__c);
            if (Datetime.now() < coolDownUntil) {
                logDeadLetter(orderId, 'Circuit breaker open — skipping callout', 0, retryCount);
                return;
            }
        }

        Order__c order = [SELECT Id, Name, Total__c, External_Id__c FROM Order__c WHERE Id = :orderId LIMIT 1];

        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ERP_Named_Credential/orders');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setHeader('X-Idempotency-Key', idempotencyKey);
        req.setBody('{"orderId":"' + order.Name + '","total":' + order.Total__c + '}');
        req.setTimeout(10000); // 10 seconds

        Http http = new Http();
        HttpResponse res;

        try {
            res = http.send(req);
        } catch (System.CalloutException ex) {
            handleFailure(orderId, ex.getMessage(), 0, retryCount);
            return;
        }

        if (res.getStatusCode() >= 200 && res.getStatusCode() < 300) {
            // Success — update order sync status
            order.Sync_Status__c = 'Synced';
            order.Last_Sync__c = Datetime.now();
            update order;
        } else {
            handleFailure(orderId, res.getBody(), res.getStatusCode(), retryCount);
        }
    }

    private void handleFailure(Id orderId, String errorMsg, Integer statusCode, Integer currentRetry) {
        if (currentRetry < MAX_RETRIES) {
            // Calculate backoff: baseDelay * 2^retryCount + jitter
            Double jitter = BASE_DELAY_SECONDS * Math.random();
            Double delaySeconds = BASE_DELAY_SECONDS * Math.pow(2, currentRetry) + jitter;
            // Note: Queueable scheduling does not enforce exact delay;
            // delaySeconds is recorded in the log for observability.
            logRetryAttempt(orderId, errorMsg, statusCode, currentRetry, (Integer)delaySeconds);
            System.enqueueJob(new OrderSyncJob(orderId, currentRetry + 1, idempotencyKey));
        } else {
            logDeadLetter(orderId, errorMsg, statusCode, currentRetry);
        }
    }

    private void logRetryAttempt(Id orderId, String errorMsg, Integer statusCode, Integer retryCount, Integer delaySeconds) {
        // DML must happen after callout block — safe here since callout is complete
        Failed_Integration_Log__c log = new Failed_Integration_Log__c(
            Record_Id__c = orderId,
            Error_Message__c = errorMsg,
            HTTP_Status__c = statusCode,
            Retry_Count__c = retryCount,
            Status__c = 'Retrying',
            Calculated_Delay_Seconds__c = delaySeconds,
            Timestamp__c = Datetime.now()
        );
        insert log;
    }

    private void logDeadLetter(Id orderId, String errorMsg, Integer statusCode, Integer retryCount) {
        Failed_Integration_Log__c log = new Failed_Integration_Log__c(
            Record_Id__c = orderId,
            Error_Message__c = errorMsg,
            HTTP_Status__c = statusCode,
            Retry_Count__c = retryCount,
            Status__c = 'Dead Letter',
            Timestamp__c = Datetime.now()
        );
        insert log;
        // Optionally publish a Platform Event to notify an ops flow
        // EventBus.publish(new Integration_Alert__e(Record_Id__c = orderId, Message__c = errorMsg));
    }
}
```

**Why it works:** Each retry is a new Queueable execution. The retry counter increments on each enqueue. The exponential backoff + jitter formula scatters retry attempts across a time window, preventing thundering-herd. The idempotency key is passed unchanged through all retries, preventing duplicate ERP records if an earlier attempt succeeded but the response was lost.

---

## Example 2: Idempotency Key Generation and Upsert Guard

**Context:** An integration creates Account records in a downstream CRM. When the Salesforce callout times out, the downstream CRM has already created the Account, but Salesforce retries and creates a duplicate.

**Problem:** Retrying without an idempotency key sends an identical payload. If the first request succeeded (response lost), the downstream system creates two Accounts with the same name.

**Solution:**

```apex
// Before enqueueing the first attempt, generate and store the idempotency key
public static void initiateSync(Id accountId) {
    Account acc = [SELECT Id, External_CRM_Id__c FROM Account WHERE Id = :accountId LIMIT 1];

    // Generate a stable idempotency key if not already set
    if (String.isBlank(acc.External_CRM_Id__c)) {
        acc.External_CRM_Id__c = generateIdempotencyKey(accountId);
        update acc;
    }

    System.enqueueJob(new AccountSyncJob(accountId, 0, acc.External_CRM_Id__c));
}

// Deterministic key based on Salesforce record Id — same Id always produces same key
private static String generateIdempotencyKey(Id recordId) {
    Blob hash = Crypto.generateDigest('SHA-256', Blob.valueOf(String.valueOf(recordId)));
    return EncodingUtil.convertToHex(hash).left(32);
}
```

```apex
// In the callout handler, pass the key in the request
req.setHeader('X-Idempotency-Key', idempotencyKey);

// On the Salesforce side, if the downstream system returns the new external ID,
// upsert using External_CRM_Id__c to prevent duplicate Account creation on reprocessing
Account incoming = new Account(
    External_CRM_Id__c = idempotencyKey,
    Name = responsePayload.get('name'),
    Sync_Status__c = 'Synced'
);
Database.upsert(incoming, Account.External_CRM_Id__c, false);
```

**Why it works:** The idempotency key is deterministic (derived from the Salesforce record Id), so it is identical on every retry. The downstream system uses the key to detect and discard duplicate requests. The `Database.upsert` on the Salesforce side prevents double-inserts if the integration callback fires more than once.

---

## Example 3: Circuit Breaker Custom Metadata Check

**Context:** An external payment gateway degrades for 30 minutes during a deployment window. Without a circuit breaker, every Order sync attempt during this window burns a Queueable execution, fills `Failed_Integration_Log__c` with noise, and delays recovery of other integrations sharing the async limit.

**Problem:** Naive retry logic treats every 503 as a transient error and keeps retrying indefinitely, exhausting the daily async Apex limit.

**Solution:**

```apex
// Custom Metadata: Circuit_Breaker_Config__mdt
// Fields: DeveloperName (Text), Is_Open__c (Checkbox), Opened_At__c (DateTime),
//         Cool_Down_Minutes__c (Number)

// At the start of execute():
Circuit_Breaker_Config__mdt cbConfig =
    Circuit_Breaker_Config__mdt.getInstance('Payment_Gateway');

if (cbConfig != null && cbConfig.Is_Open__c) {
    Datetime coolDownExpiry = cbConfig.Opened_At__c.addMinutes(
        (Integer)cbConfig.Cool_Down_Minutes__c
    );
    if (Datetime.now() < coolDownExpiry) {
        // Circuit is open and cool-down has not elapsed — skip callout
        System.debug('Circuit breaker OPEN for Payment_Gateway. Skipping callout.');
        return;
    }
    // Cool-down elapsed — half-open: attempt callout
    // On success: operator manually sets Is_Open__c = false via Setup UI or Flow
}

// ... proceed with callout
```

**Why it works:** Custom Metadata is cached at the platform level after the first read in a request context — it does not consume SOQL per transaction. Operators can toggle `Is_Open__c` in Setup without a code deploy. The cool-down window prevents half-open retry storms by spacing out recovery probes.

---

## Anti-Pattern: Retry Loop Inside a Synchronous Transaction

**What practitioners do:** Add a `for` loop in a trigger, Visualforce action, or LWC controller that retries a callout up to 3 times before throwing.

**What goes wrong:**
- All 3 attempts happen within milliseconds of each other — no backoff, no jitter, no effective delay.
- Each loop iteration consumes one of the 100 callouts allowed per transaction.
- DML before the loop (e.g., updating a status field) triggers the "callout after uncommitted work" exception on the first `Http.send()`.
- The synchronous transaction has no mechanism for the idempotency key to persist if the transaction rolls back.

**Correct approach:** Move the callout to a Queueable. Use Queueable chaining (re-enqueue) for retries. The platform's async scheduling provides the delay; the retry counter persists on the job instance.
