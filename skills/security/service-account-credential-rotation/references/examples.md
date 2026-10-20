# Service Account Credential Rotation — Examples

## Example 1: JWT Certificate Cutover

**Context:** Connected App using JWT bearer flow; certificate expires in 90 days.

**Procedure:**
1. Generate the new signing cert and key pair.
2. In one change window, replace the app's `certificate` (one PEM string per app, api_meta 264 L37419) and switch the consumer to the new key.
3. Verify traffic signing with the new cert via login history.
4. For zero downtime instead, create a second connected app with the new cert, move consumers, then retire the old app.

**Why it works:** The app holds one certificate, so the cutover is planned rather than assumed to overlap. An earlier version of this example uploaded a second certificate; the metadata has no second slot.

---

## Example 2: Integration User Password Rotation

**Context:** MuleSoft uses an integration user via the Username-Password OAuth flow (UNVERIFIED (2026-10-20): its "being phased out" status is not in the corpus).

**Procedure:**
1. Create new Salesforce credential in vault (HashiCorp).
2. Schedule a maintenance window (30 sec).
3. Reset the user's password in Salesforce.
4. Update vault with new password.
5. MuleSoft reloads credential on next token refresh.
6. Verify sessions via login history.

**Why it works:** Coordinated cutover; consumer reads from vault, not code.

---

## Anti-Pattern: Granting Password Never Expires

Granting the Password Never Expires permission (secguide 262 L6398) through the integration profile or a permission set to avoid rotation pain. In source it looks like this — the checker flags it:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: integration profile; remove this block -->
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <userPermissions>
        <enabled>true</enabled>
        <name>PasswordNeverExpires</name>
    </userPermissions>
</Profile>
```

It makes the credential a forever-live secret. Any future leak has no mitigation window. Fix: remove the permission from the profile and permission sets (or set its `<enabled>` to `false`), build the rotation runbook, use a vault.
