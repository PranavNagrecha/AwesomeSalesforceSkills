# Well-Architected Notes — Apex Enum Patterns

## Relevant Pillars

- **Operational Excellence** — Enum-based dispatch surfaces missed
  cases through `when else` throws. Strings silently fall through;
  enums make the missed branch loud, exactly when a new value is
  added by a teammate who didn't read every dispatcher.
- **Security** — Enums constrain the input space. A method that
  accepts `RenewalAction` cannot be called with arbitrary user
  input; the conversion at the boundary (`valueOf` + try/catch) is
  the one place untrusted strings are validated. This is more
  defensible than scattered `if (action == 'escalate' || action ==
  'Escalate' || ...)` checks.

## Architectural Tradeoffs

The main tradeoff is **closed set vs configuration agility**. An
enum freezes the set of values at compile time. Adding a value
requires a deployment. If the set changes weekly (campaign types,
product SKUs), use Custom Metadata or a picklist instead and accept
the runtime-string discipline.

Specifically:

- For state machines and dispatch keys: enum.
- For domain values that ops change without a release: Custom
  Metadata or picklist.
- For values that are *both* a closed contract *and* a configurable
  display label: enum + a Custom Metadata "label override" table.

## Anti-Patterns

1. **String-keyed dispatch table** — `Map<String, Handler>` keyed
   by a free-form string is enum-without-the-safety. Typos compile
   fine and fail at runtime. Promote to `Map<MyEnum, Handler>`.
2. **Persisting enum ordinals** — ordinals are positional and
   unstable across reorderings. Persist `name()` (the string form)
   and convert with `valueOf` on read.
3. **`switch on Enum` without `when else`** — a missed case is a
   silent no-op. Always include `when else { throw ... }` so a new
   enum value surfaces a hard failure in the first test that hits
   it.

## Official Sources Used

- Apex Enums (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_enums.htm
- Switch Statement (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_switch.htm
- System.NoSuchElementException (Apex Reference) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_NoSuchElementException.htm
- Versioning Apex Code in Managed Packages — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_versioning_intro.htm
- Salesforce Well-Architected: Adaptable — https://architect.salesforce.com/well-architected/adaptable/composable
