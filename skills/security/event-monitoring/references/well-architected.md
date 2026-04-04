# Well-Architected Notes — Event Monitoring

## Relevant Pillars

- **Security** — This skill is primarily a Security capability. Event Monitoring provides the visibility layer required to detect threats, audit access, investigate incidents, and enforce behavioral policies. Without it, a Salesforce org is effectively operating blind with respect to user behavior at the data access layer. Transaction Security Policies move beyond detection into active enforcement — blocking operations or requiring step-up MFA when suspicious patterns are detected.

- **Operational Excellence** — Event Monitoring directly supports observability for operational health. Log analysis identifies performance degradation patterns (slow Apex executions, heavy VisualforceRequest loads), adoption gaps (unused features, underused reports), and system misuse. SIEM integration with EventLogFile enables continuous operational visibility rather than reactive incident response.

- **Reliability** — Moderate relevance. Threat detection events and Transaction Security policies can surface systemic issues (e.g., credential stuffing campaigns, bulk API abuse) before they degrade org availability. Monitoring Apex Unexpected Exception events via EventLogFile helps identify trigger failures affecting reliability.

- **Scalability** — Low direct applicability. EventLogFile volume scales automatically with org activity. Practitioners should be aware that high-volume orgs generate large log files; log download pipelines must handle multi-hundred-MB daily CSVs efficiently.

- **Performance** — Low direct applicability. Transaction Security Policy evaluation adds latency to evaluated operations (the `EvaluationTime` field on anomaly events measures this in milliseconds). For high-throughput APIs, policy evaluation overhead should be validated under load.

---

## Architectural Tradeoffs

### Batch vs. Real-Time

The central tradeoff in Event Monitoring architecture is between batch EventLogFile analysis and real-time streaming via RTEM.

| Dimension | EventLogFile (Batch) | RTEM (Real-Time) |
|---|---|---|
| Latency | 24+ hours | Seconds |
| Coverage | 70+ event types | ~15 core event types |
| Retention | 30 days (Shield), 1 day (free) | 72 hours on event bus |
| Enforcement | None (read-only) | Transaction Security Policies |
| Use case | Compliance, forensics, SIEM | Active defense, incident response |
| License | Event Monitoring add-on or Shield | Shield or Event Monitoring add-on |

Design guidance: treat the two approaches as complementary, not competing. RTEM handles active defense; EventLogFile handles audit trails and compliance reporting. Most mature implementations use both.

### Shield vs. Add-On

Salesforce Shield bundles Event Monitoring, Platform Encryption, and Field Audit Trail. The Event Monitoring add-on provides only Event Monitoring. Key differences for this skill:

- Hourly log files: Shield only
- Platform Encryption integration: Shield only
- Field Audit Trail: Shield only
- 30-day retention and 70+ event types: both Shield and add-on

If the primary requirement is event monitoring, the add-on may be sufficient. If the org also needs at-rest encryption of sensitive fields, Shield is the right license.

### SIEM Integration Approach

For SIEM integration, practitioners face a choice between:
1. **Pull model**: Scheduled job queries EventLogFile SOQL, downloads new CSVs, pushes to SIEM. Simple but adds a 24-hour minimum latency.
2. **Push model**: RTEM subscription via Streaming API or Pub/Sub API feeds events in real time to a listener, which forwards to SIEM. Lower latency but more infrastructure.

For most compliance use cases, the pull model with daily EventLogFile is adequate and simpler. For security operations centers (SOCs) requiring fast detection, the RTEM push model is required.

---

## Anti-Patterns

1. **Using EventLogFile as a real-time monitoring system** — EventLogFile has a 24-hour minimum delay. Polling it frequently (e.g., every 5 minutes) does not produce current data. Organizations that design "near-real-time" dashboards on EventLogFile are operating on stale data. Use RTEM storage objects for same-day visibility. Reserve EventLogFile for SIEM ingestion and historical audit.

2. **Skipping Transaction Security Policy validation for supported event types** — Designing policies against event types that do not support enforcement produces silent no-ops. No error is thrown; the policy simply never fires. Always verify the "Can Be Used in a Transaction Security Policy?" flag for each event type in the Object Reference before implementation.

3. **Treating threat detection event timestamps as exact incident timestamps** — `SessionHijackingEvent`, `ApiAnomalyEvent`, and related ML events have an inherent processing lag between the suspicious action and the event's `EventDate`. Using timestamps for cross-log correlation without accounting for this lag produces false negative matches. Always correlate via `EventIdentifier`, not timestamp proximity.

4. **Storing raw EventLogFile CSVs without access controls** — Event logs contain user IDs, session tokens, source IPs, and operation details. A downloaded log file stored in an unprotected S3 bucket or shared drive becomes a secondary attack surface. Log storage destinations must have access controls at least as strict as the org itself.

---

## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing (trusted/easy/adaptable)
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Platform Events Developer Guide — Real-Time Event Monitoring objects, channel configuration, RTEM event types, and Transaction Security Policy support matrix
  URL: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro_emp.htm
- REST API Developer Guide — EventLogFile resource, log download endpoint, SOQL query patterns
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/using_resources_event_log_files.htm
- Salesforce Security Guide — Event Monitoring overview, Shield licensing context
  URL: https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
