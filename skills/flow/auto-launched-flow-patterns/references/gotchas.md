# Gotchas — Auto-Launched Flow Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Shared Governor Limits With the Calling Apex Transaction

**What happens:** An auto-launched Flow invoked via `Flow.Interview.start()` runs synchronously inside the calling Apex transaction. Every SOQL query, DML statement, CPU millisecond, and heap byte consumed inside the Flow counts against the same limits as the Apex code. If the Flow runs a Get Records element (one SOQL query) and the calling trigger already issued 95 queries for 100 records, the 100-query limit is breached and a `System.LimitException` rolls back the entire transaction.

**When it occurs:** Most commonly in trigger contexts processing large batches (standard batch size is 200 records), in `Database.Batchable` execute methods, and in any trigger that already calls multiple SOQL queries before invoking the Flow. It also occurs when multiple trigger handlers each invoke separate Flows in the same transaction.

**How to avoid:**
- Profile the Flow's SOQL and DML footprint before deploying it in a bulk trigger context using the Flow debugger's limit usage panel.
- Design the Flow to accept a collection input rather than querying data itself when Apex can pass the data in.
- Keep a governor limit budget document for each trigger: total SOQL = Apex queries + (Flow queries × max interview count).
- Consider moving the invocation to a Platform Event trigger if the Flow logic does not need to run synchronously in the same transaction.

---

## Gotcha 2: Private Flow Variables Are Invisible to External Callers

**What happens:** A developer sets up a Flow with a variable intended to receive input from Apex or a REST caller, but the variable's Input/Output Type is set to "Private" (the default). The Flow runs, but the variable is never populated — it stays at its default value (null or empty). The Flow may silently produce wrong results rather than throwing an error, making the bug hard to detect.

**When it occurs:** Whenever a developer creates a new Flow variable in Flow Builder and does not change the Access setting from "Private" to "Input and Output" or "Input Only." The UI default is "Private." Similarly, when reviewing an existing Flow, the Access setting is not prominently displayed in the variable list — it requires opening each variable to inspect.

**How to avoid:**
- Before calling `interview.start()`, verify each input variable's Access setting by opening the Flow in Flow Builder → the Resources panel → Variables → click each variable → confirm Input/Output Type.
- Name input variables with an `input` prefix and output variables with an `output` prefix (e.g., `inputAccountId`, `outputCaseId`) as a convention that signals intent and prompts reviewers to check the Access setting.
- In the checker script, parse the Flow metadata XML and assert that any variable whose API name starts with `input` or `output` has the corresponding AccessType.

---

## Gotcha 3: Flow API Name Is Case-Sensitive in Apex and REST Calls

**What happens:** `Flow.Interview.createInterview('my_flow', inputs)` and `Flow.Interview.createInterview('My_Flow', inputs)` resolve differently. If the stored Flow API name is `My_Flow` and the Apex code passes `my_flow`, Salesforce throws a runtime exception: `"FLOW_INTERVIEW_EXCEPTION: The flow my_flow doesn't exist."` This is particularly dangerous after a Flow is cloned or renamed — the API name in code goes stale without a compile error.

**When it occurs:** Most commonly when:
- A developer types the Flow API name from memory rather than copying it from Setup.
- A Flow is renamed in Setup and the Apex caller is not updated.
- A Flow is deployed from a sandbox where the API name was typed with different capitalisation.

**How to avoid:**
- Always copy the Flow API name from Setup > Flows > the Flow's detail page, not from the Flow label.
- Store Flow API names as named constants (`private static final String PRICING_FLOW = 'Calculate_Opportunity_Discount';`) in a single class so there is one place to update if the Flow is renamed.
- The checker script (`check_auto_launched_flow_patterns.py`) can scan Apex files for `Flow.Interview.createInterview` calls and cross-reference the quoted name against deployed Flow metadata XML filenames.

---

## Gotcha 4: Unhandled Fault Paths Propagate as FlowException and Roll Back the Transaction

**What happens:** If a Flow element (Get Records, Create Records, Update Records, Send Email, etc.) encounters an error and there is no Fault connector on that element, Salesforce throws an unhandled fault. When invoked from Apex, this surfaces as a `System.FlowException`. If not caught in Apex, it propagates up the call stack and rolls back the entire transaction — including any DML the caller already committed. Users see an unhelpful "We couldn't save this record" message.

**When it occurs:** Whenever a developer builds a Flow that has DML elements without Fault connectors and the element encounters a data integrity error (e.g., a duplicate rule violation, a required field missing, a record-lock conflict) in production.

**How to avoid:**
- Add a Fault connector to every element that can fail (Get Records, Create/Update/Delete Records, external calls, Send Email actions).
- On the fault path, use an Assignment element to write `{!$Flow.FaultMessage}` to a Text variable, then either create an Error_Log__c record or send an email to the admin alias.
- In Apex, always wrap `interview.start()` in a try/catch for `System.FlowException` and log `e.getMessage()` before rethrowing or returning a user-friendly message.

---

## Gotcha 5: Platform Event-Triggered Flows May Process Events Out of Order

**What happens:** When multiple Platform Events fire in rapid succession, the auto-launched Flow subscribes and processes them, but event delivery order is not guaranteed within a high-throughput burst. A Flow that assumes sequential ordering (e.g., "process Order_Fulfillment__e before Order_Cancellation__e") may apply logic in the wrong sequence, leading to inconsistent record states.

**When it occurs:** In high-volume integration scenarios where the same event type can fire multiple times for the same record in close succession — order management, payment processing, IoT data ingestion.

**How to avoid:**
- Design Platform Event-triggered Flows to be idempotent: running the same event twice produces the same result as running it once.
- Include a `Replay_Id__c` or `Event_Timestamp__c` field on the event and use a Decision element in the Flow to skip processing if the current record state is already at a later stage.
- For strict ordering requirements, use Apex EventBus subscribers with `Database.Stateful` batch processing instead of Flow.
