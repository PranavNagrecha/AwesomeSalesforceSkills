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

## OWD Alignment

| Object | Current OWD | Guest Access Required | Action Required |
|---|---|---|---|
| | | Yes / No | |

**Rule:** Guests can only see records where OWD is Public Read Only or Public Read/Write. Private OWD = zero guest access.

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
| OWD alignment | | |
| Apex class sharing | | |
| Permission sets | | |

**Overall Risk Rating:** [ ] Low [ ] Medium [ ] High [ ] Critical

---

## Remediation Plan

| Issue | Remediation Action | Owner | Target Date |
|---|---|---|---|
| | | | |
