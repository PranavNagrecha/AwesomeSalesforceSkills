# LLM Anti-Patterns: DataRaptor Load and Extract

Common mistakes AI coding assistants make when building or advising on DataRaptor (Omnistudio Data Mapper) Extract and Load. Each entry gives the mistake, why it happens, and the correct move.

## Anti-Pattern 1: Recommending a Load for Migrations or Loop-Driven Bulk Writes

**What the LLM generates:** Instructions to use a DataRaptor Load to insert or update thousands of records, often by looping over a JSON array in an Integration Procedure.

**Why it happens:** LLMs know a Load writes to Salesforce and generalize it as a bulk tool.

**Correct pattern:**

```text
Load is platform DML, not the Bulk API.
- Called once per record from an IP loop: each call is its own DML, so the
  150-statement transaction limit binds first.
- Called once with many records: above synchronousProcessThreshold the Load
  runs as Apex batch jobs (processSuperBulk spreads it further), so the call
  returns before the data exists.
For migrations and integrations, use Bulk API 2.0, Batch Apex, or Data Loader.
```

**Detection hint:** A Load inside a loop, or a Load proposed for data migration or nightly sync.

---

## Anti-Pattern 2: Writing Raw SOQL Into an Extract

**What the LLM generates:** "Set the Extract's SOQL to `SELECT Id, Name, (SELECT Id FROM Contacts) FROM Account WHERE Id = :accountId`."

**Why it happens:** LLMs know Extracts read data and assume the designer takes a SOQL string.

**Correct pattern:**

```text
The Extract tab takes objects, not SOQL:
  Step 1  Object Account   Extract Output Path Account   Filter Id = AccountId (input parameter)
  Step 2  Object Contact   Extract Output Path Contact   Filter AccountId = Account:Id
Then map Account:Name, Contact fields, etc. on the Output tab.
(The cross-step "Account:Id" filter form is UNVERIFIED (2026-10-03) in the
fetched docs; confirm it in your org's designer.)
```

**Detection hint:** A SOQL statement, a bind variable (`:accountId`), or a sub-select presented as DataRaptor Extract configuration.

---

## Anti-Pattern 3: Claiming the Upsert Key Must Be an External ID Field

**What the LLM generates:** "Mark `External_Customer_ID__c` as External ID on the field definition, or the Load can't upsert."

**Why it happens:** The LLM carries over the Apex `upsert` and Data Loader rule.

**Correct pattern:** Any mapped field can be an Upsert Key. When all Upsert Keys together match a unique existing record, the Load updates it; otherwise it creates a record. Uniqueness of the key values is the designer's responsibility (Trailhead, Data Mapper Load).

**Detection hint:** "must be designated as External ID" in DataRaptor Load guidance.

---

## Anti-Pattern 4: Assuming Multi-Object Loads Are Always Non-Atomic (or Always Atomic)

**What the LLM generates:** Either "a multi-object Load never rolls back, so write compensating logic" or "the Load is a transaction, so a failure undoes everything."

**Why it happens:** LLMs answer from general database intuition instead of the Load's settings.

**Correct pattern:** The behavior is a setting. `rollbackOnError` true means the Load does not commit if there is an error; false commits what was executed. `errorIgnored` true continues past errors. State which setting the design uses.

**Detection hint:** Any statement about Load atomicity that doesn't name `rollbackOnError`.

---

## Anti-Pattern 5: Using Turbo Extract When Formulas or Reshaping Are Needed (or Avoiding It for Parent Fields)

**What the LLM generates:** A Turbo Extract with formulas and nested output mapping, or the opposite claim that Turbo Extract can't read any related-object field.

**Why it happens:** "Turbo" sounds strictly better, and the limits are remembered vaguely.

**Correct pattern:** Turbo Extract reads a single object type "with support for fields from related objects," and it does not support formulas or complex output mappings. Use a standard Extract for several objects, formulas, or reshaped output.

**Detection hint:** Formulas or multi-level output mapping on a Turbo Extract, or "Turbo Extract can't read parent fields."

---

## Anti-Pattern 6: Testing a Load in Preview Against Shared Data

**What the LLM generates:** "Paste the OmniScript JSON into the Load's Preview tab in UAT and click Execute to check the mapping."

**Why it happens:** Preview sounds like a dry run.

**Correct pattern:** Load Preview saves records permanently ("Objects Created ... saved permanently"). Preview Loads only in a developer sandbox or scratch org, with throwaway target records.

**Detection hint:** Load Preview suggested in UAT, staging, or production.

---

## Anti-Pattern 7: Justifying the Bulk Warning With Fabricated Governor Arithmetic

**What the LLM generates:** The right conclusion ("don't use Data Mapper Load for bulk") supported by numbers that do not add up:

> "Data Mapper Load uses standard DML, one DML statement per record iteration. For 500 records, this consumes 500 DML statements in a single transaction, quickly hitting governor limits. The Integration Procedure fails with `Too many DML statements`."

**Why it happens:** The model reaches a correct recommendation and then **back-fills a mechanism to justify it**, because a bare "don't do this" reads as weaker than a causal explanation. The back-fill is never checked against the limit it invokes: the DML **statement** limit is 150, so a run that genuinely issued one statement per record would fail at iteration 151 and never reach 500. The "500" is picked as a round illustrative volume, not derived. A second confusion feeds it, the DML **rows** limit is 10,000, and models routinely blur "statements" and "rows" into a single "DML limit", which makes 500 feel comfortably inside a ceiling it is not being measured against.

This matters beyond pedantry. A reader who trusts the arithmetic concludes the safe threshold is somewhere near 500 and builds a 300-record loop that fails in production. Fabricated supporting detail attached to correct advice is more dangerous than no detail, because it converts a directional warning into a false quantitative permission.

**Correct pattern:**

```text
Per-transaction limits (Apex Developer Guide, sync and async alike):
  Total number of DML statements issued                    : 150
  Total records processed as a result of DML statements    : 10,000

A LOOP-DRIVEN Load therefore dies at the 151st iteration, on statements
,  not on rows, which are nowhere near their ceiling.

The claim that is safe to make without further checking:
  "Data Mapper Load writes via platform DML, not the Bulk API. Below
   synchronousProcessThreshold the write is bounded by the calling
   transaction's governor limits; above it the Load uses Apex batch jobs
   (OmniDataTransform metadata). It is not a data-migration tool."

The claim that needs a source before you make it:
  any statement about how many DML statements Load issues internally for
  a SINGLE invocation carrying an N-element array. A bulkified 500-row
  write sits well inside both limits. Verify against the Omnistudio Data
  Mapper Load documentation; do not infer it from the loop case.
```

**Detection hint:** Whenever generated guidance pairs a record count with `Too many DML statements`, check the count against 150, any figure above it that is described as "consuming N DML statements" before failing is fabricated arithmetic. Second, mechanical and general: grep for the phrase `DML limit` / `DML limits` used without the word `statements` or `rows`. Salesforce has two distinct DML ceilings that differ by a factor of ~67, and guidance that does not name which one it means has not checked either.
