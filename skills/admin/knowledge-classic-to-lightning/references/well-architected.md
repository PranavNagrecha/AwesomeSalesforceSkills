# Well-Architected Notes — Knowledge Classic to Lightning Migration

## Relevant Pillars

- **User Experience** — Lightning Knowledge surfaces inside the Lightning Service Console with native components: Knowledge Component on the Case page, inline article search, drag-to-attach behavior, and Einstein-powered article suggestions. Classic Knowledge required separate Console configuration, the Knowledge Sidebar, and Setup-driven layout management. Migration delivers a consistent UX with the rest of Lightning Experience and unlocks Einstein, Service Cloud Voice integration, and modern Communities article display. UNVERIFIED (2026-10-20): these Service Console and component capabilities are Help-only.

- **Operational Excellence** — Classic Knowledge's per-Article-Type sObject model produced a sprawling administrative surface: per-type layouts, per-type validation rules, per-type reports, per-type approval processes. Lightning Knowledge consolidates to a single `Knowledge__kav` with record types, simplifying ongoing administration. New Knowledge features ship for Lightning only (UNVERIFIED (2026-10-20): Help-only; the corpus does show Lightning-only Knowledge metadata such as `ConversationRecordLookup`, api_meta 264 L31937). Staying on Classic accumulates technical debt that compounds with every release cycle.

- **Reliability** — A Knowledge migration touches articles (the org's authoritative documentation), translations, downstream consumers (agents, communities, public KB), and integrations (bots, scheduled jobs). The Salesforce Migration Tool provides a supported path for version history, translation linkage, publication state, and data category visibility (UNVERIFIED (2026-10-20): Tool behaviour is Help-only). Building custom migration code for a standard Knowledge structure introduces risk without payoff. Reliability comes from preferring the Tool, validating exhaustively in sandbox, and phasing the channel cutover (Internal → Communities → Public) so each step has a rollback window.

## Architectural Tradeoffs

**Migration Tool vs custom code:** The Migration Tool is the supported path (UNVERIFIED (2026-10-20): any coverage percentage). Custom code is needed when: source fields must be merged or renamed before migration, Article Types are being consolidated, or non-standard publishing workflows must be preserved. Tradeoff: custom code provides flexibility but introduces failure modes (translation linkage, publishing service, channel flag preservation) that the Tool handles correctly by default. Recommendation: pre-process in Classic via Apex (renames, field unification), then run the Tool. Avoid full-custom migration unless the Tool is structurally insufficient.

**Article Type consolidation vs 1:1 record type mapping:** Migration is the rare opportunity to rationalize the Article Type taxonomy. An org with 12 Article Types — many barely used or overlapping — benefits from consolidation to 4–5 record types. The cost: more decision-making upfront, more field-mapping conflicts to resolve, more downstream code that must be aware of the new structure. The benefit: simpler reports, simpler approval workflows, easier onboarding for new admins. Default: consolidate when redundancy is obvious (e.g., "FAQ" and "Q_and_A"); preserve 1:1 when each Article Type has clear distinct ownership.

**Channel cutover sequencing:** Phased (Internal → Communities → Public) limits the blast radius per surface; it is not a Classic/Lightning dual state, because a multi-type migration deletes the article-type KAV objects (apexdev 264 L16013-16014). Big-bang (all channels at once) is faster to "done" but if anything fails, every channel breaks together. For most orgs the phased approach is correct — the public-facing channel is the highest-risk surface and must be the last cutover.

**Export Classic Article Types before migrating:** In a multi-type org the article-type KAV objects "are deleted during migration" (apexdev 264 L16013-16014), so there is no post-migration "audit shadow". Export what auditors need first, and use `MigratedToFromArticleVersion` / `MigratedToFromArticle` to join old and new IDs (obj 264 L162069-162076, L161733-161735).

**Data category re-architecture during migration:** The migration is also a chance to reconsider data category structure (groups, hierarchies, visibility). Restructuring during migration is efficient (one disruption window instead of two) but adds scope risk. Default: preserve categories during migration to limit blast radius; address category restructuring as a separate post-migration project.

## Anti-Patterns

1. **Production-first migration without sandbox proof.** Lightning Knowledge enablement is treated as irreversible without article deletion (UNVERIFIED (2026-10-20): Help-only). A "let's just try it" production enablement cannot be undone. Sandbox validation is mandatory; treat the production cutover as a one-way door.

2. **Custom migration code when the Tool would work.** The Salesforce Migration Tool is more reliable than custom code for standard Knowledge structures. Custom code introduces failure modes (translation orphans, channel flag drops, publication-state mishandling) that the Tool handles correctly. Default to the Tool; build custom only when structurally required.

3. **Skipping the data category visibility audit post-migration.** Category selections are visible per role, permission set or profile (obj 264 L38783-38784 — the Classic `<ArticleType>__DataCategorySelection` page, "not available in Lightning Knowledge"; Lightning metadata sets it per profile through `categoryGroupVisibilities`, api_meta 264 L100293-100295); record types are not a read gate (secguide 262 L1295-1297). Audit visibility per role with `System.runAs` regression tests against the pre-migration baseline.

4. **Leaving article-type references in code until after migration.** Classic sObjects (`FAQ__kav`, `HowTo__kav`) are deleted during a multi-type migration, and triggers on them block it (apexdev 264 L16011-16014). Apex, Quick Actions, reports, and integrations that reference them break. Clear every reference before the Tool runs.

5. **Treating channel cutover as a single event.** Migrating all channels at once removes rollback options. The Public Knowledge Base in particular is a customer-facing surface where a broken article render is highly visible; cut it last after Internal and Communities have proven stable.

6. **Not recreating approval processes on `Knowledge__kav`.** Approval processes attached to Classic Article Type sObjects do not auto-port (UNVERIFIED (2026-10-20): Help-only). Recreate per record type with appropriate entry criteria. Without this, draft articles cannot be submitted for publishing — the entire editorial workflow is broken silently until someone tries to publish.

## Official Sources Used

- Apex Developer Guide — article-type KAV objects deleted during migration; remove triggers first — apexdev 264 L16010-16016
- Object Reference — `Knowledge__kav` fields: `PublishStatus` (no Create/Update), `IsVisibleIn*`, `IsMasterLanguage`, `MasterVersionId`, `MigratedToFromArticleVersion`; record type determines article type — obj 264 L161747-162124, L163386-163388
- Security Implementation Guide — users can view records of any record type — secguide 262 L1295-1297
- Apex Reference — `KbManagement.PublishingService` `publishArticle` / `editOnlineArticle` — apexref 262 L163220-163289
- Lightning Knowledge Migration Tool — https://help.salesforce.com/s/articleView?id=sf.knowledge_migration_tool.htm
- Lightning Knowledge Overview — https://help.salesforce.com/s/articleView?id=sf.knowledge_lightning.htm
- Knowledge__kav sObject Reference — https://developer.salesforce.com/docs/atlas.en-us.knowledge_dev.meta/knowledge_dev/sforce_api_objects_knowledge__kav.htm
- KbManagement.PublishingService — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_KbManagement_PublishingService.htm
- Knowledge Translation — https://help.salesforce.com/s/articleView?id=sf.knowledge_multilingual_overview.htm
- Knowledge Data Categories — https://help.salesforce.com/s/articleView?id=sf.category_overview.htm
- Knowledge Channel Visibility — https://help.salesforce.com/s/articleView?id=sf.knowledge_articles_channels.htm
- Service Console Knowledge Component — https://help.salesforce.com/s/articleView?id=sf.console2_knowledge_component.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
