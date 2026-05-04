---
name: apex-switch-on-sobject
description: "Apex switch-on-SObjectType patterns — type dispatching across SObject collections, polymorphic handlers, the typed-variable binding that makes `when SObjectType varName` more than a tag check. Covers the single-type-per-when-block restriction, the null branch, the no-fall-through rule, and why `Type.forName()` cannot be used in a switch expression. NOT for basic Apex switch syntax on Integer / String / enum (use Apex Developer Guide directly), NOT for dynamic field access (see apex/dynamic-apex)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "switch on sobject type apex polymorphic dispatch"
  - "type-dispatch on a list of mixed sobjects"
  - "when SObjectType varName typed binding apex"
  - "trigger handler dispatch by sobject type"
  - "apex switch fall through behavior"
  - "switch on Type.forName not working"
tags:
  - switch-statement
  - sobject-type
  - polymorphism
  - trigger-handler
  - type-dispatch
inputs:
  - "Apex code that dispatches behavior based on the runtime SObjectType of a record (or a heterogeneous collection)"
  - "Whether the dispatch happens once (single record) or per element (loop body)"
  - "Whether a default branch is required for soundness"
outputs:
  - "Idiomatic `switch on <SObject>` block with one when-branch per type"
  - "Decision: when to use switch vs. instanceof / getSObjectType().equals(...)"
  - "Diagnosis: silent-skip risk if `when else` is omitted on a non-exhaustive switch"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# Apex Switch on SObject

`switch on` over an SObject expression is the right tool for type-dispatch
inside a heterogeneous collection — a generic trigger handler, a polymorphic
processor, a classifier that runs different validation per object type. It
buys two things over a chain of `instanceof` / `getSObjectType().equals(...)`
checks: **type-narrowed bindings inside each branch** (no cast required) and
a single explicit `when else` for the unhandled case.

What this skill is NOT. The simpler `switch on Integer / String / enum` form
is plain Apex syntax — go directly to the Apex Developer Guide. Dynamic field
access (`Schema.getGlobalDescribe()`, `record.get(fieldName)`) lives in
`apex/dynamic-apex`. This skill is specifically about the SObject expression
form and the branch-binding semantics.

---

## Before Starting

- Confirm the dispatch is *runtime* — if you statically know the type at
  compile time, skip the switch and just write the typed code.
- Confirm whether **`when else`** is required: if the switch is non-exhaustive
  (you only handle some types), you almost always need `when else` because
  unmatched cases silently fall through to the end of the switch with no
  side-effect — that's the failure mode that hides bugs longest.
- Note that **the binding form requires exactly one SObject type per `when`
  block**. You cannot write `when Account, Contact a { ... }` and expect a
  typed `a`; that form is reserved for value-list matching on enums and
  primitives.

---

## Core Concepts

### The two switch-on-SObject forms

```apex
// Form 1 — bind a typed variable inside the branch (the whole point of this feature).
switch on record {
    when Account a {
        // 'a' is typed Account here. No cast, no Schema check.
        a.AccountNumber = generateAccountNumber();
    }
    when Contact c {
        c.LastName = c.LastName?.toUpperCase();
    }
    when null {
        // Reached only when 'record' itself is null — safe, no NullPointerException.
        return;
    }
    when else {
        // Anything else; the runtime type is something we didn't handle.
        // SILENTLY SKIPPING this branch is the #1 latent bug — declare it explicitly.
        System.debug('Unhandled SObjectType: ' + record.getSObjectType());
    }
}
```

```apex
// Form 2 — match by exact value (rare for SObjects; mostly for primitives).
switch on someInteger {
    when 1, 2, 3 { /* multi-value matching only works for primitives + enums */ }
    when else    { ... }
}
```

### Three rules that bite people

1. **No fall-through.** Each `when` branch executes and the switch exits. There is no `break` keyword and no implicit fall-through to the next branch (unlike C / Java's switch).
2. **`when null` matches a null expression.** It does NOT match a record whose Id is null. It is reached only when the *expression* itself is null. This makes switch null-safe by design — no `NullPointerException` from the dispatch.
3. **`Type.forName(...)` is NOT a substitute for SObjectType.** `Type.forName('Account')` returns `System.Type`, which is not what `switch on` accepts in this form. To dispatch from a string name, look up the SObject prototype: `Schema.getGlobalDescribe().get(name).newSObject()` and switch on *that*.

---

## Common Patterns

### Pattern A — Polymorphic trigger handler

**When to use.** A single handler that runs across multiple SObject types
(common in framework code, `templates/apex/TriggerHandler.cls`).

```apex
public class PolyHandler {
    public static void handle(List<SObject> records) {
        for (SObject record : records) {
            switch on record {
                when Account a   { handleAccount(a); }
                when Contact c   { handleContact(c); }
                when Lead l      { handleLead(l); }
                when else        {
                    // Programmer error — every type the framework registers must have a branch.
                    throw new HandlerException('Unhandled type: ' + record.getSObjectType());
                }
            }
        }
    }
}
```

**Why not the alternative.** A chain of
`if (record instanceof Account) { Account a = (Account) record; ... }` is
verbose and re-introduces casts that the binding form already handled.

### Pattern B — Classifier with explicit unhandled-case

**When to use.** You handle some types and want all other types to fall
through harmlessly with a logged warning.

```apex
public static String classify(SObject record) {
    switch on record {
        when Account a   { return a.Type;            }
        when Contact c   { return c.LeadSource;      }
        when null        { return null;              }
        when else        {
            // Crucial: without this branch, the method returns the default null
            // and the caller has no signal that 'record' was an unrecognized type.
            ApplicationLogger.warn('classify: unhandled ' + record.getSObjectType());
            return null;
        }
    }
}
```

### Pattern C — Dispatch from a string type name

**When to use.** The caller has the type name as a string (config-driven
dispatch, custom-metadata-driven router).

```apex
public static SObject createByName(String objectApiName) {
    Schema.SObjectType t = Schema.getGlobalDescribe().get(objectApiName);
    if (t == null) {
        throw new IllegalArgumentException('Unknown SObject: ' + objectApiName);
    }
    SObject prototype = t.newSObject();
    switch on prototype {
        when Account a   { return new Account(Name = 'Default Name');     }
        when Contact c   { return new Contact(LastName = 'Default Last'); }
        when else        {
            // The string named a real SObject, but this method only constructs a few.
            throw new IllegalArgumentException('Unsupported for default-create: ' + objectApiName);
        }
    }
}
```

`Type.forName(objectApiName)` does NOT work as the switch expression here —
it returns `System.Type`, not an SObject prototype.

---

## Decision Guidance

| Situation | Use this | Reason |
|---|---|---|
| Trigger handler dispatching across 3+ SObject types | `switch on record` with one branch per type | Typed bindings, explicit `when else`, no casts |
| Single-type check ("is this an Account?") | `record.getSObjectType() == Account.SObjectType` | Switch overhead not worth it for one check |
| Dispatch from a string SObject API name | `Schema.getGlobalDescribe().get(name).newSObject()` then switch on the prototype | `Type.forName()` returns `System.Type`, not SObjectType |
| Heterogeneous list with frequent unhandled types | Switch with `when else` returning early or logging | Silent-skip is the failure mode without `when else` |
| Two types share identical handling | Two `when` branches calling the same private method | Multi-type-per-when binding is not supported |

---

## Recommended Workflow

1. **Confirm runtime dispatch.** If the type is known at compile time, write typed code; do not introduce a switch.
2. **List every SObject type the dispatch can see.** From the caller, the trigger registration, or the framework contract.
3. **Choose `when else` semantics.** Either (a) throw — programmer error, the dispatch should be exhaustive — or (b) log + return safely. Never omit `when else` on a non-exhaustive switch.
4. **Place `when null` before `when else`** if the expression can be null. The `when null` branch is the null-safety guarantee for the entire switch.
5. **Verify in test.** Write a test class that passes one record of every handled type plus one record of an unhandled type; assert the unhandled-case behavior matches step 3.

---

## Review Checklist

- [ ] Switch has either `when else` or every concrete SObject type the caller can pass.
- [ ] `when null` branch present if the expression can be null.
- [ ] No `when else` block silently returns / does nothing without a comment justifying it.
- [ ] No use of `Type.forName(...)` as the switch expression.
- [ ] Test class covers one record of every handled type + one unhandled type.
- [ ] Each branch's bound variable is used (or removed); unused-binding is a smell that the branch could be just `when Account` without binding.

---

## Salesforce-Specific Gotchas

1. **Silent skip without `when else`.** A non-exhaustive switch on an unhandled type does nothing — no exception, no warning. Always declare `when else`. (See `references/gotchas.md` § 1.)
2. **`Type.forName('Account')` does not produce a switch-able expression.** It returns `System.Type`. You need `Schema.getGlobalDescribe().get('Account').newSObject()` to get an SObject prototype. (See `references/gotchas.md` § 2.)
3. **Multi-type-per-when is not supported.** `when Account a, Contact c { ... }` does not compile. (See `references/gotchas.md` § 3.)
4. **`when null` matches the expression being null, not an SObject with `Id = null`.** Don't use it for "new record" detection. (See `references/gotchas.md` § 4.)
5. **Managed-package custom SObjects need the namespace.** `when my_pkg__Custom_Object__c c { ... }` — the namespace is part of the type identity. (See `references/gotchas.md` § 5.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Refactored Apex | Switch-based dispatch replacing instanceof chains, with typed bindings per branch |
| Test class | One record per handled type + one unhandled type; asserts `when else` behavior |
| `when else` decision rationale | One sentence per refactor: "throw" or "log + safe-return" |

---

## Related Skills

- `apex/dynamic-apex` — Schema.getGlobalDescribe / dynamic field access; pair with this skill when dispatching from a string API name
- `apex/trigger-framework` — when this dispatch goes inside a generic trigger handler; `templates/apex/TriggerHandler.cls` is the canonical base
- `apex/apex-mocking-and-stubs` — for the test class that exercises every branch
