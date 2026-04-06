# Salesforce Release Preparation — Work Template

Use this template when running a full release preparation cycle for an upcoming Salesforce seasonal release.

---

## Scope

**Skill:** `salesforce-release-preparation`

**Release:** (e.g. Summer '25, Winter '26)

**Request summary:** (fill in what was asked — full prep cycle, Release Updates audit only, sandbox preview enrollment, etc.)

---

## Context Gathered

Record the answers to the Before Starting questions before proceeding.

- **Org instance and production upgrade date:** (look up on trust.salesforce.com)
- **Sandbox Preview enrollment window closes:**
- **Active feature areas in use:** (Sales Cloud, Service Cloud, Experience Cloud, Flow, Apex, LWC, OmniStudio, etc.)
- **Active Release Updates pending enforcement:**
- **Sandboxes available for preview testing:**
- **Stakeholder communication owner:**

---

## Release Notes Triage List

Filtered using Feature Impact (Admin / Developer / End User / Requires Setup) and active feature areas.

| # | Release Notes Item | Feature Impact | Feature Area | Action Required? | Owner | Target Test Date | Status |
|---|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  | Open |
| 2 |  |  |  |  |  |  | Open |
| 3 |  |  |  |  |  |  | Open |

*Add rows as needed. Remove items classified as Informational (no action required).*

---

## Release Updates Action Plan

From Setup > Release Updates. Review each non-Enforced update.

| Release Update Name | Enforcement Date | Current Status | Sandbox Tested? | Issues Found | Production Activation Date | Owner |
|---|---|---|---|---|---|---|
|  |  | Opt-In / Auto-Activation Scheduled |  |  |  |  |
|  |  | Opt-In / Auto-Activation Scheduled |  |  |  |  |

---

## Sandbox Preview Enrollment

| Sandbox Name | Sandbox Type | Enrolled? | Reason | Preview Upgrade Date | Post-Upgrade Test Plan |
|---|---|---|---|---|---|
|  |  | Yes / No |  |  |  |

*Reference: Salesforce Knowledge Article 000391927 for enrollment steps and eligibility.*

---

## Test Results Summary

For each Release Update or behavior change tested in sandbox:

| Item | Sandbox | Test Date | Result | Issues Found | Fix Status |
|---|---|---|---|---|---|
|  |  |  | Pass / Fail |  | Fixed / Open / Not Required |

---

## Stakeholder Communication Brief

**Audience:** (end users, managers, IT team, integration owners)

**Production upgrade date:**

**Summary of end-user-visible changes:**

| Change | Who Is Affected | What They Will See | Any Action Required By User |
|---|---|---|---|
|  |  |  |  |

**Admin actions required before upgrade:**
-
-

**Communication send-by date:** (at least one week before production upgrade)

**Communication owner:**

---

## Release Readiness Checklist

- [ ] Production upgrade date confirmed from trust.salesforce.com for org's specific instance
- [ ] Release notes triaged using Feature Impact filter for Admin, Developer, and End User items
- [ ] All Release Updates reviewed; enforcement dates logged
- [ ] Each Release Update activated and tested in sandbox; no unresolved Apex test failures
- [ ] At least one sandbox enrolled in Sandbox Preview (or documented reason for skipping)
- [ ] Stakeholder communication brief drafted and approved by release sponsor
- [ ] Stakeholder communication sent at least one week before production upgrade
- [ ] Production activation of Release Updates scheduled before auto-activation deadline
- [ ] Post-upgrade monitoring plan confirmed for 48 hours after production upgrade

---

## Notes and Deviations

Record any deviations from the standard workflow and the reason.

-
-

---

## Sign-Off

| Role | Name | Date | Signature |
|---|---|---|---|
| Release Sponsor |  |  |  |
| Lead Admin |  |  |  |
| Developer (if applicable) |  |  |  |
