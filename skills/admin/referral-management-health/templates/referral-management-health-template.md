# Referral Management Health Cloud — Work Template

Use this template when configuring or troubleshooting Health Cloud referral management.

## Scope

**Skill:** `referral-management-health`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Health Cloud version / package version installed: 
- Are clinical referrals inbound, outbound, or both?
- Is provider search required? (Y/N)
- Is the HealthCloudICM permission set available in the org?
- Is the Data Pipelines Base User license provisioned?
- Are provider records using HealthcareProvider / HealthcarePractitioner record types?

## Referral Configuration Summary

| Setting | Value |
|---------|-------|
| ClinicalServiceRequest record types configured | |
| Referral Status picklist values | |
| Required fields on referral page layout | |
| Flow automation for status transitions | |
| Provider search DPE job scheduled | |

## Permission Set Assignments Needed

| User Type | HealthCloudICM | Data Pipelines Base User |
|-----------|---------------|--------------------------|
| Care coordinators | Required | Optional |
| Clinicians | Required | Optional |
| Integration/service user | Required if creates referrals | Required if runs DPE jobs |
| Admins | Required | Required for DPE setup |

## Provider Search Setup Checklist

- [ ] Data Pipelines Base User license assigned to DPE process user
- [ ] Provider records using HealthcareProvider record type on Account
- [ ] DPE job for CareProviderSearchableField configured in Setup > Data Processing Engine
- [ ] DPE job run manually and verified with: `SELECT Id, Name FROM CareProviderSearchableField LIMIT 10`
- [ ] DPE job scheduled for regular refresh (daily recommended)

## Referral Workflow Checklist

- [ ] ClinicalServiceRequest page layout includes PatientId, ReferralType, ReferredToId, Status
- [ ] Status picklist values match workflow (Draft, Submitted, In Review, Accepted, Declined, Completed, Cancelled)
- [ ] Flow automation covers all status transitions including error paths
- [ ] HealthCloudICM assigned to all referral user personas
- [ ] End-to-end referral creation and status update tested in sandbox

## Notes

(Record any deviations from standard pattern, custom requirements, or decisions made during implementation)
