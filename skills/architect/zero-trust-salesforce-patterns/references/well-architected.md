# Well-Architected Notes — Zero-Trust Salesforce Patterns

## Relevant Pillars

- **Security (Trusted)** — This is the central pillar. Zero trust as
  an architecture pattern composes Salesforce's security primitives
  (High-Assurance Session, Login Flow, RTEM + Transaction Security
  Policies, Permission Set Group + Muting, Mobile Security) into a
  layered posture that satisfies "verify explicitly, least privilege,
  assume breach". No single primitive covers all three principles; the
  composition is the value.
- **Operational Excellence** — A defensible zero-trust posture needs a
  quarterly review cadence, an explicit residual-risk register (CAEP
  gap, in-session device-trust gap), and clear ownership boundaries
  between the IdP team (device trust, conditional access) and the
  Salesforce team (PSG, RTEM, Login Flow). Without operational
  discipline the controls drift; muting PSs get rolled back, JIT-grant
  unassign jobs get disabled, TSPs get muted "temporarily".

## Architectural Tradeoffs

- **High-Assurance Session at Profile vs PSG.** Profile-level forces
  step-up too aggressively and breaks routine work. PSG-level fires
  step-up only when the user exercises the high-blast right. PSG-level
  is the right grain for almost every real case.
- **Login Flow vs RTEM + TSP for verification.** Login Flow is
  session-start; RTEM + TSP is in-session. They are complementary, not
  substitutes. Architectures that pick one and call it done lose
  either continuous verification (Login Flow only) or device-aware
  admission (RTEM only).
- **Profile minimization vs PSG + Muting for least privilege.** Profile
  rewrites are multi-quarter, break adjacent integrations, and risk
  reverting under operational pressure. PSG + Muting is reversible and
  does not touch Profiles. Both have a place — Profile minimization
  shrinks the static surface; PSG + Muting handles the dynamic policy.
- **Mobile Security vs IdP-side device trust.** Mobile Security is a
  Salesforce-native MDM signal for the Salesforce mobile app. IdP-side
  device trust (Azure AD CA, Okta Device Trust, Ping) is the desktop
  counterpart, consumed by Login Flow. Both are needed; neither alone
  is enough.
- **Synchronous block vs detect-and-respond.** TSPs offer synchronous
  blocking on supported RTEM events; for unsupported events
  (`IdentityVerificationEvent`, `MobileEmailEvent`) the only option is
  detect-and-respond via Apex/Flow subscribers. The architect must
  document which threats fall in each category.

## Anti-Patterns

1. **Single-leg posture.** "MFA only", "IP allowlist only", "Shield
   only", or "SSO only" all fail the same audit question: where is
   continuous verification? A defensible zero-trust posture composes
   at least one control from each of the four legs in SKILL.md.
2. **Profile-level High Assurance.** Forces step-up on routine work,
   gets rolled back under help-desk pressure, then there is nothing.
   Use PSG-level instead.
3. **JIT grant without scheduled revocation.** Turns "JIT" into
   "permanent" inside a quarter. Always pair the assign with a
   scheduled unassign in the same atomic transaction.
4. **Treating Salesforce Mobile Security as the whole device-trust
   answer.** It only covers the mobile app. Desktop device trust is
   an IdP problem and must be configured separately.

## Official Sources Used

- Salesforce Well-Architected — Trusted (Secure) — https://architect.salesforce.com/well-architected/trusted/secure
- Enhanced Transaction Security Policy Types — https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/security_etm_event_types.htm
- Real-Time Event Monitoring — https://developer.salesforce.com/docs/atlas.en-us.real_time_monitoring.meta/real_time_monitoring/rtem_intro.htm
- Require High-Assurance Session Security — https://help.salesforce.com/s/articleView?id=sf.security_auth_require_ha_session.htm
- Login Flows — https://help.salesforce.com/s/articleView?id=sf.security_login_flow.htm
- Permission Set Groups + Muting Permission Sets — https://help.salesforce.com/s/articleView?id=sf.perm_set_groups.htm
- Salesforce Mobile Application Security — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_developer_guide.meta/salesforce_app_developer_guide/salesforce_app_security.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
