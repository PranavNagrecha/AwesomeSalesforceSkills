# LLM Anti-Patterns — Subflows and Reusability

Common mistakes AI coding assistants make when generating or advising on Flow subflow design and reuse.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Extracting a subflow that is only called by one parent flow

**What the LLM generates:**

```
"Move the Account validation logic into a subflow for reusability."
// The validation logic is only used in one flow and is unlikely to be reused
```

**Why it happens:** LLMs apply the DRY (Don't Repeat Yourself) principle aggressively. Creating a subflow for logic that only has one caller adds indirection without benefit — it makes the flow harder to read and debug.

**Correct pattern:**

Extract to a subflow only when:
- Two or more parent flows need the same logic
- The logic is complex enough to benefit from independent testing
- The contract (inputs/outputs) is stable across callers

For single-use logic, keep it inline.

**Detection hint:** Subflow recommendation where only one parent flow is identified as a caller.

---

## Anti-Pattern 2: Not marking input/output variables as "Available for Input" or "Available for Output"

**What the LLM generates:**

```
"Create a text variable called recordId in the subflow."
// Variable exists but is not marked as Available for Input
// Parent flow cannot pass a value to it
```

**Why it happens:** LLMs create variables but forget the visibility settings. In Flow, variables must be explicitly marked as "Available for Input" and/or "Available for Output" to participate in the subflow contract.

**Correct pattern:**

For each subflow variable:
- **Inputs**: Check "Available for Input" — these receive values from the parent
- **Outputs**: Check "Available for Output" — these return values to the parent
- **Both**: Check both if the variable is modified and returned

```
Variable: recordId
  Type: Text
  Available for Input: Yes
  Available for Output: No

Variable: resultStatus
  Type: Text
  Available for Input: No
  Available for Output: Yes
```

**Detection hint:** Subflow design that lists variables without specifying their input/output availability.

---

## Anti-Pattern 3: Passing entire record collections when only an ID is needed

**What the LLM generates:**

```
Parent Flow:
  [Subflow: Process_Accounts]
    Input: accountCollection (entire SObject collection)
```

**Why it happens:** LLMs pass the full data to be "safe." Passing large collections as subflow inputs increases memory usage and makes the contract brittle — the subflow depends on which fields were queried upstream.

**Correct pattern:**

Pass the minimum data needed:

```
Parent Flow:
  [Subflow: Process_Accounts]
    Input: accountIds (collection of Text/ID values)

Subflow: Process_Accounts
  [Get Records: Accounts where Id IN accountIds]
  // Subflow controls its own field selection
```

Or pass individual fields rather than full SObjects.

**Detection hint:** Subflow input variable of type "Record Collection" when only IDs or a few fields are needed.

---

## Anti-Pattern 4: Not handling faults from within the subflow

**What the LLM generates:**

```
Subflow:
  [Get Records] --> [Update Records] --> [Output: success = true]
  // No fault connectors — if Update fails, the unhandled fault propagates to the parent
```

**Why it happens:** LLMs focus on the happy path. When a subflow has an unhandled fault, it bubbles up to the parent flow, which may also lack fault handling, causing a full transaction rollback.

**Correct pattern:**

Handle faults within the subflow and communicate the result:

```
Subflow:
  [Update Records] --fault--> [Assignment: success = false, errorMessage = $Flow.FaultMessage]
  [Update Records] --success--> [Assignment: success = true]
  Output: success (Boolean), errorMessage (Text)

Parent Flow:
  [Subflow] --> [Decision: Was subflow successful?]
    No --> [Handle error in parent context]
```

**Detection hint:** Subflow with DML elements but no fault connectors, relying on the parent to handle errors.

---

## Anti-Pattern 5: Creating deeply nested subflow chains

**What the LLM generates:**

```
Parent Flow --> Subflow A --> Subflow B --> Subflow C --> Subflow D
```

**Why it happens:** LLMs decompose aggressively. Deep nesting makes flows hard to debug (you must trace through 4+ levels), increases the risk of governor limit accumulation, and makes the overall process opaque.

**Correct pattern:**

Keep subflow nesting to 2 levels maximum:

```
Parent Flow --> Subflow A (contains all logic for step A)
            --> Subflow B (contains all logic for step B)
```

If a subflow is calling another subflow, consider whether the logic should be consolidated or whether the parent should orchestrate both directly.

**Detection hint:** Subflow that calls another subflow, creating 3+ levels of nesting.

---

## Anti-Pattern 6: Using a Screen Flow as a subflow

**What the LLM generates:**

```
"Call the existing Screen Flow as a subflow from your record-triggered flow."
```

**Why it happens:** LLMs suggest reusing an existing Screen Flow. But record-triggered and autolaunched flows cannot call Screen Flows as subflows because screen flows require user interaction.

**Correct pattern:**

Subflows must be Autolaunched Flows (no screens). If the logic exists in a Screen Flow:
1. Extract the non-screen logic into a new Autolaunched Flow
2. Call the Autolaunched Flow as a subflow
3. Have the Screen Flow also call the same Autolaunched Flow for its needs

```
Record-Triggered Flow --> Autolaunched Subflow (shared logic)
Screen Flow ------------> Autolaunched Subflow (same shared logic)
```

**Detection hint:** Advice to call a Screen Flow from a record-triggered or autolaunched flow context.
