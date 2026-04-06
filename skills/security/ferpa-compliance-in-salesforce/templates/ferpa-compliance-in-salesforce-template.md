# FERPA Compliance in Salesforce — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `ferpa-compliance-in-salesforce`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Org type (Education Cloud / custom EDA):
- LearnerProfile deployed (yes/no):
- Individual sObject already linked to Contacts (yes/no):
- Fields classified as education records vs. directory information:
- Volume of records requests per semester:
- GDPR automation already in place (yes/no — important to avoid ShouldForget conflicts):

## Approach

Which pattern from SKILL.md applies? Why?

- Pattern 1 (LearnerProfile FERPA fields + consent automation): use for initial consent setup
- Pattern 2 (Directory information opt-out): use when handling opt-out requests
- 45-day tracking: use when implementing records request workflow

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Every student Contact has IndividualId populated
- [ ] LearnerProfile FERPA booleans populated and updated by automation
- [ ] ContactPointTypeConsent records exist for parental and third-party disclosure
- [ ] Directory information opt-out flag implemented and propagated
- [ ] Opted-out students excluded from all directory channels
- [ ] 45-day response window tracked with escalation
- [ ] FERPA rights transfer automation handles age-out and postsecondary enrollment
- [ ] FLS restricts education record fields from unauthorized profiles

## Notes

Record any deviations from the standard pattern and why.
