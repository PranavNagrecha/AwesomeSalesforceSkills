# Gift Entry and Processing — Work Template

Use this template when configuring, troubleshooting, or extending NPSP Gift Entry.

## Scope

**Skill:** `gift-entry-and-processing`

**Request summary:** (fill in what the user asked for — e.g., "configure batch gift entry for year-end campaign", "troubleshoot staging records not promoting to GiftTransaction")

---

## Context Gathered

Answer these before starting any work:

- **NPSP installed?** Yes / No
- **Advanced Mapping enabled?** (NPSP Settings > Advanced Mapping) Yes / No — if No, enable it first
- **Org API version:** _______ (must be v59.0+ for GiftEntry staging object; v62.0+ for TaxReceiptStatus)
- **Entry mode needed:** Single-gift only / Batch only / Both
- **Custom batch templates required?** Yes / No — if Yes, describe scope: _______
- **Payment gateway in scope?** Yes / No — if Yes, gateway name: _______
- **Receipting required?** Yes / No — if Yes, confirm API version >= 62.0 for TaxReceiptStatus

---

## Pre-Work Checklist

Complete these before making any configuration changes:

- [ ] Advanced Mapping is enabled in NPSP Settings
- [ ] Gift Entry feature is active in NPSP Settings > Gift Entry
- [ ] Default Gift Entry Template is present and active
- [ ] Org API version confirmed and documented above
- [ ] No existing custom templates conflict with the proposed configuration

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Single-gift entry with Default Gift Entry Template
- [ ] Batch gift entry with custom template
- [ ] Both single and batch (requires separate template configurations)
- [ ] Troubleshooting stuck staging records (use processGiftEntries dry run + status audit)
- [ ] Receipting configuration (TaxReceiptStatus or custom field workaround)

**Reason for chosen pattern:** (explain why this pattern fits the request)

---

## Configuration Steps

### Step 1: Enable Prerequisites

- [ ] Advanced Mapping enabled
- [ ] Gift Entry feature activated
- [ ] API version documented

### Step 2: Default Gift Entry Template (Single-Gift Entry)

- [ ] Required fields added: Donor lookup, Gift Amount, Payment Method, Fund Designation
- [ ] Optional fields added per org requirements: ______________________
- [ ] Payment gateway configured (if in scope)
- [ ] Template saved and active

### Step 3: Custom Batch Template (Batch Gift Entry — if required)

- [ ] Template name: _______________________
- [ ] Batch entry fields defined: _______________________
- [ ] Default fund designation set: _______________________
- [ ] Campaign link configured (if applicable): _______________________
- [ ] Template saved and active

### Step 4: Test with isDryRun=true

- [ ] Test staging record created
- [ ] processGiftEntries called with isDryRun=true
- [ ] No validation errors returned
- [ ] Confirmed: no GiftTransaction, GiftDesignation, or GiftSoftCredit records created during dry run

### Step 5: Full Commit Test

- [ ] processGiftEntries called with isDryRun=false on test staging record
- [ ] GiftTransaction record created with correct Amount, PaymentMethod, Donor
- [ ] GiftDesignation record created with correct fund allocation
- [ ] GiftSoftCredit record created (if household/relationship credit applies)
- [ ] No staging record remains in Imported status after processing

### Step 6: Receipting Configuration

- [ ] API version >= 62.0? If Yes: TaxReceiptStatus field used on GiftTransaction
- [ ] API version < 62.0? If Yes: Custom receipt status field documented; migration path noted
- [ ] Receipt automation wired to GiftTransaction (Flow, Process Builder, or Apex trigger)

---

## processGiftEntries Invocation Reference

```json
// Dry run (validation only — no records created)
POST /services/data/v59.0/actions/custom/flow/GiftEntry_ProcessGiftEntries
{
  "inputs": [{ "giftEntryId": "<staging_record_id>", "isDryRun": true }]
}

// Full commit
POST /services/data/v59.0/actions/custom/flow/GiftEntry_ProcessGiftEntries
{
  "inputs": [{ "giftEntryId": "<staging_record_id>", "isDryRun": false }]
}
```

---

## Post-Work Verification

- [ ] All staging records from test runs have been processed (none left in Imported status)
- [ ] GiftTransaction records appear correctly in fundraising reports
- [ ] GiftDesignation allocations are correct for all test gifts
- [ ] Receipting status is set correctly on GiftTransaction records
- [ ] Gift Entry UI tested by an end user (not just admin)

---

## Notes and Deviations

(Record any deviations from the standard pattern and why — e.g., API version workarounds, custom template variations, payment gateway edge cases)

---

## Official Sources Referenced

- Salesforce Help — Configure Gift Entry (NPSP): https://help.salesforce.com/s/articleView?id=sf.npsp_gift_entry.htm
- Salesforce Fundraising Developer Guide — processGiftEntries Action: https://developer.salesforce.com/docs/atlas.en-us.fundraising_dev.meta/fundraising_dev/fundraising_gift_entry_api_overview.htm
