# Knowledge Base Administration — Work Template

Use this template when setting up, reviewing, or troubleshooting Lightning Knowledge in a Salesforce org.

## Scope

**Skill:** `knowledge-base-administration`

**Request summary:** (fill in what the user asked for — e.g., "Set up Lightning Knowledge with two article types and audience-scoped visibility")

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md:

- **Lightning Knowledge enabled?** (Yes / No — if No, confirm enablement is irreversible before proceeding)
- **Classic Knowledge in use?** (Yes / No — if Yes, migration plan must exist before enablement)
- **Content types needed:** (e.g., FAQ, How-To, Known Issue, Release Note)
- **Audience segments:** (e.g., Internal Agents, Partner Users, Customer Community)
- **Approval/review requirements:** (e.g., compliance officer sign-off required, or none)
- **Known constraints:** (e.g., 5-group limit for Data Categories, no existing category hierarchy)

---

## Record Type Design

| Record Type Name | Intended Audience | Key Fields | Page Layout Name | Profiles Assigned |
|---|---|---|---|---|
| (e.g., FAQ) | (e.g., All users) | (e.g., Question, Answer) | (e.g., FAQ Layout) | (e.g., Support Agent, Partner) |
| (e.g., Known Issue) | (e.g., Internal agents only) | (e.g., Root Cause, Workaround) | (e.g., Known Issue Layout) | (e.g., Support Agent) |

---

## Data Category Group Design

| Category Group | Purpose | Top-Level Categories | Visibility: Internal Agents | Visibility: Partners | Visibility: Customers |
|---|---|---|---|---|---|
| (e.g., Products) | Content org + visibility | (e.g., Product A, Product B) | All | Product A only | Product A only |

**Guest User Default Category Access:** (No Access / [specific category])

---

## Publishing Workflow Decision

Select the appropriate workflow for this org:

- [ ] **Native statuses only** (Draft → Published → Archived) — appropriate for small teams with high author trust
- [ ] **Validation Status enabled** — adds quality signal picklist without blocking publish
  - Picklist values: (list planned values, e.g., "Draft", "Ready for Review", "Validated", "Not Validated")
- [ ] **Approval Process on Knowledge__kav** — blocking gate before publish
  - Approver role/user: ___
  - Entry criteria: ___
  - On approve: Field Update → Validation Status = ___
  - On reject: Notification to author + Field Update → Validation Status = ___

---

## Checklist

Work through items in order. Tick as complete.

- [ ] Stakeholders acknowledged Lightning Knowledge enablement is irreversible
- [ ] Record type taxonomy designed and approved before enabling in production
- [ ] Lightning Knowledge enabled in the target environment
- [ ] Record types created in Object Manager > Knowledge > Record Types
- [ ] Page layouts created and assigned to record types
- [ ] Record types assigned to appropriate author profiles
- [ ] Data Category Groups created (confirm total active groups for Knowledge is 5 or fewer)
- [ ] Category hierarchy built to reflect content taxonomy
- [ ] Category visibility assigned to roles/profiles for each audience segment
- [ ] Guest user default category access configured (if public Knowledge surface exists)
- [ ] Validation Status picklist enabled (if required)
- [ ] Approval Process created and activated on Knowledge__kav (if required)
- [ ] Pilot article created for each record type, assigned to appropriate category
- [ ] Visibility verified by logging in as a test user from each audience segment
- [ ] Unclassified article behavior tested (confirm expected invisibility to standard users)
- [ ] Re-publish behavior tested (confirm previous published version archives immediately)
- [ ] Admin runbook documented with record type taxonomy and category structure

---

## Notes

Record any deviations from the standard pattern and their rationale:

(e.g., "Used Profile-based category visibility instead of Role-based for Partner tier because partner users share a role with other non-Knowledge users — override required at profile level")
