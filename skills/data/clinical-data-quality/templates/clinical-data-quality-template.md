# Clinical Data Quality — Work Template

Use this template when working on patient deduplication, Person Account merge, or clinical record integrity tasks in a Health Cloud org.

## Scope

**Skill:** `clinical-data-quality`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer these before proceeding — incorrect assumptions here are the most common source of production failures.

- **Person Accounts enabled?** Yes / No
- **Clinical objects in scope** (list all objects with Account/PatientId lookups):
  - EpisodeOfCare: Yes / No
  - PatientMedication: Yes / No
  - ClinicalEncounter: Yes / No
  - CareObservation: Yes / No
  - CoveredBenefit: Yes / No
  - Custom objects: (list names and their Account lookup field API names)
- **Estimated duplicate pair volume:** (small <50 / medium 50–500 / large >500)
- **Third-party MPI in scope?** Yes / No / Evaluating
- **HIPAA / regulatory audit requirements?** Yes / No / Unknown
- **Duplicate Rule and Matching Rule already configured?** Yes / No / Needs review

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1: Configure Matching Rules and Duplicate Rules for Person Account detection (new or updated configuration)
- [ ] Pattern 2: Pre-merge clinical record reassignment batch (one-time merge project)
- [ ] Both patterns (new org setup with deduplication + upcoming merge campaign)
- [ ] MPI evaluation / third-party ISV selection (large org or multi-source)

**Why this pattern applies:** (fill in rationale)

## Pre-Merge Reassignment Checklist

Complete this before any merge DML executes:

- [ ] All clinical objects in scope identified and their Account lookup field API names confirmed
- [ ] `PreMergePatientReassignment` batch (or equivalent) implemented and unit-tested in sandbox
- [ ] Batch executed for the target duplicate pair — no errors reported
- [ ] Post-reassignment query confirms zero records on losing Account ID for each clinical object:
  ```soql
  SELECT COUNT() FROM EpisodeOfCare WHERE AccountId = '[losingAccountId]'
  SELECT COUNT() FROM PatientMedication WHERE PatientId = '[losingAccountId]'
  SELECT COUNT() FROM ClinicalEncounter WHERE AccountId = '[losingAccountId]'
  -- (repeat for all clinical objects in scope)
  ```
- [ ] All counts return 0 — proceed to merge
- [ ] Merge executed: `merge masterAccount duplicateAccount;`

## Post-Merge Audit Checklist

Complete after merge DML:

- [ ] Winning Account record exists and has correct identity fields
- [ ] Clinical record counts on winning Account = sum of pre-merge counts on both accounts:
  ```soql
  SELECT COUNT() FROM EpisodeOfCare WHERE AccountId = '[winningAccountId]'
  -- expected: count from master + count from duplicate (before reassignment)
  ```
- [ ] No orphaned records found for the deleted Account ID (query by known record IDs if available)
- [ ] If HIPAA audit required: merge decision logged in audit object with User ID, timestamp, and reason

## Duplicate Rule Configuration Checklist

- [ ] Matching Rule scoped to **Account** object (not Contact)
- [ ] Match criteria include FirstName, LastName, PersonBirthdate at minimum
- [ ] Additional identifier field (e.g., MedicalRecordNumber__c) included if available in org
- [ ] Duplicate Rule filter includes `IsPersonAccount = true` to scope to patients only
- [ ] Initial action set to **Alert** mode (not Block) until match quality is validated

## Notes

Record any deviations from the standard pattern and why:

- (e.g., custom clinical object not in the standard batch — added MyClinicalObject__c with PatientLookup__c field)
- (e.g., org has a third-party MPI — Matching Rule configured as fallback only)
- (e.g., HIPAA audit object implemented using MergeDecisionLog__c custom object — see implementation notes)
