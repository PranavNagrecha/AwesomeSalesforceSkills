# Well-Architected Notes — Source Tracking and Conflict Resolution

## Relevant Pillars

- **Operational Excellence** — Source tracking is a core operational mechanism for reliable metadata lifecycle management. Well-Architected operational excellence requires that changes are traceable, deployments are repeatable, and the team has clear procedures for resolving divergent state. Conflict resolution procedures and sandbox tracking enablement policies are operational runbooks, not one-off fixes.

- **Reliability** — Source tracking corruption and unresolved conflicts are failure modes that silently degrade reliability. A tracking system that is occasionally reset by sandbox refreshes without a clear recovery procedure creates unpredictable deploy outcomes. The skill's recovery patterns (delete stale tracking directory, re-retrieve) restore the reliable baseline state.

- **Security** — The `.sf/` tracking directory contains org ID references and local metadata revision state. It must not be committed to Git (preventing information leakage about org topology) and must not be shared between developers (preventing one developer's tracked state from silently overwriting another's). `.gitignore` hygiene for tracking files is a security and operational concern.

## Architectural Tradeoffs

**Org-wins vs local-wins resolution:** Every conflict requires an explicit decision about which version of a component is authoritative. There is no automatic three-way merge for Salesforce metadata XML (unlike code). The tradeoff is between speed (force overwrite one side) and correctness (manual merge of both versions). For complex metadata types (page layouts, permission sets, profiles), silent overwrites are high-risk because the XML structure can contain dozens of independent sections that merge independently in meaning but conflict as a single file.

**Source-tracking-aware commands vs explicit manifest deploys:** Source tracking provides delta-deploy efficiency but requires maintaining tracking state. In CI environments where state is ephemeral, tracking-aware commands add overhead. Explicit `package.xml`-based deploys are more predictable in stateless CI pipelines at the cost of always deploying the full manifest scope. The right choice depends on team size, sandbox refresh frequency, and whether CI tracking state can be cached.

**Sandbox source tracking enablement:** Enabling source tracking in sandboxes enables richer developer workflows but increases resource usage on the platform side (the `SourceMember` object grows as components change). For very large orgs with many developers sharing one sandbox, `SourceMember` query volume can become a concern. Evaluate whether scratch-org-per-developer patterns are a better fit for high-change-velocity teams.

## Anti-Patterns

1. **Committing `.sf/` tracking files to Git** — tracking files are local, machine-specific revision state. Committing them causes conflicts between team members and makes the tracking system unreliable since different developers may receive different tracking state on clone. The `.sf/` directory must always be in `.gitignore`.

2. **Using `--ignore-conflicts` as the default deploy/retrieve flag without understanding which version is authoritative** — treating `--ignore-conflicts` as a "just make it work" shortcut without the explicit local-wins or org-wins decision causes silent data loss. The correct pattern is to always determine which version is correct before choosing the flag.

3. **Assuming source tracking covers all metadata types** — automating retrieves that rely on tracking to detect changes will miss components that are not source-tracked (see Metadata Coverage Report). Critical configuration metadata that is not tracked can drift silently between org and source control.

## Official Sources Used

- Salesforce DX Developer Guide — source tracking mechanics, `SourceMember` object behavior, conflict detection, sandbox source tracking enablement
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_source_file_format.htm

- Salesforce DX Developer Guide — Enable Source Tracking in Sandboxes
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_setup_enable_source_tracking_sandboxes.htm

- Salesforce CLI Command Reference — `sf project retrieve start`, `sf project deploy start`, `--ignore-conflicts` flag
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_project_retrieve_start.htm

- Salesforce Metadata Coverage Report — tracking coverage by metadata type
  URL: https://developer.salesforce.com/docs/metadata-coverage

- Salesforce Well-Architected: Operational Excellence — repeatable deployments, runbook discipline
  URL: https://architect.salesforce.com/well-architected/operational-excellence
