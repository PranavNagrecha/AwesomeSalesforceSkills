# Well-Architected Notes — Apex Salesforce Id Patterns

## Relevant Pillars

### Security

Any time an Id crosses a trust boundary (URL parameter, webhook, CSV upload), a string-typed input without validation is a route to a `QueryException` at best and a type-confusion bug (treating a Lead Id as a Contact Id) at worst. Typed `Id` + `getSobjectType()` creates an enforceable contract on untrusted input.

### Reliability

Hardcoded prefixes fail silently when custom object prefixes change across orgs. `getSobjectType()` fails loudly and correctly regardless of where the code runs. The difference is a p0 support ticket in production vs a clean error in development.

## Architectural Tradeoffs

- **`Id.valueOf(str)` vs cast `(Id) str`:** Functionally equivalent. Prefer `(Id) str` for inline use, `Id.valueOf` when you want the method-call form explicit in the call site.
- **`getSobjectType()` vs prefix lookup:** Always prefer `getSobjectType()`. Prefix lookup is only appropriate when you have a string you cannot yet type and you want to avoid throwing on invalid input — a narrow window.
- **`Set<Id>` vs `Set<String>`:** Always prefer `Set<Id>` when values represent records. Cheaper equality, case-insensitive by construction, type-safe.
- **Typed methods (`Id` param) vs `String` param:** Prefer `Id` typing. The only reason to take `String` is at the edge — the REST endpoint, the Aura-enabled method — where the caller cannot send an `Id` directly. Validate and re-type immediately.

## Anti-Patterns

1. **String-prefix type routing** — breaks on managed packages, custom object renames, and cross-org deploys.
2. **Mixing 15-char and 18-char strings** — silent `false` on compare; causes records to appear "missing."
3. **Treating `Id` as a `String` everywhere** — loses the platform's free validation.

## Official Sources Used

- Apex Reference — Id Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_id.htm
- Apex Reference — Schema.SObjectType: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_sobjecttype.htm
- Apex Developer Guide — Understanding Id Field Values: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_primitives.htm
- Salesforce Help — Record Id Prefixes: https://help.salesforce.com/s/articleView?id=000385203.htm
- Salesforce Well-Architected — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
