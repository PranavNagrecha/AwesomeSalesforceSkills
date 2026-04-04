# Gotchas — Sandbox Data Masking

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Encrypted Fields Are Silently Skipped Without Error or Warning

**What happens:** When a field protected by Shield Platform Encryption is included in a Data Mask configuration, the masking job runs to completion and reports success. The encrypted field's value is not modified — the real data remains. There is no warning in the Data Mask job log and no error surfaced in the UI.

**When it occurs:** Any time a masking policy is configured for a field that has a Platform Encryption policy applied to it in the sandbox org. This is most common on high-sensitivity fields like Contact.SSN__c, financial account numbers, or health record identifiers that organizations also encrypt.

**How to avoid:** Before finalizing a masking configuration, cross-reference every field in the policy against the list of encrypted fields. In Setup, navigate to Platform Encryption > Encryption Policy to see which fields have encryption enabled. Remove any encrypted fields from the Data Mask policy and document them explicitly in the compliance gap register. If the field must also be masked, discuss with the security architect: one option is to deprovision the encryption tenant secret for the sandbox copy, mask, then re-enable — but this requires careful key management coordination.

---

## Gotcha 2: Required Fields + Null/Delete Masking Causes Mid-Batch Job Abort

**What happens:** The Data Mask batch job aborts partway through with a DML exception. Some records in the object have already been masked; others retain their original values. The job log may show a partial success before the failure line. The sandbox is now in a mixed state where some records are masked and others are not — and it is not obvious which records fall into which group.

**When it occurs:** When a field configured for Null/Delete masking has a `Required` constraint (either in object settings or via validation rule). Data Mask attempts to write null to the field, Salesforce enforces the required constraint, and the DML update fails. Because Data Mask processes records in batches of 200, all records up to the failed batch are already masked when the job aborts.

**How to avoid:** Before adding any field to a Null/Delete masking configuration, verify whether it is required. Check both the field definition (Setup > Object Manager > Fields) and any active validation rules that reference the field. For required PII fields, use Pseudonymous or Deterministic masking instead of Null/Delete. If null is truly required, temporarily disable the validation rule via metadata deployment before running Data Mask, then re-enable it.

---

## Gotcha 3: Data Mask Does Not Propagate Across Lookup-Copied Fields

**What happens:** A contact's email address is masked on the Contact object, but the same email address appears in its original form in a related custom object field that copied the value at record creation (e.g., `Case_Intake__c.Reporter_Email__c` was populated by a workflow when the Case was created). After the masking run, developers can retrieve the real email from the Case Intake object even though Contact.Email is masked.

**When it occurs:** Whenever a field value is stored redundantly across multiple objects — which is common with workflow field updates, process builders that copy values, or formula fields that write to stored custom fields. Data Mask operates strictly on each field listed in the configuration; it has no awareness of data lineage or object relationships.

**How to avoid:** Audit the full data model for fields that are derivatives of or copies of PII fields. Common culprits include:
- Workflow/Process Builder field updates that stamp PII on related records
- Integration-written fields that mirror Contact or Lead values to custom objects
- Report snapshots or custom reporting objects that store snapshots of PII

Add every discovered redundant PII field to the masking configuration explicitly. Use the Salesforce Object Reference or your org's data dictionary to map all fields that reference or copy each primary PII field.

---

## Gotcha 4: Data Mask Is Not Available in Developer and Developer Pro Sandboxes

**What happens:** A team installs the Data Mask package in a Developer sandbox and attempts to configure a masking policy. The app installs without error, but running the configuration produces an error or the job silently processes zero records. The sandbox type is incompatible with Data Mask.

**When it occurs:** When a team uses a Developer or Developer Pro sandbox instead of a Partial Copy or Full Copy sandbox, which is common for small feature branches or when the team is unaware of the licensing constraint.

**How to avoid:** At the start of any masking initiative, confirm the sandbox type in Setup > Sandboxes. Data Mask requires a Partial Copy or Full Copy sandbox. If PII is reaching Developer sandboxes, the root fix is upstream: the sandbox seeding strategy should supply synthetic test data for Developer sandboxes rather than copying production records.
