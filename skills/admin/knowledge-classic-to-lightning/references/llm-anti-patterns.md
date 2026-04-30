# LLM Anti-Patterns — Knowledge Classic to Lightning Migration

Common mistakes AI coding assistants make when generating or advising on Knowledge migration.

## Anti-Pattern 1: Recommending Direct Production Migration Without Sandbox Validation

**What the LLM generates:** A migration plan that goes straight to production: "Enable Lightning Knowledge in Setup, run the Migration Tool, validate."

**Why it happens:** The Migration Tool is the official Salesforce mechanism, so the model assumes it's safe in production.

**Correct pattern:** Sandbox first — always. Lightning Knowledge enablement is irreversible without article deletion. Use a Full Copy or Partial sandbox to test the entire migration including downstream consumer rewiring. Only after sandbox sign-off should the same plan run in production. The model must include this gate explicitly.

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

**Correct pattern:** Translations must share `KnowledgeArticleId` with the master language. Insert the master version first, capture its `KnowledgeArticleId`, then insert each translation referencing the same `KnowledgeArticleId` with a different `Language`. Without this, the language-switcher UI is broken and Salesforce treats translations as orphan articles.

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

**Correct pattern:** Insert in `Draft` state. Then call `KbManagement.PublishingService.publishArticle(articleId, false)` to publish. Publishing involves more than the field — it triggers visibility flag propagation, channel updates, and search index sync. Direct DML does not trigger these side effects.

## Anti-Pattern 4: Skipping the `RecordType.DeveloperName` Filter in Migrated SOQL

**What the LLM generates:** Code update that swaps `FROM FAQ__kav` to `FROM Knowledge__kav` without adding the record type filter.

**Why it happens:** Mechanical sObject substitution.

**Correct pattern:** Classic Article Types map to record types on `Knowledge__kav`. Queries that previously returned only FAQ articles now return ALL articles (FAQs, HowTos, TechnicalNotes, etc.). Add `WHERE RecordType.DeveloperName = 'FAQ'` to preserve the original semantics.

## Anti-Pattern 5: Treating "One Object Now" as "Layouts Are Global"

**What the LLM generates:** Documentation or guidance that says "Lightning Knowledge has one object so you only need to manage one set of layouts and validation rules."

**Why it happens:** The "one sObject" simplification is over-applied.

**Correct pattern:** `Knowledge__kav` has one definition, but page layouts, validation rules, and approval processes are still per-record-type. Field-level visibility and required-field enforcement happen per record type's layout assignment. The migration must recreate per-record-type layouts; ongoing maintenance must consider every record type when changes are made.

## Anti-Pattern 6: Copying Only Some `IsVisibleIn*` Channel Flags

**What the LLM generates:** Migration code that maps `IsVisibleInApp` (Internal) but omits `IsVisibleInPkb`, `IsVisibleInCsp`, `IsVisibleInPrm`.

**Why it happens:** "Internal" is the most-used channel; the others are forgotten.

**Correct pattern:** Map all four flags explicitly. Even if the org doesn't currently use all channels, future channel activation requires the flag history to be intact. The Migration Tool maps all four; custom code must do the same.

## Anti-Pattern 7: Recommending Article Type-by-Article Type Sequential Migration

**What the LLM generates:** A plan that says "Migrate FAQ first, validate, then migrate HowTo, validate, then..."

**Why it happens:** Treating record types as if they could be migrated independently.

**Correct pattern:** Lightning Knowledge enablement is a single org-level event that processes all Article Types together. The Migration Tool runs once and migrates everything based on the configured mapping. There is no "migrate one record type at a time" mode. Plan validation by record type post-migration, not migration by record type.

## Anti-Pattern 8: Ignoring Approval Process Recreation

**What the LLM generates:** Migration plan that focuses on articles and downstream consumers but doesn't mention approval processes.

**Why it happens:** Approval processes feel like a separate admin concern.

**Correct pattern:** Approval processes attached to Classic Article Type sObjects do NOT port. Recreate them on `Knowledge__kav` with `RecordType.DeveloperName = 'X'` entry criteria per former Article Type's process. Without this, draft articles cannot be submitted for approval — the publishing workflow is broken.

## Anti-Pattern 9: Recommending Full Custom Migration When the Tool Would Suffice

**What the LLM generates:** A complex Apex / Bulk API migration plan for a standard Knowledge structure that the Salesforce Migration Tool handles natively.

**Why it happens:** The model defaults to "build a custom solution" without checking the official tool's coverage.

**Correct pattern:** Default to the Salesforce Lightning Knowledge Migration Tool. It handles versions, translations, data categories, publication state, and channel flags correctly. Custom migration is justified only for: pre-normalization (renaming fields before migration), Article Type consolidation, or non-standard schema cases. The Tool runs in 90% of orgs without custom code.

## Anti-Pattern 10: Forgetting to Audit Quick Actions for `__kav` References

**What the LLM generates:** Migration plan that updates Apex and reports but doesn't mention Quick Actions.

**Why it happens:** Quick Actions are admin-configured, not code; they're often missed in code-grep audits.

**Correct pattern:** Quick Actions on Cases (and other objects) often had "Insert Article" or related actions that referenced article-type sObjects. Audit Setup → Object Manager → Case → Buttons, Links, and Actions for any action whose URL or relationship contains `__kav`. Update to `Knowledge__kav`. Without this, "Insert Article" buttons silently break post-migration.
