# Well-Architected Notes — NFR Definition for Salesforce

## Relevant Pillars

The Salesforce Well-Architected Framework groups quality attributes into three top-level pillars. NFR definition directly operationalises all three.

- **Trusted (Security + Reliability)** — The Trusted pillar encompasses security, compliance, reliability, and data integrity. NFRs in the security/compliance and availability categories are direct expressions of Trusted pillar requirements. Defining these NFRs explicitly forces teams to answer: which security controls are required, who owns each, and how will compliance be verified before go-live?

- **Easy (Usability + Process Efficiency)** — The Easy pillar covers user experience, process simplicity, and change management. Usability NFRs (page load time, field count per layout, mobile readiness, accessibility compliance) are how the Easy pillar becomes testable. Without explicit usability NFRs, experience regressions are caught late and are expensive to fix.

- **Adaptable (Scalability + Resilience + Composability)** — The Adaptable pillar covers the system's ability to grow and recover. Performance and scalability NFRs — especially those grounded in governor limit headroom calculations — directly express Adaptable pillar requirements. Resilience NFRs (RPO, RTO, availability ownership split) belong here as well.

## Architectural Tradeoffs

**Measurability vs. effort to define:** Rigorous NFRs (percentile thresholds, environment qualifiers, measurement methods) take longer to define than vague ones. The tradeoff is front-loaded effort vs. back-loaded risk: vague NFRs are accepted quickly but generate disputes at UAT, missed go-live criteria, and post-launch performance incidents. Invest in precision during the design phase.

**Completeness vs. stakeholder fatigue:** A comprehensive NFR register covering all five categories can run to 30–50 individual requirements. Stakeholders may push back on the breadth. The risk of under-specifying is that untested NFR categories (commonly usability and availability responsibility) surface as incidents after launch. Recommend prioritising NFRs by risk and completing at least two per category, even if some remain aspirational until post-launch.

**Governor limit headroom vs. architectural complexity:** Designing for 50% headroom against governor limits typically requires async processing patterns (Batch Apex, Queueable, Platform Events, Bulk API) that add architectural complexity compared to synchronous alternatives. The tradeoff is clear: synchronous designs are simpler but hit hard ceilings as data volumes grow. The NFR register is the correct place to document this decision with the rationale.

## Anti-Patterns

1. **Single-line compliance NFRs** — Writing "must comply with GDPR" as a single NFR row is an anti-pattern because it is unassignable, untestable, and will fail any compliance audit. GDPR imposes dozens of distinct technical controls. Each control that requires a Salesforce configuration or custom feature must appear as a separate NFR with a testable acceptance criterion. The same applies to HIPAA and PCI-DSS.

2. **Conflating Salesforce infrastructure SLA with application availability**: Treating a published platform uptime figure (often quoted as a 99.9% Trust SLA; UNVERIFIED (2026-10-03): no fetched source states it) as evidence that the implementation's availability NFR is met conflates two distinct scopes. The Trust SLA does not cover custom code failures, bad deployments, or data loss from admin errors. Application availability must be separately defined with customer-owned RPO/RTO targets, monitoring, and rollback procedures.

3. **Defining scalability NFRs in record counts without governor limit mapping** — NFRs like "must handle 10 million records" are incomplete without mapping the record volume to the relevant Salesforce processing limits (SOQL rows per transaction, DML limits, Bulk API job limits, daily API allocation). A scalability NFR that ignores platform ceilings will produce an unachievable acceptance criterion or a last-minute architectural change.

## Official Sources Used

Read for this revision (2026-10-03):

- Salesforce Developer Limits and Allocations Quick Reference (Summer '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf. Concurrent API Request Limits (25 requests of 20 s or longer), API Timeout Limits, Total API Request Allocations (edition formula, Full sandbox 5,000,000, aggregate per org), overage behaviour and its exclusions, Bulk API 2.0 job size and daily record limits.
- Apex Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf. Execution Governors and Limits (per-transaction table; scheduled Apex under synchronous limits; daily asynchronous Apex executions).
- Tooling API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_tooling.pdf. SandboxInfo (`LicenseType` values; `SandboxStorage` add-on: Developer 200 MB to 400 MB, Developer Pro 1 GB to 2 GB).
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. Development environments overview (which sandboxes carry production data).
- Salesforce Object Reference, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf. EventLogFile (access rules, `LogDate`, `LogFile`, `LogFileFieldNames`); Lightning Page View event type (`EFFECTIVE_PAGE_TIME`, `DURATION`, non-durable logs note); LightningUsageByPageMetrics and related objects ("Not available in sandbox orgs").
- REST API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf. Limits resource (`/services/data/v67.0/limits`, `DailyApiRequests`, `Max` and `Remaining`).
- Salesforce Security Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf. Salesforce Shield (Platform Encryption at rest, Event Monitoring, Field Audit Trail).
- Salesforce Well-Architected: Trusted > Reliable: https://architect.salesforce.com/docs/architect/well-architected/guide/reliable.html (a direct fetch does not return the guide page; read via Wayback snapshot 2026-06-13). Availability as shared responsibility, Scale Test in a Full sandbox, throughput and latency definitions, large data volume thresholds, 10,000-child guidance.
- Salesforce Well-Architected: Adaptable > Resilient: https://architect.salesforce.com/docs/architect/well-architected/guide/resilient.html (Wayback snapshot 2026-06-13). Backup and restore as customer-owned recovery from corruption, defects, and failed data loads.
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (Wayback snapshot 2026-06-16).

Listed in the original version and not re-read; no claim in this revision rests on them alone:

- Salesforce Well-Architected: Trusted Pillar, https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html (HTTP 404 on 2026-10-03; no Wayback snapshot available).
- Salesforce Trust, https://trust.salesforce.com/ (status site; not fetched for this revision).
- Apex Governor Limits (atlas page), https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm (same content read in the PDF above).
- Salesforce Help: Shield Platform Encryption, https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm (Salesforce Help does not fetch).
