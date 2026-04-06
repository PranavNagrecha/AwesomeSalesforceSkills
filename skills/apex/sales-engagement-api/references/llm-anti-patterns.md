# LLM Anti-Patterns — Sales Engagement API

Common mistakes AI coding assistants make when generating or advising on Sales Engagement API usage in Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inserting ActionCadenceTracker via DML

**What the LLM generates:** Code that constructs an `ActionCadenceTracker` object with field assignments and calls `insert tracker;` or `Database.insert(tracker)` to enroll a target.

**Why it happens:** LLMs trained on general Salesforce patterns apply the standard "insert a junction or related record to create a relationship" idiom. Without specific knowledge of which objects are system-managed, the model assumes DML is the right tool.

**Correct pattern:**

```apex
// Use Invocable.Action — not DML
Invocable.Action.Input inp = new Invocable.Action.Input();
inp.put('targetId', leadId);
inp.put('cadenceName', 'My Cadence');
inp.put('userId', repId);
inp.put('sObjectName', 'Lead');
List<Invocable.Action.Result> results =
    Invocable.Action.createCustomAction('apex', 'assignTargetToSalesCadence')
        .invoke(new List<Invocable.Action.Input>{ inp });
```

**Detection hint:** Any code containing `new ActionCadenceTracker(` or `insert` applied to an `ActionCadenceTracker` variable is wrong. Flag immediately.

---

## Anti-Pattern 2: Writing an Apex Trigger on ActionCadenceTracker

**What the LLM generates:** A standard trigger declaration such as `trigger CadenceTrackerTrigger on ActionCadenceTracker (after insert, after update)`.

**Why it happens:** Triggers are the default Salesforce reactive mechanism. The model applies the pattern universally without knowing that ActionCadence objects are excluded from the triggerable object set.

**Correct pattern:**

```apex
// CDC-based Async Apex Trigger — the only supported mechanism
trigger ActionCadenceTrackerCDC on ActionCadenceTrackerChangeEvent (after insert) {
    // process Trigger.new as CDC change events
}
```

**Detection hint:** Any trigger declaration containing `on ActionCadenceTracker` (without `ChangeEvent` suffix) is incorrect. The correct channel is `ActionCadenceTrackerChangeEvent`.

---

## Anti-Pattern 3: Swallowing Invocable Action Results Without Inspecting isSuccess()

**What the LLM generates:** Code that calls `Invocable.Action.invoke(inputs)` and proceeds without checking the returned result list, treating the absence of an exception as proof of success.

**Why it happens:** The model applies try/catch exception handling as the sole error detection strategy, which is appropriate for DML but not for invocable actions. Invocable actions communicate failures through their result objects, not through exceptions.

**Correct pattern:**

```apex
List<Invocable.Action.Result> results = action.invoke(inputs);
for (Integer i = 0; i < results.size(); i++) {
    if (!results.get(i).isSuccess()) {
        // capture and log results.get(i).getErrors()
    }
}
```

**Detection hint:** If the model's enrollment code does not reference `.isSuccess()` or `.getErrors()` on the action results, the error handling is incomplete.

---

## Anti-Pattern 4: Creating or Modifying Cadence Structure via Apex or SOQL DML

**What the LLM generates:** Apex code that tries to `insert new ActionCadence(Name='My Cadence')` or `insert new ActionCadenceStep(...)` to build cadence content programmatically. Sometimes the model suggests using the Metadata API to deploy cadence configuration.

**Why it happens:** LLMs generalize from patterns where object-level DML creates configuration records (Custom Metadata, Custom Settings, Permission Set assignments). They are unaware that cadence structure is fully UI-owned and cannot be created or updated via code.

**Correct pattern:**

```
// Cadence structure cannot be created via Apex or Metadata API.
// Build cadences in the Cadence Builder UI in each target environment.
// Use SOQL on ActionCadence to look up existing cadence IDs by name at runtime:
ActionCadence cad = [SELECT Id FROM ActionCadence WHERE Name = 'My Cadence' LIMIT 1];
```

**Detection hint:** Any DML or Metadata API write targeting `ActionCadence`, `ActionCadenceStep`, or `ActionCadenceStepVariant` is wrong.

---

## Anti-Pattern 5: Calling the Enrollment Action One Record at a Time Inside a Loop

**What the LLM generates:** A for-each loop that creates one `Invocable.Action.Input`, invokes the action, and checks the result before moving to the next record.

**Why it happens:** The model generates straightforward procedural code that mirrors how a human would think about the problem step-by-step. It does not spontaneously apply Salesforce's bulk-processing idiom to invocable action calls.

**Correct pattern:**

```apex
// Collect ALL inputs first, then invoke once for the entire list
List<Invocable.Action.Input> allInputs = new List<Invocable.Action.Input>();
for (Id tid : targetIds) {
    Invocable.Action.Input inp = new Invocable.Action.Input();
    inp.put('targetId', tid);
    inp.put('cadenceName', cadenceName);
    inp.put('userId', assignedUserId);
    inp.put('sObjectName', tid.getSObjectType().getDescribe().getName());
    allInputs.add(inp);
}
List<Invocable.Action.Result> results = action.invoke(allInputs);
```

**Detection hint:** Any `Invocable.Action.invoke()` call inside a for loop that processes one `Invocable.Action.Input` per iteration is a bulkification anti-pattern. The input list should be accumulated across the full batch before the single `invoke()` call.

---

## Anti-Pattern 6: Querying ActionCadenceTracker for Enrollment Status Using Incorrect State Values

**What the LLM generates:** Queries such as `WHERE State = 'Enrolled'` or `WHERE Status = 'Active'` that use invented or incorrect field/value combinations.

**Why it happens:** The model infers plausible field names and values from the object name rather than from the actual object schema. `State` is the correct field; its values include `Active`, `Complete`, `Paused`, and `Error`.

**Correct pattern:**

```apex
// Correct field name is State, not Status; correct value for active runs is 'Active'
List<ActionCadenceTracker> active = [
    SELECT Id, TargetId, State
    FROM ActionCadenceTracker
    WHERE TargetId IN :targetIds
      AND State = 'Active'
];
```

**Detection hint:** Queries on `ActionCadenceTracker` using `Status` (wrong field name) or values like `'Enrolled'`, `'Running'`, or `'InProgress'` are hallucinated. The correct field is `State` with values `Active`, `Complete`, `Paused`, `Error`.
