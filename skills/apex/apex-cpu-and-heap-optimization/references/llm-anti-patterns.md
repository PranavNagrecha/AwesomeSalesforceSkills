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

**Why it happens:** LLMs know `Limits.getCpuTime()` exists and suggest calling it on every iteration. The irony is that calling it thousands of times inside a tight loop adds measurable CPU overhead itself, and the `break` silently drops unprocessed records. The `8000` is also a hardcoded 80% of the *synchronous* 10,000 ms ceiling (`salesforce_app_limits_cheatsheet.txt` L91); the same literal is wrong by 6x in a batch context, so derive it from `Limits.getLimitCpuTime()`. *UNVERIFIED (2026-09-05): the per-call CPU cost of `Limits.getCpuTime()` is not published in the Apex Developer Guide or Apex Reference Guide; the overhead claim is practitioner experience, and the correct-pattern advice stands on the dropped-records defect alone.*

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

**Why it happens:** `JSON.deserializeUntyped` appears in many Salesforce examples and LLMs default to it. Untyped deserialization creates deeply nested `Map<String, Object>` and `List<Object>` structures that consume more heap than typed Apex classes, and the repeated casting adds CPU cost. *UNVERIFIED (2026-09-05): the Apex Developer Guide documents that collections are bounded by the heap limit (`apexdev.txt` L1431) but publishes no comparison of untyped versus typed deserialization cost; the relative-heap claim is practitioner measurement, not a documented figure.*

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

**Why it happens:** LLMs generate self-contained code blocks and do not think about hoisting invariants outside loops. Recompiling the same pattern on every iteration is repeated work that produces an identical object. *UNVERIFIED (2026-09-05): neither guide publishes the CPU cost of `Pattern.compile`; "expensive" here is practitioner experience. The hoist is still correct on invariant-in-loop grounds regardless of the constant factor.*

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

**Why it happens:** LLMs borrow defensive-copy patterns from Java/C# training data. In Apex, deep-cloning a large SObject list holds a second full copy of the collection on the heap, and heap is what bounds a collection's size (`apexdev.txt` L1431). Most Apex operations do not require a defensive copy. *UNVERIFIED (2026-09-05): "doubles the heap usage" is not a documented ratio — the guides state the heap bound on collections but publish no per-clone cost.*

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

---

## Anti-Pattern 7: Catching the governor-limit exception to "handle it gracefully"

**What the LLM generates:**

```apex
try {
    processEverything(records);
} catch (System.LimitException e) {
    ApplicationLogger.error('BulkProcessor', e);
} finally {
    cleanUp();
}
```

**Why it happens:** `System.LimitException` is a real class with a real name, so it reads like any other catchable exception, and LLMs generalise the try/catch/finally idiom from Java. In Apex it is one of the uncatchable exceptions: "When exceptions are uncatchable, catch blocks, as well as finally blocks if any, aren't executed" (`apexdev.txt` L39721–L39728). The generated code produces no log row and never runs `cleanUp()`.

**Correct pattern:**

```apex
// Check headroom before the expensive block; there is no after.
if (Limits.getCpuTime() > Limits.getLimitCpuTime() / 2) {
    System.enqueueJob(new BulkProcessorQueueable(records));
    return;
}
processEverything(records);
```

**Detection hint:** `catch\s*\(\s*(System\.)?LimitException` anywhere, or a `finally` block whose only purpose is to flush logs after a limit-heavy call.

---

## Anti-Pattern 8: Asserting CPU or heap headroom after `Test.stopTest()`

**What the LLM generates:**

```apex
Test.startTest();
new AccountRollupService().recalculate(accounts, opportunities);
Test.stopTest();

System.assert(Limits.getCpuTime() < 10000, 'Too slow');
```

**Why it happens:** "Act, stop, assert" is the shape of every Apex test an LLM has seen, so the `Limits` call gets placed with the other assertions. But code after `stopTest` "is assigned the original limits that were in effect before startTest was called" (`apexrefguide.txt` L241086–L241087), so the reading describes the setup block, not the code under test. The hardcoded `10000` compounds it — the same assertion is wrong by 6x in an asynchronous context.

**Correct pattern:**

```apex
Test.startTest();
Integer cpuBefore = Limits.getCpuTime();
new AccountRollupService().recalculate(accounts, opportunities);
Integer cpuUsed = Limits.getCpuTime() - cpuBefore;
Integer cpuCeiling = Limits.getLimitCpuTime();
Test.stopTest();

Assert.isTrue(cpuUsed < cpuCeiling / 4, 'Used ' + cpuUsed + ' ms of ' + cpuCeiling + ' ms');
```

**Detection hint:** `Limits\.get(CpuTime|HeapSize)` on a line after `Test.stopTest()`, or a `Limits` assertion compared against a numeric literal instead of `Limits.getLimit*()`.
