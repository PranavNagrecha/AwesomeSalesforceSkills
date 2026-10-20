# Gotchas — Auto-Launched Flow Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Shared Governor Limits With the Calling Apex Transaction

**What happens:** An auto-launched Flow invoked via `Flow.Interview.start()` runs inside the calling Apex transaction (the package's reading; a documented synchronous guarantee is UNVERIFIED, 2026-10-20). "SOQL and DML limits apply during flow execution" (apexref 262 L157938); CPU and heap sharing are UNVERIFIED (2026-10-20). If the Flow runs a Get Records element (one SOQL query) and the calling trigger already issued 95 queries, the 100-query synchronous limit (apexdev 264 L19747) is breached and a `System.LimitException` rolls back the entire transaction.

**When it occurs:** Most commonly in trigger contexts processing large batches (standard batch size is 200 records), in `Database.Batchable` execute methods, and in any trigger that already calls multiple SOQL queries before invoking the Flow. It also occurs when multiple trigger handlers each invoke separate Flows in the same transaction.

**How to avoid:**
- Profile the Flow's SOQL and DML footprint before deploying it in a bulk trigger context (UNVERIFIED, 2026-10-20: a "limit usage panel" in the Flow debugger is not in the corpus).
- Design the Flow to accept a collection input rather than querying data itself when Apex can pass the data in.
- Keep a governor limit budget document for each trigger: total SOQL = Apex queries + (Flow queries × max interview count).
- Consider moving the invocation to a Platform Event trigger if the Flow logic does not need to run synchronously in the same transaction.

---

## Gotcha 2: Private Flow Variables Are Invisible to External Callers

**What happens:** A developer sets up a Flow with a variable intended to receive input from Apex or a REST caller, but `isInput` and `isOutput` are both false, which is the default for variables created in API 25.0+ (api_meta 264 L75629-75658). UNVERIFIED (2026-10-20): that the Flow then runs silently with the variable at its default instead of failing.

**When it occurs:** Whenever a developer creates a new Flow variable in Flow Builder and does not change the Access setting from "Private" to "Input and Output" or "Input Only." The UI default is "Private." Similarly, when reviewing an existing Flow, the Access setting is not prominently displayed in the variable list — it requires opening each variable to inspect.

**How to avoid:**
- Before calling `interview.start()`, verify each input variable's Access setting by opening the Flow in Flow Builder → the Resources panel → Variables → click each variable → confirm Input/Output Type.
- Name input variables with an `input` prefix and output variables with an `output` prefix (e.g., `inputAccountId`, `outputCaseId`) as a convention that signals intent and prompts reviewers to check the Access setting.
- In review, parse the Flow metadata XML and confirm that any variable whose API name starts with `input` or `output` has `isInput` or `isOutput` set to true (api_meta 264 L75629-75658); `check_auto_launched_flow_patterns.py` does not test this.

---

## Gotcha 3: The Flow API Name in Code Must Match a Flow in the Org

**What happens:** "If the flow doesn't exist in the current org, a TypeException is thrown" (apexref 262 L158086). The earlier text of this gotcha quoted `FLOW_INTERVIEW_EXCEPTION: The flow my_flow doesn't exist.`; UNVERIFIED (2026-10-20): that message, and that `my_flow` and `My_Flow` resolve differently (case sensitivity). A deleted flow is not checked against `createInterview()` callers (L157944), and a renamed flow goes stale without a compile error.

**When it occurs:** Most commonly when:
- A developer types the Flow API name from memory rather than copying it from Setup.
- A Flow is renamed in Setup and the Apex caller is not updated.
- A Flow is deployed from a sandbox where the API name was typed with different capitalisation.

**How to avoid:**
- Always copy the Flow API name from Setup > Flows > the Flow's detail page, not from the Flow label.
- Store Flow API names as named constants (`private static final String PRICING_FLOW = 'Calculate_Opportunity_Discount';`) in a single class so there is one place to update if the Flow is renamed.
- The checker script (`check_auto_launched_flow_patterns.py`) can scan Apex files for `Flow.Interview.createInterview` calls and cross-reference the quoted name against deployed Flow metadata XML filenames.

---

## Gotcha 4: Elements Without Fault Connectors Leave the Apex Caller Exposed

**What happens:** If a Flow element (Get Records, Create Records, Update Records, Send Email, etc.) encounters an error and there is no Fault connector on that element, Salesforce throws an unhandled fault. When invoked from Apex, this surfaces as a `System.FlowException`. If not caught in Apex, it propagates up the call stack and rolls back the transaction. UNVERIFIED (2026-10-20): the user-facing message text. The surfacing of Flow faults as `System.FlowException` is UNVERIFIED too; the guide describes `FlowException` as "any problem with starting flow interviews from Apex" (apexref 262 L214963).

**When it occurs:** Whenever a developer builds a Flow that has DML elements without Fault connectors and the element encounters a data integrity error (e.g., a duplicate rule violation, a required field missing, a record-lock conflict) in production.

**How to avoid:**
- Add a Fault connector to every element that can fail (Get Records, Create/Update/Delete Records, external calls, Send Email actions).
- On the fault path, record the fault message (`{!$Flow.FaultMessage}` is UNVERIFIED, 2026-10-20: not in either corpus) in an Error_Log__c record or an alert email.
- In Apex, always wrap `interview.start()` in a try/catch for `System.FlowException` and log `e.getMessage()` before rethrowing or returning a user-friendly message.

---

## Gotcha 5: Platform Event-Triggered Flows Order Holds Per Event, Not Across Event Types or Subscribers

**What happens:** The guide says "platform event-triggered flows and flow interviews evaluate platform event messages in the order they're received", ordered by replay ID, with order preserved within each batch of up to 200 (platform_events 264 L2184-2186). What it does not guarantee: which of several subscribers, such as triggered flows, paused interviews and processes, handles a message first (L2182-2183). The earlier claim that delivery order is not guaranteed within a burst is CONTRADICTED by that text. A Flow that assumes `Order_Fulfillment__e` is handled before a different event type `Order_Cancellation__e` has no cross-type ordering to rely on (UNVERIFIED, 2026-10-20: the guide states order per event, by replay ID).

**When it occurs:** In high-volume integration scenarios where the same event type can fire multiple times for the same record in close succession — order management, payment processing, IoT data ingestion.

**How to avoid:**
- Design Platform Event-triggered Flows to be idempotent: running the same event twice produces the same result as running it once.
- Include a `Replay_Id__c` or `Event_Timestamp__c` field on the event and use a Decision element in the Flow to skip processing if the current record state is already at a later stage.
- For strict ordering requirements, keep the related changes on one event type, which a flow evaluates in replay-ID order (platform_events 264 L2184-2186), and carry a sequence field the Flow can compare.
