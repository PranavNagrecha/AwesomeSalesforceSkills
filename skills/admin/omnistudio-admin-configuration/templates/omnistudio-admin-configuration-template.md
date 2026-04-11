# OmniStudio Admin Configuration — Work Template

Use this template when configuring OmniStudio at the org level or troubleshooting runtime, namespace, or permission issues.

## Scope

**Skill:** `omnistudio-admin-configuration`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Record answers to the Before Starting questions from SKILL.md before making any changes.

| Question | Answer |
|---|---|
| Current Standard OmniStudio Runtime toggle state | ENABLED / DISABLED / UNKNOWN |
| Current Runtime Namespace field value | `omnistudio` / `vlocity_ins` / `vlocity_cmt` / `vlocity_ps` / BLANK / UNKNOWN |
| OmniStudio license type | Industries included / Standalone OmniStudio SKU / Vlocity managed package |
| User populations needing access | Internal builders / Internal consumers / Experience Cloud community users |
| Has any component already been opened in Standard designer? | YES (migration underway) / NO (clean state) / UNKNOWN |

---

## OmniStudio Settings Configuration

Complete this section when configuring Setup > OmniStudio Settings.

| Setting | Required Value | Current Value | Action Needed |
|---|---|---|---|
| Standard OmniStudio Runtime | ENABLED (native orgs) | | |
| Runtime Namespace | `omnistudio` / `vlocity_ins` / `vlocity_cmt` / `vlocity_ps` | | |
| Disable Managed Package Runtime | ENABLED (after full migration) | | |

---

## Permission Provisioning Plan

List all user populations and their required assignments.

| User Group | OmniStudioPSL PSL | Permission Set | Community Consumer Permission |
|---|---|---|---|
| OmniStudio Builders (admin) | Required | OmniStudio Admin | Not required |
| OmniStudio Consumers (internal) | Required | OmniStudio User | Not required |
| Experience Cloud community users | Required | OmniStudio User | Required (custom PS) |
| Guest users (if applicable) | Required (check licensing) | OmniStudio User | Required (custom PS) |

**Notes on provisioning order:** PSL must be assigned before any permission set. Bulk provisioning scripts must sequence PSL assignment first.

---

## Post-Configuration Verification

Check each item after completing configuration changes.

- [ ] Setup > OmniStudio Settings shows correct Runtime Namespace value (not blank).
- [ ] Standard OmniStudio Runtime is in the expected toggle state.
- [ ] All target builder users have `OmniStudioPSL` PSL assigned.
- [ ] All target builder users have `OmniStudio Admin` permission set assigned.
- [ ] All target consumer users have `OmniStudioPSL` PSL assigned.
- [ ] All target consumer users have `OmniStudio User` permission set assigned.
- [ ] Community users (if applicable) have the community consumer custom permission set assigned.
- [ ] A test OmniScript activates without errors.
- [ ] A consumer test user can view and interact with the OmniScript.

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Greenfield Native Runtime Setup
- [ ] Community / Experience Cloud User Access
- [ ] Other: (describe)

Reason for pattern selection:

---

## Deviations and Notes

Record any deviations from the standard pattern and the justification.

| Deviation | Reason | Risk |
|---|---|---|
| | | |

---

## Deployment Runbook Entry

After completing configuration, record the final state here for the deployment runbook.

```
Environment: [Sandbox name / Production]
Date configured: 
Configured by: 

OmniStudio Settings:
  Runtime Namespace:              [value]
  Standard OmniStudio Runtime:    [ENABLED/DISABLED]
  Disable Managed Package Runtime:[ENABLED/DISABLED]

Permission set assignments verified: YES / NO
Post-activation test result: PASS / FAIL
Notes:
```
