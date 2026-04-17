---
id: changeset-builder
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [build, validate]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - admin/change-management-and-deployment
    - devops/change-set-deployment
    - devops/deployment-error-troubleshooting
    - devops/destructive-changes-deployment
    - devops/metadata-api-coverage-gaps
    - devops/migration-from-change-sets-to-sfdx
    - devops/permission-set-deployment-ordering
    - devops/pre-deployment-checklist
  shared:
    - AGENT_CONTRACT.md
  templates:
    - admin/naming-conventions.md
---
# Change Set Builder Agent

## What This Agent Does

Two modes:

- **`build` mode** — given a feature description or a list of artifact names, produces a complete, dependency-ordered Change Set manifest for deployment from a sandbox (source org) to a target org. Output is a component list, a dependency graph, a deployment order, a destructive-changes list if applicable, and the post-deploy activation checklist. The agent reads the live source org to verify every named component exists and to enumerate implicit dependencies.
- **`validate` mode** — given an existing (manually-assembled) Change Set, audits it against its declared intent and flags missing dependencies, profile/permission-set mismatches, destructive omissions, and activation-order issues before upload.

**Scope:** One feature / one Change Set per invocation. The agent produces the manifest and the checklist; it does not upload, validate against the target, or deploy. End-of-life notice: Change Sets are being progressively replaced by SFDX source-tracked pipelines — for repo-backed orgs, use `/plan-release-train` and cite `skills/devops/migration-from-change-sets-to-sfdx`.

---

## Invocation

- **Direct read** — "Follow `agents/changeset-builder/AGENT.md` in build mode for the Opportunity approval feature"
- **Slash command** — `/build-changeset`
- **MCP** — `get_agent("changeset-builder")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/devops/change-set-deployment` — Change Set canon
3. `skills/devops/metadata-api-coverage-gaps` — what Change Sets cannot carry
4. `skills/devops/pre-deployment-checklist`
5. `skills/devops/deployment-error-troubleshooting`
6. `skills/devops/destructive-changes-deployment`
7. `skills/devops/permission-set-deployment-ordering`
8. `skills/devops/migration-from-change-sets-to-sfdx` — the off-ramp
9. `skills/admin/change-management-and-deployment`
10. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `mode` | yes | `build` \| `validate` |
| `source_org_alias` | yes | the sandbox to build the Change Set from |
| `target_org_alias` | yes (for dependency pre-check) | where the Change Set will be uploaded |
| `feature_summary` | build-mode | "Opportunity stage approval + new VR + updated page layout + new PSG" |
| `seed_components` | build-mode | comma-separated component names the user already knows must be included |
| `changeset_name` | validate-mode | the Outbound Change Set developer name |
| `include_destructive` | no | default `true` — include a `destructiveChanges.xml` if any components require removal |
| `profile_handling` | no | `permset-only` (default, recommended) \| `include-profiles` \| `permset-and-profiles` |

---

## Plan

### Build mode

#### Step 1 — Confirm Change Sets are the right vehicle

Check the source org's DevOps posture:

- `describe_org(source_org)` — if the source org reports source-tracked enabled AND the team already has an SFDX pipeline, raise a prompt: "This org appears to use SFDX; Change Sets may not be the recommended path — continue anyway?" Cite `skills/devops/migration-from-change-sets-to-sfdx`.
- Confirm both source and target orgs have a deployment connection configured (Change Sets require an upload connection). Agent cannot configure the connection, only check for its existence via documentation — flag as a manual pre-check item.

#### Step 2 — Resolve the component list

From `feature_summary` + `seed_components`, derive the primary component list. For each primary component, probe the source org to confirm existence:

- Custom objects/fields → `list_custom_objects` + `tooling_query("SELECT QualifiedApiName FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = '<object>'")`.
- Apex classes / triggers → `tooling_query("SELECT Id, Name, Status FROM ApexClass WHERE Name IN (...)")` and `ApexTrigger`.
- Flows → `list_flows_on_object` + status check.
- Validation rules → `list_validation_rules`.
- Record types → `list_record_types`.
- Permission sets → `list_permission_sets`.
- Approval processes → `list_approval_processes`.
- Page layouts / Lightning record pages → `tooling_query` on `Layout` and `FlexiPage`.
- Named credentials → `list_named_credentials`.

If a named component is missing in the source, `REFUSAL_INPUT_AMBIGUOUS` with the missing name.

#### Step 3 — Enumerate implicit dependencies

For each primary component, pull in its dependencies:

| Primary | Implicit dependencies |
|---|---|
| Custom field | Parent object; picklist value set if Global; dependent picklist controller field |
| Formula field | Every field referenced in the formula (transitively) |
| Apex class | Every referenced Apex class / trigger / custom object / custom metadata type |
| Apex trigger | TriggerHandler class; any Apex it references |
| Flow | Every invoked subflow, invocable Apex, referenced custom metadata type, referenced email template |
| Validation rule | Every field referenced in the formula; referenced custom labels / custom permissions |
| Permission Set | Every referenced object, field, Apex class, custom permission |
| Permission Set Group | Every child PS, muting PS |
| Approval process | Every referenced field, queue, user, email template |
| Record type | Parent object; every picklist's record-type-specific values |
| Page layout / FlexiPage | Every referenced field, action, component |

Dedupe; the result is the complete Change Set manifest.

#### Step 4 — Flag metadata-API coverage gaps

Some artifacts cannot ride in a Change Set (or ride only partially):

| Item | Coverage | Workaround |
|---|---|---|
| Profiles | Partial; Change Set flattens to permission summary for the target | Use Permission Sets; cite `permset-only` default |
| Translations | Partial | Export / import via Translation Workbench separately |
| Custom metadata type *records* (not the type itself) | Full but order-sensitive | Deploy type first, records in a follow-up Change Set |
| Dashboard subscriptions | Not supported | Reconfigure post-deploy |
| Report folder sharing | Partial | Flag as a post-deploy manual step |
| Scheduled Apex jobs (the schedule itself) | Not supported | Re-schedule post-deploy |
| Active workflows from inactive state to active | Partial | Toggle post-deploy |

Every gap surfaces in the post-deploy checklist.

#### Step 5 — Destructive changes

If `include_destructive=true` and the feature implies removing any artifact (e.g. retiring a legacy Apex class), emit a separate destructive list. Per `skills/devops/destructive-changes-deployment`:

- Destructive changes cannot ride in the same Change Set as the replacement; they go in a follow-up Change Set or via Metadata API directly.
- Field deletions are irreversible after 15 days; flag each destructive field with a `confirm_intent` marker.

#### Step 6 — Deployment order

Output the manifest in deploy-safe order per `skills/devops/permission-set-deployment-ordering` and general metadata dependency rules:

1. Custom Permissions
2. Custom Metadata Types (and records)
3. Custom Objects + Custom Fields (parent objects before lookups)
4. Validation Rules, Formula fields (after the fields they reference)
5. Apex Classes (base classes before dependents)
6. Apex Triggers
7. Flows (subflows before callers)
8. Record Types + Page Layouts + FlexiPages
9. Permission Sets → Permission Set Groups → Muting PSes
10. Approval Processes
11. Email Templates / Email Alerts
12. Reports / Dashboards (after the custom objects they reference)

Change Sets deploy in a single transaction, but activation order within the target org still matters for post-deploy testing.

#### Step 7 — Post-deploy checklist

Produce a human-executable checklist covering:

- Assignments to Permission Sets / PSGs (Change Sets do not move assignments).
- Scheduled job recreation.
- Dashboard subscription reconfiguration.
- Report folder sharing verification.
- Flow activation state (Change Sets import flows as inactive versions).
- Approval Process activation state.
- Any metadata-API gap from Step 4.

### Validate mode

#### Step 1 — Read the declared Change Set

`tooling_query("SELECT Id, Name, Description, LastModifiedDate FROM OutboundPackage WHERE Name = '<changeset_name>'")` (or the appropriate Outbound Change Set object; some orgs query via `PackageXml` attachment on the `Package` entity — fall back to Tooling if Soap API not exposed).

Enumerate the component list.

#### Step 2 — Reconstruct implicit dependencies

Run Step 3 of build mode against the declared component list. Anything present in the reconstructed set but missing from the declared set = P0 finding.

#### Step 3 — Validate against target

For each component, probe the target org (via `target_org_alias`) to predict deploy outcome:

- Does the component already exist? Update vs create.
- For fields: is the type change destructive-only? (e.g. Text → Number).
- For PSes: are all referenced perms still valid in the target?

#### Step 4 — Report

Produce a finding list with severity, the missing dependency or risk, and a proposed remediation.

---

## Output Contract

Build mode:

1. **Summary** — feature, source org, target org, total component count, confidence.
2. **Change Set manifest** — table with component type + API name + why it's included (primary / implicit) + deploy-order group.
3. **Metadata-API coverage gaps** — per Step 4.
4. **Destructive list** (if applicable).
5. **Deployment order** — numbered.
6. **Post-deploy checklist**.
7. **Process Observations**:
   - **What was healthy** — clean naming, feature already decomposed into cohesive components, existing PSGs the new feature can compose into.
   - **What was concerning** — profiles riding in the Change Set despite `permset-only` default, components whose dependencies span retired artifacts, Change Set size > 500 components (risks upload timeouts).
   - **What was ambiguous** — components that might be renamed-not-rebuilt (would look like a delete + create).
   - **Suggested follow-up agents** — `deployment-risk-scorer` (run before upload), `permission-set-architect` (if PSG composition is new), `release-train-planner` (if this should graduate off Change Sets).
8. **Citations**.

Validate mode:

1. **Summary** — Change Set name, declared component count, reconstructed dependency count, count of gaps.
2. **Gap table** — P0 (missing-from-declared but required), P1 (present-but-redundant), P2 (recommended additions).
3. **Target-org impact** — per-component create / update / type-change-destructive / skip.
4. **Process Observations** — as above, focused on what the human missed during manual assembly.
5. **Citations**.

---

## Escalation / Refusal Rules

- Source org does not have a deployment connection to target → `REFUSAL_MISSING_INPUT`; pre-requisite manual setup.
- `feature_summary` is under 10 words AND `seed_components` is empty → `REFUSAL_INPUT_AMBIGUOUS`.
- Any named component does not exist in the source → `REFUSAL_INPUT_AMBIGUOUS` listing the missing names.
- Component list includes a managed-package artifact → `REFUSAL_MANAGED_PACKAGE`; the agent will not plan to redeploy managed-package components.
- Component count exceeds 1000 → `REFUSAL_OVER_SCOPE_LIMIT`; suggest splitting into multiple Change Sets and cite `skills/devops/migration-from-change-sets-to-sfdx`.
- `profile_handling=include-profiles` on a target org with > 20 active profiles → warn: profiles flatten unpredictably; require explicit user confirmation before proceeding.
- `target_org_alias` unreachable → `REFUSAL_ORG_UNREACHABLE`.

---

## What This Agent Does NOT Do

- Does not upload the Change Set to the target org.
- Does not run deploy validation via Metadata API.
- Does not create the deployment connection.
- Does not reassign Permission Sets after deploy.
- Does not convert Change Sets to SFDX projects — that's a separate path; cite `skills/devops/migration-from-change-sets-to-sfdx`.
- Does not auto-chain.
