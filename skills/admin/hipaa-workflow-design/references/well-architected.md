# Well-Architected Notes — HIPAA Workflow Design

## Relevant Pillars

- **Security** — All HIPAA workflow design is security-driven. Access control (minimum necessary), encryption (PHI at rest and in transit), and audit controls are non-negotiable HIPAA technical safeguards, not optional enhancements.
- **Operational Excellence** — HIPAA compliance is not a one-time implementation task. Event Monitoring streaming to SIEM is an ongoing operational requirement. Shield Field Audit Trail requires ongoing field coverage maintenance as new PHI fields are added. Compliance posture must be monitored continuously.
- **Reliability** — The Event Monitoring streaming pipeline is a reliability concern: if the pipeline fails, audit logs are permanently lost after 30 days. Pipeline health monitoring is a HIPAA compliance requirement.

## Architectural Tradeoffs

**Shield Field Audit Trail vs. Standard Field History Tracking:** Shield Field Audit Trail is more expensive (paid add-on) and requires more configuration, but is the only option that satisfies HIPAA's 6-year audit log retention requirement. Standard Field History Tracking is included in all editions but retains data for only 18 months. For a HIPAA-covered entity, Shield Field Audit Trail is not optional.

**In-Platform Audit vs. External SIEM:** Salesforce's native audit capabilities (Event Monitoring) cover the in-platform audit requirement, but only for 30 days. External SIEM is required for the 6-year retention requirement. The architectural tradeoff is not whether to use a SIEM but which SIEM and how to architect the streaming pipeline.

## Anti-Patterns

1. **Using standard Field History Tracking for HIPAA audit compliance** — 18-month retention fails the 6-year HIPAA requirement. Shield Field Audit Trail is required for all PHI fields.
2. **Treating BAA as org-wide coverage** — The BAA covers specific products, not all services in the org. PHI in uncovered products creates compliance gaps.
3. **Configuring Event Monitoring without a SIEM streaming pipeline** — Logs expire in 30 days without streaming. HIPAA requires 6-year retention — the streaming pipeline is not optional.

## Official Sources Used

- Health Cloud Admin Guide — Protect Your Health Data with Salesforce Shield: https://help.salesforce.com/s/articleView?id=ind.hc_protect_health_data.htm
- Salesforce HIPAA BAA Help Article: https://help.salesforce.com/s/articleView?id=000394847
- Salesforce Shield Security Guide: https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/security_overview.htm
- HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/index.html
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
