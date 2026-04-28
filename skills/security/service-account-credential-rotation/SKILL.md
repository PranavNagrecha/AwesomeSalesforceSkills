---
name: service-account-credential-rotation
description: "Use when designing credential rotation for integration users, connected apps, named credentials, and OAuth client secrets in Salesforce. Covers rotation cadence, zero-downtime handover, secret storage, and detection of stale credentials. Triggers: 'rotate integration user password', 'connected app secret rotation', 'named credential rotation', 'stale service account', 'zero downtime secret rotation'. NOT for end-user password policies."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Service Account Credential Rotation

Service account credentials are the forgotten middle layer of Salesforce security. Employees rotate passwords under MFA policy, connected apps rotate on explicit action, but "the integration user" often gets a password on day one of an integration and keeps it until a compliance audit forces a change years later. Similarly, connected app client secrets, JWT signing certs, and named credential OAuth tokens all have their own rotation story that no single team owns.

A workable rotation program has four parts: an inventory, a cadence, a zero-downtime pattern per credential type, and a stale-credential detector. Without the inventory, the other three are guesses.

Salesforce offers primitives for each credential type: integration user passwords (standard user policy), connected app client secrets (rotate via setup), JWT (replace cert), named credentials (refresh via setup or via a schedule). The patterns differ because the failure mode of a mid-rotation failure differs.

---

## Before Starting

- Inventory service accounts, connected apps, JWT certs, and named credentials.
- Identify consumer integrations for each — who breaks if this credential is rotated incorrectly?
- Confirm secret storage (vault, secret manager, SIEM) for each consumer.
- Confirm downtime tolerance per integration.

## Core Concepts

### Credential Types And Their Rotation Mechanics

| Credential | Rotation Mechanic | Zero-Downtime? |
|---|---|---|
| Integration user password | Setup > User > Reset | No — simultaneous cutover |
| Connected App client secret | Setup > Connected Apps > rotate | Yes — previous+current grace window supported |
| JWT signing certificate | Replace cert on connected app | Yes — dual-cert grace window |
| Named credential OAuth token | Re-auth flow or manual refresh | Yes — token refresh handles it |
| API user session ID | Re-login | Yes — sessions auto-refresh |

### Zero-Downtime Patterns

1. **Dual-credential grace window** — both old and new valid during a window; consumers roll forward.
2. **Atomic cutover with coordination** — used when grace windows are unavailable; requires a downtime slot.
3. **Auto-refresh** — OAuth handles token rotation automatically; only the refresh-token-grant path needs care.

### Rotation Cadence

Industry baselines:
- Integration user passwords: 90 days (aggressive), 180 days (typical).
- Connected app client secrets: 180 days.
- JWT signing certs: annual, with 90-day advance notice.
- Named credential tokens: automatic via OAuth refresh.

Cadence is policy; enforcement is code.

### Stale-Credential Detection

Build a detector that lists:
- User records with `LastPasswordChangeDate` > policy threshold.
- Connected apps with secret age > threshold.
- Certs approaching expiry.
- Named credentials that have not issued a callout in > 30 days (possibly unused).

---

## Common Patterns

### Pattern 1: Dual-Credential Grace Window

New credential issued; consumers switch over during a configured window; old credential revoked at window close. The only safe pattern for integration user passwords if the consumer system supports it (most do not — most need a coordinated cutover).

### Pattern 2: JWT Bearer With Dual Cert

Connected app supports two signing certs. Add the new cert, consumers switch signing key, old cert removed. Zero downtime.

### Pattern 3: Scheduled Rotation Job

An Apex Scheduled Job identifies credentials aging past policy and opens a rotation ticket (via a Case, a Flow, or an external ticketing webhook). Enforces cadence without relying on manual calendaring.

### Pattern 4: Named Credential With Per-User OAuth

Per-user OAuth names credential refresh is handled by the platform on 401 responses. The rotation "job" is user re-auth on a schedule.

### Pattern 5: Secret-Vault-First Storage

Consumer systems never store Salesforce credentials; they retrieve from a vault (HashiCorp, AWS Secrets Manager) on startup. Rotation updates the vault; consumers pick up on next read or reload.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Integration user password, consumer can handle cutover | Dual-credential window if supported, else coordinated cutover | Minimize downtime |
| Connected app secret, many consumers | Dual-credential grace window | Native support |
| JWT cert renewal | Dual cert handover | Zero downtime |
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
4. Implement the stale-credential detector as a Scheduled Job.
5. Run a pilot rotation with coordination and verification.
6. Monitor and alert on failed post-rotation health checks.

---

## Salesforce-Specific Gotchas

1. Integration user password expiry can be set to "Never" — a common anti-pattern.
2. Rotating a client secret immediately invalidates every consumer using the old one; grace window must be explicit.
3. JWT connected apps can hold up to a limited number of certs; plan the handover slot.
4. Named credentials with refresh tokens silently invalidate if the user's password changes.
5. Removing a connected app user session does not revoke active OAuth tokens.

## Proactive Triggers

- Integration user with `PasswordNeverExpires = true` → Flag Critical.
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
