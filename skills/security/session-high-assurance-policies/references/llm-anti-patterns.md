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
if (!'HIGH_ASSURANCE'.equalsIgnoreCase(level)) {   // LOW, STANDARD, blank: all fail closed
    throw new SecurityException('Step up required');
}
```

**Detection hint:** grep the diff for `UserInfo.getSession` and accept only `UserInfo.getSessionId`. Any other `UserInfo.getSession*` call is fabricated and will not compile.

---

## Anti-Pattern 2: Gating on "not STANDARD" instead of an exact HIGH_ASSURANCE match

**What the LLM generates:**

```apex
// WRONG - a LOW session is "not STANDARD", so it passes the gate
String level = Auth.SessionManagement.getCurrentSession().get('SessionSecurityLevel');
Boolean elevated = String.isNotBlank(level) && !'STANDARD'.equalsIgnoreCase(level.trim());
```

**Why it happens:** the documented map example shows only `SessionSecurityLevel=STANDARD` (apexref 262 L11487), so "anything else is elevated" looks safe. It is not: `Auth.SessionLevel` also has `LOW`, settable through the API (apexref 262 L11901-11906; api_meta 264 L101518-101520). An earlier version of this skill recommended exactly this wrong pattern.

**Correct pattern:**

```apex
String level = Auth.SessionManagement.getCurrentSession().get('SessionSecurityLevel');
Boolean elevated = level != null && 'HIGH_ASSURANCE'.equalsIgnoreCase(level.trim());
```

`HIGH_ASSURANCE` is the enum value (apexref 262 L11911); if the map ever spells it differently, this gate fails closed and the Standard-session test shows a redirect loop rather than exposure.

**Detection hint:** a gate written as "not STANDARD" (`!'STANDARD'.equalsIgnoreCase(`) is fail-open on `LOW`. Security checks must be elevated only on the exact elevated value.

---

## Anti-Pattern 3: Applying "Session Security Level Required at Login" org-wide

**What the LLM generates:** "Set Session Security Level Required at Login to High Assurance on the System Administrator profile (or in org-wide Session Settings) so all admins must use MFA."

**Why it happens:** the requirement is phrased as a population ("all admins"), and profile-level settings are the coarsest, most reachable control.

**Correct pattern:** keep the login-level requirement off any profile whose users own asynchronous Apex, and enforce MFA for them with the **Multi-Factor Authentication for User Interface Logins** permission (platform_events 264 L20413-20415). UNVERIFIED (2026-10-20): the permission-set form below and the async conflict are Help-only; the corpus grounds only the profile form (`ProfileSessionSetting.requiredSessionLevel`, api_meta 264 L101471):

```text
Profile  Finance User            Session Security Level Required at Login = None
PermSet  Finance_HA_Login        Session Security Level Required at Login = High Assurance
                                 assigned to: the 9 users owning no async Apex
PermSet  Finance_MFA_UI          MFA for User Interface Logins = true
                                 assigned to: the 3 scheduled-job owners
```

**Detection hint:** if the proposal sets the login-level requirement on a broad profile, or does not mention batch/scheduled/`@future` owners at all, it has not considered the async-Apex conflict.

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

**Correct pattern:** the list is a fixed set of Setup operations (UNVERIFIED (2026-10-20): the list itself is Help-only). Nothing on it is an sObject. For record data, write the Apex gate:

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

**Why it happens:** "MFA" and "High Assurance" are used interchangeably in most security writing. In Salesforce they are separate: High Assurance is a property of the session, set by the login-method mapping in Session Settings — MFA logins require HIGH_ASSURANCE and username/password logins the standard level (api_meta 264 L101497-101505). UNVERIFIED (2026-10-20): the per-method defaults (only Two-Factor Authentication in the High Assurance column) are Help-only.

**Correct pattern:** verify the mapping first, then verify the outcome:

```sql
SELECT UsersId, SessionType, LoginType, SessionSecurityLevel
FROM AuthSession
WHERE SessionType = 'UI' AND SessionSecurityLevel = 'Standard'
```

Any privileged user in that result set is enrolled in MFA but is not producing High Assurance sessions.

**Detection hint:** an answer that never mentions Setup → Session Settings → Session Security Levels has skipped the step that decides whether any of the rest can work.

