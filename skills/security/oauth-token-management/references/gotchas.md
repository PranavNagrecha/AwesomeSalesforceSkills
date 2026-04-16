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
