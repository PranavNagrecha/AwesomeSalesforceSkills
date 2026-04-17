---
name: api-only-user-hardening
description: "Provision and harden integration (API-only) users: no UI login, IP restrictions, minimum permission set, session lifetime, and monitoring. NOT for human admin account hardening."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "integration user setup salesforce"
  - "api only user profile"
  - "harden service account salesforce"
  - "restrict integration user ip"
tags:
  - integration
  - service-account
  - api
inputs:
  - "Integration name"
  - "required objects/fields"
  - "caller IP range"
outputs:
  - "User record + Profile + Permission Set Group + Connected App config"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# API-Only User Hardening

Integration users are the most common compromise vector because they have long-lived credentials and broad permissions. The hardened template is: API-Only profile (no UI), minimum permission set, IP range restriction, OAuth client-credential flow, 15-minute session, and Event Monitoring watchlist.

## When to Use

Any new external system-to-Salesforce connector. Also to retrofit existing integration users (one sweep per release).

Typical trigger phrases that should route to this skill: `integration user setup salesforce`, `api only user profile`, `harden service account salesforce`, `restrict integration user ip`.

## Recommended Workflow

1. Create Profile 'Salesforce API Only System Integrations' (or clone Minimum Access and flip API Only Enabled=true).
2. Assign a permission set with only the objects and fields the integration needs (principle of least privilege).
3. Set Login IP Ranges on the profile to the partner's outbound NAT CIDR — reject everything else.
4. Create a Connected App with OAuth Client Credentials flow (Spring '24+); bind it to this user; rotate client secret quarterly.
5. Add the user to an Event Monitoring or Shield Alert rule that flags unusual SOQL volumes or off-hours logins.

## Key Considerations

- API Only Profile license is a separate SKU — budget for it.
- Session Security High Assurance will block OAuth flows that lack MFA; configure accordingly.
- Client Credentials flow avoids user-impersonation pitfalls of the deprecated Username-Password flow.
- Never reuse an integration user across two integrations; accountability is lost.

## Worked Examples (see `references/examples.md`)

- *New ETL integration with Snowflake* — Daily 10M-row bulk extract.
- *Hardening an existing webhook receiver* — Legacy account has broad access.

## Common Gotchas (see `references/gotchas.md`)

- **Shared secret** — Two services share credentials; one compromise = both exposed.
- **No IP restriction** — Credential leak leads to data exfiltration from anywhere.
- **Password-expires on** — Integration silently breaks in 90 days.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Using a SysAdmin as the integration user
- Skipping IP restriction 'because OAuth'
- Password-expires on API-only users

## Official Sources Used

- Apex Developer Guide — Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security.htm
- Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Session Security Levels — https://help.salesforce.com/s/articleView?id=sf.security_hap_session.htm
- CSP and Trusted URLs — https://help.salesforce.com/s/articleView?id=sf.security_csp_overview.htm
- API Only User Profile — https://help.salesforce.com/s/articleView?id=sf.users_profiles_api_only.htm
- Privacy Center and DSR — https://help.salesforce.com/s/articleView?id=sf.privacy_center_overview.htm
