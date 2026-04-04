# Security Health Check Review — Worksheet

> Use this template to document a Health Check review session. Fill in every section. Archive completed worksheets for audit and trend tracking.

---

## Review Metadata

| Field | Value |
|---|---|
| Org name / ID | |
| Org type | Production / Full Sandbox / Partial Sandbox / Developer Sandbox / Scratch |
| Baseline in use | Salesforce Standard / Custom: _____________ |
| Health Check score | ________ % |
| Previous score (if known) | ________ % (reviewed on: _____________ ) |
| Reviewed by | |
| Review date | |
| Triggered by | Routine / Post-release / Audit / Incident |
| Salesforce release active | Spring '__ / Summer '__ / Winter '__ |

---

## Score Summary

| Risk Category | Failing Count | Passing Count | Notes |
|---|---|---|---|
| High Risk | | | |
| Medium Risk | | | |
| Low Risk | | | |
| Informational | | | Score not affected |
| **Total** | | | |

---

## High Risk Findings

> These must be remediated first. Each High Risk failure has the greatest weight on the overall score.

| # | Setting Name | Current Org Value | Required Standard Value | Owner | Target Date | Status |
|---|---|---|---|---|---|---|
| 1 | | | | | | Open / In Progress / Done |
| 2 | | | | | | |
| 3 | | | | | | |

---

## Medium Risk Findings

| # | Setting Name | Current Org Value | Required Standard Value | Owner | Target Date | Status |
|---|---|---|---|---|---|---|
| 1 | | | | | | Open / In Progress / Done |
| 2 | | | | | | |
| 3 | | | | | | |

---

## Low Risk Findings

| # | Setting Name | Current Org Value | Required Standard Value | Owner | Target Date | Status |
|---|---|---|---|---|---|---|
| 1 | | | | | | Open / In Progress / Done |
| 2 | | | | | | |

---

## Informational Items Under Review

> Informational items do not affect the score. Review them for genuine risk anyway.

| Setting Name | Org Value | Informational Reason | Risk Accepted? | Notes |
|---|---|---|---|---|
| | | | Yes / No | |
| | | | Yes / No | |

---

## Custom Baseline Status

> Complete this section only if a custom baseline is active.

| Field | Value |
|---|---|
| Baseline file name / version | |
| Date last imported | |
| Number of settings deviating from Salesforce standard | |
| All deviations documented with justification? | Yes / No / N/A |
| Baseline reviewed against current Salesforce standard? | Yes / No |
| Location of baseline XML in version control | |

### Deviation Register

> List every setting where the custom baseline differs from the Salesforce standard.

| Setting Name | Salesforce Standard Value | Custom Baseline Value | Risk Type in Custom | Business Justification |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

## Remediation Plan

| Priority | Setting | Action Required | Owner | Due Date |
|---|---|---|---|---|
| 1 (High Risk) | | | | |
| 2 (High Risk) | | | | |
| 3 (Medium Risk) | | | | |

---

## Tooling API Queries Used

> Record any Tooling API queries used to retrieve or snapshot findings for this review.

```
-- Overall score
SELECT Score FROM SecurityHealthCheck

-- All failing settings
SELECT SettingName, RiskType, OrgValue, StandardValue, MeetsStandard
FROM SecurityHealthCheckRisks
WHERE MeetsStandard = false
ORDER BY RiskType ASC

-- High Risk failures only
SELECT SettingName, OrgValue, StandardValue
FROM SecurityHealthCheckRisks
WHERE MeetsStandard = false AND RiskType = 'HIGH_RISK'
```

API version used: v______.0
Endpoint: `[instance_url]/services/data/v______.0/tooling/query/?q=...`

---

## Review Sign-Off Checklist

- [ ] Overall score recorded and compared to previous review.
- [ ] All High Risk findings have an assigned owner and target date.
- [ ] All Medium Risk findings have been triaged.
- [ ] Informational items reviewed for genuine risk.
- [ ] Custom baseline deviations are documented with justification (if applicable).
- [ ] No settings demoted to Informational solely to improve the score.
- [ ] Post-release review completed if this review was triggered by a Salesforce release.
- [ ] Worksheet archived and accessible to auditors.

---

## Notes and Exceptions

> Record any findings that require formal risk acceptance, escalation, or cross-team coordination.

| Setting | Exception Reason | Approved By | Expiry Date |
|---|---|---|---|
| | | | |
| | | | |
