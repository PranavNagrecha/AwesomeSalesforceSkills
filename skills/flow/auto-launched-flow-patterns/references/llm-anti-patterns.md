# LLM Anti-Patterns — Auto-Launched Flow Patterns

Common mistakes AI coding assistants make when generating or advising on auto-launched Flow invocation from Apex, REST API, and Platform Events.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using the wrong variable name case in Flow.Interview inputs

**What the LLM generates:**

```apex
Map<String, Object> inputs = new Map<String, Object>();
inputs.put('recordid', accountId); // Wrong case — Flow variable names are case-sensitive
Flow.Interview myFlow = new Flow.Interview.My_Auto_Flow(inputs);
myFlow.start();
```

**Why it happens:** LLMs lowercase variable names by convention. Flow input variable names are case-sensitive and must match exactly as defined in the Flow.

**Correct pattern:**

```apex
Map<String, Object> inputs = new Map<String, Object>();
inputs.put('recordId', accountId); // Exact match to Flow variable name
Flow.Interview myFlow = new Flow.Interview.My_Auto_Flow(inputs);
myFlow.start();
```

**Detection hint:** `inputs.put(` with a variable name that does not exactly match the Flow's input variable name (check casing).

---

## Anti-Pattern 2: Not reading output variables after the Flow interview completes

**What the LLM generates:**

```apex
Flow.Interview myFlow = new Flow.Interview.My_Auto_Flow(inputs);
myFlow.start();
// Assumes the flow did its work — never reads output
```

**Why it happens:** LLMs treat Flow invocation as fire-and-forget. If the calling Apex needs the Flow's output (e.g., a created record ID), it must explicitly call `getVariableValue()`.

**Correct pattern:**

```apex
Flow.Interview myFlow = new Flow.Interview.My_Auto_Flow(inputs);
myFlow.start();
Id createdRecordId = (Id) myFlow.getVariableValue('outputRecordId');
```

**Detection hint:** `Flow.Interview` usage without any `getVariableValue()` call when the Flow defines output variables.

---

## Anti-Pattern 3: Calling a Flow in a loop from Apex

**What the LLM generates:**

```apex
for (Account acc : accounts) {
    Map<String, Object> inputs = new Map<String, Object>();
    inputs.put('recordId', acc.Id);
    Flow.Interview myFlow = new Flow.Interview.My_Auto_Flow(inputs);
    myFlow.start(); // One Flow interview per record — hits limits at scale
}
```

**Why it happens:** LLMs process collections by iterating. Each `Flow.Interview.start()` in a loop consumes governor limits independently and does not benefit from Flow bulkification.

**Correct pattern:**

Design the Flow to accept a collection input and process all records in one interview:

```apex
Map<String, Object> inputs = new Map<String, Object>();
inputs.put('inputRecords', accounts); // Pass the full collection
Flow.Interview myFlow = new Flow.Interview.My_Bulk_Flow(inputs);
myFlow.start();
```

Or, if the Flow must run per-record, invoke it via a Platform Event or a record-triggered mechanism that the platform bulkifies.

**Detection hint:** `Flow.Interview` constructor or `.start()` inside a `for` or `while` loop.

---

## Anti-Pattern 4: Using wrong REST API endpoint format for Flow invocation

**What the LLM generates:**

```
POST /services/data/v59.0/actions/custom/flow/My_Auto_Flow
{
    "recordId": "001xx000003ABCD"
}
```

**Why it happens:** LLMs construct the REST body as a flat JSON object. The Flow REST API requires inputs to be wrapped in an `inputs` array, even for a single invocation.

**Correct pattern:**

```
POST /services/data/v59.0/actions/custom/flow/My_Auto_Flow

{
    "inputs": [
        {
            "recordId": "001xx000003ABCD"
        }
    ]
}
```

**Detection hint:** Flow REST API request body without the `"inputs"` array wrapper.

---

## Anti-Pattern 5: Not handling Flow faults when called from Apex

**What the LLM generates:**

```apex
Flow.Interview myFlow = new Flow.Interview.My_Auto_Flow(inputs);
myFlow.start();
// No try-catch — unhandled faults crash the calling transaction
```

**Why it happens:** LLMs omit error handling around Flow invocations. If the Flow hits an unhandled fault, it throws an exception that rolls back the entire Apex transaction.

**Correct pattern:**

```apex
try {
    Flow.Interview myFlow = new Flow.Interview.My_Auto_Flow(inputs);
    myFlow.start();
} catch (Flow.Interview.FlowException e) {
    // Log the error and handle gracefully
    Logger.error('Flow execution failed: ' + e.getMessage());
    // Decide: rethrow, return error, or compensate
}
```

**Detection hint:** `Flow.Interview` usage without a surrounding `try/catch` block.

---

## Anti-Pattern 6: Assuming Platform Event-triggered Flows share the same transaction

**What the LLM generates:**

```
// Documentation says: "The Flow runs in the same transaction as the Platform Event publish"
// This is wrong — Platform Event subscribers run asynchronously
```

**Why it happens:** LLMs confuse Platform Event subscribers with synchronous triggers. Platform Events are asynchronous — the subscribing Flow runs in a separate transaction and cannot roll back the publisher's work.

**Correct pattern:**

Design the Flow to be idempotent and handle its own failures, since it runs independently:

- Add fault connectors on every DML element
- Log errors to a custom object or send email alerts
- Do not assume the publishing transaction is still active

**Detection hint:** Documentation or comments claiming a Platform Event-triggered Flow runs "in the same transaction" as the publisher.
