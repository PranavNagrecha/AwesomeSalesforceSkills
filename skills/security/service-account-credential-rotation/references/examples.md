# Service Account Credential Rotation — Examples

## Example 1: JWT Dual-Cert Handover

**Context:** Connected App using JWT bearer flow; certificate expires in 90 days.

**Procedure:**
1. Generate new signing cert; upload to Connected App (two certs now active).
2. Update consumer signing key to new cert; deploy.
3. Verify traffic signing with new cert via login history.
4. After a week of clean telemetry, remove old cert.

**Why it works:** Dual-valid window absorbs any consumer that's slow to roll.

---

## Example 2: Integration User Password Rotation

**Context:** MuleSoft uses an integration user via Username-Password OAuth flow (legacy, being phased out).

**Procedure:**
1. Create new Salesforce credential in vault (HashiCorp).
2. Schedule a maintenance window (30 sec).
3. Reset the user's password in Salesforce.
4. Update vault with new password.
5. MuleSoft reloads credential on next token refresh.
6. Verify sessions via login history.

**Why it works:** Coordinated cutover; consumer reads from vault, not code.

---

## Anti-Pattern: PasswordNeverExpires = true

Setting this to avoid rotation pain. Makes the credential a forever-live secret. Any future leak has no mitigation window. Fix: set to false, build the rotation runbook, use a vault.
