# Well-Architected Notes — Sandbox Refresh and Templates

## Relevant Pillars

### Reliability

Sandbox refresh reliability is foundational to release pipelines. Orgs that rely on manual post-refresh steps are one missed checklist item away from a broken test environment blocking a release.

- Automated post-refresh setup via SandboxPostCopy eliminates manual error from the critical path.
- Aborting scheduled jobs in SandboxPostCopy prevents sandbox jobs from corrupting production-adjacent external systems.
- Template-driven Partial Copy sandboxes produce consistent, repeatable data sets across refresh cycles, reducing "it works on my machine" failures caused by environment drift.

### Operational Excellence

Refresh cadence, ownership, and runbook quality directly determine how much operational overhead sandbox management consumes.

- Documenting which sandboxes are refreshed, when, and by whom prevents refresh collisions that destroy uncommitted developer work.
- A pre-refresh checklist (interval check, template review, SandboxPostCopy registration) makes refresh a repeatable, low-risk operation rather than an ad-hoc admin task.
- A post-refresh manual runbook captures all steps that cannot be automated (Named Credentials, email deliverability) so the right person executes them every time.
- Keeping the SandboxPostCopy class in version control alongside the rest of the codebase ensures refresh automation evolves with the org.

### Security

Sandboxes that contain unmasked production PII or that fire scheduled jobs against production endpoints represent real security and data integrity risks.

- PII masking in SandboxPostCopy (or a Queueable delegated from it) ensures real customer data does not remain accessible to all sandbox users.
- Email deliverability should be set to "System Email Only" in sandboxes that should not send to real email addresses. This cannot be automated via Apex and must be part of the manual post-refresh runbook.
- Named Credentials with production secrets should not be reused in sandboxes — use sandbox-specific credentials where possible.

### Performance

Sandbox template design has a direct impact on the time and cost of Partial Copy refresh cycles.

- Over-specified templates with high record counts slow refresh and consume sandbox storage, approaching Full sandbox cost without Full sandbox isolation.
- Under-specified templates produce missing reference data that causes test failures — find the minimum viable template that covers all test scenarios.

---

## Architectural Tradeoffs

| Decision | Tradeoff |
|---|---|
| SandboxPostCopy vs. manual runbook | SandboxPostCopy is faster and less error-prone but requires Apex skill and version control discipline. Manual runbooks are simpler to set up but degrade over time as org configuration changes. |
| Partial Copy with template vs. Developer sandbox + data loading | Partial Copy gives a near-production data shape but is non-deterministic and has a 5-day interval. A Developer sandbox with scripted test data loading is fully deterministic and can be refreshed daily but requires maintaining data scripts. |
| Masking in SandboxPostCopy vs. Data Mask product | SandboxPostCopy masking is free and flexible but requires custom Apex and does not have field-level policy management. Salesforce Data Mask is a licensed product that provides policy-driven masking without custom code. |

---

## Anti-Patterns

1. **No SandboxPostCopy class registered** — Every refresh requires a multi-hour manual runbook. A single missed step breaks integrations or allows scheduled jobs to fire against production systems. Register and maintain a SandboxPostCopy class for every sandbox that refreshes regularly.

2. **Hardcoded org IDs in code or configuration** — Org IDs change on every refresh. Any component that stores a hardcoded org ID will fail after the first refresh. Always resolve the current org ID at runtime from a mutable custom setting updated by SandboxPostCopy.

3. **Partial Copy sandbox without a template** — Without a template, the data set is random and non-deterministic. Tests that depend on specific parent records or reference data will fail intermittently. Always attach a template to a Partial Copy sandbox before refreshing.

4. **PII in sandbox without masking** — Real customer data in developer or QA sandboxes is a data governance and GDPR/CCPA risk. Any sandbox that receives production data (Partial Copy, Full) must have a masking strategy before it is accessible to non-production users.

---

## Official Sources Used

- Apex Reference Guide — SandboxPostCopy interface definition, SandboxContext method signatures
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_System_SandboxPostCopy.htm

- Apex Developer Guide — SandboxPostCopy interface usage and examples
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_interface_System_SandboxPostCopy.htm

- Salesforce Help: Refresh Your Sandbox — refresh steps, interval behavior, status tracking
  https://help.salesforce.com/s/articleView?id=platform.data_sandbox_refresh.htm&language=en_US&type=5

- Salesforce Help: Create or Edit Sandbox Templates — template definition for Partial Copy sandboxes
  https://help.salesforce.com/s/articleView?id=platform.data_sandbox_templates.htm&language=en_US&type=5

- Salesforce Help: Sandbox Licenses and Storage Limits by Type — refresh intervals per sandbox type
  https://help.salesforce.com/s/articleView?language=en_US&id=sf.data_sandbox_environments.htm&type=5

- Salesforce Well-Architected Overview — Reliability and Operational Excellence quality framing
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
