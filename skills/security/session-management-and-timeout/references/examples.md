# Examples — Session Management And Timeout

## Example 1: Tiered Timeout for Compliance-Sensitive Admin Profiles

**Context:** A financial services company must comply with PCI-DSS, which requires that idle sessions for users with access to cardholder data time out within 15 minutes. However, their customer service representatives need 2-hour sessions to handle lengthy calls without re-authenticating mid-conversation.

**Problem:** Without tiered configuration, the org-wide timeout must be set to 15 minutes to satisfy compliance. This forces all 500 service reps to re-authenticate every 15 minutes, causing frustration and productivity loss. Setting it to 2 hours violates PCI-DSS for admin users.

**Solution:**

```xml
<!-- SecuritySettings metadata for org-wide baseline -->
<SecuritySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <sessionSettings>
        <sessionTimeout>TwoHours</sessionTimeout>
        <lockSessionsToIp>true</lockSessionsToIp>
        <forceLogoutOnSessionTimeout>true</forceLogoutOnSessionTimeout>
    </sessionSettings>
</SecuritySettings>
```

Then apply profile-level overrides:
1. Navigate to Setup > Profiles > System Administrator > Session Settings.
2. Set "Session times out after" to 15 minutes.
3. Repeat for any custom admin profile with access to payment objects.
4. Leave the Customer Service profile without a profile-level override so it inherits the 2-hour org-wide default.

**Why it works:** The org-wide value acts as a generous default for the majority of users. Profile-level overrides enforce shorter timeouts only where compliance requires it. Because the effective timeout is the minimum of all applicable levels, the 15-minute profile setting always wins for admin users regardless of the org-wide value. This satisfies PCI-DSS without impacting service reps.

---

## Example 2: Concurrent Session Limits to Prevent Credential Sharing

**Context:** A healthcare organization discovered during a security audit that several user accounts were being shared across shifts — multiple nurses used the same login at the same time from different workstations. This violates HIPAA audit trail requirements because actions cannot be attributed to a specific individual.

**Problem:** Without concurrent session limits, Salesforce allows unlimited simultaneous sessions per user. Shared credentials go undetected because multiple people can be logged in as the same user simultaneously.

**Solution:**

1. Navigate to Setup > Session Settings.
2. Enable "Limit the number of simultaneous sessions per user."
3. Set the limit to 3 sessions.
4. Communicate the change to users before enabling.

```text
Configuration:
  Concurrent session limit: 3
  Rationale: Allows one browser + one mobile + one API/CLI session
  Oldest-session behavior: When a 4th session starts, the oldest active session is terminated
```

**Why it works:** A limit of 3 accommodates legitimate multi-device use (desktop browser, mobile app, and CLI or API integration) while preventing credential sharing across multiple people. When a second person tries to log in with shared credentials, the first person's session terminates — making sharing immediately obvious. The terminated user sees a "Your session has ended" message, prompting them to report the issue or request their own credentials.

---

## Anti-Pattern: Setting Aggressive Org-Wide Timeout Without Profile Analysis

**What practitioners do:** An auditor flags a 4-hour session timeout as non-compliant. The admin changes the org-wide timeout to 15 minutes without checking for profile-level overrides or assessing user impact across the organization.

**What goes wrong:** All 2,000 users — including data-entry teams working on complex records, support agents on long calls, and report builders running large queries — start losing unsaved work every 15 minutes. Support tickets spike. Users begin saving constantly or refusing to use the platform for long-running tasks. Some circumvent the control by using browser auto-refresh extensions, which defeats the security purpose while creating unnecessary server load.

**Correct approach:** Identify which user populations need the short timeout (typically admins and privileged-access users). Apply profile-level overrides to those specific profiles. Keep the org-wide timeout at a reasonable value (2-4 hours) for the general population. Document the compliance mapping showing which control satisfies which requirement for each user segment.
