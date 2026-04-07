---
name: gift-entry-and-processing
description: "Configure and operate NPSP Gift Entry: gift entry templates, batch gift entry, payment processing, donation allocation, and receipting workflows. NOT for standard opportunity creation or direct GiftTransaction DML outside the Gift Entry framework."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "configure gift entry templates NPSP"
  - "set up batch gift entry nonprofit"
  - "gift entry not creating donation records"
  - "how to use processGiftEntries invocable action"
  - "gift entry staging record stuck not promoted"
tags:
  - npsp
  - nonprofit
  - gift-entry
  - donations
  - receipting
inputs:
  - NPSP installed and Advanced Mapping feature enabled in org
  - Org API version (v59.0+ required for GiftEntry staging object; v62.0+ for TaxReceiptStatus)
  - "Intended entry mode: single-gift (default template) or batch (custom template)"
  - Payment gateway integration details if payment processing is in scope
outputs:
  - Configured Gift Entry feature with at least one active template
  - Batch gift entry template for bulk donation processing
  - processGiftEntries invocation pattern that promotes staging records to GiftTransaction, GiftDesignation, and GiftSoftCredit target records
  - Receipting configuration using TaxReceiptStatus on GiftTransaction
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Gift Entry and Processing

This skill activates when a practitioner needs to configure, troubleshoot, or extend the NPSP Gift Entry feature — covering template setup, batch entry, the staging-to-target promotion pipeline via `processGiftEntries`, payment processing, donation allocation, and receipt tracking. It does NOT cover direct Opportunity creation or manual DML against GiftTransaction outside the Gift Entry framework.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Advanced Mapping must be enabled.** Navigate to NPSP Settings > Advanced Mapping and enable it before attempting to activate the Gift Entry feature. Gift Entry will not activate without it.
- **API version constraint.** The `GiftEntry` staging object is available at API v59.0+. The `TaxReceiptStatus` field on `GiftTransaction` is available at API v62.0+. Verify the org's API version before relying on these.
- **Template type constraint.** The Default Gift Entry Template is the only template that supports single-gift entry in the standard Gift Entry UI. Custom templates are batch-only. This is a hard platform constraint, not a configuration choice.
- **Common wrong assumption:** practitioners assume Gift Entry writes directly to Opportunity or GiftTransaction via DML. In reality, it creates a `GiftEntry` staging record first, and the `processGiftEntries` invocable action performs the promotion.

---

## Core Concepts

### Staging Object: GiftEntry

Every gift submitted through Gift Entry creates a `GiftEntry__c` (or `GiftEntry` in API v59.0+ schema) staging record. This record holds all raw gift data — donor, amount, payment method, designations — before the data is validated and committed to target objects. The staging record persists until `processGiftEntries` is explicitly called. If that action is never invoked, the gift lives only in staging and no GiftTransaction, GiftDesignation, or GiftSoftCredit record is ever created.

### processGiftEntries Invocable Action

`processGiftEntries` is the platform action that promotes a `GiftEntry` staging record to its target records:

- `GiftTransaction` — the canonical donation record
- `GiftDesignation` — maps the gift amount to one or more fund/program allocations
- `GiftSoftCredit` — assigns soft credit to relationships (e.g., household members)

The action accepts an `isDryRun` parameter. When `isDryRun=true`, it validates the staging record against all rules and field mappings without committing anything. This is the correct pre-processing gate for large batches. When `isDryRun=false` (default), it commits the records.

### Gift Entry Templates

Templates define the fields, sections, payment options, and allocations presented to gift entry users. Two template contexts exist:

- **Default Gift Entry Template** — system-provided; supports single-gift entry in the standard UI; cannot be deleted; customizable but not replaceable for single-entry mode.
- **Custom templates** — administrator-created; batch-only; define a layout and field set specific to a campaign, fiscal period, or entry team.

Activating the Gift Entry feature requires at minimum that the Default Gift Entry Template is active.

### TaxReceiptStatus and Receipting

`TaxReceiptStatus` on `GiftTransaction` tracks whether a tax receipt has been issued, is pending, or is not applicable. This field is only available at API v62.0+. Orgs on earlier API versions should use a custom field or a separate receipting object.

---

## Common Patterns

### Pattern 1: Single-Gift Entry with Dry Run Validation

**When to use:** A frontline fundraiser is entering one gift at a time, and the org wants validation before committing.

**How it works:**
1. User opens Gift Entry, selects the Default Gift Entry Template.
2. Fills in donor, amount, payment method, and designation fields.
3. Staff clicks "Validate" — this triggers `processGiftEntries` with `isDryRun=true` in the background.
4. Errors (missing required fields, invalid payment method, allocation mismatch) surface immediately.
5. Staff corrects errors, then clicks "Process" — `processGiftEntries` runs with `isDryRun=false`.
6. `GiftTransaction`, `GiftDesignation`, and optionally `GiftSoftCredit` records are created.

**Why not direct DML:** Writing directly to `Opportunity` or `GiftTransaction` bypasses Advanced Mapping field mappings, skips designation logic, and prevents receipt tracking via `TaxReceiptStatus`.

### Pattern 2: Batch Gift Entry for Year-End Processing

**When to use:** Finance team processes hundreds of mailed checks at fiscal year-end.

**How it works:**
1. Admin creates a custom batch template scoped to the year-end campaign.
2. Staff opens Batch Gift Entry, selects the custom template, enters all gifts in the batch grid.
3. Before submitting, runs a dry-run pass via `processGiftEntries` with `isDryRun=true` across all staged records — surfaces any issues.
4. Fixes flagged records in the grid.
5. Submits the batch — `processGiftEntries` runs in sequence for each staging record.
6. All promoted `GiftTransaction` records have `TaxReceiptStatus` set to `PENDING` for downstream receipt generation.

**Why not a data load:** Direct imports via Data Loader bypass Gift Entry entirely. They produce raw `GiftTransaction` records without `GiftDesignation` allocation logic and without the Advanced Mapping field transformations.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single gift entered by a fundraiser | Default Gift Entry Template | Only template type that supports single-entry UI |
| Bulk gifts from a mailer or event | Custom batch template + Batch Gift Entry | Batch templates support multi-record grid; batch processing is more efficient |
| Validating before committing a large batch | processGiftEntries with isDryRun=true | Catches field mapping and allocation errors without any DB commits |
| Receipting for tax purposes | TaxReceiptStatus on GiftTransaction (API v62.0+) | Platform-native receipt status tracking; integrates with downstream receipt flows |
| Org is on API < v62.0 | Custom receipt status field on GiftTransaction | TaxReceiptStatus not available; document the workaround in a skill note |
| Advanced Mapping not yet enabled | Enable Advanced Mapping in NPSP Settings first | Gift Entry feature activation blocked without it |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites.** Confirm NPSP is installed, Advanced Mapping is enabled (NPSP Settings > Advanced Mapping), and the org is on API v59.0+. If Advanced Mapping is off, enable it before proceeding — Gift Entry activation will fail otherwise.
2. **Activate Gift Entry.** In NPSP Settings > Gift Entry, toggle the feature on. Confirm the Default Gift Entry Template is listed as active.
3. **Configure the Default Gift Entry Template for single-gift entry.** Add required fields (donor lookup, amount, payment method, fund designation), configure payment gateway if applicable, and save.
4. **Create a custom batch template if batch entry is needed.** Set the template name, batch entry fields, allocation default, and link to the relevant campaign or fund.
5. **Test with isDryRun=true.** Submit a test staging record and invoke `processGiftEntries` with `isDryRun=true`. Confirm validation messages match expectations and no target records are created.
6. **Process and verify target records.** Run `processGiftEntries` with `isDryRun=false` on the test record. Confirm `GiftTransaction`, `GiftDesignation`, and `GiftSoftCredit` records are created with correct field values per Advanced Mapping rules.
7. **Configure receipting.** If on API v62.0+, set the default `TaxReceiptStatus` value on processed `GiftTransaction` records and wire up any receipt automation.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Advanced Mapping is enabled in NPSP Settings
- [ ] Default Gift Entry Template is active and has required fields configured
- [ ] Custom batch templates (if any) are batch-only and correctly scoped
- [ ] processGiftEntries dry-run pass executes without errors on test staging records
- [ ] processGiftEntries full-run creates GiftTransaction, GiftDesignation, and GiftSoftCredit records
- [ ] TaxReceiptStatus is set on GiftTransaction records (API v62.0+ only; document workaround if on earlier version)
- [ ] No GiftEntry staging records remain in a permanently unprocessed state after testing

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Advanced Mapping gate** — Gift Entry feature activation silently fails or produces an error if Advanced Mapping has never been enabled. Many practitioners skip this step assuming NPSP installs with it on by default. It does not. Enable it first, every time.
2. **Staging records persist if processGiftEntries is never called** — There is no automatic cleanup of `GiftEntry` staging records. If an integration or custom flow creates staging records but never invokes `processGiftEntries`, the gifts accumulate in staging indefinitely and never appear as GiftTransactions in reporting.
3. **Default template is the only single-entry template** — Attempting to use a custom template for single-gift entry produces no UI entry point. Custom templates surface only in Batch Gift Entry. This is a hard constraint, not a missing configuration.
4. **isDryRun does not roll back — it never commits** — `isDryRun=true` is a validation-only pass; it does not create records and does not need a rollback. Some practitioners apply transaction guards around dry-run calls, which adds no value and can introduce lock contention.
5. **TaxReceiptStatus API version dependency** — Querying `TaxReceiptStatus` on `GiftTransaction` in orgs below API v62.0 returns an "invalid field" error. Always check the org's API version before referencing this field in Apex, Flow, or SOQL.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Active Default Gift Entry Template | Configured single-entry template with required fields and payment options |
| Custom Batch Gift Entry Template | Batch-only template linked to a campaign or fiscal period |
| processGiftEntries invocation pattern | Documented dry-run and commit invocation sequence with error handling |
| GiftTransaction records | Promoted donation records with designation and soft credit allocations |
| TaxReceiptStatus configuration | Receipting status field wired to downstream automation (API v62.0+ orgs) |

---

## Related Skills

- `recurring-donations-setup` — Configure NPSP recurring donations, which feed staging records into Gift Entry differently than one-time gifts
- `npsp-data-model` — Understand the full NPSP object graph that Gift Entry writes into
- `gift-entry-and-processing` is the upstream step before any `care-program-management` or financial reporting workflows that consume GiftTransaction records
