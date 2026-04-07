# Examples — Gift Entry and Processing

## Example 1: Single Gift Entry with Dry Run Validation Using Default Template

**Context:** A nonprofit fundraiser is entering a $500 check donation from a known contact. The org wants staff to validate gifts before committing to prevent data errors on GiftTransaction records.

**Problem:** Without the dry-run validation step, field mapping errors (e.g., a required designation fund not selected) only surface after `processGiftEntries` fails mid-batch, leaving some staging records processed and others stuck, creating a partial-commit state that is difficult to reconcile.

**Solution:**

The Gift Entry feature exposes `processGiftEntries` as an invocable action. For single-gift dry-run validation, you can call it programmatically or rely on the standard UI "Validate" button (which calls it internally with `isDryRun=true`).

```json
// Invocable action request — processGiftEntries dry run (API v59.0+)
// POST /services/data/v59.0/actions/custom/flow/GiftEntry_ProcessGiftEntries
{
  "inputs": [
    {
      "giftEntryId": "a0G5e000004XyZtEAK",
      "isDryRun": true
    }
  ]
}

// Expected response (no errors):
{
  "actionName": "GiftEntry_ProcessGiftEntries",
  "errors": null,
  "isSuccess": true,
  "outputValues": {
    "giftTransactionId": null
  }
}
// Note: giftTransactionId is null on dry run — no record is created.
```

After confirming the dry run passes, submit the full commit:

```json
// Invocable action request — processGiftEntries full commit
{
  "inputs": [
    {
      "giftEntryId": "a0G5e000004XyZtEAK",
      "isDryRun": false
    }
  ]
}

// Response on success — giftTransactionId is populated:
{
  "outputValues": {
    "giftTransactionId": "a1F5e000003AbCdEAK"
  }
}
```

**Why it works:** The two-phase invocation (validate then commit) mirrors the platform's intended usage pattern. The staging record (`GiftEntry`) acts as a safe scratch pad. The dry run validates field mappings, required fields, and allocation rules without acquiring any record locks or creating any DML. The final commit is atomic: either all target records (GiftTransaction, GiftDesignation, GiftSoftCredit) are created, or none are.

---

## Example 2: Batch Gift Entry for Year-End Donation Processing with Advanced Mapping

**Context:** A development team receives 300 mailed checks at fiscal year-end for a capital campaign. They need to enter all gifts, validate them as a group, and process them in one batch — with each gift mapped to the correct fund designation via Advanced Mapping.

**Problem:** Without a custom batch template linked to the capital campaign, staff would need to manually select the designation for every gift. Without the dry-run batch pass, any single bad record (missing amount, duplicate donor lookup) will fail silently or block the entire batch depending on error handling configuration.

**Solution:**

**Step 1 — Create the custom batch template (Admin, Setup UI):**

1. Go to NPSP Settings > Gift Entry > Templates > New.
2. Name: `Year-End Capital Campaign — Batch 2026`.
3. Set Template Type to **Batch**.
4. Add fields: Donor (Contact lookup), Gift Amount, Payment Method, Check Number, Designation (pre-default to `Capital Campaign Fund`).
5. Enable Advanced Mapping field mappings for `GiftTransaction.Amount` and `GiftDesignation.Amount`.
6. Save and activate the template.

**Step 2 — Enter gifts in the Batch Grid:**

Staff opens Batch Gift Entry, selects the template, and enters all 300 gifts in the spreadsheet-style grid. Each row creates one `GiftEntry` staging record.

**Step 3 — Dry-run pass before committing:**

```apex
// Apex invocation of processGiftEntries for all staging records in the batch
// Using the invocable action via Apex (Flow-invocable pattern)
List<GiftEntry__c> stagingRecords = [
    SELECT Id FROM GiftEntry__c
    WHERE BatchId__c = :batchId AND Status__c = 'Imported'
];

List<Map<String, Object>> inputs = new List<Map<String, Object>>();
for (GiftEntry__c ge : stagingRecords) {
    inputs.add(new Map<String, Object>{
        'giftEntryId' => ge.Id,
        'isDryRun' => true
    });
}

// Call the invocable action
List<Object> results = Flow.Interview.createInterview(
    'GiftEntry_ProcessGiftEntries', inputs
);
// Inspect results for errors — fix flagged records before committing
```

**Step 4 — Process the clean batch:**

After fixing any flagged staging records, re-run with `isDryRun=false`. Each staging record promotes to:
- One `GiftTransaction` (amount, payment method, donor)
- One or more `GiftDesignation` records (fund allocation per Advanced Mapping)
- Zero or more `GiftSoftCredit` records (if household or relationship credit applies)

**Why it works:** The custom batch template pre-wires designation defaults so staff don't need per-gift allocation decisions. Advanced Mapping enforces the canonical field transformation rules for every record in the batch. The dry-run pass before commit ensures all 300 records are valid before any GiftTransaction records are created, avoiding partial-batch states.

---

## Anti-Pattern: Creating Opportunities Directly Instead of Using Gift Entry

**What practitioners do:** Use `insert new Opportunity(...)` in Apex or a data load to create donation records directly, bypassing Gift Entry entirely.

**What goes wrong:** Direct Opportunity creation:
- Does not create a `GiftEntry` staging record, so the gift never enters the Gift Entry pipeline.
- Does not invoke Advanced Mapping field transformations.
- Does not create `GiftDesignation` or `GiftSoftCredit` records.
- Does not set `TaxReceiptStatus` on `GiftTransaction`.
- Results in Opportunity records that may be missing NPSP allocation and soft-credit data, causing reporting gaps.

**Correct approach:** Always use Gift Entry templates to create staging records and invoke `processGiftEntries` to promote them. For programmatic bulk loads, create `GiftEntry` staging records and then invoke `processGiftEntries` per record — do not write directly to `GiftTransaction` or `Opportunity`.
