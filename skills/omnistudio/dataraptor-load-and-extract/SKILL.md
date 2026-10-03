---
name: dataraptor-load-and-extract
description: "Build or debug DataRaptor Extract and Load — multi-object extracts, upserts, iferror mapping. Triggers: DataRaptor Extract, DataRaptor Load, Turbo Extract debug. NOT for Extract vs Load design tradeoffs — use omnistudio/dataraptor-patterns."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I extract data from multiple related objects in a DataRaptor"
  - "my DataRaptor Load is failing and returning an iferror node"
  - "how do I configure a DataRaptor upsert with an external ID"
  - "what is the difference between DataRaptor Extract and Turbo Extract"
  - "how do I map SOQL relationship query results to output JSON in DataRaptor"
  - "build a Data Mapper Load that updates the account from the OmniScript"
  - "deploy an OmniDataTransform with the Salesforce CLI"
tags:
  - dataraptor
  - omnistudio
  - data-extract
  - data-load
  - upsert
  - integration-procedure
inputs:
  - "SOQL query pattern or object/field list for the extract"
  - "Target sObject and operation type for a load (insert/update/upsert/delete)"
  - "Expected output JSON structure or input JSON structure for the operation"
outputs:
  - "DataRaptor Extract configuration with SOQL and output field mappings"
  - "DataRaptor Load configuration with input mappings and upsert key"
  - "Diagnosis of iferror behavior and recommended error handling"
dependencies: []
runtime_orphan: true
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# DataRaptor Load and Extract

Use this skill when building or troubleshooting a DataRaptor Extract (read Salesforce data into JSON) or a DataRaptor Load (write JSON into Salesforce records) in OmniStudio. Current product documentation calls DataRaptors **Omnistudio Data Mappers**, and the metadata type is `OmniDataTransform`. This skill covers multi-object extracts, Turbo Extract selection, Load upsert keys, transaction behavior, and error handling.

---

## Before Starting

Gather this context before working on anything in this domain:

- Read or write? Extract and Turbo Extract read; Load writes; Transform reshapes data without touching records.
- For Extract: which objects, which filters, and which input parameters (for example `AccountId`) the caller passes.
- For Load: which objects receive data, which fields identify an existing record (the Upsert Keys), and which fields must be present (Is Required For Upsert).
- Which runtime the org uses: Omnistudio for Managed Packages or Omnistudio on the standard runtime. Trailhead modules and metadata types differ between them.
- How many records one call carries. A Load can hand work to Apex batch jobs above a threshold, which changes its transaction behavior.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Which fields uniquely identify an existing record for the Load? | Any mapped field can be an Upsert Key; when all Upsert Keys match one record the Load updates it, otherwise it creates a new one. | The right match fields instead of guessed ones. | No duplicate records from a key that does not match uniquely. |
| Which fields must be present before a record is written? | When an Is Required For Upsert field is empty, the Load skips that record. | A short, deliberate required list. | Missing data is caught, and skips are expected rather than mysterious. |
| Must a multi-object Load be all-or-nothing? | `rollbackOnError` decides whether a failure rolls back what was already executed; `errorIgnored` lets processing continue past errors. | A stated transaction rule per Load. | Partial writes happen only where the business accepts them. |
| Will the Extract run for users who should not see every field? | The Options tab can check the user's field access before running (`fieldLevelSecurityEnabled`). | FLS behavior chosen per Extract. | Guest and external users don't receive fields their profile hides. |
| Can the Extract response be cached, and for how long? | Responses can be stored in session or org platform cache with a time to live. | A cache type and TTL that match how fresh the data must be. | Fewer queries without showing stale data. |
| How many records will one Load call carry? | `synchronousProcessThreshold` and `processSuperBulk` move large inputs to Apex batch jobs. | Sizing that keeps interactive calls synchronous. | Predictable behavior for both the interactive and the bulk path. |

---

## Core Concepts

### DataRaptor Extract

An Extract reads one or more Salesforce objects and returns JSON, XML, or custom output through mappings (Trailhead, Omnistudio Data Mappers). You don't write raw SOQL. On the **Extract** tab you add objects in sequence. Each one has an **Extract Output Path** (the top-level JSON node), filters made of a field, a comparison operator, and "either a quoted literal value, an input parameter, or another field of the same source object" (Trailhead), and the fields to return. Related objects are added as later steps whose filter points at an earlier step's output, for example `Contact.AccountId = Account:Id`. UNVERIFIED (2026-10-03): the `Account:Id` cross-step filter form is common practice and matches the `Account:Type` path style in the `OmniDataTransformItem` sample, but the fetched sources do not state it directly.

| Tab | Purpose |
|---|---|
| Extract | Objects, filters, and Extract Output Paths |
| Formulas | Formulas whose results map to output JSON |
| Output | Map extract-step JSON to the output JSON |
| Options | Field-level security check, platform cache type, time to live |
| Preview | Run with Key/Value input parameters and inspect the response |

Extracts also support paging through sorted data by values or offsets. Data Mappers can read external objects and custom metadata with no extra syntax.

### Turbo Extract vs Standard Extract

A Turbo Extract "retrieves and filters data from a single Salesforce object type with support for fields from related objects." It does not support formulas or complex output mappings, and it has simpler configuration and better runtime performance (Trailhead). Use a standard Extract when you need several objects, formulas, or reshaped output.

### DataRaptor Load

A Load writes data to one or more Salesforce objects from JSON or XML input. It updates existing records and creates new ones in the same run (Trailhead).

| Setting | Behavior |
|---|---|
| Objects tab | The objects to write, in sequence |
| Fields tab | Input JSON Path to Domain Object Field mappings |
| Upsert Key | Any mapped field can be one; all Upsert Keys together must match a unique record to update it |
| Is Required For Upsert | If such a field has no data, the record is skipped |
| `rollbackOnError` | True: don't commit if there is an error. False: commit what was executed |
| `errorIgnored` | True: continue processing after errors |
| `synchronousProcessThreshold` / `processSuperBulk` | Above the threshold the Load uses Apex batch jobs; super bulk spreads the upsert over several batch jobs |
| Preview | Writes real records ("Objects Created ... saved permanently") |

UNVERIFIED (2026-10-03): whether a Load can delete records, and the exact error node an Integration Procedure receives from a failed Load (often described as `iferror`), are not stated in the fetchable sources. Check the Data Mapper Load page in Salesforce Help and the Integration Procedure debug output before relying on either.

---

## Common Patterns

### Account With Related Contacts in One Extract

**When to use:** An OmniScript needs an Account and its Contacts together.

**How it works:**
1. Extract step 1: object `Account`, Extract Output Path `Account`, filter `Id = AccountId` (input parameter).
2. Extract step 2: object `Contact`, Extract Output Path `Contact`, filter `AccountId = Account:Id`.
3. Output tab: map `Account:Name` to `Account:Name`, and the `Contact` step fields to a list node such as `Account:Contacts`.
4. Preview with `AccountId` set to a real record ID.

**Why not two separate Extracts:** one Extract is one server call from the Integration Procedure and returns the nested JSON the OmniScript needs.

### Upsert by Business Key

**When to use:** Records arrive from an external system and may or may not exist yet.

**How it works:**
1. Objects tab: add `Contact`.
2. Fields tab: map `customer:externalId` to `External_Customer_ID__c` and mark it **Upsert Key** and **Is Required For Upsert**.
3. Map the remaining fields.
4. Decide `rollbackOnError` for the Load and handle the Load response in the Integration Procedure.

The deployable `OmniDataTransform` files for both patterns are in [references/metadata-examples.md](references/metadata-examples.md).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One object plus parent fields, no formulas, performance-sensitive | Turbo Extract | Simpler and faster; supports related-object fields on a single object |
| Several objects, formulas, or reshaped output | Standard Extract | Turbo Extract has no formulas or complex output mapping |
| Write from an OmniScript | Load called from an Integration Procedure | The documented data flow for saving OmniScript data |
| Large write volumes | Size `synchronousProcessThreshold`, or use Bulk API or Batch Apex outside OmniStudio | Load is not the Bulk API; above the threshold it switches to Apex batch jobs |
| All-or-nothing multi-object write | `rollbackOnError = true` | Commits nothing if any step errors |
| Writes must not duplicate records | Upsert Keys that match uniquely plus Is Required For Upsert | Non-matching keys create new records |

---

## Recommended Workflow

1. Decide the type (Extract, Turbo Extract, Load, Transform) and the runtime (managed package or standard) before building.
2. For an Extract, add objects with Extract Output Paths and filters, then map output and set the Options tab (FLS check, cache type, TTL).
3. For a Load, add objects, map Input JSON Paths, choose Upsert Keys and Is Required For Upsert fields, and set `rollbackOnError`.
4. Preview an Extract with real input parameters; Preview a Load only in a sandbox, because Preview saves records.
5. Retrieve the `OmniDataTransform` source and run `python3 skills/omnistudio/dataraptor-load-and-extract/scripts/check_dataraptor_load_and_extract.py --source-dir force-app` to flag Loads without upsert keys, FLS off, and Turbo Extracts with formulas.
6. Call the Data Mapper from an Integration Procedure and handle its response before returning success to the OmniScript.

---

## Review Checklist

- [ ] Extract objects, filters, and Extract Output Paths produce the JSON shape the caller expects in Preview
- [ ] Turbo Extract used only for single-object reads without formulas or complex output mapping
- [ ] Load Upsert Keys match a unique record; Is Required For Upsert fields chosen deliberately
- [ ] `rollbackOnError` set to match the business transaction rule
- [ ] FLS check (`fieldLevelSecurityEnabled`) decided for Extracts used by restricted users
- [ ] Cache type and TTL fit the freshness requirement
- [ ] Load Preview run only in a sandbox
- [ ] Integration Procedure handles the Load response before reporting success

---

## Salesforce-Specific Gotchas

Full write-ups with sources are in [references/gotchas.md](references/gotchas.md).

| Gotcha | One-line summary |
|---|---|
| Preview writes | Load Preview saves records permanently. |
| Upsert Key | Any field can be a key; a non-unique match or no match creates a new record. |
| Required For Upsert | Empty required fields skip the record silently. |
| Rollback | `rollbackOnError` false commits partial work. |
| Volume | Above `synchronousProcessThreshold` the Load runs as Apex batch jobs. |
| Internal objects | `OmniDataTransform` records are internal; don't edit them with DML. |
| Metadata switch | `enableOmniStudioMetadata` can't be turned off once on. |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DataRaptor Extract configuration | Objects, filters, input parameters, output mappings, options |
| DataRaptor Load configuration | Objects, field mappings, Upsert Keys, required fields, rollback rule |
| `OmniDataTransform` source | `omniDataTransforms/<UniqueName>.rpt-meta.xml` under version control |

---

## Related Skills

- omnistudio/dataraptor-patterns: DataRaptor Transform operations and Extract vs Load design tradeoffs
- omnistudio/integration-procedures: using DataRaptors as steps within an Integration Procedure
- omnistudio/omnistudio-debugging: debugging DataRaptor Preview and Integration Procedure execution
