# Well-Architected Notes - Org Hardening And Baseline Config

## Relevant Pillars

- **Security** - baseline browser, session, network, and trust controls define the minimum org posture.
- **Operational Excellence** - hardening succeeds only when there is review cadence and exception ownership.

## Architectural Tradeoffs

- **Strict defaults vs operational convenience:** tighter posture versus more short-term friction.
- **Open trust exceptions vs managed exceptions:** faster unblock versus controllable risk.
- **One-time review vs recurring cadence:** lower immediate effort versus sustainable posture.

## Anti-Patterns

1. **Health Check only** - a score is not a hardening program.
2. **Unowned trusted-site exceptions** - hidden risk accumulates silently.
3. **Critical updates as someone else's problem** - operational debt eventually becomes security debt.

## Official Sources Used

- Salesforce Security Guide, Summer '26 (release 262): Security Health Check (baselines, risk groups, Fix Risks limitations, custom baselines), Device Activation, Session Security, Profiles > Login IP Ranges and "Enforce login IP ranges on every request" - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf
- Metadata API Developer Guide, Summer '26: SecuritySettings (NetworkAccess replace semantics, PasswordPolicies, SessionSettings clickjack, CSRF, `requireHttpOnly`, `enforceIpRangesEveryRequest`, `sessionTimeout`, declarative sample and package.xml), CspTrustedSite, CorsWhitelistOrigin, ProfileSessionSetting, ProfilePasswordPolicy - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Salesforce CLI 2.151.7 source-deploy-retrieve metadata registry (directory and suffix names for `cspTrustedSites`, `corsWhitelistOrigins`, `profileSessionSettings`), local install at /usr/local/lib/sf/node_modules/@salesforce/source-deploy-retrieve/lib/src/registry/metadataRegistry.json
- Salesforce CLI 2.151.7 local `--help` output for `project retrieve start` and `project deploy start`
