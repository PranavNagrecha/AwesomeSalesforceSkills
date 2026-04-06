# LLM Anti-Patterns — Session Management And Timeout

Common mistakes AI coding assistants make when generating or advising on Session Management And Timeout.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Numeric Minutes in Metadata API sessionTimeout

**What the LLM generates:** A SecuritySettings metadata snippet with a numeric timeout value like `<sessionTimeout>120</sessionTimeout>` or `<sessionTimeout>30m</sessionTimeout>`.

**Why it happens:** LLMs generalize from other platforms and configuration systems where timeout values are specified as integers in minutes or seconds. The Salesforce Metadata API uses a specific enum for this field, which is unusual.

**Correct pattern:**

```xml
<SecuritySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <sessionSettings>
        <sessionTimeout>TwoHours</sessionTimeout>
    </sessionSettings>
</SecuritySettings>
```

Valid enum values: FifteenMinutes, ThirtyMinutes, SixtyMinutes, TwoHours, FourHours, EightHours, TwelveHours, TwentyFourHours.

**Detection hint:** Look for any numeric value or unit suffix (m, min, s, sec, hours) inside a `<sessionTimeout>` element.

---

## Anti-Pattern 2: Claiming Profile-Level Timeout Can Extend the Org-Wide Value

**What the LLM generates:** Advice like "Set the org-wide timeout to 30 minutes and then extend it to 4 hours for the Sales profile" or "Override the org timeout at the profile level to give users more time."

**Why it happens:** LLMs assume profile-level settings are true overrides that can go in either direction (more restrictive or more permissive). In reality, the effective timeout is always the minimum of all applicable levels. A profile-level timeout can only shorten, never lengthen, the org-wide value.

**Correct pattern:**

```text
Org-wide timeout: 4 hours (longest acceptable default)
Admin profile override: 15 minutes (shorter = takes effect)
Sales profile: no override (inherits 4-hour org-wide value)

Effective: Admin = 15 min, Sales = 4 hours
```

**Detection hint:** Look for phrases like "extend," "increase," "override to a longer," or "set profile timeout higher than org" in session timeout advice.

---

## Anti-Pattern 3: Ignoring Connected App as a Third Timeout Layer

**What the LLM generates:** Session timeout advice that only discusses org-wide and profile-level settings, omitting Connected App session policies entirely. For example: "The effective timeout is the shorter of the org-wide and profile-level values."

**Why it happens:** Most LLM training data covers the two most commonly discussed layers. Connected App session timeout is a less frequently documented third layer that also participates in the minimum-wins calculation.

**Correct pattern:**

```text
Effective timeout = MIN(org-wide timeout, profile-level timeout, Connected App timeout)

All three layers must be checked when diagnosing unexpected timeout behavior.
If the user authenticates through a Connected App, its session timeout is also in play.
```

**Detection hint:** Look for session timeout explanations that reference only two levels (org and profile) without mentioning Connected App OAuth Policies.

---

## Anti-Pattern 4: Recommending Unlimited Concurrent Sessions as Safe Default

**What the LLM generates:** "The default concurrent session setting (unlimited) is fine for most organizations" or failing to mention concurrent session limits as a security control at all.

**Why it happens:** LLMs default to "least disruption" advice and avoid recommending changes that might cause user friction. Unlimited concurrent sessions is the Salesforce default, so LLMs treat it as acceptable without analyzing the security implications.

**Correct pattern:**

```text
Concurrent session limits should be explicitly evaluated during any session
hardening exercise. For most orgs:
- 3-5 sessions: appropriate for interactive users (browser + mobile + CLI)
- Unlimited: only appropriate when integration users are separated from
  interactive users and credential sharing is controlled by other means

Always account for API, CLI, and mobile sessions in the count — they are
not exempt from the limit.
```

**Detection hint:** Look for session management advice that does not mention concurrent session limits at all, or that dismisses unlimited sessions without analysis.

---

## Anti-Pattern 5: Conflating Session Timeout with OAuth Token Expiration

**What the LLM generates:** Advice that mixes session timeout configuration with OAuth access token lifetime or refresh token policies. For example: "Set the session timeout to 2 hours and the refresh token to 24 hours" as if they are configured in the same place.

**Why it happens:** LLMs conflate two related but distinct concepts. Session timeout controls how long an interactive session remains valid without activity. OAuth token lifetime is configured in Connected App settings and governs API authentication token validity. They are configured in different places and serve different purposes.

**Correct pattern:**

```text
Session timeout (Setup > Session Settings or Profile > Session Settings):
  Controls interactive session idle expiration.
  Configured as org-wide or profile-level setting.

OAuth token lifetime (Connected App > OAuth Policies):
  Controls access token and refresh token validity.
  Configured per Connected App.

These are separate controls. Changing one does not affect the other.
```

**Detection hint:** Look for advice that places session timeout and OAuth token configuration in the same settings path, or that claims changing session timeout affects API token behavior.

---

## Anti-Pattern 6: Recommending Session IP Locking Without Network Analysis

**What the LLM generates:** "Enable 'Lock sessions to the IP address from which they originated' for maximum security" as a blanket recommendation without caveats.

**Why it happens:** LLMs favor recommending the most restrictive security option when asked about hardening. Session IP locking sounds like a clear security win, and LLMs do not consider the network topology of the user population.

**Correct pattern:**

```text
Before enabling session IP locking, verify:
1. Users are on stable egress IPs (corporate network with fixed NAT)
2. VPN users have consistent exit IPs (not rotating or split-tunnel)
3. Mobile users are not on carrier networks with changing IPs
4. No users connect through load balancers that change source IP mid-session

If any of these conditions are not met, session IP locking will cause
legitimate users to be forced to re-authenticate unpredictably.
```

**Detection hint:** Look for session IP locking recommendations that do not include network topology caveats or mention VPN, mobile, or rotating IP scenarios.
