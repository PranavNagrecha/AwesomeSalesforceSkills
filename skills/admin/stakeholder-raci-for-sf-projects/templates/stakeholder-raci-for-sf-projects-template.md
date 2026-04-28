# Stakeholder RACI — Work Template

Use this template when activating the `stakeholder-raci-for-sf-projects` skill on a real engagement.

## Scope

**Skill:** `stakeholder-raci-for-sf-projects`

**Request summary:** (what did the user ask for — build a RACI from scratch, refresh an existing one, route a refusal code?)

**Project name:**

**Phase:** discovery / build / UAT / hypercare

**Target go-live:**

## Context Gathered

- **Org topology:** single org / multi-org / M&A / regulated
- **Regulatory overlay:** none / HIPAA / FINRA / PCI / GDPR / SOX / other
- **Managed packages in scope:** (list each — each one needs an AppExchange owner column)
- **Existing CAB:** yes (cadence + quorum) / no
- **Implementation partner:** none / SI name + planned hypercare exit date

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

Use `templates/raci-matrix.md` as the canonical artifact. Fill the markdown, mirror to JSON, run `scripts/check_raci.py` against the JSON.

## Checklist

- [ ] Every row has exactly one A
- [ ] No row has A on a C role
- [ ] Every row has at least one R
- [ ] Every cell is from the enum (R, A, C, I, or `—`)
- [ ] Every A cell has trigger + target + time-box
- [ ] Refusal-code-to-stakeholder map filled
- [ ] Sponsor + steerco review date scheduled
- [ ] `check_raci.py` exits clean against the JSON

## Notes

(Record deviations from the canonical pattern, partner-A transfer dates, regulatory-row scoping, and any open stakeholder-roster gaps here.)
