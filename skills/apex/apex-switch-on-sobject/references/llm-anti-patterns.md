# LLM Anti-Patterns — Apex Switch on SObject

Mistakes AI coding assistants commonly make when generating switch-on-SObject
code. The consuming agent should self-check against this list before
finalizing output.

---

## Anti-Pattern 1: Re-casting inside a typed `when` branch

**What the LLM generates.**

```apex
when Account a {
    Account acct = (Account) record;   // ← redundant
    acct.AccountNumber = '...';
}
```

**Why it happens.** Training data is dominated by `instanceof` + cast
patterns. The LLM doesn't internalize that `a` is *already* typed
Account inside the branch.

**Correct pattern.**

```apex
when Account a {
    a.AccountNumber = '...';
}
```

**Detection hint.** Inside any `when <Type> <var>` branch, look for a
cast to that same type — `(Account) record`, `(Contact) sobj`. That's
always wasted code.

---

## Anti-Pattern 2: Omitting `when else` ("the case won't happen")

**What the LLM generates.**

```apex
switch on record {
    when Account a   { handleA(a); }
    when Contact c   { handleC(c); }
}
```

**Why it happens.** The LLM reasons "the caller only passes Account or
Contact, so the else branch isn't needed." This reasoning is fragile —
caller behavior changes; new types get added.

**Correct pattern.** Always include `when else` with explicit semantics:

```apex
switch on record {
    when Account a   { handleA(a); }
    when Contact c   { handleC(c); }
    when else        {
        throw new HandlerException('Unhandled: ' + record.getSObjectType());
    }
}
```

**Detection hint.** Any `switch on` block over an SObject with no `when else`
branch is suspect. Either the dispatch is exhaustive (then declare it explicitly with a throw) or it isn't (then handle the else case).

---

## Anti-Pattern 3: Using `Type.forName()` as the switch expression

**What the LLM generates.**

```apex
public static SObject build(String apiName) {
    switch on Type.forName(apiName) {  // ← Type, not SObject
        when ... { ... }
    }
}
```

**Why it happens.** `Type.forName` is the most-discussed reflection API
in Apex training data; the LLM associates "type from string → switch"
without distinguishing `System.Type` from `Schema.SObjectType` from
SObject prototype.

**Correct pattern.**

```apex
public static SObject build(String apiName) {
    Schema.SObjectType t = Schema.getGlobalDescribe().get(apiName);
    if (t == null) throw new IllegalArgumentException(apiName);
    SObject prototype = t.newSObject();
    switch on prototype {
        when Account _   { return new Account(Name = 'Default'); }
        when else        { throw new IllegalArgumentException(apiName); }
    }
    return null;
}
```

**Detection hint.** `Type.forName(...)` *anywhere* inside a `switch on`
expression is wrong.

---

## Anti-Pattern 4: Multi-type-per-`when` with comma syntax

**What the LLM generates.**

```apex
when Account a, Lead l { handleShared(a); }   // compile error
```

**Why it happens.** Java / C# / Kotlin all support multi-value matching
in their switch / pattern-match constructs. The LLM bleeds that syntax
into Apex.

**Correct pattern.**

```apex
when Account a   { handleShared(a); }
when Lead l      { handleShared(l); }
```

**Detection hint.** Any `when` clause with two or more named types and
a binding (`when X x, Y y`) is a compile error. The multi-value form is
only legal for primitives + enums (`when 1, 2, 3`).

---

## Anti-Pattern 5: Treating `when null` as "new record"

**What the LLM generates.**

```apex
switch on record {
    when null        { /* assume insert path */ insert record; }
    when Account a   { /* assume update path */ update a;      }
}
```

**Why it happens.** "null id means new record" is a common pattern
elsewhere in Apex; the LLM conflates "new record" with "the dispatch
expression is null".

**Correct pattern.** `when null` reaches only when the *expression*
itself is null. Use `Id == null` inside the typed branch for
insert-vs-update:

```apex
switch on record {
    when null { return; /* dispatch was given null */ }
    when Account a {
        if (a.Id == null) { /* insert */ } else { /* update */ }
    }
}
```

**Detection hint.** Inside a `when null` branch, any DML or business
logic that assumes a record exists is wrong — by definition the
expression is null in that branch.

---

## Anti-Pattern 6: Forgetting the namespace for managed-package custom objects

**What the LLM generates.**

```apex
when Custom_Object__c c { /* ... */ }
```

…against a record whose actual API name is
`my_pkg__Custom_Object__c` (managed package).

**Why it happens.** The LLM sees the un-namespaced name in the package
docs and treats namespace as decoration.

**Correct pattern.**

```apex
when my_pkg__Custom_Object__c c { /* ... */ }
```

**Detection hint.** Any `when` clause with a `__c` suffix and no `__`
namespace prefix is suspect when the dispatch may receive
managed-package data.
