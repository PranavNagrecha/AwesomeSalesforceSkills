# Well-Architected Notes — Enterprise Territory Management

## Relevant Pillars

### Scalability

ETM must be designed with scale in mind from the start. The commonly cited ceiling — 1,000 territories per model by default, up to 20,000 on request — is **UNVERIFIED (2026-09-04): it does not appear in the Salesforce App Limits Cheat Sheet (a case-insensitive grep for "territor" across that document returns nothing) nor in the Metadata API or Object Reference sections for the Territory2 types.** Treat it as a planning assumption to confirm in Salesforce Help, not as a number to design a ceiling against. Territory hierarchies that are too deep (7+ levels) create complex forecast rollups and slow system-defined group recalculation. Account assignment rules evaluated across hundreds of thousands of accounts can produce multi-hour background jobs. Design hierarchies to be as flat as practical, and cluster rules by specificity to reduce evaluation time.

Large UserTerritory2Association tables (many users in many territories) also affect sharing group recalculation performance. Audit membership regularly and remove stale assignments.

### Operational Excellence

Territory management is an ongoing operational process, not a one-time setup. Seasonal territory realignments, rep turnover, and account data changes all require ongoing rule maintenance. The operational runbook should include:

- A defined change management process for territory restructuring (Planning state → preview run → stakeholder sign-off → activation window).
- A schedule for running assignment rules at the model level after bulk account imports or data cleansing operations.
- Monitoring of `Territory2AlignmentLog` as a health indicator — stale timestamps mean rules may not reflect current account data.
- Deployment of territory metadata (`Territory2Settings`, `Territory2Model`, `Territory2Type`, `Territory2`, `Territory2Rule`) as a **source deploy** between sandbox and production. Change sets and packaging are not available for these types, so the release train has to accommodate ETM rather than the reverse — and the deploying user needs Manage Territories.
- A standing check that the run after each deploy actually happened: Metadata API cannot run assignment rules, so a clean deploy with no follow-up run leaves the org configured and unassigned.

### Security

Territory membership grants at minimum Read access to assigned accounts regardless of ownership. This is the intended behavior, but it has security implications:

- An account assigned to a territory will be visible to all users who are territory members at that level or above (via TerritoryAndSubordinates sharing groups). Validate that territory boundaries align with your intended data access model.
- Territory access is additive — it cannot be used to restrict visibility below OWD. If your OWD for Account is Private and you need selective access, ETM provides it correctly. If OWD is Public Read/Write, territory membership has no restrictive effect.
- Access to related Opportunities, Contacts and Cases is set per territory on the `Territory2` component (`opportunityAccessLevel`, `contactAccessLevel`, `caseAccessLevel`, valid values `None` / `Read` / `Edit`), falling back to the `default*AccessLevel` fields in `Territory2Settings` when omitted. Over-provisioning — `Edit` where `Read` would do — is an anti-pattern, and it is invisible in the UI because each territory carries its own value.
- `Territory2ObjSharingConfig` is not that control. It is a `query`/`update`-only SOAP object (API 56.0+) for the objects enabled through `Territory2Settings.supportedObjects`, whose only documented `objectType` is `Lead`. Any runbook telling you to deploy it is describing something that does not exist.
- `t2ForecastAccessLevel` in `Territory2Settings` grants users in a parent territory access to opportunities assigned to its **child** territories "regardless of who owns the opportunities". `Edit` there is a much broader grant than it appears at the settings level; `View` is the conservative default.

### Reliability

The active territory model drives both account access and territory-based forecasting. A misconfigured model or an unfinished assignment run can silently produce incorrect forecast data and unexpected access gaps. Reliability controls include:

- Running assignment rules in preview mode before activation to validate expected coverage.
- Not archiving a model until a replacement model has been activated and verified.
- Using `Territory2AlignmentLog` queries to confirm job completion before treating post-activation data as authoritative.
- Testing territory model metadata deployment in a sandbox with production-equivalent data volumes before promoting to production.

---

## Architectural Tradeoffs

**Single active model constraint vs. flexibility:**
Only one territory model can be Active at a time. Organizations that want to pilot a new territory structure alongside the current one cannot run both as Active simultaneously. The Planning state supports preview mode, but it is not a live parallel model. Workaround: complete the transition in a single activation event, with thorough preview testing beforehand.

**Flat vs. deep hierarchy:**
Deeper hierarchies provide more granular territory management but increase the complexity of forecast rollups, system-defined group recalculations, and assignment rule evaluation time. Flat hierarchies are operationally simpler but may require more rule complexity to achieve the same account coverage. For most orgs, 3–5 levels is sufficient.

**Rule-based vs. manual assignment:**
Rule-based assignment is maintainable at scale but requires accurate, consistently populated account field data (especially BillingState, Industry, or custom fields). Manual assignment is precise but does not scale beyond small account lists. Named account overlays typically use a hybrid: a custom account field marks the named account owner, and an assignment rule evaluates that field.

**Territory forecast vs. role hierarchy forecast:**
Territory-based forecasting decouples the forecast hierarchy from the org chart. This is powerful when sales territories don't align with the role hierarchy, but it requires a separate forecast type, separate forecast user enablement, and the loss of forecast sharing. Organizations with both a geo field team and a named account team may need two separate territory-based forecast types (one per branch) rather than one unified forecast.

---

## Anti-Patterns

1. **Building the territory hierarchy to match the role hierarchy** — ETM is most valuable when the territory structure is independent of the org chart. Mirroring the role hierarchy in territories adds maintenance burden without benefit; account visibility via the role hierarchy already exists through OWD + sharing rules. Use ETM to cover access patterns that the role hierarchy cannot handle, such as cross-regional named account coverage or overlay teams.

2. **Activating a model during business hours on a large org** — Activation triggers immediate full rule recalculation. Running this during business hours on an org with 100,000+ accounts can slow account save operations (which trigger individual rule evaluation), produce hours of inconsistent territory assignment data, and disrupt sales reps who expect accurate territory visibility. Always activate in a planned off-peak maintenance window.

3. **Using Archive as a "disable" action** — Archiving a model is permanent. Organizations that archive their planning model thinking they can restore it later discover this is not possible. The correct action to temporarily stop using a model is to leave it in Planning state. Only archive models you are certain will never be needed again.

---

## Official Sources Used

- **Metadata API Developer Guide (Summer '26 / v62)** — `Territory2` (access-level enums and their OWD constraints, `parentTerritory` developer-name rule, `ruleAssociations` / `Territory2RuleAssociation.inherited`, `objectAccessLevels`, "triggers … do not fire during a deploy()", "don't support packaging or change sets"), `Territory2Model` ("initial state is Planning", deploy permitted only for Planning or Active, retrieve state exclusions, cascade delete, developer-name conflict), `Territory2Rule` (`active` / `booleanFilter` / `objectType` Account-only / `ruleItems`, the `FilterOperation` enumeration, the 10-rule-item cap, implicit sort order, "Rules can't be run via Metadata API", relaxed FLS for deploy), `Territory2Type` (`priority` required, unique, highest wins, ties assign nothing), `Territory2Settings` (`enableTerritoryManagement2` exclusivity, `default*AccessLevel`, `opportunityFilterSettings`, `supportedObjects` = Lead only, `t2ForecastAccessLevel`, `tm2BypassRealignAccInsert`, `tm2EnableUserAssignmentLog`). Supports Scalability, Operational Excellence, Security and Reliability above, and every XML block in `references/metadata-examples.md`.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Object Reference for the Salesforce Platform (Summer '26 / v62)** — `Territory2Model.State` full picklist and `LastRunRulesEndDate` / `LastOppTerrAssignEndDate` (the audit checks in Mode 2), `Territory2` access-level picklist spellings that differ from Metadata API (Gotcha 8), `Territory2AlignmentLog` fields (the completion check), `ObjectTerritory2Association.AssociationCause` and its 12-hour post-delete query window, `UserTerritory2Association` supported calls and `RoleInTerritory2` values (Gotcha 14), `ObjectTerritory2AssignmentRule` vs the legacy `AccountTerritoryAssignmentRule` whose `TerritoryId` points at `Territory` (Gotcha 6), `Territory2ObjSharingConfig` (Gotcha 13), `AccountShare.RowCause` values `Territory` / `Territory2AssociationManual` / deprecated `TerritoryManual` (the Security section and the verification SOQL), `Opportunity.IsExcludedFromTerritory2Filter`.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Apex Reference Guide (Summer '26 / v62)** — `TerritoryMgmt.OpportunityTerritory2AssignmentFilter` and the `OppTerrAssignDefaultLogicFilter` reference implementation. Grounds the claim that filter-based OTA is Apex rather than configuration (Gotcha 10), the three-valued return-map contract, and the direction of territory type priority (`Priority > tp.priority` — highest integer wins), which corrects the earlier "lower integer = higher priority" statement in this skill.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apexrefguide.pdf
- **Bulk API 2.0 and Bulk API Developer Guide (Summer '26 / v62)** — "Updating territory hierarchies" listed among the operations that increase lock contention and may require serial concurrency mode; `ObjectTerritory2Association` listed among the objects that support PK chunking. Supports the realignment-window guidance in Gotcha 14 and the Scalability section.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_asynch.pdf
- **Salesforce App Limits Cheat Sheet (Summer '26 / v62)** — used as a *negative* source: it contains no territory allocations at all, which is why the territory-count ceiling in this skill now carries an UNVERIFIED marker instead of a bare number.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- **Salesforce Sales Territories Implementation Guide** — territory model states, assignment rule behaviour, forecast by territory. Supports the model-lifecycle and forecast framing in Core Concepts.
  https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_implementing_territory_mgmt2_guide.pdf
- **Salesforce Well-Architected** — the pillar framing used to organise this file.
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- **Local knowledge: Salesforce Record Access Under the Hood** — territory system-defined sharing groups (Territory group, TerritoryAndSubordinates group). Supports the group-recalculation cost discussion in Scalability. Cross-referenced against `admin/sharing-and-visibility` rather than restated here.
