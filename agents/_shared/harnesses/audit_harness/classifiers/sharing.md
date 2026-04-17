# Classifier: sharing

## Purpose

Audit the org's record-level access model for a target sObject (or the org overall): OWD, role hierarchy usage, Sharing Rules, Apex Managed Sharing, Territory Management, Queues, Public Groups, and Experience Cloud guest/member posture. Classify findings against the `sharing-selection` decision tree. Estimate data-skew + sharing-recalc cost at the target volume. Not for designing persona-level FLS (that's `permission-set-architect`) and not for fixing data skew (flags hot owners; redistribution is a separate project).

## Replaces

`sharing-audit-agent` (now a deprecation stub pointing at `audit-router --domain sharing`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `scope` | yes | `object:<ApiName>` \| `org` |

## Inventory Probe

1. OWD + external sharing model: `tooling_query("SELECT QualifiedApiName, SharingModel, ExternalSharingModel, DeploymentStatus FROM EntityDefinition WHERE QualifiedApiName = '<object>'")`.
2. Sharing Rules: `tooling_query("SELECT Id, Name, ObjectType, SharingCriteria, Active FROM SharingRules WHERE ObjectType = '<object>'")`. Query `SharingRule` + `CriteriaBasedSharingRule` + `OwnerSharingRule` depending on edition-level Tooling coverage.
3. Apex Sharing Reasons: `tooling_query("SELECT Id, DeveloperName, MasterLabel, SobjectType FROM ApexSharingReason WHERE SobjectType = '<object>'")`.
4. Queues + Public Groups referencing object: `tooling_query("SELECT Id, DeveloperName, Type, Related FROM Group")` + `QueueSobject`.
5. Data-skew probe: top 20 owners by record count: `tooling_query("SELECT OwnerId, COUNT(Id) FROM <object> GROUP BY OwnerId ORDER BY COUNT(Id) DESC LIMIT 20")`.
6. Guest-user probe: `tooling_query("SELECT Id, Name, Status, GuestUserAccessType FROM Site")` + per-site guest profile inspection.
7. Experience Cloud Sharing Sets: `tooling_query("SELECT Id, DeveloperName, AccessMappings FROM SharingSet")`.

Inventory columns (beyond id/name/active): `owd_internal`, `owd_external`, `rule_type`, `effective_access_count`, `criteria` (for sharing rules), `top_owner_record_count` (for data-skew row).

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `SHARE_DATA_SKEW_OWNER` | P0 | A single owner holds > 10k records OR > 25% of total records on the object | owner + count + total | Redistribute records OR use Skinny Tables / review role-hierarchy implication |
| `SHARE_GUEST_WRITE_UNSCOPED` | P0 | Experience Cloud guest-user profile has write access outside expected surface | guest profile + object + permission | Restrict guest write; scope via Sharing Set |
| `SHARE_GUEST_MAD` | P0 | Guest user has `Modify All Data` on any object | guest profile + MAD source | Remove MAD — freeze audit, stop further analysis until resolved |
| `SHARE_OWD_MISMATCH` | P1 | Per `sharing-selection.md`, OWD doesn't match the data class (e.g. Private OWD on purely operational data, or Public R/W on PII object) | object + OWD + data class | Align OWD to decision-tree recommendation |
| `SHARE_APEX_MANAGED_UNJUSTIFIED` | P1 | Apex Managed Sharing exists where Criteria-Based Sharing Rule would work | ApexSharingReason + equivalent criteria | Replace with declarative Sharing Rule |
| `SHARE_MISSING_CRITERIA_RULE` | P1 | Clear persona-specific access gap exists but no Sharing Rule covers it | persona + missing access | Create Criteria-Based Sharing Rule |
| `SHARE_RULE_SPRAWL` | P2 | > 20 active Sharing Rules on a single object (hard limit pressure + recalc cost) | object + rule count | Consolidate overlapping rules |
| `SHARE_FLAT_ROLE_HIERARCHY` | P2 | Role hierarchy is effectively flat (< 3 levels) AND org has > 50 users | hierarchy depth + user count | Re-evaluate hierarchy depth |
| `SHARE_RECALC_COST_HIGH` | P1 | Private OWD + row volume > 100k; estimated recalc cost on next rule edit exceeds a reasonable window | object + row count + estimate | Plan rule edits outside business hours; consider data archival |
| `SHARE_NAMING_DRIFT` | P2 | Sharing Rule names don't follow naming conventions | rule + name pattern | Rename on next deploy |
| `SHARE_INACTIVE_RULE` | P2 | `Active=false` Sharing Rule has no documented reason | rule | Delete or document |
| `SHARE_INACTIVE_QUEUE_REFERENCED` | P1 | Sharing Rule or Queue Assignment references a Queue with 0 active members | queue + ref | Populate OR remove reference |

## Patches

None. OWD + Sharing Rule + Apex Managed Sharing changes are governance-sensitive and must flow through change management. Findings are advisory; humans apply.

## Mandatory Reads

- `skills/admin/sharing-and-visibility`
- `skills/admin/delegated-administration`
- `skills/admin/queues-and-public-groups`
- `skills/admin/enterprise-territory-management`
- `skills/admin/data-skew-and-sharing-performance`
- `skills/data/sharing-recalculation-performance`
- `skills/admin/experience-cloud-guest-access`
- `skills/admin/experience-cloud-member-management`
- `standards/decision-trees/sharing-selection.md`

## Escalation / Refusal Rules

- `scope=org` on an org with > 500 custom objects → top-20 by record count first, the rest summarized. `REFUSAL_OVER_SCOPE_LIMIT`.
- Guest user with `Modify All` → `SHARE_GUEST_MAD` P0 freeze; produce ONLY the freeze recommendation and STOP. Do not continue the audit until the guest scope is addressed. `REFUSAL_SECURITY_GUARD`.

## What This Classifier Does NOT Do

- Does not modify OWD, Sharing Rules, or Public Groups.
- Does not design persona-level FLS — delegates to `permission-set-architect`.
- Does not redistribute record ownership — surfaces hot owners; redistribution is a separate project.
