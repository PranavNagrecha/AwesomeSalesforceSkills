# Examples — Integration User Management

## Example 1: An Integration User Fails Right After an MFA Rollout — and MFA Is Not the Cause

**Context:** An org turns on MFA enforcement. The same week, a new Informatica integration user starts failing authentication on its first run. The existing MuleSoft integration user keeps working. The admin concludes that the new user missed a "grandfathered waiver" and opens a ticket to grant one.

**Problem:** The diagnosis is wrong, and the fix will not work. Org-wide MFA enforcement is scoped to direct UI logins — `SecuritySettings.enableMFADirectUILoginOptIn` "Requires all users in your Salesforce org to provide an additional verification method when logging in directly to the UI with their username and password" (`api_meta.txt` L126248–126252) — and an API Only User "can access Salesforce only via APIs, regardless of their other permissions" (`api_meta.txt` L121360–121363). There is no UI login for the setting to challenge. Something else changed in the same maintenance window: the same hardening ticket also set `requiredSessionLevel` to `HIGH_ASSURANCE` on the new user's profile, and that *does* block the flow — "For flows without a user approval step, API logins with the High Assurance session security level are blocked" (`api_meta.txt` L35826–35836). The MuleSoft user kept working because it sits on a different profile that the ticket did not touch.

**Solution:**

**Step 1 — read the failing login row before changing anything.** Filter on `UserId` and `LoginTime` only, then evaluate `Status` in the client, because `LoginHistory` is not filterable on `Status`:

```soql
SELECT LoginTime, Status, LoginType, LoginSubType, SourceIp, LoginUrl, TlsProtocol
FROM LoginHistory
WHERE UserId = '0055f00000InfaXAAR'
  AND LoginTime = LAST_N_DAYS:2
ORDER BY LoginTime DESC
```

**Step 2 — map the status to the gate that produced it.**

| What `Status` names | Actual cause | Fix |
|---|---|---|
| Restricted IP / untrusted source | `Profile.loginIpRanges`, enforced because the connected app's `ipRelaxation` is `ENFORCE` (`api_meta.txt` L35655–35661) | Add the middleware's egress range, retry cluster included |
| Login outside permitted hours | `Profile.loginHours` for that weekday (`api_meta.txt` L98071–98092) | Cover all seven days, or remove with an empty `<loginHours/>` |
| Session-level / identity-verification requirement on a headless flow | `ProfileSessionSetting.requiredSessionLevel` = `HIGH_ASSURANCE`, or a connected-app `RaiseSessionLevel` policy (`api_meta.txt` L35826–35836) | Return the integration profile to `STANDARD`; leave the app session policy off |

In this incident the status pointed at the session level. Setting `requiredSessionLevel` back to `STANDARD` on the Informatica profile restored the integration. No waiver was granted, and none was needed.

**Step 3 — reserve the waiver for accounts that actually log in through the UI.** "Waive Multi-Factor Authentication for Exempt Users" is documented as overriding the org's direct-UI-login MFA setting (`api_meta.txt` L126248–126252). Granting it to an API-only service account changes nothing about that account's API logins. If you do have a genuinely exempt account, keep the waiver in its own permission set carrying one user permission and nothing else, so it can be assigned and revoked without disturbing any data grants:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Integration MFA Waiver</label>
    <description>Waiver-only permission set. Assign to service accounts that fail identity verification. No object or field grants — those stay on the per-integration permission set.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <userPermissions>
        <enabled>true</enabled>
        <name>WaiveMfaForExemptUsers</name>
    </userPermissions>
</PermissionSet>
```

> UNVERIFIED (2026-09-05): the metadata API name of the "Waive Multi-Factor Authentication for Exempt Users" permission is shown here as `WaiveMfaForExemptUsers`. The permission's *label* appears in `api_meta.txt` L126248–126252 under `SecuritySettings.enableMFADirectUILoginOptIn`, but the Metadata API guide does not publish the `userPermissions` name string for it. Confirm the exact name by retrieving a permission set that already has the permission enabled before deploying this file.

**Why the JWT bearer flow is still the better default:** not because it evades MFA — nothing was evading MFA here — but because it transmits no password. There is no credential to rotate, expire, or leak, and no password policy that can lock the account out on a schedule nobody is watching. The one thing to remember is that it is precisely a flow with no user approval step, so it is the flow a High Assurance session requirement will silently block.

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
