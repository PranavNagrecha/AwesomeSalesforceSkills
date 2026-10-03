# Well-Architected Notes — Migration Architecture Patterns

## Relevant Pillars

- **Reliability** — The pre-migration metadata audit and per-phase
  rollback plan are the two highest-yield reliability investments.
  Every cutover wave should be reversible to the previous wave's
  state; a migration without rollback is a one-shot bet, not an
  engineering plan.
- **Security** — Regulatory splits depend on the architecture
  enforcing the boundary, not policy. A "we won't query the
  protected data" guarantee that requires people to remember the
  rule is weaker than an architecture where the path to the
  protected data physically doesn't exist.
- **Operational Excellence** — Coexistence bridges are operational
  debt; budget for ongoing maintenance, not just initial build.
  Schema drift between orgs is constant; bridge availability,
  conflict resolution, and dead-letter handling are perpetual
  responsibilities.

## Architectural Tradeoffs

- **Hard cutover vs phased coexistence.** Hard cutover is faster
  and cheaper to operate; risk is concentrated at one moment.
  Phased coexistence spreads risk over time at the cost of running
  two systems with a bridge between them. Volume + complexity
  decide; small migrations rarely justify coexistence.
- **External-Id remapping vs Salesforce-Id replacement.** Remapping
  via external-Id is more work upfront but produces a stable
  reference for the lifetime of any external system. Direct
  Salesforce-Id replacement is faster but breaks every external
  system that didn't get updated in lockstep.
- **Wave size: small (1% pilot, 10% wave 1) vs large (50% wave 1).**
  Small waves de-risk by surfacing problems early; large waves
  finish faster. Pilot + small waves are the right default unless
  the team has high confidence from previous migrations.
- **Bridge richness in coexistence.** A minimal bridge (identity +
  one-way data sync) is easier to operate but constrains user
  experience. A rich bridge (bidirectional sync, cross-org search,
  cross-org reporting) gives a unified experience at multiplicative
  ongoing cost.

## Anti-Patterns

1. **Moving data before completing the metadata audit.** Validation
   rules / required fields / picklist mismatches cause large-scale
   row failures. Audit first.
2. **Discovering external-system Id references during cutover.**
   Inventory external systems explicitly; surface every place a
   Salesforce Id is stored before migration begins.
3. **Bulk migrating with target-org automation enabled.** Welcome
   emails on records that are not new; auto-stamps overwriting
   migrated values; sub-record auto-creation duplicating records.
   Disable for the window.
4. **Regulatory split with a runtime bridge to protected data.**
   The bridge IS access; it defeats the isolation.
5. **Coexistence design without sunset or ownership commitment.**
   Becomes legacy that nobody owns; bridges drift and break.
6. **Decommissioning source orgs without exporting retention-required
   audit logs.** Field History, Setup Audit Trail, Login History are
   org-bound; export before decommission.

## Official Sources Used

Read for this revision (2026-10-03):

- Salesforce Object Reference, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf. ID field type (15-character case-sensitive, 18-character case-safe); System Fields, Audit Fields (Set Audit Fields upon Record Creation procedure, object list, `systemModstamp` exception, date range); SetupAuditTrail (at least 180 days; aggregate limits); PartnerNetworkConnection.
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. ExternalDataSource `type` values (`SfdcOrg` cross-org adapter distinct from `OData` and `OData4`).
- Best Practices for Deployments with Large Data Volumes (Summer '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_large_data_volumes_bp.pdf. Best Practices > Loading Data from the API (disable triggers, workflow, and validations during loads; load order; Public Read/Write during initial load; group children by parent); defer sharing calculation; External IDs indexed.
- Salesforce Data Loader Guide (Summer '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_data_loader.pdf. Configure Data Loader (Time Zone, Assignment rule); upsert matching on external IDs and related-object external IDs.
- Platform Events Developer Guide, Version 66.0 (Spring '26): local corpus `knowledge/imports/platform-events.md`. 72-hour retention for high-volume events; stream reset and unrelated replay IDs after org migration, instance refresh, or sandbox refresh.
- Big Objects Implementation Guide, Version 66.0: local corpus `knowledge/imports/salesforce-big-objects-guide.md`. Salesforce Connect cannot reach big objects in another org; supported APIs.
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (a direct fetch does not return the guide page; read via Wayback snapshot 2026-06-16).

Listed in the original version and not re-read for this revision (Salesforce Help does not fetch; the Architects decision-guide pages were not opened); no claim in this revision rests on them alone:

- Multi-org Strategy (Salesforce Architects) — https://architect.salesforce.com/decision-guides/multi-org-strategy
- Data 360 Provisioning Decision Guide — https://architect.salesforce.com/decision-guides
- How to Prepare for a Salesforce Org Migration — https://help.salesforce.com/s/articleView?id=000386897&type=1
- Salesforce Connect (cross-org adapter) — https://help.salesforce.com/s/articleView?id=sf.platform_connect_about.htm&type=5
- Platform Events overview: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/ (same guide read from the local corpus above)
- Salesforce Identity (SSO) — https://help.salesforce.com/s/articleView?id=sf.identity_overview.htm&type=5
- Hyperforce overview — https://help.salesforce.com/s/articleView?id=sf.hyperforce_overview.htm&type=5
- Sibling skill (multi-org strategic decision) — `skills/architect/multi-org-strategy/SKILL.md`
- Sibling skill (cutover ops) — `skills/devops/go-live-cutover-planning/SKILL.md`
