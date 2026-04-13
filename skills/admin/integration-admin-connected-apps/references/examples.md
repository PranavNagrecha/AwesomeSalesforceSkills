# Examples — Integration Admin: Connected Apps

## Example 1: Pre-Authorized Mode Blocking All Authentication

**Context:** An admin configures a connected app for a MuleSoft integration. The integration uses a dedicated integration user. The admin sets "Admin approved users are pre-authorized" in the OAuth Policies and saves. MuleSoft immediately begins receiving OAuth errors — no authentication succeeds, including test authentication from the Salesforce admin console.

**Problem:** The admin set pre-authorized mode but did not assign the connected app to the integration user's Profile or any Permission Set. Pre-authorized mode means "only users who have been explicitly pre-authorized can authenticate" — with no assignments, no users are pre-authorized.

**Solution:**

1. Navigate to Setup > Users > Profiles > [Integration User Profile].
2. Scroll to "Connected App Access" section.
3. Enable the checkbox next to the connected app name.
4. Save the profile.
5. Test authentication as the integration user — OAuth token issuance should now succeed.

Alternatively, assign via Permission Set:
1. Navigate to Setup > Permission Sets > [Integration Permission Set].
2. Click "Assigned Apps."
3. Enable the connected app and save.

**Why it works:** Pre-authorized mode gates access on an explicit profile or permission set assignment. The assignment tells Salesforce which users are pre-authorized. Without it, the "approved users" list is empty.

---

## Example 2: Monitoring a Connected App Integration for Token Revocations

**Context:** An ETL integration that has been running for 18 months suddenly fails every Sunday afternoon. The error logs from the ETL platform show "invalid_grant: expired access/refresh token." The admin suspects a refresh token is expiring but the Refresh Token Policy shows "Expire after 90 days."

**Problem:** The admin looks in Setup > Login History and sees the integration user's last login but no OAuth token-level events. Login History does not show token revocations.

**Solution:**

Query EventLogFile for ConnectedAppOAuth events (requires Event Monitoring add-on):

```
GET /services/data/v63.0/query?q=SELECT+Id,LogDate+FROM+EventLogFile
+WHERE+EventType='ConnectedAppOAuth'+AND+LogDate=LAST_N_DAYS:7
```

Download the log file CSV and filter by the integration user's username. Review the `TOKEN_TYPE` and `REVOCATION_REASON` columns. The Sunday entries show `REVOCATION_REASON=AdminRevoked` — an automated cleanup job is revoking integration tokens on Sunday nights.

Fix: Identify and disable the automated token cleanup job, or configure the integration to re-authenticate after revocations.

**Why it works:** ConnectedAppOAuth EventLogFile events capture token-level OAuth lifecycle events that Login History does not surface. The EventLogFile REST API is the only way to access this audit data.

---

## Anti-Pattern: Using System Administrator Profile for Integration Connected App

**What practitioners do:** To "simplify" integration setup, assign the System Administrator profile to the integration user and configure the connected app to allow all users to self-authorize.

**What goes wrong:** The integration user now has interactive login capability (System Administrator profile does not have the API-only flag). A compromised token provides admin-level access to the org via both API and the Salesforce UI. The integration is not subject to least-privilege principle — any data accessible to an admin is accessible to the integration, even if the integration only needs to write to a specific set of objects.

**Correct approach:** Use the Salesforce Integration user license with the "Minimum Access - API Only Integrations" profile for the base profile. Layer targeted Permission Sets on top to grant only the specific object and field permissions the integration requires. Set the connected app to pre-authorized mode and assign it to the integration Permission Set. The API-only flag in the profile prevents interactive login even if the credentials are compromised.
