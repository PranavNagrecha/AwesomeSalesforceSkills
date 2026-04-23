# LLM Anti-Patterns — Apex Callable Interface

## Anti-Pattern 1: Using `Callable` For Flow

**What the LLM generates:**

```apex
public with sharing class FlowAction implements Callable {
    public Object call(String action, Map<String, Object> args) { /* ... */ }
}
```

…then telling the admin to drag "Apex Action" in Flow.

**Why it happens:** LLMs conflate `Callable` (dynamic dispatch) with `@InvocableMethod` (Flow binding). Both seem like "Apex callable from somewhere."

**Correct pattern:**

```apex
public with sharing class FlowAction {
    @InvocableMethod(label='Do Thing')
    public static List<Output> doThing(List<Input> inputs) { /* ... */ }
}
```

**Detection hint:** `implements Callable` paired with "Flow" in surrounding comments or doc.

---

## Anti-Pattern 2: No `when else` Default In `switch on action`

**What the LLM generates:**

```apex
public Object call(String action, Map<String, Object> args) {
    switch on action {
        when 'create' { return create(args); }
        when 'update' { return update(args); }
    }
    return null;  // <-- silent fallthrough
}
```

**Why it happens:** LLMs treat `return null` as harmless. A typo action string silently returns null with no indication.

**Correct pattern:** `when else { throw new CalloutException('Unknown action: ' + action); }`.

**Detection hint:** `switch on action` without a `when else` throw branch.

---

## Anti-Pattern 3: Unguarded `Type.forName` Result

**What the LLM generates:**

```apex
Callable c = (Callable) Type.forName('SomeClass').newInstance();
```

**Why it happens:** LLMs chain calls without considering the null return. `Type.forName` returns `null` for unknown classes.

**Correct pattern:**

```apex
Type t = Type.forName('SomeClass');
if (t == null || !Callable.class.isAssignableFrom(t)) {
    throw new HandlerException('SomeClass not usable');
}
Callable c = (Callable) t.newInstance();
```

**Detection hint:** `Type.forName(...).newInstance()` chained without an intermediate null check.

---

## Anti-Pattern 4: Undocumented Action Contract

**What the LLM generates:**

```apex
public Object call(String action, Map<String, Object> args) {
    if (action == 'process') {
        return processOrder(args);
    }
    return null;
}
```

No mention of which keys `args` must contain, or what the return means.

**Why it happens:** LLMs treat `Map<String, Object>` as self-documenting — consumers will "figure it out."

**Correct pattern:** A header comment enumerating actions, required keys, and return shape.

**Detection hint:** `implements Callable` without a class-level doc comment listing actions.

---

## Anti-Pattern 5: Returning `Map<String, Object>` With Inconsistent Shapes

**What the LLM generates:**

```apex
public Object call(String action, Map<String, Object> args) {
    if (action == 'get') return new Map<String, Object>{ 'result' => records };
    if (action == 'count') return records.size();  // returns Integer
    // Each action returns a different shape.
}
```

**Why it happens:** LLMs don't recognize the consumer must cast per-action and keep those casts in sync.

**Correct pattern:** Document return type per action in the header. Either unify on `Map<String, Object>` with documented keys OR allow per-action types, but document them.

**Detection hint:** Multiple `return` statements in `call` with different runtime types.

---

## Anti-Pattern 6: `public` Where `global` Is Needed

**What the LLM generates:**

```apex
public with sharing class PackageExtensionPoint implements Callable { /* ... */ }
```

…in a managed-package intended for subscriber use.

**Why it happens:** LLMs default to `public` access modifier as the safe choice without understanding managed-package access rules.

**Correct pattern:** Use `global` for any class a subscriber needs to reference or extend.

**Detection hint:** `public ... implements Callable` in a file under a managed-package namespace.

---

## Anti-Pattern 7: Mixing Sync DML Inside `Callable` With No Limit Docs

**What the LLM generates:** A `Callable` that does `insert`, `update`, and `delete` inline without documenting the governor impact, so callers blow limits.

**Why it happens:** LLMs don't consider transaction-boundary side effects of dynamic dispatch.

**Correct pattern:** Document DML cost per action, or enqueue async for heavy work.

**Detection hint:** `insert`, `update`, `delete` inside `call` without a @governor-cost comment.

---

## Anti-Pattern 8: Raw Cast On `args.get()` Without Null Guard

**What the LLM generates:**

```apex
Id orderId = (Id) args.get('orderId');  // NPE if key missing
Integer qty = (Integer) args.get('qty');  // NPE if null
```

**Why it happens:** LLMs treat the map as a typed DTO.

**Correct pattern:** Pull into `Object`, check null, then cast. Or use `args.containsKey('orderId')` before reading.

**Detection hint:** `(Type) args.get(` immediately assigned to a typed variable without null check.
