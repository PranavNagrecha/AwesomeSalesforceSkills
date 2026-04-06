# Salesforce DevOps Tooling Selection — Work Template

Use this template when evaluating and selecting a DevOps platform for a Salesforce program.

## Scope

**Skill:** `salesforce-devops-tooling-selection`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Team composition:** (admin count, developer count, Git literacy level)
- **Compliance requirements:** (SOC 2, FedRAMP, HIPAA, data residency — or none)
- **Budget:** (per-user range, per-org range, or total annual budget)
- **Git provider:** (GitHub, GitLab, Bitbucket, Azure DevOps)
- **Org footprint:** (number of production orgs, sandbox types, scratch org usage)
- **Existing tooling:** (change sets, custom scripts, current CI/CD platform)

## Constraint-Based Elimination

| Constraint | Eliminated Tools | Reason |
|---|---|---|
| (e.g., FedRAMP required) | (e.g., Gearset, AutoRABIT, Blue Canvas) | (SaaS hosting violates data residency) |
| | | |
| | | |

## Shortlisted Tools

| Tool | Hosting Model | Strength for This Team | Known Risk |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

## Proof-of-Concept Results

| Scenario | Tool A Score | Tool B Score | Notes |
|---|---|---|---|
| Deploy Flow + Apex + Custom Metadata | | | |
| Rollback a failed deployment | | | |
| Resolve a merge conflict | | | |
| Admin deploys a declarative change | | | |
| Generate deployment audit report | | | |

## Recommendation

**Selected tool:** (name)

**Rationale:** (2-3 sentences linking constraints, evaluation results, and team fit)

**Known limitations:** (list risks the team accepts with this choice)

## Migration Plan

- [ ] Document current deployment process and tooling
- [ ] Set up selected tool in a sandbox environment
- [ ] Migrate pipeline configurations
- [ ] Train team members (admins and developers separately if needed)
- [ ] Run parallel deployments through old and new tools for 2-4 weeks
- [ ] Cut over to new tool and decommission old process
- [ ] Verify audit trail and compliance reporting in new tool

## Notes

Record any deviations from the standard pattern and why.
