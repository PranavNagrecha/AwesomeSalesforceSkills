---
name: dataraptor-load-and-extract
description: "Use when building or debugging DataRaptor Extract or DataRaptor Load operations in OmniStudio: designing multi-object extracts, configuring load upserts, handling iferror responses, or mapping output fields. NOT for DataRaptor Transform operations (use dataraptor-patterns), NOT for Integration Procedure design (use integration-procedures), NOT for bulk data loading outside OmniStudio."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# DataRaptor Load and Extract

Use this skill when building or troubleshooting DataRaptor Extract (reading data from Salesforce via SOQL) or DataRaptor Load (writing data to Salesforce via DML) in OmniStudio. This covers multi-object extracts, Turbo Extract vs standard Extract selection, load upsert configuration, output mapping, and error handling patterns.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify whether you need to read data (Extract) or write data (Load). These are different DataRaptor types with different configuration surfaces.
- For Extract: know the SOQL relationships you need — cross-object lookups use dot notation, parent-child relationships use sub-selects.
- For Load: know the DML operation (insert, update, upsert, delete) and the upsert key field if using upsert.
- Be aware that DataRaptor Load does NOT support Bulk API — it uses standard row-at-a-time DML. Do not use DataRaptor Load for high-volume data operations.

---

## Core Concepts

### DataRaptor Extract

DataRaptor Extract is an OmniStudio data retrieval tool that executes SOQL queries and maps results to output JSON. Key behaviors:

- **SOQL base object**: The primary FROM object. Cross-object fields use dot notation (e.g., `Account.Name`).
- **Parent-to-child relationships**: Use SOQL sub-selects to retrieve child records.
- **Output mapping**: Maps SOQL field paths to JSON keys in the output, using dot-notation to define nested JSON structure.
- **Preview tab**: Always test your extract in the Preview tab before embedding in an Integration Procedure.

### Turbo Extract vs Standard Extract

DataRaptor Turbo Extract is a faster read-only variant:
- Supports only direct field reads — no relationship queries, no sub-selects
- Cannot traverse parent-child relationships
- Significantly faster for simple lookups
- Use Turbo Extract for single-object field retrieval where performance matters

Standard Extract supports relationship queries, sub-selects, and complex output mapping. Use it when you need cross-object data.

### DataRaptor Load

DataRaptor Load is an OmniStudio DML tool for writing records to Salesforce sObjects. Key behaviors:

- **Supported operations**: Insert, Update, Upsert, Delete
- **Upsert key**: For upsert operations, specify the External ID field for matching. Must be designated as External ID on the field definition.
- **Multi-object support**: A single Load can write to multiple objects in sequence.
- **Error handling**: Load returns an `iferror` node in output JSON when DML fails. Check this node downstream in your Integration Procedure.
- **No Bulk API**: Uses standard DML — row-at-a-time. Not suitable for high-volume operations.
- **No rollback on partial failure**: Records written to early objects in a multi-object Load are not rolled back if a later object fails.

---

## Common Patterns

### Multi-Object Relationship Extract

**When to use:** Need to retrieve an Account and its related Contacts together for an OmniScript.

**How it works in Extract configuration:**
1. Set base object to `Account`
2. SOQL: `SELECT Id, Name, (SELECT Id, LastName, Email FROM Contacts) FROM Account WHERE Id = :accountId`
3. Output mapping: `Name` → `account.name`, use the Contacts sub-select relationship name for nested child records

**Why not two separate extracts:** Single extract with sub-select is more efficient — one SOQL query vs two. Child records are automatically nested in output JSON.

### Upsert with External ID

**When to use:** Receiving data from an external system where records may or may not already exist.

**How it works in Load configuration:**
1. Set operation to `Upsert`
2. Specify the External ID field (e.g., `External_Id__c`) — must be designated as External ID on the field
3. Map the incoming JSON path to `External_Id__c` and all other fields to update

### Handling iferror in Load

**When to use:** Any Load step that needs to handle DML failures gracefully.

**How it works:**
1. After the Load step in your Integration Procedure, add a conditional check
2. Check output path `<LoadStepName>:iferror` — if present, a DML error occurred
3. Read `<LoadStepName>:iferror:message` for the error description
4. Branch on the error to return a user-friendly message or attempt compensating actions

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single object, simple fields, performance-sensitive | Turbo Extract | Faster, no query overhead |
| Cross-object data (parent + child) | Standard Extract with sub-select | Turbo Extract does not support relationships |
| Writing to Salesforce from OmniScript | DataRaptor Load | Purpose-built DML tool |
| Writing >200 records | Do NOT use DataRaptor Load | No Bulk API — use Batch Apex separately |
| Need to detect write failure | Check `iferror` in Load output | Load does not throw; returns error info in output JSON |
| Need atomic multi-object write | Aware: no rollback | Load fails forward; design compensating actions |

---

## Recommended Workflow

1. **Determine operation type.** Read → Extract. Write → Load.
2. **For Extract:** Write and validate the SOQL in Developer Console first. Confirm it returns expected data.
3. **For Extract:** Design output mapping — map each SOQL field path to desired JSON key path. Test in Preview tab.
4. **For Load:** Identify DML operation and input JSON structure. Map each input path to the target sObject field.
5. **For Load with upsert:** Confirm the External ID field exists on the object and is marked External ID. Map it in Input Mapping.
6. **Test using the Preview tab** before embedding in an Integration Procedure.
7. **Add error handling** downstream in the Integration Procedure — check `iferror` output path from any Load step.

---

## Review Checklist

- [ ] Extract SOQL validated in Developer Console before configuring the DataRaptor
- [ ] Output mapping tested in Preview tab and JSON structure confirmed
- [ ] Turbo Extract used where only simple field reads are needed
- [ ] Load upsert key field confirmed as External ID on the sObject
- [ ] Integration Procedure checks `iferror` output from Load steps
- [ ] No Load operation used for more than ~200 records (Bulk API not supported)
- [ ] Multi-object Load: team aware there is no rollback on partial failure

---

## Salesforce-Specific Gotchas

1. **DataRaptor Load does not use Bulk API** — Row-at-a-time DML means governor limits apply. For anything over a few dozen records, this causes performance problems or limit violations.
2. **No rollback on multi-object Load failure** — If Load writes to Object A then fails on Object B, Object A records are already committed. Design single-object Loads where possible, or implement compensating actions.
3. **Output mapping path uses API relationship name, not label** — SOQL child relationship paths must use the API relationship name (e.g., `Contacts`, not `Contact`). Using the label causes empty output.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DataRaptor Extract configuration | SOQL query, input variables, output field mappings |
| DataRaptor Load configuration | Operation type, upsert key, input field mappings, error handling note |

---

## Related Skills

- dataraptor-patterns — DataRaptor Transform operations (different type)
- integration-procedures — Using DataRaptor as steps within an Integration Procedure
- omnistudio-debugging — Debugging DataRaptor Preview and Integration Procedure execution
