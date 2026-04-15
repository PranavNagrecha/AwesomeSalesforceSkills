# LLM Anti-Patterns — Nonprofit Data Quality

Common mistakes AI coding assistants make when generating or advising on Nonprofit Data Quality.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Standard Salesforce Duplicate Rules as the NPSP Duplicate Prevention Gate

**What the LLM generates:** Advice to create a standard Salesforce Duplicate Rule on the Contact object with matching criteria on First Name + Last Name + Email, enabling it with "Block" or "Alert" action, and treating this as sufficient duplicate prevention for an NPSP org.

**Why it happens:** Standard Salesforce duplicate detection is well-documented and appears prominently in training data. LLMs do not distinguish between the standard platform duplicate framework and NPSP's separate Contact Matching Rules system, which operates within the NPSP Data Importer's batch staging model.

**Correct pattern:**

```
For import-time duplicate prevention in NPSP:
1. Configure NPSP Contact Matching Rules under NPSP Settings > Contacts
2. Enable matching for the NPSP Data Importer (checks npsp__DataImport__c staging rows before insert)
3. Standard Salesforce Duplicate Rules may supplement but cannot replace NPSP matching for Importer-based loads
4. For non-Importer inserts (forms, APIs), implement duplicate detection at the integration layer
```

**Detection hint:** Look for recommendations that mention only "Duplicate Rule" and "Duplicate Management" without referencing `NPSP Settings > Contacts > Contact Matching Rule`.

---

## Anti-Pattern 2: Using Native Salesforce Contact or Account Merge for NPSP Household Deduplication

**What the LLM generates:** Instructions to merge duplicate Contacts using the standard Salesforce "Merge Contacts" button in the Contacts list view, or Apex code using `Database.merge(winnerContact, losingContactIds)`.

**Why it happens:** `Database.merge()` is the standard Salesforce merge mechanism and is thoroughly documented. LLMs are not trained to know that NPSP's TDTM trigger framework is bypassed by native merge, and that rollup fields do not recalculate without the NPSP handler chain.

**Correct pattern:**

```
For NPSP household Contact merging:
1. Navigate to the winning Contact record
2. Use the NPSP Contact Merge button (NPSP-installed action) or go to /apex/NPSP__merge?id={WinnerContactId}
3. Select losing Contact(s) and complete merge via NPSP merge page
4. Verify Household Account rollup fields (npo02__TotalOppAmount__c, etc.) after merge

NEVER use:
- Salesforce Contacts list view "Merge Contacts"
- Database.merge() without explicitly invoking NPSP rollup recalculation afterward
- Account detail page merge for NPSP Household Accounts
```

**Detection hint:** Any mention of `Database.merge()` or the standard Contacts list view merge in an NPSP context without a rollup recalculation step should be flagged.

---

## Anti-Pattern 3: Recommending Standard Salesforce NCOA or Treating NCOA as a Base NPSP Feature

**What the LLM generates:** Advice that NCOA processing can be enabled in NPSP Settings, or that there is a standard Salesforce NCOA feature. Sometimes generates fictional menu paths like "NPSP Settings > Data Integrity > NCOA" or recommends enabling a non-existent "NCOA sync" toggle.

**Why it happens:** NCOA is a well-known nonprofit data concept and LLMs associate it with NPSP/Salesforce nonprofit functionality. The actual mechanism (Insights Platform Data Integrity — a separately licensed premium add-on) is obscure enough that models hallucinate simpler activation paths.

**Correct pattern:**

```
NCOA in Salesforce NPSP requires:
1. Insights Platform Data Integrity — a SEPARATELY LICENSED premium add-on
2. Confirm the license under Setup > Company Information > Licenses
3. Insights Platform Data Integrity is INCOMPATIBLE with Agentforce Nonprofit orgs
4. Without the add-on, NCOA must be processed externally (third-party service) and 
   results imported back to npsp__Address__c records via Data Loader
```

**Detection hint:** Any response that says NCOA can be "configured" or "enabled" in NPSP without mentioning the Insights Platform Data Integrity add-on license.

---

## Anti-Pattern 4: Editing Contact Mailing Address Fields Directly Instead of npsp__Address__c

**What the LLM generates:** Flows, Apex triggers, or data loader instructions that update `Contact.MailingStreet`, `Contact.MailingCity`, `Contact.MailingState`, and `Contact.MailingPostalCode` directly for address standardization or verification purposes.

**Why it happens:** Contact address fields are the standard Salesforce address fields and appear in most Salesforce documentation. LLMs do not know that NPSP overrides these fields with values from the linked `npsp__Address__c` object on the next synchronization event, making direct Contact field updates ephemeral.

**Correct pattern:**

```
In NPSP orgs, ALL address updates must target npsp__Address__c records:

// Correct: update the npsp__Address__c record
npsp__Address__c addr = [SELECT Id, npsp__MailingStreet__c FROM npsp__Address__c WHERE Id = :addressId];
addr.npsp__MailingStreet__c = '123 Main St';
update addr;

// WRONG: this will be overwritten by NPSP sync
Contact c = [SELECT Id, MailingStreet FROM Contact WHERE Id = :contactId];
c.MailingStreet = '123 Main St';
update c;
```

**Detection hint:** Any Flow, Apex, or data loader job that targets `Contact.MailingStreet/City/State/PostalCode` for address standardization in an NPSP org.

---

## Anti-Pattern 5: Triggering Address Verification via Direct API Callout Rather Than NPSP's TDTM Framework

**What the LLM generates:** Custom Apex code that calls a geocoding API (Google Maps, SmartyStreets) directly in a trigger or batch, updates address fields on Contact, and bypasses the NPSP `ADDR_Addresses_TDTM` handler.

**Why it happens:** Custom API callout patterns are common in Salesforce training data. LLMs generate this pattern because it works generically, without knowing that NPSP has a built-in address verification integration framework that handles callout dispatch, response parsing, field mapping, and retry logic within the `ADDR_Addresses_TDTM` handler chain.

**Correct pattern:**

```
Use NPSP's built-in address verification framework:
1. Configure the verification service under NPSP Settings > Address Settings
   (Cicero, Google Geocoding API, or SmartyStreets)
2. NPSP's ADDR_Addresses_TDTM handler dispatches callouts on npsp__Address__c create/update
3. For historical records, run: Database.executeBatch(new ADDR_Addresses_TDTM(), 25)
4. Custom callout Apex that bypasses TDTM will conflict with NPSP's handler and may 
   cause double-callouts or field value conflicts
```

**Detection hint:** Apex code that imports a geocoding library or makes direct `Http` callouts in a Contact or Address trigger context, without referencing `ADDR_Addresses_TDTM` or the NPSP verification settings.

---

## Anti-Pattern 6: Recommending npsp__Address__c Bulk Updates Without Considering Callout Limits

**What the LLM generates:** Instructions to run a Data Loader update on all `npsp__Address__c` records to trigger address verification, using the maximum batch size (200 records per batch in standard Bulk API).

**Why it happens:** Bulk API batch size of 200 is standard guidance. LLMs do not know that NPSP's address verification fires an external HTTP callout per address record, and that Salesforce enforces a maximum of 100 callouts per Apex transaction.

**Correct pattern:**

```
When triggering address verification via batch:
- Use Database.executeBatch(new ADDR_Addresses_TDTM(), 25) 
- Batch size of 25 keeps callouts well within the 100-callout-per-transaction limit
- Monitor AsyncApexJob for failures — failed batches often indicate API rate limits 
  on the external verification service
- For very large orgs (100k+ addresses), run during off-hours and in phases
```

**Detection hint:** Any recommendation to update `npsp__Address__c` records in batches of 200 or larger when address verification is configured.
