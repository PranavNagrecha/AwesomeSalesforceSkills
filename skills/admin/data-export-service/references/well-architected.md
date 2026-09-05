# Well-Architected Notes — Salesforce Data Export Service

## Relevant Pillars

- **Reliability** — Data Export Service is *not* a reliability control on its own. The reliability question is "what is the org's RPO/RTO and which tool delivers them?" — Data Export delivers neither in any meaningful way. The skill's contribution to Reliability is naming this honestly so the architect picks the right tool.
- **Operational Excellence** — The 48-hour download window, no-API-automation constraint, and human-operator loop make this an operations problem more than a configuration problem. Operational Excellence is where the skill earns its keep — runbook quality, on-call coverage, and quarterly drill discipline determine whether the export is fit for any purpose.
- **Security** — At-rest encryption of the destination, access control on the download distribution list, and Shield-clear-text-in-export awareness are the security touchpoints. Mishandling any of these turns a benign weekly job into a data-spill vector.

Performance and Scalability are not central — Data Export is bounded by the ZIP-set generation, which scales with org size but is not a workload the consumer optimizes. Scalability concerns push toward Bulk API or Data Cloud Zero Copy, not toward tuning Data Export.

## Architectural Tradeoffs

### Data Export Service vs Salesforce Backup and Restore (paid)

UNVERIFIED (2026-09-05): every Data Export Service column value below (cadence, restore, Big Object handling, 48-hour expiry, achievable RPO/RTO) and every Backup and Restore column value is help-only — neither product appears in any of the seven Salesforce developer PDFs used to ground this repo. Treat the table as a structure for the conversation, not as quotable figures.

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

The Bulk API 2.0 column here is grounded; the Data Export Service column is not (see the note above). What can be stated with a source: query jobs do not consume the shared 15,000-batches-per-rolling-24-hours allocation because "in Bulk API 2.0, only ingest jobs consume batches. Query jobs don't" (`salesforce_app_limits_cheatsheet.txt:740–741`); results are retrievable "within 7 days of job completion" with a 20-minute retrieval timeout and a 1 GB maximum retrieved file size (`:906–917`); and the rolling ceilings are 10,000 query jobs and 1 TB of query results per 24 hours (`:921–932`).

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

Sources are split by whether this skill could actually read them. The PDFs below were read as extracted text and every line citation in this package points into them; the help.salesforce.com articles could not be fetched, which is why every Data Export Service UI claim in this package carries an UNVERIFIED marker.

**Read and cited (Summer '26 / v62 developer PDFs):**

- Data Loader Guide — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_data_loader.pdf (batch-mode `process-conf.xml` bean shape and every `sfdc.*` / `dataAccess.*` / `process.*` key in `references/metadata-examples.md` § 3–4; the `extract` / `extract_all` operations and their soft-delete difference; the `csvWrite` DAO; mandatory password encryption; the Windows-only constraint; the export SOQL restrictions behind Gotcha 12; and the single grounded mention of the weekly export feature anywhere in the corpus, at line 916)
- Bulk API 2.0 and Bulk API Developer Guide — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_asynch.pdf (the query-job create/monitor/results walkthrough in `references/metadata-examples.md` § 5; `query` vs `queryAll`; `Sforce-Locator` and `maxRecords` paging; the same-API-version 409 rule; automatic chunking and the `ORDER BY` / `LIMIT` interaction behind Gotcha 10; the rejected SOQL shapes)
- Salesforce Developer Limits and Allocations Quick Reference — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf (query jobs not consuming the batch allocation; the 7-day results lifespan; the 20-minute retrieval timeout and 1 GB file ceiling; the 10,000-job and 1 TB rolling-24-hour ceilings behind Gotcha 13 — and the *negative* result that this document, the canonical home of Salesforce numeric limits, does not mention the Data Export Service at all)
- Object Reference for the Salesforce Platform — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (`SystemModstamp` vs `LastModifiedDate` behind Gotcha 9 and the incremental-watermark rule; `IsDeleted`; `systemModstamp` being the one audit field that cannot be set on import; `ContentVersion.VersionData` base64 growth and the all-versions SOQL behaviour; `PermissionSetAssignment` fields, special access rules and the query shape used in Verification)
- Metadata API Developer Guide — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the `PermissionSet` sample definition and `PermissionSetUserPermission` field table behind `references/metadata-examples.md` § 2; `ApiEnabled` as the guide's own `userPermissions` example; the API-40.0-and-later rule that an unspecified permission deploys disabled — and the negative results that no Data Export metadata type exists and that `WeeklyExport` appears nowhere in the guide)
- REST API Developer Guide — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf (`QueryAll` vs `Query` on deleted records; the `sObject Get Deleted` resource, its `earliestDateAvailable` / `latestDateCovered` response fields, the two-hourly delete-log purge, the 15-day floor and the 600,000-ID `EXCEEDED_ID_LIMIT` behind Gotcha 14)
- Best Practices for Deployments with Large Data Volumes, Salesforce Summer '26, last updated June 19 2026 — PDF filename UNVERIFIED (2026-09-05): the document was read as extracted text and does not state its own `resources.docs.salesforce.com` filename, so no URL is given here rather than a guessed one (`SystemModstamp` carrying a standard index, and the 30%-of-first-million / 15%-of-additional selectivity threshold behind Gotcha 11)

**Not fetchable from this environment (help.salesforce.com blocks retrieval) — every claim resting on them is marked UNVERIFIED in place:**

- Export Backup Data from Salesforce — https://help.salesforce.com/s/articleView?id=sf.admin_exportdata.htm&type=5 (the 48-hour window, the file-size split, the binary-content checkboxes, the Big Object / External Object exclusions)
- Schedule a Data Export — https://help.salesforce.com/s/articleView?id=sf.admin_exportdata_scheduling.htm&type=5 (edition-to-cadence eligibility, the 7-day cooldown, the Weekly Data Export permission)
- Salesforce Backup and Restore Overview — https://help.salesforce.com/s/articleView?id=sf.bnr_overview.htm&type=5 (the paid-product column of the tradeoff table above)

**Architecture guidance (Salesforce Architects, not a developer guide):**

- Salesforce Well-Architected — Trusted / Backup — https://architect.salesforce.com/well-architected/trusted/backup (the Reliability framing: obligation-first, RPO/RTO before tooling)
