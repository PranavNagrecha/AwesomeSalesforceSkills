# Well-Architected Notes — FSC Compliant Data Sharing API

## Relevant Pillars

- **Security** — CDS is a security enforcement layer. Using participant objects correctly ensures access grants are tracked in the CDS audit trail, survive org-level recalculation, and are not bypassed by direct share table manipulation. Developers who circumvent CDS by writing directly to `AccountShare` create access controls that are invisible to FSC compliance workflows and risk granting unreviewed access that persists after organizational changes.

- **Reliability** — CDS asynchronous processing introduces eventual consistency between participant record state and share row state. Reliable implementations do not assert on share row existence synchronously and design revocation workflows around participant record deletion rather than share row deletion. Failure to account for asynchronous behavior produces access gaps and unreliable test suites.

- **Scalability** — `ParticipantGroup` reduces participant record volume by replacing per-user, per-account records with a single group-account participant record. At scale (thousands of accounts, dozens of team members), per-user patterns produce millions of participant records that degrade query performance and recalculation times. Group-based patterns keep participant counts proportional to account volume, not to the product of users and accounts.

- **Operational Excellence** — CDS centralizes sharing decisions in participant records, making sharing state auditable via SOQL on `AccountParticipant` and `ParticipantRole`. This is operationally superior to inspecting raw share rows, which are generated, platform-managed artifacts that do not represent intent — only current computed state.

## Architectural Tradeoffs

**Per-user participants vs. ParticipantGroup:** Per-user `AccountParticipant` records are simpler to reason about and debug but do not scale when team membership is fluid. `ParticipantGroup` reduces maintenance DML volume and improves recalculation performance but introduces an indirection layer that makes access debugging slightly less direct (the developer must trace group membership to understand who has access). Choose per-user records for static, named-individual access; choose groups for role-based or team-based access patterns.

**CDS vs. standard Apex managed sharing in non-CDS-enabled orgs:** If CDS is not enabled (e.g., the org uses FSC but has not activated CDS), standard Apex managed sharing via direct `AccountShare` inserts is the correct approach. Do not insert participant records in a non-CDS-enabled org — they persist in the database but produce no access effect and add confusing dead data. Evaluate whether enabling CDS is feasible before designing an Apex sharing solution for FSC.

**Synchronous participant insert vs. batch/queueable:** For trigger-driven participant inserts on small sets of records, synchronous DML is acceptable. For bulk operations (branch reorganizations, territory reassignments), a queueable or batch pattern avoids DML row limit violations and keeps the triggering transaction lightweight. Batch recalculation via CDS is implicit (the platform drives it from participant records), but the initial participant population DML may still require asynchronous patterns.

## Anti-Patterns

1. **Direct AccountShare DML as a CDS substitute** — Inserting or deleting `AccountShare` rows directly to manage FSC access bypasses the CDS engine. Share rows written outside the CDS engine are not part of the audit trail, are overwritten on recalculation, and may conflict with CDS-managed rows. All FSC sharing grants in CDS-enabled orgs must flow through participant records.

2. **Using share row existence as the authoritative signal of access state** — Because CDS is asynchronous and share rows are regenerated from participant records on every recalculation, the share table reflects computed state at a point in time, not persistent intent. Relying on share row presence to determine whether a user "should have" access produces race conditions and post-recalculation surprises. Treat participant records as the source of truth and share rows as a read-only derived artifact.

3. **Ignoring OWD before inserting participant records** — Inserting participant records without verifying that OWD is restrictive produces a false sense of security. The participant records exist, no error is thrown, but no access is granted. Worse, the CDS configuration appears correct, making it difficult to diagnose why users lack access. Always verify OWD as the first diagnostic step.

## Official Sources Used

- Salesforce Help — Compliant Data Sharing for Financial Services Cloud — https://help.salesforce.com/s/articleView?id=sf.fsc_compliant_data_sharing.htm
- Salesforce Help — Considerations and Limitations for Compliant Data Sharing — https://help.salesforce.com/s/articleView?id=sf.fsc_compliant_data_sharing_considerations.htm
- Metadata API Developer Guide — IndustriesSettings — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_industriessettings.htm
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
