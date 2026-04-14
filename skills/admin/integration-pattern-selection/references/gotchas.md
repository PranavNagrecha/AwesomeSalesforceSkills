# Gotchas — Integration Pattern Selection

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Salesforce Cannot Participate in Distributed Transactions Across Multiple Systems

**What happens:** When architects design multi-system orchestration in Apex — calling ERP, shipping, and billing systems in sequence — Salesforce DML can be rolled back on an Apex exception, but external system calls that succeeded before the exception cannot be reversed. If the billing system call fails at step 3, ERP and shipping already created records that cannot be undone by the Apex transaction rollback. The systems are left in an inconsistent state.

**When it occurs:** Whenever an Apex trigger or scheduled job makes multiple sequential HTTP callouts to different external systems and tries to handle failure by catching exceptions.

**How to avoid:** Multi-system transactions with cross-system rollback requirements must be orchestrated by middleware (MuleSoft, Boomi). Salesforce participates as an endpoint (Remote Call-In) or as an event source (fires a Platform Event); it does not orchestrate the cross-system transaction.

---

## Gotcha 2: Synchronous Callout Timeout Is 120 Seconds — Not Indefinite

**What happens:** Apex HTTP callouts timeout after 120 seconds. If an external system takes longer than 120 seconds to respond — common for high-latency ERP systems, large file processing, or ML inference endpoints — the callout throws a System.CalloutException and the Salesforce transaction may rollback. Any Salesforce DML that was part of the same transaction is also rolled back.

**When it occurs:** When a synchronous Request/Reply pattern is chosen for integrations with external systems that do not have guaranteed sub-120-second response times.

**How to avoid:** Apply the timing test rigorously: if the external system cannot guarantee sub-60-second responses (allowing margin), the integration must use an asynchronous Fire-and-Forget pattern with a callback mechanism. Never choose synchronous for integrations with unknown or variable external response times.

---

## Gotcha 3: Platform Events Are Eventually Consistent — Not Guaranteed Delivery

**What happens:** Platform Events have a 72-hour replay window, and EventBus.RetryableException provides up to 9 automatic retries. After 9 failures, the subscriber trigger is suspended and does not process new events until manually re-enabled. Events that were published while the trigger was suspended are replayed only if the Replay ID mechanism works correctly — Replay ID can be stale after Salesforce maintenance events.

**When it occurs:** When Platform Events are selected as the Fire-and-Forget mechanism without designing a dead-letter monitoring and trigger suspension recovery pattern.

**How to avoid:** Any integration using Platform Events must include: (1) monitoring for trigger suspension, (2) a dead-letter queue pattern for failed events, and (3) a replay recovery procedure after org maintenance windows. Do not select Platform Events for integrations that require guaranteed single delivery or strong ordering guarantees.
