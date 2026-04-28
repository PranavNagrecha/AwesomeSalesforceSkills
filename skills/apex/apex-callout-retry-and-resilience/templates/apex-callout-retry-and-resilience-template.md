# Template — Apex Callout Retry and Resilience

This template is the **strategy-layer** scaffold. It does NOT replace the HTTP plumbing — that lives in `templates/apex/HttpClient.cls`. This template wraps `HttpClient` with retry policy, circuit breaker, and dead-letter behavior.

## Section A — Synchronous Bounded Retry

Use when: caller is user-facing OR latency budget < 30s.

```apex
public class ResilientHttpClient {

    public static CalloutResult post(String endpoint, String body,
                                     Map<String, String> headers,
                                     RetryPolicy policy, Integer timeoutMs) {
        CalloutResult last = null;
        Integer attempt = 0;
        while (attempt < policy.maxAttempts) {
            if (Limits.getCallouts() >= Limits.getLimitCallouts() - 1) {
                // No headroom; bail.
                return CalloutResult.budgetExhausted();
            }
            attempt++;
            try {
                HttpRequest req = HttpClient.buildPost(
                    endpoint, body, headers, timeoutMs);
                HttpResponse resp = new Http().send(req);
                last = CalloutResult.from(resp);
                if (last.isSuccess() || !last.isRetryable()) {
                    return last;
                }
            } catch (CalloutException e) {
                last = CalloutResult.fromException(e);
                if (!last.isRetryable()) return last;
            }
            // "Backoff" is just CPU work between attempts;
            // do NOT busy-wait on System.now().
            // Real backoff requires async — see Section B.
            if (attempt < policy.maxAttempts) {
                doMinimalCpuWork(policy.backoffMs[attempt - 1]);
            }
        }
        return last;
    }

    private static void doMinimalCpuWork(Integer hintMs) {
        // Intentionally empty: there is no legal sync sleep in Apex.
        // For real delay, use the Queueable chain pattern (Section B).
    }
}

public class RetryPolicy {
    public Integer maxAttempts;
    public List<Integer> backoffMs; // length = maxAttempts - 1
    public RetryPolicy(Integer maxAttempts, List<Integer> backoffMs) {
        this.maxAttempts = maxAttempts;
        this.backoffMs = backoffMs;
    }
    public static RetryPolicy singleAttempt() {
        return new RetryPolicy(1, new List<Integer>());
    }
}
```

## Section B — Queueable Async Retry Chain

Use when: backoff > a few seconds, OR fire-and-forget acceptable.

```apex
public class CalloutRetryQueueable implements Queueable, Database.AllowsCallouts {

    private final Id sourceId;
    private final String endpointName;
    private final Integer attempt;
    private final List<Integer> backoffSchedule; // seconds

    public CalloutRetryQueueable(Id sourceId, String endpointName,
                                 Integer attempt, List<Integer> backoffSchedule) {
        this.sourceId = sourceId;
        this.endpointName = endpointName;
        this.attempt = attempt;
        this.backoffSchedule = backoffSchedule;
    }

    public void execute(QueueableContext ctx) {
        if (CalloutCircuitBreaker.isOpen(endpointName)) {
            DeadLetter.write(endpointName, sourceId, 'circuit_open', attempt);
            return;
        }
        CalloutResult r = doCallout(sourceId, endpointName);
        if (r.isSuccess()) {
            CalloutCircuitBreaker.recordSuccess(endpointName);
            return;
        }
        CalloutCircuitBreaker.recordFailure(endpointName);
        if (!r.isRetryable() || attempt >= backoffSchedule.size()) {
            DeadLetter.write(endpointName, sourceId, r, attempt);
            return;
        }
        // Re-enqueue with attempt + 1.
        // Actual delay enforcement: a Scheduled Apex picker reads
        // a Pending_Retry__c queue ordered by next_attempt_at.
        Pending_Retry__c next = new Pending_Retry__c(
            Source_Id__c = sourceId,
            Endpoint__c = endpointName,
            Attempt__c = attempt + 1,
            Next_Attempt_At__c = System.now().addSeconds(
                backoffSchedule[attempt - 1])
        );
        insert next;
    }
}
```

A scheduled job (every 1 minute) reads `Pending_Retry__c WHERE Next_Attempt_At__c <= NOW()` and enqueues the next `CalloutRetryQueueable`.

## Section C — Circuit Breaker via Cache.Org

```apex
public class CalloutCircuitBreaker {

    private static final Integer THRESHOLD = 5;       // failures
    private static final Integer WINDOW_S = 60;       // seconds
    private static final Integer COOLDOWN_S = 30;     // open -> half-open

    public static Boolean isOpen(String endpoint) {
        State s = readState(endpoint);
        if (s.status == 'OPEN' && System.now() < s.openUntil) {
            return true;
        }
        return false;
    }

    public static void recordSuccess(String endpoint) {
        writeState(endpoint, new State('CLOSED', 0, null));
    }

    public static void recordFailure(String endpoint) {
        State s = readState(endpoint);
        Integer newCount = s.failureCount + 1;
        if (newCount >= THRESHOLD) {
            writeState(endpoint, new State(
                'OPEN', 0, System.now().addSeconds(COOLDOWN_S)));
        } else {
            writeState(endpoint, new State('CLOSED', newCount, null));
        }
    }

    private static String key(String endpoint) {
        return 'ckt:' + endpoint.toLowerCase();
    }

    private static State readState(String endpoint) {
        Object raw = Cache.Org.get(key(endpoint));
        return raw == null
            ? new State('CLOSED', 0, null)
            : (State) raw;
    }

    private static void writeState(String endpoint, State s) {
        Cache.Org.put(key(endpoint), s, WINDOW_S);
    }

    public class State {
        public String status; // CLOSED | OPEN | HALF_OPEN
        public Integer failureCount;
        public DateTime openUntil;
        public State(String status, Integer fc, DateTime openUntil) {
            this.status = status;
            this.failureCount = fc;
            this.openUntil = openUntil;
        }
    }
}
```

## Section D — Dead-Letter Object

```text
Failed_Callout__c custom sObject:
  Endpoint__c             Text(80)
  Source_Record_Id__c     Text(18)
  Payload__c              LongTextArea(131072)
  Last_Status_Code__c     Number(3,0)
  Last_Response_Body__c   LongTextArea(32768)
  Attempt_Count__c        Number(2,0)
  Last_Error__c           Text(255)
  Reprocess_Status__c     Picklist(Pending, Reprocessing, Resolved, Abandoned)
```

## Verification

- [ ] `ResilientHttpClient.post` returns within `maxAttempts * (timeoutMs + backoffMs) < 90_000ms`
- [ ] 4xx responses (except 408/429) DO NOT trigger retry
- [ ] `Limits.getCallouts()` checked before every retry
- [ ] Queueable marked `Database.AllowsCallouts`
- [ ] Circuit-breaker key includes `endpoint.toLowerCase()`
- [ ] `Cache.Org.put` TTL aligned with WINDOW_S
- [ ] `Failed_Callout__c` insert occurs on exhaustion AND on circuit-open short-circuit
- [ ] Test class with sequenced `MockHttpResponseGenerator` covers: success-on-2nd, exhaustion, 4xx-no-retry, circuit-open
- [ ] Idempotency-Key persisted on source record before first attempt and reused on every retry
- [ ] No `System.now()` busy-wait loops anywhere in the call path
