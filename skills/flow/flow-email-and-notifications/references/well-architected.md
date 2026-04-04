# Well-Architected Notes — Flow Email and Notifications

## Relevant Pillars

- **Reliability** — Notification actions can fail due to rate limits, expired credentials, or invalid recipient IDs. Every action must have a fault connector so failures are observable and recoverable. Notifications that fail silently become operational blind spots.
- **Operational Excellence** — Notification logic in Flows should be intentional and auditable. Each notification type (email, bell, SMS, Slack) has distinct limits, prerequisites, and failure modes. Documenting which channels are in use and what their limits are is part of maintainable automation.
- **Security** — Email actions can expose data if recipient fields are sourced from user-controlled input without validation. Custom Notification bodies accept merge fields from Flow variables — never include sensitive data (e.g., SSNs, passwords, financial details) in notification content because the delivery channel may not be audited or access-controlled.
- **Performance** — Custom Notifications have a 1,000/hour org-wide limit. Send Email actions count against daily org email limits. Notification-heavy flows on high-volume objects must be designed with these caps in mind to avoid degrading other automated communications in the org.
- **Scalability** — Flows that send one notification per record do not scale when triggered by bulk data loads. High-volume notifications should be evaluated for batching, async delivery (e.g., Platform Events), or re-routing to scheduled flows that aggregate before sending.

## Architectural Tradeoffs

### Send Email vs Email Alert

The Send Email core action is more flexible (fully dynamic recipients and body) but cannot use managed Classic Email Templates. Email Alerts support brand-controlled Letterhead templates but require the template to be fixed at design time in Setup. Choose Send Email when content must be fully dynamic; choose Email Alert (invoked from Flow) when brand and template governance matter more than flexibility.

### Custom Notification vs Email for Internal Alerts

Custom Notifications are synchronous, immediate, and visible without leaving Salesforce. They are the right choice for time-sensitive internal alerts to users who are active in the app. Email is better for asynchronous communication, audit trails, or recipients who are not active Salesforce users. Do not default to email for every notification; use the channel that matches the urgency and recipient behavior.

### Native Actions vs Apex Callouts for Third-Party Channels

For SMS and Slack, the native Flow actions require specific add-ons. In orgs without those licenses, third-party SMS or messaging via Apex callout is possible, but callouts from record-triggered synchronous flows are prohibited (callout-from-DML restriction). A Platform Event-based pattern (fire event in flow, handle in Apex subscriber) is required for callout-based alternatives. This significantly increases implementation complexity.

## Anti-Patterns

1. **No fault connector on notification actions** — Notification actions fail at runtime for reasons outside the developer's control (limits, expired tokens, invalid IDs). Flows without fault connectors either silently swallow failures or roll back transactions. Every Send Custom Notification, Send Email, Send SMS, and Post Message to Slack element must have a fault connector.

2. **Assuming Send Email supports Classic Email Templates** — Builders expect a template picker in the Send Email action because they are familiar with Email Alerts. When they do not find it, they either give up or try to pass a template ID in the body field. The correct pattern is to use a Text Template resource in Flow for dynamic body content, or to invoke an Email Alert if a managed template is required.

3. **Sending high-volume custom notifications in record-triggered flows without rate limit planning** — The 1,000/hour org limit is a hard cap that applies globally. A single high-volume record-triggered flow can exhaust this quota, preventing other flows from sending notifications. Always calculate peak notification rates before go-live and design async alternatives for high-volume scenarios.

## Official Sources Used

- Salesforce Help — Flow Core Action: Send Custom Notification — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_actions_sendcustomnotif.htm&type=5
- Salesforce Help — Flow Core Action: Send Email — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_actions_sendemail.htm&type=5
- Salesforce Help — Custom Notification Builder — https://help.salesforce.com/s/articleView?id=sf.notif_builder_custom.htm&type=5
- Salesforce Help — Salesforce for Slack — https://help.salesforce.com/s/articleView?id=sf.slack_setup_salesforce_for_slack.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Flow Reference — https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
