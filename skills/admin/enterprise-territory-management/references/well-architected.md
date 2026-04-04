# Well-Architected Notes — Enterprise Territory Management

## Relevant Pillars

### Scalability

ETM must be designed with scale in mind from the start. The 1,000-territory-per-model limit (default) is a hard ceiling in Enterprise Edition — exceeding it requires a Salesforce Support request to raise the limit for Performance/Unlimited editions (up to 20,000). Territory hierarchies that are too deep (7+ levels) create complex forecast rollups and slow system-defined group recalculation. Account assignment rules evaluated across hundreds of thousands of accounts can produce multi-hour background jobs. Design hierarchies to be as flat as practical, and cluster rules by specificity to reduce evaluation time.

Large UserTerritory2Association tables (many users in many territories) also affect sharing group recalculation performance. Audit membership regularly and remove stale assignments.

### Operational Excellence

Territory management is an ongoing operational process, not a one-time setup. Seasonal territory realignments, rep turnover, and account data changes all require ongoing rule maintenance. The operational runbook should include:

- A defined change management process for territory restructuring (Planning state → preview run → stakeholder sign-off → activation window).
- A schedule for running assignment rules at the model level after bulk account imports or data cleansing operations.
- Monitoring of `Territory2AlignmentLog` as a health indicator — stale timestamps mean rules may not reflect current account data.
- Deployment of territory metadata (Territory2Model, Territory2Type, Territory2, AccountTerritoryAssignmentRule) via Metadata API between sandbox and production to ensure consistency and auditability.

### Security

Territory membership grants at minimum Read access to assigned accounts regardless of ownership. This is the intended behavior, but it has security implications:

- An account assigned to a territory will be visible to all users who are territory members at that level or above (via TerritoryAndSubordinates sharing groups). Validate that territory boundaries align with your intended data access model.
- Territory access is additive — it cannot be used to restrict visibility below OWD. If your OWD for Account is Private and you need selective access, ETM provides it correctly. If OWD is Public Read/Write, territory membership has no restrictive effect.
- `Territory2ObjSharingConfig` controls whether territory members get Read or Read/Write access to related Opportunities and Contacts. Over-provisioning (granting Read/Write when only Read is needed) is an anti-pattern.

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

- Salesforce Sales Territories Implementation Guide (Spring '26) — territory model states, limits, assignment rules, opportunity territory assignment, forecast by territory, metadata deployment
  URL: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_implementing_territory_mgmt2_guide.pdf
- Salesforce Help: Allocations and Considerations for Territories — numeric limits (territories per model, active model constraint)
  URL: https://help.salesforce.com/s/articleView?id=sf.tm2_allocations.htm&language=en_US&type=5
- Salesforce Help: Territory Hierarchy — hierarchy structure and parent-child relationships
  URL: https://help.salesforce.com/s/articleView?id=sales.tm2_territory_hierarchy.htm&language=en_US&type=5
- Salesforce Help: Setting Up and Managing Territory Assignments — assignment rules behavior
  URL: https://help.salesforce.com/s/articleView?id=sales.tm2_assign_accounts_to_territories.htm&language=en_US&type=5
- Salesforce Record Access Under the Hood (local knowledge) — territory system-defined sharing groups (Territory group, TerritoryAndSubordinates group)
- Salesforce Well-Architected Overview — architecture quality framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Metadata API Developer Guide — Territory2 metadata types and deployment
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Object Reference (AccountTerritoryAssignmentRule) — assignment rule object semantics
  URL: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_accountterritoryassignmentrule.htm
