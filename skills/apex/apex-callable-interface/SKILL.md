---
name: apex-callable-interface
description: "Use when building Apex classes meant to be invoked dynamically — from Flow, external packages, managed-package extensions, or loose-coupling code that cannot directly reference the concrete class. Trigger keywords: Callable, call method, dynamic Apex, action registry, plugin pattern, managed package extension point. NOT for: Invocable methods exposed to Flow (see apex-invocable-methods) or REST endpoints (see apex-rest-services)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "I need to let admins point a record-triggered flow at any Apex class without recompiling"
  - "How do I build a plugin system in Apex where subscribers register by name?"
  - "My managed package needs an extension point consumers can plug their Apex into"
tags:
  - apex-callable-interface
  - apex-dynamic-dispatch
  - apex-extension-point
  - apex-plugin-pattern
inputs:
  - "The action or operation to expose for dynamic invocation"
  - "The expected input keys and their types"
  - "The call site (Flow, managed package consumer, service registry)"
outputs:
  - "A `Callable` implementation with a documented action contract"
  - "Checker findings against unsafe dynamic-dispatch patterns"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Apex Callable Interface

Activate this skill when Apex must be invoked dynamically without the caller having a compile-time reference. The `System.Callable` interface provides a single-method contract (`call(String action, Map<String, Object> args)`) that lets Flow, managed package consumers, and service registries address any implementing class by type name and action string.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Who is the caller?** A managed-package extension, Flow, an in-repo service registry, or ad-hoc reflection?
- **Is the call site trusted?** A trusted caller can skip input validation; an untrusted one cannot.
- **Does the action need to be async?** `Callable.call` runs synchronously in the caller's transaction.
- **What's the contract versioning story?** Changing accepted keys is a breaking change for every consumer.

---

## Core Concepts

### The `System.Callable` Interface

One method: `Object call(String action, Map<String, Object> args)`.

- `action` is a free-form string — you define the action vocabulary per class.
- `args` is a `Map<String, Object>` — you document the expected keys.
- Return is `Object` — callers cast. Document the return shape per action.
- The interface is in the `System` namespace and is available in every org.

### Dynamic Instantiation Via `Type.forName` + Cast

A caller typically looks like:

```apex
Type t = Type.forName(namespace, className);
if (t == null) throw new HandlerNotFoundException(className);
Object instance = t.newInstance();
if (!(instance instanceof Callable)) {
    throw new NotCallableException(className);
}
Object result = ((Callable) instance).call(action, args);
```

The indirection is the whole point — the caller has zero compile-time coupling to the implementation.

### Extension-Point Pattern (Managed Package)

Managed packages can ship a `Callable` with public action strings. Subscribers implement the same `Callable` in their org with custom logic, and the package looks up the subscriber's class via a custom metadata record or custom setting.

### Flow Compatibility

Apex `Callable` is NOT directly invokable from Flow. Flow needs `@InvocableMethod`. `Callable` is for code-to-code dispatch — often behind an `@InvocableMethod` facade when Flow is a consumer.

---

## Common Patterns

### Plugin Action Registry

**When to use:** You have a fixed set of "hook" points where admins or subscribers should be able to inject logic.

**How it works:**

```apex
public with sharing class PluginRegistry {
    public static Object invoke(String pluginApiName, String action, Map<String, Object> args) {
        Plugin__mdt config = Plugin__mdt.getInstance(pluginApiName);
        if (config == null) return null;
        Type t = Type.forName(config.Namespace__c, config.ClassName__c);
        if (t == null || !Callable.class.isAssignableFrom(t)) {
            throw new PluginException('Plugin not found or not Callable: ' + pluginApiName);
        }
        return ((Callable) t.newInstance()).call(action, args);
    }
}
```

**Why not the alternative:** Hardcoded `if (pluginName == 'X') new X()` requires redeployment for every new plugin.

### Documented Action Contract

**When to use:** Every `Callable` class where you expect multiple actions.

**How it works:**

```apex
global with sharing class OrderFulfillmentActions implements Callable {
    // Actions:
    //   'reserveInventory': args { 'orderId': Id } -> Id (reservation id)
    //   'cancelReservation': args { 'reservationId': Id } -> Boolean
    //   'quote': args { 'productIds': Set<Id>, 'qty': Map<Id, Integer> } -> Decimal
    global Object call(String action, Map<String, Object> args) {
        switch on action {
            when 'reserveInventory' { return reserveInventory((Id) args.get('orderId')); }
            when 'cancelReservation' { return cancelReservation((Id) args.get('reservationId')); }
            when 'quote' { return quote(args); }
            when else { throw new CalloutException('Unknown action: ' + action); }
        }
    }
    // ...
}
```

**Why not the alternative:** Undocumented `Map<String, Object>` contracts lead to runtime casts that fail silently.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Flow needs to invoke Apex | `@InvocableMethod` | `Callable` is not wired to Flow directly |
| Managed package extension point | `Callable` via metadata | Loose coupling survives package updates |
| In-repo dispatch by config | `Callable` via metadata | Removes hardcoded `if/else` branches |
| REST client calling Apex | `@RestResource` | `Callable` is not a REST endpoint |
| Scheduled or async job | `Queueable` / `Schedulable` | `Callable` runs in caller's transaction |
| Type-safe helper class | Regular Apex class | `Callable` is for dynamic dispatch only |

---

## Recommended Workflow

1. Confirm the caller actually needs dynamic dispatch (most don't — direct class reference is simpler).
2. Define the action vocabulary as comments at the top of the class — name, expected keys, return type.
3. Implement `call` with a `switch on action` and throw on unknown actions.
4. Add `TypeException`-safe casts on every `args.get(...)` call.
5. Write tests: a happy-path test per action plus an "unknown action" test that asserts the expected exception.
6. If the class is a managed-package extension point, ship a reference implementation and document the contract in the package's help.

---

## Review Checklist

- [ ] All expected action strings are documented at the top of the class.
- [ ] `switch on action` with a default `when else` throw clause.
- [ ] Every `args.get('key')` is type-cast to the expected type with a clear failure mode.
- [ ] Unknown action test asserts the specific exception type.
- [ ] Class is `global` if it's a managed-package extension point; `public` otherwise.
- [ ] `Callable` consumers use `Type.forName` + `instanceof Callable` check, not raw cast.

---

## Salesforce-Specific Gotchas

1. **`Callable` is synchronous** — calls run in the caller's transaction, share governor limits, and cannot be enqueued by the interface alone.
2. **`Type.forName(null, 'X')` searches the caller's namespace** — pass the correct namespace explicitly in a managed-package context.
3. **`Callable.call` return is `Object`** — callers must cast; a typo in the action string yields a runtime exception, not a compile error.
4. **Args map is not validated** — missing keys return `null` from `.get()`, casts to primitives may `NullPointerException` or `TypeException`.
5. **No Aura/LWC direct access** — `Callable` is Apex-to-Apex; UI layers should go through `@AuraEnabled` facades.
6. **Removing an action is a breaking change** — downstream consumers have no compile-time contract, so silent regressions are common.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `scripts/check_apex_callable_interface.py` | Scans for unguarded `args.get` casts, missing `when else`, and `Callable` used where `@InvocableMethod` is correct |
| `templates/apex-callable-interface-template.md` | Work template for defining a `Callable` class with a documented action contract |

---

## Related Skills

- `apex-invocable-methods` — when Flow needs to invoke Apex (not `Callable`)
- `apex-custom-metadata-types` — storing plugin registrations
- `apex-dependency-injection` — higher-level patterns that may use `Callable` under the hood
