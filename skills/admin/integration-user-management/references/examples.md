# Examples — Integration User Management

## Example 1: Integration User Blocked by MFA After MFA Enforcement Rollout

**Context:** An org enables MFA enforcement for all users. The existing MuleSoft integration user was created before MFA enforcement and continues to authenticate normally (grandfathered waiver). A new Informatica integration project starts and the admin creates a new integration user. First authentication attempt from Informatica fails with MFA challenge.

**Problem:** New integration users created after MFA enforcement is enabled do not automatically receive the MFA waiver. The new Informatica user requires MFA but cannot complete MFA challenges in a server-to-server flow.

**Solution:**

Option A — MFA Waiver via Permission:
1. Create a permission set named "Integration MFA Waiver."
2. Enable the "Waive Multi-Factor Authentication for Exempt Users" user permission.
3. Assign to the Informatica integration user.
4. Test authentication — MFA challenge should no longer appear.

Option B — JWT Bearer Flow (preferred):
1. Configure the connected app with a certificate-based JWT bearer flow instead of username-password OAuth.
2. JWT bearer flow never triggers MFA — it uses a signed JWT assertion, not interactive authentication.
3. This eliminates the need for MFA waivers entirely for this integration.

**Why Option B is preferred:** JWT bearer flow is inherently MFA-resistant and does not require ongoing waiver management. Any new integration user using JWT bearer flow does not need an MFA waiver regardless of org MFA enforcement settings.

---

## Example 2: Auditing an Integration User for Unexpected API Activity

**Context:** The security team flags that an integration user is making API calls at 3 AM on weekdays — outside the expected ETL window (11 PM to 1 AM). They need to determine whether this is legitimate activity or a compromised credential.

**Solution:**

Query LoginHistory via the API to get full detail:

```soql
SELECT Id, UserId, Status, LoginType, SourceIp, LoginTime, Application
FROM LoginHistory
WHERE UserId = '005XXXXXXXXXXXXXXXXX'
  AND LoginTime >= 2026-04-01T00:00:00Z
  AND LoginTime < 2026-04-12T00:00:00Z
ORDER BY LoginTime DESC
LIMIT 500
```

Review the results:
- `SourceIp` matches the known ETL server IP for the 11 PM–1 AM window.
- `SourceIp` for the 3 AM calls shows a different IP address not in the known ETL server range.
- `LoginType` shows "OAuth" for both windows — consistent with the integration pattern.

Conclusion: The 3 AM activity appears to originate from an unrecognized IP. The security team temporarily disables the integration user, rotates the connected app consumer secret, and investigates the source. The ETL tool had a background retry job configured to run at 3 AM on failure — the retry was coming from a different server in the ETL cluster. The IP range was expanded in the integration user's profile to include the retry cluster's IP.

**Why it works:** The `LoginHistory` SOQL object provides full audit history (up to 6 months) including IP address, login type, and status — detail that the Setup UI's 20,000-record limit would have truncated for a high-frequency integration.

---

## Anti-Pattern: Granting System Administrator Profile to Integration User

**What practitioners do:** An integration user is getting permission errors accessing a specific object. The admin temporarily grants the System Administrator profile to "unblock" the integration, intending to narrow it down later.

**What goes wrong:** System Administrator profile enables interactive Salesforce UI login. The integration user account now has full admin access via browser. "Temporary" admin profiles rarely get revoked. Audit logs now show integration API calls mixed with admin-session activity, making forensics impossible. If the integration user's credentials are compromised, the attacker has full admin access to the org.

**Correct approach:** When an integration user encounters permission errors, investigate the specific error (which object, which operation), then add a permission to the integration user's permission set for only that specific object/operation. Never grant admin profile to resolve permission errors. Use the Salesforce Permission Set API or the Permission Set Debug Logs to identify exactly what permission is missing.
