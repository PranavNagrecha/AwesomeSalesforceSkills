---
name: git-branching-for-salesforce
description: "Use when selecting or reviewing a Git branching strategy for a Salesforce project — choosing between trunk-based development, GitFlow, or environment branching, and mapping branches to orgs, packages, and CI pipelines. Trigger keywords: 'git branching strategy Salesforce', 'trunk-based vs GitFlow', 'branch per package', 'feature branch model SFDX', 'branching for unlocked packages', 'git workflow Salesforce DX'. NOT for CI/CD pipeline implementation (use devops/github-actions-for-salesforce or devops/gitlab-ci-for-salesforce), NOT for environment topology decisions (use devops/environment-strategy), NOT for scratch org lifecycle management."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "what git branching strategy should we use for our Salesforce project"
  - "how do I map git branches to Salesforce sandboxes and scratch orgs"
  - "we are adopting unlocked packages and need to design our branch model"
  - "should we use trunk-based development or GitFlow for Salesforce"
  - "our feature branches keep causing merge conflicts with declarative metadata"
tags:
  - git-branching-for-salesforce
  - trunk-based-development
  - gitflow
  - branching-strategy
  - unlocked-packages
  - sfdx
  - devops
inputs:
  - "Development model: org-based (change sets, Metadata API deploy) or source-driven (Salesforce CLI, scratch orgs, packages)"
  - "Number of concurrent workstreams and team size"
  - "Package architecture: single project, unlocked packages, managed 2GP"
  - "Environment inventory: sandbox types and scratch org usage"
  - "Release cadence: continuous delivery, scheduled releases, or hybrid"
outputs:
  - "Branch model diagram or description with branch-to-org mapping"
  - "Branch naming conventions and lifecycle rules"
  - "Merge and promotion flow aligned to release pipeline"
  - "Package versioning alignment notes (if using unlocked or 2GP packages)"
  - "Branch protection and review gate recommendations"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Git Branching For Salesforce

Use this skill when designing or reviewing a Git branching strategy for a Salesforce program. The skill helps practitioners choose the right branching model, map branches to Salesforce orgs and pipeline stages, and avoid the metadata-specific merge pain that makes generic Git advice insufficient for Salesforce projects.

---

## Before Starting

Gather this context before recommending or reviewing a branching strategy:

- What development model is in use? Org-based promotion (change sets, Metadata API deploy) constrains branching because there is no source-of-truth repo by default. Source-driven development (SFDX, scratch orgs) enables richer branching but requires discipline around metadata formatting.
- What is the package architecture? A monolithic `force-app` directory, multiple unlocked packages, or managed 2GP packages each impose different constraints on how branches relate to version lineage.
- How many developers work concurrently, and on how many independent features? High concurrency demands short-lived branches or trunk-based development to minimize merge debt.

---

## Core Concepts

### Branch-to-Org Mapping

Every Salesforce branch model must answer the question: which org backs which branch? Unlike standard web development where any branch can deploy to any identical server, Salesforce orgs accumulate state. A sandbox configured for UAT should map to a specific integration or release branch. Scratch orgs are ephemeral and pair naturally with feature branches. Long-lived sandboxes pair with long-lived branches (main, develop, release).

### Package Version Ancestry Is Linear

For unlocked packages and managed 2GP, the package version ancestry forms a linear chain. When you create a new package version, you must specify an ancestor that is the highest promoted version. You cannot create parallel version lineages from separate branches and later merge them. This means the branching model must funnel all package-relevant changes through a single promotion path. Feature branches can exist for development, but the packaging branch must be linear.

### Metadata Merge Conflicts Are Structural, Not Textual

Salesforce metadata in XML format creates merge problems that differ from typical code merges. A single custom object file (`Account.object-meta.xml`) can accumulate hundreds of field references. Two developers adding fields to the same object will produce a valid Git merge but potentially an invalid metadata deploy if the merge reorders elements. Decomposed source format (SFDX) mitigates this by storing each field as a separate file, but profiles, permission sets, and custom labels still produce frequent structural conflicts.

---

## Common Patterns

### Trunk-Based Development (Recommended for Most Teams)

**When to use:** Teams of 2-15 developers doing source-driven development with scratch orgs. Works best with continuous delivery or frequent releases.

**How it works:**
1. `main` branch is the single source of truth, always deployable.
2. Developers create short-lived feature branches (< 2 days) from `main`.
3. Each feature branch gets its own scratch org for development and testing.
4. Pull requests merge back to `main` after CI passes (Apex tests, static analysis, deploy validation).
5. `main` deploys to an integration sandbox for smoke testing, then promotes to UAT and production.
6. Release tags on `main` mark what was deployed to production.

**Why not the alternative:** GitFlow's long-lived `develop` branch creates merge debt with Salesforce metadata. Profile and permission set conflicts compound over time. Trunk-based development keeps the delta small and conflicts manageable.

### Environment Branching (GitFlow Variant)

**When to use:** Large programs (15+ developers) with rigid release gates, compliance requirements, or multiple workstreams targeting different release windows.

**How it works:**
1. `main` reflects what is in production.
2. `develop` (or `integration`) is the merge target for all feature work. Maps to a Developer Pro or Partial Copy sandbox.
3. Feature branches are created from `develop`, one per user story.
4. `release/*` branches are cut from `develop` when a release is frozen. Maps to a UAT or staging sandbox.
5. Hotfix branches are created from `main` for emergency production fixes, merged back to both `main` and `develop`.

**Why not the alternative:** Trunk-based development requires mature CI and disciplined short-lived branches. If the team has slow test cycles, limited automation, or separate release trains, environment branching provides the gating structure that trunk-based lacks.

### Package-Aligned Branching

**When to use:** Teams using multiple unlocked packages or managed 2GP. Each package may have its own release cadence.

**How it works:**
1. `main` branch contains all packages in their released state.
2. Feature branches follow `feature/<package-name>/<story>` naming.
3. A `packaging/<package-name>` branch (or CI job on `main`) handles version creation with `sf package version create`.
4. Package ancestry is tracked through `sfdx-project.json` on the packaging branch.
5. After promotion (`sf package version promote`), changes merge to `main` and a release tag is applied.

**Why not the alternative:** Without package-aligned branches, teams risk creating package versions from branches that include unfinished work from other packages. The linear ancestry requirement means a bad version in the chain blocks future versions.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Small team (2-8), scratch orgs, continuous delivery | Trunk-based development | Low merge friction, fast feedback, scratch orgs handle isolation |
| Large team, multiple release trains, compliance gates | Environment branching (GitFlow variant) | Provides release isolation and approval checkpoints |
| Multiple unlocked packages with independent release cadences | Package-aligned branching on top of trunk-based | Linear ancestry requires controlled packaging path |
| Org-based development with change sets, no scratch orgs | Simplified trunk-based with sandbox-mapped branches | Branching complexity should match automation maturity |
| Hotfix-heavy production with infrequent releases | Environment branching with dedicated hotfix branch | Hotfixes must bypass the normal release train |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing a branching strategy:

1. **Identify the development model.** Determine whether the team uses org-based (change sets, Metadata API) or source-driven (SFDX, scratch orgs, packages) development. Org-based teams should start with a simplified model — adding complex branching to an org-based workflow creates overhead without matching benefit.
2. **Inventory the environment topology.** List every sandbox, scratch org definition, and their purposes. Map each environment to a pipeline stage (dev, integration, UAT, staging, production). This mapping drives the branch-to-org relationship.
3. **Select a branching model.** Use the decision guidance table above. Default to trunk-based development unless the team has a specific constraint that requires environment branching or package-aligned branching.
4. **Define branch naming conventions.** Standardize names: `feature/<story-id>-<short-desc>`, `release/<version>`, `hotfix/<ticket>`. Enforce conventions through branch protection rules and CI validation.
5. **Configure branch protection and merge rules.** Require pull request reviews, passing CI checks (Apex tests, deploy validation to a scratch org or sandbox), and no direct pushes to `main` or `develop`.
6. **Align package versioning (if applicable).** If using unlocked or 2GP packages, ensure `sfdx-project.json` ancestor fields are updated only on the packaging path. Do not create package versions from feature branches.
7. **Document and validate.** Record the branch model, naming conventions, and merge rules in the repository README or a CONTRIBUTING guide. Validate by walking through a feature, a release, and a hotfix scenario end-to-end.

---

## Review Checklist

Run through these before marking a branching strategy complete:

- [ ] Every long-lived branch maps to a specific Salesforce org (sandbox or scratch org definition)
- [ ] Feature branches have a maximum lifespan policy (recommend < 5 days)
- [ ] Branch protection rules enforce PR reviews and passing CI on `main` and `develop`
- [ ] Merge direction is documented (feature -> develop -> release -> main, or feature -> main)
- [ ] Hotfix path is defined and does not require waiting for the next release train
- [ ] Package versioning (if applicable) flows through a single linear branch path
- [ ] Destructive changes (field deletes, type changes) have a documented branch and deployment process
- [ ] Branch naming conventions are enforced by CI or pre-commit hooks

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Profile and permission set merge conflicts** — Profiles in metadata format are monolithic XML files. Two developers adding field permissions on different objects still produce merge conflicts because the profile file includes all FLS entries. Use decomposed source format and consider permission sets over profiles to reduce conflict surface.
2. **Package version ancestry blocks parallel branches** — If two branches each create an unlocked package version, only one can be promoted as the ancestor of the next version. The other branch's version becomes a dead end. Always create package versions from a single controlled branch.
3. **Scratch org expiry invalidates long-lived feature branches** — Scratch orgs expire after 1-30 days (default 7). A feature branch that outlives its scratch org requires re-creating the org and re-pushing source, which may reveal deploy errors that were masked by incremental pushes.
4. **Declarative changes made in sandboxes drift from source** — If a developer or admin makes changes directly in a sandbox that maps to a branch, those changes are not in Git until explicitly pulled. This "sandbox drift" causes the branch to diverge from the org it supposedly represents.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Branch model document | Diagram or text description of all branch types, naming conventions, and merge flows |
| Branch-to-org mapping table | Maps each branch to its corresponding Salesforce environment |
| Branch protection configuration | GitHub/GitLab branch protection rules for main and integration branches |
| Work template (filled) | Completed `git-branching-for-salesforce-template.md` with project-specific decisions |

---

## Related Skills

- devops/environment-strategy — Use alongside this skill to design the environment topology that branches map to
- devops/github-actions-for-salesforce — Use to implement CI/CD pipelines that enforce the branching strategy
- devops/gitlab-ci-for-salesforce — Use to implement CI/CD pipelines in GitLab that enforce the branching strategy
- devops/destructive-changes-deployment — Use when the branching model must accommodate metadata deletions
- devops/org-shape-and-scratch-definition — Use when scratch orgs back feature branches and need consistent definitions
