# Well-Architected Notes — Program Outcome Tracking Design

## Relevant Pillars

- **Operational Excellence** — Grant compliance reporting requires accurate, auditable outcome data. The data model must support report reproducibility across grant periods. Staff data entry workflows must be simple enough to ensure consistent outcome recording.
- **Reliability** — Outcome data collected throughout a program year must be available and accurate at grant reporting time. Data entry gaps (missing outcome records for completed participants) directly impact grant compliance. Build data quality checks into the program closeout workflow.
- **Security** — Participant program data may include sensitive health, employment, or housing information subject to HIPAA or state privacy laws. Field-level security on sensitive outcome fields (health metrics, employment income, housing status) must restrict access to authorized program staff only.

## Architectural Tradeoffs

**Custom Outcome Objects vs. NPC Outcome Management:** For NPSP/PMM orgs, custom Outcome objects are the only option. For NPC orgs, Outcome Management provides a native, supported framework that reduces custom development but requires learning the NPC object model. The NPC approach is preferred for new NPC orgs; custom objects remain valid for complex NPSP implementations where NPC migration is not planned.

**Outcome data on Contact vs. ProgramEngagement:** Linking Outcome records to ProgramEngagement__c (rather than Contact) preserves program context (which program, which cohort, which service) and enables program-level aggregation. Linking outcomes directly to Contact creates a flat structure that loses program context when participants attend multiple programs.

## Anti-Patterns

1. **Using NPSP Opportunity data for program impact reporting** — Opportunity Amount reflects donations received, not program results. Grant reports citing Opportunity-based metrics to claim program impact conflate fundraising and program delivery data.
2. **Assuming PMM ships Outcome or Indicator objects** — PMM covers service delivery logistics. Outcome measurement always requires custom objects on NPSP/PMM, or NPC Outcome Management on Nonprofit Cloud.
3. **Cross-program Stage picklist ambiguity** — Sharing a single ProgramEngagement Stage picklist across programs with different completion definitions produces inflated and misleading outcome counts in grant reports.

## Official Sources Used

- Salesforce Nonprofit Program Management Module (PMM) Help Documentation — https://help.salesforce.com/s/articleView?id=sfdo.PMM_Overview.htm
- Nonprofit Cloud Program Management Developer Docs — https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud_dev.meta/nonprofit_cloud_dev/nonprofit_cloud_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
