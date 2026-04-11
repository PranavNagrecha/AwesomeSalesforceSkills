# LLM Anti-Patterns — Constituent Data Migration

Common mistakes AI coding assistants make when generating or advising on constituent data migration in NPSP.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Advising Data Loader to Import Contacts Directly into NPSP

**What the LLM generates:** Instructions telling the practitioner to use Data Loader targeting the `Contact` sObject to bulk-insert constituent records, or a Data Loader job definition with `Contact` as the target object.

**Why it happens:** Data Loader is the canonical Salesforce bulk import tool. LLMs trained on general Salesforce content default to recommending it for any bulk contact load, without awareness that NPSP's TDTM trigger framework requires a different entry point.

**Correct pattern:**

```
Stage records in npsp__DataImport__c via Data Loader (targeting the staging object, not Contact).
Then process via the NPSP Data Importer UI or BDI_DataImport Apex batch class.
Never insert Contact records directly for NPSP constituent migration.
```

**Detection hint:** Look for `sObject: Contact` or `targetObject: Contact` in a Data Loader configuration, or any instruction to "use Data Loader to import contacts" in an NPSP context.

---

## Anti-Pattern 2: Recommending the Salesforce Data Import Wizard for NPSP Contacts

**What the LLM generates:** A workflow that uses Setup > Data Import Wizard > Contacts and Leads to import constituent records into an NPSP org.

**Why it happens:** The Data Import Wizard is a native Salesforce tool that appears in Setup and is often mentioned in general Salesforce documentation for contact imports. LLMs conflate "standard Salesforce" guidance with "NPSP" guidance.

**Correct pattern:**

```
Use the NPSP Data Importer (App Launcher > NPSP Data Import), not the standard Data Import Wizard.
The NPSP Data Importer processes npsp__DataImport__c staging records through the BDI_DataImport
Apex batch, which fires NPSP TDTM triggers and creates Household Accounts, Addresses, and
Relationships correctly.
```

**Detection hint:** References to "Setup > Data Import Wizard" or "Contacts and Leads import" in an NPSP migration workflow.

---

## Anti-Pattern 3: Creating Separate Staging Rows for Each Household Member

**What the LLM generates:** A CSV or import mapping that creates one `npsp__DataImport__c` row per Contact, with two separate rows for a married couple who should share a household.

**Why it happens:** The "one record per contact" pattern is intuitive and matches standard CRM import conventions. LLMs unfamiliar with NPSP's Contact1/Contact2 pairing model generate this structure by default.

**Correct pattern:**

```
Place both contacts in the same household on a SINGLE npsp__DataImport__c row.
Use Contact1 fields (npsp__Contact1_Firstname__c, npsp__Contact1_Lastname__c, etc.)
for the primary contact and Contact2 fields for the second household member.
Two rows = two separate households. One row with Contact1+Contact2 = one shared household.
```

**Detection hint:** A CSV where each row has only Contact1 fields populated and Contact2 fields are always blank, even when the source data includes household pairs. Or a mapping guide that instructs "one row per contact."

---

## Anti-Pattern 4: Assuming Household Account Names Can Be Set via the Import

**What the LLM generates:** A staging CSV that includes an Account Name column mapped to a Household Account name field, with the expectation that NPSP will use that name when creating the Account.

**Why it happens:** In standard Salesforce, Account Name is a writeable field on Account and can be set via import. LLMs apply this general knowledge to NPSP without accounting for NPSP's Household Naming automation.

**Correct pattern:**

```
NPSP auto-generates Household Account names using the Household Naming Format configured in
NPSP Settings > Household > Household Naming. The import cannot override this.
If custom household names must be preserved, configure the Household Naming Format before
migration, or run a post-import batch update to Account.Name after the NPSP import completes.
```

**Detection hint:** A staging CSV that includes a column like `Account_Name` or `npsp__HH_Account_Name__c` mapped to a free-text household name, with a comment suggesting this will be used to name the created Account.

---

## Anti-Pattern 5: Ignoring Contact Matching Rules and Running Full Migration Without a Pilot Batch

**What the LLM generates:** A migration plan that proceeds directly from "prepare the CSV" to "run the full import of all 50,000 records" without a pilot batch step, or a plan that does not mention reviewing or configuring Contact Matching Rules.

**Why it happens:** LLMs optimize for conciseness and often skip validation steps. Contact Matching Rules are an NPSP-specific configuration concept that general data migration guidance does not cover.

**Correct pattern:**

```
Before running a full constituent migration:
1. Review NPSP Settings > Duplicate Management > Contact Matching Rule.
2. Run a pilot batch of 50–100 representative rows.
3. Inspect results: check for unexpected duplicates, orphaned records, and matching errors.
4. Adjust the matching rule if needed.
5. Only after the pilot passes, proceed with the full migration in chunked runs.
```

**Detection hint:** A migration workflow that jumps from CSV preparation to full import with no pilot batch step, or a workflow that does not mention `Contact Matching Rules` or `Duplicate Detection` configuration anywhere in the NPSP Settings setup phase.

---

## Anti-Pattern 6: Suggesting npsp__DataImport__c Records Can Be Edited After Processing to Correct Mistakes

**What the LLM generates:** Instructions to update `npsp__Status__c` back to blank or "Open" on already-imported staging rows and re-run the importer to correct data mistakes post-import.

**Why it happens:** The staging object pattern suggests that editing the staging row and re-running should be safe. LLMs apply this general assumption without knowing that re-processing can create duplicate Contact and Account records.

**Correct pattern:**

```
Do NOT re-process imported staging rows by resetting their status. This can create duplicates.
For post-import corrections:
- Use standard Salesforce data tools to directly update the Contact, Account, or Opportunity records
  that were created by the original import.
- If re-import is unavoidable, first delete the incorrectly created Contact/Account records,
  create a new staging row with corrected data, and run the importer fresh.
- Always clean up (delete) processed npsp__DataImport__c rows after each run.
```

**Detection hint:** Instructions to update `npsp__Status__c = ''` or `npsp__Status__c = 'Open'` on existing imported rows followed by a re-run of the Data Importer.
