# Gotchas — Session Management And Timeout

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Profile-Level Timeout Only Works When Shorter Than Org-Wide

**What happens:** A practitioner sets the org-wide timeout to 30 minutes and then sets a profile-level timeout to 4 hours for a specific group of users who need longer sessions. The profile-level value is silently ignored — those users still timeout after 30 minutes.

**When it occurs:** Whenever a profile-level timeout is configured to be longer (more permissive) than the org-wide setting. The effective timeout is always the minimum of all applicable levels. Profile-level overrides can only restrict, never extend, the org-wide timeout.

**How to avoid:** Set the org-wide timeout to the longest acceptable value for the org. Use profile-level overrides only to shorten the timeout for specific populations. If different user groups need different timeout lengths, the org-wide value must be at least as long as the longest required timeout.

---

## Gotcha 2: Lightning Client-Side Idle Detection Masks True Server Timeout

**What happens:** In Lightning Experience, the client-side JavaScript detects mouse movements, keystrokes, and scrolling as "activity" and sends periodic keep-alive pings to the server. A user who is reading a long page and occasionally scrolling may never see a timeout prompt, even if the org-wide timeout is set to 15 minutes. However, if their browser tab is backgrounded or their laptop goes to sleep, the keep-alive stops and the server-side timeout clock runs uninterrupted.

**When it occurs:** In Lightning Experience only. Salesforce Classic does not have client-side idle detection and only resets the timeout on full page loads (navigation clicks). This means the same user with the same timeout setting will experience different timeout behavior depending on whether they are in Lightning or Classic.

**How to avoid:** Test timeout behavior in the actual experience your users use (Lightning vs. Classic). Do not assume that a timeout value tested in Classic will produce the same user experience in Lightning. When documenting timeout behavior for compliance auditors, clarify that Lightning idle detection extends the apparent idle time.

---

## Gotcha 3: Concurrent Session Limit Counts API and CLI Sessions

**What happens:** A user with a concurrent session limit of 3 has a browser session, a Salesforce CLI session (for development), and a mobile app session. When an automated integration makes an API call using their credentials (e.g., a named credential tied to their user, or a CI/CD pipeline using their security token), the oldest session terminates without warning.

**When it occurs:** Any time the total number of active sessions (browser, mobile, API, CLI, all session types) exceeds the configured limit. API sessions and CLI sessions are not exempt from the limit.

**How to avoid:** When setting concurrent session limits, account for all session types the user population uses. Dedicated integration users (with their own licenses) should handle API traffic instead of piggybacking on interactive user credentials. Set the limit high enough to accommodate legitimate multi-device use — a value of 5 is generally safe for users who use browser, mobile, CLI, and occasional API access.

---

## Gotcha 4: Metadata API sessionTimeout Uses Enum Values, Not Minutes

**What happens:** A practitioner tries to deploy a SecuritySettings metadata component with `<sessionTimeout>30</sessionTimeout>` (expecting 30 minutes). The deployment fails or is silently ignored because the Metadata API expects an enum value like `ThirtyMinutes`, `TwoHours`, `FourHours`, etc. — not a numeric value in minutes.

**When it occurs:** When deploying session timeout configuration via the Metadata API (SecuritySettings type) or CI/CD pipelines. The valid enum values are: FifteenMinutes, ThirtyMinutes, SixtyMinutes, TwoHours, FourHours, EightHours, TwelveHours, TwentyFourHours.

**How to avoid:** Always reference the Metadata API Developer Guide for SecuritySettings to confirm the correct enum values. Use the enum name exactly as documented (PascalCase, no spaces). Validate the metadata component in a sandbox before deploying to production.

---

## Gotcha 5: Force Logout on Timeout Requires Explicit Enablement

**What happens:** A practitioner configures a 15-minute session timeout assuming the user will be fully logged out when it expires. Instead, the user sees a "Your session has expired" modal but can click "OK" and remain on the page with a stale session. In some cases the UI appears functional but API calls fail silently.

**When it occurs:** When the "Force logout on session timeout" setting is not explicitly enabled in Setup > Session Settings. By default, Salesforce shows a timeout notification but does not always force a full redirect to the login page.

**How to avoid:** Always enable "Force logout on session timeout" when session timeout is a compliance control. Verify by testing: after the timeout period, confirm the user is redirected to the login page (or a configured Logout URL) rather than shown a dismissable modal.
