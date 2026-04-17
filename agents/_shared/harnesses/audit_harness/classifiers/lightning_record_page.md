# Classifier: lightning_record_page

## Purpose

Audit Lightning Record Pages for a target sObject: Dynamic Forms adoption, component count, related-list strategy, Path element, custom LWC presence, visibility-rule coverage, mobile-form-factor declaration, and dead (unassigned) pages. Not for designing new record pages; not for auditing LWCs in depth (use the existing `lwc-auditor` agent).

## Replaces

`lightning-record-page-auditor` (now a deprecation stub pointing at `audit-router --domain lightning_record_page`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Opportunity` |

## Inventory Probe

1. `tooling_query("SELECT Id, DeveloperName, MasterLabel, EntityDefinition.QualifiedApiName, Type, PageType, IsActive FROM FlexiPage WHERE SobjectType = '<object>'")`.
2. Per page: `tooling_query("SELECT Metadata FROM FlexiPage WHERE Id = '<id>'")` — region/component tree.
3. Page assignment: `tooling_query("SELECT FlexiPageId, Profile, RecordType FROM FlexiPageRegionInfo")` or equivalent `ProfilePageAssignment`.
4. If custom LWCs present: `tooling_query("SELECT Id, MasterLabel, IsExposed FROM AuraDefinitionBundle WHERE ApiVersion >= 55")` + text-search the Metadata XML for LWC component references.

Inventory columns (beyond id/name/active): `page_type`, `component_count`, `uses_dynamic_forms`, `assigned_profile_count`, `custom_lwc_count`.

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `LRP_HIGH_COMPONENT_COUNT` | P1 | > 25 components on one page (render-cost hit) | page id + component count | Split into tabs or remove low-value components |
| `LRP_MONOLITHIC_RECORD_DETAIL` | P2 | Page uses classic Record Detail instead of Dynamic Forms | page id | Migrate to Dynamic Forms; cite `skills/admin/dynamic-forms-and-actions` |
| `LRP_TOO_MANY_RELATED_LISTS` | P2 | > 6 related lists on one tab | page id + related-list count | Move some to a second tab |
| `LRP_MULTIPLE_RECENT_VIEWED` | P1 | More than one "Recently Viewed" widget on the same page | page id | Dedupe |
| `LRP_MISSING_PATH` | P2 | Object has a defined sales/service process but the Path component is absent | page id + stage field name | Add Path element on the primary page |
| `LRP_LWC_WITH_INIT_SOQL` | P1 | Custom LWC marked `@api isRoot` with SOQL in `connectedCallback` | LWC bundle id | Move SOQL to a `@wire` pattern |
| `LRP_MISSING_VISIBILITY_FILTER` | P2 | Persona-dependent component has no Component Visibility Filter | page id + component | Add visibility filter per persona / record type |
| `LRP_NO_MOBILE_FORM_FACTOR` | P2 | Page uses sub-tabs + related lists but no mobile form-factor declared | page id | Declare mobile / phone form factor explicitly |
| `LRP_DEAD_PAGE` | P2 | Page is assigned to no profile AND no record type | page id | Retire on next cleanup |

## Patches

None. LRP mechanical patching requires FlexiPage metadata round-tripping that's brittle for LWC-heavy pages. Findings are advisory.

## Mandatory Reads

- `skills/admin/dynamic-forms-and-actions`
- `skills/admin/lightning-app-builder-advanced`
- `skills/admin/lightning-page-performance-tuning`
- `skills/admin/record-types-and-page-layouts`
- `skills/admin/path-and-guidance`
- `skills/lwc/lwc-performance`

## Escalation / Refusal Rules

- Object has > 20 record pages → sample top-5 by assignment volume + flag count as P1 `LRP_HIGH_PAGE_COUNT` (emit as a Process Observation, not a code here). `REFUSAL_OVER_SCOPE_LIMIT`.
- Custom LWC source lives in a managed package → audit by API surface only; skip render-weight scoring. `REFUSAL_MANAGED_PACKAGE` for the LWC portion.

## What This Classifier Does NOT Do

- Does not modify or deploy record pages.
- Does not audit LWCs in depth — that's the `lwc-auditor` agent (recommend it).
- Does not design record types — that's `record_type_layout`.
