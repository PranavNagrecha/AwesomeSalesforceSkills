# Well-Architected Alignment -- org-limits-monitoring

## Pillar: Operational Excellence

Org-level limit monitoring is a foundational operational excellence practice. Without proactive visibility into limit consumption, teams operate reactively -- discovering limit exhaustion only when integrations fail, users cannot save records, or platform events are silently dropped. A well-architected org treats limit monitoring as infrastructure, not an afterthought.

**Operational Excellence patterns this skill enforces:**
- Automated monitoring via Scheduled Apex -- removes dependency on manual Setup page checks.
- Threshold-based alerting with configurable severity levels -- warning and critical thresholds give teams graduated response time.
- Custom Metadata-driven configuration -- thresholds and notification channels can be adjusted by administrators without code deployments.
- Trend tracking via snapshot records -- historical consumption data supports capacity planning and budget forecasting.
- Runbook integration -- every alert maps to a documented escalation path and remediation procedure.

**Anti-patterns this skill catches:**
- Manual-only monitoring via Setup > Company Information -- does not scale and fails on weekends and holidays.
- Hard-coded threshold values in Apex -- creates deployment overhead when thresholds need adjustment.
- Monitoring only the limits that have failed before -- a reactive posture that guarantees future surprises from unmonitored limits.

---

## Pillar: Reliability

Org-level limit exhaustion causes org-wide failures that affect all users and integrations simultaneously. Unlike per-transaction governor limit violations (which fail one transaction), an exhausted daily API call limit blocks every inbound and outbound API call for the remainder of the rolling window. Proactive monitoring is a reliability control that prevents these cascading failures.

**Reliability practices this skill mandates:**
- Multi-limit coverage -- monitoring API calls alone is insufficient; storage, platform events, async apex executions, and metadata limits all have org-wide failure modes.
- Alert channel redundancy -- if the primary alert channel is email and the email service is affected by the same limit exhaustion, the alert never arrives. Use at least two independent channels.
- Reconciliation patterns for silent failures -- Platform Event hourly limits fail silently; subscriber-side reconciliation is the only reliable detection mechanism.
- Monitoring job self-healing -- if the Scheduled Apex job is aborted or fails, it should be able to re-register itself or alert through an independent mechanism.

---

## Pillar: Security

Limit monitoring intersects with security in two ways. First, a sudden spike in API consumption may indicate unauthorized API access or a compromised integration credential making excessive calls. Second, the monitoring infrastructure itself must be secured -- the Scheduled Apex job runs with elevated system context and the Custom Metadata configuration controls alerting behavior.

**Security considerations this skill addresses:**
- Anomaly detection -- a monitoring job that tracks consumption velocity (not just absolute values) can flag unusual spikes that warrant security investigation.
- Named Credential usage for external callouts -- monitoring jobs that call external incident management systems (PagerDuty, Slack) must use Named Credentials, never hard-coded credentials.
- Principle of least privilege for monitoring configuration -- Custom Metadata deployment permissions should be restricted to platform administrators, not all developers.

---

## Official Sources Used

- Salesforce Well-Architected Overview -- architecture quality model, Operational Excellence and Reliability pillars
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Apex Reference Guide -- OrgLimits class, OrgLimit class methods (getAll, getName, getLimit, getValue)
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_OrgLimits.htm
- REST API Developer Guide -- Limits resource
  https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm
- Salesforce Help -- Monitor Your Org's API Usage
  https://help.salesforce.com/s/articleView?id=sf.code_manage_packages_api_usage.htm
- Salesforce Help -- Data and File Storage Allocations
  https://help.salesforce.com/s/articleView?id=sf.overview_storage.htm
