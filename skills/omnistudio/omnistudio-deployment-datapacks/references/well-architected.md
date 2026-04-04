# Well-Architected Notes — OmniStudio Deployment DataPacks

## Relevant Pillars

### Operational Excellence

DataPacks are the primary mechanism for bringing OmniStudio deployments under operational control. Without DataPack-based version control and CI/CD:

- OmniStudio components exist only as org records with no audit trail
- Changes cannot be reviewed before promotion
- Rollback requires manually re-creating the prior component state from memory or screenshots
- Cross-environment parity cannot be verified

Using DataPacks with Git as the system of record gives teams the same operational properties for OmniStudio that SFDX metadata deployment provides for Apex and configuration metadata: a reviewable, reproducible, rollback-capable delivery pipeline. The Salesforce Well-Architected Framework's Operational Excellence pillar explicitly requires observable, repeatable, and recoverable deployment processes — DataPack CI/CD satisfies all three for OmniStudio components.

### Reliability

Reliability failures in DataPack deployments most commonly take two forms: the import succeeds but the component is in an incorrect state (inactive, with broken references, or with missing environment-specific data), and the import fails at a dependency boundary leaving the org in a partially promoted state.

Designing for reliability means:
- Including full dependency closures in every DataPack set so imports are atomic from a component-graph perspective
- Using `--activate` to ensure post-import state is consistent with deployment intent
- Implementing environment-specific override mechanisms so components do not carry hardcoded source-org values that produce runtime failures in the target
- Running post-import smoke tests before marking a deployment complete

### Security

DataPack JSON files committed to Git contain the full component definition, including any hardcoded values inside element configurations. If a practitioner has embedded API credentials, access tokens, or sensitive endpoint URLs inside an OmniStudio element (a common shortcut in development), those values will be captured verbatim in the DataPack JSON and committed to Git. Scan DataPack output for secrets before committing. Enforce a policy that credentials always live in Named Credentials, not inside component element configurations.

---

## Architectural Tradeoffs

**Full dependency closure vs. targeted export:** Exporting with `--maxDepth -1` guarantees completeness but produces larger DataPack sets with more components per import job. Targeted exports (only the changed component) are faster but require that the target org already has consistent dependency versions. For orgs with a stable shared baseline, targeted export is acceptable. For fresh targets or after major changes to shared components, full-closure export is the safe default.

**Activation as part of import vs. separate activation step:** Including `--activate` in the import simplifies the pipeline but means a partially failed import (some components succeed, some fail) may activate inconsistent component versions in the target. A two-phase approach — import all components first, verify all show Success, then activate — gives a checkpoint between the two operations at the cost of added pipeline complexity.

**DataPacks-only vs. hybrid SFDX + DataPacks:** OmniStudio components that have been converted to standard platform metadata (LWC-based OmniStudio in Standard mode) may support SFDX metadata deployment in addition to DataPacks. Teams should verify whether their org uses managed package or standard mode before defaulting to DataPacks as the only option. In standard mode, some component types can be deployed via SFDX, which integrates more naturally with existing DevOps tooling.

---

## Anti-Patterns

1. **Manual export and import without Git as the source of record** — Teams that export DataPacks ad hoc, import directly to production, and never commit the JSON to source control lose the change audit trail entirely. If a production component needs to be rolled back, there is no prior state to restore from. The org becomes the single source of truth, which means any accidental change — including one made by a developer testing in production — is irreversible without re-authoring from memory. Always commit DataPack exports to Git before importing to any promoted environment.

2. **Importing without environment-specific value substitution** — Deploying DataPack JSON verbatim from a development org to production without replacing Named Credential names, endpoint URLs, or Custom Setting references embeds environment-specific assumptions in production. Components appear to import successfully but fail at runtime with cryptic errors (`Named Credential not found`, `null response from HTTP action`) because the source-org values do not exist in production. Establish an environment override map and apply it as a pipeline step on every import.

3. **Treating the vlocity CLI as a point-in-time tool rather than a pipeline citizen** — Running `packDeploy` manually from a developer laptop introduces the same risks as manual SFDX deployment: no reproducibility, no audit trail, no rollback. The DataPack tooling is designed to be executed in automated pipelines with authenticated connected app credentials, not developer session tokens. Formalise the deployment mechanism in a pipeline YAML before the first production promotion.

---

## Official Sources Used

- OmniStudio DataPacks (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.os_datapacks.htm
- OmniStudio DataPacks Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.salesforce_vlocity_omnistudio.meta/salesforce_vlocity_omnistudio/omnistudio_datapacks.htm
- OmniStudio Developer Guide (vlocity Build Tool) — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- Salesforce Well-Architected — Operational Excellence — https://architect.salesforce.com/well-architected/operational-excellence
- Salesforce Well-Architected — Reliability — https://architect.salesforce.com/well-architected/reliability
