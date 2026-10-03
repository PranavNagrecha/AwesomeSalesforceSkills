# Well-Architected Notes — Nonprofit Cloud vs NPSP Migration

## Relevant Pillars

- **Adaptable (primary)** — this is a platform-foundation decision, not a project decision. NPSP is a managed package:
  its objects are namespaced, its automation is package Apex, and everything built on top depends on a codebase the
  organisation does not own. Nonprofit Cloud's objects are native standard objects — `GiftTransaction`,
  `GiftCommitment`, `Program`, `ProgramEnrollment` — which changes the upgrade model, the customisation model, and what
  a future integration can assume. The choice sets the constraints for the next decade, and nonprofits change platforms
  rarely.
- **Resilient** — the risk in this migration is not downtime. It is silent misattribution: soft credits, recurring
  commitments, and designations that load successfully and report incorrectly. That failure is discovered by a donor or
  an auditor, and it is expensive to unwind once fundraising has been operating on the data.
- **Automated** — the migration's repeatability is the whole safety margin. A conversion pipeline that can be re-run per
  entity, with reconciliation at each step, is what makes a cutover rehearsable. One-shot data loads are not.
- **Efficient** — effort is predicted by the customisation surface, not by record count. The number of NPSP namespace
  references across the metadata tree is the cheapest reliable estimate available, and it takes minutes to produce.

## Architectural Tradeoffs

**Migrate now vs stay and augment.** Staying on NPSP costs nothing today and accumulates: new platform capability
targets the native objects, and every year of additional NPSP-dependent customisation raises the eventual migration
price. Migrating costs a programme measured in quarters and buys a native foundation. The deciding variable is not
sentiment about NPSP — it is the size of the customisation surface, which only grows. An org with thin customisation
should move earlier than it wants to; an org with a decade of package-dependent automation should be honest that the
migration is a re-implementation.

**Big-bang vs per-entity conversion.** A single cutover is shorter and gives one reconciliation point, which is also a
single point of failure with no partial rollback. Per-entity conversion — constituents, then gifts, then commitments,
then soft credits, then programs — is longer, requires a period where two systems are authoritative for different
things, and lets each entity be signed off independently. Prefer per-entity, and be explicit about which system is
authoritative for what during the overlap, because ambiguity there produces the double-entry that reconciliation is
supposed to catch.

**Field-for-field fidelity vs modelling to the target.** Preserving every NPSP field keeps reports working and imports
the previous platform's compromises permanently. Modelling to the target's shape — `GiftCommitment` plus
`GiftCommitmentSchedule` rather than one recurring-donation record; `Benefit` / `BenefitAssignment` /
`BenefitDisbursement` rather than one service-delivery object — produces cleaner data and forces every report and
integration to be rebuilt. Migrate history at the fidelity the organisation genuinely reports on, not at the fidelity
the old schema happened to store.

**Prototype environment.** Developer Edition is the cheap prototype and is not listed as an edition where Program
Management is available; Fundraising is documented for Enterprise, Unlimited, and Developer Editions. Choosing the
prototype environment by cost rather than by module availability is a week nobody planned for.

## Anti-Patterns

1. **The mapping sheet written from memory.** `ProgramEngagement` is the NPSP object; `ProgramEnrollment` is the
   Nonprofit Cloud one. A plausible-but-wrong target name passes review, propagates into build tickets and integration
   specs, and is found by a compiler months later. Copy target names from the Nonprofit Cloud Developer Guide's
   standard-object lists.
2. **Estimating from record count.** Four hundred thousand gifts is a load-time question. The programme's cost lives in
   the formula fields, validation rules, report types, list-view filters, and external field mappings that reference
   `npsp__`, `npe03__`, or `pmdm__` — none of which the compiler will find for you.
3. **Migrating what the platform generates.** `GiftDefaultSoftCredit` describes soft credits the recurrence engine
   creates for commitment transactions. Loading the equivalent NPSP records as data double-counts precisely the
   attributions the organisation is most sensitive about.
4. **Reconciliation signed off by the migration team.** The team that moved the records can prove the records arrived.
   Only the fundraising lead can confirm the attribution is right, and attribution is where this migration fails.

## Official Sources Used

Read for this revision (2026-10-03):

- Nonprofit Cloud Developer Guide, Version 67.0 (Summer '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/nonprofit_cloud.pdf. Chapter 1 edition box; Chapter 2 data models (Grantmaking Application Form model introduced Spring '26, Individual Application "won't receive future platform enhancements"); Chapter 3 Fundraising (object list and API versions, GiftTransaction fields and `Status` values, GiftSoftCredit fields and `Role` values, GiftDefaultSoftCredit, Fundraising Access licence rule); Chapter 4 Program Management (object list, editions); Chapter 10 Group Memberships and Households (PartyRelationshipGroup, AccountContactRelation, ContactContactRelation, AccountAccountRelation, PartyRoleRelation); Chapter 11 Record Rollup Definitions (RecordAggregationDefinition, RecordAggregationResult, licence and permission).
- NPSP package source, Salesforce.org: https://github.com/SalesforceFoundation/NPSP (`cumulusci.yml` namespace and dependencies; `force-app/main/default/objects` and `force-app/tdtm/objects` listings via https://api.github.com/repos/SalesforceFoundation/NPSP/git/trees/main?recursive=1). Object and field names for soft credits, allocations, rollups, households, and trigger handlers.
- Program Management Module source, Salesforce.org: https://github.com/SalesforceFoundation/PMM (`sfdx-project.json` namespace `pmdm`; object listing).
- Outbound Funds Module source, Salesforce.org: https://github.com/SalesforceFoundation/OutboundFundsModule (`cumulusci.yml` namespace `outfunds`; object listing; repository description as an Open Source Commons project).

Earlier sources, verified 2026-08-14 by a previous revision and consistent with the PDF above:

- Nonprofit Cloud Developer Guide: Fundraising Standard Objects, https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud.meta/nonprofit_cloud/npc_fundraising_standard_objects.htm
- Nonprofit Cloud Developer Guide: Program Management Standard Objects, https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud.meta/nonprofit_cloud/npc_pm_standard_objects.htm
- Nonprofit Cloud Developer Guide: GiftDefaultSoftCredit, https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud.meta/nonprofit_cloud/npc_fundraising_api_objects_giftdefaultsoftcredit.htm

### Still not sourced here

NPSP option names (account model choices), the behaviour of TDTM exclusion fields, and household rollup field names come from NPSP documentation outside the package source and are marked UNVERIFIED where used. The package source shows what objects and fields exist, not how the package behaves; the installed package in the source org remains the authority for names.
