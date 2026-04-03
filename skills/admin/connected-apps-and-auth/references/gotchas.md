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
