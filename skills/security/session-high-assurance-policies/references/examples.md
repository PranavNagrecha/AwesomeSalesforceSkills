# Examples — Session High Assurance Policies

## Example 1: Step-up gate on a compensation detail component

**Context:** HR org. Compensation figures live on `Employee__c` fields that a small population may read, but only from a session that was established with a second factor.

**Problem:** There is no Session Security Level Policy for a custom object, and the team's first instinct — a profile-wide "Session Security Level Required at Login" — would break the nightly payroll batch owned by the same profile.

**Solution:** Guard the controller and redirect a Standard session through Salesforce's own verification UI.

```apex
public with sharing class CompensationGate {
    private static final String STANDARD_LEVEL = 'STANDARD';

    public class StepUpRequiredException extends Exception {}

    @AuraEnabled
    public static String getVerificationUrl(String returnUrl) {
        Map<String, String> session = Auth.SessionManagement.getCurrentSession();
        String level = session.get('SessionSecurityLevel');
        if (level != null && STANDARD_LEVEL.equalsIgnoreCase(level)) {
            return Auth.SessionManagement.generateVerificationUrl(
                Auth.VerificationPolicy.HIGH_ASSURANCE,
                'View compensation detail',
                returnUrl
            );
        }
        return null;
    }

    @AuraEnabled(cacheable=true)
    public static Employee__c readCompensation(Id employeeId) {
        Map<String, String> session = Auth.SessionManagement.getCurrentSession();
        String level = session.get('SessionSecurityLevel');
        if (level == null || STANDARD_LEVEL.equalsIgnoreCase(level)) {
            throw new StepUpRequiredException('High Assurance session required.');
        }
        // Field-level security still does the actual authorization work.
        return [
            SELECT Id, Base_Salary__c, Bonus_Target__c
            FROM Employee__c
            WHERE Id = :employeeId
            WITH USER_MODE
            LIMIT 1
        ];
    }
}
```

**Failure path when the session is Standard:** `readCompensation` throws before any SOQL runs, so the component receives an error rather than data. It then calls `getVerificationUrl` and navigates the user to the returned URL; on successful verification Salesforce returns them to `returnUrl` with the session raised.

**Why it works:** the check sits on the Apex entry point, so it also covers anyone invoking the `@AuraEnabled` method directly. `WITH USER_MODE` keeps FLS and sharing enforced independently — the session level is an *additional* gate, never the authorization decision itself.

**What this does not do:** it does not stop the same user reading `Base_Salary__c` through a report, the REST API, or Data Loader. If that matters, the field needs field-level security or encryption treatment, not a session gate.

---

## Example 2: Login-level requirement scoped to a permission set, with the async carve-out

**Context:** A 12-person finance team must always authenticate with a second factor. Three of them own scheduled Apex.

**Problem:** Setting **Session Security Level Required at Login = High Assurance** on the Finance profile is the obvious move, and it is exactly what breaks the scheduled jobs — Salesforce documents High Assurance session settings as intended for synchronous and UI-based processing only, not for asynchronous contexts such as future, batch, or scheduled jobs.

**Solution:**

1. Leave the profile's Session Security Level Required at Login at **None**.
2. Create permission set `Finance_High_Assurance_Login` and set the requirement there.
3. Assign it to the nine users who own no asynchronous Apex.
4. For the three job owners, enforce MFA through the **Multi-Factor Authentication for User Interface Logins** permission instead, leaving the session-level requirement unset. This is the resolution Salesforce publishes for the async-Apex conflict.
5. Re-own the scheduled jobs to a dedicated automation user if you later need all twelve on the login requirement.

**Failure path if you skip step 4:** the asynchronous job fails at runtime for the affected owner. The user-facing symptom is a job that stops producing output, not a login error, so it is usually found days later by whoever consumes the output.

**Why it works:** the two mechanisms enforce the same business rule through different platform surfaces. The session-level requirement changes how the session is *created*; the MFA permission changes what the *UI login* demands. Only the first participates in asynchronous context validation.

---

## Example 3: Prove the policy is actually in force

**Context:** A quarter after rollout, an auditor asks for evidence that privileged users are reaching High Assurance sessions.

**Problem:** The Setup screens show intent, not outcome. If someone moved **Two-Factor Authentication** out of the High Assurance column in Session Settings, every downstream policy quietly stops biting and no error is raised anywhere.

**Solution:** query the session store directly. `AuthSession.SessionSecurityLevel` is documented as "Standard or High, depending upon the authentication method used".

```sql
SELECT UsersId, Users.Name, SessionType, LoginType,
       SessionSecurityLevel, LoginHistoryId, CreatedDate, SourceIp
FROM AuthSession
WHERE SessionType = 'UI'
  AND UsersId IN (
      SELECT AssigneeId FROM PermissionSetAssignment
      WHERE PermissionSet.PermissionsModifyAllData = true
  )
ORDER BY CreatedDate DESC
```

Any row with `SessionSecurityLevel = 'Standard'` for a Modify All Data holder is the finding. Join to `LoginHistory` on `LoginHistoryId` to recover `LoginSubType`, `Browser`, and `SourceIp` for the same event.

**Why it works:** it measures the sessions that actually existed rather than the configuration that was supposed to produce them.

**Caveat:** `AuthSession` holds current sessions, so schedule this (or stream login events via Event Monitoring) rather than expecting a historical record to still be there. Users can query only their own sessions; an administrator sees all of them.

**Reusable helper:** the two documented surfaces disagree on casing — the Apex map example shows `SessionSecurityLevel=STANDARD` while `AuthSession` documents "Standard or High" — so normalise once and fail closed.

```apex
public inherited sharing class SessionLevel {
    /** True only when the current session is demonstrably NOT standard. */
    public static Boolean isElevated() {
        Map<String, String> session = Auth.SessionManagement.getCurrentSession();
        String level = session == null ? null : session.get('SessionSecurityLevel');
        return String.isNotBlank(level) && !'STANDARD'.equalsIgnoreCase(level.trim());
    }
}
```
