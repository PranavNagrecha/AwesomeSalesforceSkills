---
name: omnistudio-ci-cd-patterns
description: "Use when designing or implementing CI/CD pipelines for OmniStudio components — DataPack export/import, versioning, environment promotion, and automated deployment. NOT for standard Salesforce metadata CI/CD or Apex-only pipelines."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "How do I deploy OmniStudio components between sandboxes without losing the active version?"
  - "My DataPack import succeeded but the OmniScript is not live — what went wrong?"
  - "How do I include OmniStudio in a GitHub Actions or Bitbucket CI/CD pipeline?"
  - "What is the difference between DataPack deployment and SFDX metadata deploy for OmniStudio?"
  - "OmniStudio DataPack deploy is not activating components after import"
tags:
  - omnistudio
  - cicd
  - datapack
  - deployment
  - omnistudio-ci-cd-patterns
  - devops
inputs:
  - "Org runtime type: Package Runtime (managed package) or Standard/Core Runtime"
  - "Source and target environment (e.g., dev sandbox to UAT to production)"
  - "OmniStudio component types to deploy (OmniScript, Integration Procedure, DataRaptor, etc.)"
  - "CI/CD platform in use (GitHub Actions, Bitbucket Pipelines, Jenkins, etc.)"
outputs:
  - "Deployment path decision: DataPack-based (Package Runtime) vs. Metadata API/SFDX (Standard Runtime)"
  - "DataPack export job file configuration for the OmniStudio Build Tool"
  - "Pipeline steps for DataPack export, import, and activation"
  - "Post-deployment verification checklist"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# OmniStudio CI/CD Patterns

This skill activates when a practitioner needs to include OmniStudio components in a CI/CD pipeline or promote components between environments. It covers the two distinct deployment paths — DataPack-based for Package Runtime vs. Metadata API/SFDX for Standard Runtime — the activation requirement after DataPack import, and the evolving Salesforce roadmap for unified deployment.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Determine the org runtime before selecting any tooling**: OmniStudio Package Runtime (managed package) and Standard/Core Runtime require fundamentally different deployment approaches. Using the wrong approach produces silent failures. Check Setup > OmniStudio Settings or verify whether the org has the `vlocity_cmt` or `vlocity_ins` namespace installed.
- **Most common wrong assumption**: Practitioners assume a successful `packDeploy` or DataPack import means the new version is live. It is not. `packDeploy` without `--activate` creates or updates the component record but leaves the previously active version serving runtime traffic. The `--activate` flag must be explicitly included.
- **Roadmap awareness (early 2026)**: Salesforce has announced atomic deployment capabilities that will unify OmniStudio components and standard metadata into a single pipeline. This is in progress as of early 2026. Until GA, the two separate paths remain required.

---

## Core Concepts

### Package Runtime vs. Standard/Core Runtime

OmniStudio is available in two runtime modes that determine which deployment tooling applies:

- **Package Runtime (managed package)**: OmniStudio is installed as a managed package (namespace `vlocity_cmt` for Communications/Energy/Media or `vlocity_ins` for Insurance). Components are stored as data records, not metadata. Deployment uses DataPacks (JSON export/import) via the OmniStudio Build Tool or the `sf omnistudio datapack` CLI plugin. Metadata API and SFDX `sf project deploy start` do not handle these components.
- **Standard/Core Runtime**: OmniStudio is natively integrated into the Salesforce platform. Components are stored as standard metadata types (FlexCard, OmniScript, IntegrationProcedure, etc.). Deployment uses Metadata API, Change Sets, or SFDX/sf CLI exactly like other Salesforce metadata. DataPacks and the OmniStudio Build Tool are not applicable.

Mixing these paths is the most common architectural error in OmniStudio CI/CD.

### DataPacks — Structure and Export/Import

DataPacks are JSON-based export bundles that represent one or more OmniStudio components and their dependencies. In Package Runtime, components are exported via `packExport` (which pulls the component data from org records into a JSON file structure) and imported via `packDeploy` (which pushes the JSON back into the target org as records). DataPacks can be stored in version control (Git) as JSON files, enabling change tracking and diff reviews. Each DataPack export includes a manifest (`VlocityUITemplate`, `OmniScript`, `IntegrationProcedure`, etc.) with version identifiers.

### The --activate Flag Requirement

After `packDeploy` completes, the imported component version exists as a record in the target org but is NOT automatically set as the active version. The previously active version continues serving all runtime requests. To make the new version live, `packDeploy` must include the `--activate` flag, which triggers OmniStudio's activation mechanism — compiling the component and setting it as the active version for that key (Type/SubType/Language). Without `--activate`, an import can succeed (exit 0) while the deployed changes are completely invisible to users.

### OmniStudio Build Tool and sf CLI Plugin

The OmniStudio Build Tool uses a YAML or JSON job file to define which components to export or deploy. The job file specifies component keys, options (activate, maximumDeployCount, defaultMaxParallel), and the pack format. In a CI/CD pipeline, the job file is committed to version control, and the pipeline calls `node vlocity -job <jobfile.yaml> packExport` or `packDeploy --activate` at each stage.

The `sf omnistudio datapack` CLI plugin provides equivalent functionality integrated with the `sf` toolchain: `sf omnistudio datapack export` and `sf omnistudio datapack deploy --activate`. This is the preferred modern approach for new pipeline implementations.

---

## Common Patterns

### DataPack Pipeline for Package Runtime

**When to use:** Org uses Package Runtime (managed package namespace). Need to promote OmniStudio components from dev sandbox to UAT to production.

**How it works:**
1. Developer exports changed components from dev sandbox: `sf omnistudio datapack export --manifest-file manifest.json --output-dir datapacks/`
2. Exported DataPack JSON is committed to the feature branch in Git.
3. CI pipeline (GitHub Actions, Bitbucket, etc.) runs on PR merge:
   a. Authenticates to target org via JWT or connected app OAuth.
   b. Runs `sf omnistudio datapack deploy --source-dir datapacks/ --activate --target-org uat-alias`
   c. Verifies exit code — non-zero marks the pipeline as failed.
4. Post-deploy step queries the org to confirm the active version matches the deployed version.
5. On production release approval, the same pipeline runs against the production org.

**Why not standard SFDX deploy:** `sf project deploy start` ignores OmniStudio data records in Package Runtime orgs. Source tracking does not capture them. Only DataPack tools work for this runtime.

### Standard Runtime SFDX Pipeline

**When to use:** Org uses Standard/Core Runtime. Components are native metadata types (OmniScript, IntegrationProcedure, DataRaptor, FlexCard).

**How it works:**
1. Pull components: `sf project retrieve start --metadata OmniScript:MyScript,IntegrationProcedure:MyIP`
2. Commit to Git feature branch.
3. CI pipeline runs `sf project deploy start --manifest package.xml --target-org uat-alias` on PR merge.
4. No `--activate` flag needed — Standard Runtime components are activated via the standard Salesforce metadata deployment mechanism.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Package Runtime org, promoting between sandboxes | DataPack export/deploy with --activate | Package Runtime stores components as data records, not metadata |
| Standard/Core Runtime org | SFDX metadata deploy (sf project deploy start) | Native metadata types — DataPacks are not applicable |
| Package Runtime, unsure if import succeeded | Query active version in target org post-deploy | packDeploy exit 0 does not confirm activation succeeded |
| DataPack import succeeded but component not live | Re-run packDeploy with --activate flag | Missing --activate is the most common cause |
| Mixed runtime components in one org | Separate pipeline stages per component type | No single tool handles both runtimes correctly |
| Unified pipeline across OmniStudio + standard metadata | Use separate stages until Salesforce atomic deployment GA | As of early 2026, unified deployment is in development |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm org runtime** — Check Setup > OmniStudio Settings. If the `vlocity_cmt` or `vlocity_ins` namespace is installed, the org uses Package Runtime. If OmniStudio components appear as standard metadata types, use the Standard/Core Runtime path.
2. **Select the correct tooling** — Package Runtime: install the `sf omnistudio datapack` CLI plugin or OmniStudio Build Tool. Standard Runtime: ensure `sf` CLI with Salesforce DX is configured for standard metadata deployment. Do not mix tooling between runtimes.
3. **Define the DataPack job file (Package Runtime only)** — Create a YAML/JSON job file specifying component keys to export, options (activate: true, maximumDeployCount, parallel settings), and output directory. Commit the job file to version control.
4. **Export from source org** — Run `sf omnistudio datapack export` from the source org. Commit the resulting DataPack JSON to the feature branch. Review the diff to confirm only the expected components changed.
5. **Deploy to target org with --activate** — In the pipeline, authenticate to the target org and run `sf omnistudio datapack deploy --activate`. Treat any non-zero exit code as a pipeline failure. Do not proceed to the next environment if this step fails.
6. **Verify active version post-deploy** — Query the target org to confirm the component's active version matches the deployed version. For Package Runtime, check the `IsActive` flag on the relevant `OmniScript__c` or `IntegrationProcedure__c` record. This step catches the "import succeeded, activation silently failed" failure mode.
7. **Gate production deployment on UAT sign-off** — Require explicit UAT approval (manual gate or approval job) before the pipeline promotes to production. OmniStudio components interact with business processes that require UAT validation by business users.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Org runtime confirmed (Package Runtime or Standard/Core Runtime)
- [ ] Correct deployment tooling selected for the runtime
- [ ] DataPack job file committed to version control (Package Runtime)
- [ ] DataPack deploy run with --activate flag (Package Runtime)
- [ ] Post-deploy active version verification completed
- [ ] Pipeline exits non-zero on any deploy or activation failure
- [ ] UAT sign-off captured before production promotion
- [ ] Rollback procedure documented (re-deploy prior DataPack version with --activate)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **packDeploy without --activate leaves old version live** — The most common OmniStudio CI/CD failure. `packDeploy` exits 0, the import looks correct in the target org, but users continue to see the old behavior because the previously active version is still serving traffic. Always include `--activate` and verify the active version post-deploy.
2. **DataPack dependencies must be exported together** — If an OmniScript references a specific Integration Procedure or DataRaptor, those dependencies must be included in the same DataPack export or must already exist in the target org at import time. Deploying the OmniScript without its referenced DataRaptor silently imports the component but produces runtime errors when the missing dependency is called.
3. **Standard Runtime components cannot be deployed via DataPack tooling** — If the org has migrated from Package Runtime to Standard/Core Runtime, DataPack export/import will not see the components — they are now native metadata. Attempting DataPack deploy to a Standard Runtime org either errors or silently does nothing. Always reconfirm runtime type when reusing pipeline scripts across orgs.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DataPack job file | YAML/JSON configuration for OmniStudio Build Tool export/deploy operations |
| CI/CD pipeline steps | Ordered pipeline stages for export, import, activation, and post-deploy verification |
| Active version verification query | Post-deploy SOQL to confirm the active version matches the deployed component |
| Runtime determination checklist | Decision steps for confirming Package Runtime vs. Standard/Core Runtime |

---

## Related Skills

- omnistudio-testing-patterns — Test components before promoting them through the deployment pipeline
- omnistudio-datapack-migration — Foundational DataPack structure knowledge that underpins this skill
