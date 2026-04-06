# IP Range and Login Flow Strategy — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `ip-range-and-login-flow-strategy`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Target users:** Internal (profile assignment) or External/Experience Cloud (site assignment)?
- **Profiles or sites affected:**
- **Current MFA enforcement:** Is native Salesforce MFA enabled? What method (Authenticator app, SMS, email)?
- **Existing Login Flow assignments:** Check Setup > Login Flows for current assignments on target profiles.
- **IP detection requirement:** Does the flow need IP-based branching? If so, is an Apex Invocable already deployed?
- **Known constraints:** Login Flow User permission limitations, latency budget, component restrictions in login context.

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Pattern 1: IP-Aware Conditional Verification Flow
- [ ] Pattern 2: Experience Cloud Custom Login Page with Data Collection
- [ ] Pattern 3: Periodic Re-Verification on Schedule
- [ ] Custom combination (describe below)

**Justification:**

## Implementation Plan

1. **Apex Invocable(s) needed:**
   - IP detection: Yes / No
   - Record update: Yes / No
   - Other:

2. **Custom Metadata / Custom Settings:**
   - Corporate IP ranges: `Corporate_IP_Range__mdt` — Yes / No
   - Terms version config: `Terms_Config__mdt` — Yes / No
   - Other:

3. **Flow design:**
   - Number of screens on happy path:
   - Number of screens on exception path:
   - Decision elements:
   - Fault handling strategy:

4. **Assignment:**
   - Profile-level: (list profiles)
   - Site-level: (list sites)

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Login Flow is a Screen Flow (not Autolaunched or Record-Triggered)
- [ ] Flow uses `$Flow.LoginFlow_UserId` or `$Flow.LoginFlow_LoginType` where applicable
- [ ] IP detection uses Apex Invocable with `Auth.SessionManagement`, not formula-only
- [ ] Corporate IP ranges stored in Custom Metadata, not hardcoded
- [ ] Tested from both trusted and untrusted IP addresses
- [ ] Assignment confirmed: one flow per profile; site-level overrides profile-level
- [ ] Flow handles browser-close gracefully
- [ ] No DML requiring full session context (Login Flow User limitations addressed)
- [ ] Login latency impact assessed — happy path has minimal screens
- [ ] Existing MFA enforcement not weakened or bypassed

## Notes

Record any deviations from the standard pattern and why.
