# Gotchas — Apex Switch on SObject

Non-obvious behaviors that cause real bugs when using `switch on` over an
SObject expression.

---

## Gotcha 1: Silent skip when `when else` is omitted

**What happens.** A non-exhaustive switch (no `when else`) on an SObject
type that doesn't match any branch evaluates to nothing — no exception,
no debug log, no compile-time warning.

**When it occurs.** A new SObject type is added later (custom object,
package install) and routed through an existing handler. The switch
quietly skips it. The bug surfaces in production months later as
"validation didn't fire on these records".

**How to avoid.** Always declare `when else` explicitly. Two valid
choices:
- `throw new HandlerException('Unhandled: ' + record.getSObjectType())` if the dispatch is supposed to be exhaustive (programmer error otherwise).
- Log + safe-default if non-exhaustive on purpose (`ApplicationLogger.warn(...)` + `return null`).

The validator at `scripts/validate_repo.py` cannot catch this — only code
review and a test that passes an unhandled type can.

---

## Gotcha 2: `Type.forName('Account')` does not work as the switch expression

**What happens.** Compile error or runtime mismatch — `Type.forName()`
returns `System.Type`, not `Schema.SObjectType` and not an SObject
prototype. The switch-on-SObject form expects an expression whose runtime
class is an SObject subclass.

**When it occurs.** Config-driven dispatch where the API name is a string
("Account", "MyPkg__Custom__c").

**How to avoid.** Use the global describe, instantiate a prototype, and
switch on the prototype:

```apex
SObject prototype = Schema.getGlobalDescribe().get(apiName).newSObject();
switch on prototype { when Account a { ... } when else { ... } }
```

The prototype is throw-away — only its concrete class matters for the
switch dispatch.

---

## Gotcha 3: Multi-type-per-when binding does not compile

**What happens.** `when Account a, Contact c { ... }` is a compile error.
The multi-value form (`when 1, 2, 3 { ... }`) is reserved for primitives
and enums.

**When it occurs.** Refactoring an `instanceof` chain where two types
share identical handling.

**How to avoid.** Two separate `when` branches each call a shared private
method:

```apex
switch on record {
    when Account a   { shared(a); }
    when Lead l      { shared(l); }
    when else        { ... }
}

private static void shared(SObject r) { /* logic that takes the SObject base */ }
```

---

## Gotcha 4: `when null` matches the *expression*, not `record.Id == null`

**What happens.** Practitioners assume `when null` matches a record whose
Id field is null (a "new" or "unsaved" record). It doesn't — it matches
only when the expression itself (`record`) is null.

**When it occurs.** Trying to use the switch to differentiate
insert-vs-update paths.

**How to avoid.** For insert-vs-update, check `record.Id == null`
explicitly inside the typed branch:

```apex
switch on record {
    when Account a {
        if (a.Id == null) { /* insert path */ } else { /* update path */ }
    }
    when null { /* the dispatch itself was given a null reference */ }
    when else { /* ... */ }
}
```

---

## Gotcha 5: Managed-package custom SObjects need the namespace in the `when` branch

**What happens.** `when Custom_Object__c c { ... }` does not match a
managed-package custom object whose fully-qualified API name is
`my_pkg__Custom_Object__c`.

**When it occurs.** Subscribers of a managed package writing dispatch
code in their own org.

**How to avoid.** Use the namespaced type in the `when` clause:

```apex
when my_pkg__Custom_Object__c c { /* ... */ }
```

If the consumer code is itself in the same package, the bare name works
and the namespace is implicit. Cross-namespace code must qualify.

---

## Gotcha 6: Compiler does not warn on duplicate-type branches

**What happens.** Two branches for the same SObject type both compile;
the second is unreachable but no warning fires.

```apex
switch on record {
    when Account a { handleA1(a); }
    when Account a { handleA2(a); }   // ← unreachable; no warning
}
```

**How to avoid.** Code review. The validator can catch this only via a
custom checker (which `scripts/check_apex_switch_on_sobject.py` does for
this skill — see that file).

---

## Gotcha 7: `getSObjectType()` returns null on a record with no type set

**What happens.** A bare `new SObject()` (rare but possible in test
contexts) has `getSObjectType()` return null. The switch-on-SObject form
itself handles this safely (it just doesn't match any typed `when`
branch and falls into `when else`), but downstream code that calls
`record.getSObjectType().getDescribe()` inside the `when else` branch
will NPE.

**How to avoid.** Inside `when else`, null-check `getSObjectType()`
before calling `.getDescribe()`:

```apex
when else {
    Schema.SObjectType t = record?.getSObjectType();
    String label = (t == null) ? '(unknown)' : t.getDescribe().getLabel();
    System.debug('Unhandled: ' + label);
}
```
