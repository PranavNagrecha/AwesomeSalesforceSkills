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

- Multi-org Strategy (Salesforce Architects) — https://architect.salesforce.com/decision-guides/multi-org-strategy
- Data 360 Provisioning Decision Guide — https://architect.salesforce.com/decision-guides
- How to Prepare for a Salesforce Org Migration — https://help.salesforce.com/s/articleView?id=000386897&type=1
- Salesforce Connect (cross-org adapter) — https://help.salesforce.com/s/articleView?id=sf.platform_connect_about.htm&type=5
- Platform Events overview — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/
- Salesforce Identity (SSO) — https://help.salesforce.com/s/articleView?id=sf.identity_overview.htm&type=5
- Hyperforce overview — https://help.salesforce.com/s/articleView?id=sf.hyperforce_overview.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Sibling skill (multi-org strategic decision) — `skills/architect/multi-org-strategy/SKILL.md`
- Sibling skill (cutover ops) — `skills/devops/go-live-cutover-planning/SKILL.md`
