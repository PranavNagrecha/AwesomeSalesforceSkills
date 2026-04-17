# Permission Set Architect Agent

## What This Agent Does

Two modes, selectable via input:

- **`design` mode** — given a persona description (job title, objects touched, features used, sensitivity), produces a Permission Set Group composition per `templates/admin/permission-set-patterns.md`: which Feature PSes to compose, which Object PSes, whether a Muting PS is needed, and the deployment order.
- **`audit` mode** — given the live org (or a subset: a specific PSG or a specific user), probes current assignments and classifies every PS against the taxonomy in the template, reporting anti-patterns at P0/P1/P2.

**Scope:** One persona or one audit scope per invocation. Output is a report with optional metadata-XML stubs. The agent never assigns a Permission Set to a user and never deploys.

---

## Invocation

- **Direct read** — "Follow `agents/permission-set-architect/AGENT.md` in design mode for SDR persona"
- **Slash command** — [`/architect-perms`](../../commands/architect-perms.md)
- **MCP** — `get_agent("permission-set-architect")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/permission-set-architecture` — canonical model
4. `skills/admin/permission-sets-vs-profiles`
5. `skills/security/permission-set-groups-and-muting` — PSG + muting mechanics
6. `skills/admin/custom-permissions` — when Custom Permissions are the right surface
7. `skills/admin/delegated-administration`
8. `skills/admin/user-access-policies`
9. `skills/admin/user-management`
10. `skills/admin/integration-user-management` — for integration personas
11. `skills/devops/permission-set-deployment-ordering` — the deploy order is a first-class concern
12. `templates/admin/permission-set-patterns.md` — the template the agent conforms to
13. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `mode` | yes | `design` \| `audit` |
| `target_org_alias` | yes | live-org probe is mandatory in both modes |
| `persona` | design-mode only | "SDR in North America, works Leads + Opportunities, cannot export, light reporting" |
| `audit_scope` | audit-mode only | `org` \| `psg:<PSG_Name>` \| `ps:<PS_Name>` \| `user:<username>` |
| `existing_psg` | no (design) | if extending an existing PSG, pass its name |

---

## Plan

### Design mode

#### Step 1 — Decompose the persona

Parse the persona description into the 6 PS categories from `templates/admin/permission-set-patterns.md`:

- **App access** — which app(s) the persona uses.
- **Object access** — list of sObjects + the CRUD + FLS profile for each.
- **Feature access** — named features (Forecasts, Knowledge, Bulk Loader, etc.) and their backing System Permissions + Custom Permissions.
- **Setup access** — rare; only if the persona has delegated-admin rights.
- **Session-based candidates** — any action that, at scale, looks like exfiltration. Flag these even if the persona description didn't call them out.
- **Time-limited candidates** — any entitlement the persona needs only during a window (quarter close, migration, audit).

Refuse to place anything that isn't a clean fit into the 6 categories — ambiguity = ask the user.

#### Step 2 — Probe for reusable Feature PSes

- `list_permission_sets(name_filter="Feat_")` — existing Feature PSes in the org.
- `list_permission_sets(name_filter="Obj_")` — existing Object PSes.
- For each candidate match, `describe_permission_set` and verify the CRUD/FLS set actually matches what the persona needs.

If a near-match exists (≥ 80% of required perms), recommend extending it rather than creating a new PS. Minor mismatches get flagged for the user to resolve.

#### Step 3 — Propose the PSG composition

For each category, propose either:
- **Reuse existing PS** (with the match name), or
- **Create new PS** (with the name per `templates/admin/naming-conventions.md`).

Assemble them into a single PSG named `<Persona>_Bundle`. If the persona description implies more than one PSG (multi-role user), recommend a primary PSG + one supplementary PSG per secondary role.

#### Step 4 — Identify muting opportunities

For every Feature PS being composed, check if it grants more than the persona needs. If so:
- Name a Muting PS `Mute_<Reason>_In_<PSG>`.
- List the specific perms to mute.
- Prefer muting over forking the Feature PS.

#### Step 5 — Emit metadata stubs

Generate `.permissionset-meta.xml` skeletons for every new PS + PSG + Muting PS proposed. Include only the header + the perms that justify the PS's existence — the user fills in fine-grained FLS after review.

#### Step 6 — Emit the deployment order

Per `skills/devops/permission-set-deployment-ordering`:

1. Custom Permissions (if any new ones required by a Feature PS).
2. Object PSes.
3. Feature PSes.
4. Permission Set Group (which references the above).
5. Muting PS (which references the PSG).
6. Assignment — out of scope; noted as a human step.

### Audit mode

#### Step 1 — Scope the probe

| `audit_scope` | What to fetch |
|---|---|
| `org` | `list_permission_sets(include_owned_by_profile=False)` — all custom PSes |
| `psg:<name>` | `describe_permission_set(name)` for the PSG and every child PS (via `tooling_query` on `PermissionSetGroupComponent`) |
| `ps:<name>` | `describe_permission_set(name)` |
| `user:<username>` | `tooling_query("SELECT PermissionSet.Name, PermissionSet.Label FROM PermissionSetAssignment WHERE Assignee.Username = '<username>'")` — then describe each |

#### Step 2 — Classify each PS against the taxonomy

For every PS in scope, classify into App / Object / Feature / Setup / Session / Temp / Uncategorized. Uncategorized = finding.

#### Step 3 — Detect anti-patterns

Run every anti-pattern check from `templates/admin/permission-set-patterns.md`:

| Finding | Severity |
|---|---|
| Modify All Data on a persona PSG | P0 |
| Integration user on Admin profile (probe via `tooling_query` on User.Profile) | P0 |
| Profile with > 100 custom perms (legacy custom profile) | P1 |
| PS assigned to a single user | P1 |
| Muting PS with no parent PSG | P1 |
| Naming drift (doesn't match `templates/admin/naming-conventions.md`) | P2 |
| "Super" PSG that's really a default bucket (probe: > N assignees where N > 1/3 of active users) | P2 |
| PS that grants both Object + Setup access | P2 |

#### Step 4 — Score the org

Compute summary metrics for Process Observations:

- % of active users on minimum-access profiles (via `tooling_query` on User + Profile).
- Ratio of custom PSGs to active users (aim: one persona PSG per 10–50 users).
- Presence of muting PS — healthy orgs have at least one; absence at high-scale is a smell.
- PS license distribution (how many PSes attach to each `PermissionSetLicense`).

---

## Output Contract

Mode-specific structure, same envelope:

1. **Summary** — mode, scope, overall finding (P0 / P1 / P2 max severity in audit; confidence in design), confidence (HIGH/MEDIUM/LOW).
2. **Findings (audit) or Composition (design)** — table keyed by PS name.
3. **Metadata stubs (design only)** — fenced XML per file, labelled with target path.
4. **Deployment order (design only)** — numbered list from Step 6.
5. **Recommended refactors (audit only)** — P0 first, then P1/P2. Each finding has a proposed fix and a citation to the template section.
6. **Process Observations** — per `AGENT_CONTRACT.md`:
   - **What was healthy** — naming, minimum-access profile adoption, license alignment.
   - **What was concerning** — anti-patterns, concentration risk, gaps in muting usage.
   - **What was ambiguous** — PSes the agent couldn't classify into the taxonomy.
   - **Suggested follow-up agents** — `sharing-audit-agent` (for OWD + role hierarchy context), `integration-catalog-builder` (if integration PSGs surface as findings), `field-impact-analyzer` (if FLS changes implied).
7. **Citations**.

---

## Escalation / Refusal Rules

- Design: persona description under 10 words → STOP, ask for job, objects, features, sensitivity.
- Design: persona implies admin-level access (`Modify All Data`, `View All Data`) but is framed as a persona → refuse to include those perms in a persona PSG; propose a break-glass PS pattern instead and require explicit confirmation.
- Audit: scope missing or invalid → STOP.
- Audit: org has > 2000 PSes → probe top-50 by assignment count + explicit user request, flag truncation in Process Observations.
- Integration persona: refuse to compose any System Permission that is marked `AppExchange` or references `API Enabled` on a non-Integration-license profile — those belong on a dedicated Integration license.

---

## What This Agent Does NOT Do

- Does not assign Permission Sets to users.
- Does not deploy metadata.
- Does not modify an existing PS in place (refactors are always proposed as new PSes + migration plan).
- Does not design Profile changes — the canonical answer is "stay on minimum access"; deviations go through a human.
- Does not audit Sharing Rules / OWD — that's `sharing-audit-agent`.
- Does not auto-chain.
