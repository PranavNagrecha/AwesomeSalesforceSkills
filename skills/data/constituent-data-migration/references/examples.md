# Examples — Constituent Data Migration

## Example 1: Migrating Constituents from Excel into NPSP with Household Pairing

**Context:** A regional food bank is migrating 12,000 constituent records from an Excel-based donor database into a new NPSP org. Source data includes individual donors, couples in shared households, home addresses, and 3 years of giving history. The organization has no prior Salesforce data — this is a net-new load.

**Problem:** The data team initially planned to use Data Loader to insert Contact records directly, following the same process they used for a standard Salesforce org migration. Without this skill's guidance, they would bypass NPSP's TDTM trigger framework, producing 12,000 one-contact orphaned households, blank rollup fields on every Account, and no Address records.

**Solution:**

Prepare the staging CSV with the correct `npsp__DataImport__c` field mapping:

```
npsp__Contact1_Firstname__c, npsp__Contact1_Lastname__c, npsp__Contact1_Personal_Email__c,
npsp__Contact2_Firstname__c, npsp__Contact2_Lastname__c, npsp__Contact2_Personal_Email__c,
npsp__HH_Street__c, npsp__HH_City__c, npsp__HH_State__c, npsp__HH_Zip__c,
npsp__Donation_Amount__c, npsp__Donation_Date__c, npsp__Donation_Stage__c
```

For a married couple (John and Mary Smith) at the same address:

```
John, Smith, john@smithfamily.net, Mary, Smith, mary@smithfamily.net,
123 Elm St, Portland, OR, 97201,
500.00, 2024-12-01, Closed Won
```

This single row creates: Contact for John, Contact for Mary, one Smith Household Account, one Address record linked to both contacts, and one Opportunity for $500 linked to the Household Account.

Upload the CSV to `npsp__DataImport__c` via Data Loader (staging object only). Then process via the NPSP Data Importer UI: **App Launcher > NPSP Data Import > Import**.

**Why it works:** The NPSP Data Importer invokes the `BDI_DataImport` Apex batch class, which applies Contact Matching Rules, creates Household Accounts, fires TDTM triggers, and populates all rollup fields correctly. The entire household — both contacts, address, account, and donation — is created atomically from one staging row.

---

## Example 2: Migrating Household Relationships from a Legacy CRM with Existing Contacts

**Context:** A community foundation has been on NPSP for two years with 8,000 Contact records already loaded. They are migrating an additional 3,000 contacts from a legacy CRM. Some of the new contacts are spouses or household members of existing contacts; others are new individuals not yet in the org.

**Problem:** Without correct matching rule configuration, the import will either create duplicates (if matching is too strict) or incorrectly merge distinct individuals with the same name (if matching is too loose). Household pairing for new contacts married to existing contacts requires careful staging row design.

**Solution:**

Step 1 — Review and tune Contact Matching Rules before the run:

```
NPSP Settings > Duplicate Management > Contact Matching Rule
Default: Match on First Name + Last Name + Email
Recommended for this scenario: Match on First Name + Last Name + Email + Mailing Zip
(Reduces false positives for common names)
```

Step 2 — For a new Contact (Jane Doe) who is the spouse of an existing Contact (Robert Doe, already in the org with Account ID `0011x000001ABCDE`), structure the staging row as:

```
npsp__Contact1_Firstname__c = Jane
npsp__Contact1_Lastname__c = Doe
npsp__Contact1_Personal_Email__c = jane@doefamily.com
npsp__HH_Account_Id__c = 0011x000001ABCDE   ← existing Household Account ID
```

By providing `npsp__HH_Account_Id__c`, NPSP links the new Contact into Robert's existing Household Account rather than creating a new one. The existing Account's rollup fields update automatically after processing.

Step 3 — Run a pilot batch of 100 rows. Use the NPSP Data Importer results screen to verify: (a) no unexpected duplicates, (b) new contacts appear in the correct household, (c) rollup fields on existing households have recalculated.

**Why it works:** Providing the existing Household Account ID explicitly on the staging row short-circuits NPSP's household-creation logic and attaches the new Contact to the correct existing Account. Without this, NPSP would create a new one-contact Jane Doe Household Account even if Robert's household already exists.

---

## Anti-Pattern: Using the Standard Data Import Wizard or Data Loader for NPSP Contacts

**What practitioners do:** Use the Salesforce Data Import Wizard (Setup > Data Import Wizard > Contacts and Leads) or Data Loader targeting the `Contact` object to bulk-import constituent records into an NPSP org, following the same process used in non-NPSP orgs.

**What goes wrong:**
- NPSP's TDTM triggers do not fire when Contacts are inserted via the standard API path.
- Each inserted Contact generates a new one-contact Household Account, fragmenting household groupings.
- Household Account rollup fields (total giving, last gift date, number of gifts) remain blank for all imported Contacts.
- `npsp__Address__c` records are not created; address data on Contact is populated but not connected to the NPSP address model.
- `npe4__Relationship__c` records linking household members are not created.
- Remediating these issues requires identifying and deleting all orphaned households, re-running rollups, and re-importing data through the correct path — a multi-day effort for large datasets.

**Correct approach:** Always use the NPSP Data Importer with `npsp__DataImport__c` as the staging object. For automated pipelines, upsert to `npsp__DataImport__c` and invoke `BDI_DataImport` via Apex batch.
