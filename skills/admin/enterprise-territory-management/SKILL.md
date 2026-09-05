---
name: enterprise-territory-management
description: "Use when configuring or troubleshooting Salesforce Enterprise Territory Management (ETM): territory models, territory types, territory hierarchies, account assignment rules, opportunity territory assignment, and forecast by territory. Trigger keywords: territory model, territory hierarchy, ETM, assign accounts to territories, territory forecast, territory activation. NOT for choosing the coverage model first — use admin/territory-design-requirements. NOT for role hierarchy — use admin/sharing-and-visibility. NOT for Field Service ServiceTerritory — use admin/fsl-service-territory-setup. Trigger keywords: Territory2, Territory2Model, Territory2Rule, territory2Model-meta.xml, ObjectTerritory2Association, UserTerritory2Association, territory assignment rule, run assignment rules, territory access level, Manage Territories permission."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Operational Excellence
triggers:
  - "how do I set up territory management in Salesforce for our sales team"
  - "accounts are not being assigned to the correct territory automatically"
  - "I need to configure forecast by territory instead of by role hierarchy"
  - "what is the difference between territory types and territory hierarchy"
  - "I activated the territory model and now assignment rules are running again"
  - "how do I deploy territory model configuration between sandboxes"
  - "territory model isn't working"
  - "territory model won't deploy - model is archived in production"
  - "Territory2 doesn't show up in my change set component list"
  - "opportunities have no territory so they're missing from the territory forecast"
  - "write the territory2Model and territory2Rule metadata xml for a new model"
  - "accounts loaded by data loader never got a territory assigned"
  - "which territory wins when an account is in two territories"
  - "deploy failed - invalid value Read Only for accountAccessLevel"
  - "user still sees territory accounts after I removed them from the territory"
tags:
  - territory-model
  - account-assignment-rules
  - territory-forecast
  - territory-hierarchy
  - opportunity-territory
  - etm
inputs:
  - org feature enablement status (ETM enabled vs Legacy Territory Management)
  - "territory model design (geographic, named account, overlay, or hybrid)"
  - account field values used as assignment rule criteria
  - forecast type configuration (role-based vs territory-based)
  - Salesforce editions (Enterprise, Performance, Unlimited)
outputs:
  - configured territory model with territory types and hierarchy
  - account assignment rules that auto-assign accounts to territories
  - territory member assignments for users
  - territory-based forecast configuration guidance
  - deployment guidance for territory metadata via Metadata API
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Enterprise Territory Management

This skill activates when a practitioner needs to design, configure, audit, or troubleshoot Salesforce Enterprise Territory Management (ETM). It covers territory models, territory types, hierarchy design, account assignment rules, opportunity territory assignment, user territory membership, and forecast by territory.

---

## Before Starting

Gather this context before working on anything in this domain:

- **ETM must be enabled in the org.** ETM is a separate feature from Legacy (Original) Territory Management. The two cannot coexist — check Setup > Territory Management. If it shows "Enterprise Territory Management," ETM is active. Legacy Territory Management is no longer recommended.
- **Only one territory model can be Active at a time.** All other models remain in Planning or Archived state. Activating a model triggers a full background recalculation of all account assignment rules.
- **Territory forecast is separate from role hierarchy forecast.** A territory-based Forecast Type must be configured independently. Forecast hierarchy is derived from the active territory model.
- **Deployment mechanism is decided for you.** Every Sales Territories metadata type repeats the same Usage sentence — "Sales Territories components don't support packaging or change sets and aren't supported in CRUD calls" (Metadata API Developer Guide, `Territory2` / `Territory2Model` / `Territory2Rule` / `Territory2Type` / `Territory2Settings`). ETM ships as a source deploy, and `deploy()` requires the Manage Territories permission.
- **Limits:** UNVERIFIED (2026-09-04): the commonly cited figures — 1,000 territories per model by default, up to 20,000 on request for Performance/Unlimited — do not appear in the Salesforce App Limits Cheat Sheet (a case-insensitive grep for "territor" across it returns nothing) or in the Metadata API and Object Reference sections for the Territory2 types. Confirm the current allocation in Salesforce Help before designing to a ceiling. What *is* documented: only one model can be in `Active` state, and `Territory2Type.priority` must be unique across types.

---

## Questions to Ask Before Configuring

Ask these before opening Setup. Each one maps to a documented behaviour that will otherwise be discovered after activation, when the model is live and the recalculation is running.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is the developer name of this model, and does a model with that name already exist in production — in what state?" | `deploy()` works only on models in `Planning` or `Active`; a same-named model sitting in `Archived` blocks the deploy permanently, and developer names are unique so Metadata API can't create around it | A version-stamped developer name and a `SELECT DeveloperName, State FROM Territory2Model` result from the target org |
| "How does this change reach production — change set or source deploy?" | Sales Territories components can't go in a change set or a package, and `deploy()` needs Manage Territories | A source-deploy plan and a named person who holds Manage Territories |
| "What is the org-wide default for Account, and for Opportunity, Contact and Case?" | OWD narrows which `accountAccessLevel` values are legal, and for some objects the guide requires the element to be omitted entirely | The exact access-level element set per territory, in Metadata API spelling — not the Setup labels |
| "Must an opportunity land in exactly one territory, and who is writing the Apex?" | Filter-based OTA is an Apex class implementing `TerritoryMgmt.OpportunityTerritory2AssignmentFilter` wired into `Territory2Settings.opportunityFilterSettings`; there is no declarative filter | An owner for the class, or a decision to assign `Opportunity.Territory2Id` some other way |
| "What integer does each territory type get, and can one account end up in two territories of the same type?" | Priority must be unique per type, the *highest* integer wins, and a tie at the top assigns no territory at all | A priority table plus a tie query run against real multi-territory accounts |
| "Who runs the assignment rules after the deploy lands, and in what window?" | "Rules can't be run via Metadata API" — the deploy installs rules and assigns nothing; the run is user-initiated and logged in `Territory2AlignmentLog` | A named runner, a window, and a completion check that reads the log rather than assuming |
| "Are Leads in scope, and is `tm2BypassRealignAccInsert` set anywhere in the settings we are inheriting?" | Lead assignment is a separate `supportedObjects` switch; the bypass flag stops account rules during insert jobs org-wide with no error | A reviewed `Territory2.settings` file rather than one copied forward from another org |

What a proper configuration adds over just building the model in Setup: the territory metadata is source-controlled and deployable on a path that actually exists, the access levels are legal for the org's sharing model instead of rejected at deploy, opportunities reach the forecast because someone owns the assignment mechanism, and the post-deploy rule run is a scheduled step with a completion check rather than an assumption.

---

## Core Concepts

### Territory Model

A territory model is the top-level container for your entire territory structure. It holds all territory types, the territory hierarchy, and all account assignment rules. A model progresses through three states:

- **Planning** — model is being designed; assignment rules can be run in preview mode without affecting live data or access.
- **Active** — model is live; assignment rules execute automatically on account create/update, and the model drives account-territory relationships, user access, and territory forecasting. Only one model can be in this state at a time.
- **Archived** — model is retired and read-only. Archiving cannot be reversed — an archived model cannot be reactivated.

The `Territory2Model.State` picklist is wider than those three. The Object Reference lists `Planning`, `Activating`, `Activation Failed`, `Active`, `Archiving`, `Archiving Failed`, `Archived`, `Deleting`, `Deletion Failed`. An audit that tests only for `Active` misreads a stuck `Activating` or a failed `Activation Failed` as "no active model". Metadata API `retrieve()` returns nothing at all for models in `Cloning`, `Cloning Failed`, `Deleting` or `Deletion Failed`.

Transitioning a model from Planning to Active triggers an immediate background recalculation of all assignment rules across the entire model. For large orgs this can take hours. Monitor `Territory2AlignmentLog` for completion status; the model itself stamps `LastRunRulesEndDate` when a rule run finishes and `LastOppTerrAssignEndDate` when the opportunity filter last ran.

### Territory Types

Territory types are a categorization layer — they do not appear in the territory hierarchy itself, but every territory must be assigned a type. Types help you organize and report on territories by business meaning. Common examples:

- **Geographic** — regions such as "US West" or "EMEA North"
- **Named Account** — accounts owned by specific reps regardless of geography
- **Industry Overlay** — cross-functional coverage (e.g., Healthcare Overlay)

Each territory type has a required **priority** (integer), and the direction is the opposite of most people's intuition. The Metadata API guide: "The account-assigned territory whose territory type priority is highest is then assigned to the opportunity. The `priority` field value on each territory type must be unique." The Apex Reference Guide's reference filter confirms it in code — it keeps the territory whose `Territory2.Territory2Type.Priority` is numerically greater. So give the level that should win opportunity territory assignment the **largest** integer. Two territories tied at the top priority assign no territory at all.

### Territory Hierarchy

The territory hierarchy defines parent-child relationships between territories within a model. Parent territories do not automatically propagate access or rules down to child territories — each level must be explicitly configured.

For each territory, Salesforce creates two system-defined sharing groups:
- **Territory group** — direct members of that territory.
- **TerritoryAndSubordinates group** — members of that territory and all territories below it in that branch.

These groups drive record access calculations. Modifying territory membership triggers recalculation of these groups, which can add latency in large orgs.

### Account Assignment Rules

Account assignment rules are filter-based criteria that automatically assign accounts to territories based on account field values (standard or custom). In Metadata API the type is `Territory2Rule`; the corresponding SOAP objects are `ObjectTerritory2AssignmentRule` and `ObjectTerritory2AssignmentRuleItem`. `AccountTerritoryAssignmentRule` is a **different, legacy** object — its `TerritoryId` points at the pre-ETM `Territory`, not `Territory2`.

A rule belongs to the **model**, not to a territory: the file lives in the model's `rules` folder and carries `Territory2ModelId`, while the link to a territory is a separate `ruleAssociations` entry on each `Territory2` (with an `inherited` flag). A rule with no association deploys cleanly and assigns nothing.

Key behaviors:

- Rules can run **automatically** when an account is created or updated (controlled by the `active` flag in metadata / `IsActive` on the object). The documented exception: a record whose `IsExcludedFromRealign` is true is skipped entirely.
- A rule can hold **up to 10 rule items**, and their sort order "is implicitly derived from the position of the rule items in the XML" — reordering them silently renumbers a `booleanFilter` such as `(1 AND 2) OR 3`.
- `objectType` is documented as `Account` only.
- Rules can also be **run manually** for a single territory or the entire model.
- If an account matches rules for multiple territories, it is assigned to **all matching territories**.
- Rules are **not retroactive** — creating or modifying a rule does not apply it to existing accounts. A manual rule run is required to backfill.
- Accounts can also be **manually assigned** to territories, independent of rules.

### Opportunity Territory Assignment (OTA)

Opportunity territory assignment links an opportunity to a territory, which is required for the opportunity to appear in territory-based forecasts. OTA can be:

- **Filter-based (automatic):** an **Apex class** implementing `TerritoryMgmt.OpportunityTerritory2AssignmentFilter`, named in `Territory2Settings.opportunityFilterSettings` (`apexClassName`, `enableFilter`, `runOnCreate`, `runMultiThreaded`). There is no declarative filter builder. Salesforce passes only opportunities whose `IsExcludedFromTerritory2Filter` is false, and the returned `Map<Id,Id>` is three-valued: a territory Id assigns, a `null` **clears** the existing `Territory2Id`, and an opportunity absent from the map keeps what it had.
- **Manual:** Users or automation can set the `Territory2Id` field on an opportunity directly.

Opportunities not assigned to any territory do not appear in territory forecasts. Monitor `Opportunity.Territory2Id` population as a key data quality metric.

### Forecast by Territory

Territory-based forecasting uses the active territory model's hierarchy as the forecast hierarchy — entirely independent of role hierarchy forecasting. You configure a **Forecast Type** in Setup > Forecasts Settings with the territory hierarchy as the source.

Important constraints:
- Forecast **sharing is not available** for territory-based forecast types, unlike role-based forecasts.
- Users must be both territory members and enabled as forecast users.
- The forecast hierarchy reflects the territory hierarchy of the active model; switching the active model restructures the forecast hierarchy.

### Access and Sharing via Territory Membership

When a user is assigned as a member of a territory, Salesforce grants them access to accounts assigned to that territory regardless of account ownership. The level is set per territory, on the `Territory2` component itself: `accountAccessLevel` (`Read` / `Edit` / `All`), `opportunityAccessLevel`, `contactAccessLevel` and `caseAccessLevel` (`None` / `Read` / `Edit`). An omitted element falls back to the matching `default*AccessLevel` in `Territory2Settings`.

`Territory2ObjSharingConfig` is **not** the metadata for that. It is a SOAP object (API 56.0+, `query`/`update` only) hanging off `TerritoryMgmtObjectConfig`, covering the objects enabled through `Territory2Settings.supportedObjects` — where the guide states "The only supported object type is `Lead`." Its Metadata API counterpart is `Territory2.objectAccessLevels` (API 57.0+).

The share rows this produces on Account carry `RowCause` `Territory` (granted by an assignment rule) or `Territory2AssociationManual` (granted by a manual account-to-territory assignment; it replaced the deprecated `TerritoryManual` in API version 45.0). Those two values are how you prove territory access in an audit.

Territory membership is always **additive** — it cannot restrict access below the org-wide default (OWD). Where the OWD floor already grants the access, the territory adds nothing; where it does not, the territory's access level applies. Sizing the recalculation that a large membership change triggers is the same exercise as any sharing recalculation — see `admin/sharing-and-visibility`.

---

## Mode 1 — Set Up a Territory Model

Use this mode when building ETM from scratch or standing up a new territory structure.

**Step 1 — Enable ETM.** Navigate to Setup > Territory Management and enable Enterprise Territory Management. This is a one-way migration if Legacy Territory Management was previously active.

**Step 2 — Define Territory Types.** Create territory types that reflect your go-to-market segmentation. Assign unique priority integers, largest = wins OTA. Every territory must have a type. Shape the files from `references/metadata-examples.md` §2.

**Step 3 — Create the Territory Model.** Create a new model in Planning state. All configuration happens while in Planning — safe to iterate on without impacting live access or forecasts.

**Step 4 — Build the Territory Hierarchy.** Create territories within the model. Assign each a territory type. Set up parent-child relationships to reflect coverage structure. Avoid hierarchies deeper than 5–6 levels — complexity increases in forecasting rollups and access management.

**Step 5 — Configure Assignment Rules.** Create `Territory2Rule` components in the model's `rules` folder based on Account field criteria (e.g. `BillingCountry equals United States`), then associate each to its territories through `ruleAssociations` on the `Territory2`. Mark rules `active` for automatic execution on account create/update. Run rules in preview first to validate expected assignments before activating the model.

**Step 6 — Assign Users to Territories.** Insert `UserTerritory2Association` records for each rep and manager — this is data, not metadata, so it moves by Data Loader or Apex. `RoleInTerritory2` is a picklist: `Owner`, `Administrator`, `Sales Rep`. Users can belong to multiple territories. The object supports no `update()` call, so a role change is delete + insert.

**Step 7 — Set Access Levels.** Set `opportunityAccessLevel`, `contactAccessLevel` and `caseAccessLevel` on each `Territory2`, in Metadata API spelling (`None` / `Read` / `Edit`), and confirm they are legal for the org's OWD. Omit the element where the guide requires no value; the fallback is `Territory2Settings`.

**Step 8 — Activate the Model.** Activate the territory model. This triggers background assignment recalculation. Monitor `Territory2AlignmentLog`. Plan activation for off-peak windows on large orgs.

**Step 9 — Configure Forecast Type (if using territory forecasts).** In Setup > Forecasts Settings, add a Forecast Type using the territory hierarchy. Enable forecast users for territory managers.

---

## Mode 2 — Review / Audit Territory Configuration

Use this mode when auditing an existing ETM setup for correctness or scale.

**Check model state.** Query `Territory2Model` for `State` field. Confirm exactly one model has `State = 'Active'`.

**Audit territory count.** `SELECT COUNT() FROM Territory2 WHERE Territory2ModelId = '<modelId>'` — compare against the ceiling you confirmed for this org rather than a remembered number (see the Limits note in Before Starting).

**Review assignment rule coverage.** Query `ObjectTerritory2AssignmentRule` filtered by `Territory2ModelId` — not `AccountTerritoryAssignmentRule`, which is the legacy object. Verify rules with expected auto-execution are marked `IsActive = true`, and that every rule is associated to at least one territory.

**Check last rule run.** Review `Territory2AlignmentLog` (`StartTime`, `EndTime`, `Status`, `RunAsId`; `Territory2Id` is null for a model-level run) and `Territory2Model.LastRunRulesEndDate`. Stale timestamps indicate rules have not run since recent account data changes.

**Audit user memberships.** Query `UserTerritory2Association` to confirm expected reps are assigned to expected territories.

**Verify opportunity territory assignment.** Check `Opportunity.Territory2Id` population rate on open opportunities. Unpopulated opportunities will not appear in territory forecasts.

| Check | SOQL / Navigation | Flag If |
|---|---|---|
| Active model count | `SELECT Id, Name, State FROM Territory2Model WHERE State != 'Archived'` | More than 1 `Active`, or any model stuck in `Activating` / `Activation Failed` |
| Territory count per model | `SELECT COUNT() FROM Territory2 WHERE Territory2ModelId = :modelId` | Growing without an agreed ceiling (see the Limits note in Before Starting) |
| Rules that assign nothing | `SELECT Id, DeveloperName FROM ObjectTerritory2AssignmentRule WHERE Territory2ModelId = :modelId` compared against `ruleAssociations` in source | A rule with no territory association |
| Unassigned accounts | `SELECT COUNT() FROM Account WHERE Id NOT IN (SELECT AccountId FROM ObjectTerritory2Association)` | Unexpectedly large |
| Open opps without territory | `SELECT COUNT() FROM Opportunity WHERE Territory2Id = null AND IsClosed = false` | Unexpectedly large |

---

## Mode 3 — Troubleshoot Assignment and Sharing Issues

Use this mode when accounts are not assigned to expected territories, users lack expected access, or territory forecasts show missing data.

**Accounts not assigning automatically:**
- Confirm `IsActive = true` on the `ObjectTerritory2AssignmentRule`, and that a `ruleAssociations` entry points at it from the territory you expect.
- Confirm the territory model is in Active state (not Planning, and not stuck in `Activating`).
- Check `IsExcludedFromRealign` on the account — a true value stops rules from evaluating that record at all.
- Check `tm2BypassRealignAccInsert` in `Territory2.settings` — if true, rules don't run during account insert jobs, so anything loaded stays unassigned with no error.
- Rules are not retroactive — existing accounts require a manual rule run after a new rule is created.
- Check that account field values match rule criteria exactly (case sensitivity on text/picklist values).

**Users missing access to territory accounts:**
- Confirm the user has a `UserTerritory2Association` record for the territory, with `IsActive = true`.
- Verify the access-level field for the object on the `Territory2` itself (`opportunityAccessLevel`, `contactAccessLevel`, `caseAccessLevel`) — and whether it was omitted, in which case the `Territory2Settings` default applies.
- Query `AccountShare` for `RowCause IN ('Territory','Territory2AssociationManual')` to see whether the share row exists at all.
- Remember: territory membership adds access but cannot override OWD Private if OWD is more restrictive than the territory config.

**Forecast missing accounts or opportunities:**
- Verify open opportunities have `Territory2Id` populated.
- Confirm the territory is in the Active model's hierarchy.
- Confirm the user is both a territory member and an enabled forecast user.
- Remember: territory forecast sharing is not supported — this is expected behavior, not a bug.

**Opportunity has no territory:**
- Confirm `Territory2Settings.opportunityFilterSettings.enableFilter` is true and `apexClassName` names a deployed class.
- Check `Opportunity.IsExcludedFromTerritory2Filter` — excluded opportunities are never passed to the filter.
- Check for a priority tie: if the account sits in two territories whose types share the top priority, the documented outcome is no territory assigned.

**Assignment ran but accounts went to wrong territory:**
- Check for multiple matching rules — accounts are assigned to all matching territories, not just one.
- Check for manual assignments that may conflict with rule-based intent.
- Review territory type priority values if OTA is producing unexpected results.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Sales reps cover fixed geographic regions | Geographic territory type with BillingState/Country-based rules | Simple criteria, easy to maintain |
| Named account coverage alongside geo | Separate territory type for named accounts; configure as overlay | Keeps named account lists distinct from geo hierarchy |
| Testing territory redesign without disrupting live model | Create new model in Planning state; run rules in preview | Only one model can be Active; Planning state is safe |
| Backfilling accounts after new rule creation | Manually run assignment rules at model level | Rules are not retroactive by default |
| Territory-based forecasting without changing role hierarchy | Add territory Forecast Type in Forecasts Settings | ETM forecast is entirely independent of role hierarchy forecast |
| Promoting territory config to production | Source deploy of `Territory2Model`, `Territory2Type`, `Territory2`, `Territory2Rule`, run by a user with Manage Territories | Sales Territories components "don't support packaging or change sets"; a change-set plan has no path |
| Enabling the feature itself | Deploy `Territory2.settings` alone, before anything else | `enableTerritoryManagement2` "is exclusive of all other operations" |

---


## Recommended Workflow

1. **Answer the seven questions above** and record them in `templates/enterprise-territory-management-template.md`. Two of them are blocking: the target org's state for this model's developer name, and whether the release path is a source deploy. Both fail at deploy time if guessed.
2. **Confirm the design is settled** — if the coverage model, alignment criteria or hierarchy shape are still open, that is `admin/territory-design-requirements`, not this skill.
3. **Enable the feature on its own.** Deploy `settings/Territory2.settings-meta.xml` in its own deployment (§1 and §6 of `references/metadata-examples.md`), because `enableTerritoryManagement2` "is exclusive of all other operations."
4. **Write the source.** Shape `territory2Types/`, `territory2Models/<Model>/`, its `territories/` and `rules/` folders from `references/metadata-examples.md` §2–§5, using developer names in `parentTerritory` and Metadata API access-level spellings.
5. **Run the checker** over the folder before deploying: `python3 scripts/check_enterprise_territory_management.py --manifest-dir force-app/main/default`. It catches active rules with no rule items, `parentTerritory` pointing outside the model, duplicate territory names, duplicate type priorities, empty models, and non-Account `objectType`.
6. **Validate, then deploy** with the model-qualified manifest from §6 (`sf project deploy validate` first). Then load `UserTerritory2Association` (§8), activate the model, and start the rule run (§9) — the deploy installs rules and assigns nothing.
7. **Verify with the queries in §10**, not by looking at the model page. Confirm the alignment log shows a finished run, `ObjectTerritory2Association` rows exist with `AssociationCause = Territory2AssignmentRule`, and `AccountShare` carries `RowCause = Territory`. Then walk the Review Checklist below and `references/gotchas.md` for anything the queries can't see.

---

## Review Checklist

Run through these before marking ETM setup complete:

- [ ] ETM is enabled; Legacy Territory Management is not active
- [ ] Territory model is in Active state; exactly one Active model exists
- [ ] All territories have a territory type assigned
- [ ] Account assignment rules are active and have been run against existing accounts
- [ ] User territory memberships are populated for all sales reps and managers
- [ ] Access levels are set on each `Territory2` in Metadata API spelling, and are legal for the org's OWD
- [ ] `Territory2.settings` was reviewed rather than copied forward — check `tm2BypassRealignAccInsert` and `tm2EnableUserAssignmentLog`
- [ ] Territory type priorities are unique, and no sampled account sits in two territories tied at the top priority
- [ ] Open opportunities have Territory2Id populated for forecast accuracy
- [ ] Filter-based OTA has a deployed Apex class named in `opportunityFilterSettings`, or a documented decision not to use it
- [ ] Forecast type is configured for territory hierarchy if using territory forecasts
- [ ] Territory count is inside whatever ceiling was confirmed for this org (see the Limits note in Before Starting)
- [ ] The release plan is a source deploy — no change-set step anywhere in it
- [ ] `python3 scripts/check_enterprise_territory_management.py --manifest-dir <dir>` reports no ERROR findings
- [ ] Metadata deployment tested in sandbox before promoting to production

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Activating a model triggers full assignment recalculation** — The moment you move a territory model from Planning to Active, Salesforce runs all account assignment rules across the entire model as a background job. For orgs with large account volumes this can take hours. Plan activation during off-peak windows and monitor `Territory2AlignmentLog` for completion.

2. **Assignment rules are not retroactive** — Creating or modifying an assignment rule does not automatically apply it to existing accounts. You must explicitly run rules (at the territory or model level) to assign pre-existing accounts. This is the most common cause of "why didn't my accounts move to the new territory?"

3. **Archived models cannot be reactivated** — Once a territory model is Archived, it is permanently read-only. You cannot promote an Archived model back to Active. If you need to go back to a previous structure, you must recreate it. Keep work-in-progress models in Planning state, not Archived.

4. **Forecast sharing is not available for territory-based forecast types** — Unlike role-based forecasts, territory forecast types do not support the forecast sharing feature. Attempting to share territory forecast access will silently have no effect.

5. **Territory membership is additive — it cannot restrict below OWD** — If Account OWD is Public Read/Write, territory membership adds nothing. If Account OWD is Private, territory membership adds Read access. Territory access never narrows access below the OWD floor.

---

## Output Artifacts

| Artifact | Kind | Description |
|---|---|---|
| `Territory2Settings` (`settings/Territory2.settings-meta.xml`) | Metadata | Feature switch plus default access levels, OTA Apex wiring, realign bypass, user assignment log |
| `Territory2Model` (`territory2Models/<Model>/`) | Metadata | Container for the model's territories and rules; state lives on the object, not the file |
| `Territory2Type` (`territory2Types/`) | Metadata | Classification layer with the unique `priority` integer that decides OTA |
| `Territory2` (`.../territories/`) | Metadata | One territory: type, `parentTerritory`, per-object access levels, `ruleAssociations` |
| `Territory2Rule` (`.../rules/`) | Metadata | Filter-based assignment rule on Account; belongs to the model, up to 10 rule items |
| `UserTerritory2Association` | Data (Data Loader / Apex) | Links users to territories with `RoleInTerritory2`; no `update()` call |
| `ObjectTerritory2Association` | Data (read) | The account-to-territory assignments the rules produced, with `AssociationCause` |
| `Territory2AlignmentLog` | Data (read) | Start/end/status of each rule run job, and who started it |
| `AccountShare` with `RowCause` `Territory` / `Territory2AssociationManual` | Data (read) | Proof that territory access actually materialised |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing the deployable XML, the manifest, the retrieve/deploy commands, or the verification SOQL |
| `references/gotchas.md` | Something deployed cleanly and did not work, or before committing to a release path |
| `references/examples.md` | Shaping a geographic model or a named-account overlay, and sizing the priority values |
| `references/well-architected.md` | Trading off hierarchy depth, model count and access breadth — and for the source list |
| `references/llm-anti-patterns.md` | Reviewing generated ETM advice, especially anything naming `Territory` without the 2 |

---

## Related Skills

- admin/territory-design-requirements — run this first; coverage model, alignment criteria, hierarchy depth and user-to-territory ratios are decided there, not here
- admin/sharing-and-visibility — OWD and sharing rules set the floor that territory access is additive to, and the recalculation cost of a large membership change is sized there
- admin/role-hierarchy-design — the org chart the territory hierarchy is deliberately independent of; do not mirror one into the other
- admin/assignment-rules — Lead and Case routing; its `references/routing-selector.md` is what names ETM as the answer for Account and Opportunity geography, and unlike ETM those rules do ship in change sets
- admin/fsl-service-territory-setup — a different feature entirely: Field Service `ServiceTerritory` shares no data, no configuration and no UI with Sales Cloud `Territory2`
- admin/collaborative-forecasts — forecast types, adjustments and quotas, once the territory forecast type is enabled
- data/territory-data-alignment — bulk-loading `UserTerritory2Association` and realignment data at volume
- devops/metadata-api-retrieve-deploy — the source-deploy mechanics ETM is forced onto
- devops/change-set-deployment — read it to confirm what a change set *cannot* carry before planning an ETM release around one
