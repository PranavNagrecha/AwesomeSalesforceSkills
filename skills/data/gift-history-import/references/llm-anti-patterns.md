# LLM Anti-Patterns — Gift History Import

Common mistakes AI coding assistants make when generating or advising on NPSP gift history imports.

---

## Anti-Pattern 1: Recommending Data Loader Directly to Opportunity for NPSP Gift Import

**What the LLM generates:** Instructions to export donation history to CSV and import directly into the Salesforce Opportunity object using Data Loader, treating it like a standard CRM object insert.

**Why it happens:** LLMs know that Opportunity is a standard Salesforce object and Data Loader is a standard import tool. They do not model the NPSP trigger layer that fires from BDI batch processing to create related payment, OCR, and GAU records.

**Correct pattern:** All NPSP gift imports must go through `npsp__DataImport__c` staging and the NPSP Data Importer (BDI) batch. This is the only import path that creates the full gift data model including payment records, OCRs, and GAU allocations.

**Detection hint:** If instructions say to load directly into Opportunity, npe01__OppPayment__c, or npsp__General_Accounting_Unit__c without first staging to DataImport__c, the approach is wrong for NPSP gift migration.

---

## Anti-Pattern 2: Assuming Custom Fields Map Automatically Without Advanced Mapping

**What the LLM generates:** DataImport__c staging CSV with custom fields populated, followed by BDI batch run — without any mention of enabling Advanced Mapping or configuring field maps.

**Why it happens:** LLMs assume that staging fields in a staging object automatically maps them to target fields. They do not model the explicit Advanced Mapping toggle and configuration step required in NPSP Settings.

**Correct pattern:** Enable Advanced Mapping in NPSP Settings > Data Import before staging data. Configure explicit field maps from DataImport__c source fields to target object fields (Opportunity, Payment, GAU). Without this configuration, custom fields in staging rows are silently ignored.

**Detection hint:** If any custom fields need to be populated on imported gift records but the instructions do not mention enabling Advanced Mapping, the import will silently lose that data.

---

## Anti-Pattern 3: Loading Gift History Directly to npe01__OppPayment__c

**What the LLM generates:** A Bulk API job that inserts payment records directly into `npe01__OppPayment__c` with a lookup to the previously imported Opportunity.

**Why it happens:** LLMs reason that if you already have Opportunities in Salesforce, you can add payments by inserting child records. This is correct for standard Salesforce objects but incorrect for NPSP managed payment records where NPSP triggers expect to create payment records through its own automation.

**Correct pattern:** Do not insert payment records directly. Stage the full gift record (with payment fields populated) in DataImport__c. BDI creates the payment record as part of its coordinated batch process. Direct payment inserts bypass NPSP's payment automation and may create duplicate payment entries or conflict with NPSP's payment scheduler.

**Detection hint:** If instructions insert records into `npe01__OppPayment__c` directly (not via BDI), flag this as bypassing NPSP payment automation.

---

## Anti-Pattern 4: Using Contact Matching Fields That Are Not Configured in NPSP Matching Rules

**What the LLM generates:** DataImport__c staging rows populated with only a donor's full name as the matching key (Contact1_Firstname, Contact1_Lastname), assuming BDI will correctly identify the donor.

**Why it happens:** LLMs use name matching as the obvious identifier for people records. They do not model that NPSP Contact Matching Rules have specific configurations that determine which fields are used for deduplication — and name-only matching has a very high false-positive rate.

**Correct pattern:** Check the NPSP Contact Matching Rules configuration (NPSP Settings > Contact Matching). If External IDs are available in the source system, use them as the primary matching key by populating a custom External ID field on Contact and mapping it in DataImport__c. Name and email matching alone creates donor duplicates at high rates when source data has name spelling variants.

**Detection hint:** If the staging spec relies exclusively on first name + last name for donor identification and the organization has any name variation in its source data, deduplication risk is high.

---

## Anti-Pattern 5: Attempting to Import More Than 50,000 Records in a Single BDI Run

**What the LLM generates:** Instructions to load 200,000 historical gift records into DataImport__c in a single batch and then run the NPSP Data Importer once.

**Why it happens:** LLMs do not model per-batch file size and record count limits. They assume "import all records, then run the tool once" as the simplest path.

**Correct pattern:** NPSP Data Importer processes a maximum of 50,000 DataImport__c rows per batch run and a maximum file size of 100 MB. Large imports must be chunked: insert ≤50,000 rows, run BDI to completion, insert the next chunk, repeat. Staging more rows than a single batch can handle before running BDI leads to partial processing and a growing backlog of unprocessed staging rows that degrade BDI performance.

**Detection hint:** If total gift volume exceeds 50,000 and the instructions describe a single BDI run, chunking is missing from the plan.
