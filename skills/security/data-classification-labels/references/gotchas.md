# Gotchas — Data Classification Labels

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Classification Is Metadata-Only — No Runtime Enforcement

**What happens:** Setting `SecurityClassification = Restricted` on a field does not restrict who can read or write it. Records are not blocked. Fields are not hidden. No encryption is applied. The label is purely informational metadata.

**When it occurs:** Teams implementing a compliance program assume that classifying a field as `Restricted` or `MissionCritical` will trigger some platform protection. It does not. A user with FLS read access to the field can still read it regardless of its classification label.

**How to avoid:** Treat classification as a governance documentation layer — it describes what the field contains, not how it is protected. Actual data protection requires separate mechanisms: Field-Level Security (FLS) for access control, Shield Platform Encryption for encryption at rest, and Shield Event Monitoring for usage auditing. Never substitute classification for FLS changes.

---

## Gotcha 2: ComplianceGroup Cannot Be Updated via Tooling API Writes

**What happens:** Attempting to update `ComplianceGroup` via the Tooling API `FieldDefinition` object (e.g., via a REST PATCH or a Tooling API `update()` call) does not persist the change. The API call may return success but the `ComplianceGroup` value remains unchanged in the org.

**When it occurs:** Automation scripts that use the Tooling API to batch-classify fields — setting both `SecurityClassification` and `ComplianceGroup` in a single Tooling API write — will successfully update `SecurityClassification` but silently leave `ComplianceGroup` at its previous value. This creates a discrepancy between the intended classification state and the actual org state.

**How to avoid:** Use the Metadata API (`CustomField` metadata type) or the Setup > Data Classification UI to set `ComplianceGroup`. Tooling API reads for `ComplianceGroup` work correctly and should be used for auditing. Only writes are affected by this platform gap. Validate `ComplianceGroup` values via Tooling API query after any Metadata API deployment to confirm they persisted.

---

## Gotcha 3: Standard Field Classification Requires Stub Metadata Files

**What happens:** Standard Salesforce fields (e.g., `Contact.Email`, `Lead.Phone`) cannot be classified by modifying the object-level metadata XML directly. If you create a `.field-meta.xml` file for a standard field containing the full field definition (type, length, label, etc.), the deployment will fail with a metadata error indicating the field is not customizable.

**When it occurs:** Practitioners who correctly know that standard field classification is possible create stub files but inadvertently include standard field attributes (e.g., `<type>`, `<length>`) that are not allowed in a standard field override. Or they skip creating a stub file entirely, assuming standard fields can only be classified in the UI.

**How to avoid:** For standard fields, create a minimal `.field-meta.xml` stub containing only the classification elements (`<securityClassification>`, `<complianceGroup>`, `<businessStatus>`) inside a `<CustomField>` element with the correct `<fullName>`. Omit all other field attributes. The platform merges the classification attributes into the standard field definition on deploy. Test this pattern in a sandbox before deploying to production.

---

## Gotcha 4: Einstein Data Detect Recommends ComplianceGroup Only — Not SecurityClassification

**What happens:** After running Einstein Data Detect and accepting all recommendations, practitioners assume the fields are "fully classified." In fact, Data Detect only populates `ComplianceGroup`. `SecurityClassification` remains null on all fields that were not manually labeled.

**When it occurs:** Teams running a classification initiative use Data Detect as a one-stop solution and skip the manual `SecurityClassification` assignment step. Post-initiative Tooling API queries show `SecurityClassification = null` on hundreds of fields despite the team believing they had been through a full classification review.

**How to avoid:** After running Data Detect and accepting `ComplianceGroup` recommendations, run a separate pass to assign `SecurityClassification` values based on the compliance group. A field classified as `PII` or `HIPAA` should typically be `Confidential` or `Restricted` depending on its sensitivity tier. Create a decision matrix mapping `ComplianceGroup` values to expected `SecurityClassification` tiers and use it as a post-Data-Detect checklist.

---

## Gotcha 5: API Version Below 46.0 Silently Drops Classification Attributes on Deploy

**What happens:** If a metadata deployment uses API version 45.0 or lower, the `securityClassification`, `complianceGroup`, `businessOwnerId`, and `businessStatus` XML elements are silently ignored. The deploy succeeds, the fields are deployed, but the classification attributes are not applied.

**When it occurs:** Projects that have not updated their `sfdx-project.json` `sourceApiVersion` (or are using older CI/CD tooling with a hardcoded API version) will silently drop classification metadata on every deploy. Because no error is raised, the issue can persist for months before being caught by a compliance audit query.

**How to avoid:** Confirm `sourceApiVersion` in `sfdx-project.json` is 46.0 or later before deploying classification metadata. Add a post-deploy Tooling API validation step to your CI/CD pipeline that queries `FieldDefinition` on recently deployed fields and asserts that classification values are present. This catches silent drops before they reach a production org.
