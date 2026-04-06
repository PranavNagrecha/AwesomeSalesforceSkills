---
name: session-management-and-timeout
description: "Use this skill when configuring session timeout values, concurrent session limits, session IP locking, or logout behavior in Salesforce. Covers org-wide session settings, profile-level overrides, Connected App session policies, and Metadata API SecuritySettings deployment. NOT for OAuth token refresh flows, login IP ranges, or MFA/identity-provider configuration."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "users are getting logged out too quickly and losing unsaved work in Lightning"
  - "how do I set different session timeout values for admins versus standard users"
  - "we need to limit concurrent sessions per user to prevent credential sharing"
  - "session timeout keeps reverting after deployment — how do I push it via metadata"
  - "how does session IP locking work and when should I enable it"
tags:
  - session-management-and-timeout
  - session-timeout
  - session-security
  - concurrent-sessions
  - connected-app
  - security-settings
inputs:
  - Current org-wide session timeout value and whether profile-level overrides exist
  - Whether Connected Apps with custom session policies are in use
  - Concurrent session limit requirements per user population
  - Whether session IP locking is enabled or required by compliance
outputs:
  - Session timeout configuration plan covering org, profile, and Connected App levels
  - Concurrent session limit recommendation with user-impact assessment
  - Metadata API SecuritySettings snippet for deployment
  - Review checklist for session hardening
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Session Management And Timeout

This skill activates when an org needs to configure, audit, or harden its session management settings. It covers timeout value selection at the org, profile, and Connected App levels; concurrent session limits; session IP locking; and deploying session configuration through the Metadata API. It does NOT cover OAuth token refresh mechanics, login IP range restrictions, or multi-factor authentication setup.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine the current org-wide session timeout value (Setup > Session Settings > Timeout Value). The default is 2 hours of inactivity. Know whether any compliance mandate requires a shorter timeout.
- Identify whether profile-level session timeout overrides are in place. Profile-level values override the org-wide setting only when they are more restrictive (shorter). The effective timeout is the minimum of all applicable levels.
- Check whether Connected Apps with OAuth Policies session timeout are deployed. These add a third layer of timeout control that compounds with org and profile settings.

---

## Core Concepts

Session management in Salesforce operates across three independent configuration layers. Understanding how they interact is essential to avoid unexpected logout behavior or overly permissive session lifetimes.

### Three-Tier Timeout Hierarchy

Salesforce evaluates session timeout at three levels: org-wide (Setup > Session Settings), profile-level (Profile > Session Settings), and Connected App-level (OAuth Policies). The effective timeout for any given user session is the **minimum** of all applicable levels. For example, if the org timeout is 4 hours, the user's profile timeout is 2 hours, and they authenticated through a Connected App with a 1-hour timeout, their session expires after 1 hour of inactivity. This minimum-wins behavior is the single most important concept — it means tightening any one level always takes effect, but loosening a single level may have no impact if a stricter layer remains.

### Concurrent Session Limits

Salesforce allows administrators to limit the number of simultaneous sessions a single user can hold, configurable from 1 to 20. The default is unlimited. When a user exceeds the limit, the oldest session is terminated. This is configured at Setup > Session Settings > Limit the number of simultaneous sessions per user. Enabling concurrent session limits is a common control to prevent credential sharing, but setting the value too low causes friction for users who legitimately use multiple browser tabs, Salesforce CLI, and mobile apps simultaneously — each of these counts as a separate session.

### Session IP Locking and Security Levels

When "Lock sessions to the IP address from which they originated" is enabled, any request from a different IP address than the one used at login triggers re-authentication. This is powerful for preventing session hijacking but causes problems for users on mobile networks, VPNs with rotating exit IPs, or split-tunnel corporate networks. Salesforce also supports session security levels (Standard vs High Assurance) that determine which features require a step-up authentication — this interacts with session management but is configured separately in Session Security Levels.

---

## Common Patterns

### Tiered Timeout by User Role

**When to use:** The org has compliance-sensitive admin users who should have shorter timeouts and business users who need longer sessions to complete complex data entry.

**How it works:**
1. Set the org-wide timeout to the longest acceptable value (e.g., 4 hours) as the baseline.
2. Create profile-level timeout overrides for admin and privileged-access profiles (e.g., 30 minutes or 1 hour).
3. Leave standard user profiles without an override so they inherit the org-wide value.
4. Document the effective timeout per profile in the session configuration plan.

**Why not the alternative:** Setting a short org-wide timeout to satisfy admin requirements punishes all users. Profile-level overrides let you differentiate without forcing the lowest common denominator on everyone.

### Connected App Session Isolation

**When to use:** A third-party integration authenticates via OAuth and should have session timeout behavior independent of the interactive user session.

**How it works:**
1. Configure the Connected App's OAuth Policies with a specific session timeout (e.g., 12 hours for a batch integration that runs overnight).
2. Set the Logout URL in the Connected App to a branded endpoint if users interact with it directly.
3. Understand that the Connected App timeout is subject to the minimum-wins rule: if the user's profile timeout is shorter, the profile timeout wins.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Compliance requires 15-minute timeout for admins | Profile-level override on System Administrator profile | Avoids penalizing all users with aggressive org-wide timeout |
| Users complain about frequent logouts | Check all three timeout layers; the shortest one wins | A restrictive Connected App or profile override may be the cause even if the org-wide value looks generous |
| Credential sharing is suspected | Enable concurrent session limit (3-5 sessions) | Blocks multi-user access on one credential while allowing legitimate multi-device use |
| Users on VPN with rotating IPs get logged out | Disable session IP locking or work with network team to stabilize egress IP | Session IP locking terminates sessions on IP change, which is incompatible with rotating-IP networks |
| Deploying session config across sandboxes | Use Metadata API SecuritySettings with sessionTimeout enum | Ensures consistency across environments without manual Setup clicks |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner configuring session management:

1. **Audit current state** — Navigate to Setup > Session Settings and record the org-wide timeout value, concurrent session limit, session IP locking status, and any other active session policies. Check each profile for profile-level timeout overrides (Profile > Session Settings). List all Connected Apps and their OAuth Policies timeout values.
2. **Define requirements** — Gather timeout requirements per user population. Map compliance mandates (PCI-DSS, HIPAA, SOC 2) to specific timeout values. Determine whether concurrent session limits or IP locking are required.
3. **Design the timeout hierarchy** — Set the org-wide timeout to the longest acceptable default. Apply profile-level overrides only where a shorter timeout is needed. Configure Connected App timeouts only for OAuth-authenticated integrations that need independent timeout behavior. Document the effective timeout per user persona.
4. **Deploy via Metadata API** — Write a SecuritySettings metadata component with the `sessionTimeout` enum value (e.g., `TwoHours`, `FourHours`). Deploy to sandbox first and verify the setting propagates correctly in Setup > Session Settings.
5. **Validate and test** — Log in as a user from each affected profile. Confirm the session expires at the expected time by checking the timeout behavior. Test concurrent session limits by opening sessions beyond the limit and verifying the oldest session terminates. If session IP locking is enabled, confirm it works correctly from a stable IP and verify the re-auth prompt triggers on IP change.
6. **Document and communicate** — Record the session configuration plan as an output artifact. Notify affected user populations of timeout changes to avoid surprise data loss from unsaved work.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Org-wide timeout value is set and documented
- [ ] Profile-level overrides are applied only where necessary, with effective timeout calculated per profile
- [ ] Connected App session policies are configured and documented for OAuth integrations
- [ ] Concurrent session limit is set to an appropriate value (or intentionally left unlimited with justification)
- [ ] Session IP locking decision is documented with rationale
- [ ] Metadata API SecuritySettings snippet is committed to version control for repeatable deployment
- [ ] Affected users are notified of timeout changes

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Minimum-wins is absolute across layers** — If a Connected App sets a 30-minute timeout, a user authenticating through that app gets 30 minutes regardless of the org-wide 4-hour setting. Practitioners who only check the org-wide value miss the real effective timeout.
2. **Lightning extends idle detection differently than Classic** — Lightning Experience uses client-side activity detection (mouse movement, keystrokes) to reset the idle timer. Salesforce Classic only resets on page navigation. Users who read long pages in Classic without clicking will timeout faster than expected.
3. **Concurrent session limit counts all session types** — API sessions, CLI sessions, mobile app sessions, and browser sessions all count toward the concurrent limit. Setting the limit to 2 may lock out a user who has a browser session and a Salesforce CLI session when they open the mobile app.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Session configuration plan | Document covering timeout values at org, profile, and Connected App levels with effective timeout per user persona |
| SecuritySettings metadata snippet | Deployable Metadata API component for session timeout and security settings |
| Concurrent session impact assessment | Analysis of how session limits affect different user populations including API and mobile users |

---

## Related Skills

- connected-app-security-policies — Use alongside this skill when configuring OAuth policies and session behavior for Connected Apps
- org-hardening-and-baseline-config — Covers broader org security baseline including session settings as one component of the hardening checklist
- login-forensics — Use to investigate session-related login anomalies and audit session termination events

---

## Official Sources Used

- Session Settings — https://help.salesforce.com/s/articleView?id=sf.admin_sessions.htm
- Metadata API SecuritySettings — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_securitysettings.htm
- Salesforce Well-Architected Security — https://architect.salesforce.com/well-architected/trusted/security
