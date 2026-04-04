# Well-Architected Notes — Sandbox Data Masking

## Relevant Pillars

- **Security** — Primary pillar. Sandbox data masking directly enforces data protection by design (GDPR Article 25). Non-production environments that contain unmasked PII are a hidden security risk surface: they are often less tightly controlled than production (broader profile access, developer tooling, export capabilities) yet hold real customer data. Data Mask reduces blast radius from sandbox credential compromise or insider access.

- **Operational Excellence** — Data Mask configured with SandboxPostCopy automation removes the human-in-the-loop dependency from the post-refresh compliance gate. This reduces the probability of an engineer accessing real data during the window between refresh completion and manual masking. Automation also reduces mean time to sandbox readiness by eliminating the manual coordination step.

- **Reliability** — Correctly configured masking policies prevent test failures caused by data format assumptions breaking when test data changes. Deterministic masking in particular ensures cross-object FK relationships remain consistent, avoiding intermittent test failures that look like code bugs.

## Architectural Tradeoffs

| Decision | Tradeoff |
|---|---|
| Pseudonymous vs. Deterministic masking | Pseudonymous is simpler and produces more varied test data. Deterministic is required when the same value must be consistent across related objects. Use Deterministic only where referential integrity is validated by tests; otherwise Pseudonymous is preferred. |
| Null/Delete vs. replacement masking | Null is the simplest and leaves no residual data. However it fails on required fields and eliminates test coverage for format-sensitive logic. Prefer replacement masking for fields that drive workflow or validation logic. |
| SandboxPostCopy automation vs. manual run | SandboxPostCopy eliminates the human window of exposure. It adds Apex maintenance overhead and requires the Data Mask package to be stable at refresh time. For infrequently refreshed sandboxes, manual is acceptable with a documented runbook and access gate. |
| Data Mask vs. synthetic data seeding | Data Mask is faster to set up for existing production-refresh workflows. Synthetic seeding (no production data in the sandbox at all) is architecturally cleaner and eliminates the masking problem entirely, but requires significant upfront investment in data factories. For orgs with complex data models, Data Mask is a pragmatic bridge. |

## Anti-Patterns

1. **Treating Field-Level Security as a data masking control** — FLS controls UI and API visibility for a given profile/permission set, but System Administrator profiles and anonymous Apex bypass it. FLS is an access control, not an anonymization control. Orgs that rely on FLS to protect sandbox PII are non-compliant with GDPR/HIPAA requirements for de-identification. Data Mask is the correct tool.

2. **Configuring masking after granting sandbox access** — Teams that refresh a sandbox and grant developer access first, then run Data Mask afterward, create a window where real PII is accessible to non-production users. The correct sequence is: refresh → run Data Mask → verify masking → grant access. Automate this sequence to eliminate the window.

3. **Masking only the primary object and ignoring derived copies** — Masking Contact.Email without also masking the same email value stored on Case, custom objects, or integration-written fields gives a false sense of compliance. A full field-coverage audit against the org data model is required before declaring masking complete.

## Official Sources Used

- Salesforce Data Mask Overview — https://help.salesforce.com/s/articleView?id=sf.data_mask_overview.htm
- Salesforce Well-Architected Guide Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Shield Platform Encryption Implementation Guide — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm&type=5
- SandboxPostCopy Interface (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_interface_System_SandboxPostCopy.htm
