# LLM Anti-Patterns — Flow Invocable From Apex

Common mistakes AI coding assistants make when generating or advising on Flow Invocable From Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Single-record signature

**What the LLM generates:**

```apex
@InvocableMethod(label='Geocode')
public static Result geocode(String address) { ... }
```

**Why it happens:** LLMs default to the mental model "one call, one record" from REST/GraphQL training data. Salesforce's bulk contract is unusual and easy to forget.

**Correct pattern:**

```apex
@InvocableMethod(label='Geocode')
public static List<Result> geocode(List<Request> requests) { ... }
```

**Detection hint:** Signature without `List<` in the parameter. Compiler error will catch it, but agents should spot it at author time.

---

## Anti-Pattern 2: SOQL inside the request loop

**What the LLM generates:**

```apex
public static List<Response> process(List<Request> requests) {
    List<Response> results = new List<Response>();
    for (Request r : requests) {
        Account acct = [SELECT Id, Name FROM Account WHERE Id = :r.accountId];  // ← SOQL per record
        results.add(buildResponse(r, acct));
    }
    return results;
}
```

**Why it happens:** LLMs pattern-match on "loop over inputs, look something up" and inline the SOQL for readability.

**Correct pattern:**

```apex
public static List<Response> process(List<Request> requests) {
    Set<Id> accountIds = new Set<Id>();
    for (Request r : requests) accountIds.add(r.accountId);

    Map<Id, Account> accounts = new Map<Id, Account>(
        [SELECT Id, Name FROM Account WHERE Id IN :accountIds]
    );

    List<Response> results = new List<Response>();
    for (Request r : requests) {
        results.add(buildResponse(r, accounts.get(r.accountId)));
    }
    return results;
}
```

**Detection hint:** SOQL literal `[SELECT ... FROM ... WHERE ... = :r.field]` inside a `for (Request r : requests)` loop.

---

## Anti-Pattern 3: Missing `callout=true`

**What the LLM generates:**

```apex
@InvocableMethod(label='Call Vendor')
public static List<Response> callVendor(List<Request> rs) {
    HttpResponse r = new Http().send(buildReq(rs));
    ...
}
```

**Why it happens:** LLMs see the annotation syntax but don't connect "does HTTP" to the `callout` attribute.

**Correct pattern:**

```apex
@InvocableMethod(label='Call Vendor', callout=true)
public static List<Response> callVendor(List<Request> rs) { ... }
```

**Detection hint:** `Http`, `HttpRequest`, `Http.send`, or `callout:` string literal inside an invocable method whose annotation doesn't include `callout=true`.

---

## Anti-Pattern 4: Private wrapper fields

**What the LLM generates:**

```apex
public class Request {
    @InvocableVariable
    private String address;   // ← invisible to Flow
    public String getAddress() { return address; }
}
```

**Why it happens:** Java bleed — LLMs default to private fields with getters/setters.

**Correct pattern:**

```apex
public class Request {
    @InvocableVariable(required=true label='Address')
    public String address;
}
```

**Detection hint:** `@InvocableVariable` followed by `private`.

---

## Anti-Pattern 5: Shortened output list

**What the LLM generates:**

```apex
for (Request r : requests) {
    if (r.skipFlag) continue;   // ← silently shrinks output list
    results.add(process(r));
}
```

**Why it happens:** LLMs apply standard list-filter patterns without understanding Flow's positional index contract.

**Correct pattern:**

```apex
for (Request r : requests) {
    Response resp = new Response();
    if (r.skipFlag) {
        resp.status = 'skipped';
    } else {
        resp = process(r);
    }
    results.add(resp);
}
```

**Detection hint:** A `continue` statement inside a loop that also builds a list returned from an invocable method.

---

## Anti-Pattern 6: Static cache for "efficiency"

**What the LLM generates:**

```apex
public class MyInvocable {
    private static Map<String, Account> cache = new Map<String, Account>();
    public static List<Response> run(List<Request> rs) {
        for (Request r : rs) {
            if (!cache.containsKey(r.key)) cache.put(r.key, load(r.key));
            results.add(build(cache.get(r.key)));
        }
    }
}
```

**Why it happens:** LLMs apply general "cache to avoid recomputation" wisdom without considering that two flows in the same transaction share the class's static state.

**Correct pattern:** Build the map as a local variable inside `run()`. If genuine cross-call caching is needed, use `Platform Cache` with an explicit partition + expiry policy.

**Detection hint:** `private static Map<` at class level inside an `@InvocableMethod` class.

---

## Anti-Pattern 7: Throwing plain `Exception`

**What the LLM generates:**

```apex
try { ... } catch (Exception e) {
    throw new Exception('DB error: ' + e.getMessage());
}
```

**Why it happens:** Simple error-handling pattern that works in many languages.

**Correct pattern:**

```apex
try { ... } catch (Exception e) {
    ApplicationLogger.logError('MyInvocable', e);
    throw new AuraHandledException('Unable to process request.');
}
```

**Detection hint:** `throw new Exception(` inside an invocable method.

---

## Anti-Pattern 8: Flow label, not API name, in `createInterview`

**What the LLM generates:**

```apex
Flow.Interview flow = Flow.Interview.createInterview('Deactivate Stale Accounts', inputs);
```

**Why it happens:** LLMs see the flow label in the spec and use it verbatim.

**Correct pattern:**

```apex
Flow.Interview flow = Flow.Interview.createInterview('Deactivate_Stale_Accounts', inputs);
```

**Detection hint:** Flow name string containing a space inside `Flow.Interview.createInterview(...)`.

---

## Anti-Pattern 9: Missing `description` on `@InvocableVariable`

**What the LLM generates:**

```apex
@InvocableVariable(required=true)
public String accountId;
```

**Why it happens:** LLMs produce minimum-viable annotations without considering the admin UX.

**Correct pattern:**

```apex
@InvocableVariable(required=true label='Account ID' description='15- or 18-character Account record Id.')
public String accountId;
```

**Detection hint:** `@InvocableVariable` without a `description=` argument.

---

## Anti-Pattern 10: No null-input defense

**What the LLM generates:**

```apex
public static List<Response> run(List<Request> requests) {
    List<Response> results = new List<Response>();
    for (Request r : requests) results.add(process(r));    // NPE if requests is null
    return results;
}
```

**Why it happens:** LLMs assume callers never pass null collections.

**Correct pattern:**

```apex
public static List<Response> run(List<Request> requests) {
    if (requests == null || requests.isEmpty()) return new List<Response>();
    ...
}
```

**Detection hint:** Invocable methods with no null / empty guard on the input collection.
