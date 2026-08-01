# Well-Architected Notes — Session High Assurance Policies

## Relevant Pillars

| Pillar | How this skill contributes |
|---|---|
| **Security** | Step-up authentication narrows the window in which a stolen password alone is useful. A Standard session that reaches a gated operation is stopped or challenged rather than served. |
| **Reliability** | The dominant failure mode here is self-inflicted: a login-level requirement applied to a profile that owns asynchronous Apex takes out batch and scheduled jobs with no login-shaped error to trace. Scoping is a reliability control, not a nicety. |
| **Operational Excellence** | The configuration is silently reversible from one Session Settings screen, so the design is incomplete without a detection query that measures the sessions actually produced. |

## Architectural Tradeoffs

- **Login-level requirement vs in-session step-up.** Requiring High Assurance at login is simpler to explain and audit, but it applies to every session those users open — including the ones that host asynchronous work. In-session step-up (`Auth.SessionManagement.generateVerificationUrl`) is narrower and keeps async contexts clean, at the cost of application code that must be maintained and tested on every entry point.
- **Declarative policy vs Apex gate.** A Session Security Level Policy is enforced by the platform at every entry point to the named operation, including API paths your code never sees. An Apex gate covers only the entry points you wrote it on. Prefer the policy whenever the requirement maps to one of the 17 listed operations, and be explicit in the design about the coverage you lose when it does not.
- **Session level vs data-layer controls.** Elevating the session is cheap and reversible; encrypting a field or tightening field-level security is neither. The session level is the right control for "who may reach this surface" and the wrong control for "who may read this value" — the two must be designed together, not traded against each other.
- **Blocking vs raising.** *Block* is unambiguous and produces no support load for a population that has no business in the operation. *Raise* keeps a legitimate population working, at the cost of a challenge they will meet once per session and then forget about — which is also why it produces weaker evidence in an audit.

## Anti-Patterns

1. Using a session security level as a substitute for field-level security, sharing, or encryption.
2. Setting the login-level requirement on a profile whose users own `@future`, Batch, or Scheduled Apex.
3. Enabling any of this without first confirming which login methods sit in the High Assurance column of Session Settings.
4. Leaving integration and API-only profiles inside the scope, where no identity-verification challenge can ever be satisfied.
5. Writing the Apex check as "elevated if the value equals the high literal", which fails open on any unexpected value.
6. Treating the Setup screen as evidence of enforcement instead of querying `AuthSession` for the sessions that were actually created.

## Official Sources Used

- Apex Reference Guide — `Auth.SessionManagement` class (method list, `getCurrentSession()` map keys including `SessionSecurityLevel`, `setSessionLevel`, `generateVerificationUrl`, `getRequiredSessionLevelForProfile`) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Auth_SessionManagement.htm — used to replace the fabricated `UserInfo.getSessionSecurityLevel()` call and to source every Apex signature in this skill.
- Apex Reference Guide — `System.UserInfo` methods — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_userinfo.htm — used to confirm that `getSessionId()` is the only session method on `UserInfo` and that no session-security accessor exists there.
- Apex Reference Guide — `Auth.VerificationPolicy` enum — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_enum_Auth_VerificationPolicy.htm — used for the `HIGH_ASSURANCE` policy argument to `generateVerificationUrl`.
- Object Reference — `AuthSession` — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_authsession.htm — used for the `SessionSecurityLevel` picklist wording ("Standard or High"), `SessionType`, `LoginHistoryId`, and the note that non-admins see only their own sessions.
- Salesforce Security Guide — Require High-Assurance Session Security for Sensitive Operations — https://help.salesforce.com/s/articleView?id=xcloud.security_auth_require_ha_session.htm — used for the Setup → Identity Verification → Session Security Level Policies path, the list of gateable operations, and the raise-or-block actions.
- Salesforce Security Guide — Modify Session Security Settings — https://help.salesforce.com/s/articleView?id=xcloud.admin_sessions.htm — used for the Session Security Levels login-method mapping and its documented per-method defaults.
- Salesforce Knowledge — "High Assurance" Level Blocks Asynchronous Apex — https://help.salesforce.com/s/articleView?id=000392426&type=1 — used for the async-Apex conflict and the Multi-Factor Authentication for User Interface Logins workaround.
- Salesforce Help — Edit Session Settings in Profiles — https://help.salesforce.com/s/articleView?id=platform.users_profiles_session.htm — used for the profile/permission-set "Session Security Level Required at Login" control.
