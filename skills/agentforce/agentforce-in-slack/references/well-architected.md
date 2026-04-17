# Well-Architected Notes — Agentforce In Slack

## Relevant Pillars

- **Security** — This skill's core concern. The public vs. private action permission model is a security control. Private actions enforce Salesforce record-level security by resolving each Slack user's identity to a Salesforce user and executing actions under that user's permission set. Without this control, a Slack user could invoke agent actions that surface records they lack Salesforce access to see. The Einstein Trust Layer applies to all Slack action traffic, including canvas content and DM payloads.

- **User Experience** — Slack-native actions (Create Canvas, Send DM, Look Up User) directly shape how users experience the agent in their natural workspace tool. Choosing the right action for the right workflow (e.g., canvases for structured summaries, DMs for alerts, message history search for context retrieval) determines whether the agent is genuinely useful or just another chat interface.

- **Trust** — The identity mapping layer between Slack and Salesforce is foundational to user trust. Users must be confident that the agent only shows them their own data, not data belonging to other users. The private action / identity proxy design achieves this. Trust Layer logs provide the audit trail that confirms each action was executed under the correct identity.

- **Reliability** — The General Slack Actions topic dependency means that if the topic is accidentally removed from an agent during a configuration change, all Slack-native actions fail silently. Reliability considerations include: ensuring the topic is present in post-deployment validation, monitoring for private action authorization failure rates, and designing graceful degradation for unmapped users.

- **Operational Excellence** — Identity mapping requires ongoing maintenance: new users must be mapped at hire, offboarded users' mappings should be reviewed, and production deployments must explicitly re-provision mappings. Building these as checklist items in onboarding and deployment processes prevents silent failures from mapping gaps.

## Architectural Tradeoffs

**Private actions vs. public actions for Salesforce-backed data:**
Private actions are more secure but require identity mapping overhead and introduce a "first-use friction" where users must complete an OAuth flow. Public actions are simpler but execute under the integration user's broad permissions, which is inappropriate for user-specific or sensitive data. The tradeoff is between security posture and deployment complexity. For internal employee-facing agents where Salesforce data is sensitive (pipeline, HR, cases), private actions are required. For FAQ-style agents that only surface non-sensitive shared content, public actions are acceptable.

**Managed Slack actions vs. custom Slack API integrations:**
The General Slack Actions topic provides four managed actions with built-in Trust Layer coverage, no OAuth token management, and Salesforce-supported maintenance. Custom Slack API integrations give more flexibility (e.g., custom message formatting with Block Kit, webhook-driven workflows) but at the cost of Trust Layer bypass, manual token management, and maintenance ownership. The tradeoff is flexibility vs. compliance posture. For regulated orgs or orgs with strict data governance, the managed path is strongly preferred.

**Canvas vs. plain text agent responses:**
Canvases provide rich, structured, persistent content that users can share and edit. Plain text responses are immediate but ephemeral and unformatted. Canvases require a Slack paid plan. The tradeoff is richness vs. accessibility. Design canvas-based workflows only when the richer format is essential to the use case (e.g., meeting summaries, project briefs) and always provide a graceful fallback for Free-plan workspaces.

## Anti-Patterns

1. **Assuming Slack-native actions are available after Slack deployment without explicitly adding the General Slack Actions topic** — the deployment flow does not add the topic automatically. This is the most common configuration mistake. Every Slack deployment checklist must include "Add General Slack Actions topic in Agent Builder" as an explicit post-deployment step.

2. **Using public action scope for user-specific Salesforce data** — configuring an action as public when it queries records specific to the requesting user (e.g., "my open cases", "my quota attainment") means all users see the same data (the integration user's view) or the action must implement its own identity filtering, which is fragile and bypasses Salesforce's native permission model. Always use private action scope for user-specific Salesforce data queries.

3. **Expecting sandbox identity mappings to survive a production deployment** — identity mappings are data, not metadata. They are not included in any metadata deployment vehicle. Teams that test identity mapping thoroughly in sandbox and then skip re-provisioning in production will have all private actions fail on go-live day. Include identity mapping re-provisioning as an explicit production go-live step.

## Official Sources Used

- Connect an Agent to Slack (Agentforce for Slack Setup) — https://help.salesforce.com/s/articleView?id=ai.agent_deploy_emp_slack.htm
- Customizing Agentforce Agents with Custom Slack Actions — https://docs.slack.dev/ai/customizing-agentforce-agents-with-custom-slack-actions
- Set Up and Manage Agentforce in Slack — https://slack.com/help/36218109305875
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
