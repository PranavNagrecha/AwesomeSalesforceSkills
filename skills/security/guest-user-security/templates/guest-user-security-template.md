# Guest User Security — Audit Template

Use this template to document a guest user security audit for one Experience Cloud site.

## Site Information

**Site Name:**
**Guest User Profile Name:**
**Site Purpose (public knowledge base / form submission / commerce / other):**

---

## Object Permission Audit

For each object accessible to the guest profile, complete this table:

| Object | Read | Create | Edit | Delete | View All | Modify All | Action Required |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

**Rule:** Guest profile should have maximum Read on objects needed for display. Only Create for form submission objects. Never Edit, Delete, View All, or Modify All.

---

## Field Permission Audit

For objects with Read access, review field permissions:

| Object | Sensitive Fields Accessible | Action Required |
|---|---|---|
| | | |

**Fields to check:** SSN, DOB, Email, Phone, BillingStreet, AnnualRevenue, financial data, health data

---

## Guest User Sharing Rule Inventory

| Object | Guest user sharing rule | Criteria | Records matched | Business justification | Action Required |
|---|---|---|---|---|---|
| | | | | | |

**Rule:** Guest org-wide defaults are Private for every object and can't be changed. Guest user sharing rules (criteria-based, Read Only) are the only way to grant a guest access to a record. OWD is not a lever — never propose changing it to grant guest access.

**Also check:** guest user still listed in a public group or queue, leftover manual shares, leftover Apex managed shares. None of these reach guests any more; all are stale grants to remove.

---

## Apex Class Review

For each @AuraEnabled or @RestResource class reachable from the guest site:

| Class Name | `with sharing`? | `WITH USER_MODE` in SOQL? | Action Required |
|---|---|---|---|
| | | | |

---

## Permission Set Assignment Review

List all permission sets assigned to the guest user:

| Permission Set Name | Object Permissions Granted | Risk Level | Action Required |
|---|---|---|---|
| | | Low / Medium / High | |

---

## Secure Guest User Record Access Toggle

- [ ] Confirm "Secure Guest User Record Access" is ON (Setup > Sites > [Site] > Settings)

---

## Findings Summary

| Category | Issues Found | Priority |
|---|---|---|
| Object permissions | | |
| Field permissions | | |
| Guest sharing rule inventory | | |
| Apex class sharing | | |
| Permission sets | | |

**Overall Risk Rating:** [ ] Low [ ] Medium [ ] High [ ] Critical

---

## Remediation Plan

| Issue | Remediation Action | Owner | Target Date |
|---|---|---|---|
| | | | |
