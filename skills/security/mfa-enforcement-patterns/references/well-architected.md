# Well-Architected Notes — MFA Enforcement

## Relevant Pillars

- **Security** — MFA is the single most impactful control against
  credential-based compromise.
- **Operational Excellence** — exceptions and integration migration are
  ongoing ops, not one-time work.

## Architectural Tradeoffs

- **Salesforce MFA vs IdP MFA:** delegating to the IdP centralises the
  UX but requires correct assertion of auth context.
- **Connected App vs exempted integration user:** Connected App is more
  work upfront and safer long-term.
- **Short session lifetime vs MFA friction:** shorter sessions reduce
  session-theft risk but increase MFA prompts; pick per risk tier.

## Exception Hygiene

- Mandatory expiry.
- Named owner.
- Monthly review.
- Zero "permanent" exceptions.

## Official Sources Used

- MFA Overview —
  https://help.salesforce.com/s/articleView?id=sf.mfa_require_user_to_login.htm
- MFA with SSO —
  https://help.salesforce.com/s/articleView?id=sf.mfa_with_sso.htm
