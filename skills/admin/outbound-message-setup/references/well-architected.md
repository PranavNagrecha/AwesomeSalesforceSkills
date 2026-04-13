# Well-Architected Notes — Outbound Message Setup

## Relevant Pillars

- **Reliability** — At-least-once delivery semantics with 24-hour retry window provide strong delivery guarantees for transient endpoint failures. The acknowledgment mechanism prevents false positives — the message is only considered delivered when the SOAP Ack:true is received. External systems must be idempotent (handle duplicate deliveries) because at-least-once means duplicates can occur even on successful retry.
- **Operational Excellence** — Monitoring the Pending queue in Setup > Process Automation > Outbound Messages is the primary operational health check. Messages stuck in pending indicate endpoint or acknowledgment failures and require immediate investigation.

## Architectural Tradeoffs

**Outbound Messages vs. Platform Events:** Outbound Messages are no-code and support at-least-once SOAP delivery but are limited to Workflow Rules (being phased out), SOAP format only, and single-record payloads. Platform Events support Flow/Apex triggering, JSON/custom payloads, and fan-out to multiple subscribers, but require the receiving system to connect to the Salesforce event bus (CometD) rather than passively receiving HTTP pushes. For new integrations, Platform Events are the recommended path.

**Outbound Messages vs. Apex HTTP callouts:** Apex callouts provide full control over request format (JSON, XML, custom), retry logic, error handling, and payload construction, but require code and consume Salesforce governor limits. Outbound Messages are no-code and consume no Apex governor limits but are constrained to SOAP format and Workflow Rule triggering.

## Anti-Patterns

1. **External system returning HTTP 200 without SOAP acknowledgment** — The most common and most disruptive Outbound Message failure. Results in hundreds of duplicate deliveries over 24 hours before messages are dropped. Always provide the external development team with the exact SOAP acknowledgment template.

2. **Using Outbound Messages for high-volume or batch scenarios** — Outbound Messages deliver one record at a time via SOAP. For high-volume change notification (thousands of records per hour), the SOAP overhead and sequential delivery model creates latency and queue depth issues. Use Change Data Capture or Platform Events for high-volume scenarios.

3. **No monitoring of the pending queue** — Deploying Outbound Messages to production without any monitoring of the pending queue. Messages can silently drop after 24 hours with no notification. Schedule periodic queue checks or implement external monitoring via the Salesforce API.

## Official Sources Used

- Salesforce Help — Setting Up Outbound Messaging — https://help.salesforce.com/s/articleView?id=sf.workflow_outbound_messaging.htm&type=5
- Metadata API Developer Guide — WorkflowOutboundMessage — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_workflowoutboundmessage.htm
- Integration Patterns and Practices — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
