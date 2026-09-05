# Well-Architected Mapping: Change Management and Deployment

## Pillars Addressed

### Operational Excellence

Release methods, approvals, and validation steps are core operating mechanisms, not paperwork.

- Source-driven deployment reduces manual variance.
- Checklists and promotion rules make releases repeatable.

### Reliability

Reliable releases depend on realistic validation and credible rollback.

- Explicit sequencing reduces surprise regressions.
- Smoke tests and rollback plans shorten incident duration when things go wrong.

### Security

Permissions, sharing, and integration metadata often ride in deployments and need tighter review than ordinary layout changes.

- High-risk metadata gets explicit scrutiny before promotion.
- Environment-aligned auth and permission handling reduces accidental exposure.

## Pillars Not Addressed

- **User Experience** - this skill improves user outcomes indirectly through safer releases, not through interface design itself.
- **Scalability** - the emphasis is release discipline rather than runtime scale design.

## Official Sources Used

- Metadata API Developer Guide, `deploy()` → `DeployOptions`
  (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) —
  `checkOnly`, `rollbackOnError` ("must be set to `true` if you're deploying to a
  production org"), `purgeOnDelete`, `ignoreWarnings`, `allowMissingFiles`,
  `performRetrieve`, `singlePackage`, and the `testLevel` enum with its per-environment
  defaults. Grounds "The Deploy Contract" in SKILL.md, `references/metadata-examples.md`
  §3, and the `rollbackOnError`, test-level, `purgeOnDelete`, and Master-Detail gotchas.
- Metadata API Developer Guide, "Deleting Components from an Organization" — the
  `destructiveChanges.xml` / `destructiveChangesPre.xml` / `destructiveChangesPost.xml`
  contract, the companion `package.xml` requirement, the no-wildcards rule, and
  "post destructive changes are processed before running any tests". Grounds
  `references/metadata-examples.md` §2 and the destructive-manifest gotcha.
- Metadata API Developer Guide, `deployRecentValidation()` and "Deploy a Recently
  Validated Component Set Without Tests" — the ten-day quick-deploy window, the
  target-environment constraint, and the two coverage rules. Grounds the quick-deploy
  gotcha and the validate → quick → report sequence.
- Metadata API Developer Guide, "Deploying and Retrieving Metadata with the Zip File",
  `DeployResult`, `DeployMessage`, `RunTestsResult`, `cancelDeploy()`, and the
  Deployment Status / deploy-limits sections of `deploy()` — the manifest element
  reference, the nine-value `DeployStatus` enum including `SucceededPartial`, the fields
  to read when verifying a release, the write-lock and single-concurrent-deploy
  behaviour, and the absence of any reverse operation. Grounds
  `references/metadata-examples.md` §1, §5, §6 and the concurrency gotcha.
- Metadata API Developer Guide, Profile metadata type — "We designed Profile metadata
  deployment to overlay the existing Profile settings in a target org". Grounds the
  "Profiles are release debt" guardrail; the mechanism itself is owned by
  `admin/permission-sets-vs-profiles`, which this skill defers to rather than restates.
- Metadata API Developer Guide, FlowDefinition and Flow metadata types — "If you deploy
  with flow definitions, the active version numbers in the flow definitions override the
  `status` fields in the flows", plus the `FlowVersionStatus` values. Grounds the Flow
  activation gotcha.
- Salesforce App Limits Cheat Sheet, Metadata Limits and Apex Governor Limits
  (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf)
  — 10,000 files per deploy or retrieve, ~39 MB compressed / 600 MB uncompressed, 10,000
  files per inbound or outbound change set, and 7,500 class and trigger code units per
  Apex deployment. Grounds the deploy-size gotcha and the Change Set ceiling.
- Salesforce Object Reference, `DevopsEnvDeployment`
  (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf)
  — a queryable record of DevOps Center promotions with `DeployStatus` and
  `CheckDeployStatus` picklists, API version 66.0 and later. Grounds the SOQL
  verification in `references/metadata-examples.md` §5.
- Salesforce Well-Architected — operational-quality framing for release design; supports
  the Operational Excellence and Reliability sections above.
