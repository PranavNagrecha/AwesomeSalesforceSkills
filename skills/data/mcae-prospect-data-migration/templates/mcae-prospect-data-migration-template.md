# MCAE Prospect Data Migration — Work Template

Use this template when planning or executing an MCAE prospect import or migration task.

---

## Scope

**Skill:** `mcae-prospect-data-migration`

**Request summary:** (fill in what the user or stakeholder asked for)

**Migration type:** (check one)
- [ ] External import — from legacy CRM, ESP, or spreadsheet into MCAE
- [ ] Cross-BU migration — from one MCAE Business Unit to another (requires Salesforce Support case)

---

## Pre-Migration Context

Answer these questions before any work begins:

| Question | Answer |
|---|---|
| Target MCAE Business Unit name | |
| Salesforce Connector active? (yes/no) | |
| Source system / file type | |
| Estimated record count in source CSV | |
| Custom fields required in the import? (yes/no) | |
| List all custom fields needed (one per row) | |
| Are all custom fields connector-mapped bidirectionally? (yes/no) | |
| Does the source data include engagement metrics (opens, clicks, score)? | |
| Stakeholders informed engagement history cannot be migrated? (yes/no) | |

---

## Custom Field Verification Checklist

For each custom field that must be included in the import:

| Custom Field Label | Salesforce Object Field API Name | MCAE Field Created? | Connector Mapped Bidirectionally? |
|---|---|---|---|
| (field 1) | | [ ] | [ ] |
| (field 2) | | [ ] | [ ] |
| (field 3) | | [ ] | [ ] |

Complete this table before running the import. Do not proceed if any row has an unchecked box.

---

## Source CSV Preparation

- [ ] Source CSV exported from: ___________________________
- [ ] Record count in source CSV: ___________________________
- [ ] Deduplicated on Email column (remove duplicate emails)
- [ ] Rows with blank Email removed
- [ ] Engagement metric columns removed from CSV (opens, clicks, last activity date, score)
- [ ] CSV split into chunks of ≤100,000 rows if record count exceeds 100,000
  - Number of files: _____
  - File names: ___________________________

---

## Field Mapping Plan

Document how each CSV column maps to an MCAE field before starting the import:

| CSV Column Header | MCAE Field | Field Type | Action |
|---|---|---|---|
| Email | Email | Default | Map |
| FirstName | First Name | Default | Map |
| LastName | Last Name | Default | Map |
| Company | Company | Default | Map |
| Phone | Phone | Default | Map |
| (custom column 1) | | Custom | Map / Do not import |
| (custom column 2) | | Custom | Map / Do not import |
| (engagement column) | (none — excluded) | N/A | Do not import |

---

## Engagement History Scope Statement

(Fill in and obtain stakeholder sign-off before migration)

The following engagement data from the source system **cannot** be migrated to MCAE and will be excluded from this import:

- [ ] Email open counts / open history
- [ ] Email click counts / click history
- [ ] Form submission history
- [ ] Page view history
- [ ] Lead/engagement scores derived from activity
- [ ] Other: ___________________________

**Post-migration plan to rebuild engagement signal:**
- Score-gated automation rules suppressed for: _____ days after cut-over
- Re-engagement campaign planned: (yes/no) — Target send date: _______________
- Stakeholder sign-off obtained from: ___________________________  Date: _______________

---

## Import Execution Log

| File Name | Record Count | Import Submitted | Import Complete | Success Count | Error Count | Notes |
|---|---|---|---|---|---|---|
| part 1 of ___ | | | | | | |
| part 2 of ___ | | | | | | |

---

## Post-Import Verification

- [ ] Import completion notification received
- [ ] Total imported record count matches expected count
- [ ] Spot-checked 5–10 records in MCAE Prospects view
- [ ] Default field values correct on spot-checked records
- [ ] Custom field values present and correct on spot-checked records
- [ ] Imported prospects assigned to the correct MCAE list(s)
- [ ] No unexpected overwrites on existing prospect records

---

## Outputs and Handoff

| Artifact | Status | Notes |
|---|---|---|
| Imported prospect list in MCAE | | |
| Field mapping log (this document) | | |
| Engagement history scope statement (signed off) | | |
| Post-migration re-engagement campaign brief | | |

---

## Notes and Deviations

(Record any decisions made that deviate from the standard pattern and why.)
