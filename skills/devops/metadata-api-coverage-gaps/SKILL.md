---
name: metadata-api-coverage-gaps
description: "Use this skill when a deployment, source push, or package version fails because a metadata type is unsupported, partially supported, or behaves differently across Metadata API, source tracking, unlocked packages, and 2GP managed packages. NOT for deployment error troubleshooting, Metadata API tutorials, or dependency mapping — use devops/deployment-error-diagnosis."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - metadata-api
  - metadata-coverage
  - deployment
  - source-tracking
  - release-runbook
  - devops
triggers:
  - "my deployment failed because a metadata type is not supported by Metadata API"
  - "which Salesforce metadata types cannot be deployed with sf project deploy or retrieved with sf project retrieve"
  - "I need a release runbook for settings that cannot be migrated through Metadata API"
  - "how do I check the Metadata Coverage Report for unsupported or partially supported types"
  - "source tracking is not detecting changes to a specific metadata type in my scratch org"
  - "my unlocked package version create is silently excluding a metadata type"
inputs:
  - "List of metadata types or component names that are failing or suspected to be unsupported"
  - "Deployment target context: source deploy, change set, unlocked package, or 2GP managed package"
  - "Salesforce API version in use (affects which types are supported)"
  - "Org edition and feature licenses that may gate metadata type availability"
outputs:
  - "Coverage gap assessment listing each affected metadata type with its support status across Metadata API, source tracking, unlocked packages, and 2GP"
  - "Release runbook documenting manual post-deployment steps for unsupported types"
  - "Workaround recommendations (Tooling API, post-deploy scripts, Setup UI steps, or data loader)"
  - "package.xml or sfdx-project.json adjustments to exclude unsupported types and avoid silent failures"
dependencies: []
version: 1.0.3
author: Pranav Nagrecha
updated: 2026-10-20
---

# Metadata API Coverage Gaps

This skill activates when a practitioner encounters metadata types that are unsupported, partially supported, or behave inconsistently across different Salesforce deployment mechanisms. It guides you through identifying the gap using the Metadata Coverage Report, choosing a workaround, and building a release runbook so that manual configuration steps are not forgotten during deployments.

---

## Before Starting

Gather this context before working on anything in this domain:

- **API version in use** -- Metadata type support changes between API versions. A type unsupported in v55 may be supported in v60. Always confirm against the current API version.
- **Deployment mechanism** -- Support status differs between Metadata API (source deploy), change sets, unlocked packages, and 2GP managed packages. A type may be deployable via Metadata API but excluded from package uploads.
- **Org edition and licenses** -- Some metadata types only exist in orgs with specific features enabled (e.g., Industry Cloud types require Health Cloud or Financial Services Cloud licenses). The type will appear unsupported if the feature is not enabled.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which channels will carry this release — Metadata API deploy, change sets, unlocked, 2GP, or classic managed packages? | Coverage is per channel, and a type that deploys through Metadata API can still fail in a managed package version (Gotcha 6) | The coverage-report columns to check for every type in the release |
| Which `sourceApiVersion` does the project pin, and do every developer and CI use it? | It decides the fields retrieved for each type, so mixed versions behave differently for the same source (Gotcha 4) | One pinned version, changed only as a team decision |
| Was coverage checked at the API version you will deploy at, after the latest release? | Coverage changes between API versions, and the report may trail a new release (Gotcha 1) | A dated coverage check plus a sandbox retrieve-and-deploy of any newly supported type |
| Which Settings types are in the release, and how will you confirm each field landed? | A supported Settings type can still leave sub-elements unapplied (Gotcha 2) | A post-deploy Setup or Tooling API comparison against the source XML |
| What will `.forceignore` exclude, and has each pattern been tested? | Patterns follow `.gitignore` rules, so a broad glob silently drops unrelated components (Gotcha 3) | Narrow, reviewed patterns and a retrieve that proves only the intended files are excluded |
| Does the release delete anything, and is each deleted type covered by Metadata API? | A type Metadata API can't handle has to be deleted by hand in each org (Gotcha 5) | A destructive manifest of covered types plus runbook steps for the rest |
| Are changes being found through source tracking in a scratch org or Developer / Developer Pro sandbox? | Types unsupported in source tracking never show up as changes (Gotcha 7) | An explicit retrieve list for untracked types in the CI retrieve step |

A configuration built from these answers turns every coverage gap into a named runbook step with an owner; "just deploying" finds the gaps in production, one environment at a time.

---

## Core Concepts

### The Metadata Coverage Report

Salesforce publishes the Metadata Coverage Report at `developer.salesforce.com/docs/metadata-coverage`. The Metadata API guide calls it "the ultimate source of truth for metadata coverage across several channels. These channels include Metadata API, scratch org source tracking, unlocked packages, second-generation managed packages, classic managed packages, and more." It is the authoritative source for determining whether a given type can be deployed through a given channel.

### Unsupported vs. Partially Supported Types

The Metadata API Developer Guide's "Unsupported Metadata Types" page does not list the types itself. It says some features "have metadata types that aren't available in Metadata API," that changes to them must be made "manually in each of your organizations," that some types "may also be unsupported in source tracking, packaging, and change sets," and it points to Metadata Coverage for the list. Types can also be removed: `OrgPreferenceSettings` was deprecated in API 47.0 and removed in 48.0, with most of its preferences moved to Boolean fields on other Settings types. Partially supported types are more dangerous: they retrieve successfully but deploy with silent data loss or require specific field ordering that is not enforced by the API.

### Release Runbooks for Manual Steps

When a metadata type cannot be deployed programmatically, the gap must be documented in a release runbook -- a step-by-step checklist executed manually in the target org after (or before) the automated deployment. Without a runbook, these settings drift between environments and cause hard-to-diagnose production issues weeks later. The runbook should specify: the exact Setup path, the values to configure, the order relative to the automated deployment, and who is responsible.

### Source Tracking Gaps

Source tracking in scratch orgs and sandboxes (with Developer/Developer Pro licenses) does not track all metadata types. When a type is not source-tracked, changes made in the org UI will not appear in `sf project retrieve start` results. This creates silent configuration drift. The Metadata Coverage Report column "Source Tracking" indicates which types are tracked.

---

## Common Patterns

### Pattern 1: Pre-Deployment Coverage Audit

**When to use:** Before building a CI/CD pipeline for a project, or when onboarding a new metadata type into source control for the first time.

**How it works:**
1. List all metadata types in the project's `package.xml` or `sfdx-project.json` package directories.
2. Cross-reference each type against the Metadata Coverage Report for the target API version.
3. For any type marked "Not Supported" or missing from the report, check the Unsupported Metadata Types page in the Metadata API Developer Guide.
4. Create a coverage gap table (see template) and classify each gap as Critical (blocks deployment), High (causes config drift), or Low (cosmetic or rarely changed).
5. For Critical and High gaps, define a workaround and add it to the release runbook.

**Why not the alternative:** Skipping the audit and discovering gaps during a production deployment causes emergency manual fixes under pressure, often with incomplete documentation.

### Pattern 2: Post-Deploy Script for Tooling API Workarounds

**When to use:** When a metadata type is not supported by Metadata API but is accessible through the Tooling API or REST API (e.g., certain FlowDefinition activations, some org-level settings).

**How it works:**
1. Identify the Tooling API object that corresponds to the unsupported metadata type (e.g., `FlowDefinition` for activating a specific Flow version).
2. Write a post-deploy script (Bash, Python, or Node) that uses `sf org open` or authenticated REST calls to update the setting.
3. Integrate the script into the CI/CD pipeline as a post-deployment step.
4. Add error handling and idempotency -- the script should succeed even if run twice.

**Why not the alternative:** Manual Setup UI steps are error-prone and do not scale across multiple orgs or frequent releases.

### Pattern 3: Exclusion-and-Runbook for Truly Unsupported Types

**When to use:** When no programmatic workaround exists -- the type must be configured manually in each target org.

**How it works:**
1. Add the type to `.forceignore` (or the `sfdx-project.json` exclusion list) so that retrieve/deploy commands do not fail on it.
2. Document the manual steps in the release runbook with screenshots or exact Setup navigation paths.
3. Add a validation step to the runbook: a SOQL query, a Tooling API check, or a manual verification that confirms the setting is correct after manual application.
4. Assign a named owner for each manual step in the runbook.

**Why not the alternative:** Leaving unsupported types in the project source causes intermittent deployment failures that erode team confidence in the CI/CD pipeline.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Type is in Metadata Coverage Report as "Not Supported" but available via Tooling API | Post-deploy script using Tooling API | Automatable; reduces manual error |
| Type is completely unsupported by any API | Exclusion + release runbook with manual steps | No alternative; runbook prevents drift |
| Type is supported but source tracking does not track it | Retrieve explicitly before each commit; add to CI retrieve step | Prevents silent drift in scratch orgs |
| Type was supported in older API version but removed | Pin the component to the older API version in `package.xml`, or migrate to the replacement type | Avoids deploy failures on version upgrade |
| Type is supported by Metadata API but not by unlocked packages | Deploy the component separately via `sf project deploy` after package install | Keeps the package installable |

---

## Recommended Workflow

Step-by-step instructions for handling metadata API coverage gaps:

1. **Identify the gap** -- Run `sf project retrieve start` or `sf project deploy start` and note any errors referencing unsupported types. Alternatively, consult the Metadata Coverage Report for the project's API version.
2. **Classify the type** -- Check the Metadata Coverage Report for support status across every channel it lists (Metadata API, scratch org source tracking, unlocked packages, 2GP and classic managed packages, and more). Record the result in the coverage gap table.
3. **Assess impact** -- Determine whether the gap is Critical (blocks deployment), High (causes config drift between environments), or Low (rarely changed, cosmetic).
4. **Choose a workaround** -- For Tooling API-accessible types, write a post-deploy script. For truly unsupported types, document manual steps in a release runbook. For source-tracking gaps, add an explicit retrieve step to the CI pipeline.
5. **Update project configuration** -- Add unsupported types to `.forceignore` or exclude them from `package.xml` / `sfdx-project.json` packageDirectories. Ensure the CI pipeline does not fail on excluded types.
6. **Document in the release runbook** -- Record every manual step with the Setup navigation path, expected values, execution order relative to the automated deployment, and the responsible team member.
7. **Validate after deployment** -- Run the checker script or manual verification steps from the runbook to confirm that all manually configured settings match the expected state in the target org.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every metadata type in the project has been checked against the Metadata Coverage Report for the target API version
- [ ] Unsupported types are excluded from `package.xml`, `.forceignore`, or `sfdx-project.json` as appropriate
- [ ] A release runbook exists for every metadata type that requires manual configuration
- [ ] Each runbook step has an owner, a Setup navigation path, and a verification query or screenshot
- [ ] Post-deploy scripts are idempotent and include error handling
- [ ] Source-tracking gaps are mitigated with explicit retrieve steps in the CI pipeline
- [ ] The coverage gap table is committed to the project repository for team visibility

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Retrieve pulls the latest Flow version, not the active one** -- A Flow member without a version number "is the latest version" (Metadata API guide, Flow `fullName`), not the currently active version. If version 3 is active but version 5 is the latest (inactive) version, `sf project retrieve` pulls version 5. Deploying it ships version 5's content under whatever `<status>` the file carries, not version 3. Control activation with `<status>` on the Flow — the Metadata API guide recommends, as of API 44.0, discontinuing `FlowDefinition` for activation, and a `FlowDefinition` in the same deploy overrides the flows' status fields.
2. **OrgPreferenceSettings was removed as a whole type** -- It is available in API 37.0 to 47.0, deprecated in 47.0, and removed in 48.0. A project that raises `sourceApiVersion` to 48.0 or later can no longer carry `OrgPreference.settings`. The fix is to move each preference to its Boolean field on the replacement Settings type (for example `enableCompileOnDeploy` on `ApexSettings`) and delete the old file. A Settings field can also be release-bound while its type stays supported: `ApexSettings.enableEnforceSummer26ApexHeapLimit` (field available in API 68.0) keeps a nonproduction org on the lower Summer '26 Apex heap limits, but it is honoured only in Winter '27 — in Spring '27 the higher heap limits are enforced regardless of the setting (Metadata API Developer Guide 264, `api_meta.txt` L113855-113862). The Winter '27 heap increase itself (10 MB sync / 25 MB async, Apex Developer Guide 264 L19780) is a release-level change, not tied to `sourceApiVersion`, so do not treat the field as a version gate.
3. **Source tracking does not track permission set assignments** -- Changes to `PermissionSetAssignment` records (which users are assigned to which permission sets) are data, not metadata. Source tracking will never detect these changes. Use data loader or a post-deploy script to manage assignments.
4. **Unlocked packages silently exclude unsupported types** -- When creating a package version, unsupported types in the package directory are silently excluded rather than causing an error. The package installs successfully but is missing configuration, leading to runtime failures in the subscriber org.
5. **ForecastingSettings has persistent gaps** -- `ForecastingSettings` is a long-standing example of a partially supported type. Retrieving it succeeds, but deploying it often fails with cryptic errors depending on the target org's forecasting configuration. Manual Setup configuration is typically required.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Coverage gap table | Spreadsheet or markdown table listing each metadata type, its support status across all channels, impact classification, and chosen workaround |
| Release runbook | Step-by-step manual configuration checklist for unsupported types, with owners, Setup paths, and verification steps |
| Post-deploy script | Automated script (Bash/Python/Node) that configures Tooling API-accessible settings after the main deployment |
| `.forceignore` updates | Additions to `.forceignore` excluding unsupported types from source tracking and deployment |

---

## Related Skills

- architect/metadata-coverage-and-dependencies -- Use for architecture-level metadata dependency mapping and coverage assessment across a full org; this skill focuses on the DevOps workflow for handling gaps during deployments
- devops/unlocked-package-development -- Use when the coverage gap is specifically related to unlocked package version creation or installation
- devops/change-set-deployment -- Use when working with change sets, which have their own distinct set of supported metadata types
- apex/metadata-api-and-package-xml -- Use for constructing package.xml files and understanding Metadata API retrieval mechanics
