# Well-Architected Notes — Custom Button to Action Migration

## Relevant Pillars

- **User Experience** — Lightning Quick Actions, Screen Flows, and LWC Quick Actions provide consistent UX patterns across the org: action bar placement, mobile parity, accessible focus management, predictable spinner / toast feedback. Classic JavaScript buttons varied wildly in look and feel — some used `alert()`, some used custom popups, some did inline DOM manipulation. Migration normalizes the action surface, making the org feel cohesive and reducing per-action user training.

- **Operational Excellence** — JavaScript buttons need a rebuild for Lightning Experience (UNVERIFIED (2026-10-20): that they are unsupported and silently render as nothing is Help-only). The org may accumulate "ghost" Page Layout entries that admins forget about. Migrating to supported Lightning action types removes a class of silent failures and aligns the action surface with the platform's supported, evolving APIs (Lightning Confirm, Toast Events, NavigationMixin, Lightning Message Service). Each migrated action becomes maintainable through Setup or LWC source rather than free-form HTML/JS in a button definition.

- **Security** — Classic JavaScript buttons could call `sforce.connection.update()` to perform DML directly from the browser without going through Apex sharing rules — a subtle but real security gap if the user had API access but the Apex layer was the intended security boundary (UNVERIFIED (2026-10-20): the AJAX Toolkit's behaviour is not in the corpus). Lightning Quick Actions force traffic through `@AuraEnabled` Apex methods that explicitly declare `with sharing` and FLS enforcement — `WITH USER_MODE` on reads (in API 67.0 and later you can't use `WITH SECURITY_ENFORCED`, apexdev 264 L11926-11927; UNVERIFIED (2026-10-20): the 57.0 floor for `WITH USER_MODE` is a Help release-note figure), plus `Security.stripInaccessible(AccessType, records).getRecords()` on write paths that assemble records from user input. The migration is the moment to verify that security is enforced at the Apex layer, not assumed at the UI layer.

## Architectural Tradeoffs

**Headless LWC vs Screen Flow for one-click actions:** Headless LWC provides the lowest-friction UX (one click, toast, done). Screen Flow adds a confirmation screen and can be configured by admins without code. Tradeoff: Headless LWC requires developer effort but produces a snappier UX; Screen Flow is admin-maintainable at the cost of an extra click. For high-frequency actions, Headless LWC; for occasional or admin-tunable actions, Screen Flow.

**Apex-backed list-view action vs invocable Apex from Flow:** An Apex-backed action returns per-record results to whatever UI hosts it; invocable Apex from a Flow is admin-configurable and supports complex business logic without code. Tradeoff: Apex for control and partial-success reporting, Flow for admin maintainability. An LWC quick action cannot be the host because it runs on record pages only (LWC guide `use-config-for-quick-actions`); a mass quick action is limited to create or update actions (api_meta 264 L47565-47572), so the surface that hands a selection to Apex is UNVERIFIED (2026-10-20) (Help-only).

**Coexistence period length:** Short coexistence (1–2 weeks) gets to a single source of truth quickly but risks the Lightning replacement having undiscovered bugs. Long coexistence (1–6 months) is safer but accumulates dual-management overhead. Tradeoff: shorter requires confidence in the migration testing; longer requires discipline to actually retire the Classic version. The right length depends on the action's criticality and the team's ability to monitor adoption.

**Custom Permissions vs profile-based action visibility:** Custom Permissions in Quick Action visibility rules are stable and assignable via Permission Sets. Profile-based logic is more direct but brittle. Same tradeoff as Dynamic Forms — Custom Permissions are the well-architected default for any non-trivial visibility logic.

## Anti-Patterns

1. **Direct JavaScript-to-LWC translation.** The button's JavaScript was written for Classic's runtime; LWC's runtime is fundamentally different (components query only their own template and not `window`/`document`, LWC guide `create-components-dom-work`; no `sforce.*` namespace). Translation produces broken code; re-architecture produces working code. Identify the user-facing intent and rebuild on the right Lightning surface.

2. **Removing the Classic button without a coexistence period.** Breaks Classic users immediately. Coexistence is mandatory if any Classic users remain; instrumenting both surfaces with adoption tracking provides the trigger for retirement. Without coexistence, the migration becomes an outage.

3. **Ignoring the Mass Action selection cap.** If selections are capped (UNVERIFIED (2026-10-20): 200 is a Help-only figure), silently processing only the first 200 records is the worst possible UX — the user sees no error and assumes the action worked. Always handle larger collections explicitly: either chunk with progress reporting, or kick off async processing with a clear "started" message.

4. **Treating S-Controls as having a migration path.** S-controls are deprecated (api_meta 264 L45109-45110) and have no conversion path. Rebuild from scratch on a supported surface. Trying to preserve S-Control content brings outdated security patterns into modern code.

5. **Skipping Salesforce Mobile App testing.** Mobile is a separate surface, and LWC quick actions are not supported in the mobile app (LWC guide `use-config-for-quick-actions`). Untested actions may fail to invoke or have degraded UX on mobile (UNVERIFIED (2026-10-20): the drawer and subset-support wording is Help-only). Test on real devices.

6. **Using `alert()` and `confirm()` in LWC.** `window.confirm()` isn't supported for cross-origin iframes in Chrome and Safari (LWC guide `use-dialog-confirm`). Use `LightningConfirm` and `ShowToastEvent` for portable, supported user feedback.

7. **Returning `PageReference` from `@AuraEnabled` Apex called by LWC.** Apex returns data; LWC navigates. The `PageReference` return is silently ignored and the user is stuck on the original page (UNVERIFIED (2026-10-20): the ignored-return behaviour is Help-only). Always have the LWC explicitly invoke `NavigationMixin.Navigate` after the call resolves.

## Official Sources Used

- Custom Buttons and Links Overview — https://help.salesforce.com/s/articleView?id=sf.customize_examplecustombuttons.htm
- Lightning Quick Actions — https://help.salesforce.com/s/articleView?id=sf.actions_overview.htm
- Headless LWC Quick Actions — https://developer.salesforce.com/docs/platform/lwc/guide/use-quick-actions.html
- Lightning Message Service — https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel.html
- NavigationMixin — https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate.html
- Salesforce Mobile App Quick Actions — https://help.salesforce.com/s/articleView?id=sf.actions_in_salesforce_mobile.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- WebLink fields (`displayType`, `linkType` values, `url` holds the JavaScript): api_meta 264 L47857-47860, L47926-47932, L47984-47986; the WebLink sObject supports `query()`: object_reference 264 L314753-314755
- QuickAction `type` values (no URL value; Flow is Beta as of 41.0; LightningComponent 38.0+): api_meta 264 L102947-102971
- S-controls deprecated since Spring '09: api_meta 264 L45109-45110; `Scontrol` type marked Deprecated: L109760-109761
- LWC quick actions: record pages only, `actionType`, not supported in the mobile app: LWC guide `use-config-for-quick-actions`; headless `invoke()` and `recordId`: `use-quick-actions-headless`
- `LightningConfirm` vs `window.confirm()`: LWC guide `use-dialog-confirm`; `RefreshEvent` from `lightning/refresh`: `data-refreshview-api`; `standard__webPage`: `reference-page-reference-type`
- `WITH SECURITY_ENFORCED` cannot be used at API 67.0 and later: apexdev 264 L11926-11927
- Mass quick actions (an existing create or update action, Lightning Experience) and list-view buttons: api_meta 264 L47565-47572, L47523-47526. The `use-quick-actions-mass.html` page an earlier list cited returns 404 and is removed; a selection reaching Apex or a Flow is UNVERIFIED (2026-10-20)
- The WITH SECURITY_ENFORCED SOQL Clause Is Removed (Summer '26 / API 67.0) — https://help.salesforce.com/s/articleView?id=release-notes.rn_apex_removed_withSecurityEnforced.htm&type=5 — grounds the version qualifier on the Security pillar note above
- Secure Apex Code with User Mode Database Operations (Generally Available) (Spring '23 / API 57.0) — https://help.salesforce.com/s/articleView?id=release-notes.rn_apex_User_Mode_GA.htm&type=5 — UNVERIFIED (2026-10-20): Help-only; the only source for the 57.0 floor
