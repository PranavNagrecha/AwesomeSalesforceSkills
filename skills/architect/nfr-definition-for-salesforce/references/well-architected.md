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

2. **Conflating Salesforce infrastructure SLA with application availability** — Treating Salesforce's 99.9% Trust SLA as evidence that the implementation's availability NFR is met conflates two distinct scopes. The Trust SLA does not cover custom code failures, bad deployments, or data loss from admin errors. Application availability must be separately defined with customer-owned RPO/RTO targets, monitoring, and rollback procedures.

3. **Defining scalability NFRs in record counts without governor limit mapping** — NFRs like "must handle 10 million records" are incomplete without mapping the record volume to the relevant Salesforce processing limits (SOQL rows per transaction, DML limits, Bulk API job limits, daily API allocation). A scalability NFR that ignores platform ceilings will produce an unachievable acceptance criterion or a last-minute architectural change.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected: Trusted Pillar — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
- Salesforce Well-Architected: Resilient Pillar — https://architect.salesforce.com/docs/architect/well-architected/guide/resilient.html
- Salesforce Trust — Service Level Agreement — https://trust.salesforce.com/
- Salesforce Governor Limits Reference — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
