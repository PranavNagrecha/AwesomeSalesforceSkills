# Gotchas — Lead Data Import and Dedup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Blocking Duplicate Rules Do Not Block Web-to-Lead or API Inserts

**What happens:** A Duplicate Rule with action "Block" evaluates the incoming lead record and creates a `DuplicateRecordSet`, but the lead is inserted anyway. No error is returned to the Web-to-Lead form submitter, the API caller, or the calling Apex. The block is silently ignored.

**When it occurs:** Any time a lead is inserted via Web-to-Lead POST, Salesforce REST/SOAP API, Apex `Database.insert()` without a `DuplicateRuleHeader`, or a data load tool that does not pass the duplicate save option. This is documented Salesforce platform behavior — blocking rules are enforced only when saving via the standard Salesforce UI (including Lightning record create pages).

**How to avoid:** Set Duplicate Rules to "Alert" mode and use an after-insert Apex trigger or Flow to detect and route duplicates for non-UI channels. Alert mode reliably creates `DuplicateRecordSet` records for all insert pathways. If UI blocking is still desired, keep "Block" on the rule — it works correctly for UI-based inserts — and add the trigger-based detection as a safety net for other channels.

---

## Gotcha 2: Data Import Wizard Dedup Does Not Match Within the Import File

**What happens:** The Data Import Wizard dedup only matches incoming records against existing Salesforce records. It does not detect duplicate rows within the import file itself. If the same email address appears on 3 rows in the CSV, all 3 rows are inserted as new records (or 1 updates an existing record and 2 more are inserted as duplicates of each other).

**When it occurs:** Any CSV import where the source file has not been pre-deduplicated. Common with trade show badge exports, merged marketing lists, or any file assembled from multiple sources.

**How to avoid:** Before running the Data Import Wizard, deduplicate the import file itself using Excel (`Remove Duplicates` on the Email column), a Python `pandas.drop_duplicates()` step, or a SQL `DISTINCT` query if working from a database. Only after the file is internally deduplicated should it be uploaded to Salesforce.

---

## Gotcha 3: Standard Lead Matching Rule Uses Fuzzy Algorithms That Can Match Unexpected Records

**What happens:** The Standard Lead Matching Rule uses Jaro-Winkler fuzzy matching on Name and Company fields. This can produce false-positive matches — two different people with similar names at similarly-named companies are flagged as duplicates. Conversely, it can produce false negatives when email domains differ even though names match exactly.

**When it occurs:** Orgs importing data from industries with common names (e.g., "John Lee" at "Acme Corp" and "Jon Lee" at "Acme Corporation" may be flagged as the same person). Also in orgs with contacts sharing a corporate email domain but different name variations.

**How to avoid:** Review the matching rule threshold setting in Setup > Matching Rules. A lower threshold catches more potential duplicates but increases false positives. A higher threshold reduces false positives but may miss genuine duplicates with name variations. Test the configured threshold against a sample of known duplicates and known non-duplicates before activating a rule on a production import. Consider adding Email as a required match field (weight it heavily) to anchor fuzzy name matching to a more reliable identifier.

---

## Gotcha 4: findDuplicates() Apex API Only Evaluates Active Duplicate Rules

**What happens:** Calling `Datacloud.DuplicateRule.findDuplicates()` in Apex returns no results if all matching Duplicate Rules on the Lead object are inactive, even when true duplicates exist in the org.

**When it occurs:** During sandbox testing when a developer deactivates a Duplicate Rule to test a different behavior, then runs tests of the dedup trigger. All calls to `findDuplicates()` return empty results. The developer concludes the trigger is not detecting duplicates, but the actual cause is the deactivated rule.

**How to avoid:** Before running any dedup trigger test, verify that at least one Lead Duplicate Rule is active in Setup. Include test assertions that mock the `findDuplicates()` result using Test.setFixedSearchResults() or custom test data setup — do not rely on the rule being active in the sandbox for test coverage.

---

## Gotcha 5: The 5-Active-Rules-Per-Object Limit Applies to Rules Created by Managed Packages

**What happens:** An org installs a marketing automation managed package (e.g., Account Engagement/Pardot connector) that includes its own Duplicate or Matching Rules on the Lead object. These rules consume slots from the 5-active-rules limit. When the admin later tries to activate a custom rule, it fails with a validation error because the limit is already reached.

**When it occurs:** Any org that has installed one or more AppExchange packages that include Lead dedup rules. The package rules often have non-obvious names and are easy to overlook during an audit.

**How to avoid:** Before designing new Duplicate Rules, run an audit in Setup > Duplicate Rules filtered to the Lead object and review all active rules — including those from managed packages. If all 5 slots are occupied, evaluate whether any existing rules are redundant or can be consolidated before activating new ones.
