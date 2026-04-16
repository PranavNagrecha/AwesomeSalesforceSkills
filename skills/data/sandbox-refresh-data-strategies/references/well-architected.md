# Well-Architected Notes — Sandbox Refresh Data Strategies

## Relevant Pillars

### Operational Excellence
Sandbox data readiness is a gate for every QA and UAT cycle. An org with a well-designed post-refresh data strategy can start testing within minutes of a sandbox refresh completing. An org without one spends days on manual data setup before each sprint.

### Security
Sandbox data strategies must account for PII. Using production data in non-Full sandboxes requires an anonymization step (pseudonymization, data masking, or synthetic replacement). Partial sandbox copies in regulated industries must confirm that data masking is applied before QA personnel access the sandbox.

### Reliability
SandboxPostCopy reliability requires async delegation. Scripts that fail silently leave sandboxes in an inconsistent data state that surfaces only during testing. Queueable-based post-copy patterns are more reliable and easier to monitor via AsyncApexJob.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Environment Readiness | Post-refresh data must be reliable and automated; manual runbooks are a reliability risk |
| Data Privacy | PII must be masked before exposing to non-Full sandbox environments |
| Automation | SandboxPostCopy + Queueable chains for reference data; native Data Seeding for scenario data |
| Sandbox Type Selection | Architect must select sandbox copy type based on data requirements, not just storage size |

## Cross-Skill References

- `data/deployment-data-dependencies` — Handling org-specific ID resolution after data loads
- `data/data-migration-planning` — Full data migration tool selection (SFDMU, Data Loader)
- `devops/deployment-pipeline-design` — CI/CD pipeline integration with sandbox refresh events

## Official Sources Used

- Salesforce Help — SandboxPostCopy Interface: https://help.salesforce.com/s/articleView?id=sf.data_sandbox_post_copy.htm
- Salesforce Help — Data Seeding: https://help.salesforce.com/s/articleView?id=sf.data_seeding.htm
- Salesforce Help — Sandbox Types and Templates: https://help.salesforce.com/s/articleView?id=sf.data_sandbox_environments.htm
- Apex Developer Guide — Queueable Apex: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
