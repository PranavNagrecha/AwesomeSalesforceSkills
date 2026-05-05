# Well-Architected Notes — Salesforce Data Export Service

## Relevant Pillars

- **Reliability** — Data Export Service is *not* a reliability control on its own. The reliability question is "what is the org's RPO/RTO and which tool delivers them?" — Data Export delivers neither in any meaningful way. The skill's contribution to Reliability is naming this honestly so the architect picks the right tool.
- **Operational Excellence** — The 48-hour download window, no-API-automation constraint, and human-operator loop make this an operations problem more than a configuration problem. Operational Excellence is where the skill earns its keep — runbook quality, on-call coverage, and quarterly drill discipline determine whether the export is fit for any purpose.
- **Security** — At-rest encryption of the destination, access control on the download distribution list, and Shield-clear-text-in-export awareness are the security touchpoints. Mishandling any of these turns a benign weekly job into a data-spill vector.

Performance and Scalability are not central — Data Export is bounded by the ZIP-set generation, which scales with org size but is not a workload the consumer optimizes. Scalability concerns push toward Bulk API or Data Cloud Zero Copy, not toward tuning Data Export.

## Architectural Tradeoffs

### Data Export Service vs Salesforce Backup and Restore (paid)

| Dimension | Data Export Service | Salesforce Backup and Restore |
|---|---|---|
| Cost | Free (included in edition) | Separate paid add-on |
| Cadence | Weekly or monthly | Daily snapshots |
| Restore | None (manual reload via Data Loader) | Record-level with relationship resolution |
| Big Objects | Excluded | Included |
| Metadata | Excluded | Excluded (use Git) |
| 48-hour expiry | Yes | N/A — managed retention |
| Audit trail | Operator runbook | Native audit log |
| RPO achievable | 7 days (best case) | 24 hours |
| RTO achievable | Days–weeks | Hours |

The "free vs paid" framing is misleading — they're different products. The choice is between buying a backup capability (real restore, real RPO) or operating an evidence-archive workflow (cheap, no restore).

### Data Export Service vs Bulk API 2.0

| Dimension | Data Export Service | Bulk API 2.0 |
|---|---|---|
| Setup | UI checkboxes | OAuth + tooling |
| Scope | Per-object (all-or-nothing rows) | SOQL filter (record-level) |
| Cadence control | Weekly / Monthly fixed | Any cadence the consumer schedules |
| Automation | Email-and-click | Fully programmable |
| Best for | One-time full-org snapshot, compliance evidence | Ongoing replication, filtered exports, automation |

For ongoing replication or filtered exports, Bulk API wins on every axis except UI simplicity.

### Including binary content (Files / Documents / Attachments)

Including binary content in the export takes a fast 20-minute job and turns it into a 4–8-hour, multi-zip, often-fails-mid-download job. The right answer depends on the consumer:

- Evidence-archive consumer: exclude binary content; document the gap.
- Legal-discovery consumer: include the targeted subset only (use Bulk API to filter, not Data Export to bulk-download).
- BI / warehouse consumer: exclude binary; replicate ContentVersion via dedicated Bulk API job.

Defaulting binary content to OFF is the right call for almost every use case.

## Anti-Patterns

1. **"Weekly Data Export = backup"** — the most common audit finding. The export has no restore path, expires in 48 hours, and skips Big Objects, External Objects, and metadata. Reframing as evidence archive (or replacing with a real backup product) is the correct fix.
2. **Treating Data Export as automation-ready** — it is UI-only. Teams that build CI/CD around assumed scriptability hit a wall. Bulk API is the right substrate for automation.
3. **Ignoring destination security posture** — exports may contain Shield-protected fields in clear; landing them on unencrypted storage breaks the compliance framework that funded Shield.
4. **Including all checkboxes "to be safe"** — operationally fragile, security-amplifying, and almost never aligned to the actual consumer need.

## Official Sources Used

- Export Backup Data from Salesforce — https://help.salesforce.com/s/articleView?id=sf.admin_exportdata.htm&type=5
- Schedule a Data Export — https://help.salesforce.com/s/articleView?id=sf.admin_exportdata_scheduling.htm&type=5
- Salesforce Backup and Restore Overview — https://help.salesforce.com/s/articleView?id=sf.bnr_overview.htm&type=5
- Salesforce Backup Best Practices — https://architect.salesforce.com/well-architected/trusted/backup
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Salesforce Well-Architected Framework Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
