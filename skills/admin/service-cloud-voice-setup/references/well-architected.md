# Well-Architected Notes — Service Cloud Voice Setup

## Relevant Pillars

- **Security** — Service Cloud Voice uses OAuth 2.0 between Salesforce and Amazon Connect, with IAM roles created by the provisioning wizard. Admins must ensure IAM roles follow least-privilege principles. The Amazon Connect instance should not be publicly accessible via the AWS console to unauthorized staff; access should be governed by AWS IAM policies. VoiceCall records contain PII (caller phone numbers, transcripts) and must be protected by field-level security and object permissions.
- **Reliability** — Amazon Connect has its own service availability SLA (99.99% for the managed service). Contact flows must handle Amazon Connect unavailability gracefully — configure fallback routing or error branches in contact flows so calls are not silently dropped if the Salesforce connection is interrupted. After Conversation Work Time prevents agent overload, contributing to sustained reliability under high call volume.
- **Operational Excellence** — The guided provisioning wizard reduces operational risk by automating AWS infrastructure setup. Post-setup, operational excellence requires monitoring VoiceCall record creation rates, transcript availability rates, and ACW duration compliance. Salesforce's built-in reporting on VoiceCall objects supports call volume dashboards without additional tooling.
- **Performance** — Real-time transcription introduces latency; the Kinesis Video Stream must be sized appropriately for the concurrent call volume. Omni-Channel capacity weights for voice should be set lower than for asynchronous channels (chat, email) since calls are synchronous and cannot be queued the same way.
- **Scalability** — Amazon Connect scales automatically for call volume within AWS service limits. Salesforce Omni-Channel queue depth and agent capacity are the constraining factors on the Salesforce side. Scale testing should include peak call volume scenarios with real agents in ACW to confirm routing does not back up.

## Architectural Tradeoffs

**Guided wizard provisioning vs. manual AWS setup:** The guided wizard is faster, safer, and requires no AWS expertise. It installs Salesforce-managed contact flows that handle the critical handoff between Amazon Connect and Salesforce Omni-Channel. The tradeoff is reduced control over the initial AWS infrastructure shape. Teams with complex existing AWS architectures (specific VPC configurations, custom IAM boundaries) may need to use the import path, which requires more AWS expertise but preserves existing infrastructure.

**Native Service Cloud Voice vs. Open CTI with a third-party telephony provider:** Service Cloud Voice provides deeper integration (VoiceCall records, real-time transcription, Einstein AI features) but requires Amazon Connect specifically. Open CTI supports any telephony provider but delivers only basic call control with no native transcript or AI features. Teams already invested in a non-Amazon telephony platform face a re-platforming cost to gain native Voice features.

**Real-time transcription always-on vs. on-demand:** Enabling transcription for all calls increases Amazon Connect data streaming costs (Kinesis Video Streams pricing). Organizations with high call volume should evaluate whether transcription is needed for all calls or only for flagged/escalated calls. Selective transcription requires contact flow logic in Amazon Connect to conditionally start the media stream.

## Anti-Patterns

1. **Bypassing the provisioning wizard for manual Amazon Connect configuration** — Manually creating an Amazon Connect instance in AWS and attempting to connect it to Salesforce without the wizard's IAM trust configuration results in a non-functional integration. Calls may reach Amazon Connect but cannot be handed off to Salesforce agents because the required trust relationship and managed contact flows are missing. Always use the Salesforce-guided wizard as the entry point.

2. **Sharing one Amazon Connect instance across multiple Salesforce orgs** — Attempting to link a single Amazon Connect instance to both a production org and a sandbox violates the one-to-one constraint enforced by Salesforce's OAuth application model. This leads to routing events firing against the wrong org and potential VoiceCall record corruption. Each Salesforce org must have its own dedicated Amazon Connect instance.

3. **Enabling transcription without validating the AWS Live Media Streaming prerequisite** — Toggling on Call Transcription in Salesforce Setup without first enabling Live Media Streaming in the Amazon Connect AWS console produces no errors but also no transcripts. Teams discover the misconfiguration late (often after Einstein features are already presented to end users) because there is no validation check at the point of configuration in Salesforce.

## Official Sources Used

- Set Up Service Cloud Voice with Amazon Connect — https://help.salesforce.com/s/articleView?id=sf.voice_setup_amazon_connect.htm
- Configure Call Transcription — https://help.salesforce.com/s/articleView?id=sf.voice_transcription_setup.htm
- Configure After Conversation Work Time — https://help.salesforce.com/s/articleView?id=sf.voice_acw_setup.htm
- Service Cloud Voice Best Practices Guide — https://help.salesforce.com/s/articleView?id=sf.voice_best_practices.htm
- Service Cloud Voice Overview — https://help.salesforce.com/s/articleView?id=sf.voice_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
