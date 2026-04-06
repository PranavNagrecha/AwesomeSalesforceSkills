---
name: migration-from-change-sets-to-sfdx
description: "Use when planning or executing a migration from change-set-based deployments to Salesforce DX source-driven development. Trigger keywords: 'migrate from change sets', 'move to SFDX', 'convert metadata to source format', 'sf project convert mdapi', 'source-driven development adoption'. NOT for greenfield SFDX project setup (use sf-cli-and-sfdx-essentials), unlocked package design (use unlocked-package-development), or DevOps Center pipeline creation (use devops-center-pipeline)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I migrate my org from change sets to SFDX source-driven development"
  - "convert existing metadata retrieved from production into source format for git"
  - "we want to stop using change sets and start using Salesforce CLI for deployments"
  - "what is the best strategy to incrementally move components out of change sets into a DX project"
  - "sf project convert mdapi is failing or producing unexpected directory structure"
tags:
  - migration
  - change-sets
  - sfdx
  - source-format
  - metadata-api
  - source-driven-development
  - devops
inputs:
  - "inventory of metadata types currently promoted via change sets (Apex, Flows, Custom Objects, etc.)"
  - "source org alias or username authenticated with sf CLI"
  - "whether the org already has a connected git repository or version control system"
  - "team size and current release cadence (weekly, biweekly, ad hoc)"
  - "target end state: manifest-based deploys, unlocked packages, or DevOps Center"
outputs:
  - "migration plan with phased component conversion sequence"
  - "SFDX project directory with converted source-format metadata"
  - "package.xml manifest covering the migrated component set"
  - "pre- and post-migration validation checklist"
  - "decision guidance on target deployment model (manifest vs. packages vs. DevOps Center)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Migration From Change Sets To SFDX

This skill activates when a team or practitioner needs to transition from the point-and-click change set deployment model to Salesforce DX source-driven development. It covers the canonical migration path: retrieving metadata from an org via the Metadata API, converting it to source format with `sf project convert mdapi`, establishing a git-tracked SFDX project, and adopting CLI-based deployment workflows. The skill guides incremental, component-by-component migration to preserve git history and minimize disruption to in-flight releases.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which metadata types are currently deployed via change sets? Get a rough inventory: Apex classes, triggers, Flows, custom objects, page layouts, permission sets, reports.
- Has the team authenticated any orgs with `sf org login`? Is a Dev Hub enabled if packages are the eventual target?
- Does a git repository already exist for this org's metadata, or is this a from-scratch setup?
- What is the team's Salesforce edition? Source tracking is only available in scratch orgs and Developer/Developer Pro sandboxes. Full-copy and partial-copy sandboxes require manifest-based retrieval.
- Are there active change set deployments in flight that must complete before the migration cutover?

---

## Core Concepts

### Metadata API Format vs. Source Format

Salesforce metadata exists in two on-disk representations. **Metadata API format** (also called "mdapi format") is the legacy structure produced by `sf project retrieve start --metadata-dir` or the older `sfdx force:mdapi:retrieve`. Files land in a flat directory with `package.xml` at the root and subdirectories like `classes/`, `objects/`, `flows/`. **Source format** is the decomposed structure used by SFDX projects: a single custom object is split into individual files per field, per list view, per validation rule under `force-app/main/default/objects/ObjectName/`. Source format is designed for version control — smaller files, cleaner diffs, fewer merge conflicts.

The conversion command `sf project convert mdapi --root-dir <mdapi-dir> --output-dir <source-dir>` transforms metadata API format into source format. This is a one-way formatting conversion; it does not deploy or retrieve anything.

### Incremental Component Migration

The recommended approach is not a one-time "big bang" conversion of the entire org. Instead, migrate component groups incrementally — starting with the most actively changed metadata types (Apex classes, LWC, Flows) and leaving stable, rarely-changed metadata (reports, dashboards, email templates) for later phases. Each batch is retrieved, converted, committed to git, and validated with a round-trip deploy to a sandbox. This preserves meaningful git history (each commit represents a logical component group) and limits blast radius if something goes wrong.

### package.xml as the Migration Manifest

During migration, `package.xml` serves as the manifest that controls what gets retrieved from the source org. You can retrieve everything at once with wildcard members (`<members>*</members>`), but this pulls hundreds of standard and managed-package components you do not own. Best practice is to build a targeted `package.xml` listing only the metadata types and specific members your team maintains. This manifest becomes the basis for your ongoing manifest-based deploy workflow if you do not adopt packages.

### Source Tracking vs. Manifest-Based Workflow

After migration, the team must choose a deployment model. **Source tracking** (`sf project deploy start` / `sf project retrieve start` with no manifest) works in scratch orgs and select sandbox types — it automatically tracks local and remote changes. **Manifest-based deployment** (`sf project deploy start --manifest package.xml`) works in any org and is the direct replacement for change sets. **Unlocked packages** group metadata into versioned, installable units. Most teams migrating from change sets start with manifest-based deploys and graduate to packages once the project structure is stable.

---

## Common Patterns

### Pattern 1: Phased Retrieval and Conversion

**When to use:** The org has 200+ components deployed via change sets and the team wants a controlled migration over 2-4 sprints.

**How it works:**

1. Build a `package.xml` listing one metadata type group at a time (e.g., all Apex classes first).
2. Retrieve: `sf project retrieve start --manifest package.xml --target-org prod --output-dir mdapi-output/`
3. Convert: `sf project convert mdapi --root-dir mdapi-output/ --output-dir force-app/`
4. Review the converted source, commit to git with a descriptive message ("Add Apex classes from production").
5. Validate with a round-trip deploy to a sandbox: `sf project deploy start --source-dir force-app/ --target-org dev-sandbox`
6. Repeat for the next metadata type group (custom objects, flows, LWC, etc.).

**Why not big bang:** A single retrieve-and-convert of everything produces one massive commit with no logical grouping, makes merge conflicts likely if anyone else is working, and if conversion fails on one type the entire batch must be redone.

### Pattern 2: Shadow Period (Parallel Change Set + CLI Deploys)

**When to use:** The team cannot stop releasing during migration. Some team members are still learning the CLI.

**How it works:**

1. Convert existing metadata to source format and commit to git (using Pattern 1).
2. For the next 1-2 release cycles, deploy to production using both the old change set process and the new CLI process simultaneously. The CLI deploy is validate-only (`--dry-run`) to confirm parity.
3. Once 2-3 consecutive releases pass CLI validation without issues, cut over fully to CLI deploys.
4. Retire the change set workflow and update runbooks.

**Why not immediate cutover:** Teams unfamiliar with the CLI will make mistakes under release pressure. A shadow period builds confidence without risking production stability.

### Pattern 3: Direct-to-Packages Migration

**When to use:** The org has clear domain boundaries (Sales objects, Service objects, Integration logic) and the team plans to adopt unlocked packages.

**How it works:**

1. Retrieve and convert metadata following Pattern 1.
2. Organize source into multiple `packageDirectories` in `sfdx-project.json`, one per domain.
3. Create unlocked packages for each directory using `sf package create`.
4. Create package versions and install in a sandbox for validation.
5. Deploy packages to production instead of using manifest-based deploys.

**Why not start here:** This adds packaging complexity on top of the format migration. Only suitable for teams with a clear modular architecture and Dev Hub access.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Small team (1-3 admins), simple org, infrequent releases | Pattern 1 + manifest-based deploys | Low overhead, minimal tooling setup, direct change-set replacement |
| Mid-size team, regular release cadence, cannot pause releases | Pattern 2 (shadow period) | Builds team confidence while maintaining release continuity |
| Large team, modular org architecture, Dev Hub available | Pattern 3 (direct to packages) | Packages provide versioning, dependency management, and installation governance |
| Org has heavy managed-package customizations | Pattern 1, exclude managed-package components from package.xml | Managed-package metadata cannot be deployed via CLI; only your customizations migrate |
| Team uses DevOps Center already | Skip CLI manifest deploys; convert source format and connect to DevOps Center | DevOps Center handles deployment orchestration; you just need the source format conversion |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner executing this migration:

1. **Inventory current state** — List all metadata types currently promoted via change sets. Check recent change set history in Setup > Outbound Change Sets. Identify which components change frequently vs. rarely.
2. **Set up the SFDX project** — Run `sf project generate --name <project-name>`. Initialize a git repository if none exists. Authenticate the source org with `sf org login web --alias prod`.
3. **Build the migration manifest** — Create a `package.xml` targeting the first batch of metadata types. Start with Apex classes and triggers (they have the clearest file-to-component mapping).
4. **Retrieve and convert** — Run `sf project retrieve start --manifest package.xml --target-org prod --output-dir mdapi-output/`. Then `sf project convert mdapi --root-dir mdapi-output/ --output-dir force-app/`. Review the output structure.
5. **Validate round-trip** — Deploy the converted source to a sandbox: `sf project deploy start --source-dir force-app/ --target-org dev-sandbox`. Confirm zero errors. This proves the conversion is lossless.
6. **Commit and iterate** — Commit the converted source to git. Repeat steps 3-5 for each remaining metadata type group. Resolve conflicts between batches as they arise.
7. **Cut over** — Once all actively-maintained metadata is in the SFDX project, perform the next production release via `sf project deploy start` instead of a change set. Retire the change set process.

---

## Review Checklist

Run through these before marking the migration complete:

- [ ] All actively-maintained metadata types are retrieved and converted to source format
- [ ] Source format files are committed to a git repository with logical, per-batch commits
- [ ] Round-trip deploy to a sandbox succeeds with zero errors for the full source directory
- [ ] `sfdx-project.json` has correct `sourceApiVersion` matching the org's current API version
- [ ] `.forceignore` is configured to exclude metadata the team does not own (managed-package components, standard objects not customized)
- [ ] Team members have authenticated their orgs with `sf org login` and can run basic CLI commands
- [ ] At least one production deploy has been completed via CLI (validate-only counts for the shadow period)
- [ ] Change set workflow is formally retired and runbooks are updated

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`sf project convert mdapi` silently skips unsupported types** — Some metadata types (e.g., InstalledPackage, certain legacy email template types) are not supported in source format. The convert command does not error; it just omits them. Always compare the count of components in the mdapi directory against the converted source directory to catch dropped items.

2. **Source API version mismatch breaks retrieval** — If `sfdx-project.json` specifies `"sourceApiVersion": "59.0"` but the org is on API version 62.0, certain newer metadata types will not be retrieved or may have missing fields. Always set `sourceApiVersion` to match the target org's current release API version.

3. **Object decomposition creates hundreds of files** — Converting a single custom object with 80 fields, 10 validation rules, and 5 list views from mdapi format produces 95+ individual files in source format. This is by design, but teams unfamiliar with source format are alarmed by the file count. Prepare the team for this before the first conversion.

4. **Profiles and permission sets do not round-trip cleanly** — Retrieved profiles contain every object and field permission in the org, including standard objects and managed-package fields. Deploying this back overwrites the target org's profile with exactly what was retrieved, potentially removing permissions granted after retrieval. Use `.forceignore` to exclude profiles, or use permission sets exclusively.

5. **Flows retrieved in mdapi format include inactive versions** — A retrieve with `<members>*</members>` for FlowDefinition pulls all versions, including inactive ones. Converting these creates source files for flows the team may not recognize. Use specific member names in `package.xml` to retrieve only the active flow versions you intend to manage.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Migration plan | Phased schedule mapping metadata type groups to sprint iterations, with owners and validation milestones |
| SFDX project | Initialized project with `sfdx-project.json`, `.forceignore`, and `force-app/` containing converted source |
| package.xml manifest | Targeted retrieval manifest listing only team-maintained metadata types and members |
| Validation report | Results of round-trip deploy to sandbox confirming conversion fidelity |
| Cutover checklist | Go/no-go criteria for switching the next production release from change sets to CLI deploys |

---

## Related Skills

- `devops/change-set-deployment` — Use when the team is still using change sets and needs help with the current workflow, not the migration away from it.
- `apex/sf-cli-and-sfdx-essentials` — Use when the question is about SF CLI commands, authentication, or scratch org basics rather than the migration process itself.
- `devops/unlocked-package-development` — Use when the team has completed the source-format migration and is ready to adopt unlocked packages.
- `devops/scratch-org-management` — Use when setting up scratch orgs as part of the post-migration development workflow.
- `apex/metadata-api-and-package-xml` — Use when the question is about package.xml authoring, metadata type references, or retrieval patterns rather than the migration workflow.
