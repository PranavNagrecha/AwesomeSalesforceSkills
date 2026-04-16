# Well-Architected Notes — Flow for Slack

## Relevant Pillars

- **Reliability** — Slack actions fail silently when prerequisites are missing (package, permission set, OAuth token). Fault path monitoring must be configured on all flows using Slack actions. Flow fault emails should route to an operations mailbox.
- **Security** — Slack messages sent from Flow are authenticated as the running user or auto-process user. Sensitive Salesforce data sent to Slack channels becomes accessible to all channel members. Apply the same field-level governance thinking as for record previews.
- **Operational Excellence** — The prerequisite stack (managed package + org connection + permission set + OAuth token) creates operational dependencies. Document and monitor all four prerequisites. Changes to any layer (Slack workspace admin revokes token, permission set removed) silently break Flow notifications.

## Architectural Tradeoffs

**Flow Core Actions vs. Custom Slack App:** Flow Core Actions are no-code, configurable, and maintained by Salesforce. They cover the most common use cases (messaging, channel management). For complex Slack UX (modals, Block Kit layouts, interactive message components beyond buttons), a custom Slack app via the Slack SDK is required. Choose based on UX complexity requirements.

**Slack Notification vs. Salesforce Notification:** Slack notifications from Flow are conversational and persistent in channels. Salesforce in-app notifications (Notification Builder) are Salesforce-native but not visible outside the app. For cross-functional teams who live in Slack, Flow-to-Slack is higher-impact than Salesforce notifications.

**Send Slack Message vs. Send Message to Launch Flow:** Send Slack Message is one-way push. Send Message to Launch Flow adds an interactive button that triggers a Salesforce Flow when clicked, enabling lightweight approval workflows without a full screen flow. Use the interactive version when user acknowledgment or decision input is required.

## Anti-Patterns

1. **Slack Actions Without Fault Path Handling** — Slack actions that fault at runtime (permission set missing, OAuth revoked) without a configured fault path silently drop the notification. Always configure fault paths that send an admin alert or log the failure.

2. **Hardcoded Channel Display Names Instead of Channel IDs** — Channel display names can be renamed by Slack admins. Hardcoded display names in Flow may stop routing to the correct channel after a rename. Use Slack channel IDs (format: CXXXXXXXXXX) which are immutable.

3. **Sending Sensitive Field Values to Public Channels** — Salesforce data merged into Slack messages becomes visible to all channel members and potentially persisted in Slack exports. Avoid sending PII, financial terms, or privileged legal information to public or large private channels.

## Official Sources Used

- Slack Flow Core Actions — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_actions_slack.htm
- Use Flows with Slack — https://help.salesforce.com/s/articleView?id=sf.flow_build_use_flows_with_slack.htm
- Flow Core Actions for Slack: Send Slack Message — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_actions_slack_send_message.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
