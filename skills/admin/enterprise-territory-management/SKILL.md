---
name: enterprise-territory-management
description: "Use this skill when configuring or troubleshooting Salesforce Enterprise Territory Management (ETM): territory models, territory types, territory hierarchies, account assignment rules, opportunity territory assignment, and forecast by territory. Trigger keywords: territory model, territory hierarchy, ETM, assign accounts to territories, territory forecast, territory activation. NOT for role hierarchy (use sharing-and-visibility). NOT for Legacy/Original Territory Management (pre-ETM)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Enterprise Territory Management

This skill activates when a practitioner needs to design, configure, audit, or troubleshoot Salesforce Enterprise Territory Management (ETM). It covers territory models, territory types, hierarchy design, account assignment rules, opportunity territory assignment, user territory membership, and forecast by territory.

---

## Before Starting

Gather this context before working on anything in this domain:

- **ETM must be enabled in the org.** ETM is a separate feature from Legacy (Original) Territory Management. The two cannot coexist — check Setup > Territory Management. If it shows "Enterprise Territory Management," ETM is active. Legacy Territory Management is no longer recommended.
- **Only one territory model can be Active at a time.** All other models remain in Planning or Archived state. Activating a model triggers a full background recalculation of all account assignment rules.
- **Territory forecast is separate from role hierarchy forecast.** A territory-based Forecast Type must be configured independently. Forecast hierarchy is derived from the active territory model.
- **Limits:** Up to 1,000 territories per territory model in Enterprise Edition (default). Performance/Unlimited orgs can request up to 20,000 territories per model from Salesforce Support. Only one Active model is permitted at any time.

---

## Core Concepts

### Territory Model

A territory model is the top-level container for your entire territory structure. It holds all territory types, the territory hierarchy, and all account assignment rules. A model progresses through three states:

- **Planning** — model is being designed; assignment rules can be run in preview mode without affecting live data or access.
- **Active** — model is live; assignment rules execute automatically on account create/update, and the model drives account-territory relationships, user access, and territory forecasting. Only one model can be in this state at a time.
- **Archived** — model is retired and read-only. Archiving cannot be reversed — an archived model cannot be reactivated.

Transitioning a model from Planning to Active triggers an immediate background recalculation of all assignment rules across the entire model. For large orgs this can take hours. Monitor `Territory2AlignmentLog` for completion status.

### Territory Types

Territory types are a categorization layer — they do not appear in the territory hierarchy itself, but every territory must be assigned a type. Types help you organize and report on territories by business meaning. Common examples:

- **Geographic** — regions such as "US West" or "EMEA North"
- **Named Account** — accounts owned by specific reps regardless of geography
- **Industry Overlay** — cross-functional coverage (e.g., Healthcare Overlay)

Each territory type has a **priority value** (integer). When an opportunity qualifies for multiple territories, the priority value determines which territory's assignment rule takes precedence for opportunity territory assignment.

### Territory Hierarchy

The territory hierarchy defines parent-child relationships between territories within a model. Parent territories do not automatically propagate access or rules down to child territories — each level must be explicitly configured.

For each territory, Salesforce creates two system-defined sharing groups:
- **Territory group** — direct members of that territory.
- **TerritoryAndSubordinates group** — members of that territory and all territories below it in that branch.

These groups drive record access calculations. Modifying territory membership triggers recalculation of these groups, which can add latency in large orgs.

### Account Assignment Rules

Account assignment rules are filter-based criteria that automatically assign accounts to territories based on account field values (standard or custom). Key behaviors:

- Rules can run **automatically** when an account is created or updated (controlled by the `IsActive` flag on the rule).
- Rules can also be **run manually** for a single territory or the entire model.
- If an account matches rules for multiple territories, it is assigned to **all matching territories**.
- Rules are **not retroactive** — creating or modifying a rule does not apply it to existing accounts. A manual rule run is required to backfill.
- Accounts can also be **manually assigned** to territories, independent of rules.

### Opportunity Territory Assignment (OTA)

Opportunity territory assignment links an opportunity to a territory, which is required for the opportunity to appear in territory-based forecasts. OTA can be:

- **Filter-based (automatic):** Salesforce evaluates OTA rules and assigns a territory based on account territory membership or field criteria.
- **Manual:** Users or automation can set the `Territory2Id` field on an opportunity directly.

Opportunities not assigned to any territory do not appear in territory forecasts. Monitor `Opportunity.Territory2Id` population as a key data quality metric.

### Forecast by Territory

Territory-based forecasting uses the active territory model's hierarchy as the forecast hierarchy — entirely independent of role hierarchy forecasting. You configure a **Forecast Type** in Setup > Forecasts Settings with the territory hierarchy as the source.

Important constraints:
- Forecast **sharing is not available** for territory-based forecast types, unlike role-based forecasts.
- Users must be both territory members and enabled as forecast users.
- The forecast hierarchy reflects the territory hierarchy of the active model; switching the active model restructures the forecast hierarchy.

### Access and Sharing via Territory Membership

When a user is assigned as a member of a territory, Salesforce grants them **at least Read access** to all accounts assigned to that territory, regardless of account ownership. Additional access to related Opportunities, Contacts, and Cases is controlled by `Territory2ObjSharingConfig` metadata settings.

Territory membership is always **additive** — it cannot restrict access below the org-wide default (OWD).

---

## Mode 1 — Set Up a Territory Model

Use this mode when building ETM from scratch or standing up a new territory structure.

**Step 1 — Enable ETM.** Navigate to Setup > Territory Management and enable Enterprise Territory Management. This is a one-way migration if Legacy Territory Management was previously active.

**Step 2 — Define Territory Types.** Create territory types that reflect your go-to-market segmentation. Assign priority values: lower integer = higher priority for OTA tie-breaking. Every territory must have a type.

**Step 3 — Create the Territory Model.** Create a new model in Planning state. All configuration happens while in Planning — safe to iterate on without impacting live access or forecasts.

**Step 4 — Build the Territory Hierarchy.** Create territories within the model. Assign each a territory type. Set up parent-child relationships to reflect coverage structure. Avoid hierarchies deeper than 5–6 levels — complexity increases in forecasting rollups and access management.

**Step 5 — Configure Assignment Rules.** For each territory, create account assignment rules based on field criteria (e.g., `BillingState = 'CA'`). Mark rules active for automatic execution on account create/update. Run rules in preview mode first to validate expected assignments before activating the model.

**Step 6 — Assign Users to Territories.** Add `UserTerritory2Association` records for each sales rep and manager. Assign territory roles as appropriate (e.g., Territory Manager, Account Executive). Users can belong to multiple territories.

**Step 7 — Configure Object Sharing.** Review `Territory2ObjSharingConfig` metadata to confirm Opportunity and Contact access levels are set correctly for territory members (Read/Write vs Read-Only).

**Step 8 — Activate the Model.** Activate the territory model. This triggers background assignment recalculation. Monitor `Territory2AlignmentLog`. Plan activation for off-peak windows on large orgs.

**Step 9 — Configure Forecast Type (if using territory forecasts).** In Setup > Forecasts Settings, add a Forecast Type using the territory hierarchy. Enable forecast users for territory managers.

---

## Mode 2 — Review / Audit Territory Configuration

Use this mode when auditing an existing ETM setup for correctness or scale.

**Check model state.** Query `Territory2Model` for `State` field. Confirm exactly one model has `State = 'Active'`.

**Audit territory count.** `SELECT COUNT() FROM Territory2 WHERE Territory2ModelId = '<modelId>'` — flag if count is approaching 1,000 (default limit).

**Review assignment rule coverage.** For each territory, check `AccountTerritoryAssignmentRule` records. Verify rules with expected auto-execution are marked `IsActive = true`.

**Check last rule run.** Review `Territory2AlignmentLog` for last-run timestamps. Stale timestamps indicate rules have not run since recent account data changes.

**Audit user memberships.** Query `UserTerritory2Association` to confirm expected reps are assigned to expected territories.

**Verify opportunity territory assignment.** Check `Opportunity.Territory2Id` population rate on open opportunities. Unpopulated opportunities will not appear in territory forecasts.

| Check | SOQL / Navigation | Flag If |
|---|---|---|
| Active model count | `SELECT Id, Name FROM Territory2Model WHERE State = 'Active'` | More than 1 result |
| Territory count per model | `SELECT COUNT() FROM Territory2 WHERE Territory2ModelId = :modelId` | Approaching 1,000 |
| Unassigned accounts | `SELECT COUNT() FROM Account WHERE Id NOT IN (SELECT AccountId FROM ObjectTerritory2Association)` | Unexpectedly large |
| Open opps without territory | `SELECT COUNT() FROM Opportunity WHERE Territory2Id = null AND IsClosed = false` | Unexpectedly large |

---

## Mode 3 — Troubleshoot Assignment and Sharing Issues

Use this mode when accounts are not assigned to expected territories, users lack expected access, or territory forecasts show missing data.

**Accounts not assigning automatically:**
- Confirm the assignment rule is `IsActive = true` on `AccountTerritoryAssignmentRule`.
- Confirm the territory model is in Active state (not Planning).
- Rules are not retroactive — existing accounts require a manual rule run after a new rule is created.
- Check that account field values match rule criteria exactly (case sensitivity on text/picklist values).

**Users missing access to territory accounts:**
- Confirm the user has a `UserTerritory2Association` record for the territory.
- Verify the `Territory2ObjSharingConfig` access level for the object in question.
- Remember: territory membership adds access but cannot override OWD Private if OWD is more restrictive than the territory config.

**Forecast missing accounts or opportunities:**
- Verify open opportunities have `Territory2Id` populated.
- Confirm the territory is in the Active model's hierarchy.
- Confirm the user is both a territory member and an enabled forecast user.
- Remember: territory forecast sharing is not supported — this is expected behavior, not a bug.

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
| Promoting territory config to production | Deploy Territory2Model, Territory2Type, Territory2 metadata via Metadata API or change set | Territory model metadata is fully deployable |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking ETM setup complete:

- [ ] ETM is enabled; Legacy Territory Management is not active
- [ ] Territory model is in Active state; exactly one Active model exists
- [ ] All territories have a territory type assigned
- [ ] Account assignment rules are active and have been run against existing accounts
- [ ] User territory memberships are populated for all sales reps and managers
- [ ] Territory2ObjSharingConfig is configured for Opportunity and Contact access
- [ ] Open opportunities have Territory2Id populated for forecast accuracy
- [ ] Forecast type is configured for territory hierarchy if using territory forecasts
- [ ] Territory count is below 1,000 (or within Salesforce-approved limit)
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

| Artifact | Description |
|---|---|
| Territory2Model | Container for the entire ETM configuration; deployable via Metadata API |
| Territory2Type | Classification layer for territories, including priority values for OTA |
| Territory2 | Individual territory records with parent-child hierarchy relationships |
| AccountTerritoryAssignmentRule | Filter-based rules that auto-assign accounts to territories |
| UserTerritory2Association | Links users to territories with territory roles |
| Territory2ObjSharingConfig | Controls Opportunity/Contact access level for territory members |
| Territory2AlignmentLog | Audit log of assignment rule execution jobs and completion status |

---

## Related Skills

- sharing-and-visibility — use for role hierarchy design, OWD configuration, and sharing rules; ETM access is additive to the core sharing model, not a replacement
- forecast-management — use for configuring forecast types, adjustments, and quota management once the territory forecast type is enabled
