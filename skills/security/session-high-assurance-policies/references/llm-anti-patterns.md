# LLM Anti-Patterns — Session High Assurance Policies

## Anti-Pattern 1: Calling a session-security method on `UserInfo`

**What the LLM generates:**

```apex
// WRONG - no such method exists on UserInfo
if (UserInfo.getSessionSecurityLevel() != 'HIGH_ASSURANCE') {
    throw new SecurityException('Step up required');
}
```

**Why it happens:** `UserInfo` is where `getUserId`, `getProfileId`, `getSessionId`, and `getUserType` live, so a session *level* accessor looks like it belongs there. It does not. The Apex Reference lists exactly one session method on `UserInfo`: `getSessionId()`.

**Correct pattern:**

```apex
Map<String, String> session = Auth.SessionManagement.getCurrentSession();
String level = session == null ? null : session.get('SessionSecurityLevel');
if (String.isBlank(level) || 'STANDARD'.equalsIgnoreCase(level)) {
    throw new SecurityException('Step up required');
}
```

**Detection hint:** grep the diff for `UserInfo.getSession` and accept only `UserInfo.getSessionId`. Any other `UserInfo.getSession*` call is fabricated and will not compile.

---

## Anti-Pattern 2: Comparing against the "high" literal instead of the "standard" literal

**What the LLM generates:**

```apex
// WRONG - fails open on any value the model did not anticipate
Boolean elevated = 'HIGH_ASSURANCE'.equals(
    Auth.SessionManagement.getCurrentSession().get('SessionSecurityLevel'));
```

**Why it happens:** the `Auth.SessionLevel` enum has a `HIGH_ASSURANCE` member, so the model assumes the map returns the same token. The documented map example shows `SessionSecurityLevel=STANDARD`; the `AuthSession` object documents the picklist as "Standard or High". The elevated literal for the Apex map is not spelled out.

**Correct pattern:**

```apex
String level = Auth.SessionManagement.getCurrentSession().get('SessionSecurityLevel');
Boolean elevated = String.isNotBlank(level) && !'STANDARD'.equalsIgnoreCase(level.trim());
```

**Detection hint:** any case-sensitive `.equals(` against a session-level string, or any comparison whose *positive* branch is the elevated one, is a fail-open gate. Security checks must fail closed on unknown values.

---

## Anti-Pattern 3: Applying "Session Security Level Required at Login" org-wide

**What the LLM generates:** "Set Session Security Level Required at Login to High Assurance on the System Administrator profile (or in org-wide Session Settings) so all admins must use MFA."

**Why it happens:** the requirement is phrased as a population ("all admins"), and profile-level settings are the coarsest, most reachable control.

**Correct pattern:** scope it to a permission set, assign only to users who own no asynchronous Apex, and enforce MFA for the rest with the **Multi-Factor Authentication for User Interface Logins** permission:

```text
Profile  Finance User            Session Security Level Required at Login = None
PermSet  Finance_HA_Login        Session Security Level Required at Login = High Assurance
                                 assigned to: the 9 users owning no async Apex
PermSet  Finance_MFA_UI          MFA for User Interface Logins = true
                                 assigned to: the 3 scheduled-job owners
```

**Detection hint:** if the proposal touches a profile rather than a permission set, or does not mention batch/scheduled/`@future` owners at all, it has not considered the async-Apex conflict.

---

## Anti-Pattern 4: Treating the session level as field-level security

**What the LLM generates:** "Require a High Assurance session to view the SSN field" — implemented purely as a session check, with SSN left readable in the profile's field-level security.

**Why it happens:** the business requirement literally names the field, so a field-shaped answer feels right, and step-up sounds stronger than FLS.

**Correct pattern:** the session level gates the *surface*; FLS gates the *field*. Keep both, and query in user mode so the field control is real:

```apex
if (!SessionLevel.isElevated()) {
    throw new SecurityException('High Assurance session required.');
}
return [SELECT Id, SSN__c FROM Contact WHERE Id = :recordId WITH USER_MODE LIMIT 1];
```

**Detection hint:** a design that removes or relaxes an FLS control "because the session gate covers it" is the failure. A session gate covers only the entry points you wrote it on — not reports, not the REST API, not Data Loader.

---

## Anti-Pattern 5: Inventing a declarative policy for record data

**What the LLM generates:** "In Setup → Identity Verification → Session Security Level Policies, add a policy for the `Patient__c` object and set it to High Assurance."

**Why it happens:** the policy list *looks* extensible, and the model has seen the phrase "session security level policies" attached to sensitive-data requirements.

**Correct pattern:** the list is fixed at 17 Setup operations. Nothing on it is an sObject. For record data, write the Apex gate:

```text
Requirement                       Implementation
"Restrict Data Export"        ->  Session Security Level Policy: Manage Data Export
"Restrict report building"    ->  Session Security Level Policy: Reports and Dashboards
"Restrict Patient__c detail"  ->  Apex gate on the controller + FLS  (no policy exists)
```

**Detection hint:** if a proposed Session Security Level Policy names an object, a field, a Visualforce page, or an LWC, it is fabricated.

---

## Anti-Pattern 6: Assuming MFA enrollment implies a High Assurance session

**What the LLM generates:** "MFA is enabled for these users, so their sessions are already High Assurance — no further configuration is needed."

**Why it happens:** "MFA" and "High Assurance" are used interchangeably in most security writing. In Salesforce they are separate: High Assurance is a property of the *login method* mapping in Session Settings, and only **Two-Factor Authentication** defaults into the High Assurance column. Username and Password, Delegated Authentication, Activation, Lightning Login, Passwordless Login, Authentication Provider, and SAML all default to Standard.

**Correct pattern:** verify the mapping first, then verify the outcome:

```sql
SELECT UsersId, SessionType, LoginType, SessionSecurityLevel
FROM AuthSession
WHERE SessionType = 'UI' AND SessionSecurityLevel = 'Standard'
```

Any privileged user in that result set is enrolled in MFA but is not producing High Assurance sessions.

**Detection hint:** an answer that never mentions Setup → Session Settings → Session Security Levels has skipped the step that decides whether any of the rest can work.

