# Gotchas — Connected App Security Policies

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: PKCE and Require Secret Are Mutually Exclusive

**What happens:** Enabling both "Require Proof Key for Code Exchange" and "Require Secret for Web Server Flow" on the same Connected App causes token exchange to fail with `invalid_client_credentials`. The platform does not warn at save time; the failure only surfaces at runtime when the OAuth client attempts the token exchange.

**When it occurs:** Anytime both checkboxes are saved simultaneously. This commonly happens when a developer enables PKCE to harden a public client but does not realize that the existing "Require Secret" setting must be cleared.

**How to avoid:** When enabling PKCE, explicitly uncheck "Require Secret for Web Server Flow" in the same edit. For confidential server-side clients that should use a secret, leave PKCE disabled and keep Require Secret enabled. Document the mutual exclusion in code review and Connected App deployment checklists.

---

## Gotcha 2: ECA Credential Rotation Promotes Instantly — Zero Grace Period

**What happens:** When using the External Client Apps (ECA) model (default from API v65 / Spring '25 onwards), rotating a consumer secret via the ECA Metadata API or the UI promotes the new secret immediately. The old secret stops working the instant rotation completes. Any active integrations still using the old secret receive `invalid_client` errors with no warning.

**When it occurs:** Any client secret rotation on an ECA-managed Connected App. This differs from some legacy tooling documentation and community guides that describe a brief overlap window — that window does not exist in the ECA model.

**How to avoid:** Treat ECA secret rotation as an atomic, coordinated deployment. Prepare all consumers with the new secret before triggering rotation. Use short-lived access tokens where possible so in-flight tokens expire quickly. Add the zero-grace-period caveat explicitly to all integration runbooks.

---

## Gotcha 3: JWT Bearer invalid_grant From Clock Drift Is Silent

**What happens:** Salesforce validates the assertion's `exp` claim against its own clock, allowing a documented **3-minute buffer for clock skew**. If the signing server's clock drifts far enough that `exp` falls outside that buffer, every token request fails with `invalid_grant`. The error response does not distinguish clock drift from other `invalid_grant` causes (expired refresh token, revoked credentials, wrong audience, etc.).

Note there is **no 60-second `iat` rule**. `iat` is not a required claim for the Salesforce JWT bearer flow at all — the required set is `iss`, `sub`, `aud`, `exp`. Chasing a sub-minute NTP threshold wastes the debugging session and can mask drift that is genuinely outside the 3-minute `exp` window.

**When it occurs:** On servers with poor NTP configuration, after VM migrations or snapshot restores that reset the system clock, or in containerized environments where the container clock drifts from the host.

**How to avoid:** Synchronize the signing host clock with NTP and monitor drift. Log the raw `exp` value you signed on every JWT assertion so clock-skew debugging is possible. Keep the assertion TTL short — roughly 3 minutes is conventional and matches the size of the skew buffer, so a drift failure shows up consistently rather than intermittently.

---

## Gotcha 4: High Assurance "Switch to High Assurance" Does Not Block Access

**What happens:** The "Switch to High Assurance" state prompts the user to step up their session security level but does not prevent access if they decline or if the step-up cannot be completed. Practitioners who set this state believing it enforces MFA find that low-assurance sessions still access the Connected App.

**When it occurs:** Whenever "Switch to High Assurance" is used as a permanent enforcement posture rather than as a transitional migration state.

**How to avoid:** Use "Switch to High Assurance" only during a time-bounded migration window. Once all users and integrations can satisfy High Assurance, change the setting to **Blocked** to deny all low-assurance access. Set a calendar reminder or Salesforce flow automation to check and upgrade this setting after the migration deadline.

---

## Gotcha 5: IP Relaxation on the Connected App Overrides Profile IP Ranges

**What happens:** Setting `ipRelaxation` to `relaxIpRanges` on a Connected App disables IP checks for token requests made through that app, even if the authenticating user's profile has Login IP Ranges defined. Many administrators assume profile IP ranges are always enforced regardless of Connected App settings; this assumption is wrong.

**When it occurs:** Whenever a Connected App has relaxed IP restrictions and the authenticating user has restrictive profile IP ranges. The profile ranges are bypassed for the OAuth token grant.

**How to avoid:** Audit Connected App IP relaxation settings independently from profile IP range audits. A security review that checks only profile IP ranges will miss Connected App overrides. Include Connected App IP relaxation in org security health checks and periodic reviews.

---

## Gotcha 6: Device Flow Is Blocked and Cannot Be Re-Enabled on a Custom Connected App

**What happens:** Salesforce enforced the removal on a calendar date rather than a release boundary — *"Starting August 28, 2025, new and existing authorizations to any org using the OAuth 2.0 Device Flow with the default Salesforce CLI connected app will be blocked."* Note **existing** authorizations, not just new ones: a CI job that had been running for a year stops working on that date with no config change on your side.

The obvious remediation is closed by name in the same article: *"You cannot work around this restriction by re-enabling the Device Flow in a custom connected app, because the **Enable for Device Flow** option in the **API (Enable OAuth Settings)** section has been permanently disabled by Salesforce."* So standing up your own Connected App to carry the flow is not a migration plan — the only plan is moving off Device Flow.

**When it occurs:** Any headless authorization built on `sf org login device` — build agents, containers, jump boxes, kiosk-style tooling — and any runbook that tells an engineer to authorize by reading a code off a terminal. Also hits anyone who inherits such a runbook and tries to reproduce it in a new org.

**How to avoid:** Migrate headless authorization to the JWT Bearer flow (`sf org login jwt`) with a dedicated integration user and a certificate you rotate on a schedule; use the Web Server flow (`sf org login web`) wherever a browser is genuinely available. Grep runbooks, Dockerfiles and CI configs for `login device` / `auth:device:login` before an audit rather than after an outage. Related restriction from the same change: an org admin must install the Salesforce CLI connected app themselves — standard users no longer can.
