# Data Cloud vs CRM Analytics — Decision Record Template

Use this template when documenting a platform boundary decision for architecture review. It complements `SKILL.md` in `architect/data-cloud-vs-analytics-decision`.

## Scope

**Skill:** `data-cloud-vs-analytics-decision`

**Request summary:** (what leadership or the project asked)

## Context Gathered

Record the answers to the Before Starting questions from `SKILL.md`:

- Primary outcome (activation, embedded BI, warehouse handoff, compliance):
- Data sources and systems of record:
- Harmonization / identity resolution required? (Yes / No + why):
- Intended analytics surfaces (CRM Analytics only, external BI, both):
- Known latency or freshness SLAs:
- Existing licenses (Data Cloud, CRM Analytics, neither, both):

## Platform roles (one sentence each)

- **Data Cloud owns:**
- **CRM Analytics owns:**
- **Explicitly out of scope for this decision:**

## Direct Data / DMO decision (if applicable)

- DMOs or subject areas in scope:
- Evidence of mapping readiness (Contact Point / Party Identification where needed):
- Proof-of-concept scope and exit criteria:

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| | | |

## Approvals

- Data platform lead:
- Analytics lead:
- Security / privacy reviewer (if PII or activation):

## Related skills used next

- (e.g.) `architect/data-cloud-architecture` for DSO/DLO/DMO design
- (e.g.) `admin/einstein-analytics-basics` for CRM Analytics build

## Notes

Record deviations from the default complementary pattern and why.
