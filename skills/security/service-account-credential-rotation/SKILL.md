---
name: service-account-credential-rotation
description: "Use when designing credential rotation for integration users, connected apps, named credentials, and OAuth client secrets in Salesforce. Covers rotation cadence, zero-downtime handover, secret storage, and detection of stale credentials. Triggers: 'rotate integration user. NOT for end-user password policies — use admin/connected-apps-and-auth."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "how often to rotate integration user password"
  - "rotate connected app client secret without downtime"
  - "rotate named credential oauth token"
  - "detect stale service account"
  - "salesforce credential rotation runbook"
tags:
  - security
  - credentials
  - rotation
  - service-account
  - named-credentials
inputs:
  - "inventory of service accounts and their consumers"
  - "current rotation cadence and secret storage locations"
  - "downtime tolerance per integration"
outputs:
  - "rotation cadence policy"
  - "zero-downtime rotation runbook"
  - "stale-credential detection plan"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Service Account Credential Rotation

Service account credentials are the forgotten middle layer of Salesforce security. Employees rotate passwords under MFA policy, connected apps rotate on explicit action, but "the integration user" often gets a password on day one of an integration and keeps it until a compliance audit forces a change years later. Similarly, connected app client secrets, JWT signing certs, and named credential OAuth tokens all have their own rotation story that no single team owns.

A workable rotation program has four parts: an inventory, a cadence, a zero-downtime pattern per credential type, and a stale-credential detector. Without the inventory, the other three are guesses.

Salesforce offers primitives for each credential type: integration user passwords (password policy `expiration`, api_meta 264 L129594-129601), connected app client secrets and certificates (`ConnectedAppOauthConfig`, L37419-37443), External Client App secret rotation on deploy (L67305-67311), and named-credential token refresh (L66295-66298). The patterns differ because the failure mode of a mid-rotation failure differs.

---

## Before Starting

- Inventory service accounts, connected apps, JWT certs, and named credentials.
- Identify consumer integrations for each — who breaks if this credential is rotated incorrectly?
- Confirm secret storage (vault, secret manager, SIEM) for each consumer.
- Confirm downtime tolerance per integration.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which profiles or permission sets give a service account the Password Never Expires permission? | It is a user permission, not a User field (secguide 262 L6398) — gotchas.md 1 | An inventory of exemptions, each with an owner and an end date |
| What password expiration does the org (and each profile) enforce? | Valid values run from Never to OneYear, default NinetyDays (api_meta 264 L129594-129601) — Rotation Cadence | A cadence the platform enforces rather than one written in a policy document |
| How many consumers share each connected app secret or certificate? | The connected app holds one `certificate` and a `consumerSecret` that can't be edited after save (api_meta 264 L37419-37443) — gotchas.md 2 and 3 | A cutover plan sized to the number of consumers |
| Is the app a connected app or an External Client App? | Only External Client Apps document `shouldRotateConsumerSecret` (api_meta 264 L67305-67311) — Credential Types table | The rotation mechanism that actually exists for this app type |
| What refresh-token policy and rotation setting does each app use? | `refreshTokenPolicy` defaults to infinite (api_meta 264 L37835-37836); `isRefreshTokenRotationEnabled` issues a new token per refresh (L37538-37552) — gotchas.md 4 | Token lifetime that matches the rotation policy |
| Where does each consumer read the credential from? | Hardcoded secrets turn every rotation into a code change — llm-anti-patterns.md Anti-Pattern 3 | A vault path per consumer |
| How is a retired app's access ended? | Removing an app in the UI and revoking its tokens are different steps — gotchas.md 5 | An explicit revoke step in the runbook |

A proper configuration adds an inventory, platform-enforced expiry and a tested cutover per credential; "just rotating the password" breaks every consumer that was not on the list.

---

## Core Concepts

### Credential Types And Their Rotation Mechanics

| Credential | Rotation Mechanic | Zero-Downtime? |
|---|---|---|
| Integration user password | Setup > User > Reset | No — simultaneous cutover |
| Connected App client secret | Setup > Connected Apps; `consumerSecret` can't be edited after save in metadata (api_meta 264 L37441-37443) | Unverified — see marker below |
| External Client App secret | `shouldRotateConsumerSecret` replaces the secret on metadata deploy (api_meta 264 L67305-67311) | No — the deploy replaces it |
| JWT signing certificate | Replace the single `certificate` on the app (api_meta 264 L37419; L67151-67155 for External Client Apps) | No — one certificate field, so coordinate the cutover |
| Named credential OAuth token | Salesforce refreshes expired or invalid access tokens on a 401 (api_meta 264 L66295-66298) | Yes, for access tokens |
| API user session ID | Re-login | Unverified — see marker below |

UNVERIFIED (2026-10-20): a previous-plus-current client-secret grace window in Setup, and session auto-refresh for API users, are Help-only claims with no corpus line. An earlier version of this table claimed a dual-certificate grace window; the metadata has one `certificate` field per app, so that row was corrected.

### Zero-Downtime Patterns

1. **Dual-credential grace window** — both old and new valid during a window; consumers roll forward.
2. **Atomic cutover with coordination** — used when grace windows are unavailable; requires a downtime slot.
3. **Auto-refresh** — OAuth handles token rotation automatically; only the refresh-token-grant path needs care.

### Rotation Cadence

Salesforce enforces password expiry through the password policy `expiration` (Never, ThirtyDays, SixtyDays, NinetyDays — the default — SixMonths, OneYear; api_meta 264 L129594-129601) and per-profile `passwordExpiration`, where 0 means never (L101392-101394).

Industry baselines (policy, not platform facts):
- Integration user passwords: 90 days (aggressive), 180 days (typical).
- Connected app client secrets: 180 days.
- JWT signing certs: annual, with 90-day advance notice.
- Named credential tokens: automatic via OAuth refresh; refresh-token lifetime follows the app's `refreshTokenPolicy`, default infinite (api_meta 264 L37835-37836).

Cadence is policy; enforcement is code.

### Stale-Credential Detection

Build a detector that lists:
- User records whose `PasswordExpirationDate` (API 63.0+, obj 264 L298549-298555) is empty or far out — or `LastPasswordChangeDate` beyond the threshold (UNVERIFIED (2026-10-20): that field is not in the 264 object reference).
- Connected apps with secret age > threshold.
- Certs approaching expiry.
- Named credentials that have not issued a callout in > 30 days (possibly unused; UNVERIFIED (2026-10-20): the corpus names no per-credential last-used field — source this from Event Monitoring or your own logging).

---

## Common Patterns

### Pattern 1: Dual-Credential Grace Window

New credential issued; consumers switch over during a configured window; old credential revoked at window close. The only safe pattern for integration user passwords if the consumer system supports it (most do not — most need a coordinated cutover).

### Pattern 2: JWT Bearer Certificate Cutover

The connected app stores one PEM `certificate` (api_meta 264 L37419). Replacing it and switching the consumer's signing key happen together, so schedule a coordinated cutover; for zero downtime, stand up a second connected app with the new certificate and move consumers across before retiring the old app.

### Pattern 3: Scheduled Rotation Job

An Apex Scheduled Job identifies credentials aging past policy and opens a rotation ticket (via a Case, a Flow, or an external ticketing webhook). Enforces cadence without relying on manual calendaring.

### Pattern 4: Named Credential With Per-User OAuth

Salesforce refreshes expired or invalid access tokens on a 401 response, plus any extra status codes listed as `AdditionalRefreshStatusCode` (api_meta 264 L66295-66298). The rotation "job" is user re-auth on a schedule.

### Pattern 5: Secret-Vault-First Storage

Consumer systems never store Salesforce credentials; they retrieve from a vault (HashiCorp, AWS Secrets Manager) on startup. Rotation updates the vault; consumers pick up on next read or reload.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Integration user password, consumer can handle cutover | Dual-credential window if supported, else coordinated cutover | Minimize downtime |
| Connected app secret, many consumers | Grace window if your org shows one (UNVERIFIED (2026-10-20)), else coordinated cutover | `consumerSecret` can't be edited after save in metadata (api_meta 264 L37441-37443) |
| JWT cert renewal | Coordinated cutover, or a second app with the new cert | One `certificate` per app (api_meta 264 L37419) |
| Named credential (OAuth) | Auto-refresh; schedule re-auth if refresh-token-grant lifecycle requires | Platform handles |
| Consumer stores credential in code | Move to vault before rotating | Eliminates hardcoded credentials |

## Review Checklist

- [ ] Inventory is current.
- [ ] Cadence is documented per credential type.
- [ ] Zero-downtime runbook exists per type.
- [ ] Stale-credential detector is scheduled.
- [ ] Vault or equivalent secret store used for every credential.
- [ ] Post-rotation verification step exists per integration.

## Recommended Workflow

1. Inventory all service accounts, connected apps, certs, and named credentials.
2. Classify each by consumer set and downtime tolerance.
3. Set cadence per type and write the runbook.
4. Implement the stale-credential detector as a Scheduled Job, and run `python3 scripts/check_service_account_credential_rotation.py --manifest-dir <force-app>` on every metadata change.
5. Run a pilot rotation with coordination and verification.
6. Monitor and alert on failed post-rotation health checks.

---

## Salesforce-Specific Gotchas

1. Integration user password expiry can be set to "Never" (`expiration` Never, api_meta 264 L129596; profile `passwordExpiration` 0, L101394) or bypassed with the Password Never Expires permission — a common anti-pattern.
2. Rotating a client secret without a coordinated cutover breaks every consumer still using the old one (UNVERIFIED (2026-10-20): the timing of invalidation is Help-only).
3. A connected app holds one `certificate` (api_meta 264 L37419), so a JWT certificate change is a cutover, not an overlap.
4. Named-credential refresh tokens may stop working after the user's password changes (UNVERIFIED (2026-10-20): Help-only); refresh-token lifetime itself follows `refreshTokenPolicy` (api_meta 264 L37818-37842).
5. Removing a connected app user session does not revoke active OAuth tokens (UNVERIFIED (2026-10-20): Help-only).

## Proactive Triggers

- Integration user whose profile or permission set grants the Password Never Expires permission (`<userPermissions><name>PasswordNeverExpires</name>`) → Flag Critical.
- Connected app secret last rotated > 365 days → Flag High.
- JWT cert expires < 90 days → Flag High.
- Named credential not invoked in 90 days → Flag Medium.
- Consumer storing credential in source code → Flag Critical.

## Output Artifacts

| Artifact | Description |
|---|---|
| Credential inventory | Per account/app/cert, consumer list, storage location |
| Rotation runbook | Type-by-type zero-downtime instructions |
| Stale-credential detector | Scheduled job definition |

## Related Skills

- `security/oauth-token-management` — token lifecycle.
- `security/api-only-user-hardening` — integration user baseline.
- `integration/named-credentials-setup` — named credential design.
- `devops/pipeline-secrets-management` — pipeline-side storage.
