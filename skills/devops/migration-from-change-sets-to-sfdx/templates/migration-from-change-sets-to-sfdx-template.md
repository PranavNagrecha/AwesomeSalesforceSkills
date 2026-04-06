# Migration From Change Sets To SFDX — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `migration-from-change-sets-to-sfdx`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Metadata types currently promoted via change sets:
- Org authenticated with sf CLI (alias):
- Git repository exists: yes / no
- Team size and release cadence:
- Target end state: manifest-based / unlocked packages / DevOps Center

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] **Pattern 1: Phased Retrieval and Conversion** — incremental, batch-by-batch migration
- [ ] **Pattern 2: Shadow Period** — parallel change set + CLI deploys during transition
- [ ] **Pattern 3: Direct-to-Packages** — migrate and immediately adopt unlocked packages

## Migration Batch Plan

| Batch | Metadata Types | Sprint/Phase | Owner | Status |
|-------|---------------|-------------|-------|--------|
| 1 | Apex classes, triggers | | | |
| 2 | Custom objects, fields | | | |
| 3 | Flows, process builders | | | |
| 4 | LWC, Aura components | | | |
| 5 | Permission sets, layouts | | | |
| 6 | Reports, dashboards | | | |

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] All actively-maintained metadata types are retrieved and converted to source format
- [ ] Source format files are committed to a git repository with logical, per-batch commits
- [ ] Round-trip deploy to a sandbox succeeds with zero errors for the full source directory
- [ ] sfdx-project.json has correct sourceApiVersion matching the org's current API version
- [ ] .forceignore is configured to exclude metadata the team does not own
- [ ] Team members have authenticated their orgs with sf org login
- [ ] At least one production deploy has been completed via CLI
- [ ] Change set workflow is formally retired and runbooks are updated

## Notes

Record any deviations from the standard pattern and why.
