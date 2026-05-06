# Well-Architected Notes — Salesforce Backup and Restore

## Relevant Pillars

- **Reliability** — Backup-and-restore is the canonical reliability
  control for the data layer. The objective is not "have a backup"
  but "be able to restore to a defined RPO within a defined RTO".
  Reliability is measured by tested restore drills, not by the
  presence of a tool.
- **Operational Excellence** — A documented restore runbook with
  named owners, decision authority, and a recurring drill cadence is
  what separates a backup tool from a recovery capability. Without
  the runbook, the tool is shelfware.
- **Security** — Backup data is a high-value target. Encryption at
  rest in the backup store, access control on restore (who can
  initiate, who must approve), and audit logging of restores are
  security-critical. A backup tool that allows any admin to restore
  any object expands the blast radius of a compromised admin
  account.

## Architectural Tradeoffs

- **Native Salesforce Backup vs third-party.** Native is simpler to
  procure (single vendor, single contract) and integrates well with
  Salesforce's identity / billing. Third-party tools (Own / Druva /
  Spanning / Gearset) typically lead on restore UX, sandbox seeding,
  cross-org compare, and anomaly detection. The break-even depends
  on whether you need those advanced capabilities.
- **Self-rolled Bulk API vs paid product.** Self-rolled is cheap in
  steady state and gives full control of data residency. The cost is
  paid in a crisis: the engineering work to implement
  relationship-aware restore is large, and bugs in restore code are
  discovered exactly when you can least afford them.
- **Daily RPO vs sub-daily.** Daily is sufficient for most use cases
  and is the floor that native Salesforce Backup supports. Sub-daily
  costs significantly more and is justified only when the business
  has explicitly committed to it.
- **Full-org snapshot vs targeted object backup.** Full-org is
  comprehensive but slow to restore at scale. Targeted backup of
  the highest-value objects (Accounts, Opportunities, Contracts)
  with daily cadence and a longer-cadence full-org snapshot is a
  cost-effective compromise.

## Anti-Patterns

1. **Treating Recycle Bin as a backup.** It is a delete buffer with
   a 15-day rolling, capacity-bounded window. It does not cover
   modifications or hard deletes.
2. **Self-rolled restore that ignores referential integrity.** Naive
   re-insert of CSVs in alphabetical order produces orphaned children
   on every lookup field.
3. **Buying a backup tool but never running a restore drill.** The
   tool's correctness is unknown until tested.
4. **Confusing sandbox refresh with DR.** Sandboxes are development
   resources; they are not a supported disaster-recovery target.
5. **Failing to plan for file content.** File storage is a parallel,
   often larger, dimension that is ignored in record-count-only
   capacity planning.

## Official Sources Used

- Salesforce Backup Overview — https://help.salesforce.com/s/articleView?id=sf.backup_overview.htm&type=5
- Recycle Bin (Records) — https://help.salesforce.com/s/articleView?id=sf.home_delete.htm&type=5
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Data Export (Weekly) — https://help.salesforce.com/s/articleView?id=sf.admin_exportdata.htm&type=5
- Backup Your Data — Trailhead — https://trailhead.salesforce.com/content/learn/modules/data-management/backup-your-data
- Salesforce Well-Architected Reliability — https://architect.salesforce.com/well-architected/trusted/resilient
