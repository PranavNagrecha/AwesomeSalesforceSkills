# Well-Architected Notes — Health Cloud Multi-Cloud Strategy

## Relevant Pillars

### Security

Multi-cloud Health Cloud implementations handle Protected Health Information (PHI) across multiple Salesforce products, each with distinct data processing boundaries. The Security pillar applies at every cloud junction:

- **HIPAA BAA scope per cloud:** The Salesforce Health Cloud HIPAA BAA does not extend to Marketing Cloud. Each cloud that stores or processes PHI must have its own BAA in place before PHI data flows are activated. Failing to enforce this is a HIPAA Privacy Rule violation with reportable breach potential.
- **Experience Cloud portal access control:** External patient users must be governed by Sharing Sets, Sharing Rules, and PSL-gated permission sets. The default OWD for Health Cloud objects is Private; portal users must have explicit record access paths. Guest User access must be restricted to the minimum necessary data.
- **OmniStudio callout credentials:** Integration Procedures that call external EHR APIs (Epic, Cerner) must use Named Credentials to avoid storing credentials in Apex or OmniScript configuration. Named Credentials with the "Allow Merge Fields in HTTP Header" option provide per-user credential isolation.
- **Field-level encryption for PHI fields:** Health Cloud orgs handling sensitive PHI fields (SSN, diagnosis codes, medication names) should evaluate Salesforce Shield Platform Encryption. Encryption scope must be confirmed with the customer's CISO before the data model is finalized.

Usage context for this skill: When designing the multi-cloud topology, the architect must map every PHI data flow between clouds and confirm the BAA and encryption posture for each segment. This mapping is a Security pillar deliverable, not an afterthought.

### Reliability

A multi-cloud Health Cloud implementation introduces multiple failure domains. Reliability design must account for each cloud's availability independently:

- **Marketing Cloud sync reliability:** Marketing Cloud Health Cloud Connect is an asynchronous replication mechanism. If Marketing Cloud is unavailable, appointment reminder journeys will not trigger. Care-critical workflows (e.g., medication alerts) must NOT rely on Marketing Cloud as the delivery path — use Health Cloud's internal Case-based tasks or OmniStudio processes instead.
- **Experience Cloud portal availability:** The patient portal depends on Health Cloud org availability. Health Cloud planned maintenance windows must be communicated to portal users. If the portal is used for time-sensitive patient actions (appointment booking), a maintenance banner mechanism should be implemented.
- **OmniStudio Integration Procedure retry behavior:** Integration Procedures that call external EHR systems do not have built-in retry on callout failure. Reliability requires implementing explicit error handling in the Integration Procedure and, for critical writes, a Platform Event-based retry pattern.

Usage context for this skill: During org topology design, identify which patient-facing workflows are reliability-critical and ensure they do not route through optional add-on clouds (Marketing Cloud, CRM Analytics) as their primary execution path.

### Scalability

- **Experience Cloud license capacity:** The Experience Cloud for Health Cloud add-on is sold per external user or as a login-based model. For health systems with large patient populations, the login-based model is often more cost-effective. The architecture must plan for license tier at the expected patient volume, not at go-live volume.
- **OmniStudio governor limits:** OmniScripts and Integration Procedures run within Salesforce governor limits — they are not exempt from Apex CPU limits, callout limits (100 callouts per transaction), or SOQL row limits (50,000). High-throughput care coordination workflows that trigger many Integration Procedures simultaneously must be designed with asynchronous execution (Queueable Apex or batch OmniScript) to avoid limit breaches.
- **Marketing Cloud data extension row limits:** Marketing Cloud data extensions used for Health Cloud synced records are subject to row limits based on the Marketing Cloud edition. For large health systems (millions of patient records), confirm that the Marketing Cloud edition supports the data volume before designing the sync scope.

Usage context for this skill: The scalability analysis must be per-cloud, not per-org, because each cloud in the topology has independent capacity constraints.

## Architectural Tradeoffs

**Single-org vs. hub-and-spoke:** A single Health Cloud org with Experience Cloud is simpler, cheaper, and easier to maintain. Hub-and-spoke (multiple orgs per entity) provides stricter data isolation at the cost of dramatically higher integration complexity and license cost. This is the central tradeoff in multi-cloud Health Cloud architecture. The default recommendation is single-org unless a specific regulatory driver (42 CFR Part 2 behavioral health data segregation, international data residency) mandates separation.

**Marketing Cloud integration vs. internal notifications:** Marketing Cloud provides sophisticated journey orchestration and external channel delivery (email, SMS). However, it adds cost, a separate BAA requirement, and a sync reliability dependency. For simpler use cases (appointment reminders), Salesforce Flow + custom notification or an external SMS gateway via Named Credential callout may meet the requirement without the Marketing Cloud complexity and compliance overhead.

**OmniStudio vs. custom LWC for patient-facing flows:** OmniStudio OmniScripts are bundled in Health Cloud and provide no-code configurability for non-developer care program staff. Custom LWC gives developers more control and avoids OmniStudio's runtime overhead. For patient-facing portal flows where care program staff need to iterate on assessment questions without code deployments, OmniStudio wins. For high-performance portal UI where runtime speed is critical and the care program team has no need to self-configure, custom LWC is appropriate.

## Anti-Patterns

1. **Assuming Health Cloud BAA covers all connected Salesforce products** — Teams that execute a HIPAA BAA for Health Cloud and then connect Marketing Cloud, MuleSoft, or CRM Analytics assume those products are covered under the same agreement. Each product requires its own BAA evaluation. This anti-pattern leads to HIPAA-noncompliant data flows that are not discovered until a compliance audit or breach investigation.

2. **Building the patient portal in a separate Salesforce org to "isolate" patient data** — Motivated by a misunderstanding of data isolation requirements, some architects create a dedicated "portal org" and integrate it with the Health Cloud org via APIs. This doubles the license cost, introduces bidirectional sync complexity, creates identity management challenges (patient identity in two orgs), and provides no meaningful additional data isolation beyond what Sharing Sets and OWD configurations achieve in a single-org model. Use the single-org Experience Cloud for Health Cloud model unless a documented regulatory requirement explicitly mandates a separate org.

3. **Skipping the PSL assignment matrix deliverable** — Treating PSL assignment as a minor operational detail rather than an architecture deliverable leads to incomplete assignments being discovered in UAT. The PSL assignment matrix (which PSLs each persona needs, and in what quantity) must be produced as a formal architecture artifact and validated against the order form to confirm PSL quantities are purchased.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Health Cloud Administration Guide — https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/admin_overview.htm
- Experience Cloud for Health Cloud FAQ — https://help.salesforce.com/s/articleView?id=sf.experience_cloud_health_cloud_faq.htm
- Health Cloud Permission Sets and Licenses — https://help.salesforce.com/s/articleView?id=sf.health_cloud_psl.htm
- Marketing Cloud HIPAA Compliance — https://help.salesforce.com/s/articleView?id=sf.mc_overview_hipaa.htm
