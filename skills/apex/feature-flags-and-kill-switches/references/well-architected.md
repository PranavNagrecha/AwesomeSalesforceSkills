# Well-Architected Notes — Feature Flags And Kill Switches

## Relevant Pillars

- **Security** — Feature flags control access to functionality. Custom Permissions integrate directly with Salesforce's permission model, ensuring that feature gating respects the platform's native authorization framework. Kill switches that disable integration callouts reduce the attack surface during incidents. Poorly implemented flags (e.g., checking a text field value instead of a boolean, or trusting client-side flag evaluation) can create authorization bypass vulnerabilities.

- **Reliability** — Kill switches are fundamentally a reliability pattern. They allow teams to disable malfunctioning features in production without code deployments, reducing mean time to recovery (MTTR) from hours to seconds. A feature that cannot be turned off at runtime is a feature that can only be fixed by deploying under pressure — the most error-prone scenario possible. Every integration callout, complex trigger chain, and batch process should have a kill switch.

- **Operational Excellence** — Feature flags enable trunk-based development and continuous delivery by decoupling deployment from release. Code can be deployed to production behind a flag set to `false`, validated in the production environment, and then enabled by flipping the flag. This eliminates the "big bang" release anti-pattern and supports incremental rollout. Flag hygiene — tracking, documenting, and cleaning up temporary flags — is an operational discipline that prevents technical debt accumulation.

- **Scalability** — CMDT and Custom Settings are cached at the application server level and do not consume SOQL queries. This means feature flag checks have near-zero performance overhead even at scale. In contrast, querying a Custom Object for flag state would consume SOQL limits and degrade under high transaction volumes.

## Architectural Tradeoffs

The primary tradeoff is between **deployment consistency** and **runtime flexibility**:

- **CMDT** maximizes deployment consistency. Records deploy with metadata, so all environments stay in sync. But changes require a metadata deployment (even if it is just a record edit via Setup UI), which means you cannot flip a flag from within Apex code.
- **Hierarchical Custom Settings** maximize runtime flexibility. Values can be changed via DML in Apex, scheduled jobs, or anonymous Apex. But values are data, not metadata, so they drift between environments unless scripted.
- **Custom Permissions** sit in between. They are metadata (deployable), but the assignment of permission sets to users is data (per-environment). They are the only mechanism available in declarative contexts like formula fields, validation rules, and flows.

The second tradeoff is **flag granularity vs. complexity**:

- A single `FeatureFlag__mdt` object with one record per feature is simple but limited to org-wide scope.
- Adding user/profile scoping requires Custom Permissions or Custom Settings, which increases the number of moving parts.
- Combining mechanisms (e.g., CMDT for org-wide kill switch plus Custom Permission for user-scoped rollout) is powerful but requires clear documentation to avoid confusion about which flag takes precedence.

## Anti-Patterns

1. **Scattering raw getInstance() calls throughout the codebase** — When flag checks are duplicated across triggers, services, and controllers, renaming or removing a flag requires a multi-file search-and-replace. Centralize all flag reads in a single utility class (`FeatureFlags.isEnabled('Name')`) so there is one place to change the implementation and one place to add test overrides.

2. **Defaulting to "enabled" when a flag record is missing** — If `getInstance()` returns null and the code treats that as `true`, then a missing CMDT record (due to a failed deployment or sandbox refresh) silently enables a feature that was supposed to be gated. Always default to `false` (disabled) on null. A missing kill switch should kill the feature, not enable it.

3. **Never cleaning up temporary flags** — Feature flags introduced for a one-time rollout that are never removed become permanent dead code. Over time, the codebase accumulates branching logic for flags that have been `true` in all environments for years. Establish a flag registry with an expiration date and schedule cleanup sprints to remove flags whose rollout is complete.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- FeatureManagement Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_FeatureManagement.htm
- CustomPermission Metadata Type — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_custompermission.htm
- Custom Metadata Type Methods — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_methods_system_custom_metadata_types.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
