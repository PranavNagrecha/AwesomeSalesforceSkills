# Well-Architected Notes — LWC Mobile Offline and Briefcase

## Relevant Pillars

- **Reliability** — Offline UX is reliability work. The LWC must continue functioning when the network is partially or fully unavailable, and queued user input must reach the server eventually with predictable conflict semantics. Most "the app broke offline" tickets come from imperative Apex calls failing without a fallback path or from queued writes silently failing on reconnect — both are reliability failures, not feature gaps. Treat offline as a first-class reliability target with explicit test coverage (airplane-mode runs, force-quit cycles, reconnect with stale-data scenarios), not an afterthought.

- **Performance Efficiency** — Briefcase priming volume directly trades against sync time, device storage, and battery. Over-priming (rules that select tens of thousands of records per user, or include large blob fields) creates 5+ minute syncs that consume the user's start-of-shift productivity window. Under-priming creates "data not available offline" surprises that block work entirely. The art is in scoping the rule so the per-user record count stays well below the published soft limits while still covering the realistic-day workflow. Re-evaluate quarterly as data grows.

## Architectural Tradeoffs

| Tradeoff | Why it matters |
|---|---|
| Briefcase priming vs LDS-cache-only | Briefcase is deterministic ("these records will be on the device") but costs sync time and storage. LDS recently-viewed cache is free but only covers records the user happened to open. Use Briefcase for any offline window > 1 hour or any "must be available" record set; use LDS-cache-only for short-window read-mostly UX. |
| LDS reads vs imperative Apex | LDS is offline-aware out of the box; imperative Apex is online-only unless you build the offline path manually. Whenever a value can be expressed as a field-on-record (even via a roll-up summary or formula), prefer LDS — the offline experience is essentially free. Imperative Apex should be reserved for genuinely uncacheable computations (external system calls, complex aggregations across orgs, etc.) and always paired with explicit offline error handling. |
| Last-write-wins vs conflict detection | Last-write-wins is the platform default and the only zero-cost option. Conflict detection requires a custom Apex layer with timestamp comparison and a UX for the conflict-resolution screen — significant build cost. Use it only for high-stakes records where silent overwrite is unacceptable (regulated industries, financial data, anything with audit obligations). For most CRM use cases, last-write-wins is acceptable if rollout training mentions it. |
| Single-record-type forms vs full picker | An offline-create flow that hard-codes a single record-type-id always works. A flow that lets the user pick from multiple record types depends on metadata cache being warm, which is opportunistic. If multi-record-type creation is essential, accept that the first offline use after install will fail and design rollout / training around it. |
| Long-lived `localStorage` drafts vs server-side draft API | `localStorage` drafts are fast to build but unencrypted, browser-scoped, and prone to loss on app reinstall or sign-out. A server-side draft API (custom object + Apex endpoint) survives device changes and respects FLS, but costs more to build and reduces the offline-only window (each draft save needs network). Choose based on data sensitivity. |
| Pre-warming metadata cache vs pure offline-first design | Pre-warming (hidden component that calls `getPicklistValues` on app launch) is a small ongoing tax but turns offline picklist failures into a one-time online setup. Pure offline-first design avoids the dependency by sourcing dropdown content from CMT records or hard-coded lists in code, but limits flexibility. |

## Anti-Patterns

1. **Designing offline UX without an airplane-mode test loop** — Reading the Briefcase docs, configuring a rule, and shipping without testing on a real device with airplane mode enabled produces "works on my desk" code that breaks at the first reconnect. Every offline-aware LWC needs a documented airplane-mode test plan, run on a real device (simulators do not faithfully reproduce mobile-app offline behavior).
2. **Briefcase rules that exceed per-user soft limits "just in case"** — Priming everything-the-user-might-conceivably-need creates 5-minute syncs and storage pressure on older devices. Start with the smallest viable rule, measure actual offline access patterns, and expand only when concrete usage justifies it.
3. **Imperative Apex with no offline path** — A `getStuff` call that throws on offline and is caught by a generic `.catch((err) => { this.error = err; })` produces a "something went wrong" UX that the user can't act on. Either rewrite the path through LDS or branch explicitly on offline state with a meaningful empty-state message.
4. **Treating the bell-icon "Pending Issues" surface as the sole error UI** — End users do not check Pending Issues. If a sync failure matters (validation rule rejection, permission error), the LWC should surface the failure prominently in a "My Pending Submissions" view, ideally with a re-edit/retry path.
5. **Confusing Briefcase Builder with FSL Mobile offline priming** — These are completely separate offline pipelines targeting different mobile apps. Configuring Briefcase has no effect on FSL Mobile, and vice versa. Confirm which app the user population uses before designing.
6. **Trusting `navigator.onLine` for correctness** — `navigator.onLine` is `true` on captive-portal Wi-Fi, on networks where Salesforce hosts are unreachable, and during connecting/disconnecting transitions. Use it for UX hints; use actual network call results for correctness decisions.

## Official Sources Used

- Salesforce Help — Briefcase Builder Overview — https://help.salesforce.com/s/articleView?id=sf.briefcase_builder_overview.htm
- Salesforce Help — Configure Offline Mode for the Salesforce Mobile App — https://help.salesforce.com/s/articleView?id=sf.salesforce_app_offline_setup.htm
- Salesforce Developers — Salesforce Mobile App Offline Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_offline_dev_guide.meta/salesforce_app_offline_dev_guide/
- Salesforce Developers — LWC Use Configuration via `@salesforce/client/formFactor` and userinfo modules — https://developer.salesforce.com/docs/platform/lwc/guide/use-config-userinfo.html
- Salesforce Developers — LWC Use Lightning Data Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-ui-api.html
- Salesforce Architects — Well-Architected Reliable Pillar — https://architect.salesforce.com/well-architected/trusted/reliable
- Salesforce Architects — Well-Architected Performance Pillar — https://architect.salesforce.com/well-architected/adaptable/resilient
