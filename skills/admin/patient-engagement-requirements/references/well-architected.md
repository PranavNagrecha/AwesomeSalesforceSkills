# Well-Architected Notes — Patient Engagement Requirements

## Relevant Pillars

- **Security** — Patient portal features must handle PHI with HIPAA compliance: secure messaging must use BAA-covered channels, assessment responses containing PHI must be encrypted, portal authentication must meet HIPAA access control requirements. Every engagement channel that carries PHI requires explicit BAA coverage verification.
- **Operational Excellence** — License prerequisites (Experience Cloud for HC, CRM Analytics, OmniStudio installation) must be confirmed and activated before implementation begins. Discovering license gaps during build phases creates costly rework. The engagement feature inventory must include license dependency documentation as a mandatory artifact.
- **Reliability** — IAM scheduling aggregation from multiple sources (Salesforce Scheduler + EHR) creates dependency on external system availability. Patient self-scheduling must handle graceful degradation when the EHR scheduling system is unavailable.

## Architectural Tradeoffs

**IAM with Salesforce Scheduler vs. EHR Scheduling Passthrough:** IAM can aggregate Salesforce Scheduler (native) and EHR scheduling systems. Using native Salesforce Scheduler provides full data control and reporting but requires replicating provider availability from EHR systems. Using EHR scheduling passthrough maintains the EHR as the system of record for availability but creates integration complexity and a dependency on EHR API availability for every patient scheduling request.

**OmniScript Assessments vs. Salesforce Surveys:** OmniScript (via OmniStudio) provides rich, branching assessment forms with clinical logic. Salesforce Surveys is simpler but lacks clinical assessment library integration and OmniStudio's conditional logic capabilities. For standardized clinical instruments (PHQ-9, GAD-7, SDOHCC) that require specific scoring and response mapping, OmniScript is the recommended approach.

## Anti-Patterns

1. **Assuming patient portal is included in base Health Cloud** — Experience Cloud for Health Cloud is a separate add-on. Designing portal features without confirming this license creates a hard scope gap.
2. **Including no-show prediction without CRM Analytics license** — IAM no-show prediction requires CRM Analytics. Building requirements that assume this capability without confirming the CRM Analytics license creates an undeliverable requirement.
3. **Using non-HIPAA-covered messaging channels for patient clinical communications** — routing PHI through standard Chatter or Email-to-Case without BAA coverage creates HIPAA compliance exposure.

## Official Sources Used

- Salesforce Health Cloud Admin Guide — Intelligent Appointment Management: https://help.salesforce.com/s/articleView?id=ind.hc_iam.htm
- Trailhead — Intelligent Appointment Management for Health Cloud: https://trailhead.salesforce.com/content/learn/modules/intelligent-appointment-management-for-health-cloud
- OmniStudio Developer Guide: https://developer.salesforce.com/docs/industries/omnistudio/overview
- Experience Cloud for Health Cloud: https://help.salesforce.com/s/articleView?id=ind.hc_exp_cloud_for_health_cloud.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
