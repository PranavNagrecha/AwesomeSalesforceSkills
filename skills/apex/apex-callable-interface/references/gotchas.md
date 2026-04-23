# Gotchas — Apex Callable Interface

Non-obvious Salesforce platform behaviors that cause real production problems.

## Gotcha 1: `Callable` Is Not Callable From Flow

**What happens:** An admin drags an "Apex Action" element, expects to see their `Callable` class, but the picker shows nothing.

**When it occurs:** Any Flow attempting to invoke `Callable`.

**How to avoid:** Expose `@InvocableMethod` instead. `Callable` is Apex-to-Apex only. You can stack: the `@InvocableMethod` body calls into a `Callable` registry.

---

## Gotcha 2: `Type.forName(null, 'X')` Uses The Caller's Namespace

**What happens:** Managed-package code calling `Type.forName(null, 'SubscriberClass')` fails to find a subscriber class because the null namespace means "this namespace" (the package's).

**When it occurs:** Managed-package extension points loading subscriber implementations.

**How to avoid:** Persist both namespace and class name in metadata. Pass namespace explicitly: `Type.forName(config.Namespace__c, config.ClassName__c)`. For subscriber-org classes, namespace is empty string or `''`, NOT null.

---

## Gotcha 3: Action String Typos Are Runtime Errors, Not Compile Errors

**What happens:** Caller passes `'customze'` (typo) instead of `'customize'`. The `switch on action` hits the `when else` clause, and if there's no default throw, returns `null` silently.

**When it occurs:** Any call site with hand-typed action strings.

**How to avoid:** Always have a `when else` that throws with the bad action name. Document actions as `public static final String` constants consumers can import.

---

## Gotcha 4: `(Type) args.get('key')` On Wrong Type Throws `TypeException`, Not A Clean Null

**What happens:** Caller passes `'orderId': '001...'` (String) where the receiver expects `Id`. `(Id) args.get('orderId')` throws `TypeException` — but typed as `String`, the cast does succeed (String IS castable to Id syntactically), then the next operation blows up.

**When it occurs:** Any loosely-typed `Map<String, Object>` contract.

**How to avoid:** Validate types explicitly at the top of `call`: `Object raw = args.get('orderId'); if (!(raw instanceof String) && !(raw instanceof Id)) { throw ... }`.

---

## Gotcha 5: `Callable` Runs In The Caller's Transaction

**What happens:** A `Callable` that inserts records adds to the caller's DML count. A caller at 140 DML statements invoking a `Callable` that does 15 more hits the 150 limit.

**When it occurs:** Chained calls, batch loops, trigger contexts.

**How to avoid:** Document governor-heavy actions. For work that must be isolated, have the `Callable` enqueue a `Queueable` rather than doing DML inline.

---

## Gotcha 6: Managed-Package `Callable` Classes Need `global` Access

**What happens:** A managed package ships a `public with sharing class X implements Callable`. Subscriber code cannot instantiate it — `public` is package-scoped.

**When it occurs:** Shipping a `Callable` from a managed package intended as an extension point.

**How to avoid:** Use `global` for classes intended for subscriber use. Internal `Callable` classes inside the package can stay `public`.

---

## Gotcha 7: Subscriber Classes Without Namespace Use Empty String

**What happens:** Metadata record stores `Namespace__c = null`. Code does `Type.forName(config.Namespace__c, ...)` and finds the package-namespaced class by accident, or fails to find the subscriber class.

**When it occurs:** Extension-point lookups where subscribers are in the default namespace.

**How to avoid:** For default namespace, use `''` (empty string), not `null`. Document the convention in metadata field help.

---

## Gotcha 8: Removing An Action Breaks Consumers Silently

**What happens:** Version 2 of a `Callable` removes the `'legacyExport'` action. Consumers hit the `when else` throw, and the operator sees a 500 error in prod they cannot reproduce in sandbox (where no consumer was testing legacy).

**When it occurs:** Refactoring a `Callable` class that has unknown external consumers.

**How to avoid:** Treat action strings as a public API. Deprecate with logging before removal: the `when 'legacyExport'` branch can log a warning and call the new action, giving consumers time to migrate.
