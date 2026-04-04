---
name: environment-strategy
description: "Use when designing the full environment topology for a Salesforce program — selecting which org types to provision, how many, and how they map to your branching strategy and release pipeline. Trigger keywords: 'environment strategy', 'org topology', 'scratch org vs sandbox', 'how many environments do I need', 'environment planning', 'DevOps environment design'. NOT for sandbox-type-only decisions (use admin/sandbox-strategy), NOT for scratch org lifecycle or daily usage (use devops/scratch-org-management), NOT for release pipeline mechanics (use devops/release-management)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I decide between scratch orgs and sandboxes for my environment strategy"
  - "we need to design our Salesforce org environments before starting development"
  - "our branching strategy does not match the number of environments we have"
  - "should we use scratch orgs or sandboxes for CI and integration testing"
  - "what environment types do we need for a new Salesforce program"
tags:
  - environment-strategy
  - scratch-orgs
  - sandboxes
  - org-topology
  - branching-strategy
  - devops
inputs:
  - "Team size and number of parallel workstreams"
  - "Source control and branching strategy (trunk-based, feature branch, Gitflow)"
  - "Test types required: unit, integration, UAT, performance, training"
  - "Data sensitivity and compliance requirements"
  - "CI/CD tooling in use (Salesforce CLI, GitHub Actions, CircleCI, etc.)"
  - "Salesforce edition and available sandbox allocations"
outputs:
  - "Environment matrix: type, purpose, data volume, source tracking, refresh/expiry cadence, branch alignment"
  - "Org-count recommendation with rationale"
  - "Decision guidance on scratch org vs sandbox per stage"
  - "Branching strategy alignment notes"
  - "Environment governance checklist"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Environment Strategy

Use this skill when designing or reviewing the full Salesforce environment topology for a program — covering all org types (scratch orgs and sandboxes), their roles in the pipeline, and how they align to the team's branching and release strategy. This skill fills the cross-type decision gap between scratch-org management and sandbox-strategy.

---

## Before Starting

Gather this context before working on environment design:

- Which Salesforce edition is in use and how many sandbox licenses are allocated? Full and Partial Copy sandboxes are limited and often constrain topology choices.
- What branching strategy does the team use or plan to use? Trunk-based development favors fewer long-lived environments. Feature-branch Gitflow often requires environment-per-branch or a shared integration environment.
- What test types are required at each stage? Unit tests, integration tests, UAT, performance/load testing, and training each have different environment requirements.
- Is the team using source-driven development (SFDX/Salesforce CLI with scratch orgs) or change-set-based promotion? This determines whether scratch orgs are viable at all.
- What are the data sensitivity and compliance requirements? Full and Partial Copy sandboxes copy production data and require masking plans.

---

## Core Concepts

### The Five Org Types and Their Roles

Salesforce provides five distinct non-production org types. Each serves a specific pipeline role and no single type covers all needs.

**Scratch Orgs** are temporary, source-tracked orgs created from a definition file (`project-scratch-def.json`). They expire after a maximum of 30 days (default 7 days), start empty, and are ideal for isolated unit tests and CI runs. Scratch orgs are provisioned and destroyed programmatically via `sf org create scratch`. They cannot hold persistent integration state and are not suitable for UAT or load testing. Source tracking is on by default.

**Developer Sandboxes** are persistent, Metadata API-based copies of production metadata with no production data. Storage is 200 MB. They suit isolated developer work and early integration. Refresh copies production metadata from a point in time and takes minutes to hours.

**Developer Pro Sandboxes** are identical in behavior to Developer sandboxes but provide 1 GB of storage. Use when a Developer sandbox runs out of space for large metadata sets or AppExchange packages.

**Partial Copy Sandboxes** copy production metadata and a configurable sample of production data (up to 5 GB). Refresh is limited to every 5 days. Suitable for integration testing with realistic data volumes and UAT when a full data set is not required.

**Full Sandboxes** are complete copies of production — metadata and all data. Refresh is limited to every 29 days. Use for regression, performance/load testing, and production rehearsal. Highest cost and highest governance burden due to real data presence.

### Source Tracking and Pipeline Fit

Scratch orgs are the only org type with native source tracking enabled by default. Sandboxes support source tracking only when used with Salesforce CLI's `--track-source` flag on Developer and Developer Pro sandboxes (Salesforce DX Developer Guide, Spring '24+). Partial Copy and Full sandboxes do not support source tracking. This matters because CI pipelines that rely on `sf project deploy start` with source tracking must target scratch orgs or Developer/Developer Pro sandboxes — not Partial or Full sandboxes.

### Branching Strategy Alignment

Environment count must follow branching strategy, not the reverse. The two dominant models are:

**Trunk-based development**: Developers commit directly or use very short-lived feature branches that merge to main frequently. This model needs fewer persistent environments: scratch orgs for local/CI, one integration sandbox, one UAT sandbox, one pre-production Full sandbox, and production.

**Feature-branch / Gitflow**: Long-lived feature branches exist per workstream. Each branch may need its own scratch org or Developer sandbox for isolated development before merging to an integration branch. This model increases environment count linearly with team size and requires strong automation to avoid sprawl.

Mismatching branching strategy to environment topology — for example, running a Gitflow model with only one shared Developer sandbox — forces serialized development and kills team velocity.

---

## Common Patterns

### Pattern 1: Source-Driven Pipeline with Scratch Orgs for CI

**When to use:** Team uses SFDX, source control is the system of record, and CI must run every pull request with a clean environment.

**How it works:**
1. Developers work in individual scratch orgs created from `project-scratch-def.json`.
2. The CI pipeline (`sf org create scratch --definition-file config/project-scratch-def.json`) creates a fresh scratch org per run.
3. Apex tests and validation run in the scratch org, which is then deleted.
4. A shared Developer or Developer Pro sandbox acts as the integration target after PR merge.
5. Partial Copy sandbox is used for UAT. Full sandbox (if available) for pre-production regression.

**Why not a shared sandbox for CI:** A shared sandbox becomes a serialization bottleneck when multiple PRs need simultaneous validation. Scratch orgs are disposable and parallel.

### Pattern 2: Sandbox-Only Pipeline for Teams Without SFDX Adoption

**When to use:** Team is on change sets or early Salesforce CLI adoption, scratch orgs are not viable, or the org uses features not supported by scratch org shapes (some managed packages, Experience Cloud with complex data).

**How it works:**
1. Each developer or workstream gets a dedicated Developer sandbox.
2. An integration Developer Pro or Partial Copy sandbox serves as the shared merge target.
3. UAT runs in a Partial Copy or Full sandbox.
4. A Full sandbox (pre-production) mirrors production for regression before release.

**Why not scratch orgs for every team:** Some metadata types and managed package configurations do not deploy reliably into scratch orgs. Persistent sandboxes tolerate messier real-world configurations.

---

## Decision Guidance

Use this matrix when selecting environment types for each pipeline stage:

| Pipeline Stage | Recommended Org Type | Data Volume | Source Tracked | Refresh / Expiry |
|---|---|---|---|---|
| Unit test / CI per PR | Scratch Org | None (empty) | Yes | 7–30 days / disposable |
| Individual developer work | Developer Sandbox | None | Yes (CLI flag) | On demand |
| Individual dev with large packages | Developer Pro Sandbox | None | Yes (CLI flag) | On demand |
| Integration / merge target | Developer Pro or Partial Copy | Sample (Partial) | Dev Pro only | 5-day min (Partial) |
| UAT with realistic data | Partial Copy Sandbox | Up to 5 GB sample | No | 5-day min |
| Performance / load testing | Full Sandbox | Full production copy | No | 29-day min |
| Pre-production regression | Full Sandbox | Full production copy | No | 29-day min |
| Training | Developer or Partial Copy | Scripted seed data | Dev only | On demand |

| Situation | Recommended Approach | Reason |
|---|---|---|
| CI must be parallel and clean | Scratch org per run | Disposable, source-tracked, parallel-safe |
| Feature not supported in scratch org | Developer Pro Sandbox | Persistent, CLI source tracking, no data copy |
| UAT team needs realistic data | Partial Copy Sandbox | Data sample without full production copy cost |
| Load / performance testing required | Full Sandbox | Only type with full data volume parity |
| Team has no SFDX experience yet | Developer Sandbox pipeline | Lower adoption barrier, still source-controllable |
| Compliance requires data minimization | Scratch Orgs + scripted seed | No production data ever enters the environment |

---

## Recommended Workflow

Step-by-step instructions for designing or reviewing an environment strategy:

1. **Map test types to stages** — List every type of testing the program requires (unit, integration, UAT, performance, training). Each type becomes a pipeline stage and drives at least one environment requirement.
2. **Select org types per stage** — Use the Decision Guidance matrix above to assign the cheapest org type that meets the stage's data volume, source tracking, and parity requirements.
3. **Align to branching strategy** — Confirm environment count matches the team's branching model. Trunk-based needs fewer persistent envs; Gitflow needs one per active long-lived branch.
4. **Design refresh and expiry governance** — For each sandbox, define refresh cadence, who owns the refresh, what post-refresh automation runs (Named Credentials, users, integration re-config), and masking requirements for any sandbox containing real data.
5. **Validate against Salesforce edition limits** — Confirm available Full and Partial Copy sandbox allocations. If the design requires more than the edition provides, revise the topology or plan a license upgrade.
6. **Document the environment matrix** — Use the template in `templates/environment-strategy-template.md`. Record type, purpose, branch alignment, data volume, source tracking, and refresh cadence.
7. **Run the checker script** — Execute `scripts/check_env_strategy.py` against the project root to confirm `sfdx-project.json` and a scratch org definition file are present if scratch orgs are part of the design.

---

## Review Checklist

Run through these before marking environment strategy design complete:

- [ ] Every pipeline stage (CI, integration, UAT, performance, training) has an assigned environment type
- [ ] Org types are matched to the cheapest option that meets each stage's requirements
- [ ] Branching strategy is documented and environment count matches it
- [ ] Scratch org expiry (30-day max) is accounted for in CI automation
- [ ] Full and Partial Copy sandboxes have a documented refresh cadence and post-refresh runbook
- [ ] Any sandbox receiving production data has a masking plan in place
- [ ] Named Credentials, users, and integration endpoints are re-configured via automation after each refresh
- [ ] Environment count is within available sandbox license allocations

---

## Salesforce-Specific Gotchas

1. **Scratch org data is lost on expiry and not transferable** — Scratch orgs are disposable. Any data loaded into a scratch org for testing is gone when the org expires or is deleted. Persistent integration state must live in a sandbox or be scripted for re-seeding. Never use a scratch org as a shared data store across team members.

2. **Full Sandbox refresh window is 29 days** — The Full sandbox can only be refreshed once every 29 days. If a release or incident forces an unplanned refresh, the next scheduled window is pushed out by the full 29-day clock from the refresh date. Plan releases around this constraint, not around calendar quarters.

3. **Sandbox Preview opt-in can break environments before scheduled release** — Salesforce rolls out new releases to sandboxes before production. Sandboxes enrolled in Sandbox Preview receive the release several weeks early. If your scratch org definition targets a feature that behaves differently between the current release and the preview, CI can start failing before production is ever updated. Explicitly opt sandboxes out of preview when stability is critical.

4. **Source tracking is not available on Partial Copy or Full sandboxes** — Only scratch orgs and Developer/Developer Pro sandboxes support the `sf project deploy start --source-dir` source-tracking flow. Teams that deploy to Partial Copy or Full sandboxes must use `sf project deploy start --manifest` (package.xml-based) instead. Mixing source-tracked and manifest-based deployment commands in the same pipeline causes silent metadata drift.

5. **Scratch org limits apply per Dev Hub, not per project** — The default active scratch org limit is 40 per Dev Hub (200 on higher plans). A CI pipeline that creates scratch orgs per PR and never deletes them will hit this limit silently, causing new org creation to fail. Every CI run must explicitly delete scratch orgs after use with `sf org delete scratch`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Environment matrix | Table of all environments with type, purpose, data volume, source tracking, branch alignment, and refresh cadence |
| Org-count recommendation | Minimum and recommended environment count with rationale tied to team size and branching model |
| Branching alignment notes | Mapping of each branch tier to its corresponding environment |
| Environment governance checklist | Post-refresh runbook items, masking requirements, and ownership assignments |

---

## Related Skills

- **admin/sandbox-strategy** — Use for detailed sandbox-type selection, refresh governance, and masking within a sandbox-only topology. NOT for scratch org or cross-type decisions.
- **devops/scratch-org-management** — Use for scratch org lifecycle, definition files, and daily developer usage patterns. NOT for overall topology design.
- **devops/release-management** — Use for release pipeline mechanics, change set promotion, and deployment orchestration. NOT for environment type selection.
- **devops/continuous-integration-testing** — Use for CI pipeline design and Apex test execution. Assumes environment strategy has already been decided.
