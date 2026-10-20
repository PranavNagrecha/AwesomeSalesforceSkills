# Examples — Session High Assurance Policies

## Example 1: Step-up gate on a compensation detail component

**Context:** HR org. Compensation figures live on `Employee__c` fields that a small population may read, but only from a session that was established with a second factor.

**Problem:** There is no Session Security Level Policy for a custom object, and the team's first instinct — a profile-wide "Session Security Level Required at Login" — would break the nightly payroll batch owned by the same profile.

**Solution:** Guard the controller and redirect a Standard session through Salesforce's own verification UI.

```apex
public with sharing class CompensationGate {
    // Enum value per apexref 262 L11911; LOW, STANDARD, blank or unknown all fail closed.
    private static final String HIGH_LEVEL = 'HIGH_ASSURANCE';

    public class StepUpRequiredException extends Exception {}

    @AuraEnabled
    public static String getVerificationUrl(String returnUrl) {
        Map<String, String> session = Auth.SessionManagement.getCurrentSession();
        String level = session.get('SessionSecurityLevel');
        if (!HIGH_LEVEL.equalsIgnoreCase(level)) {
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
        if (!HIGH_LEVEL.equalsIgnoreCase(level)) {
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

**Failure path when the session is not High Assurance (Standard, LOW, or unreadable):** `readCompensation` throws before any SOQL runs, so the component receives an error rather than data. It then calls `getVerificationUrl` and navigates the user to the returned URL; on successful verification Salesforce returns them to `returnUrl` with the session raised.

**Why it works:** the check sits on the Apex entry point, so it also covers anyone invoking the `@AuraEnabled` method directly. `WITH USER_MODE` keeps FLS and sharing enforced independently — the session level is an *additional* gate, never the authorization decision itself.

**What this does not do:** it does not stop the same user reading `Base_Salary__c` through a report, the REST API, or Data Loader. If that matters, the field needs field-level security or encryption treatment, not a session gate.

---

## Example 2: Login-level requirement with the async carve-out

**Context:** A 12-person finance team must always authenticate with a second factor. Three of them own scheduled Apex.

**Problem:** Setting **Session Security Level Required at Login = High Assurance** on the Finance profile (`ProfileSessionSetting.requiredSessionLevel`, api_meta 264 L101471) is the obvious move, and Help KB 000392426 reports that it breaks the scheduled jobs. UNVERIFIED (2026-10-20): the async conflict, the permission-set form of the setting used in steps 2-3, and the published workaround in step 4 are Help-only — reproduce in a sandbox first.

**Solution:**

1. Leave the profile's Session Security Level Required at Login at **None**.
2. Create permission set `Finance_High_Assurance_Login` and set the requirement there.
3. Assign it to the nine users who own no asynchronous Apex.
4. For the three job owners, enforce MFA through the **Multi-Factor Authentication for User Interface Logins** permission instead (identity verification at login, platform_events 264 L20413-20415), leaving the session-level requirement unset.
5. Re-own the scheduled jobs to a dedicated automation user if you later need all twelve on the login requirement.

**Failure path if you skip step 4:** per Help KB 000392426 (UNVERIFIED (2026-10-20)), the asynchronous job fails at runtime for the affected owner. The user-facing symptom is a job that stops producing output, not a login error, so it is usually found days later by whoever consumes the output.

**Why it works:** the two mechanisms enforce the same business rule through different platform surfaces. The session-level requirement changes how the session is *created*; the MFA permission changes what the *UI login* demands. Only the first participates in asynchronous context validation.

---

## Example 3: Prove the policy is actually in force

**Context:** A quarter after rollout, an auditor asks for evidence that privileged users are reaching High Assurance sessions.

**Problem:** The Setup screens show intent, not outcome. If someone moved **Two-Factor Authentication** out of the High Assurance column in Session Settings, MFA logins would stop producing High Assurance sessions (UNVERIFIED (2026-10-20): Help-only, like the claim that policies then stop biting silently — see gotchas.md Gotcha 4).

**Solution:** query the session store directly. `AuthSession.SessionSecurityLevel` is documented as "Standard or High, depending upon the authentication method used" (obj 264 L47595).

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

**Caveat:** `AuthSession` holds current sessions, so schedule this (or stream login events via Event Monitoring) rather than expecting a historical record to still be there. Non-admin users see only their own sessions, "while administrators can see all sessions" (obj 264 L47652).

**Reusable helper:** the two documented surfaces disagree on casing — the Apex map example shows `SessionSecurityLevel=STANDARD` (apexref 262 L11487) while `AuthSession` documents "Standard or High" — and a `LOW` level also exists (apexref 262 L11901-11906). Match the elevated value exactly and fail closed on everything else.

```apex
public inherited sharing class SessionLevel {
    /** True only on an exact HIGH_ASSURANCE match; LOW, STANDARD, blank and unknown values return false. */
    public static Boolean isElevated() {
        Map<String, String> session = Auth.SessionManagement.getCurrentSession();
        String level = session == null ? null : session.get('SessionSecurityLevel');
        return level != null && 'HIGH_ASSURANCE'.equalsIgnoreCase(level.trim());
    }
}
```
