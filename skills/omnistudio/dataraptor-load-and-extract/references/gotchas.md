# Gotchas — DataRaptor Load and Extract

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Load Does Not Support Bulk API — Row-at-a-Time DML

**What happens:** A DataRaptor Load called in a loop inside an Integration Procedure executes one DML statement per iteration. For more than ~150 records, this hits the governor limit for DML statements per transaction.

**When it occurs:** Any pattern where a Load is invoked in a loop or where the input JSON contains a list of records and the Load processes each one individually.

**How to avoid:** Use DataRaptor Load only for single-record or small-set DML operations in a conversational OmniScript context. For bulk operations, use Batch Apex or Bulk API 2.0 outside the OmniStudio context.

---

## Gotcha 2: iferror Node Does Not Throw an Exception

**What happens:** A DataRaptor Load DML fails silently. The Integration Procedure continues executing subsequent steps as if nothing happened. The user receives a success response even though the record was not saved.

**When it occurs:** When the Integration Procedure does not check the `<LoadStepName>:iferror` output path after the Load step.

**How to avoid:** Always add an explicit check for the `iferror` output node after every Load step. Use a Set Values or Conditional step to detect failures and return appropriate error information to the user.

---

## Gotcha 3: Output Mapping Relationship Name Must Be the API Name

**What happens:** A DataRaptor Extract with a sub-select returns no data in the child relationship output path, even though the SOQL query is returning child records in Developer Console.

**When it occurs:** The output mapping path uses the label or object name instead of the API relationship name. For example, mapping `Contact` instead of `Contacts` (the API plural relationship name) for Account-to-Contact.

**How to avoid:** Use the SOQL relationship name (the API name, which is typically plural for standard objects: `Contacts`, `Cases`, `Opportunities`) in the output mapping path. Verify the exact relationship name by checking the object's relationship configuration in Setup.

---

## Gotcha 4: Turbo Extract Cannot Filter by Formula Fields

**What happens:** A Turbo Extract returns incorrect or unfiltered data when the WHERE clause references a formula field.

**When it occurs:** Using Turbo Extract with a filter condition on a formula field. Turbo Extract bypasses the full SOQL engine and does not support all SOQL features including formula field filters.

**How to avoid:** Use standard DataRaptor Extract (not Turbo) when filtering on formula fields, cross-object fields, or any complex SOQL predicate. Reserve Turbo Extract for simple equality filters on indexed fields.
