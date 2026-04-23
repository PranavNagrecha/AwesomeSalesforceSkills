# MFA Enforcement — Examples

## Example 1: Post-Acquisition SSO Interop

Company A uses Okta SSO with MFA. Acquired Company B had direct login
with MFA auto-enabled. Merge plan:

- Federate B's users to Okta.
- Map email to `FederationId`.
- Confirm Okta asserts `AuthnContextClassRef` = MFA.
- Remove direct MFA from B's users; Okta now enforces.
- Keep one break-glass non-SSO admin, exception expires in 90 days.

## Example 2: Legacy ETL Integration Using Username/Password

Nightly ETL hits `/services/data/v58.0/query` using a service account's
username + security token + SOAP login.

**Problem:** this is a direct login subject to MFA; MFA will break the job.

**Fix:** migrate to a Connected App with JWT Bearer flow. ETL signs a
JWT with a server-side key; Salesforce returns an access token.
Usernames/passwords are removed.

## Example 3: Exception Object Schema

```text
MFA_Exception__c
- User__c (lookup)
- Justification__c (long text, required)
- Owner__c (lookup to internal approver)
- ExpiresAt__c (date, required, validation: <= today + 180)
- ReviewedAt__c (date)
```

Validation rule: `ExpiresAt__c - TODAY() > 180 → error`.

## Example 4: Authenticator Rollout Communication

- T-21 days: announce to all direct-login users.
- T-14: Authenticator install guide published.
- T-7: reminder; help-desk runbook live.
- T-0: enforce; monitor error rate.
- T+7: retrospective; close exceptions requested "for go-live."

## Example 5: Audit Query (Login History)

```sql
SELECT UserId, LoginTime, AuthenticationMethod, Status
FROM LoginHistory
WHERE LoginTime = LAST_N_DAYS:30
  AND AuthenticationMethod = 'Username/Password'
```

Any direct username/password logins post-cutover are investigation
targets.
