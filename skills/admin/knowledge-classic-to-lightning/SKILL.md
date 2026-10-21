---
name: knowledge-classic-to-lightning
description: "Migrating Classic Knowledge (KnowledgeArticleVersion / Article Types) to Lightning Knowledge (Knowledge__kav with record types): article-type-to-record-type mapping, multi-language translation preservation, data category re-architecture, file attachment porting, version and publication-state retention, channel visibility translation, and downstream Case Feed / Community / Bot rewiring. NOT for new Lightning Knowledge setup or editorial publishing workflow design (use admin/knowledge-base-administration)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Reliability
triggers:
  - "How do I migrate Classic Knowledge articles to Lightning Knowledge?"
  - "Convert multiple Article Types to a single Knowledge__kav with record types"
  - "Preserve translations and version history across the Knowledge migration"
  - "Data categories before and after Lightning Knowledge migration"
  - "Salesforce-provided Lightning Knowledge Migration Tool — when to use vs custom"
tags:
  - knowledge
  - lightning-knowledge
  - article-types
  - record-types
  - data-categories
  - migration
  - multilingual
inputs:
  - "Classic Knowledge enabled status; current Article Types (count, fields, layouts)"
  - "Active translation languages and per-language article counts"
  - "Data category groups, hierarchies, and visibility settings"
  - "Channel exposure: Internal, Customer (Communities), Partner, Public Knowledge Base"
  - "Downstream consumers: Case Feed Knowledge Component, Knowledge Sidebar, Communities, Einstein Bots, Service Setup Assistant"
  - "Whether the Salesforce-provided Lightning Knowledge Migration Tool will be used (recommended) vs a fully custom path"
outputs:
  - "Lightning Knowledge enabled with `Knowledge__kav` record types corresponding to old Article Types"
  - "Migrated articles preserving version history, translations, publication state, and data categories"
  - "Updated Quick Actions, Case Feed Knowledge Component config, Community pages, and Einstein Bot Knowledge action references"
  - "Migration audit log mapping Classic article ID → Lightning Knowledge__kav ID per language and per version"
  - "Pre-migration export of Classic article types (their KAV objects are deleted during a multi-type migration)"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Knowledge Classic to Lightning Migration

This skill activates when a practitioner needs to migrate from Classic Knowledge (multiple Article Types as separate sObjects) to Lightning Knowledge (a single `Knowledge__kav` sObject with record types), preserving versions, translations, data categories, and downstream consumer integrations.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Classic Knowledge is enabled and inventory Article Types (retrieve the article-type objects; UNVERIFIED (2026-10-20): a queryable `KnowledgeArticleType` object is not in the corpus). In Classic "the concrete derived object uses the prefix of the article type name (for example, FAQ__kav)"; in Lightning "the type of article is determined by the RecordType field" on `Knowledge__kav` (obj 264 L163386-163388), whose `Knowledge` prefix can be renamed in Object Manager (L161753-161754).
- Inventory translations. `SELECT Language, COUNT(Id) FROM KnowledgeArticleVersion WHERE PublishStatus='Online' GROUP BY Language`. Lightning Knowledge supports the same multi-language structure but the migration must port each language version individually.
- Inventory data categories by retrieving `DataCategoryGroup` metadata (api_meta 264 L51372-51400) or calling `describeDataCategoryGroups()` / `describeDataCategoryGroupStructures()` (obj 264 L163382-163384) — there is no `CategoryGroup` sObject to query. Deploying `DataCategoryGroup` between orgs "permanently removes categories and record categorizations that are not specified in your XML file" (api_meta 264 L51376-51377).
- Identify downstream consumers: Case Feed Knowledge Component (Lightning Service Console), Knowledge Sidebar (Classic only; UNVERIFIED (2026-10-20): its deprecation), Community Knowledge pages, Einstein Bot Knowledge action, Salesforce Service Cloud "suggested articles" on Cases, and any Apex code querying article sObjects directly.
- Confirm whether the Salesforce-provided Lightning Knowledge Migration Tool is in scope; custom code is needed only for unusual data category structures, custom field mappings, or article-type consolidation decisions (UNVERIFIED (2026-10-20): any coverage percentage for the Tool).
- Remove Apex triggers on the article-type KAV objects first: "you must remove any Apex triggers that reference the KAV article types", because those objects "are deleted during migration" (apexdev 264 L16011-16014).

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Has the full migration run in a sandbox first? | Enabling Lightning Knowledge is treated as a one-way door (Gotcha 1) | A signed-off sandbox run before production |
| Which Article Types merge into which record types? | Record types replace article types; layouts and rules are per record type (Gotcha 2) | A type-to-record-type map with field conflicts resolved |
| Will translations be migrated by the Tool or by custom code? | Custom inserts can break the master/translation linkage (Gotcha 3) | Translations created through `submitForTranslation`, because `KnowledgeArticleId` and `MasterVersionId` are not createable (obj 264 L162023-162026, L162061-162064) |
| Who should see which articles after migration? | Data category visibility, not record type assignment, governs viewing (Gotcha 4) | A per-role visibility baseline to compare against |
| Which channels (App, Csp, Prm, Pkb) does each article use today? | Every `IsVisibleIn*` flag must survive (Gotcha 6) | A per-flag count baseline |
| Does any custom code publish or archive articles? | `PublishStatus` is not settable by DML (Gotcha 7) | Publishing-service calls in the migration code |
| Which Apex, triggers and Quick Actions name an article-type `__kav` object? | Those objects are deleted during migration (Gotcha 8) | A pre-migration removal and rewrite list |

UNVERIFIED (2026-10-20): row 1's one-way door and row 3's broken linkage after custom inserts are Help-only; the other rows cite their gotcha's corpus line.

A proper configuration adds a tested record-type map, preserved translation and channel data, and code cleared of article-type references before the Tool runs, where "just doing it" deletes objects that live code still names.

---

## Core Concepts

### 1. Object Model: From Many to One

Classic Knowledge created one sObject per Article Type — `FAQ__kav`, `HowTo__kav`, `Procedure__kav`, etc. Each had its own fields, layouts, and validation rules.

Lightning Knowledge has ONE sObject: `Knowledge__kav`. Differentiation between former Article Types is via record types on `Knowledge__kav`.

| Classic Concept | Lightning Equivalent | Migration Action |
|---|---|---|
| Article Type (`FAQ__kav`, `HowTo__kav`) | Record Type on `Knowledge__kav` | Create one record type per Article Type |
| Per-Article-Type custom fields | Fields on `Knowledge__kav` (with field-level page-layout assignment per record type) | Create unified field set; assign visibility per record type |
| Per-Article-Type page layouts | Page layouts assigned per record type | Recreate layouts; assign |
| Per-Article-Type validation rules | Validation rules on `Knowledge__kav` (with `RecordType.DeveloperName` predicate) | Translate predicates |
| `KnowledgeArticleVersion` (single base sObject) | `Knowledge__kav` (Knowledge Article Version) — yes, same suffix | Same conceptual structure; field semantics preserved |
| Article Type approval processes | Approval processes on `Knowledge__kav` (with record-type entry criteria) | Recreate per record type |

UNVERIFIED (2026-10-20): that layouts, validation rules and approval processes do not port automatically is Help-only; the record-type model itself is obj 264 L163386-163388.

### 2. Migration Tool vs Custom Migration

| Path | When to use | Tradeoffs |
|---|---|---|
| Salesforce Lightning Knowledge Migration Tool | Standard Article Types, standard data categories, modest custom fields | Officially supported; handles versions, translations, publication state |
| Custom migration (Apex / Bulk API) | Unusual schemas (custom approval workflows, non-standard field mappings, partial migration scope) | Full control; significant effort; must replicate the Migration Tool's handling of versions and translations |
| Hybrid (Tool + post-processing) | Standard articles via Tool; targeted custom logic for edge cases | Best of both; requires sequencing discipline |

UNVERIFIED (2026-10-20): what the Tool handles (versions, translations, publication state) is Help-only.

The Salesforce Migration Tool is invoked from Setup → Knowledge → Lightning Knowledge Migration Tool. It runs in the background, produces a detailed log, and supports re-run for failed articles (UNVERIFIED (2026-10-20): Migration Tool behaviour is Help-only). Default to using it. Migrated rows carry `MigratedToFromArticleVersion` (API 43.0+) and `MigratedToFromArticle` (API 45.0+), "the ID for the corresponding pre- or post-migration article" (obj 264 L162069-162076, L161733-161735).

### 3. Versions and Publication States

Classic Knowledge tracks versions: each article has a "master" version, may have an "online" published version, and may have draft versions. Translations are per-version per-language.

| Publication State | What it means |
|---|---|
| Draft | Author is working on a new or updated version |
| Online (Published) | Visible to channels |
| Archived | Previously published, now archived |

Lightning Knowledge keeps the same `PublishStatus` values — Draft, Online, Archived (obj 264 L162102-162110). Migration must port the publication state per-language per-version; custom migrations must explicitly preserve `PublishStatus`, `IsLatestVersion`, and `IsVisibleIn*` flags. From API 47.0, a query with no `PublishStatus` filter returns draft, published and archived articles when Lightning Knowledge is enabled (L163435-163436).

### 4. Translations

`KnowledgeArticleId` is "the ID of the article independent from its version" (obj 264 L162038-162039), and a translation points at its source through `MasterVersionId` (L162066). UNVERIFIED (2026-10-20): that every translation row shares the master's `KnowledgeArticleId`.

| Field | Purpose |
|---|---|
| `Knowledge__kav.KnowledgeArticleId` | Stable across versions (L162038-162039); shared by translations — UNVERIFIED (2026-10-20), see above |
| `Knowledge__kav.Language` | The translated locale |
| `Knowledge__kav.IsMasterLanguage` | "Indicates whether the article has one or more translations associated with it" (obj 264 L161973-161974) |
| `Knowledge__kav.MasterVersionId` | "ID of the source article, if the article is the translation of a source article" (L162066) |
| `Knowledge__kav.TranslationCompletedDate` | Tracks when each translation was finished |

Migration MUST preserve the `KnowledgeArticleId` linkage so master and translations stay grouped. Inserting translations as standalone articles (with new `KnowledgeArticleId` per language) breaks the language-switcher UX in the published surface (UNVERIFIED (2026-10-20): Help-only UI behaviour).

### 5. Data Categories: Preserved but Re-validated

Data category selections are visible per "role, permission set, or profile" (obj 264 L38783-38784 — the Classic `<ArticleType>__DataCategorySelection` page, "not available in Lightning Knowledge"; Lightning metadata sets it per profile through `categoryGroupVisibilities`, api_meta 264 L100293-100295); in Lightning they live on `Knowledge__DataCategorySelection` (L162224-162225). Record types do NOT restrict viewing: "Users can view records of any record type, even if the record type isn't associated with their profile" (secguide 262 L1295-1297). UNVERIFIED (2026-10-20): that the Migration Tool ports category assignments and visibility settings unchanged.

Verify: pre-migration, run "as user X, list visible articles." Post-migration, run the same query. Visible-article counts should match (or differences should be intentional and documented).

### 6. Downstream Consumer Migration Surface

| Consumer | Classic | Lightning | Migration step |
|---|---|---|---|
| Case Feed Knowledge sidebar | Knowledge Sidebar in Service Console | Knowledge Component in Lightning Service Console | Add Knowledge Component to Lightning record page; remove Classic sidebar config |
| Community Knowledge tab | Community page using Classic article type sObject | Community page using `Knowledge__kav` | Update Community Builder pages; field references may need updating |
| Einstein Bot "Suggest Articles" | Bot dialog action with Classic article type | Bot action with `Knowledge__kav` | Update bot action; test "suggested articles" intent flow |
| Service Cloud "Suggested Articles" on Case | Auto-suggest using Classic articles | Auto-suggest using `Knowledge__kav` | Re-enable in Knowledge Settings; verify article matching |
| Apex querying `FAQ__kav` directly | Hardcoded sObject reference | `Knowledge__kav WHERE RecordType.DeveloperName = 'FAQ'` | Remove triggers on the article types BEFORE migration (apexdev 264 L16013-16014); rewrite other code to `Knowledge__kav` |

UNVERIFIED (2026-10-20): the Case Feed, Community, Einstein Bot and Suggested Articles rows above are Help-only surface behaviour; `suggestedArticles` is a `KnowledgeSettings` field (api_meta 264 L123916-123918).

---

## Common Patterns

### Pattern 1: Standard Migration via Lightning Knowledge Migration Tool

**When to use:** Org has standard Article Types, modest custom field counts, and uses the standard Knowledge object model.

**How it works:**
1. Take a sandbox copy. NEVER run the migration tool directly in production without sandbox validation.
2. In sandbox, enable Lightning Knowledge from Setup → Knowledge Settings.
3. Run the Lightning Knowledge Migration Tool from Setup → Knowledge → Lightning Knowledge Migration Tool.
4. Map each Article Type to a record type. Map each Classic field to its Lightning counterpart.
5. Submit; the tool runs asynchronously. Monitor via the Migration Tool log page.
6. After completion, validate: counts match, translations present, data categories preserved, publication states correct.
7. Test downstream consumers in sandbox.
8. Repeat in production once sandbox is signed off. The Migration Tool runs in production exactly the same way (UNVERIFIED (2026-10-20): steps 2–8 describe Help-only Setup and Tool behaviour).

**Why not the alternative:** The Migration Tool handles version history, translation linkage, publication state, and data categories (UNVERIFIED (2026-10-20): Migration Tool behaviour is Help-only, including any coverage percentage). Build custom only when the Tool cannot handle a specific concern.

### Pattern 2: Custom Field-Mapping Decisions Requiring Pre-Processing

**When to use:** Some Classic fields need to be renamed, merged, or transformed before migration. Example: two Article Types both have a "Summary" field, but one is `Description__c` and the other is `Summary__c` — they should map to the same Lightning field.

**How it works:**
1. In the Classic source, normalize field names BEFORE running the Migration Tool. Add a unified `Article_Summary__c` field to every relevant Article Type, populate it via Apex script from the legacy fields.
2. Run the Migration Tool with the unified field mapping to a single Lightning field.
3. Drop the legacy fields after verification.

**Why not the alternative:** The Migration Tool maps fields 1:1 — it cannot merge two source fields into one target (UNVERIFIED (2026-10-20): Migration Tool behaviour is Help-only). Pre-processing in Classic is the right place for the transform; afterwards the article-type objects are gone (apexdev 264 L16013-16014).

### Pattern 3: Article Type Consolidation Decisions

**When to use:** The org has too many Article Types (8+). Some are legacy / barely used. Lightning Knowledge benefits from fewer record types — easier list views, simpler approval workflows, simpler reporting.

**How it works:**
1. Pre-migration, audit Article Types by published-article count and last-update date.
2. Decide which Article Types collapse: e.g., merge "FAQ" and "Q_and_A" into one Lightning record type called "FAQ".
3. Use the Migration Tool's record-type mapping to point both Article Types at the single Lightning record type (UNVERIFIED (2026-10-20): Migration Tool behaviour is Help-only).
4. Document field-mapping conflicts (where the merged Article Types had different fields with similar purposes).

**Why not the alternative:** Migrating 1:1 preserves the current proliferation indefinitely. Migration is the moment to rationalize the taxonomy — afterward, consolidating record types requires more downstream rewiring (record-type-aware code, layouts, validation rules).

### Pattern 4: Phased Channel Cutover

**When to use:** The org publishes articles to multiple channels (Internal, Communities, Public) and cannot risk a simultaneous cutover everywhere.

**How it works:**
1. Migrate to Lightning Knowledge in sandbox + production, recording each article's `IsVisibleInApp` / `IsVisibleInCsp` / `IsVisibleInPrm` / `IsVisibleInPkb` values (obj 264 L161993-162021).
2. Cut over Internal users first: point the internal surfaces at `Knowledge__kav`. Service agents use Lightning Knowledge. (In a multi-type org the Classic article-type objects no longer exist after migration, apexdev 264 L16013-16014 — there is no Classic channel left to switch off.)
3. After 2 weeks of stable Internal use, cut over Communities. Update Community Builder pages, retest.
4. Public Knowledge Base last. The public-facing surface is the highest-risk; cut last after all internal validation.

**Why not the alternative:** A single big-bang channel cutover risks customer-facing issues with no rollback time. Surface-by-surface rollout limits the blast radius (it cannot roll the data back to Classic).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard Article Types, standard fields, modest scale | Salesforce Lightning Knowledge Migration Tool | Handles versions, translations, categories with low risk |
| Need to merge two source fields into one target | Pre-process in Classic via Apex; THEN run Migration Tool | Tool maps 1:1 only (UNVERIFIED (2026-10-20): Migration Tool behaviour is Help-only) |
| Need to consolidate Article Types (8 → 4) | Use Migration Tool record-type mapping for consolidation | Saves a follow-up rationalization project |
| Multilingual with active translations | Migration Tool handles natively; verify per-language counts | Preserves translation linkage via `KnowledgeArticleId` |
| Heavy data category visibility customization | Test category-based visibility post-migration with role-impersonation | Category visibility is per role, permission set or profile (obj 264 L38783-38784 — the Classic `<ArticleType>__DataCategorySelection` page, "not available in Lightning Knowledge"; Lightning metadata sets it per profile through `categoryGroupVisibilities`, api_meta 264 L100293-100295); record types do not restrict viewing (secguide 262 L1295-1297) |
| Many channels (Internal, Customer, Partner, Public) | Phased channel cutover (Pattern 4) | Limits the blast radius per surface |
| Apex code references `FAQ__kav` directly | Remove triggers first; update other code to `Knowledge__kav WHERE RecordType.DeveloperName = 'FAQ'` before the Tool runs | Article-type KAV objects are deleted during migration (apexdev 264 L16013-16014) |
| Einstein Bot uses Knowledge action | Update bot action AFTER migration; test "suggested articles" flow | Bot action references the Knowledge object; must point at `Knowledge__kav` |
| Org is on Classic UI primarily | Migration may require Service Cloud Console UI modernization in parallel | Lightning Knowledge needs Lightning Service Console for the Knowledge Component (UNVERIFIED (2026-10-20): Help-only) |

UNVERIFIED (2026-10-20): the Migration Tool rows (record-type consolidation, native translation handling, Einstein Bot action) describe Help-only behaviour.

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Sandbox-first inventory and decision matrix.** Spin up a Full Copy or Partial sandbox (production enablement is treated as irreversible without article deletion — UNVERIFIED (2026-10-20): Help-only). Enumerate Article Types, custom fields, data categories, languages, channels, downstream consumers. For each Article Type, decide: keep as own record type, consolidate with another, or drop.
2. **Pre-process if consolidating fields or types.** Run Apex scripts in Classic to normalize fields BEFORE invoking the Migration Tool. Add unified fields, populate, and validate. Remove triggers on the article-type KAV objects and run `scripts/check_knowledge_classic_to_lightning.py --manifest-dir <project>`.
3. **Run the Migration Tool in sandbox.** Configure mappings carefully — this is the high-cognitive-load step. Submit, monitor via the Migration Tool log.
4. **Validate exhaustively.** Counts per Article Type → record type. Counts per language. Publication state distribution. Data category visibility (impersonate users via `System.runAs`). Sample articles open and render correctly.
5. **Update downstream consumers in sandbox.** Service Console pages, Communities, Einstein Bots, Apex code. Test end-to-end (Case Feed shows articles; Community search returns expected results).
6. **Sign off; replicate in production with phased channel cutover.** Run the Migration Tool with identical configuration in production. Cut over channels Internal → Communities → Public Knowledge Base with stability windows between each — never simultaneously.
7. **Post-cutover audit.** After a 30-day soak, run a last-known-good comparison (article count per category, per language, per channel matches the pre-migration baseline), joining old and new IDs through `MigratedToFromArticleVersion` (obj 264 L162069-162076). There is no retain-or-drop decision for a multi-type org: the article-type KAV objects "are deleted during migration" (apexdev 264 L16013-16014), so export anything auditors need beforehand.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Migration Tool ran successfully in sandbox; log shows zero unrecoverable errors (UNVERIFIED (2026-10-20): the Tool log is Help-only)
- [ ] Article counts per former Article Type → record type match exactly (allow only documented exclusions)
- [ ] Translation counts per language match pre-migration baseline
- [ ] Data category assignments match: same articles in same categories
- [ ] Publication state distribution matches: Online / Draft / Archived counts agree
- [ ] User-perspective visibility tested for at least one user per relevant role / permission set
- [ ] Service Console Knowledge Component is added to Case page layout and surfaces articles
- [ ] Community Builder pages reference `Knowledge__kav` (not legacy article type sObject)
- [ ] Einstein Bot Knowledge actions updated and tested in conversation
- [ ] Apex code referencing `FAQ__kav`, `HowTo__kav`, etc. updated to `Knowledge__kav` with record-type filter; tests pass
- [ ] Phased cutover schedule agreed; channel-by-channel rollback plan documented
- [ ] Migration audit log persisted (Classic article ID → Lightning Knowledge__kav ID, per language, per version)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Enabling Lightning Knowledge is irreversible without deleting articles.** Once you enable Lightning Knowledge in Setup, you cannot revert to Classic Knowledge without disabling Knowledge entirely — which deletes ALL articles (UNVERIFIED (2026-10-20): Help-only; the corpus confirms only that article-type KAV objects are deleted during a multi-type migration, apexdev 264 L16013-16014, and that "when Lightning Knowledge is enabled, you can't add an article type", pkg2_dev 264 L4591-4592). This is why sandbox-first is mandatory. Test the full migration in sandbox before touching production.

2. **`Knowledge__kav` is one sObject, but article-type record types still drive layouts and validation.** The "we have one object now" mental model leads admins to assume layouts are global. They aren't — page layouts are still assigned per record type, validation rules use `RecordType.DeveloperName` predicates, and approval processes have record-type entry criteria. Migration must recreate per-record-type layouts and rules (UNVERIFIED (2026-10-20): that the Tool does not port them).

3. **Translations preserve `KnowledgeArticleId` — break this and the language switcher disappears.** Custom migrations that insert translations as fresh records (each with its own `KnowledgeArticleId`) lose the master-translation linkage that `MasterVersionId` records (obj 264 L162066). UNVERIFIED (2026-10-20): the Tool's handling and the language-switcher UI behaviour are Help-only.

4. **Data category visibility is per role, permission set or profile — record types do not add a read gate.** Category selections are visible per "role, permission set, or profile" (obj 264 L38783-38784 — the Classic `<ArticleType>__DataCategorySelection` page, "not available in Lightning Knowledge"; Lightning metadata sets it per profile through `categoryGroupVisibilities`, api_meta 264 L100293-100295), while "users can view records of any record type, even if the record type isn't associated with their profile" (secguide 262 L1295-1297). A visibility change after migration points at category assignments, sharing or channel flags — not at record-type assignment. Audit visibility per user role post-migration.

5. **The Service Console Knowledge Component requires Lightning Service Console — not Lightning Experience alone (UNVERIFIED (2026-10-20): Help-only).** Some orgs run on Lightning Experience for sales but Service Console for support. The Knowledge Component renders only inside Service Console. If your support team is using non-console Lightning pages, Knowledge surfacing will be broken until Service Console is adopted.

6. **Salesforce Knowledge "channels" (Internal, Customer, Partner, Public) are visibility flags, not separate stores.** A single article record can be visible in multiple channels via `IsVisibleInPkb`, `IsVisibleInCsp`, `IsVisibleInPrm`, `IsVisibleInApp` (obj 264 L161993-162021). Migration must preserve every flag per article. The Migration Tool does this (UNVERIFIED (2026-10-20): Migration Tool behaviour is Help-only); manual or partial migrations that miss a flag silently hide articles from the channel.

7. **`PublishStatus` is queryable but not directly settable via DML — use `KbManagement.PublishingService` Apex methods.** The field's properties are "Defaulted on create, Filter, Group, Restricted picklist, Sort" — no Create or Update (obj 264 L162102-162105) — so custom migration code that tries to `INSERT Knowledge__kav (PublishStatus='Online')` fails. Lightning Knowledge requires using `KbManagement.PublishingService.publishArticle(articleId, flagAsNew)` to publish, `editOnlineArticle(articleId, false)` to create a draft from an online version, etc. (apexref 262 L163220-163226, L163284-163289). The Migration Tool handles this; manual scripts must use the Apex publishing service.

8. **Quick Actions on Cases referenced article-type sObjects directly in some setups.** A "Insert Article" Quick Action that hardcoded `FAQ__kav` in its URL or relationship breaks after migration, because the article-type KAV objects are deleted during migration (apexdev 264 L16013-16014). Audit Case Quick Actions for `__kav` substring references and update to `Knowledge__kav`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Lightning Knowledge enabled in target org | Setup change; preserved across deployments |
| `Knowledge__kav` record types | One per former Article Type (or per consolidated group) |
| Page layouts and validation rules | Recreated per record type |
| Migrated articles | Versions, translations, publication state, and data categories preserved |
| Migration audit log | Classic article ID → Lightning Knowledge__kav ID, per language and per version (seeded from `MigratedToFromArticleVersion`) |
| Updated Service Console pages | Knowledge Component added; Classic sidebar config removed |
| Updated Community Builder pages | References switched to `Knowledge__kav` |
| Updated Einstein Bot dialogs | Knowledge actions point at Lightning structure |
| Updated Apex code | `__kav` references switched and deployed |
| Phased cutover plan | Channel-by-channel with stability windows |

---

## Related Skills

- `admin/knowledge-base-administration` — Use for new Lightning Knowledge configuration (post-migration)
- `admin/approval-processes` — Use when designing approval workflows on the migrated articles
- `agentforce/rag-patterns-in-salesforce` — Use when migrated articles will ground Einstein/Agentforce responses
- `lwc/visualforce-to-lwc-migration` — Use if Knowledge surfaces also include Visualforce pages being modernized
- `data/data-cloud-data-streams` — Use when migrated articles must also populate Data Cloud for AI grounding
