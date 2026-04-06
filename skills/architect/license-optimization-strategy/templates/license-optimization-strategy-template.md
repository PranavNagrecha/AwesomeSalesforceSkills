# License Optimization Strategy — Work Template

Use this template when auditing license utilisation, recommending right-sizing, or reclaiming inactive seats for a Salesforce org.

---

## Scope

**Skill:** `license-optimization-strategy`

**Org:** (org name / environment — production, sandbox, etc.)

**Request summary:** (describe what triggered this review — cost audit, renewal preparation, license ceiling alert, offboarding backlog, etc.)

**Date of assessment:** (YYYY-MM-DD)

---

## License Baseline

*Pull from Setup > Company Information and SOQL queries against UserLicense and PermissionSetLicense.*

### User License Summary

| License Type | Seats Purchased | Seats In Use | Available Headroom | % Utilised |
|---|---|---|---|---|
| Salesforce (CRM) | | | | |
| Salesforce Platform | | | | |
| Identity | | | | |
| Customer Community | | | | |
| Customer Community Login | | | | |
| Partner Community | | | | |
| Partner Community Login | | | | |
| (other) | | | | |

### Permission Set License Summary

| PSL Name | Seats Purchased | Seats Assigned | Available | % Utilised |
|---|---|---|---|---|
| (PSL 1) | | | | |
| (PSL 2) | | | | |
| (PSL 3) | | | | |

---

## Inactive User Analysis

*Query: `SELECT Id, Name, Username, LastLoginDate, Profile.UserLicense.Name FROM User WHERE IsActive = true ORDER BY LastLoginDate ASC NULLS FIRST`*

### Never-Logged-In Users

| User Name | Username | License Type | Created Date | Recommended Action |
|---|---|---|---|---|
| | | | | Freeze + notify, deactivate after [date] |

**Count:** _____ users | **Seats recoverable:** _____

### Inactive 90+ Days

| User Name | Username | License Type | Last Login Date | Recommended Action |
|---|---|---|---|---|
| | | | | Freeze + notify, deactivate after [date] |

**Count:** _____ users | **Seats recoverable:** _____

### Active Within 90 Days (retain)

**Count:** _____ users — no action required.

---

## License Right-Sizing Recommendations

*For each user group, document actual object usage vs. assigned license tier.*

### Group: [Job Function / Profile Name]

- **Current license:** Salesforce (CRM)
- **User count:** _____
- **Actual object access:** (list standard CRM objects used — Leads, Opportunities, Cases, etc.)
- **Recommended license:** (Salesforce Platform / Identity / retain CRM)
- **Rationale:** (why this group qualifies or does not qualify for a downgrade)
- **Sandbox validation status:** [ ] Not started / [ ] In progress / [ ] Validated / [ ] Not applicable
- **Projected cost impact:** (estimated annual saving if migration proceeds)

*Repeat block for each user group.*

---

## PSL Rationalisation Plan

*For each PSL with surplus assignments, document action.*

### PSL: [PSL Name]

- **Seats purchased:** _____
- **Seats assigned:** _____
- **Users inactive 90+ days with this PSL:** _____
- **Integration users with this PSL:** (list — check before unassigning)
- **Automations depending on this PSL:** (list flows, batch jobs — check before unassigning)
- **Safe-to-unassign count:** _____
- **Planned unassignment date/window:** (schedule for off-peak)
- **Seats to recover:** _____

*Repeat block for each PSL under review.*

---

## Login-Based License Evaluation

*Complete this section if any user population logs in fewer than 6 times per month and LBL entitlement may be available.*

### Population: [User Group Name]

- **Current license type:** _____
- **User count:** _____
- **Median logins per user per month (from LoginHistory):** _____
- **Contracted per-seat monthly cost:** _____
- **Contracted LBL per-login cost:** _____
- **Breakeven logins per month per user:** _____ (per-seat cost / per-login cost)
- **LBL entitlement available:** [ ] Yes / [ ] No / [ ] Confirm with AE
- **Recommendation:** (migrate to LBL / retain per-seat / investigate further)
- **Projected monthly cost delta:** _____

---

## Reclamation Execution Tracker

| Action | Target Users / PSLs | Freeze Date | Notify Date | Deactivate / Unassign Date | Seats Recovered | Status |
|---|---|---|---|---|---|---|
| Deactivate never-logged-in | (list or count) | | | | | |
| Deactivate 90-day inactive | (list or count) | | | | | |
| PSL unassign: [PSL name] | (list or count) | N/A | N/A | | | |
| License downgrade: [group] | (list or count) | N/A | N/A | | | |

---

## Review Checklist

- [ ] License baseline exported from Setup > Company Information for all license types and PSLs
- [ ] Active-user query run; results segmented by login recency
- [ ] Inactive users frozen and notified before any deactivation; seat recovery confirmed after deactivation
- [ ] License tier right-sizing validated in sandbox before production changes; profile-to-license binding confirmed
- [ ] PSL assignments audited; integration users and dependent automations checked before any unassignment
- [ ] Login-Based License economics evaluated for infrequent-access populations where entitlement exists
- [ ] License utilisation report and right-sizing recommendation produced with projected cost impact

---

## Notes and Deviations

*(Record any exceptions to the standard pattern, business constraints that prevent a recommended action, or follow-up items for the next review cycle.)*
