# Gotchas — Knowledge Classic to Lightning Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

UNVERIFIED (2026-10-20) (file-level): every statement below about what the Lightning Knowledge Migration Tool does, and about Service Console UI behaviour, is Help-only; corpus-grounded lines carry their cite.

## Gotcha 1: Enabling Lightning Knowledge Is Irreversible Without Article Deletion

**What happens:** A team enables Lightning Knowledge in production "just to see the UI", intending to disable it later if it doesn't work for them. They then discover that disabling Knowledge entirely is the only way back — and that requires deleting ALL articles.

**Why:** Lightning Knowledge changes the object model: the article type comes from `RecordType` on `Knowledge__kav`, not from a per-type object (obj 264 L163386-163388), and in a multi-type org the article-type KAV objects "are deleted during migration" (apexdev 264 L16013-16014). UNVERIFIED (2026-10-20): that the only way back is disabling Knowledge, which deletes all article data.

**Mitigation:** Test the entire migration in Full Copy or Partial sandbox first. Sign off completely before enabling in production. Treat the production enablement as a one-way door.

## Gotcha 2: Page Layouts Are Per-Record-Type, Not Global

**What happens:** Migration completes; "we have one Knowledge object now." A new field is added to `Knowledge__kav`. Field appears on the FAQ record type's pages but is missing on the HowTo record type's pages. Admins assume the migration is broken.

**Why:** Lightning Knowledge has one sObject (`Knowledge__kav`), but record types still drive page layouts ("use the record type to determine the article structure and other settings", obj 264 L162123-162124). The "one object" mental model misleads admins into expecting layouts to be global.

**Mitigation:** Treat record types as the unit of layout management. Field changes need explicit assignment to each record type's page layout. Establish a checklist: when adding a field, walk through each record type's layout assignment.

## Gotcha 3: Translations Without Preserved `KnowledgeArticleId` Become Orphans

**What happens:** A custom migration script inserts `Knowledge__kav` rows for each translation, generating fresh `KnowledgeArticleId` values per language. Migration "succeeds" — articles exist, content is correct. Users notice the language-switcher dropdown is empty when viewing an article. They cannot navigate from the English version to the French translation.

**Why:** `KnowledgeArticleId` is "the ID of the article independent from its version" (obj 264 L162038-162039) and a translation names its source in `MasterVersionId` (L162066). UNVERIFIED (2026-10-20): that the language switcher depends on a shared `KnowledgeArticleId`.

**Mitigation:** Use the Salesforce Migration Tool, which handles this correctly. For custom migrations: insert the master-language article, then create each translation with `KbManagement.PublishingService.submitForTranslation(articleId, language, assigneeId, dueDate)`, which "returns new ID of the draft translation" (apexref 262 L163396-163398). Do not try to set `KnowledgeArticleId` or `MasterVersionId` yourself — both are "Filter, Group, Sort" (plus Nillable) with no Create property (obj 264 L162023-162026, L162061-162064). Verify post-migration: `SELECT KnowledgeArticleId, COUNT(Id) FROM Knowledge__kav GROUP BY KnowledgeArticleId HAVING COUNT(Id) > 1` should return groups matching translation expectations.

## Gotcha 4: `PublishStatus='Online'` Cannot Be Set Directly via DML

**What happens:** A custom migration script sets `PublishStatus='Online'` on new `Knowledge__kav` records to mark them as published, and the save is rejected.

**Why:** `PublishStatus` is "Defaulted on create, Filter, Group, Restricted picklist, Sort" — no Create or Update property (obj 264 L162102-162105) — so DML cannot set it at all; Online also needs the "Manage Articles" permission (L162111). Transitions go through `KbManagement.PublishingService` (apexref 262 L163284-163289). UNVERIFIED (2026-10-20): what else publishing triggers (channel propagation, search index updates).

**Mitigation:** Insert articles in Draft state. Then iterate and call `KbManagement.PublishingService.publishArticle(articleId, false)` to publish (`flagAsNew` true publishes a major version, apexref 262 L163285). The Migration Tool does this internally; custom migrations must replicate the publishing service calls.

## Gotcha 5: Channel Visibility Flags Are Independent — Easy to Lose

**What happens:** A migrated article is visible in Internal but not in the Customer Community. Investigation: pre-migration, the article had `IsVisibleInCsp=true` (Customer Portal). Post-migration, the value is `false` because the migration script copied only the visibility flags it knew about.

**Why:** Articles have multiple independent channel flags: `IsVisibleInPkb` (public knowledge base), `IsVisibleInCsp` (Customer Portal), `IsVisibleInPrm` (partner portal), `IsVisibleInApp` (Articles tab) (obj 264 L161993-162021). Each is independent. A migration that copies only some flags silently loses channel exposure for the others.

**Mitigation:** Explicitly map all four `IsVisibleIn*` flags in the migration. The Salesforce Migration Tool handles this; custom code MUST include each flag.

## Gotcha 6: Service Console Knowledge Component Requires Service Console UI

**What happens:** A support team is on Lightning Experience but uses a custom record page for Cases (not the Service Console template). After migration, the team is told to use the Knowledge Component to access articles. They add it to their custom record page; the component renders but search returns no results.

**Why:** The Knowledge Component has full functionality only inside the Service Console UI. On non-console Lightning record pages, it renders but with limited capabilities — search, attach-to-case, and some other behaviors are degraded.

**Mitigation:** If support uses Service Console, no problem. If support uses standard Lightning Experience record pages, plan for a Service Console adoption project alongside the Knowledge migration. Or, build a custom LWC that queries `Knowledge__kav` (or runs SOSL) to provide search-and-display in non-console contexts.

## Gotcha 7: Record Types Do Not Gate Article Visibility — Look Elsewhere

**What happens:** Post-migration, Support Agents can no longer see Hardware-category articles. The team blames the new "TechnicalNote" record type that their profile is not assigned.

**Why:** Record type assignment is not a read gate: "Users can view records of any record type, even if the record type isn't associated with their profile" (secguide 262 L1295-1297). Category selections are visible per "role, permission set, or profile" (obj 264 L38783-38784 — the Classic `<ArticleType>__DataCategorySelection` page, "not available in Lightning Knowledge"; Lightning metadata sets it per profile through `categoryGroupVisibilities`, api_meta 264 L100293-100295), and channel flags (`IsVisibleIn*`) and sharing decide the rest.

**Mitigation:** Compare category assignments (`Knowledge__DataCategorySelection`, obj 264 L162224-162259), category visibility and channel flags against the pre-migration baseline. Test post-migration visibility with `System.runAs` for each affected role.

## Gotcha 8: `__kav` References in Apex, Quick Actions, and Reports

**What happens:** Migration completes; articles look correct in Service Console. A week later, an Apex scheduled job fails: "sObject type FAQ__kav does not exist."

**Why:** In a multi-type org the article-type KAV objects "are deleted during migration"; Apex triggers on them must be removed first, and "admins see an error message if Apex triggers still reference the article type KAV objects" (apexdev 264 L16011-16014). Any other Apex, Quick Action, report, or LWC that names them breaks afterwards.

**Mitigation:** Pre-migration grep for every Article Type sObject name across Apex, Visualforce, LWC, Flow, Process Builder, and report types. Remove triggers on the article types and update each other reference to `Knowledge__kav` with a `RecordType.DeveloperName` filter BEFORE the Tool runs.

## Gotcha 9: Approval Process Migration Requires Per-Record-Type Recreation

**What happens:** Pre-migration, the FAQ Article Type had an approval process. Post-migration, draft FAQ articles can be saved but cannot be submitted for approval — the option is missing.

**Why:** Approval processes were attached to the Classic Article Type sObject, which is deleted during a multi-type migration (apexdev 264 L16013-16014). UNVERIFIED (2026-10-20): that the Tool never recreates them. Lightning approval processes attach to `Knowledge__kav` with record-type-aware entry criteria, but they must be recreated.

**Mitigation:** Recreate approval processes on `Knowledge__kav` with entry criteria `RecordType.DeveloperName = 'FAQ'` (or equivalent per record type). Test the full approval cycle (submit → approver review → approval/rejection → publish) per record type before sign-off.
