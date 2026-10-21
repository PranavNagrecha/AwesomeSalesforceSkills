# LLM Anti-Patterns — Knowledge Classic to Lightning Migration

Common mistakes AI coding assistants make when generating or advising on Knowledge migration.

UNVERIFIED (2026-10-20) (file-level): claims about what the Migration Tool does (coverage, 1:1 mapping, single run, channel flags) and that enablement is irreversible are Help-only.

## Anti-Pattern 1: Recommending Direct Production Migration Without Sandbox Validation

**What the LLM generates:** A migration plan that goes straight to production: "Enable Lightning Knowledge in Setup, run the Migration Tool, validate."

**Why it happens:** The Migration Tool is the official Salesforce mechanism, so the model assumes it's safe in production.

**Correct pattern:** Sandbox first — always. Lightning Knowledge enablement is treated as irreversible without article deletion (UNVERIFIED (2026-10-20)), and a multi-type migration deletes the article-type KAV objects (apexdev 264 L16013-16014). Use a Full Copy or Partial sandbox to test the entire migration including downstream consumer rewiring. Only after sandbox sign-off should the same plan run in production. The model must include this gate explicitly.

## Anti-Pattern 2: Inserting Translations as Standalone Records

**What the LLM generates:**

```apex
for (Translation tr : translations) {
    Knowledge__kav record = new Knowledge__kav(
        Title = tr.title,
        Language = tr.language,
        // ... no KnowledgeArticleId reference
    );
    insert record;
}
```

**Why it happens:** The model treats each translation as an independent article record.

**Correct pattern:** Keep translations linked to their source: `MasterVersionId` holds "the ID of the source article" (obj 264 L162066) and `KnowledgeArticleId` is the version-independent article ID (L162038-162039); neither has a Create property (obj 264 L162023-162026, L162061-162064), so create the translation with `KbManagement.PublishingService.submitForTranslation(articleId, language, assigneeId, dueDate)`, which returns the draft translation's ID (apexref 262 L163396-163398). UNVERIFIED (2026-10-20): that a translation inserted with its own `KnowledgeArticleId` breaks the language switcher.

## Anti-Pattern 3: Setting `PublishStatus='Online'` via Direct DML

**What the LLM generates:**

```apex
Knowledge__kav article = new Knowledge__kav(
    Title = 'How to reset your password',
    PublishStatus = 'Online',
    // ...
);
insert article;
```

**Why it happens:** PublishStatus is a writable field; setting it directly looks correct.

**Correct pattern:** `PublishStatus` has no Create or Update property (obj 264 L162102-162105), so leave it unset; then call `KbManagement.PublishingService.publishArticle(articleId, false)` to publish (apexref 262 L163284-163289).

## Anti-Pattern 4: Skipping the `RecordType.DeveloperName` Filter in Migrated SOQL

**What the LLM generates:** Code update that swaps `FROM FAQ__kav` to `FROM Knowledge__kav` without adding the record type filter.

**Why it happens:** Mechanical sObject substitution.

**Correct pattern:** Classic Article Types map to record types on `Knowledge__kav` (obj 264 L163386-163388). Queries that previously returned only FAQ articles now return ALL articles (FAQs, HowTos, TechnicalNotes, etc.). Add `WHERE RecordType.DeveloperName = 'FAQ'` to preserve the original semantics.

## Anti-Pattern 5: Treating "One Object Now" as "Layouts Are Global"

**What the LLM generates:** Documentation or guidance that says "Lightning Knowledge has one object so you only need to manage one set of layouts and validation rules."

**Why it happens:** The "one sObject" simplification is over-applied.

**Correct pattern:** `Knowledge__kav` has one definition, but page layouts, validation rules, and approval processes are still per-record-type. Field-level visibility and required-field enforcement happen per record type's layout assignment. The migration must recreate per-record-type layouts; ongoing maintenance must consider every record type when changes are made.

## Anti-Pattern 6: Copying Only Some `IsVisibleIn*` Channel Flags

**What the LLM generates:** Migration code that maps `IsVisibleInApp` (Internal) but omits `IsVisibleInPkb`, `IsVisibleInCsp`, `IsVisibleInPrm`.

**Why it happens:** "Internal" is the most-used channel; the others are forgotten.

**Correct pattern:** Map all four flags explicitly (obj 264 L161993-162021). Even if the org doesn't currently use all channels, future channel activation requires the flag history to be intact; custom code must map every flag.

## Anti-Pattern 7: Recommending Article Type-by-Article Type Sequential Migration

**What the LLM generates:** A plan that says "Migrate FAQ first, validate, then migrate HowTo, validate, then..."

**Why it happens:** Treating record types as if they could be migrated independently.

**Correct pattern:** Lightning Knowledge enablement is a single org-level event that processes all Article Types together. The Migration Tool runs once and migrates everything based on the configured mapping. There is no "migrate one record type at a time" mode. Plan validation by record type post-migration, not migration by record type.

## Anti-Pattern 8: Ignoring Approval Process Recreation

**What the LLM generates:** Migration plan that focuses on articles and downstream consumers but doesn't mention approval processes.

**Why it happens:** Approval processes feel like a separate admin concern.

**Correct pattern:** Approval processes attached to Classic Article Type sObjects do NOT port — the objects are deleted during a multi-type migration (apexdev 264 L16013-16014). Recreate them on `Knowledge__kav` with `RecordType.DeveloperName = 'X'` entry criteria per former Article Type's process. Without this, draft articles cannot be submitted for approval — the publishing workflow is broken.

## Anti-Pattern 9: Recommending Full Custom Migration When the Tool Would Suffice

**What the LLM generates:** A complex Apex / Bulk API migration plan for a standard Knowledge structure that the Salesforce Migration Tool handles natively.

**Why it happens:** The model defaults to "build a custom solution" without checking the official tool's coverage.

**Correct pattern:** Default to the Salesforce Lightning Knowledge Migration Tool. It handles versions, translations, data categories, publication state, and channel flags correctly. Custom migration is justified only for: pre-normalization (renaming fields before migration), Article Type consolidation, or non-standard schema cases. (UNVERIFIED (2026-10-20): any coverage percentage for the Tool.)

## Anti-Pattern 10: Forgetting to Audit Quick Actions for `__kav` References

**What the LLM generates:** Migration plan that updates Apex and reports but doesn't mention Quick Actions.

**Why it happens:** Quick Actions are admin-configured, not code; they're often missed in code-grep audits.

**Correct pattern:** Quick Actions on Cases (and other objects) often had "Insert Article" or related actions that referenced article-type sObjects. Audit Setup → Object Manager → Case → Buttons, Links, and Actions for any action whose URL or relationship contains `__kav`. Update to `Knowledge__kav` before migration — the article-type KAV objects are deleted during it (apexdev 264 L16013-16014). Without this, "Insert Article" buttons silently break post-migration.
