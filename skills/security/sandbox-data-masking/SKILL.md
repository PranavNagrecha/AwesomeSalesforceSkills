---
name: sandbox-data-masking
description: "Use this skill when configuring or reviewing Salesforce Data Mask to protect PII/PHI in partial or full copy sandboxes after a refresh. Trigger keywords: data mask, sandbox masking, PII in sandbox, GDPR sandbox, HIPAA non-production, mask contacts, obfuscate fields non-production. NOT for sandbox refresh mechanics (use sandbox-refresh-and-templates), NOT for production data anonymization, NOT for Shield Platform Encryption at rest."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "developers can see real customer email addresses in the sandbox after refresh"
  - "how do I mask PII fields in a full copy sandbox before giving access to QA"
  - "we need to comply with GDPR and stop copying personal data into non-production environments"
  - "what masking types does Salesforce Data Mask support and which field types can I mask"
  - "data mask job failed after sandbox refresh and contacts still have real phone numbers"
tags:
  - sandbox-data-masking
  - data-privacy
  - pii-protection
  - gdpr
  - hipaa
  - compliance
inputs:
  - "Sandbox type: partial copy or full copy (Data Mask is not available for developer/developer pro sandboxes)"
  - "List of objects and fields containing PII or PHI"
  - "Compliance requirements: GDPR, HIPAA, CCPA, or internal data governance policy"
  - "Whether Shield Platform Encryption is enabled on any target fields"
  - "Whether Big Objects or External Objects are in scope"
outputs:
  - "Data Mask configuration plan: object/field coverage, masking type per field"
  - "Post-refresh runbook for triggering the Data Mask job"
  - "Compliance gap list: fields not maskable due to platform limitations"
  - "Review checklist for confirming masking completed before granting sandbox access"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Sandbox Data Masking

This skill activates when a team needs to configure Salesforce Data Mask to protect sensitive data (PII, PHI, or regulated information) in partial copy or full copy sandboxes, or when investigating why a masking job did not run correctly after a sandbox refresh.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Sandbox type**: Data Mask requires a partial copy or full copy sandbox. It is not available for Developer or Developer Pro sandboxes. Confirm the sandbox tier before scoping the work.
- **Licensing**: Data Mask is a paid add-on. Confirm the org has the Data Mask permission set license assigned before attempting configuration.
- **Encrypted fields**: Fields protected by Shield Platform Encryption cannot be masked by Data Mask. Attempting to configure masking on an encrypted field will silently skip the field; the real value remains. This is the most common wrong assumption.
- **Big Objects and External Objects**: Data Mask does not support these. Plan separately for any PII stored there.
- **Field type support**: Data Mask supports Text, Email, Phone, TextArea, URL, and certain custom field types. Formula fields, Roll-up Summaries, and encrypted fields are not maskable.

---

## Core Concepts

### What Salesforce Data Mask Is

Salesforce Data Mask is a managed package from Salesforce Labs (licensed as an add-on) that runs inside your org and transforms field values in sandbox environments after a refresh. It does not move data outside Salesforce — the masking jobs execute as Apex batch jobs against the sandbox org's data directly. Data Mask is available only in partial copy and full copy sandboxes.

Data Mask is configured through a declarative UI (the Data Mask app installed from AppExchange). You define masking policies at the object and field level, then run the policy manually or trigger it via the SandboxPostCopy interface so it fires automatically at the end of a sandbox refresh.

### Masking Types

Data Mask provides three masking strategies per field:

1. **Pseudonymous (Pattern-based replacement)**: Replaces values with realistic but fake values using Salesforce's internal data library. For example, a real name "Jane Smith" becomes "Carlos Rivera." This preserves referential integrity for testing workflows that validate name formats or email delivery.
2. **Deterministic**: The same input always produces the same output within a single masking run, preserving uniqueness constraints and enabling consistent cross-object join testing. Useful when you need masked data to be consistent across related records (e.g., Contact email matches the User login email for the same person).
3. **Null/Delete**: Replaces field values with null or blank. The simplest option; use when the field value is irrelevant to testing. Cannot be used on required fields — the job will error on required fields configured for null masking.

### Compliance Scope

Under GDPR, HIPAA, and CCPA, personal data copied to non-production environments must be protected equivalently to production, or anonymized. Data Mask satisfies the anonymization requirement when configured for all relevant fields. A masking policy that misses even one object containing personal data — such as a custom object storing payment reference numbers — means the sandbox is still in scope for compliance obligations. Always cross-reference masking coverage against the org's data inventory or Record Information Architecture.

---

## Common Patterns

### Pattern 1: Automated Post-Refresh Masking via SandboxPostCopy

**When to use:** Any org running a full copy or partial copy sandbox on a recurring refresh cadence where manual steps cause compliance gaps or human error.

**How it works:**
1. Create an Apex class that implements `SandboxPostCopy` and calls the Data Mask API to kick off the saved masking configuration.
2. Register the class in the sandbox definition or in the sandbox request through the SandboxPostCopy interface.
3. When the sandbox refresh completes, Salesforce invokes the class automatically. Data Mask runs its batch jobs before the sandbox becomes accessible.

The Data Mask managed package exposes an invocable Apex interface. Your `SandboxPostCopy` class calls it by name using `Type.forName` to avoid a hard compile-time dependency:

```apex
global class MaskAfterRefresh implements SandboxPostCopy {
    global void runApexClass(SandboxContext ctx) {
        Type dataMaskType = Type.forName('DataMask', 'DataMaskFacade');
        if (dataMaskType != null) {
            Object facade = dataMaskType.newInstance();
            // invoke the run method via reflection or interface cast
            // actual method name: DataMaskFacade.runConfiguration(String configName)
        }
    }
}
```

**Why not manual:** Manual post-refresh masking relies on a human remembering to run the job. In practice, developers request sandbox access before masking is complete, exposing real data. Automation removes the window of exposure.

### Pattern 2: Field Coverage Audit Before Enabling Sandbox Access

**When to use:** Before granting any developer or QA access to a newly refreshed full copy sandbox.

**How it works:**
1. Export the Data Mask configuration as a CSV or screenshot for each object.
2. Cross-reference against the org data dictionary or the fields marked as "Contains PII" in your custom metadata.
3. Run a SOQL spot-check on a known PII field (e.g., `SELECT Email FROM Contact LIMIT 1`) and confirm the value does not match a known production email format (e.g., a real domain rather than `@example.com`).
4. Lock the sandbox profile to a read-only permission set until the audit is complete.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Real customer emails must not appear in sandbox | Pseudonymous masking on Email fields | Preserves valid email format for workflow testing without exposing real addresses |
| Cross-object FK integrity needed after masking | Deterministic masking on shared key fields | Same input always yields same output, so joins still resolve correctly |
| Field value is irrelevant to any test scenario | Null/Delete masking | Simplest, fastest; eliminates all residual data risk |
| Field is encrypted with Shield Platform Encryption | No Data Mask option; plan alternative | Data Mask cannot access encrypted field values; must use a separate anonymization strategy or deprovision encrypted data before copy |
| PII exists in a Big Object | Out of scope for Data Mask | Big Objects are not supported; document as compliance exception with manual remediation plan |
| Developer sandbox tier requested | Upgrade to partial copy or use seeded data | Data Mask is unavailable; advise against copying production data to Developer sandbox at all |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking sandbox access as compliant:

- [ ] Data Mask licensed and permission set assigned to the running user
- [ ] All objects containing PII/PHI fields identified and mapped to a masking policy
- [ ] No encrypted fields configured in the masking policy (verify field-by-field)
- [ ] Big Objects and External Objects documented as out-of-scope with remediation plan if they contain PII
- [ ] Required fields not configured for Null/Delete masking
- [ ] Masking job completed without errors (check Data Mask job log in the app)
- [ ] SOQL spot-check confirms masked values on at least Contact.Email, Contact.Phone, and any custom PII fields
- [ ] SandboxPostCopy automation tested on the most recent refresh cycle
- [ ] Sandbox access not granted until masking job log shows successful completion

---

## Salesforce-Specific Gotchas

1. **Encrypted fields are silently skipped** — Data Mask does not throw an error when a Shield-encrypted field is included in the masking policy. It silently skips those fields and the real encrypted value remains in the sandbox. There is no warning in the job log. Verify by checking which fields have Shield encryption enabled in Setup > Platform Encryption, and remove them from the masking policy entirely; handle separately.

2. **Required fields configured for Null masking cause batch abort** — If a field with a Required field-level setting is configured for Null/Delete masking, the batch job aborts mid-run with a DML error. Because Data Mask processes records in batches, some records may already be masked while others retain original values when the job aborts. Always verify required vs. optional field settings before configuring Null masking.

3. **Data Mask does not cascade to lookup-related objects automatically** — If you mask `Contact.Email` but the same email address appears on a related custom object (e.g., `Support_Request__c.Requester_Email__c`), that field retains the real value unless explicitly included in the masking policy. The masking configuration is per-field; there is no automatic relationship traversal. Cross-reference against all objects that copy or mirror PII fields.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data Mask configuration plan | Object-by-object, field-by-field mapping of masking type, documenting any excluded fields and the reason |
| Post-refresh runbook | Step-by-step instructions for running Data Mask after each sandbox refresh, including who runs it and access control gates |
| Compliance gap register | List of fields not maskable due to platform limitations (encrypted fields, Big Objects) with remediation or acceptance notes |
| SOQL spot-check queries | Ready-to-run queries to verify masking effectiveness on key PII fields after a job completes |

---

## Related Skills

- `sandbox-refresh-and-templates` — covers sandbox refresh mechanics, SandboxPostCopy wiring, and sandbox template selection; use alongside this skill when configuring automated post-refresh masking
- `sandbox-strategy` — covers org environment topology and when to use each sandbox type; informs whether Data Mask is even needed for a given environment
