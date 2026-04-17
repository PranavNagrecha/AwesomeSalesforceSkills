# Well-Architected Notes — Slack Connect Patterns

## Relevant Pillars

- **Security** — The primary pillar for Slack Connect. Data loss prevention, split-ownership retention, channel history exposure on conversion, and DLP tool selection by plan tier are all security decisions. The practitioner must confirm DLP controls exist before the first external message is sent.
- **Operational Excellence** — Admin acceptance workflows, invite link expiration handling, partner plan tier monitoring, and quarterly compliance reviews all fall under operational excellence. The 14-day invite expiry and silent DLP removal on plan downgrade require proactive operational controls.
- **Reliability** — Slack Connect channel availability depends on both organizations maintaining paid plans. A partner's plan cancellation or downgrade can break assumed DLP guarantees. Reliability governance includes plan-tier monitoring and contractual notification requirements.
- **Performance** — Not a primary concern for Slack Connect channel communication. Not applicable.
- **Scalability** — The 250 external organization hard limit is the key scalability constraint. Architecture decisions for large multi-party channels must account for this ceiling.

## Architectural Tradeoffs

**Native DLP vs. Third-Party DLP:** Enterprise Grid organizations gain native PCRE-based DLP at no additional cost. Organizations on lower tiers must invest in a third-party DLP vendor (Nightfall, Symantec DLP, Microsoft Purview) and maintain a Slack Events API subscription. Third-party solutions offer richer classification capabilities (ML-based entity detection) but require vendor management and additional cost. The tradeoff is operational simplicity (native) vs. regulatory coverage depth (third-party).

**New Channel vs. Channel Conversion:** Creating a new channel for Slack Connect is always architecturally safer than converting an existing channel. The tradeoff is continuity of conversation history (conversion) vs. preventing unintended history exposure (new channel). In regulated environments, always choose a new channel.

**Slack Connect vs. Alternative Collaboration Tools:** Slack Connect is appropriate when both organizations already use Slack on paid plans and the collaboration is conversational. If the partner organization uses Microsoft Teams, the correct architecture is a Teams Connect channel (or a shared channel in Teams) rather than attempting to bridge Slack Connect across platform boundaries, which is unsupported.

## Anti-Patterns

1. **Assuming DLP Coverage Is Symmetric** — Configuring DLP rules in one organization's Slack admin console and assuming they apply to the partner organization's messages in the shared channel. Each workspace's DLP rules apply only to that workspace's members' messages. Both sides must independently configure and maintain their DLP controls.

2. **Treating Slack Connect as Salesforce-to-Salesforce Integration** — Proposing a Slack Connect channel as the mechanism for synchronizing Salesforce records between two orgs. Slack Connect provides human communication, not programmatic data exchange. Record sync between Salesforce orgs requires Salesforce-to-Salesforce (S2S) integration, Outbound Messages, or middleware.

3. **Using a Retention Policy Delete as a Compliance Control in Shared Channels** — Relying on a short retention policy to ensure sensitive information is removed from a Slack Connect channel. Deletion by one organization does not remove the partner's copy. Short retention policies create a false sense of data minimization in cross-org contexts.

## Official Sources Used

- Slack Connect guide: Work with external organizations — https://slack.com/help/articles/360035280511 (channel sharing setup, 250-org limit, admin acceptance requirement, paid plan requirement)
- How data management features apply to Slack Connect — https://slack.com/help/articles/360035622694 (split-ownership retention, deletion asymmetry, eDiscovery scope)
- Slack data loss prevention — https://slack.com/help/articles/1500001560242 (native DLP availability by plan tier, PCRE rules, Enterprise Grid/Enterprise+ restriction)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (pillar framing)
