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

- Salesforce Security Guide - https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Security Health Check - https://help.salesforce.com/s/articleView?id=sf.security_health_check.htm&type=5
- Critical Updates and Release Settings - https://help.salesforce.com/s/articleView?id=sf.release_updates.htm&type=5
