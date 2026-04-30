# Dynamic Forms Migration — Work Template

Use this template when migrating an object's record page from Page Layouts to Dynamic Forms.

---

## Scope

**Skill:** `dynamic-forms-migration`

**Object:** _(Account / Contact / Custom_Object__c)_

**Current page layout count:** _(per-record-type, per-profile)_

**Approach:** [ ] Single page with visibility rules  [ ] Multiple pages per record type

---

## Current State Audit

| Page Layout | Assigned Profiles | Assigned Record Types | Field Count |
|---|---|---|---|
| | | | |

---

## FLS Audit (Pre-Migration)

For each profile, confirm Field-Level Security matches expected access at the data layer (NOT via Dynamic Forms visibility):

| Profile | Field | FLS Read | FLS Edit | Expected? |
|---|---|---|---|---|
| | | [ ] | [ ] | [ ] |

Action: fix FLS discrepancies BEFORE adding visibility rules.

---

## Visibility Rule Plan

| Field / Section | Visibility Rule | Source (record-type-driven, profile-driven, value-driven) |
|---|---|---|
| Customer_Tier__c | `RecordType.DeveloperName equals 'Customer'` | Record-type |
| Commission_Amount__c | `$Permission.View_Commission_Fields equals true` | Custom Permission (preferred) |
| | | |

Prefer Custom Permissions over `$User.Profile.Name` strings.

---

## Coordinated Changes

| Surface | Change Required | Owner |
|---|---|---|
| Compact Layout | Review and update Highlights Panel field set | |
| Quick Action layouts | Audit for changes (Quick Actions still use Page Layout's QA section) | |
| Print View | Remains Page Layout-driven; verify retained layout has needed fields | |

---

## User-Impersonation Test Matrix

| Profile | Record Type | Expected Visible Fields | Verified |
|---|---|---|---|
| Sales Rep | Customer | (list) | [ ] |
| Sales Manager | Customer | (list, including commission) | [ ] |
| Sales Rep | Partner | (list) | [ ] |
| | | | |

---

## Mobile Verification

- [ ] iOS Salesforce Mobile App — sample record per record type renders correctly
- [ ] Android Salesforce Mobile App — same
- [ ] Mobile-specific visibility rules (`$Browser.FormFactor equals 'Phone'`) tested if used

---

## Decommissioning Plan

| Page Layout | Action | Reason |
|---|---|---|
| Sales_Layout | Retire | All assignments moved to Dynamic Forms page |
| Customer_Minimal | RETAIN | Required for Quick Actions, Print View, Classic users |
| | | |

---

## Sign-Off Checklist

- [ ] FLS audited per profile; fixes deployed
- [ ] "Upgrade Now" run in sandbox; auto-conversion verified against source layout
- [ ] Visibility rules added per the plan above; all use Custom Permissions where applicable
- [ ] Compact Layouts reviewed and updated for Highlights Panel
- [ ] Quick Action layouts verified
- [ ] User-impersonation testing completed for full Profile × RecordType matrix
- [ ] Mobile testing completed on real iOS and Android devices
- [ ] User preview window completed (1–2 weeks in sandbox with real users)
- [ ] At least one minimal Page Layout per record type retained (for QA / Print / Classic)
- [ ] Documentation: per-component visibility rules + business intent committed to source
