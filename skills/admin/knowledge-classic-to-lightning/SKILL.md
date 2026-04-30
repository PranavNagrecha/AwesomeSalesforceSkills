---
name: knowledge-classic-to-lightning
description: "Migrating Classic Knowledge (KnowledgeArticleVersion / Article Types) to Lightning Knowledge (Knowledge__kav with record types): article-type-to-record-type mapping, multi-language translation preservation, data category re-architecture, file attachment porting, version and publication-state retention, channel visibility translation, and downstream Case Feed / Community / Bot rewiring. NOT for new Lightning Knowledge setup (use admin/knowledge-base-administration) or for editorial workflow design (use admin/knowledge-publishing-workflow)."
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
  - "Decommissioning plan for Classic article types (retain or delete after soak)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-29
---

# Knowledge Classic to Lightning Migration

This skill activates when a practitioner needs to migrate from Classic Knowledge (multiple Article Types as separate sObjects) to Lightning Knowledge (a single `Knowledge__kav` sObject with record types), preserving versions, translations, data categories, and downstream consumer integrations.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Classic Knowledge is enabled and inventory Article Types: `SELECT Id, MasterLabel, DeveloperName FROM KnowledgeArticleType`. Each Classic Article Type is a separate sObject (`FAQ__kav`, `HowTo__kav`, etc.); Lightning collapses them into one `Knowledge__kav` with record types.
- Inventory translations. `SELECT Language, COUNT(Id) FROM KnowledgeArticleVersion WHERE PublishStatus='Online' GROUP BY Language`. Lightning Knowledge supports the same multi-language structure but the migration must port each language version individually.
- Inventory data categories. `SELECT Id, MasterLabel, ParentId FROM CategoryGroup` and `SELECT Id, MasterLabel, GroupId FROM Category`. Categories carry over but visibility settings must be re-validated against the new record-type structure.
- Identify downstream consumers: Case Feed Knowledge Component (Lightning Service Console), Knowledge Sidebar (Classic only — being deprecated), Community Knowledge pages, Einstein Bot Knowledge action, Salesforce Service Cloud "suggested articles" on Cases, and any Apex code querying article sObjects directly.
- Confirm whether the Salesforce-provided Lightning Knowledge Migration Tool is in scope. The Migration Tool handles 80–90% of cases; custom code is needed only for unusual data category structures, custom field mappings, or article-type consolidation decisions.

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

### 2. Migration Tool vs Custom Migration

| Path | When to use | Tradeoffs |
|---|---|---|
| Salesforce Lightning Knowledge Migration Tool | Standard Article Types, standard data categories, modest custom fields | Officially supported; handles versions, translations, publication state |
| Custom migration (Apex / Bulk API) | Unusual schemas (custom approval workflows, non-standard field mappings, partial migration scope) | Full control; significant effort; must replicate the Migration Tool's handling of versions and translations |
| Hybrid (Tool + post-processing) | Standard articles via Tool; targeted custom logic for edge cases | Best of both; requires sequencing discipline |

The Salesforce Migration Tool is invoked from Setup → Knowledge → Lightning Knowledge Migration Tool. It runs in the background, produces a detailed log, and supports re-run for failed articles. Default to using it.

### 3. Versions and Publication States

Classic Knowledge tracks versions: each article has a "master" version, may have an "online" published version, and may have draft versions. Translations are per-version per-language.

| Publication State | What it means |
|---|---|
| Draft | Author is working on a new or updated version |
| Online (Published) | Visible to channels |
| Archived | Previously published, now archived |

Lightning Knowledge preserves the same state machine. Migration must port the publication state per-language per-version. The Migration Tool handles this; custom migrations must explicitly preserve `PublishStatus`, `IsLatestVersion`, and `IsVisibleIn*` flags.

### 4. Translations

Each translated article in Classic is a `KnowledgeArticleVersion` row with the same `KnowledgeArticleId` (the master article) and a different `Language` value. Lightning Knowledge structure is identical: each translation is a `Knowledge__kav` row sharing a `KnowledgeArticleId` with a different `Language`.

| Field | Purpose |
|---|---|
| `Knowledge__kav.KnowledgeArticleId` | Stable across versions and translations |
| `Knowledge__kav.Language` | The translated locale |
| `Knowledge__kav.IsMasterLanguage` | True for the master version's language record |
| `Knowledge__kav.TranslationCompletedDate` | Tracks when each translation was finished |

Migration MUST preserve the `KnowledgeArticleId` linkage so master and translations stay grouped. Inserting translations as standalone articles (with new `KnowledgeArticleId` per language) breaks the language-switcher UX in the published surface.

### 5. Data Categories: Preserved but Re-validated

Data Category Groups, Categories, and the category visibility settings (per role / permission set) port directly. The migration tool preserves the assignments. The risk is that record-type-based visibility (new in Lightning) may unintentionally restrict article visibility for users who previously saw articles by category alone.

Verify: pre-migration, run "as user X, list visible articles." Post-migration, run the same query. Visible-article counts should match (or differences should be intentional and documented).

### 6. Downstream Consumer Migration Surface

| Consumer | Classic | Lightning | Migration step |
|---|---|---|---|
| Case Feed Knowledge sidebar | Knowledge Sidebar in Service Console | Knowledge Component in Lightning Service Console | Add Knowledge Component to Lightning record page; remove Classic sidebar config |
| Community Knowledge tab | Community page using Classic article type sObject | Community page using `Knowledge__kav` | Update Community Builder pages; field references may need updating |
| Einstein Bot "Suggest Articles" | Bot dialog action with Classic article type | Bot action with `Knowledge__kav` | Update bot action; test "suggested articles" intent flow |
| Service Cloud "Suggested Articles" on Case | Auto-suggest using Classic articles | Auto-suggest using `Knowledge__kav` | Re-enable in Knowledge Settings; verify article matching |
| Apex querying `FAQ__kav` directly | Hardcoded sObject reference | `Knowledge__kav WHERE RecordType.DeveloperName = 'FAQ'` | Code change; deploy with the rest of the migration |

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
8. Repeat in production once sandbox is signed off. The Migration Tool runs in production exactly the same way.

**Why not the alternative:** The Migration Tool handles version history, translation linkage, publication state, and data categories better than custom code in 90% of cases. Build custom only when the Tool cannot handle a specific concern.

### Pattern 2: Custom Field-Mapping Decisions Requiring Pre-Processing

**When to use:** Some Classic fields need to be renamed, merged, or transformed before migration. Example: two Article Types both have a "Summary" field, but one is `Description__c` and the other is `Summary__c` — they should map to the same Lightning field.

**How it works:**
1. In the Classic source, normalize field names BEFORE running the Migration Tool. Add a unified `Article_Summary__c` field to every relevant Article Type, populate it via Apex script from the legacy fields.
2. Run the Migration Tool with the unified field mapping to a single Lightning field.
3. Drop the legacy fields after verification.

**Why not the alternative:** The Migration Tool maps fields 1:1 — it cannot merge two source fields into one target. Pre-processing in Classic is the right place for the transform.

### Pattern 3: Article Type Consolidation Decisions

**When to use:** The org has too many Article Types (8+). Some are legacy / barely used. Lightning Knowledge benefits from fewer record types — easier list views, simpler approval workflows, simpler reporting.

**How it works:**
1. Pre-migration, audit Article Types by published-article count and last-update date.
2. Decide which Article Types collapse: e.g., merge "FAQ" and "Q_and_A" into one Lightning record type called "FAQ".
3. Use the Migration Tool's record-type mapping to point both Article Types at the single Lightning record type.
4. Document field-mapping conflicts (where the merged Article Types had different fields with similar purposes).

**Why not the alternative:** Migrating 1:1 preserves the current proliferation indefinitely. Migration is the moment to rationalize the taxonomy — afterward, consolidating record types requires more downstream rewiring (record-type-aware code, layouts, validation rules).

### Pattern 4: Phased Channel Cutover

**When to use:** The org publishes articles to multiple channels (Internal, Communities, Public) and cannot risk a simultaneous cutover everywhere.

**How it works:**
1. Migrate to Lightning Knowledge in sandbox + production with all channels disabled in Lightning.
2. Cut over Internal users first: enable Internal channel for Lightning, disable Internal channel for Classic. Service agents use Lightning Knowledge.
3. After 2 weeks of stable Internal use, cut over Communities. Update Community Builder pages, retest.
4. Public Knowledge Base last. The public-facing surface is the highest-risk; cut last after all internal validation.

**Why not the alternative:** A single big-bang channel cutover risks customer-facing issues with no rollback time. Channel-by-channel preserves rollback at each step.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard Article Types, standard fields, modest scale | Salesforce Lightning Knowledge Migration Tool | Handles versions, translations, categories with low risk |
| Need to merge two source fields into one target | Pre-process in Classic via Apex; THEN run Migration Tool | Tool maps 1:1 only |
| Need to consolidate Article Types (8 → 4) | Use Migration Tool record-type mapping for consolidation | Saves a follow-up rationalization project |
| Multilingual with active translations | Migration Tool handles natively; verify per-language counts | Preserves translation linkage via `KnowledgeArticleId` |
| Heavy data category visibility customization | Test category-based visibility post-migration with role-impersonation | Record types add new visibility axis that may unintentionally restrict |
| Many channels (Internal, Customer, Partner, Public) | Phased channel cutover (Pattern 4) | Maintains rollback options |
| Apex code references `FAQ__kav` directly | Update to `Knowledge__kav WHERE RecordType.DeveloperName = 'FAQ'`; deploy with migration | Required for the integration to find articles post-migration |
| Einstein Bot uses Knowledge action | Update bot action AFTER migration; test "suggested articles" flow | Bot action references the Knowledge object; must point at `Knowledge__kav` |
| Org is on Classic UI primarily | Migration may require Service Cloud Console UI modernization in parallel | Lightning Knowledge needs Lightning Service Console for the Knowledge Component |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Sandbox first — always.** Spin up a Full Copy or Partial sandbox. Never test the Migration Tool's first run in production. Reasons: the Tool changes object model permanently; some changes cannot be reversed without re-disabling Knowledge entirely (which deletes articles).
2. **Inventory and decision matrix.** Enumerate Article Types, custom fields, data categories, languages, channels, downstream consumers. For each Article Type, decide: keep as own record type, consolidate with another, or drop.
3. **Pre-process if consolidating fields or types.** Run Apex scripts in Classic to normalize fields BEFORE invoking the Migration Tool. Add unified fields, populate, and validate.
4. **Run the Migration Tool in sandbox.** Configure mappings carefully — this is the high-cognitive-load step. Submit, monitor.
5. **Validate exhaustively.** Counts per Article Type → record type. Counts per language. Publication state distribution. Data category visibility (impersonate users). Sample articles open and render correctly.
6. **Update downstream consumers in sandbox.** Service Console pages, Communities, Einstein Bots, Apex code. Test end-to-end (Case Feed shows articles; Community search returns expected results).
7. **Sign off and replicate in production.** Run the Migration Tool with identical configuration. Validate identically.
8. **Phased channel cutover (Pattern 4).** Internal → Communities → Public, with stability windows between each.
9. **Post-cutover audit.** After 30 days, run a last-known-good comparison: same article query in Lightning matches the pre-migration Classic baseline (article count per category, per language, per channel).
10. **Decommission Classic Article Types.** After signoff, decide retain (read-only audit) or drop. Dropping requires disabling Classic Knowledge cohorts which is irreversible — be deliberate.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Migration Tool ran successfully in sandbox; log shows zero unrecoverable errors
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

1. **Enabling Lightning Knowledge is irreversible without deleting articles.** Once you enable Lightning Knowledge in Setup, you cannot revert to Classic Knowledge without disabling Knowledge entirely — which deletes ALL articles. This is why sandbox-first is mandatory. Test the full migration in sandbox before touching production.

2. **`Knowledge__kav` is one sObject, but article-type record types still drive layouts and validation.** The "we have one object now" mental model leads admins to assume layouts are global. They aren't — page layouts are still assigned per record type, validation rules use `RecordType.DeveloperName` predicates, and approval processes have record-type entry criteria. Migration must recreate per-record-type layouts and rules.

3. **Translations preserve `KnowledgeArticleId` — break this and the language switcher disappears.** The Migration Tool does this correctly. Custom migrations that insert translations as fresh records (each with its own `KnowledgeArticleId`) lose the master-translation linkage. The published article surface has a "view in another language" switcher that depends on this linkage; without it, users see translations as completely separate articles.

4. **Data category visibility is per-role and per-permission-set; consolidation may unintentionally restrict.** A Classic article visible to a role via category visibility may, post-migration, also be subject to record-type access controls. Users who lacked the new record type's read access lose visibility even though categories are unchanged. Audit visibility per user role post-migration.

5. **The Service Console Knowledge Component requires Lightning Service Console — not Lightning Experience alone.** Some orgs run on Lightning Experience for sales but Service Console for support. The Knowledge Component renders only inside Service Console. If your support team is using non-console Lightning pages, Knowledge surfacing will be broken until Service Console is adopted.

6. **Salesforce Knowledge "channels" (Internal, Customer, Partner, Public) are visibility flags, not separate stores.** A single article record can be visible in multiple channels via `IsVisibleInPkb`, `IsVisibleInCsp`, `IsVisibleInPrm`, `IsVisibleInApp`. Migration must preserve every flag per article. The Migration Tool does this; manual or partial migrations that miss a flag silently hide articles from the channel.

7. **`PublishStatus` is queryable but not directly settable via DML — use `KbManagement.PublishingService` Apex methods.** Custom migration code that tries to `INSERT Knowledge__kav (PublishStatus='Online')` fails. Lightning Knowledge requires using `KbManagement.PublishingService.publishArticle(articleId, isFlagAsNew)` to publish, `editOnlineArticle(articleId, false)` to create a draft from an online version, etc. The Migration Tool handles this; manual scripts must use the Apex publishing service.

8. **Quick Actions on Cases referenced article-type sObjects directly in some setups.** A "Insert Article" Quick Action that hardcoded `FAQ__kav` in its URL or relationship breaks after migration. Audit Case Quick Actions for `__kav` substring references and update to `Knowledge__kav`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Lightning Knowledge enabled in target org | Setup change; preserved across deployments |
| `Knowledge__kav` record types | One per former Article Type (or per consolidated group) |
| Page layouts and validation rules | Recreated per record type |
| Migrated articles | Versions, translations, publication state, and data categories preserved |
| Migration audit log | Classic article ID → Lightning Knowledge__kav ID, per language and per version |
| Updated Service Console pages | Knowledge Component added; Classic sidebar config removed |
| Updated Community Builder pages | References switched to `Knowledge__kav` |
| Updated Einstein Bot dialogs | Knowledge actions point at Lightning structure |
| Updated Apex code | `__kav` references switched and deployed |
| Phased cutover plan | Channel-by-channel with stability windows |

---

## Related Skills

- `admin/knowledge-base-administration` — Use for new Lightning Knowledge configuration (post-migration)
- `admin/knowledge-publishing-workflow` — Use when designing approval workflows on the migrated articles
- `agentforce/agentforce-knowledge-grounding` — Use when migrated articles will ground Einstein/Agentforce responses
- `lwc/visualforce-to-lwc-migration` — Use if Knowledge surfaces also include Visualforce pages being modernized
- `data/data-cloud-knowledge-ingestion` — Use when migrated articles must also populate Data Cloud for AI grounding
