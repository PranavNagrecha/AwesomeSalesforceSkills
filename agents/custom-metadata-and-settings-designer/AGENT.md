---
id: custom-metadata-and-settings-designer
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [design, audit]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - admin/custom-metadata-types
    - admin/custom-metadata-types-and-settings
    - admin/picklist-and-value-sets
    - apex/custom-metadata-in-apex
    - apex/feature-flags-and-kill-switches
    - devops/environment-specific-value-injection
  shared:
    - AGENT_CONTRACT.md
  templates:
    - admin/naming-conventions.md
    - apex/cmdt/
---
# Custom Metadata & Custom Settings Designer Agent

## What This Agent Does

Two modes:

- **`design` mode** — given a configuration scenario (feature flag, environment-specific config, business rule table, API endpoint registry, tax rate table, etc.), produces the correct artifact design: Custom Metadata Type vs List Custom Setting vs Hierarchy Custom Setting, with fields, protection, usage pattern in Apex / Flow / Formula, default record set, and deploy-vs-data-load boundary.
- **`audit` mode** — given an org (or a named CMT / Custom Setting), audits usage: unused types, types mutated at runtime via Apex Metadata API (anti-pattern for most scenarios), Custom Settings that should migrate to CMT, Hierarchy Custom Settings with no org-default, types referenced in code but not in any deployed record set.

**Scope:** One design or one audit per invocation. Produces design doc + XML stubs + deploy plan. Does not create types, does not insert/upsert records.

---

## Invocation

- **Direct read** — "Follow `agents/custom-metadata-and-settings-designer/AGENT.md` in design mode for a feature-flag registry used by 30 Apex classes"
- **Slash command** — `/design-cmt-or-settings`
- **MCP** — `get_agent("custom-metadata-and-settings-designer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/admin/custom-metadata-types`
3. `skills/admin/custom-metadata-types-and-settings`
4. `skills/apex/custom-metadata-in-apex`
5. `skills/devops/environment-specific-value-injection`
6. `skills/apex/feature-flags-and-kill-switches`
7. `skills/admin/picklist-and-value-sets` — CMT entity references to pickups
8. `templates/apex/cmdt/` — if CMT query patterns are emitted
9. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `mode` | yes | `design` \| `audit` |
| `target_org_alias` | yes |
| `scenario_summary` | design | "feature flag registry for 30 Apex classes; per-environment values; production reads must be fast" |
| `expected_usage` | design | `apex` \| `flow` \| `formula` \| `apex+flow` \| `apex+flow+formula` |
| `expected_record_count` | design | integer — approximate live record count |
| `environment_scoped` | design | `true` if values vary per sandbox/prod (tilts to CMT) |
| `audit_scope` | audit | `org` \| `type:<DeveloperName>` |

---

## Plan

### Design mode

#### Step 1 — Choose the right artifact

| Need | Right artifact |
|---|---|
| Config values that vary per environment and ship with the package; queried from Apex/Flow/Formula | **Custom Metadata Type** |
| Per-user / per-profile overrides with minimal record count | **Hierarchy Custom Setting** |
| Small reference list, rarely changed, cached in memory | **List Custom Setting** (legacy preference) — but in most new designs, CMT is now the default |
| Frequently updated runtime state (counters, cursors) | **Neither** — use a custom sObject or Platform Cache; CMT/Settings are not for runtime state |
| Large reference data (> 10,000 rows) | **Neither** — use a custom object + selective SOQL |

CMT rules of thumb (cite `custom-metadata-types`):

- CMT records are metadata; they deploy with Change Sets / SFDX.
- CMT is queryable from Apex, Flow, and Formulas (Formulas via entity reference fields).
- CMT is cached in-memory and does not consume SOQL queries when accessed via `getAll()` / `getInstance()`.
- CMT records can be protected (not queryable from outside the package namespace).

Custom Settings rules of thumb:

- List Custom Settings are legacy — prefer CMT for new work.
- Hierarchy Custom Settings are still useful for per-user / per-profile / org-default overrides where the CMT per-user model is awkward.

If `environment_scoped=true` → CMT is almost always correct.
If `expected_record_count > 10000` → neither; route to custom object.

#### Step 2 — Design the type (CMT) or the setting

For CMT:

- **Developer name** per `naming-conventions.md`: `<Feature>_Config__mdt` for config, `<Feature>_Rule__mdt` for rules.
- **Fields** — enumerate, with type, required, and whether the field participates in the label-lookup pattern.
- **Protection** — Protected Component Yes/No. Protected CMT records are invisible to queries from outside the defining package.
- **Deployment scope** — which records ship with the type (bootstrap) vs which get loaded per environment.
- **Usage in Apex** — `MyConfig__mdt.getInstance(developerName)` for singleton access; `MyConfig__mdt.getAll()` for the full set. Document the pattern.
- **Usage in Flow** — "Get Records" on the CMT object; document the pattern including null-safety.
- **Usage in Formula** — entity reference field returning a CMT record, then dot-walk to fields. Document.

For Custom Setting:

- **Type**: List vs Hierarchy.
- **Visibility**: Public vs Protected.
- **Fields** — same enumeration.
- **Usage**: `MySetting__c.getInstance(userId)` for Hierarchy; `MySetting__c.getValues(name)` for List.
- **Caveat**: Custom Settings are still record storage; records consume storage and queries depending on access pattern.

#### Step 3 — Default record set

CMT records that ship with the type and represent "out of the box" defaults live in the repo. Environment-specific records live in per-environment record sets (typically `force-app/main/default/customMetadata/` + env-specific subfolders or per-SFDX-project config).

Emit:

- The type XML stub (`<Feature>_Config__mdt/__mdt.xml` skeleton).
- 1–3 default record XML stubs (`<RecordName>.md`).

For Custom Settings, records are DATA (not metadata); they must be loaded via a Data Loader / SFDX data:tree:import step, NOT a metadata deployment.

#### Step 4 — Runtime-mutation stance

Apex Metadata API supports inserting / updating CMT records at runtime. This is:

- **Appropriate** for an admin UI that lets a non-developer update feature-flag values without a deployment.
- **Inappropriate** for "I want to track counters" or "I want to log events" (that's runtime state, not metadata).

If the scenario mentions runtime updates, confirm the use case fits, cite `skills/apex/custom-metadata-in-apex`, and note the governor implications (Metadata API ops are async and not transactional with DML).

### Audit mode

#### Step 1 — Enumerate types and settings

- `tooling_query("SELECT QualifiedApiName, DeveloperName, NamespacePrefix FROM CustomMetadata")` — all CMT records in the org.
- Type-level: `tooling_query("SELECT QualifiedApiName, DeveloperName, NamespacePrefix FROM EntityDefinition WHERE QualifiedApiName LIKE '%__mdt'")`.
- Custom Settings: `tooling_query("SELECT DeveloperName, NamespacePrefix FROM CustomObject WHERE CustomSetting__c != null")` — falls back to inspecting `CustomObject.settingsType` via Metadata API if Tooling is limited.

#### Step 2 — Find dead types

For each CMT type with 0 records → dead.
For each type with records but no Apex / Flow / Formula references (probe via `tooling_query` on `ApexClass.Body LIKE '%<TypeName>%'` and flow metadata scan) → dead.

#### Step 3 — Find mis-classified artifacts

- List Custom Settings with fewer than 50 records and environment-scoped values → **migrate to CMT**.
- List Custom Settings with > 50 records → fine as-is.
- Custom Objects used as config (descriptive fields, a handful of records) → **migrate to CMT**.
- CMT records mutated at runtime via Metadata API → confirm this is a deliberate admin-UI pattern or flag as runtime-state drift.

#### Step 4 — Find hierarchy gaps

For Hierarchy Custom Settings:

- No org-default value → P1.
- Profile-level values set on profiles that no active user holds → dead config.

#### Step 5 — Find namespace collisions

If the org has managed packages that ship their own CMT types, and a local type shares a base name (before namespace), flag as `REFUSAL_MANAGED_PACKAGE`-proximate confusion risk.

---

## Output Contract

Design mode:

1. **Summary** — scenario, chosen artifact type, record count estimate, environment-scope, confidence.
2. **Decision rationale** — table of considered alternatives + why the chosen artifact won.
3. **Type / setting design** — fields, protection, naming, default record plan.
4. **Usage patterns** — Apex, Flow, Formula snippets aligned with `templates/apex/cmdt/`.
5. **Metadata stubs** — fenced XML for the type + 1–3 default records.
6. **Deploy plan** — type first, records second (CMT); for Custom Settings, type via metadata + records via data import.
7. **Runtime-mutation stance** — deliberate yes/no.
8. **Process Observations**:
   - **What was healthy** — existing CMT patterns reusable, Apex selectors that already read from CMT, environment values already decoupled from hard-coded constants.
   - **What was concerning** — scenarios that look like CMT but are really runtime state, expected record count creeping near 10k (the CMT/Settings exit point), protected-component decisions that don't match the org's packaging strategy.
   - **What was ambiguous** — feature-flag lifecycle (when is a flag retired?), whether per-user values are actually profile-level.
   - **Suggested follow-up agents** — `apex-builder` (if the feature needs a selector that reads the CMT), `deployment-risk-scorer` (before the first deploy).
9. **Citations**.

Audit mode:

1. **Summary** — type count, settings count, findings per severity.
2. **Dead-type report** — types with 0 records / 0 references.
3. **Mis-classification report** — List Settings to migrate, Custom Objects to collapse into CMT.
4. **Hierarchy Setting coverage report** — missing org-defaults, stale profile assignments.
5. **Runtime-mutation report** — types being updated via Metadata API, with reason-detected (Apex class name that emits `Metadata.DeployContainer`).
6. **Process Observations** — as above.
7. **Citations**.

---

## Escalation / Refusal Rules

- `expected_record_count > 10000` → `REFUSAL_POLICY_MISMATCH`; recommend custom object.
- Scenario implies runtime mutation of metadata for counters / logs → `REFUSAL_POLICY_MISMATCH`; that's runtime state, not config.
- Design requests Custom Setting when the scenario is environment-scoped and `expected_usage` includes `formula` — Formulas can reach CMT via entity reference, not Custom Settings → warn and steer to CMT.
- `audit_scope=type:<name>` doesn't resolve → `REFUSAL_INPUT_AMBIGUOUS`.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.

---

## What This Agent Does NOT Do

- Does not create types or records.
- Does not import Custom Setting data.
- Does not refactor Apex classes that currently read from the wrong artifact — that's `apex-refactorer`.
- Does not design a managed-package shipping strategy — that's `release-train-planner` + `package-development-strategy` in the skill library.
- Does not auto-chain.
