# Well-Architected Notes — Apex Callable Interface

## Relevant Pillars

### Reliability

`Callable` enables loose coupling between publishers (managed packages, core services) and subscribers (extensions, plugins, territory-specific logic). This is a reliability win — the publisher can ship fixes without waiting on every subscriber, and subscribers can modify behavior without touching core code. The cost is that the interface has no compile-time contract; reliability depends on discipline around action-name documentation and default error branches.

### Operational Excellence

Well-designed `Callable` classes document their action vocabulary in a single, searchable place (class header comment + metadata description). Consumers can onboard without reading the implementation. Poorly-designed `Callable` classes become lore-only: only the author knows which actions exist.

## Architectural Tradeoffs

- **`Callable` vs `@InvocableMethod`:** Flow binds to `@InvocableMethod`. Apex binds to `Callable`. If both matter, wrap `Callable` inside an `@InvocableMethod` facade. Never try to use `Callable` for Flow.
- **`Callable` vs Direct Class Reference:** Direct reference is simpler and type-safe. Only reach for `Callable` when you genuinely need loose coupling — managed packages, plugin registries, admin-configurable dispatch. Reflex use of `Callable` is over-engineering.
- **`global` vs `public` Access:** Managed-package extension points must be `global`. Internal `Callable` classes stay `public`. Choose at class creation; changing later is a breaking change.
- **Action Strings vs Method-Per-Action Class:** For fewer than ~3 actions, consider separate classes each implementing `Callable` for one action. For many related actions, one class with `switch on action`.

## Anti-Patterns

1. **Using `Callable` Where Direct Class Reference Works** — adds indirection, removes type safety, buys nothing.
2. **`Callable` For Flow** — fundamental mismatch; `@InvocableMethod` is the only Flow binding.
3. **Undocumented Action Vocabulary** — consumers must read the source. Breaking changes become surprises.
4. **Silent `when else` Fallthrough** — typos produce null returns with no feedback.

## Official Sources Used

- Apex Reference — System.Callable Interface: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_System_Callable.htm
- Apex Developer Guide — Extending Managed Packages: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callable_interface.htm
- Apex Reference — Type Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_type.htm
- ISVforce Guide — Extensibility: https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/
- Salesforce Well-Architected — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
