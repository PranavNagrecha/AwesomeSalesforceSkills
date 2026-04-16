# Well-Architected Notes — Slack Salesforce Integration Setup

## Relevant Pillars

- **Security** — Record preview cards render based on the Platform Integration User's page layout — NOT the Slack user's field-level security. Sensitive field exposure in Slack channels is a critical security risk requiring page layout governance on the Platform Integration User.
- **Operational Excellence** — The three-party handshake requires coordinated admin access across two platforms. Documenting the setup process, role requirements, and channel governance policies is essential for operational sustainability.
- **Reliability** — The integration depends on the Salesforce for Slack managed app's OAuth token remaining active. Token revocation by a Slack admin breaks the integration silently. Monitoring the connection status in Setup is required.

## Architectural Tradeoffs

**Salesforce for Slack App vs. Custom Slack App:** The managed Salesforce for Slack app provides out-of-the-box record sharing, search, and notifications without code. A custom Slack app provides full control over UX, data exposure, and business logic but requires significant development effort. For standard sales productivity use cases, the managed app is sufficient. For deeply customized workflows, consider a custom app via Slack SDK.

**Record Preview Governance vs. No Sharing:** Completely disabling record URL sharing in Slack eliminates the data exposure risk but removes a core productivity feature. A policy-based approach (governance rules defining which object types can be shared in which channel types) balances security and usability.

## Anti-Patterns

1. **Allowing Any Record to Be Shared in Any Channel** — Unrestricted record sharing exposes sensitive field data to all channel members regardless of their Salesforce permissions. Define and enforce a channel governance policy mapping record types to appropriate channel restrictions.

2. **Attempting Government Cloud Connection** — Government Cloud org connection to Slack is not supported. Proposing it as a configuration option wastes implementation effort. Identify org type early and route to alternative integration patterns.

3. **Skipping User Onboarding After Org Connection** — The org-level connection alone does not authorize individual users. Skipping the user personal account connection step results in poor adoption and support tickets claiming the integration "doesn't work."

## Official Sources Used

- Connect Salesforce and Slack — https://slack.com/help/articles/30754346665747
- Configure Salesforce for Use with Slack — https://slack.com/help/articles/360044038514
- Connect the Salesforce for Slack App to a Salesforce Org — https://help.salesforce.com/s/articleView?id=sf.slack_apps_digital_hq_setup.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
