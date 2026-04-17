---
name: session-high-assurance-policies
description: "Enforce step-up authentication for sensitive pages/objects using High Assurance session level and login flow policies. NOT for initial MFA enrollment UX."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "step up auth for sensitive record"
  - "high assurance session salesforce"
  - "require mfa to view ssn field"
  - "session level policy"
tags:
  - session
  - mfa
  - high-assurance
inputs:
  - "Which objects/pages require step-up"
  - "current login policies"
outputs:
  - "Session Settings policy"
  - "profile/permission-set config"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Session High Assurance Policies

Salesforce sessions have a Security Level: Standard or High Assurance. A High Assurance Session Policy forces re-authentication with MFA when a user accesses a flagged object, report, or page. This skill configures the policy and tests it against the sensitive records.

## When to Use

Records with regulated or high-value data (SSN, bank account, salary) that should not be readable with a stolen cookie. Not for everything — user experience will suffer.

Typical trigger phrases that should route to this skill: `step up auth for sensitive record`, `high assurance session salesforce`, `require mfa to view ssn field`, `session level policy`.

## Recommended Workflow

1. Identify the 1-3 objects/pages that justify High Assurance (scope carefully).
2. Setup → Session Settings → Policies: set the session level for the profile or permission set to 'High Assurance'.
3. For records: use a Login Flow or an Apex service that checks UserInfo.getSessionSecurityLevel() and redirects to MFA if Standard.
4. Write a test: log in from a non-MFA device, navigate to the record, confirm the step-up prompt.
5. Document the UX impact and communicate to the affected user population.

## Key Considerations

- Session security level is per session, not per action; once stepped up the user stays High Assurance until logout.
- Connected apps can be configured with High Assurance requirements separately.
- Mobile SDK apps must support the Refresh Token flow with device PIN to honor High Assurance.
- High Assurance ≠ MFA; it means the session was created with a secondary factor.

## Worked Examples (see `references/examples.md`)

- *Require HA to view SSN field* — HR org.
- *Connected app HA requirement* — Mobile app used by auditors.

## Common Gotchas (see `references/gotchas.md`)

- **Org-wide HA breaks integrations** — API-only integration users fail login.
- **Step-up on report** — Users hit the prompt on every refresh.
- **Mobile SDK crash** — App fails to refresh.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Applying HA org-wide
- Forgetting integration user profiles
- Using HA as a substitute for field-level security

## Official Sources Used

- Apex Developer Guide — Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security.htm
- Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Session Security Levels — https://help.salesforce.com/s/articleView?id=sf.security_hap_session.htm
- CSP and Trusted URLs — https://help.salesforce.com/s/articleView?id=sf.security_csp_overview.htm
- API Only User Profile — https://help.salesforce.com/s/articleView?id=sf.users_profiles_api_only.htm
- Privacy Center and DSR — https://help.salesforce.com/s/articleView?id=sf.privacy_center_overview.htm
