# LLM Anti-Patterns — Apex Flow Invocation From Apex

## Anti-Pattern 1: Per-Record Flow Invocation

**What the LLM generates:**

```apex
for (Account a : accounts) {
    Flow.Interview.createInterview('Tier_Flow',
        new Map<String, Object>{ 'acct' => a }).start();
}
```

**Why it happens:** LLMs write record-level code and don't know Flow invocation is expensive. Each interview charges governor limits separately.

**Correct pattern:** Design the Flow to accept a collection input, invoke once.

**Detection hint:** `Flow.Interview.createInterview` inside any `for`/`while` block that iterates SObject lists.

---

## Anti-Pattern 2: No Try/Catch Around `start()`

**What the LLM generates:**

```apex
Flow.Interview i = Flow.Interview.createInterview(name, params);
i.start();
```

**Why it happens:** LLMs treat Apex APIs as unchecked. `start()` can throw `Flow.FlowException` for flow-internal faults, `SObjectException` for bad Flow name, and `DmlException` for governor exhaustion.

**Correct pattern:** Wrap in try/catch that logs and either surfaces a cleaner error or falls back.

**Detection hint:** `createInterview` + `start()` sequence with no enclosing `try`.

---

## Anti-Pattern 3: Casting Output Without Null Check

**What the LLM generates:**

```apex
Decimal price = (Decimal) i.getVariableValue('finalPrice');
```

**Why it happens:** LLMs pattern-match to "type-cast the result" without considering that typos or missing output variables return `null`.

**Correct pattern:**

```apex
Object obj = i.getVariableValue('finalPrice');
Decimal price = obj == null ? null : (Decimal) obj;
```

**Detection hint:** `(Type) i.getVariableValue(...)` with no surrounding null check.

---

## Anti-Pattern 4: Hardcoded Flow Name As String Literal

**What the LLM generates:**

```apex
Flow.Interview.createInterview('Assign_Tier', params);
```

**Why it happens:** LLMs default to inline strings. A typo or rename silently breaks only at runtime.

**Correct pattern:** Centralize Flow names in a single constants class or Custom Metadata Type. Ideally an integration test validates the Flow exists.

**Detection hint:** Any string literal passed as the first argument to `createInterview`.

---

## Anti-Pattern 5: Passing Wrong Primitive Type

**What the LLM generates:**

```apex
Map<String, Object> params = new Map<String, Object>{
    'amount' => 1000,         // Integer — Flow expected Decimal/Number
    'startDate' => '2026-01-01' // String — Flow expected Date
};
```

**Why it happens:** LLMs don't enforce type strictness in `Map<String, Object>`.

**Correct pattern:**

```apex
Map<String, Object> params = new Map<String, Object>{
    'amount' => Decimal.valueOf(1000),
    'startDate' => Date.newInstance(2026, 1, 1)
};
```

**Detection hint:** Integer or String values for Flow params whose name suggests a numeric/date field.

---

## Anti-Pattern 6: Treating Apex Test Data As Available To Flow

**What the LLM generates:**

```apex
@IsTest
static void testFlowCall() {
    // No data setup
    FlowRunner.run('Assign_Tier', new Map<String, Object>{ 'id' => '001...' });
}
```

**Why it happens:** LLMs skip the arrange step.

**Correct pattern:** Create actual records in the test; the Flow's SOQL sees them.

**Detection hint:** Test method invoking a Flow wrapper without any `insert` or `Test.loadData` in the method or setup.

---

## Anti-Pattern 7: Reading Input-Only Variables

**What the LLM generates:**

```apex
i.start();
SObject fromFlow = (SObject) i.getVariableValue('inputAcct');
```

**Why it happens:** LLMs don't know Flow distinguishes input from output availability.

**Correct pattern:** Only call `getVariableValue` on variables marked "Available for Output" in Flow Builder.

**Detection hint:** Reading back a variable whose name starts with `input`.

---

## Anti-Pattern 8: Reusing A Single `Flow.Interview` Instance

**What the LLM generates:**

```apex
Flow.Interview i = Flow.Interview.createInterview(name, params);
for (Account a : accounts) {
    i.start();  // thinks each call runs the flow for `a`
}
```

**Why it happens:** LLMs reuse the variable like a prepared statement.

**Correct pattern:** Each `createInterview` is single-use. Create a new instance per invocation (or even better, invoke the Flow once with a collection).

**Detection hint:** `.start()` called more than once on the same `Flow.Interview` variable.
