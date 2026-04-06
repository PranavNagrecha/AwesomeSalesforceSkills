# LLM Anti-Patterns — Apex CPU and Heap Optimization

Common mistakes AI coding assistants make when generating or advising on Apex CPU time and heap size optimization.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting String concatenation refactor but ignoring the real cost — nested loops

**What the LLM generates:**

```apex
// "Optimized" version — replaced += with String.join
String result = String.join(myList, ',');
```

The LLM focuses on string concatenation micro-optimization while the actual CPU bottleneck is an O(n*m) nested loop three lines above that it left untouched.

**Why it happens:** Training data is full of "avoid string concatenation in loops" advice, so LLMs pattern-match on that and miss the algorithmic issue (e.g., a nested `for` doing a linear scan instead of a Map lookup).

**Correct pattern:**

```apex
// Fix the algorithmic cost first — replace inner loop with Map lookup
Map<Id, Account> accountMap = new Map<Id, Account>(accounts);
for (Contact c : contacts) {
    Account a = accountMap.get(c.AccountId);
    if (a != null) {
        c.Description = a.Name;
    }
}
```

**Detection hint:** Nested `for` loops where the inner collection grows with data volume — search for `for.*\{[^}]*for.*\{` in the same method.

---

## Anti-Pattern 2: Recommending Limits.getCpuTime() checkpoints inside the hot loop itself

**What the LLM generates:**

```apex
for (Integer i = 0; i < records.size(); i++) {
    if (Limits.getCpuTime() > 8000) {
        break; // Stop before hitting the limit
    }
    processRecord(records[i]);
}
```

**Why it happens:** LLMs know `Limits.getCpuTime()` exists and suggest calling it on every iteration. The irony is that calling it thousands of times inside a tight loop adds measurable CPU overhead itself, and the `break` silently drops unprocessed records.

**Correct pattern:**

```apex
// Check periodically, not every iteration; handle remaining records
Integer checkInterval = 200;
for (Integer i = 0; i < records.size(); i++) {
    if (Math.mod(i, checkInterval) == 0 && Limits.getCpuTime() > 8000) {
        // Enqueue remaining work asynchronously instead of silently dropping
        System.enqueueJob(new RecordProcessorQueueable(records, i));
        return;
    }
    processRecord(records[i]);
}
```

**Detection hint:** `Limits\.getCpuTime\(\)` inside a `for` or `while` loop body without a modulo or batch-interval guard.

---

## Anti-Pattern 3: Deserializing a large JSON payload into a generic Object instead of typed classes

**What the LLM generates:**

```apex
Map<String, Object> payload = (Map<String, Object>) JSON.deserializeUntyped(jsonBody);
// Then casting every nested field individually
String name = (String) ((Map<String, Object>) ((List<Object>) payload.get('records')).get(0)).get('Name');
```

**Why it happens:** `JSON.deserializeUntyped` appears in many Salesforce examples and LLMs default to it. Untyped deserialization creates deeply nested `Map<String, Object>` and `List<Object>` structures that consume far more heap than typed Apex classes, and the repeated casting adds CPU cost.

**Correct pattern:**

```apex
public class ApiResponse {
    public List<RecordWrapper> records;
}
public class RecordWrapper {
    public String Name;
}

ApiResponse payload = (ApiResponse) JSON.deserialize(jsonBody, ApiResponse.class);
String name = payload.records[0].Name;
```

**Detection hint:** `JSON\.deserializeUntyped` followed by multiple `(Map<String, Object>)` or `(List<Object>)` casts.

---

## Anti-Pattern 4: Using regex patterns compiled inside a loop

**What the LLM generates:**

```apex
for (String line : lines) {
    Pattern p = Pattern.compile('\\d{3}-\\d{4}');
    Matcher m = p.matcher(line);
    if (m.find()) {
        results.add(m.group());
    }
}
```

**Why it happens:** LLMs generate self-contained code blocks and do not think about hoisting invariants outside loops. `Pattern.compile` is expensive in Apex and recompiling on every iteration is a significant CPU drain at scale.

**Correct pattern:**

```apex
Pattern p = Pattern.compile('\\d{3}-\\d{4}');
for (String line : lines) {
    Matcher m = p.matcher(line);
    if (m.find()) {
        results.add(m.group());
    }
}
```

**Detection hint:** `Pattern\.compile` appearing inside a `for` or `while` block.

---

## Anti-Pattern 5: Cloning entire SObject lists to "avoid mutation" instead of working in place

**What the LLM generates:**

```apex
List<Account> safeList = new List<Account>();
for (Account a : accounts) {
    safeList.add(a.clone(true, true, true, true));
}
// process safeList
```

**Why it happens:** LLMs borrow defensive-copy patterns from Java/C# training data. In Apex, deep-cloning a large SObject list doubles the heap usage and adds CPU for field copying. Most Apex operations do not require a defensive copy.

**Correct pattern:**

```apex
// Work on the original list unless there is a documented reason to clone
for (Account a : accounts) {
    a.Description = 'Updated';
}
update accounts;
```

**Detection hint:** `.clone(true` inside a loop, or a loop that builds a new list by cloning every element from an existing list.

---

## Anti-Pattern 6: Building a massive debug string that is never conditionally gated

**What the LLM generates:**

```apex
String debugOutput = '';
for (Account a : accounts) {
    debugOutput += 'Processing: ' + JSON.serialize(a) + '\n';
}
System.debug(debugOutput);
```

**Why it happens:** LLMs add verbose debug logging by default. `JSON.serialize` on every record in a loop consumes both CPU (serialization) and heap (accumulated string), and the debug log may be truncated anyway — wasting resources for output nobody reads.

**Correct pattern:**

```apex
// Log only in development, and limit what is serialized
if (LoggingConfig__mdt.getInstance('Debug')?.Enabled__c == true) {
    System.debug(LoggingLevel.FINE, 'Processing ' + accounts.size() + ' accounts');
}
```

**Detection hint:** `JSON\.serialize` inside a `for` loop combined with string concatenation, especially near `System\.debug`.
