# Well-Architected Notes — Lightning Experience Transition

## Relevant Pillars

- **User Experience** — A Classic-to-LEX transition is the most visible UI change a Salesforce org will ever undergo. The program's success criteria are about minimizing user-experience disruption while moving every user onto a more adaptable runtime. Sequencing waves, retaining rollback paths, and triaging assets so users land on a working LEX page (not a broken JS button) are all UX-driven decisions.
- **Operational Excellence** — Wave-based rollout, telemetry-gated promotion (`LightningExitByPageMetrics`), explicit rollback triggers, and audit-log capture are the operational hallmarks of a controlled migration. The alternative (flip the org-wide switch and deal with what breaks) is the operations-cost antipattern.
- **Reliability** — Per-cohort permission-set rollout protects production from a single-point change failure: if Wave 1 surfaces a Sev-1, Waves 2+ are still on Classic and the impact is contained. Reliability comes from blast-radius control, not from skipping the migration.

## Architectural Tradeoffs

- **Speed vs blast-radius control.** A single-wave flip is faster on the calendar but exposes every triage miss simultaneously. Multi-wave is slower but contains failure to one cohort at a time. The tradeoff threshold is roughly user count × asset complexity: low-complexity orgs can afford single-wave, high-complexity orgs cannot.
- **Replace vs Rebuild for legacy assets.** A 1:1 Replace ships faster but carries forward Classic-era UX into LEX (a Quick Action that mimics a JavaScript button line-for-line). A Rebuild is slower but leverages Lightning-native primitives (LWC + flow + Apex action) and produces a more maintainable asset. Replace for low-traffic assets; Rebuild for assets the cohort uses every day.
- **Org-wide flip vs permission-set cutover.** The org-wide setting (`enableLexEndUsersNoSwitching` / `enableUsersAreLightningOnly`, api_meta 264 L124742-124756, L124831-124835) affects every user at once; UNVERIFIED (2026-10-20): that it is a one-way door. The switcher-hiding permission set is reversible per cohort (UNVERIFIED (2026-10-20): permission name) — un-assign it if a Sev-1 surfaces. Prefer the permission-set cutover path; only flip the org-wide setting after 14+ days of stable LEX-only telemetry.
- **Asset-level skill citation vs program-level orchestration.** This skill explicitly does not duplicate the asset-level skills (`lwc/visualforce-to-lwc-migration`, `admin/custom-button-to-action-migration`, `admin/knowledge-classic-to-lightning`). It cites them. The tradeoff is that the program plan must list which asset-level skill applies to each Replace/Rebuild row, rather than re-explaining the asset-level mechanics.

## Anti-Patterns

1. **Org-wide LEX flip as the first action.** Predictably surfaces every triage miss simultaneously. Use permission-set-driven waves and reserve the org-wide flip for cutover after telemetry stabilizes.
2. **"Migrate everything" instead of triage.** Treating the Readiness Check as a backlog rather than an input. Cross-reference with usage data; retire dead assets before rebuilding them.
3. **Trusting the AppExchange "Lightning Ready" badge as production-equivalent.** Validate the workflows the cohort uses against the package in a LEX sandbox; the badge means "renders without breaking," not "every feature is parity" (UNVERIFIED (2026-10-20): badge semantics are Help-only).
4. **Ignoring the per-user `UserPreferencesLightningExperiencePreferred` flag.** A profile-level rollout silently lies about adoption if users have a sticky Classic preference (UNVERIFIED (2026-10-20): precedence is Help-only). Reset it by DML — the field is updateable (obj 264 L299363-299369) — or hide the switcher.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — used for the Adaptable / Operational Excellence / Reliability framing and the wave-based rollout vs single-flip tradeoff
- Lightning Experience Transition Assistant (Help) — https://help.salesforce.com/s/articleView?id=sf.lex_transition_assistant.htm — primary source for Readiness Check mechanics and the Discover/Roll Out/Optimize phases
- Object Reference — `LightningUsageByAppTypeMetrics`, `LightningUsageByPageMetrics`, `LightningExitByPageMetrics` (fields; "Not available in sandbox orgs") — obj 264 L170377-170670; `User.UserPreferencesLightningExperiencePreferred` — L299363-299369
- Metadata API — `WebLink` `linkType` / `openType` (JavaScript-button audit) — api_meta 264 L47926-47944; `LightningExperienceSettings` Classic-off switches — L124742-124756, L124831-124835; `CustomApplication.uiType` Aloha/Lightning — L41933-41937
