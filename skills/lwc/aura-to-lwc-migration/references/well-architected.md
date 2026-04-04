# Well-Architected Notes — Aura to LWC Migration

## Relevant Pillars

- **User Experience** — LWC renders faster and with lower overhead than Aura because it uses native browser Web Components APIs rather than a framework-level virtual DOM abstraction. Migrating to LWC directly improves perceived performance for end users: smaller JavaScript bundles, faster initial paint, and better mobile responsiveness. The migration itself must not introduce regressions in interaction fidelity — event handling, navigation transitions, and data refresh behavior must be verified to match the original Aura component.

- **Operational Excellence** — Aura is in maintenance mode as of Spring '25. Salesforce no longer adds new features or improvements to the Aura framework. Staying on Aura means accepting technical debt that grows over time: new base components, new platform APIs, and new DevOps tooling (e.g., LWC Jest testing) are LWC-only. Migration is an operational investment that reduces long-term maintenance burden and keeps the org aligned with Salesforce's strategic direction.

- **Security** — LWC enforces Locker Service security through native browser shadow DOM (or synthetic shadow in legacy contexts) rather than Aura's JavaScript-level Locker Service. Shadow DOM boundary enforcement is stricter: cross-component DOM querying via `querySelector` across shadow roots is blocked. Migration must verify that no component relied on unrestricted DOM traversal across Aura component boundaries, which is a Locker bypass that would be closed by migration.

## Architectural Tradeoffs

**Big-bang rewrite vs incremental migration:** Big-bang delivers a fully migrated codebase faster and avoids the complexity of maintaining an LMS bridge layer. It carries more deployment risk and requires full regression testing before go-live. Incremental migration allows component-by-component validation and keeps production stable, but requires maintaining coexistence infrastructure (LMS channels, Aura wrappers) for a longer period. The right choice depends on the number of components, the complexity of the shared event model, and the team's capacity for parallel development.

**LMS channel permanence:** LMS channels created as migration bridges can be kept permanently as the cross-component messaging infrastructure even after full LWC migration. This is a valid architecture choice — LMS is a supported production mechanism, not just a migration workaround. However, if the event pattern is local (parent-child), collapsing from LMS to direct property binding or CustomEvent reduces indirection and improves debuggability.

**Shadow DOM strictness:** LWC's shadow DOM (even synthetic) is stricter than Aura's Locker Service in terms of cross-component DOM access. If a component relied on accessing child component DOM nodes via `querySelector` across component boundaries, this breaks after migration. This is actually a well-architected constraint — the correct pattern is to expose component state via `@api` properties and CustomEvents rather than reaching into child DOM. Migration forces this correction.

## Anti-Patterns

1. **Maintaining Aura application events indefinitely** — Using LMS to bridge Aura application events during migration is a temporary measure. Leaving Aura application events active alongside LMS channels long-term creates dual-messaging infrastructure, makes debugging unclear, and prevents full elimination of the Aura framework dependency. Complete the migration by removing Aura application event infrastructure once all publishers and subscribers have moved to LMS or direct CustomEvent.

2. **Accumulating permanent Aura wrapper components** — Aura wrappers created to host legacy Aura components inside LWC-first pages should have a tracked end date. Permanent wrappers add framework overhead (both Aura and LWC are loaded for the page), complicate testing, and prevent full LWC adoption. Every Aura wrapper should have a linked backlog item for completing the inner component migration.

3. **Copying $A patterns verbatim** — Porting `$A.enqueueAction`, `$A.getCallback`, `$A.createComponent`, or value provider syntax directly into LWC JavaScript without rethinking the pattern. Each of these represents an Aura-framework coupling point. The correct migration is to rethink the pattern in LWC terms (wire adapters, reactive properties, conditional rendering) rather than hunting for a `$A` equivalent.

## Official Sources Used

- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Architects: Decision Guide — https://architect.salesforce.com/decision-guides/
