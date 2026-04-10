# Health Cloud Timeline — Work Template

Use this template when configuring or troubleshooting the Industries Enhanced Timeline in Health Cloud.

## Scope

**Skill:** `health-cloud-timeline`

**Request summary:** (fill in what the user asked for — e.g., "Add ClinicalEncounter to patient timeline", "Migrate from legacy HealthCloud.Timeline component", "Timeline filter categories not appearing")

---

## Context Gathered

Answer each question before beginning configuration work.

| Question | Answer |
|---|---|
| Org has Health Cloud or Industries license with Timeline permission? | Yes / No |
| Industries Timeline component or legacy HealthCloud.Timeline currently on page? | Industries / Legacy / Neither |
| API version in sfdx-project.json | e.g., 58.0 |
| Objects to surface on timeline | e.g., ClinicalEncounter, Care_Gap__c |
| Account relationship field for each object | e.g., AccountId (standard), Account__c (custom) |
| Desired timeline category names | e.g., Encounters, Care Gaps, Medications |
| Are category values already in Setup > Timeline > Categories? | Yes / No / Partial |

---

## Object Relationship Audit

Complete one row per object before writing any TimelineObjectDefinition metadata.

| Object API Name | Account Relationship Field | Direct or Chained? | Date Field | Name Field | Description Field |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |

Objects without an Account relationship path: (list any — these cannot appear on the timeline without schema changes)

---

## Timeline Category Plan

List all categories needed. Cross-reference against Setup > Timeline > Categories before deployment.

| Category Label (exact) | Exists in Setup? | Objects Assigned |
|---|---|---|
| | | |
| | | |
| | | |

---

## TimelineObjectDefinition Checklist

One row per definition to create or update.

| Object | Definition File Created | active = true | dateField Confirmed (not formula) | Category Matches Setup | Deployed |
|---|---|---|---|---|---|
| | [ ] | [ ] | [ ] | [ ] | [ ] |
| | [ ] | [ ] | [ ] | [ ] | [ ] |
| | [ ] | [ ] | [ ] | [ ] | [ ] |

---

## Migration Checklist (if moving from legacy HealthCloud.Timeline)

- [ ] Audited legacy timeline configuration (Custom Settings or managed package config)
- [ ] Created TimelineObjectDefinition for each previously configured object
- [ ] Created all required category values in Setup > Timeline > Categories
- [ ] Added Industries Timeline component to patient/member page layout in App Builder
- [ ] Removed legacy HealthCloud.Timeline component from the same page layout
- [ ] Validated both components are NOT simultaneously active on any page layout
- [ ] Tested on 3+ patient records with data in each configured object category

---

## Post-Deployment Validation

- [ ] Open 2+ patient records with data across all configured objects
- [ ] Confirm each timeline category appears in the filter picklist
- [ ] Confirm records render with correct icon, label, and date ordering
- [ ] Confirm no duplicate entries (would indicate both legacy and new components are active)
- [ ] Ran `python3 scripts/check_health_cloud_timeline.py --manifest-dir <path> --categories "<csv list>"`

---

## Approach Notes

Which pattern from SKILL.md applies?

- [ ] Adding a new custom object to the Enhanced Timeline
- [ ] Adding a standard Health Cloud clinical object to the Enhanced Timeline
- [ ] Migrating from legacy to Industries Timeline
- [ ] Troubleshooting missing timeline entries

Reason for pattern choice: ___

Deviations from standard pattern and why: ___

---

## Configuration Summary

Document final configuration for admin runbook.

| Object | Definition File | Date Field | Category | Icon | Deployed Date |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
