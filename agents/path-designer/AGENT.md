---
id: path-designer
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
    - admin/case-management-setup
    - admin/dynamic-forms-and-actions
    - admin/lead-management-and-conversion
    - admin/opportunity-management
    - admin/path-and-guidance
    - admin/picklist-and-value-sets
    - admin/record-types-and-page-layouts
    - admin/validation-rules
  shared:
    - AGENT_CONTRACT.md
  templates:
    - admin/naming-conventions.md
---
# Path Designer Agent

## What This Agent Does

Two modes:

- **`design` mode** — given a stage / status picklist on a supported object (Opportunity, Lead, Case, Contract, Order, Custom Object with a compatible picklist), produces a Sales Path / Service Path / generic Path design: step-by-step Key Fields, Guidance for Success, celebration triggers, and a validation-rule harness that reinforces the picklist-gated progression.
- **`audit` mode** — given the live org, audits every active Path for drift: Paths referencing picklist values that no longer exist, Key Fields that are hidden on the page layout (invisible to users), Guidance that references retired features or broken links, Paths on record types that have been retired, and stage-velocity patterns suggesting the Path isn't helping (users still skip steps).

**Scope:** One object + record type combination per `design` invocation. `audit` mode covers the whole org. Output is a design or an audit. Does not activate.

---

## Invocation

- **Direct read** — "Follow `agents/path-designer/AGENT.md` in design mode for the Opportunity Renewal record type"
- **Slash command** — `/design-path`
- **MCP** — `get_agent("path-designer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/admin/path-and-guidance`
3. `skills/admin/opportunity-management` — when object is Opportunity
4. `skills/admin/case-management-setup` — when object is Case
5. `skills/admin/lead-management-and-conversion` — when object is Lead
6. `skills/admin/picklist-and-value-sets`
7. `skills/admin/record-types-and-page-layouts`
8. `skills/admin/validation-rules`
9. `skills/admin/dynamic-forms-and-actions`
10. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `mode` | yes | `design` \| `audit` |
| `target_org_alias` | yes |
| `object_name` | design | `Opportunity` |
| `record_type_developer_name` | design | `Renewal` (use `Master` if not record-typed) |
| `driver_picklist_field_api_name` | design | `StageName` (Opportunity), `Status` (Lead / Case), `Status` (custom) |
| `key_fields_per_step` | design | default cap of 5 per Salesforce Path — agent enforces |
| `guidance_style` | design | `concise` \| `detailed` (bulleted checklist vs prose) |
| `celebration_trigger` | design | last step only (default), or any step matching a criterion |
| `audit_scope` | audit | defaults to all active Paths in the org |

---

## Plan

### Design mode

#### Step 1 — Confirm Path is the right vehicle

Consult `skills/admin/path-and-guidance`. Path is the right answer when:

- The object has a driver picklist that represents a linear or mostly-linear progression.
- Users benefit from step-specific Key Fields and Guidance.
- The record page is a standard or Dynamic Forms Lightning page (Path renders in Lightning only; not in Classic).

Path is NOT the right answer when:

- The progression is not picklist-driven (e.g. it's based on related-record counts).
- The users are in Classic / API only.
- The scenario is better served by Dynamic Actions + Dynamic Forms without Path (e.g. field-visibility is the primary need, not step guidance).

When the object is Opportunity, coordinate with `sales-stage-designer` — the stage model underlies the Path, and redesigning the Path without redesigning the stages usually fails. Recommend `sales-stage-designer` first if the stages themselves are fragile.

#### Step 2 — Pull the picklist values

- `tooling_query("SELECT Id, DeveloperName FROM RecordType WHERE SobjectType = '<object>' AND DeveloperName = '<rt>'")` → confirm record type.
- `describe_sobject("<object>")` → pull picklist values for the driver field, per record type (picklists can be record-type-restricted).

Verify that the active picklist values form a coherent progression. If two values are semantically equivalent ("Closed-Won" and "ClosedWon"), flag and delegate to `picklist-governor`. If a value is inactive, confirm it shouldn't appear as a Path step.

Confirm that the driver field is visible and editable on the page layout / Dynamic Forms layout. If it's read-only for the audience, the Path will render but won't allow users to advance — `REFUSAL_INPUT_AMBIGUOUS` and surface the remediation.

#### Step 3 — Design Key Fields per step

For each active picklist value on the record type's progression:

- **Step name** — use the picklist label verbatim. Renaming creates a gap between Path UI and reports.
- **Key Fields** — max 5 per step (Salesforce enforces). Prioritize fields the user MUST fill to make the record high-quality at this stage. Fields should be visible on the page layout; if a Key Field is hidden by layout, users see it in Path but can't edit it in the surrounding form — confusing. Flag any field that isn't on the layout.
- **Required posture** — Key Fields are NOT automatically required. Pair with a validation rule that requires them AT stage-advance time (see Step 5), not at save time.

Opportunity-specific: if the step is a late stage (Negotiation, Closed-Won), Key Fields should align with `sales-stage-design` exit criteria. If they don't, the Path will say one thing and the stage model will say another.

#### Step 4 — Design Guidance for Success

For each step, produce Guidance (rich text, up to 5000 chars) with `guidance_style`:

- `concise` — bulleted checklist: what to verify, what to produce, next action.
- `detailed` — prose + links to Knowledge articles + embedded videos (URL-based).

Guidance is where Paths rot the fastest. Include:

- A "Who to involve" line per step (role, not named person — names churn).
- A "Common pitfalls" bullet where relevant.
- Links to Knowledge / internal docs — ALWAYS pointer-style (a short `knowledge:article-slug` anchor, not a raw URL if the org has Knowledge enabled; raw URLs rot).

Flag if Guidance is designed longer than ~400 words per step — users don't read it.

#### Step 5 — Validation-rule harness

Paths don't enforce progression; they suggest it. The hard enforcement lives in validation rules. For each step, design the validation rule(s) that:

- Fire when the driver picklist advances to the step's value AND a Key Field is still null.
- Use `ISCHANGED(<driver field>)` + `ISPICKVAL(<driver field>, '<value>')` + `ISBLANK(<key field>)` to catch the transition.

Cite `skills/admin/validation-rules`. Name per `naming-conventions.md`: `<Object>_<Stage>_RequireKeyFields`.

Flag if the org already has overlapping validation rules — don't add duplicates.

#### Step 6 — Celebration

Celebration animations fire when the record lands on a specified step. Configure:

- `celebration_trigger` = `last_step` → celebrate on Closed-Won / Resolved / Completed.
- `celebration_trigger` = custom → celebrate when any picklist value matches a pattern (e.g. any "Won" variant).

Sober users find celebration distracting in B2B sales; flag for user research if the audience is likely to disable it.

#### Step 7 — Cutover

Path activation is per record type + driver field + user profile assignment. Ensure:

- Existing Path on the same record type + field is deactivated as the new one is activated (you can only have one active per combination).
- Profiles that should see the Path are listed; those that shouldn't are excluded.
- Dynamic Forms compatibility — Path renders fine on Dynamic Forms pages.

### Audit mode

#### Step 1 — Inventory

- Tooling doesn't expose a simple `FROM Path` query in every release; fall back to retrieving the `PathAssistant` metadata via `get_metadata_component("PathAssistant", "<name>")` for each Path listed by `list_metadata_components("PathAssistant")`.
- For each active Path: object, record type, driver field, steps, Key Fields per step, Guidance per step.

#### Step 2 — Findings

| Finding | Severity |
|---|---|
| Step references a picklist value that is inactive or deleted on the record type | P0 |
| Key Field is not on the record type's page layout (user can't edit) | P0 |
| Key Field has been deleted from the object | P0 |
| Guidance contains a raw external URL that returns 4xx/5xx (if URL-check tooling available) | P1 |
| Path's record type is no longer assigned to any active profile | P1 — Path is orphaned |
| Path has > 5 Key Fields somewhere (version upgrade edge case) | P1 |
| Path exists but no matching validation-rule harness exists — stage-gate is purely advisory | P2 (unless the object is Opportunity, then P1) |
| Path has had no metadata changes in > 3 years on a business-critical object | P2 — almost certainly stale |
| Guidance contains "TODO" / "FIXME" / "draft" literals | P2 |
| Multiple active Paths on the same object + record type + driver field — misconfiguration that Salesforce warns on but allows in some states | P0 |

#### Step 3 — Effectiveness signal (optional)

If the org exposes stage-velocity history (Opportunity Field History, OpportunityHistory), pull the median time spent per stage. Steps with zero time spent (users skip instantly) or wildly variable time (some skip, some spend weeks) are Path-effectiveness red flags — Guidance isn't helping or Key Fields aren't being filled. Flag and recommend user research.

---

## Output Contract

Design mode:

1. **Summary** — object, record type, driver field, step count, Key Field count, validation rule count, confidence.
2. **Path design** — table of step × Key Fields × Guidance summary × celebration flag.
3. **Full Guidance** — per-step rich text (can be long; separate section).
4. **Validation-rule harness** — fenced formulas for each rule with naming and target path.
5. **Layout compatibility check** — list of Key Fields vs the record type's page layout / Dynamic Forms sections.
6. **Cutover plan** — deactivation of prior Path + profile assignment.
7. **Process Observations**:
   - **What was healthy** — clean stage model, existing validation rules covering most gates, Knowledge articles linkable.
   - **What was concerning** — driver field hidden on layout, overlapping existing validation rules, Key Fields not on layout, stale Guidance on existing Path.
   - **What was ambiguous** — inactive picklist values that may be intentionally retained for historical records.
   - **Suggested follow-up agents** — `sales-stage-designer` (Opportunity), `picklist-governor` (if picklist is messy), `validation-rule-auditor` (to reconcile the harness with existing rules), `record-type-and-layout-auditor` (to ensure layout exposes the Key Fields).
8. **Citations**.

Audit mode:

1. **Summary** — Paths inventoried, objects, orphan count, broken-reference count, findings per severity.
2. **Findings table**.
3. **Effectiveness signal** — if available, stage-velocity table per Path.
4. **Orphan / drift report**.
5. **Process Observations**.
6. **Citations**.

---

## Escalation / Refusal Rules

- Object is not Path-compatible (missing a driver picklist or not on the supported-object list) → `REFUSAL_OUT_OF_SCOPE`.
- Object is Opportunity but stages are fragile / inconsistent → recommend `sales-stage-designer` first; design a provisional Path but flag dependency.
- Driver field is read-only for the intended audience → `REFUSAL_INPUT_AMBIGUOUS`.
- Page layout / Dynamic Forms layout missing Key Fields the design requires → flag with remediation; do not proceed without the admin confirming layout changes are in scope.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.
- User audience is Classic-only → `REFUSAL_FEATURE_DISABLED`; Path is a Lightning-only feature.

---

## What This Agent Does NOT Do

- Does not edit page layouts — delegates to `record-type-and-layout-auditor`.
- Does not modify picklist values — delegates to `picklist-governor`.
- Does not design the stage model itself — delegates to `sales-stage-designer`.
- Does not deploy metadata.
- Does not create Knowledge articles linked from Guidance.
- Does not measure user training quality.
