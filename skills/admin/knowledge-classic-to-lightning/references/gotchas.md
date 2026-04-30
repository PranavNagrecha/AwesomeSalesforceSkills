# Gotchas — Knowledge Classic to Lightning Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Enabling Lightning Knowledge Is Irreversible Without Article Deletion

**What happens:** A team enables Lightning Knowledge in production "just to see the UI", intending to disable it later if it doesn't work for them. They then discover that disabling Knowledge entirely is the only way back — and that requires deleting ALL articles.

**Why:** Lightning Knowledge fundamentally changes the object model. Salesforce does not support converting a Lightning Knowledge org back to Classic Knowledge. The only path back is "disable Knowledge" which deletes all article data; you cannot then re-enable Classic Knowledge with the original articles intact.

**Mitigation:** Test the entire migration in Full Copy or Partial sandbox first. Sign off completely before enabling in production. Treat the production enablement as a one-way door.

## Gotcha 2: Page Layouts Are Per-Record-Type, Not Global

**What happens:** Migration completes; "we have one Knowledge object now." A new field is added to `Knowledge__kav`. Field appears on the FAQ record type's pages but is missing on the HowTo record type's pages. Admins assume the migration is broken.

**Why:** Lightning Knowledge has one sObject (`Knowledge__kav`), but record types still drive page layouts and field-level visibility. The "one object" mental model misleads admins into expecting layouts to be global.

**Mitigation:** Treat record types as the unit of layout management. Field changes need explicit assignment to each record type's page layout. Establish a checklist: when adding a field, walk through each record type's layout assignment.

## Gotcha 3: Translations Without Preserved `KnowledgeArticleId` Become Orphans

**What happens:** A custom migration script inserts `Knowledge__kav` rows for each translation, generating fresh `KnowledgeArticleId` values per language. Migration "succeeds" — articles exist, content is correct. Users notice the language-switcher dropdown is empty when viewing an article. They cannot navigate from the English version to the French translation.

**Why:** The language-switcher UX depends on translations sharing a `KnowledgeArticleId`. Each translation row must have the same `KnowledgeArticleId` as the master language, with `Language` differentiating them.

**Mitigation:** Use the Salesforce Migration Tool, which handles this correctly. For custom migrations: insert the master language first, capture its `KnowledgeArticleId`, then insert each translation with that same `KnowledgeArticleId` and the appropriate `Language`. Verify post-migration: `SELECT KnowledgeArticleId, COUNT(Id) FROM Knowledge__kav GROUP BY KnowledgeArticleId HAVING COUNT(Id) > 1` should return groups matching translation expectations.

## Gotcha 4: `PublishStatus='Online'` Cannot Be Set Directly via DML

**What happens:** A custom migration script inserts `Knowledge__kav` records with `PublishStatus='Online'` to mark them as published. Insert succeeds; articles exist but the Service Console doesn't show them as published. The "Online" channel views are empty.

**Why:** `PublishStatus` is a system-managed field. Direct DML can set initial states like `Draft`, but transitions to `Online` and `Archived` must go through the `KbManagement.PublishingService` Apex namespace. The `Online` status involves more than the field — it triggers visibility flags, channel propagation, and search index updates.

**Mitigation:** Insert articles in Draft state. Then iterate and call `KbManagement.PublishingService.publishArticle(articleId, false)` to publish. The Migration Tool does this internally; custom migrations must replicate the publishing service calls.

## Gotcha 5: Channel Visibility Flags Are Independent — Easy to Lose

**What happens:** A migrated article is visible in Internal but not in the Customer Community. Investigation: pre-migration, the article had `IsVisibleInCsp=true` (Customer Portal). Post-migration, the value is `false` because the migration script copied only the visibility flags it knew about.

**Why:** Articles have multiple independent channel flags: `IsVisibleInPkb` (Public Knowledge Base), `IsVisibleInCsp` (Customer Portal/Communities), `IsVisibleInPrm` (Partner Portal), `IsVisibleInApp` (Internal). Each is independent. A migration that copies only some flags silently loses channel exposure for the others.

**Mitigation:** Explicitly map all four `IsVisibleIn*` flags in the migration. The Salesforce Migration Tool handles this; custom code MUST include each flag.

## Gotcha 6: Service Console Knowledge Component Requires Service Console UI

**What happens:** A support team is on Lightning Experience but uses a custom record page for Cases (not the Service Console template). After migration, the team is told to use the Knowledge Component to access articles. They add it to their custom record page; the component renders but search returns no results.

**Why:** The Knowledge Component has full functionality only inside the Service Console UI. On non-console Lightning record pages, it renders but with limited capabilities — search, attach-to-case, and some other behaviors are degraded.

**Mitigation:** If support uses Service Console, no problem. If support uses standard Lightning Experience record pages, plan for a Service Console adoption project alongside the Knowledge migration. Or, build a custom LWC that wraps the `KnowledgeServiceLayer` to provide search-and-display in non-console contexts.

## Gotcha 7: Data Category Visibility Restrictions Compound with Record Type Access

**What happens:** Pre-migration, Support Agent role had visibility on data category "Hardware". Post-migration, Support Agents can no longer see Hardware-category articles. Confused, the team checks data category visibility — it's still set correctly. Investigation: the Hardware articles migrated to record type "TechnicalNote" which the Support Agent profile doesn't have read access to.

**Why:** Lightning Knowledge introduces record-type-based visibility on top of data category visibility. Both must permit access for an article to be visible. A user with category access but lacking record type access loses visibility — this is new behavior post-migration.

**Mitigation:** Audit profile and permission set assignments for record-type read access. The Migration Tool may consolidate Article Types into record types in ways that require new profile permissions. Test post-migration visibility with `System.runAs` for each affected role.

## Gotcha 8: `__kav` References in Apex, Quick Actions, and Reports

**What happens:** Migration completes; articles look correct in Service Console. A week later, an Apex scheduled job fails: "sObject type FAQ__kav does not exist." Audit reveals the legacy Article Type sObject was dropped post-migration; code that referenced it broke.

**Why:** Classic Article Type sObjects (`FAQ__kav`, `HowTo__kav`) become inaccessible after the Migration Tool runs (or after Classic Knowledge is fully decommissioned). Any Apex, Quick Action, report, or LWC that referenced them by name breaks.

**Mitigation:** Pre-migration grep for every Article Type sObject name across Apex, Visualforce, LWC, Flow, Process Builder, and report types. Update each reference to `Knowledge__kav` with appropriate `RecordType.DeveloperName` filter. Deploy the code changes alongside the migration.

## Gotcha 9: Approval Process Migration Requires Per-Record-Type Recreation

**What happens:** Pre-migration, the FAQ Article Type had an approval process. Post-migration, draft FAQ articles can be saved but cannot be submitted for approval — the option is missing.

**Why:** Approval processes were attached to the Classic Article Type sObject. They do not auto-port to Lightning Knowledge. Lightning approval processes attach to `Knowledge__kav` with record-type-aware entry criteria, but they must be recreated.

**Mitigation:** Recreate approval processes on `Knowledge__kav` with entry criteria `RecordType.DeveloperName = 'FAQ'` (or equivalent per record type). Test the full approval cycle (submit → approver review → approval/rejection → publish) per record type before sign-off.
