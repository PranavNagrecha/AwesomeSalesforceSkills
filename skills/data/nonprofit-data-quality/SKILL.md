---
name: nonprofit-data-quality
description: "Use this skill when standardizing addresses, detecting duplicate household Contacts, running NCOA processing, or improving data hygiene in an NPSP org. Triggers: address verification NPSP, household duplicate detection, NCOA update nonprofit, data hygiene NPSP. NOT for generic Salesforce data quality, Nonprofit Cloud (NPC) data quality, or standard Account/Contact deduplication outside NPSP."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "NPSP household contacts have duplicate entries and standard duplicate rules are not catching them correctly"
  - "nonprofit org mailing addresses are outdated and need NCOA processing to find relocated constituents"
  - "address verification was set up in NPSP but historical contact records still show unverified addresses"
  - "merging duplicate household contacts loses donation rollup totals because standard Account merge was used"
  - "nonprofit data team needs to standardize address fields across thousands of constituent records before a fundraising campaign"
tags:
  - npsp
  - nonprofit-data-quality
  - address-standardization
  - ncoa
  - duplicate-detection
  - household-accounts
  - data-hygiene
inputs:
  - "NPSP org with Nonprofit Success Pack installed, version confirmed, Household Account model active"
  - "Address verification integration configured (Cicero, Google Geocoding, or SmartyStreets)"
  - "List of affected Contact and npsp__Address__c records scoped for remediation"
  - "Insights Platform Data Integrity license confirmation (required for NCOA only)"
  - "Configured NPSP Contact Matching Rules (in NPSP Settings > Contacts tab)"
outputs:
  - "Verified and standardized npsp__Address__c records with correct geocoding and delivery point codes"
  - "Merged duplicate household Contacts with recalculated NPSP rollup totals"
  - "NCOA processing run report with address corrections and deceased/undeliverable flags"
  - "Data hygiene audit report showing address verification coverage percentage"
  - "Configured duplicate detection rules scoped to NPSP Contact Matching Rules"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Nonprofit Data Quality

Use this skill to standardize constituent addresses, detect and merge duplicate household Contacts, run National Change of Address (NCOA) processing, and perform ongoing data hygiene in an NPSP org. It activates when data quality problems are rooted in NPSP's household address model, NPSP-specific duplicate detection, or nonprofit-specific enrichment services — not generic Salesforce data tools.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm NPSP version installed (`npsp__` namespace) and that the Household Account model is active — Individual Account model orgs have different address behavior.
- Confirm which address verification integration is configured under NPSP Settings > Address Verification (Cicero, Google Geocoding API, or SmartyStreets). Each has distinct field mappings and rate limits.
- For NCOA specifically: confirm whether the org has the separately licensed Insights Platform Data Integrity add-on. NCOA is not available in base NPSP. It is also incompatible with Agentforce Nonprofit orgs.
- Check NPSP Contact Matching Rules settings — these govern duplicate detection within the NPSP framework and are separate from standard Salesforce Duplicate Rules.

---

## Core Concepts

### NPSP Address Object Model

NPSP stores addresses as `npsp__Address__c` custom objects, not directly on the Contact or Account. Each `npsp__Address__c` record is linked to a Household Account via `npsp__Household_Account__c`. A household can have multiple address records (Home, Seasonal, Work, Other), and one is designated as the "Default" via `npsp__Default_Address__c = true`. NPSP then copies the default address fields to the Household Account and to each member Contact's mailing address fields via a scheduled batch job or trigger.

This architecture means address standardization must operate on `npsp__Address__c` records — not directly on Contact or Account mailing fields. Direct edits to Contact mailing fields are overwritten by NPSP's address management batch.

### Address Verification Integration

NPSP integrates with third-party address verification services (Cicero, Google Geocoding, SmartyStreets). Once configured, the service automatically verifies addresses on **newly created or updated** `npsp__Address__c` records. It does **not** retroactively verify records created before the integration was set up. Orgs that enable address verification after initial data load must run the `ADDR_Addresses_TDTM` batch manually (via the NPSP Address Settings or Apex execute) to process historical records.

Verification populates fields like `npsp__Verified__c`, `npsp__Verification_Status__c`, `npsp__Address_Type__c`, and geocoding latitude/longitude. Unverified records have `npsp__Verified__c = false`.

### NPSP Contact Matching Rules and Duplicate Detection

Standard Salesforce Duplicate Rules operate on standard Contact fields and use standard Account merge. In an NPSP org, standard Account merge does **not** recalculate NPSP rollup fields (total donations, last gift date, etc.) and does not fire NPSP Apex triggers. For household duplicate merging, NPSP provides the **NPSP Contact Merge** Flow (or Visualforce page in older versions) specifically to ensure triggers fire and rollups recalculate.

NPSP Contact Matching Rules (under NPSP Settings > Contacts) are configured separately from Salesforce Duplicate Rules and are used by the NPSP Data Importer for duplicate detection during bulk imports.

### NCOA Processing via Insights Platform Data Integrity

National Change of Address (NCOA) processing matches constituent mailing addresses against the USPS database to find households that have relocated or are undeliverable. In Salesforce, NCOA for nonprofits is provided by the **Insights Platform Data Integrity** add-on — a separately licensed premium subscription managed through the Insights Platform. It is **not** a standard NPSP feature and is **not** compatible with Agentforce Nonprofit orgs (the add-on conflicts with Agentforce Nonprofit's data model expectations). NCOA processing updates `npsp__Address__c` records with corrections and flags undeliverable or deceased records.

---

## Common Patterns

### Pattern 1: Mass Address Verification for Historical Records

**When to use:** The org enabled NPSP address verification after initial data load. Thousands of `npsp__Address__c` records have `npsp__Verified__c = false` and need retroactive verification.

**How it works:**
1. Navigate to NPSP Settings > Address Settings (or run via Developer Console).
2. Execute the `ADDR_Addresses_TDTM` batch class to process all unverified `npsp__Address__c` records against the configured verification service.
3. Monitor with the batch status. Processing is subject to external API callout limits — for large volumes, run in off-hours and track the batch with `AsyncApexJob` queries.
4. After the batch completes, query for records still showing `npsp__Verified__c = false` and `npsp__Verification_Status__c` for error details.

**Why not the alternative:** Updating Contact or Account mailing fields directly does not go through the `npsp__Address__c` layer and will be overwritten on the next NPSP address synchronization cycle.

### Pattern 2: NPSP Contact Merge for Duplicate Households

**When to use:** Duplicate Contact records exist in the same or different Household Accounts and must be merged without losing donation history or rollup totals.

**How it works:**
1. Identify duplicates via a SOQL query using NPSP Contact Matching criteria, or via a report.
2. Navigate to the winning Contact record and use the **NPSP Contact Merge** button (installed by NPSP on the Contact record page, or invoke via the `/apex/NPSP__merge` page).
3. Select the losing Contact(s) to merge into the winner — NPSP Contact Merge fires NPSP Apex triggers (`TDTM_Runnable` handlers) that recalculate Household rollups and consolidate relationship records.
4. Verify post-merge: `npo02__TotalOppAmount__c`, `npo02__LastOppAmount__c`, and `npo02__NumberOfClosedOpps__c` on the Household Account should reflect all merged records.

**Why not the alternative:** Salesforce's native **Merge Contacts** (from the Contacts list view or Account detail) bypasses NPSP's trigger framework. Rollup fields will not recalculate and `npe4__Relationship__c` records may be orphaned.

### Pattern 3: Configuring NPSP Contact Matching Rules for Ongoing Duplicate Prevention

**When to use:** The org is importing new constituents regularly and needs to prevent duplicate Contacts from being created during bulk loads or form submissions.

**How it works:**
1. In NPSP Settings > Contacts, configure the Contact Matching Rule to match on a combination of First Name, Last Name, Email, and/or Phone — enough specificity to avoid false positives while catching true duplicates.
2. Enable the matching rule for the NPSP Data Importer so it checks staging rows against existing Contacts before creating new records.
3. For real-time form submissions (e.g., Classy, Luminate), configure matching at the integration layer before records reach Salesforce.
4. Do not rely on standard Salesforce Duplicate Rules as the primary gate for NPSP data — they operate after the Contact is created and do not block the NPSP Data Importer.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Address verification enabled after initial data load | Run `ADDR_Addresses_TDTM` batch to process historical `npsp__Address__c` records | Automatic verification only fires on newly created/updated records |
| Merging duplicate household Contacts | Use NPSP Contact Merge Flow/page | Standard Account merge bypasses NPSP triggers and rollups break |
| NCOA update for nationwide mailing campaign | Insights Platform Data Integrity add-on | Only licensed path for USPS NCOA in Salesforce/NPSP |
| Preventing duplicates during bulk import | NPSP Contact Matching Rules + NPSP Data Importer | Works within NPSP's staging object model |
| Duplicate prevention for real-time web submissions | Match at integration layer before insert | NPSP matching only applies during Data Importer batch |
| Standardizing address format (not verification) | Formula fields or Flow on `npsp__Address__c` trigger | Formatting is distinct from verification; do not use standard account address fields |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Clarify scope** — Determine whether the task is address standardization, duplicate Contact merging, NCOA processing, or general data hygiene. Each requires a different toolchain and licensing check. Confirm NPSP is installed and the Household Account model is active.
2. **Audit current state** — Query `npsp__Address__c` for `npsp__Verified__c = false` count; query Contacts for duplicate matches using NPSP Contact Matching Report; check Insights Platform Data Integrity license status if NCOA is requested.
3. **Resolve address verification gaps** — If historical records are unverified, execute the `ADDR_Addresses_TDTM` batch class from NPSP Settings > Address Settings or Developer Console. Monitor the `AsyncApexJob` batch and review verification failures.
4. **Merge duplicate Contacts** — Use the NPSP Contact Merge button or `/apex/NPSP__merge` page — never the native Salesforce merge — to merge each duplicate pair. Confirm rollup fields recalculate on the Household Account post-merge.
5. **Run NCOA processing** (if licensed) — Initiate NCOA job through Insights Platform Data Integrity, review address correction output, flag deceased and undeliverable records, and update `npsp__Address__c` with corrections.
6. **Validate results** — Query updated `npsp__Address__c` records for verification status, confirm rollup fields on affected Household Accounts, and generate a data hygiene coverage report showing before/after counts.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All `npsp__Address__c` updates were made on the `npsp__Address__c` object — not directly on Contact or Account mailing fields
- [ ] All Contact merges used NPSP Contact Merge — rollup fields (`npo02__TotalOppAmount__c`, etc.) verified post-merge
- [ ] Address verification batch confirmed completed and `npsp__Verified__c` coverage has improved
- [ ] NCOA step only attempted if Insights Platform Data Integrity license is confirmed active (and org is not Agentforce Nonprofit)
- [ ] NPSP Contact Matching Rules reviewed and appropriate strictness configured to prevent future duplicates
- [ ] No standard Salesforce Duplicate Rules or native Account merge used as primary mechanisms

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Address verification does not back-fill historical records** — Setting up an address verification integration (Cicero/Google/SmartyStreets) under NPSP Address Settings only validates addresses created or updated after that point. Records loaded before setup remain unverified. The fix is to manually run the `ADDR_Addresses_TDTM` batch job to reprocess existing `npsp__Address__c` records.

2. **NCOA requires a separately licensed Insights Platform Data Integrity add-on** — NCOA is not included in NPSP or in any standard Salesforce license tier. It is a premium add-on through the Insights Platform. Additionally, Insights Platform Data Integrity is explicitly incompatible with Agentforce Nonprofit orgs and should not be recommended for orgs using that product.

3. **Native Salesforce Contact/Account merge breaks NPSP rollups** — Using the standard Salesforce merge (from Contacts list view, Account detail, or via `Database.merge()` in Apex) does not invoke NPSP's TDTM trigger framework. Rollup fields on the Household Account will be stale or incorrect until a manual recalculation is triggered. Always use the NPSP Contact Merge Flow or `/apex/NPSP__merge` page for household Contact deduplication.

4. **Direct edits to Contact mailing address fields are overwritten** — If users or automated processes edit Contact mailing address fields (MailingStreet, MailingCity, etc.) directly, NPSP's address management sync will overwrite those changes on the next synchronization pass with the values from the linked default `npsp__Address__c` record. All address edits must be made on the `npsp__Address__c` record.

5. **Seasonal addresses bypass standard verification flow** — Seasonal `npsp__Address__c` records (those with `npsp__Seasonal_Start_Month__c` populated) are activated by a scheduled batch, not by real-time trigger. Address verification does not automatically re-fire when a seasonal address becomes the active default — the seasonal activation batch sets the default but does not invoke the verification callout.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Address verification coverage report | SOQL query results showing count and percentage of `npsp__Address__c` records with `npsp__Verified__c = true` before and after remediation |
| NPSP Contact Merge run log | Record of which Contact records were merged, who the winner was, and confirmed rollup field values post-merge |
| NCOA processing output | Address correction report from Insights Platform Data Integrity showing updated, undeliverable, and deceased flags |
| Data hygiene remediation plan | Prioritized list of address records requiring manual review after batch processing |

---

## Related Skills

- `data/constituent-data-migration` — Use before this skill when loading new constituents into NPSP; address quality is best enforced at import time
- `data/npsp-data-model` — Use alongside this skill to understand the full `npsp__Address__c` object structure and relationships before writing queries or Flows
- `data/large-scale-deduplication` — Use for deduplication at scale across the full org; this skill handles NPSP-specific household Contact merging specifically
