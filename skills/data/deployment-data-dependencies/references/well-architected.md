# Well-Architected Notes — Deployment Data Dependencies

## Relevant Pillars

### Reliability
Deployments that depend on org-specific data (Record Type IDs, Queue IDs, Custom Setting values) are unreliable because they carry implicit environment assumptions. A reliable deployment pipeline externalizes all ID references and resolves them dynamically in the target org.

### Operational Excellence
Deployment runbooks must explicitly list data migration steps alongside metadata deployment steps. Omitting Custom Setting data loads or post-deployment ID-resolution scripts from runbooks creates knowledge gaps that cause failures on every subsequent deployment.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Portability | Use DeveloperName / Name for all cross-org references, never raw IDs |
| Runbook completeness | Deployment runbooks must include data migration steps for Custom Settings and reference data |
| Auditability | Log the source and target ID mapping for RecordTypes and Queues in deployment artifacts |

## Cross-Skill References

- `data/data-migration-planning` — Full data migration strategy and tool selection
- `devops/deployment-pipeline-design` — CI/CD pipeline design including data migration stages
- `data/sandbox-refresh-data-strategies` — Reference data seeding strategies for sandboxes

## Official Sources Used

- Salesforce SFDMU Documentation — External ID and RecordType.DeveloperName mapping: https://github.com/forcedotcom/SFDX-Data-Move-Utility
- Salesforce Apex Developer Guide — Schema.SObjectType: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_sobject_type.htm
- Salesforce Help — Custom Settings Overview: https://help.salesforce.com/s/articleView?id=sf.cs_about.htm
- Salesforce Help — Record Types: https://help.salesforce.com/s/articleView?id=sf.customize_recordtype.htm
- Bulk API 2.0 Developer Guide — Upsert with External ID: https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_bulk_create_job.htm
