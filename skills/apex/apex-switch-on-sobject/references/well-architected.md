# Well-Architected Notes — Apex Switch on SObject

## Relevant Pillars

- **Operational Excellence** — The dispatch shape directly affects how
  fast a future engineer can read and extend the handler. Switch with
  typed bindings + explicit `when else` is the most readable form for
  ≥3 SObject types; it removes manual casts (one less thing to misread)
  and makes the unhandled case impossible to miss in code review.
- **Security** — `when else` doubles as a guardrail. A handler that
  silently skips unknown types is a vector for "I added Order processing
  to my package, but the validation layer didn't fire on it" — which can
  produce records that bypass FLS / sharing checks because the
  validation pass thought the type was out of scope. Explicit `when else`
  closes that gap.

## Architectural Tradeoffs

- **Switch vs. visitor pattern.** A full visitor pattern (separate
  `Visitor` interface with `visitAccount`, `visitContact` methods) is
  more extensible — adding a new type is a compile error in every
  visitor. Apex's switch-on-SObject is lighter weight but lacks that
  exhaustiveness check. Use the visitor when the type set is closed and
  important; use switch when the type set is small and dispatch sites
  are few.
- **Switch vs. type-keyed map of handlers.** A
  `Map<Schema.SObjectType, Type>` registry of handler classes is the
  most flexible — handlers can be registered at runtime via custom
  metadata. Cost is more code and less locality (the dispatch logic
  lives in the registry, not the call site). Use the registry for
  framework-level dispatch (one handler per record type, dozens of
  types); use switch for in-method polymorphism.
- **Switch vs. instanceof chain.** Switch wins on readability and
  binding ergonomics. The only reason to keep an instanceof chain is
  legacy code below a refactor budget — there's no semantic advantage.

## Anti-Patterns

1. **Non-exhaustive switch without `when else`.** Silent skip on
   unhandled types. Always declare `when else`.
2. **Duplicating cast logic inside a `when` branch.** The binding form
   already gives you a typed variable — `when Account a { Account x = (Account) record; }` is redundant and a sign the author copied an instanceof chain.
3. **Switching on `Type.forName(name)`.** Returns `System.Type`, not an
   SObject. Look up the prototype via `Schema.getGlobalDescribe().get(name).newSObject()` instead.
4. **Putting `when null` last.** Stylistically `when null` belongs near
   the top of the switch — it's the null-safety guarantee, and reading
   it first establishes that the dispatch is null-safe before the
   reader enters the typed branches.

## Official Sources Used

- Apex Switch Statements — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_switch.htm
- Apex SObject Types — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SObject_types.htm
- Schema.SObjectType Class Reference — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Schema_SObjectType.htm
- Apex Dynamic Apex (sibling skill) — `skills/apex/dynamic-apex/SKILL.md`
- Trigger framework template — `templates/apex/TriggerHandler.cls`
