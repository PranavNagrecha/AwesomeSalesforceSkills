# Well-Architected Notes — Knowledge Classic to Lightning Migration

## Relevant Pillars

- **User Experience** — Lightning Knowledge surfaces inside the Lightning Service Console with native components: Knowledge Component on the Case page, inline article search, drag-to-attach behavior, and Einstein-powered article suggestions. Classic Knowledge required separate Console configuration, the Knowledge Sidebar, and Setup-driven layout management. Migration delivers a consistent UX with the rest of Lightning Experience and unlocks Einstein, Service Cloud Voice integration, and modern Communities article display.

- **Operational Excellence** — Classic Knowledge's per-Article-Type sObject model produced a sprawling administrative surface: per-type layouts, per-type validation rules, per-type reports, per-type approval processes. Lightning Knowledge consolidates to a single `Knowledge__kav` with record types, simplifying ongoing administration. New Knowledge features (search relevance tuning, Einstein article recommendations, multi-language enhancements) ship for Lightning only. Staying on Classic accumulates technical debt that compounds with every release cycle — and that debt is now formally recognized by the vendor: Salesforce lists *Classic Knowledge Data Model End of Support* with a retirement date of March 1, 2026. Operational excellence here means retiring an unsupported surface, not opportunistically adopting a newer one.

- **Reliability** — A Knowledge migration touches articles (the org's authoritative documentation), translations, downstream consumers (agents, communities, public KB), and integrations (bots, scheduled jobs). The Salesforce Migration Tool provides a tested, supported path that handles version history, translation linkage, publication state, and data category visibility. Building custom migration code for a standard Knowledge structure introduces risk without payoff. Reliability comes from preferring the Tool, validating exhaustively in sandbox, and phasing the channel cutover (Internal → Communities → Public) so each step has a rollback window. Salesforce codifies part of this discipline as a precondition: production enablement of the Tool requires a Support case carrying evidence of a validated migration in a full copy sandbox refreshed within the last month, on the same release as production, with a confirmed backup. The requirements are, in effect, a reliability checklist the vendor enforces on your behalf.

## Architectural Tradeoffs

**Migration timing:** There is no longer a "defer" branch to trade off. With Classic Knowledge's data model past its March 1, 2026 End of Support date, the tradeoff space is bounded by *how* and *how fast*, not *whether*. What deferral still buys is real but small: fewer concurrent changes, more time to rationalize Article Types. What it costs is an org running on a data model Salesforce no longer commits to, on a runway whose length the org does not control. Scope the migration to the smallest safe change (preserve categories, preserve the Article Type taxonomy unless redundancy is obvious) rather than deferring the whole program to accommodate a rationalization project.

**Migration Tool vs custom code:** The Migration Tool handles 90% of cases and is the supported path. Custom code is needed when: source fields must be merged or renamed before migration, Article Types are being consolidated, or non-standard publishing workflows must be preserved. Tradeoff: custom code provides flexibility but introduces failure modes (translation linkage, publishing service, channel flag preservation) that the Tool handles correctly by default. Recommendation: pre-process in Classic via Apex (renames, field unification), then run the Tool. Avoid full-custom migration unless the Tool is structurally insufficient.

**Article Type consolidation vs 1:1 record type mapping:** Migration is the rare opportunity to rationalize the Article Type taxonomy. An org with 12 Article Types — many barely used or overlapping — benefits from consolidation to 4–5 record types. The cost: more decision-making upfront, more field-mapping conflicts to resolve, more downstream code that must be aware of the new structure. The benefit: simpler reports, simpler approval workflows, easier onboarding for new admins. Default: consolidate when redundancy is obvious (e.g., "FAQ" and "Q_and_A"); preserve 1:1 when each Article Type has clear distinct ownership.

**Channel cutover sequencing:** Phased (Internal → Communities → Public) preserves rollback at each step but extends the dual-state window (where both Classic and Lightning serve different channels). Big-bang (all channels at once) is faster to "done" but if anything fails, every channel breaks together. For most orgs the phased approach is correct — the public-facing channel is the highest-risk surface and must be the last cutover.

**Retain Classic Article Types vs decommission:** Post-migration, Classic Article Types can remain as read-only "audit shadow" or be dropped entirely. Retention preserves an inspection path for auditors comparing pre/post content; decommissioning eliminates the dual-store ambiguity and reclaims storage. Default: retain for 90 days post-cutover; decommission after a documented soak with verified zero-reference status from any code or integration.

**Data category re-architecture during migration:** The migration is also a chance to reconsider data category structure (groups, hierarchies, visibility). Restructuring during migration is efficient (one disruption window instead of two) but adds scope risk. Default: preserve categories during migration to limit blast radius; address category restructuring as a separate post-migration project.

## Anti-Patterns

1. **Production-first migration without sandbox proof.** Lightning Knowledge enablement is irreversible without article deletion. A "let's just try it" production enablement cannot be undone. Sandbox validation is mandatory; treat the production cutover as a one-way door.

2. **Custom migration code when the Tool would work.** The Salesforce Migration Tool is more reliable than custom code for standard Knowledge structures. Custom code introduces failure modes (translation orphans, channel flag drops, publication-state mishandling) that the Tool handles correctly. Default to the Tool; build custom only when structurally required.

3. **Skipping the data category visibility audit post-migration.** Lightning Knowledge introduces record-type-based visibility on top of category visibility. Users who saw articles via category alone may lose access if they lack record-type read permissions. Audit visibility per role with `System.runAs` regression tests; correct any restrictive impact via permission set updates.

4. **Decommissioning Classic Article Types immediately after migration.** Classic sObjects (`FAQ__kav`, `HowTo__kav`) become inaccessible once Knowledge is fully decommissioned. Apex, Quick Actions, reports, and integrations that reference them break. Decommission only after a soak window with confirmed zero references — the "no false positives" rule applies here too.

5. **Treating channel cutover as a single event.** Migrating all channels at once removes rollback options. The Public Knowledge Base in particular is a customer-facing surface where a broken article render is highly visible; cut it last after Internal and Communities have proven stable.

6. **Not recreating approval processes on `Knowledge__kav`.** Approval processes attached to Classic Article Type sObjects do not auto-port. Recreate per record type with appropriate entry criteria. Without this, draft articles cannot be submitted for publishing — the entire editorial workflow is broken silently until someone tries to publish.

7. **Treating the migration as discretionary roadmap work.** Classic Knowledge's data model carries an End of Support retirement date of March 1, 2026. Business cases that weigh migration against "keep Classic" are evaluating an option the vendor has withdrawn. Scope and sequence the work; do not re-litigate it.

8. **Scheduling the production run before Salesforce Support has enabled the Tool.** Production enablement requires a case, a readiness questionnaire, sandbox Validation-step evidence from a recently refreshed full copy sandbox, a confirmed backup, and release alignment between sandbox and production. Salesforce states processing can take up to a week. A change window booked on the assumption that production behaves like sandbox will be forfeited.

## Official Sources Used

- Lightning Knowledge Migration Tool — https://help.salesforce.com/s/articleView?id=sf.knowledge_migration_tool.htm
- Requirements to Enable Lightning Knowledge Migration Tool (production enablement case, readiness questionnaire, full copy sandbox, same-release rule) — https://help.salesforce.com/s/articleView?id=000382103&language=en_US&type=1
- Salesforce Past Product & Feature Retirements (states the entry *Classic Knowledge Data Model End of Support* and the retirement date March 1, 2026 — it does not define End of Support; links detail article id `005239564`) — https://help.salesforce.com/s/articleView?id=005132112&language=en_US&type=1
- Lightning Knowledge User Access (internal users can read articles by default; the Knowledge User license is required to do more than read) — https://help.salesforce.com/s/articleView?id=service.knowledge_setup_users_lex.htm&language=en_US&type=5
- Set Access for Lightning Knowledge (Manage Articles / Publish Articles app permissions; Manage Data Categories system permission — this unit does not discuss feature licenses) — https://trailhead.salesforce.com/content/learn/projects/set-up-salesforce-knowledge/set-access-for-lightning-knowledge
- Lightning Knowledge Overview — https://help.salesforce.com/s/articleView?id=sf.knowledge_lightning.htm
- Standard Objects list (confirms no `KnowledgeArticleType`, `CategoryGroup`, or `Category` standard object exists) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_list.htm
- ArticleType (Metadata API) — Classic Article Types are metadata, not a queryable sObject — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_articletype.htm
- DataCategoryGroup (Metadata API) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_datacategorygroup.htm
- describeDataCategoryGroups() / describeDataCategoryGroupStructures() — the supported way to enumerate Data Category Groups — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_describedatacategorygroups.htm
- Knowledge__kav sObject Reference — https://developer.salesforce.com/docs/atlas.en-us.knowledge_dev.meta/knowledge_dev/sforce_api_objects_knowledge__kav.htm
- KbManagement.PublishingService — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_KbManagement_PublishingService.htm
- Knowledge Translation — https://help.salesforce.com/s/articleView?id=sf.knowledge_multilingual_overview.htm
- Knowledge Data Categories — https://help.salesforce.com/s/articleView?id=sf.category_overview.htm
- Knowledge Channel Visibility — https://help.salesforce.com/s/articleView?id=sf.knowledge_articles_channels.htm
- Service Console Knowledge Component — https://help.salesforce.com/s/articleView?id=sf.console2_knowledge_component.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
