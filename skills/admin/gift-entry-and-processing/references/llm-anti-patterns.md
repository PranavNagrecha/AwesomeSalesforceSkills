# LLM Anti-Patterns — Gift Entry and Processing

Common mistakes AI coding assistants make when generating or advising on Gift Entry and Processing.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Creating Opportunities Directly Instead of Using Gift Entry Staging

**What the LLM generates:**
```apex
Opportunity opp = new Opportunity(
    Name = 'Donation - ' + donorName,
    StageName = 'Closed Won',
    CloseDate = Date.today(),
    Amount = giftAmount,
    AccountId = donorAccountId
);
insert opp;
```

**Why it happens:** LLMs are trained heavily on standard Salesforce CRM patterns where Opportunity is the canonical revenue object. The NPSP Gift Entry staging model (GiftEntry → processGiftEntries → GiftTransaction) is a newer, less-represented pattern. LLMs default to the most common DML pattern they've seen.

**Correct pattern:**
```apex
// Create a GiftEntry staging record, then invoke processGiftEntries
// Do not write directly to Opportunity or GiftTransaction
GiftEntry__c staging = new GiftEntry__c(
    DonorId__c = donorContactId,
    Amount__c = giftAmount,
    PaymentMethod__c = 'Check',
    DesignationId__c = fundId
);
insert staging;

// Then invoke processGiftEntries via Flow invocable action or REST API
// POST /services/data/v59.0/actions/custom/flow/GiftEntry_ProcessGiftEntries
// with giftEntryId = staging.Id, isDryRun = false
```

**Detection hint:** Look for `insert new Opportunity` or `insert new GiftTransaction` in code supposedly implementing NPSP Gift Entry. Neither should appear — staging records go to `GiftEntry__c` and promotion is handled by `processGiftEntries`.

---

## Anti-Pattern 2: Using a Custom Template for Single-Gift Entry

**What the LLM generates:**
```
"Create a custom Gift Entry template and configure it for both single-gift
entry and batch entry to give users flexibility."
```

**Why it happens:** LLMs infer from general UI customization patterns that templates can be assigned to any entry mode. The single-entry / batch-only constraint on custom templates is a non-obvious platform limitation that does not follow from general Salesforce UX patterns.

**Correct pattern:**
```
Single-gift entry: Default Gift Entry Template only (system-provided; cannot be
replaced for single-entry mode).

Batch gift entry: Create custom templates. These are batch-only and will not
appear in the single-gift entry UI.

Do not attempt to use a custom template for single-gift entry — it will not
surface in the UI regardless of template configuration.
```

**Detection hint:** Any instruction that says "use a custom template for single-gift entry" or "configure the custom template for both modes" is incorrect. Single-entry mode has exactly one template option: the Default Gift Entry Template.

---

## Anti-Pattern 3: Skipping the isDryRun Validation Pass Before Batch Commits

**What the LLM generates:**
```apex
// Process all staging records directly
for (GiftEntry__c ge : stagingRecords) {
    processGiftEntries(ge.Id, false); // isDryRun=false immediately
}
```

**Why it happens:** LLMs optimize for brevity and assume validation is handled elsewhere (e.g., at the UI level). They do not model the Gift Entry two-phase commit pattern as a deliberate architectural requirement.

**Correct pattern:**
```apex
// Phase 1: Dry run all records — surface errors before any commits
List<String> errors = new List<String>();
for (GiftEntry__c ge : stagingRecords) {
    Object result = processGiftEntries(ge.Id, true); // isDryRun=true
    if (result has errors) errors.add(ge.Id + ': ' + errorMessage);
}

// Fix flagged records, then:
// Phase 2: Commit only clean records
for (GiftEntry__c ge : cleanStagingRecords) {
    processGiftEntries(ge.Id, false); // isDryRun=false
}
```

**Detection hint:** Any Gift Entry processing loop that calls `processGiftEntries` with only `isDryRun=false` (or omits the parameter entirely) with no prior validation pass is missing the dry-run gate. Flag for review before running against production data.

---

## Anti-Pattern 4: Applying Rollback Logic Around isDryRun Calls

**What the LLM generates:**
```apex
Savepoint sp = Database.setSavepoint();
try {
    processGiftEntries(giftEntryId, true); // isDryRun=true
} catch (Exception e) {
    Database.rollback(sp); // Unnecessary — dry run creates no records
}
```

**Why it happens:** LLMs apply defensive Apex patterns (Savepoint/Rollback) to any operation that touches database-adjacent logic. They do not model `isDryRun=true` as a zero-DML validation call.

**Correct pattern:**
```apex
// isDryRun=true creates NO records — no Savepoint needed
// Just call and inspect the result object for validation errors
Object validationResult = processGiftEntries(giftEntryId, true);
if (validationResult.hasErrors()) {
    // Handle validation errors — log, surface to UI, etc.
}
// No rollback needed — nothing was written
```

**Detection hint:** Savepoint/Rollback wrappers around `isDryRun=true` calls are always unnecessary overhead. If you see them, remove them and add a comment explaining that dry-run is a pure validation pass.

---

## Anti-Pattern 5: Referencing TaxReceiptStatus Without Checking API Version

**What the LLM generates:**
```soql
SELECT Id, Amount, TaxReceiptStatus FROM GiftTransaction WHERE CloseDate = THIS_YEAR
```

```apex
gt.TaxReceiptStatus = 'PENDING';
update gt;
```

**Why it happens:** LLMs generate code using the most recent API features they have seen in training data without modeling API version constraints. `TaxReceiptStatus` is a newer field (API v62.0+) that LLMs may reference in orgs that are on earlier API versions.

**Correct pattern:**
```
Before referencing TaxReceiptStatus:
1. Confirm org API version >= 62.0
2. If API version < 62.0: use a custom field (e.g., Receipt_Status__c) as a workaround
3. Document the migration path to TaxReceiptStatus when the org upgrades

// API v62.0+ only:
SELECT Id, Amount, TaxReceiptStatus FROM GiftTransaction WHERE CloseDate = THIS_YEAR

// Orgs below v62.0 — use custom field:
SELECT Id, Amount, Receipt_Status__c FROM GiftTransaction WHERE CloseDate = THIS_YEAR
```

**Detection hint:** Any code that references `TaxReceiptStatus` without a preceding API version check or comment should be flagged. Ask: "What API version is this org on?" before using this field in any Apex, Flow, or SOQL artifact.
