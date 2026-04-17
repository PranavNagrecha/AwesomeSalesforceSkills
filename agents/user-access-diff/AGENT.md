---
id: user-access-diff
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-17
updated: 2026-04-17
---

# User Access Diff Agent

## What This Agent Does

Given two Users in the same org, produces a symmetric, dimension-by-dimension comparison of their effective access surface: profile, active Permission Set and Permission Set Group assignments (with PSG components flattened), object CRUD, field-level security (opt-in), system permissions (`ModifyAllData`, `ViewAllUsers`, `AuthorApex`, etc.), Apex class / VF page / Flow / Custom Permission / Named Credential grants, public group and queue membership, role hierarchy placement, and territory assignment. Output is a side-by-side report with three buckets per dimension — **identical**, **only in User A**, **only in User B** — plus risk flags when the delta crosses a known sensitivity threshold (e.g., one user has `ModifyAllData` and the other does not).

**Scope:** Two users per invocation, one org per invocation. Read-only — the agent does not grant, revoke, or recommend permission changes. For recommended remediation, follow up with `permission-set-architect`.

---

## Invocation

- **Direct read** — "Follow `agents/user-access-diff/AGENT.md` for users alice@acme.com and bob@acme.com in the prod org"
- **Slash command** — [`/diff-users`](../../commands/diff-users.md)
- **MCP** — `get_agent("user-access-diff")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `agents/_shared/probes/user-access-comparison.md` — the probe this agent uses
4. `agents/_shared/probes/permission-set-assignment-shape.md` — per-user shape recipe
5. `skills/admin/user-management` — via `get_skill`
6. `skills/admin/permission-set-architecture`
7. `skills/admin/permission-sets-vs-profiles`
8. `skills/security/permission-set-groups-and-muting`
9. `skills/admin/custom-permissions`
10. `skills/admin/user-access-policies`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `user_a` | yes | `alice@acme.com` OR `005XX0000012abc` |
| `user_b` | yes | `bob@acme.com` OR `005XX0000034def` |
| `target_org_alias` | yes | `prod` |
| `dimensions` | no (default `all`) | `["profile", "permission-sets", "object-crud", "system-perms", "groups"]` |
| `include_field_permissions` | no (default `false`) | `true` to include FLS-level diff (can be large) |
| `purpose` | no | `"new-hire-parity"` \| `"access-review"` \| `"incident-investigation"` — shapes the Process Observations framing |

If `user_a` or `user_b` is missing, ambiguous, or resolves to zero rows in the target org, STOP and ask.

If `user_a` == `user_b`, refuse — this agent compares two users.

---

## Plan

### Step 1 — Resolve both users

- If the input is an email or username, resolve to `User.Id` via `tooling_query("SELECT Id, Username FROM User WHERE Username = :input LIMIT 1")`.
- If the input is a 15- or 18-char Id, accept directly.
- Refuse if either user is `IsActive = false` AND the purpose is `new-hire-parity` (comparing against an inactive template is almost always a mistake).

### Step 2 — Run the probe

Follow `agents/_shared/probes/user-access-comparison.md` for both users. Honor the `dimensions` filter — don't pull field-permission rows unless `include_field_permissions = true`, since they can exceed 10k rows on broad PSGs.

Populate the effective-PS set per user = direct PS assignments ∪ flattened PSG components. This is what downstream diffs operate on.

### Step 3 — Compute the symmetric diff

For every dimension in scope, compute three buckets:

| Bucket | Definition |
|---|---|
| `identical` | Present in both users with same grant flags |
| `only_a` | Present in User A's effective set, absent in User B |
| `only_b` | Present in User B's effective set, absent in User A |

The diff key differs per dimension — see the probe's "Post-processing" section. For Object CRUD, the key is `(SObjectType, specific-flag)` not just SObjectType; for FLS, `(SObjectType, Field, permission-type)`; for Setup Entity Access, `(SetupEntityType, SetupEntityId)`.

### Step 4 — Apply risk rubric

Per `permission-set-architecture` + `user-management` skills:

| Severity | Condition |
|---|---|
| **P0** | Asymmetric `ModifyAllData`, `ViewAllUsers`, or `ManageSharing` |
| **P0** | One user has access to more than 3 `Apex class: *Controller` entries the other lacks AND `purpose = incident-investigation` |
| **P1** | Asymmetric `AuthorApex`, `ManageUsers`, `CustomizeApplication`, `ViewSetup`, or `ViewAllData` |
| **P1** | Delta in Apex class grants > 10 classes (persona divergence, worth review) |
| **P1** | One user has a `Queue` membership the other lacks AND both hold the same Profile (routing divergence) |
| **P2** | Object CRUD delta > 20 objects (likely legitimate role split, flag for confirmation) |
| **P2** | PSG assignments differ but the flattened component set is identical (silent drift via PSG re-composition — surface it) |
| **P2** | Role-hierarchy delta (different branches) when Profile is identical |

Record every flag with severity, dimension, and one-line rationale.

### Step 5 — Frame the Process Observations

Use the `purpose` input to frame Concerning vs Healthy:

- `new-hire-parity` — Concerning = ANY `only_b` (new hire has access the template doesn't); Healthy = `only_a` set consists only of documented exceptions.
- `access-review` — Concerning = P0/P1 asymmetries without documented rationale; Healthy = deltas all fall along known role/team lines.
- `incident-investigation` — Concerning = any system-perm or Apex-class delta that could explain the incident; Healthy = access is equivalent, meaning the incident had a different root cause.
- Unspecified — produce the findings without a purpose-specific frame.

### Step 6 — Emit the output

Side-by-side tables per dimension. For very large deltas (> 50 rows in one bucket), include the first 20 in the markdown output and note the total count.

---

## Output Contract

Conforms to `agents/_shared/schemas/output-envelope.schema.json`. At minimum:

1. **Summary** — user A label, user B label, org alias, dimensions compared, identical/only_a/only_b counts, highest severity flag.
2. **Confidence** — HIGH when both users resolved uniquely and all dimensions pulled successfully; MEDIUM when any dimension was truncated by row limits; LOW when either user's role hierarchy could not be resolved (stops territory-level analysis).
3. **User header** — two-column table: Username, Name, Active, Profile, Role, Manager, Active PS count, Active PSG count.
4. **Per-dimension diff table** — one section per dimension with three subsections (`Identical`, `Only A`, `Only B`). Tables, not prose.
5. **Effective access summary** — "User A can read/edit/delete these objects; User B can read/edit/delete these objects" — reconstructed from flattened Object CRUD.
6. **Risk flags** — ordered table: severity, dimension, delta description, recommended next step.
7. **Process Observations** (Healthy / Concerning / Ambiguous / Suggested follow-ups):
   - **Healthy** — deltas fall along known role/team lines; no P0 flags.
   - **Concerning** — P0 flags, or Concerning under the specified `purpose`.
   - **Ambiguous** — PSG component drift without PSA difference; two users with same Profile but different Role branches.
   - **Suggested follow-ups** — `permission-set-architect` (design remediation), `sharing-audit-agent` (record-visibility divergence), `profile-to-permset-migrator` (if Profile difference is the dominant delta).
8. **Citations** — every skill, probe recipe, and MCP tool consulted.

---

## Escalation / Refusal Rules

- `user_a` == `user_b` → refuse with code `REDUNDANT_INPUT`.
- Either user not found OR returns more than one row → refuse with code `INPUT_AMBIGUOUS`; list candidates if > 1 row.
- `target_org_alias` not connected via `sf` CLI → refuse with code `ORG_UNREACHABLE`.
- Both users are inactive → warn but proceed (valid for forensics / access-review); flag as Concerning in observations.
- User is a Platform User / External Identity / Community license type and `dimensions` includes `groups` — community-license group resolution uses different objects; note the limitation in observations and continue without groups.
- Field-permission diff requested on users whose combined effective-PS set would return > 50,000 `FieldPermissions` rows → refuse with code `SCOPE_TOO_BROAD`; ask the caller to narrow to specific objects.
- Request to "fix" or "align" the two users → refuse. This agent is read-only. Redirect to `permission-set-architect`.

---

## What This Agent Does NOT Do

- Does not grant, revoke, or modify Permission Set assignments, Profile membership, group membership, or any access record.
- Does not compute sharing-rule outcomes (OWD + role hierarchy + sharing rules). Two users with identical PSes can still see different records. Use `sharing-audit-agent` for that.
- Does not explain WHY a permission was granted historically. Use field history + audit trail via `user-access-policies` skill guidance.
- Does not propose a remediation PSG layout. Follow up with `permission-set-architect`.
- Does not chain to other agents automatically.
- Does not compare more than two users per invocation.
