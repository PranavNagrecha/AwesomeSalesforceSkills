# Gotchas: Connected Apps and Auth

---

## Using Admin Users for Integrations

**What happens:** A system integration authenticates as a human admin because it was the fastest way to get moving.

**When it bites you:** Security reviews, incident response, and any permission-related defect investigation.

**How to avoid it:** Use a dedicated integration principal with minimal permission sets and documented ownership.

---

## Hardcoded Endpoints and Tokens in Code

**What happens:** Developers or admins put API URLs or bearer tokens directly into Apex, JavaScript, or config files.

**When it bites you:** Environment promotion, credential rotation, and emergency revocation.

**How to avoid it:** Use Named Credentials and External Credentials as the default integration boundary.

---

## Choosing the Wrong OAuth Flow

**What happens:** A user-delegated scenario is built with machine auth, or a system-to-system integration is awkwardly forced through user consent.

**When it bites you:** Token lifecycle, access reviews, and long-term operability.

**How to avoid it:** Choose the auth flow based on whether user context is required and whether certificate management exists.

---

## No Revoke or Rotation Runbook

**What happens:** The integration works until a secret must be rotated or a connected app must be revoked quickly. Nobody knows the blast radius.

**When it bites you:** Expiring certificates, security incidents, and audit findings.

**How to avoid it:** Treat revoke, rotate, and recover as tested operational procedures.

---

## Assuming You Can Create a New Connected App in Spring '26+

**What happens:** A design calls for a brand-new connected app, but starting in Spring '26 Salesforce blocks connected-app creation by default — through both the UI and the Metadata API. Only package installation is excepted, and creation otherwise requires an exception from Salesforce Support.

**When it bites you:** Mid-build, when the "create connected app" step in the UI or a `ConnectedApp` metadata deploy fails in a Spring '26+ org and the whole integration timeline stalls.

**How to avoid it:** Design net-new inbound integrations on an External Client App (ECA), Salesforce's stated successor to connected apps. If a connected app is genuinely required, deliver it through a package install or request a Support exception. Existing connected apps keep functioning without restriction, so this only affects net-new creation.

---

## Expecting an External Client App to Survive a Sandbox Refresh

**What happens:** A team relies on the connected-app habit that local apps copy automatically when a sandbox is cloned or refreshed, then finds the ECA missing after a refresh.

**When it bites you:** Post-refresh integration testing, when the auth container an integration depends on is simply not there.

**How to avoid it:** External Client Apps do not copy into sandboxes automatically. Add ECA recreation or redeployment to the sandbox runbook, and don't treat a refresh as the mechanism that carries integration auth across environments.
