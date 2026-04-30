# Well-Architected Notes — Custom Button to Action Migration

## Relevant Pillars

- **User Experience** — Lightning Quick Actions, Screen Flows, and LWC Quick Actions provide consistent UX patterns across the org: action bar placement, mobile parity, accessible focus management, predictable spinner / toast feedback. Classic JavaScript buttons varied wildly in look and feel — some used `alert()`, some used custom popups, some did inline DOM manipulation. Migration normalizes the action surface, making the org feel cohesive and reducing per-action user training.

- **Operational Excellence** — JavaScript buttons are unsupported in Lightning Experience and silently render as nothing. The org accumulates "ghost" Page Layout entries that admins forget about. Migrating to supported Lightning action types removes a class of silent failures and aligns the action surface with the platform's supported, evolving APIs (Lightning Confirm, Toast Events, NavigationMixin, Lightning Message Service). Each migrated action becomes maintainable through Setup or LWC source rather than free-form HTML/JS in a button definition.

- **Security** — Classic JavaScript buttons could call `sforce.connection.update()` to perform DML directly from the browser without going through Apex sharing rules — a subtle but real security gap if the user had API access but the Apex layer was the intended security boundary. Lightning Quick Actions force traffic through `@AuraEnabled` Apex methods that explicitly declare `with sharing` and FLS enforcement (`WITH SECURITY_ENFORCED`, `Security.stripInaccessible`). The migration is the moment to verify that security is enforced at the Apex layer, not assumed at the UI layer.

## Architectural Tradeoffs

**Headless LWC vs Screen Flow for one-click actions:** Headless LWC provides the lowest-friction UX (one click, toast, done). Screen Flow adds a confirmation screen and can be configured by admins without code. Tradeoff: Headless LWC requires developer effort but produces a snappier UX; Screen Flow is admin-maintainable at the cost of an extra click. For high-frequency actions, Headless LWC; for occasional or admin-tunable actions, Screen Flow.

**Mass Quick Action vs invocable Apex from Flow:** Mass Quick Action with an LWC gives the user immediate per-record feedback and a custom UI for the operation. Invocable Apex from a Flow is admin-configurable and supports complex business logic without code. Tradeoff: LWC for UX richness, Flow for admin maintainability. For mission-critical mass operations, LWC with progress reporting; for declarative bulk updates, Flow.

**Coexistence period length:** Short coexistence (1–2 weeks) gets to a single source of truth quickly but risks the Lightning replacement having undiscovered bugs. Long coexistence (1–6 months) is safer but accumulates dual-management overhead. Tradeoff: shorter requires confidence in the migration testing; longer requires discipline to actually retire the Classic version. The right length depends on the action's criticality and the team's ability to monitor adoption.

**Custom Permissions vs profile-based action visibility:** Custom Permissions in Quick Action visibility rules are stable and assignable via Permission Sets. Profile-based logic is more direct but brittle. Same tradeoff as Dynamic Forms — Custom Permissions are the well-architected default for any non-trivial visibility logic.

## Anti-Patterns

1. **Direct JavaScript-to-LWC translation.** The button's JavaScript was written for Classic's runtime; LWC's runtime is fundamentally different (LWS sandboxing, no global DOM, no `sforce.*` namespace). Translation produces broken code; re-architecture produces working code. Identify the user-facing intent and rebuild on the right Lightning surface.

2. **Removing the Classic button without a coexistence period.** Breaks Classic users immediately. Coexistence is mandatory if any Classic users remain; instrumenting both surfaces with adoption tracking provides the trigger for retirement. Without coexistence, the migration becomes an outage.

3. **Ignoring the 200-record Mass Action limit.** Silently processing only the first 200 records is the worst possible UX — the user sees no error and assumes the action worked. Always handle larger collections explicitly: either chunk with progress reporting, or kick off async processing with a clear "started" message.

4. **Treating S-Controls as having a migration path.** S-Controls are fully retired and have no conversion path. Rebuild from scratch on a supported surface. Trying to preserve S-Control content brings outdated security patterns into modern code.

5. **Skipping Salesforce Mobile App testing.** Mobile is a separate surface with subset support for Quick Action types. Untested actions may render as drawers, fail to invoke, or have degraded UX on mobile. Test on real devices.

6. **Using `alert()` and `confirm()` in LWC.** May work in LWS-disabled orgs but blocked in LWS (the modern default). Use `LightningConfirm` and `ShowToastEvent` for portable, supported user feedback.

7. **Returning `PageReference` from `@AuraEnabled` Apex called by LWC.** Apex returns data; LWC navigates. The `PageReference` return is silently ignored and the user is stuck on the original page. Always have the LWC explicitly invoke `NavigationMixin.Navigate` after the call resolves.

## Official Sources Used

- Custom Buttons and Links Overview — https://help.salesforce.com/s/articleView?id=sf.customize_examplecustombuttons.htm
- Lightning Quick Actions — https://help.salesforce.com/s/articleView?id=sf.actions_overview.htm
- Headless LWC Quick Actions — https://developer.salesforce.com/docs/platform/lwc/guide/use-quick-actions.html
- LWC Mass Quick Actions — https://developer.salesforce.com/docs/platform/lwc/guide/use-quick-actions-mass.html
- Lightning Message Service — https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel.html
- NavigationMixin — https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate.html
- Lightning Web Security — https://developer.salesforce.com/docs/platform/lwc/guide/security-lwsec-intro.html
- Salesforce Mobile App Quick Actions — https://help.salesforce.com/s/articleView?id=sf.actions_in_salesforce_mobile.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
