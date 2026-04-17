# Classifier: list_view_search_layout

## Purpose

Audit every object's List Views and Search Layouts (lookup dialogs, search results, tab results, recent items) for drift and usability failures. Surfaces list views with filters referencing deleted fields, sensitive data leaking through "All Users" sharing, list views shared to zero-member Public Groups, lookup dialogs missing disambiguators, and stale duplicates. Not for granting / revoking sharing (that's `sharing`) and not for fixing fields (that's `field-impact-analyzer`).

## Replaces

`list-view-and-search-layout-auditor` (now a deprecation stub pointing at `audit-router --domain list_view_search_layout`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_scope` | no | default: all objects; may restrict (e.g. `Account,Contact,Case,Opportunity`) |
| `include_inactive_list_views` | no | default `false` |
| `sensitive_field_patterns` | no | default: PII patterns (`SSN`, `DOB`, `Personal_*`, `SSN__c`) |

## Inventory Probe

1. List views: `tooling_query("SELECT Id, DeveloperName, Name, SobjectType, IsSoqlCompatible FROM ListView WHERE SobjectType IN (<scope>)")`.
2. Per list view: pull filter criteria, columns, sharing scope (private / group / all users / inactive-user), record-type filter.
3. Search Layouts: metadata fetch of Layout → SearchLayout section, or `CustomObject` metadata parse per-object for Search Results / Lookup Dialogs / Lookup Phone Dialogs / Search Filter Fields / Tab Layouts / Recent Items.
4. Public Groups referenced by list view sharing: `tooling_query("SELECT Id, DeveloperName, IsActive, OwnerId, Owner.IsActive FROM Group WHERE Id IN (...)")` + member counts.

Inventory columns (beyond id/name/active): `is_soql_compatible`, `shared_to_scope`, `last_modified_by_active`, `has_chart`, `column_count`, `filter_column_count`.

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `LV_FILTER_DELETED_FIELD` | P0 | List view filter references a deleted field | list view id + missing field API name | Replace field or retire list view; route via `field-impact-analyzer` |
| `LV_FILTER_INACTIVE_PICKLIST_VALUE` | P1 | Filter references an inactive picklist value | list view + value | Update filter or reactivate value |
| `LV_COLUMN_DELETED_FIELD` | P0 | Column references a deleted field | list view + missing field | Replace column |
| `LV_COLUMN_NO_FLS` | P1 | Column references a field the audience has no FLS to — appears blank | list view + field + audience | Add FLS OR drop column |
| `LV_NOT_SOQL_COMPATIBLE` | P2 | `IsSoqlCompatible=false` — filter degrades to non-indexed behavior | list view id + filter summary | Simplify filter (no cross-object / formula-heavy predicates) |
| `LV_SENSITIVE_ALL_USERS` | P0 | Shared to "All Users" AND filter/columns include sensitive fields (`sensitive_field_patterns`) | list view + matched pattern | Restrict to a narrower audience OR remove sensitive columns |
| `LV_ALL_USERS_RESTRICTED_RECORDS` | P1 | Shared "All Users" but OWD + sharing rules don't grant the underlying data — list view implies access that doesn't exist | list view + effective audience | Rename to reflect actual accessibility or restrict scope |
| `LV_EMPTY_PUBLIC_GROUP` | P1 | Shared to a Public Group with 0 active members | list view + group + member count | Reassign to an active group |
| `LV_INACTIVE_OWNER_BROAD_SHARE` | P2 | `createdBy`/`lastModifiedBy` inactive AND list view shared broadly | list view + owner | Transfer ownership to an active admin |
| `LV_DUPLICATE_FILTER` | P2 | Two list views with identical filter criteria (different names) | list view pair | Consolidate into one canonical list view |
| `LV_STALE_LONG_NO_MODIFY` | P2 | Not modified in > 12 months on an object with substantial data-model churn | list view + last modified | Review for retirement |
| `LV_CHART_DELETED_FIELD` | P1 | List View Chart pinned to a deleted field | list view + chart + missing field | Drop chart or re-pin |
| `SL_LOOKUP_MISSING_DISAMBIGUATOR` | P0 | Lookup Dialog returns only Name on Contact/Case/Opportunity (users pick wrong records) | object + lookup layout columns | Add Account/Email/Record Number column |
| `SL_SEARCH_RESULT_THIN` | P1 | Search Results has < 3 columns on a business-critical object | object + column count | Add key disambiguators (Status, Owner, AccountName) |
| `SL_SEARCH_RESULT_FLS_BLOCKED` | P2 | Search Layout includes FLS-blocked column that many users can't read | object + column + audience | Swap for an accessible column |
| `SL_SEARCH_LAYOUT_TOO_WIDE` | P2 | Search Layout has > 10 columns | object + count | Trim to essentials |
| `SL_FILTER_FIELDS_MISSING` | P2 | Search Filter Fields lack a commonly-filtered field (Status/Stage) | object | Add the common filter field |
| `SL_TAB_LAYOUT_GAP` | P2 | Tab layout missing a column users rely on in the default list view | object + field | Align tab layout with default list view |

## Patches

None. List view / search layout metadata is brittle to programmatic patch (SOQL-incompatible filters, column indexes). Findings surface the target state; humans apply via Setup or `force-app` metadata edits.

## Mandatory Reads

- `skills/admin/list-views-and-compact-layouts`
- `skills/admin/record-types-and-page-layouts`
- `skills/admin/queues-and-public-groups`
- `skills/admin/picklist-and-value-sets`
- `templates/admin/naming-conventions.md`

## Escalation / Refusal Rules

- Org has no list views (new org) → `REFUSAL_OUT_OF_SCOPE`.
- Managed-package list views / search layouts → `REFUSAL_MANAGED_PACKAGE` for those assets; report as read-only.
- Run user lacks FLS describe → `REFUSAL_INSUFFICIENT_ACCESS`; request a run user with Modify All Data.

## What This Classifier Does NOT Do

- Does not delete / modify list views or search layouts.
- Does not change sharing — delegates to `sharing`.
- Does not edit fields — delegates to `field-impact-analyzer` / `picklist`.
