# Git Branching For Salesforce — Work Template

Use this template when designing, reviewing, or documenting a Git branching strategy for a Salesforce project.

## Scope

**Skill:** `git-branching-for-salesforce`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer these before selecting a branching model:

- **Development model:** (org-based / source-driven / hybrid)
- **Team size:** (number of concurrent developers)
- **Package architecture:** (monolithic force-app / unlocked packages / managed 2GP / none)
- **Salesforce edition:** (e.g., Enterprise, Unlimited, Developer)
- **Sandbox allocations:** Full Copy: ___ / Partial Copy: ___ / Developer Pro: ___ / Developer: ___
- **Scratch org usage:** (yes/no, Dev Hub org identified?)
- **Release cadence:** (continuous / biweekly / monthly / quarterly)
- **Compliance or approval gates:** (yes/no — describe if yes)
- **Existing branching model (if any):** (describe current state)

## Selected Branching Model

**Model:** (trunk-based / environment branching / package-aligned / other)

**Rationale:** (why this model fits the context above)

## Branch Inventory

| Branch Pattern | Lifecycle | Maps To (Org) | Purpose |
|---|---|---|---|
| `main` | Long-lived | Production | Source of truth for released code |
| `develop` (if applicable) | Long-lived | ___ sandbox | Integration target for all feature work |
| `feature/<story>` | Short-lived (< ___ days) | Scratch org | Individual feature development |
| `release/<version>` (if applicable) | Medium-lived | ___ sandbox | Release freeze and UAT |
| `hotfix/<ticket>` | Short-lived | ___ sandbox | Emergency production fixes |
| `packaging/<pkg>` (if applicable) | Long-lived or CI-only | N/A | Package version creation |

## Branch Naming Conventions

```text
Feature:   feature/<story-id>-<short-description>
Release:   release/<YYYY.QN> or release/<semver>
Hotfix:    hotfix/<ticket-id>-<short-description>
Packaging: packaging/<package-name>
```

## Merge Flow

Describe the merge direction and rules:

```text
feature/* ──► (PR + CI) ──► ___
___ ──► (release freeze) ──► ___
___ ──► (deploy to prod) ──► main
hotfix/* ──► main AND ___
```

## Branch Protection Rules

| Branch | Direct Push | PR Required | CI Required | Reviews Required |
|---|---|---|---|---|
| `main` | No | Yes | Yes — deploy validation | ___ |
| `develop` | No | Yes | Yes — Apex tests | ___ |
| `release/*` | No | Yes | Yes — full test suite | ___ |

## Package Versioning Alignment (if applicable)

- Package versions created from branch: ___
- Ancestor version tracking: (auto from sfdx-project.json / manual)
- Promotion step: (describe when and how `sf package version promote` runs)

## Destructive Changes Process

- Destructive manifests stored in: `destructive/` directory
- CI detection: (describe how CI handles destructiveChanges.xml)
- Review process: (separate PR / flagged in same PR / other)

## Hotfix Workflow

1. Create `hotfix/<ticket>` from: ___
2. Validate fix in: ___ (org)
3. Merge to: `main` AND ___
4. Deploy to production via: ___
5. Tag: ___

## Review Checklist

- [ ] Every long-lived branch maps to a specific org
- [ ] Feature branch lifespan policy defined (max ___ days)
- [ ] Branch protection rules configured for main and integration branches
- [ ] Merge direction documented
- [ ] Hotfix path defined and does not block on normal release train
- [ ] Package versioning aligned to single linear branch (if applicable)
- [ ] Destructive changes process documented
- [ ] Branch naming conventions enforced by CI or hooks

## Notes

Record any deviations from the standard patterns and why.
