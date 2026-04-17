# Classifier: quick_action

## Purpose

Audit every Quick Action (object-specific) and Global Action in the org: actions broken by deleted fields, actions that are never surfaced on any layout or Dynamic Action, actions that duplicate existing automations, actions invoking retired Flows / LWCs / Visualforce, and action layouts missing required fields. Produces a prioritized cleanup + consolidation plan. NOT for designing new actions — the Wave-3a retired agent's `design` mode moves to Wave-3c's `designer_base` harness as `action-designer`.

## Replaces

`quick-action-and-global-action-auditor` (audit mode only; now a deprecation stub pointing at `audit-router --domain quick_action`). Design mode migrates to Wave-3c.

## Inputs

| Input | Required | Example |
|---|---|---|
| `audit_scope` | no | defaults to all active actions in the org |

## Inventory Probe

1. `tooling_query("SELECT Id, DeveloperName, Label, Type, SobjectType, TargetObject, TargetParentField FROM QuickActionDefinition")` — object-specific + Global (Global has `SobjectType` blank).
2. Per action: layout fields + order, predefined values, referenced Flow / LWC / Visualforce.
3. Page Layout + FlexiPage (Dynamic Actions) assignment: list every layout / FlexiPage and reverse-index which actions they surface.
4. Downstream references: `tooling_query` on `FlowDefinition`, `AuraDefinitionBundle`, `ApexPage` for the artifacts the action invokes.

Inventory columns (beyond id/name/active): `type`, `sobject_type`, `surfaces_count` (number of layouts + Dynamic Action sections that expose it), `references` (list of flow/lwc/vf artifact IDs).

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `QA_FIELD_DELETED` | P0 | Action layout references a deleted or FLS-inaccessible field | action + field | Drop field from layout or restore FLS |
| `QA_FLOW_DEACTIVATED` | P0 | References a deactivated / deleted Flow | action + flow id | Restore flow or swap to a live replacement |
| `QA_VF_ORPHANED` | P0 | References a Visualforce page that is orphaned / deleted / inactive | action + VF page | Migrate to LWC or swap page |
| `QA_LWC_DELETED` | P0 | References a deleted LWC | action + LWC id | Restore or swap |
| `QA_NO_LAYOUT` | P0 | Action has no field layout and cannot be displayed | action | Author layout |
| `QA_INVISIBLE` | P1 | Action not on any Page Layout AND not in any Dynamic Actions section | action | Surface on a layout OR retire |
| `QA_DUPLICATES_STANDARD` | P1 | Custom action mirrors a standard Salesforce action (e.g. custom "New Case") | action + standard equivalent | Retire custom; use standard |
| `QA_DUPLICATES_CUSTOM` | P2 | Multiple custom actions do the same thing with slight variations | action cluster | Consolidate via parameterization |
| `QA_LEGACY_SEND_EMAIL_TEMPLATE` | P2 | "Send Email" action on an Einstein-Send-migrated org still references legacy template | action + template id | Update to Einstein-Send-aware template |
| `QA_PREDEFINED_FIELD_GONE` | P0 | Create-a-Record predefined value references a field/formula no longer present | action + predefined value | Remove predefined value or restore field |
| `QA_SUCCESS_MESSAGE_UNRESOLVED_MERGE` | P1 | SuccessMessage contains a merge field that doesn't resolve on the target object | action + merge field | Swap merge field or remove |
| `QA_ICON_INACTIVE` | P2 | Action icon is inactive / deleted | action | Reassign icon |
| `QA_VF_BACKED_DEEMPHASIZED` | P2 | Action Type = VisualForcePage in an org that has de-emphasized VF | action | Migration candidate to LWC or Flow |
| `QA_RT_PICKER_INACTIVE_RT` | P1 | Record type picker includes an inactive RT | action + RT | Remove inactive RT from picker |
| `QA_GLOBAL_CHANNEL_ASSUMPTION` | P1 | Global create-record action on an object with active Flows/triggers that assume a specific channel but the action doesn't provide it | action + object + channel | Add channel field to action layout OR scope action to the right channel |

## Patches

None. Quick Action metadata is coupled to referenced Flows/LWCs/VF pages — mechanical patching without re-validating downstream artifacts risks breaking existing user workflows. Findings are advisory; fixes land via Setup or `force-app`.

## Mandatory Reads

- `skills/admin/global-actions-and-quick-actions`
- `skills/admin/dynamic-forms-and-actions`
- `skills/admin/record-types-and-page-layouts`
- `skills/flow/screen-flows`
- `standards/decision-trees/automation-selection.md`
- `templates/admin/naming-conventions.md`

## Escalation / Refusal Rules

- Managed-package actions → `REFUSAL_MANAGED_PACKAGE`; audit as read-only.
- No actions in the org → `REFUSAL_OUT_OF_SCOPE`.

## What This Classifier Does NOT Do

- Does not edit layouts — delegates to `record_type_layout`.
- Does not build the backing Flow / LWC — delegates to `flow-builder` / `lwc-builder`.
- Does not audit the backing Flow / LWC in depth — delegates to `flow-analyzer` / `lwc-auditor`.
- Does not design new actions — that's the Wave-3c designer harness scope.
