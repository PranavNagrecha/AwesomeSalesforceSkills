# Well-Architected Notes — Session High Assurance Policies

## Relevant Pillars

| Pillar | How this skill contributes |
|---|---|
| **Security** | Step-up authentication narrows the window in which a stolen password alone is useful. A Standard session that reaches a gated operation is stopped or challenged rather than served. |
| **Reliability** | The dominant failure mode here is self-inflicted: a login-level requirement applied to a profile that owns asynchronous Apex is reported (Help KB, UNVERIFIED (2026-10-20)) to take out batch and scheduled jobs with no login-shaped error to trace. Scoping is a reliability control, not a nicety. |
| **Operational Excellence** | The configuration is silently reversible from one Session Settings screen, so the design is incomplete without a detection query that measures the sessions actually produced. |

## Architectural Tradeoffs

- **Login-level requirement vs in-session step-up.** Requiring High Assurance at login is simpler to explain and audit, but it applies to every session those users open — including the ones that host asynchronous work. In-session step-up (`Auth.SessionManagement.generateVerificationUrl`) is narrower and keeps async contexts clean, at the cost of application code that must be maintained and tested on every entry point.
- **Declarative policy vs Apex gate.** A Session Security Level Policy is enforced by the platform at the named operation rather than only where you wrote code (UNVERIFIED (2026-10-20): API-path coverage is Help-only). An Apex gate covers only the entry points you wrote it on. Prefer the policy whenever the requirement maps to one of the Help-listed operations (UNVERIFIED (2026-10-20): the list is not in the corpus), and be explicit in the design about the coverage you lose when it does not.
- **Session level vs data-layer controls.** Elevating the session is cheap and reversible; encrypting a field or tightening field-level security is neither. The session level is the right control for "who may reach this surface" and the wrong control for "who may read this value" — the two must be designed together, not traded against each other.
- **Blocking vs raising.** *Block* is unambiguous and produces no support load for a population that has no business in the operation. *Raise* keeps a legitimate population working, at the cost of a challenge they will meet once per session and then forget about — which is also why it produces weaker evidence in an audit.

## Anti-Patterns

1. Using a session security level as a substitute for field-level security, sharing, or encryption.
2. Setting the login-level requirement on a profile whose users own `@future`, Batch, or Scheduled Apex.
3. Enabling any of this without first confirming which login methods sit in the High Assurance column of Session Settings.
4. Leaving integration and API-only profiles inside the scope, where no identity-verification challenge can ever be satisfied.
5. Writing the Apex check as "elevated if the value is not `STANDARD`", which fails open on a `LOW` session (apexref 262 L11901-11906); gate on an exact `HIGH_ASSURANCE` match instead.
6. Treating the Setup screen as evidence of enforcement instead of querying `AuthSession` for the sessions that were actually created.

## Official Sources Used

- Apex Reference Guide (262) — `Auth.SessionManagement` method entries (apexref 262 L11397-11831), `getCurrentSession()` example with `SessionSecurityLevel=STANDARD` (L11472-11490), `setSessionLevel` usage and test failure (L11711-11713), `Auth.SessionLevel` LOW / STANDARD / HIGH_ASSURANCE (L11891-11912); `UserInfo.getSessionId()` (L243284).
- Object Reference (264) — `AuthSession.SessionSecurityLevel` "Standard or High, depending upon the authentication method used" (obj 264 L47595).
- Metadata API Developer Guide (264) — `ProfileSessionSetting.requiredSessionLevel` and the `SessionSecurityLevel` enumeration incl. LOW (api_meta 264 L101448-101530); ConnectedApp session policy `Block` / `RaiseSessionLevel` and JWT-flow blocking (L37955-37970).
- Platform Events Developer Guide (264) — identity-verification triggers `ProfilePolicy` (profile's "Session security level required at login") and `TwoFactorAuthentication` (MFA for User Interface Logins permission) (platform_events 264 L20411-20415).
- Not corpus, used only for claims marked UNVERIFIED: Help — Require High-Assurance Session Security for Sensitive Operations (https://help.salesforce.com/s/articleView?id=xcloud.security_auth_require_ha_session.htm); Modify Session Security Settings (https://help.salesforce.com/s/articleView?id=xcloud.admin_sessions.htm); KB 000392426 "High Assurance" Level Blocks Asynchronous Apex (https://help.salesforce.com/s/articleView?id=000392426&type=1).
