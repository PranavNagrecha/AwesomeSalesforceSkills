# OmniScript Versioning — Activation Checklist Template

Use this template for every OmniScript version activation in production.

## OmniScript Identity

**Type:** ________________________________
**SubType:** ________________________________
**Language:** ________________________________
**Current Active Version:** ________________________________
**Target Version to Activate:** ________________________________

---

## Pre-Activation Checklist

- [ ] New version tested in UAT/Staging sandbox with matching configuration
- [ ] UAT sign-off obtained from product owner or BA
- [ ] No open Sev-1 defects against the new version
- [ ] DataPack backup of the current active version exported and stored:
  - Backup location: ________________________________
  - Backup date/time: ________________________________
- [ ] Activation window scheduled during low-traffic period
- [ ] Support team notified of activation window

---

## Activation Steps

1. Log in to the target org.
2. Navigate to: OmniStudio > OmniScripts
3. Filter by Type: `____________` and SubType: `____________`
4. Locate Version `____________` — confirm Status = Inactive
5. Click row menu > **Activate** on version `____________`
6. Confirm: version `____________` now shows **Active**
7. Confirm: version `____________` now shows **Inactive**
8. Proceed to post-activation smoke test (see below)

---

## Post-Activation Smoke Test

Open the OmniScript in an incognito browser (to simulate fresh session):

| Test Step | Expected Result | Actual Result | Pass/Fail |
|---|---|---|---|
| OmniScript loads correctly | No error, correct first step displayed | | |
| Step navigation works | Forward and back navigation functional | | |
| Data sources load | Remote Actions / Integration Procedures return data | | |
| Submission completes | Final step submits without error | | |

**Overall Result:** [ ] PASS — activation complete [ ] FAIL — initiate rollback

---

## Rollback Procedure (if needed)

1. Navigate to: OmniStudio > OmniScripts
2. Filter by Type: `____________` and SubType: `____________`
3. Locate Version `____________` (previously active) — Status = Inactive
4. Click **Activate** on version `____________`
5. Confirm: version `____________` now shows **Active**
6. Verify site functionality restored
7. Document rollback and open defect ticket for the failed version

---

## Activation Record

| Field | Value |
|---|---|
| Activated by | |
| Activation date/time | |
| Old version | |
| New version | |
| Smoke test result | Pass / Fail / Rollback |
| Notes | |
