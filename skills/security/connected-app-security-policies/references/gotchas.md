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

**What happens:** The JWT Bearer flow requires the signed assertion's `iat` (issued-at) timestamp to be within 60 seconds of Salesforce's server time. If the signing server's clock drifts beyond this window, every token request fails with `invalid_grant`. The error response does not distinguish clock drift from other `invalid_grant` causes (expired refresh token, revoked credentials, wrong audience, etc.).

**When it occurs:** On servers with poor NTP configuration, after VM migrations or snapshot restores that reset the system clock, or in containerized environments where the container clock drifts from the host.

**How to avoid:** Synchronize the signing host clock with NTP and monitor drift. Log the raw `iat` value on every JWT assertion so clock-skew debugging is possible. Keep JWT TTL short (≤ 3 minutes as required by Salesforce) — a shorter TTL makes drift failures more consistent and therefore easier to isolate.

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
