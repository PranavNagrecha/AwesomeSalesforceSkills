# Gotchas — OAuth Token Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Access token TTL is not “always two hours”

**What happens:** Engineers hard-code a 110-minute refresh cadence based on an old default, but the org enforces a shorter Connected App or org session timeout. Tokens expire earlier and refresh attempts fail if the refresh token was not obtained or was revoked.

**When it occurs:** Mixed environments where production org Session Settings differ from sandbox, or after security teams tighten timeouts without notifying integration owners.

**How to avoid:** Read the effective session timeout pairing from official Connected App and Session Settings documentation for the org’s edition; base refresh scheduling on measured `expires_in` (and clock skew margin), not folklore.

---

## Gotcha 2: Revoke “access token” vs “refresh token” has different blast radius

**What happens:** During incident response, operators revoke what they think is “the bad token,” but parallel integration workers keep running because they hold independent access tokens tied to the same surviving refresh credential.

**When it occurs:** Multi-worker integrations, overlapping sessions for the same integration user, or human admins using UI revocation without matching it to OAuth token types.

**How to avoid:** Name the revocation target explicitly in the runbook (access vs refresh vs reset grant); verify post-action by attempting refresh and a sample API call from a known client profile.

---

## Gotcha 3: Immediate refresh token expiry (`zero`) breaks unattended jobs

**What happens:** A Connected App metadata sets `<refreshTokenPolicy>zero</refreshTokenPolicy>` under `<oauthPolicy>` while still advertising `RefreshToken` scope. Interactive demos work (user is present to log in again) but nightly sync jobs fail on the first access token expiry.

**When it occurs:** Copy-paste from restrictive mobile templates into server integrations, or security mandates “expire refresh immediately” without changing the grant model.

**How to avoid:** Match refresh policy to the integration’s ability to re-authenticate; for unattended processes, prefer flows and policies that do not require an interactive user at each access token boundary, or accept explicit scheduled re-auth with monitoring.

---

## Gotcha 4: Refresh token policy metadata may not reflect UI-only experiments

**What happens:** Developers tweak OAuth policies in a scratch org UI but never retrieve Connected App metadata; local checks pass while the org behaves differently.

**When it occurs:** Teams that manage Connected Apps only through Setup in some environments and metadata in others.

**How to avoid:** Treat retrieved `connectedApps/*.connectedApp` metadata as the reconciliation source for CI checks; retrieve after policy changes.

---

## Gotcha 5: Salesforce revokes refresh tokens itself for anonymizing-VPN egress — no admin action involved

**What happens:** A user or integration is frozen and every OAuth refresh token granted to that user is revoked, with no matching change in Setup, no policy edit, and nothing in the org's own IP settings. Salesforce contained the account on its own: the documented actions are that the account "will be frozen", "All OAuth refresh tokens granted to the user will be revoked", and an email goes to org admins from Salesforce Security. This is not a Login IP Range, Trusted IP Range, or login-hours failure, and the affected user must contact an admin to restore access.

**When it occurs:** Traffic egressing from anonymizing VPNs, proxies, or high-risk IP addresses. Salesforce began enhanced measures on November 20, 2025 and expanded them to **all Connected App and API traffic** beginning April 24, 2026 — which is what pulls headless integrations and middleware into scope, not just interactive browser logins. Attribute this by date: the source page names no release.

**How to avoid:** Pin integration egress to stable, attributable addresses (fixed NAT or a named egress gateway) rather than a commercial VPN or proxy pool, and confirm what your middleware host actually egresses from — cloud-hosted workers are the common surprise. There is **no documented opt-out or allowlist**, so an admin who only unfreezes the user has not fixed it: "Containment actions apply as soon as misuse is detected", and users "must ensure they are no longer connecting from an anonymizing VPN, proxies, or high-risk IP address before reauthorizing" or they are contained again. The documented restore path is to review the session in Session Management, unfreeze the account, have the user reauthenticate and reset their password, then reauthorize the connected apps — budget for a full re-authorization, because the refresh tokens are already gone.

---

## Gotcha 6: Partner apps lose the right to turn OAuth hardening back off

**What happens:** A team enables PKCE or Refresh Token Rotation on an ISV Connected App or External Client App, a client breaks, and they go to switch it off — but the toggle is one-way. Salesforce states "After PKCE is enabled, partners won't be permitted to disable" and "After RTR is enabled, Partners won't be permitted to disable."

**When it occurs:** Partner-distributed Connected Apps and External Client Apps only. This is an ISV/AgentExchange obligation with a compliance deadline of **May 11, 2026** for all four required controls — PKCE, Refresh Token Rotation, "Limit Idle Refresh Token Time-to-Live (TTL) to 30 Days", and "Enforce Refresh Token IP Allowlist". It is not a blanket org-level change, so do not tell a customer their internal Connected App inherited it.

**How to avoid:** Rehearse each control in a scratch or partner test org **before** enabling it in the distributed app. PKCE and RTR are irreversible on their own, and the other two lock as well once you self-attest: after the Review Controls attestation "the security controls are locked and can't be disabled" — only the IP ranges stay editable. Two constraints bite late: the idle-TTL control means Salesforce "invalidates the idle refresh token after 30 days", which kills the store-one-refresh-token-forever design for any consumer that syncs less often than monthly; and the IP allowlist caps at "A total of 256 IP addresses ... across all IP ranges" and should be enabled "only if your CA/ECA uses a callback URL that is not a: Localhost, Salesforce org, Custom URL scheme". Non-compliance risks "the Partner Application's AgentExchange de-listing and/or Salesforce's temporary or permanent suspension of the Partner Application's interoperation with Salesforce's services."
