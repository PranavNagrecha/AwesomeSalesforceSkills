# LLM Anti-Patterns — Data Classification Labels

Common mistakes AI coding assistants make when generating or advising on Salesforce Data Classification Labels.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming Classification Restricts Field Access

**What the LLM generates:** Advice like "Set `SecurityClassification = Restricted` on the SSN field to prevent unauthorized users from accessing it" or "Classifying a field as MissionCritical will limit who can read or write it."

**Why it happens:** LLMs associate the word "classification" with access control in general security contexts. Training data from non-Salesforce sources describes classification systems that do carry enforcement (e.g., government data classification with access tiers). The LLM incorrectly generalizes this to the Salesforce metadata-only implementation.

**Correct pattern:**

```
Classification labels in Salesforce have no enforcement semantics.
Setting SecurityClassification = Restricted does not change who can
read or write the field. Actual access control requires:
- Field-Level Security (FLS) on profiles and permission sets
- Shield Platform Encryption for encryption at rest
- Sharing rules and object-level security for record access
Classification is documentation, not enforcement.
```

**Detection hint:** Any sentence pairing "classification" with "restrict", "prevent access", "block", or "protect from unauthorized" is likely describing a false capability.

---

## Anti-Pattern 2: Using Tooling API to Set ComplianceGroup

**What the LLM generates:** A script that uses the Tooling API to bulk-update `ComplianceGroup` on `FieldDefinition` records — typically a REST PATCH or Apex Tooling API `update()` call looping over fields.

**Why it happens:** The Tooling API `FieldDefinition` object exposes `ComplianceGroup` as a readable field. LLMs trained on Salesforce API patterns assume that readable fields on Tooling API objects are also writable, which is not always true. The pattern of "query then update" is common in Tooling API automation.

**Correct pattern:**

```xml
<!-- ComplianceGroup must be set via Metadata API CustomField -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>SSN__c</fullName>
    <complianceGroup>PII</complianceGroup>
    <complianceGroup>HIPAA</complianceGroup>
    <securityClassification>Restricted</securityClassification>
    <businessStatus>Active</businessStatus>
</CustomField>
```

**Detection hint:** Any code that calls `update()` or HTTP PATCH on a `FieldDefinition` Tooling API object targeting `complianceGroup` is using an unreliable write path.

---

## Anti-Pattern 3: Including Full Standard Field Definition in Stub Files

**What the LLM generates:** A `.field-meta.xml` file for a standard field (e.g., `Contact.Email`) that includes the field's type, length, label, or other intrinsic attributes alongside classification elements.

**Why it happens:** LLMs copy field metadata templates that include the full `CustomField` structure. When asked to classify a standard field, they use the same template without recognizing that standard fields cannot have their intrinsic attributes overridden via metadata deploy.

**Correct pattern:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Stub for standard field Contact.Email — classification attributes only -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Email</fullName>
    <securityClassification>Confidential</securityClassification>
    <complianceGroup>PII</complianceGroup>
    <businessStatus>Active</businessStatus>
</CustomField>
```

**Detection hint:** A stub file for a standard field (no `__c` suffix on the fullName) that contains `<type>`, `<length>`, `<label>`, or `<required>` elements is using the wrong template and will fail on deploy.

---

## Anti-Pattern 4: Treating Einstein Data Detect as Full Classification Coverage

**What the LLM generates:** Instructions that end with "run Einstein Data Detect and accept all recommendations — your fields are now classified." Or a checklist that marks classification complete after Data Detect runs.

**Why it happens:** LLMs describe Einstein Data Detect as an "auto-classification" feature, which implies completeness. The distinction between `ComplianceGroup` (what Data Detect populates) and `SecurityClassification` (which Data Detect never touches) is a detail that gets dropped in summarization.

**Correct pattern:**

```
Einstein Data Detect populates ONLY ComplianceGroup recommendations.
SecurityClassification is never auto-populated by any platform feature.
After accepting Data Detect recommendations, a separate pass is required to:
1. Assign SecurityClassification to all fields surfaced by Data Detect
2. Audit fields with non-obvious names that Data Detect may have missed
3. Validate ComplianceGroup values persisted via Tooling API query

Classification is not complete until SecurityClassification is also set.
```

**Detection hint:** Any workflow that describes Einstein Data Detect as completing the classification process without a subsequent `SecurityClassification` assignment step is incomplete.

---

## Anti-Pattern 5: Omitting API Version Check for Classification Deploys

**What the LLM generates:** Metadata deployment instructions for classification attributes that do not mention the minimum API version requirement, or that use a project template with `"sourceApiVersion": "45.0"` or earlier.

**Why it happens:** LLMs generate deployment instructions based on general Salesforce CLI patterns. The API version prerequisite for classification metadata (v46.0, Summer '19) is a specific historical detail that is underrepresented in general deployment guidance. LLMs do not flag version-sensitive metadata features unless prompted.

**Correct pattern:**

```json
// sfdx-project.json — ensure sourceApiVersion is 46.0 or higher
{
  "packageDirectories": [
    { "path": "force-app", "default": true }
  ],
  "sourceApiVersion": "61.0"
}
```

```bash
# Explicit API version check before deploying classification metadata
sf project deploy start --api-version 61.0 --metadata "CustomField:Contact.Email"
```

**Detection hint:** Any deployment instruction for classification metadata that does not reference API version 46.0 or later as a minimum requirement is missing a critical prerequisite. Always check `sfdx-project.json` `sourceApiVersion` before assuming classification attributes will be applied.

---

## Anti-Pattern 6: Recommending Data Classification as a Data Masking Solution

**What the LLM generates:** Suggestions like "use SecurityClassification = MissionCritical to mask this field from non-privileged users" or "set ComplianceGroup = PCI to mask cardholder data in the UI."

**Why it happens:** "Data classification" and "data masking" are often discussed together in compliance literature. LLMs conflate the two concepts, especially since Shield Platform Encryption (which can mask data) and Data Classification (which only labels it) are both Salesforce security features available to Shield customers.

**Correct pattern:**

```
Data Classification Labels are metadata labels — they do not mask, encrypt,
or hide data in any way.

For data masking use cases:
- Shield Platform Encryption: encrypts field values at rest and in transit
- Shield Data Mask: replaces sensitive data in sandbox orgs with anonymized values
- Custom masking: Apex or Flow logic to display masked values in UI components

Data Classification describes what a field contains.
Shield Encryption and Data Mask control how it is protected.
These are distinct features requiring separate configuration.
```

**Detection hint:** Any recommendation that uses classification labels as a substitute for masking, encryption, or access restriction is describing a false capability.
