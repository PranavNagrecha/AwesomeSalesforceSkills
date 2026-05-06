# Well-Architected Notes — SAML SSO Troubleshooting

## Relevant Pillars

- **Security** — SSO is a security control; broken SSO is a security
  incident, not just a UX problem. Diagnostic shortcuts that weaken
  the configuration (e.g. extending assertion lifetime to 24 hours)
  trade real security for convenience.
- **Reliability** — SSO failures are typically time-pressured (users
  cannot work). The diagnostic loop must be runnable under
  pressure, which requires the runbook to be written before the
  incident.
- **Operational Excellence** — Cert rotation is a recurring
  operational task. Treating each rotation as an emergency rather
  than a scheduled change predicts more incidents.

## Architectural Tradeoffs

- **IdP-initiated vs SP-initiated.** IdP-initiated is simpler for
  users (click the app tile in Okta / OneLogin / Azure AD). SP-
  initiated supports deep-linking via RelayState. Most enterprises
  enable both.
- **Federation Id vs Username matching.** Federation Id decouples
  Salesforce Username from IdP NameID and is the more flexible
  choice. Username matching is simpler but ties the two values
  together for life.
- **JIT Provisioning vs SCIM.** JIT auto-creates users on first
  login from assertion attributes; SCIM provisions users
  proactively via the IdP's user-management API. SCIM is more
  reliable; JIT is faster to set up.
- **Encrypted assertions vs signed-only.** Encryption protects
  attribute confidentiality. Signed-only is simpler to debug. For
  most enterprise SSO, signed-only is sufficient because TLS
  protects the transport.

## Anti-Patterns

1. **Cert-rotation-as-emergency.** Schedule rotations in advance.
2. **Long-lived assertions.** Address clock skew instead.
3. **JIT without attribute mapping.** Creates broken users.
4. **Treating SAML Assertion Validator as authoritative on IdP
   correctness.**
5. **Mixing IdP-initiated and SP-initiated configuration in the same
   IdP app entry.**

## Official Sources Used

- About Single Sign-On — https://help.salesforce.com/s/articleView?id=sf.sso_about.htm&type=5
- Configure SAML Settings for SSO — https://help.salesforce.com/s/articleView?id=sf.sso_saml.htm&type=5
- Validate Single Sign-On Settings (SAML Assertion Validator) — https://help.salesforce.com/s/articleView?id=sf.sso_validate.htm&type=5
- Login History — https://help.salesforce.com/s/articleView?id=sf.users_login_history.htm&type=5
- Just-in-Time Provisioning for SAML — https://help.salesforce.com/s/articleView?id=sf.sso_jit.htm&type=5
- Salesforce Well-Architected Trustworthy — https://architect.salesforce.com/well-architected/trusted/secure
