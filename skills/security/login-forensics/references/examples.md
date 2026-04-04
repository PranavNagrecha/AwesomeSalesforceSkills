# Examples — Login Forensics

## Example 1: Credential Stuffing Attack — Identify Affected Accounts by Source IP

**Context:** The security team receives an alert from an external threat feed that an IP block (`198.51.100.0/24`) was used in a credential stuffing campaign against multiple SaaS platforms. They need to determine whether any Salesforce accounts were targeted, which users had successful logins from that block, and whether MFA was completed or bypassed.

**Problem:** Checking Setup > Login History in the UI only shows 20,000 records and does not allow IP range filtering or cross-user pivots. The team cannot export this data fast enough through the UI during an active incident.

**Solution:**

Step 1 — Identify any users who had a successful login from the suspicious IP block:

```soql
SELECT UserId, LoginTime, SourceIp, Status, Browser, Platform
FROM LoginHistory
WHERE SourceIp LIKE '198.51.100.%'
  AND LoginTime >= LAST_N_DAYS:7
ORDER BY LoginTime ASC
```

Step 2 — Separate successes from failures to determine blast radius:

```soql
SELECT UserId, COUNT(Id) totalAttempts,
       SUM(CASE WHEN Status = 'Success' THEN 1 ELSE 0 END) successes
FROM LoginHistory
WHERE SourceIp LIKE '198.51.100.%'
  AND LoginTime >= LAST_N_DAYS:7
GROUP BY UserId
ORDER BY successes DESC
```

Note: `CASE` expressions are not supported in SOQL. Use two separate queries — one filtered by `Status = 'Success'` and one by `Status != 'Success'` — and join results in a script.

Step 3 — For each user with a successful login, check whether MFA was completed or skipped:

```soql
SELECT UserId, VerificationTime, Activity, Status, Comments
FROM IdentityVerificationHistory
WHERE UserId IN ('005XXXXXXXXXXXXXXX', '005YYYYYYYYYYYYYYY')
  AND VerificationTime >= LAST_N_DAYS:7
ORDER BY VerificationTime DESC
```

Step 4 — Freeze affected accounts and revoke sessions in Apex (run via Developer Console):

```apex
// Freeze a compromised user
User u = [SELECT Id, IsActive FROM User WHERE Id = '005XXXXXXXXXXXXXXX' LIMIT 1];
u.IsActive = false;
update u;

// Revoke all active sessions for the user
Auth.SessionManagement.revokeSessionsForUser('005XXXXXXXXXXXXXXX',
    Auth.SessionManagement.REVOKEALLSESSIONS_TYPE.ALL_SESSIONS);
```

**Why it works:** `LoginHistory` provides the source IP for every login attempt with no license requirement. The SOQL approach scales to the full 6-month history, supports aggregation, and is automatable via the REST API. Combining it with `IdentityVerificationHistory` gives a complete picture of whether multi-factor authentication was actually enforced at each login event.

---

## Example 2: Login Flow for Step-Up Authentication on a Privileged Profile

**Context:** An org has a "Data Export Admin" profile that can export up to 10,000 records via list views and reports. The security team wants to require a TOTP verification challenge at login for any user on this profile, without enrolling them in a full MFA flow that would affect all users.

**Problem:** Standard MFA in Salesforce applies org-wide or per permission set. Login Flows allow per-profile enforcement without requiring org-wide MFA policy changes, but practitioners often configure them incorrectly (attaching to the wrong entity or skipping the sandbox test cycle).

**Solution:**

Step 1 — Build the Screen Flow in Flow Builder:
- Flow type: Screen Flow
- Add a Screen element with a custom component or formula field that collects the verification token
- Call an invocable Apex action that validates the token against `Totp` library or a custom TOTP provider
- Add a Decision element: if validation fails, route to an error screen and set an output variable `loginFlowError = true`

Step 2 — Register the Login Flow:
- Setup > Login Flows > New
- Connect the Screen Flow to the "Data Export Admin" profile
- Set execution context to "On Login"

Step 3 — Verify behavior:

```soql
-- After testing, confirm the Login Flow fired and the LoginHistory records show the correct LoginType
SELECT UserId, LoginTime, LoginType, Status, SourceIp
FROM LoginHistory
WHERE LoginTime >= TODAY
ORDER BY LoginTime DESC
LIMIT 50
```

Expected `LoginType` value: `Application` (browser UI login). Login Flows do not alter the `LoginType` field, but a Flow-terminated login (error route) will result in a `LoginHistory` record with `Status = 'Failed'`.

Step 4 — Monitor for bypasses:

```soql
SELECT UserId, LoginTime, Status
FROM LoginHistory
WHERE LoginTime >= LAST_N_DAYS:30
ORDER BY LoginTime DESC
LIMIT 200
```

Cross-reference any `Status = 'Success'` records for users on the "Data Export Admin" profile against the expected login window (Login Hours) to catch off-hours access.

**Why it works:** Login Flows intercept the login process after credential validation but before session creation, which means they cannot be bypassed by an attacker who only has the password. The `Auth.SessionManagement` approach revokes existing sessions if a breach is detected after the fact. Attaching the flow to a profile rather than org-wide minimizes disruption to regular users.

---

## Anti-Pattern: Relying on Setup > Login History UI for Incident Response

**What practitioners do:** When a user account is reported compromised, practitioners open Setup > Login History in the Salesforce UI, filter by the user's name, and read the resulting table to investigate the timeline.

**What goes wrong:**
- The UI only displays the most recent 20,000 login records org-wide, not per user
- There is no way to export the UI results directly to CSV for sharing with legal or compliance teams
- The UI does not support IP range filtering (e.g., `198.51.100.*`) or cross-user aggregation
- During a high-volume credential stuffing event, the 20,000-record cap means recent entries push older relevant records out of view
- The UI does not show `IdentityVerificationHistory` in the same view, so MFA bypass analysis requires a second manual lookup

**Correct approach:** Always use SOQL against `LoginHistory` and `IdentityVerificationHistory` via the Developer Console, REST API, or a tooling script. Filter by `LoginTime` range and `UserId` or `SourceIp` as appropriate. Export results to CSV for audit trail preservation. SOQL returns the full 6-month history within governor limits, not just the last 20,000 org-wide records.
