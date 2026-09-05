# Stakeholder RACI — Intake Sheet

**What this template is for:** the *intake*, not the deliverable. It captures the context that decides
how the matrix is shaped — phase, topology, regulatory overlay, packages, delegate groups, partner
exit date — before a single cell is filled. The deliverable itself is the sibling template,
`raci-matrix.md`. Use both, in that order: this sheet answers the questions, that template carries the
answers.

## Scope

**Skill:** `stakeholder-raci-for-sf-projects`

**Request summary:** (what did the user ask for — build a RACI from scratch, refresh an existing one, route a refusal code?)

**Project name:**

**Phase:** discovery / build / UAT / hypercare

**Target go-live:**

## Context Gathered

| Question | Answer |
|---|---|
| Org topology | single org / multi-org / M&A / regulated |
| Regulatory overlay | none / HIPAA / FINRA / PCI / GDPR / SOX / other |
| Managed packages in scope | (each one needs an AppExchange owner column) |
| Delegate groups already in the org | (retrieve them — they are the permission row as it actually stands) |
| Running integrations and their owners | (org-wide API allocation is shared; unlisted owners break rehearsed loads) |
| Existing CAB | yes (cadence + quorum) / no |
| Implementation partner | none / SI name + planned hypercare exit date |
| Next seasonal release + any pending Release Updates | (dates the programme does not control) |

## Questions to Ask Before Configuring

Work the table in `SKILL.md` § *Questions to Ask Before Configuring* and record the answers here. The
seven that most often change the shape of the matrix:

| Ask | Answer |
|---|---|
| Who loses something when the sandbox is refreshed, and who schedules it? | |
| Who signs off a data load — tool operator or record owner? | |
| Who decides when we activate a Release Update, against which enforcement release? | |
| Do today's delegate groups match what we are about to write about permissions? | |
| Is "the Salesforce admin" one column or several roles one person fills? | |
| Which running integrations exist, and who owns each? | |
| Multi-org: does each role mean the same person in every org? | |

## Stakeholder Roster — Confirmation

| Role | Named individual | Confirmed by user? |
|---|---|---|
| Business sponsor | _____________ | yes / no |
| Process owner | _____________ | yes / no |
| Data steward | _____________ | yes / no |
| Security architect | _____________ | yes / no |
| Integration architect | _____________ | yes / no |
| CRM admin lead | _____________ | yes / no |
| Release manager | _____________ | yes / no |
| AppExchange owner(s) | _____________ | yes / no |
| Compliance officer | _____________ | yes / no |
| End-user representative | _____________ | yes / no |

If any role lacks a named individual, surface as a project risk before drafting the matrix.

## Approach

Fill `templates/raci-matrix.md` — the markdown tables for circulation, then the YAML block as the file
of record — and lint it:

```bash
python3 scripts/check_raci.py --file <path>/raci.yaml --repo-root <repo-root> --strict
```

Copy the filled reference version from `references/worked-examples.md` rather than retyping the
skeleton.

## Checklist

- [ ] All ten required activity slugs have a row
- [ ] Every row has exactly one A, and at least one R
- [ ] No row has A on a C role
- [ ] Every cell is from the enum (R, A, C, I, or `-`)
- [ ] Every A cell has trigger + target + time-box, and the target is not that row's A
- [ ] Programme escalation path has level, forum, chair, time-box
- [ ] `executed_by` filled per row and every path resolves
- [ ] Refusal-code-to-stakeholder map filled
- [ ] Delegate groups retrieved and diffed against the permission row
- [ ] Sponsor + steerco review date scheduled
- [ ] `check_raci.py --strict` exits clean against the YAML

## Notes

(Record deviations from the canonical pattern, partner-A transfer dates, regulatory-row scoping, and any open stakeholder-roster gaps here.)
