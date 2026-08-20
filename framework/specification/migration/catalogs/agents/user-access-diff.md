# V2 Migration Profile: `user-access-diff`

## Current source

- Path: `agents/user-access-diff/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Given two Users in the same org, produces a symmetric, dimension-by-dimension comparison of their effective access surface: profile, active Permission Set and Permission Set Group assignments (with PSG components flattened), object CRUD, field-level security (opt-in), system permissions (`ModifyAllData`, `ViewAllUsers`, `AuthorApex`, etc.), Apex class / VF page / Flow / Custom Permission / Named Credential grants, public group and queue membership, role hierarchy placement, and territory assignment. Output is a side-by-side report with three buckets per dimension — **identical**, **only in User A**, **only in User B** — plus risk flags when the delta crosses a known sensitivity threshold (e.g., one user has `ModifyAllData` and the other does not).

## V2 role

- Exposure: command/catalog specialist; not default subagent.
- This agent is a **catalog specialist**, not automatically a Cursor subagent.
- It MUST execute through the V2 run contract when invoked by a V2 command or adapter.
- Its existing Salesforce domain guidance remains canonical until explicitly superseded by a reviewed V2 product specification.

## Required V2 inputs

The adapter MUST validate the existing `inputs.schema.json` when present. It MUST additionally accept a run context containing `run_id`, execution mode, host capabilities, context budget, evidence policy, and optional project/org locators. Missing hard inputs produce `refused`; unavailable optional enrichment produces `partial` or a documented standalone path.

### Current input excerpt

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

## Evidence requirements

- Material statements about the target org require live read-only org evidence or an explicit `org_evidence_unavailable` unknown.
- Material statements about local source require project-inspector evidence or an explicit standalone result.
- Platform behavior claims require a current official source, a versioned SfSkills skill based on an official source, or a clearly labelled hypothesis.
- Skill citations justify recommendations; they do not prove org state.
- Every material claim MUST appear in the claim-evidence graph.

## Evidence prohibited

- Uncited model memory as proof of org state.
- A stale deployment/test result represented as current without timestamp and org association.
- A skill used as evidence that a component exists.
- Hidden raw tool output not represented in the evidence index.
- Product-side Salesforce mutation.

## Context contract

- Core contract and safety context: always loaded.
- Domain context target: at most 8 selected skill/reference files.
- Hard domain context limit: 12 unless the run returns an explicit overflow state.
- Raw MCP output in the model context: at most 32 KiB per page.
- Full subagent transcripts: prohibited.
- Existing broad mandatory-read lists MUST be converted to core plus conditional packs before this agent can be labelled V2-native.

## Framework collaborators

- `sf-context-librarian`: required when more than three candidate knowledge files exist.
- `sf-project-inspector`: optional enrichment; never assume the SfSkills repository is the Salesforce project.
- `sf-org-grounder`: required when `requires_org` is true and live mode is requested; host fallback applies when subagents cannot call MCP.
- `sf-evidence-reviewer`: required before a completed V2 product result.
- Deterministic output validation: always required.

## Failure modes

- Ambiguous target org or project.
- Missing or stale evidence.
- Context overflow or silent truncation.
- Contradictory repository and org evidence.
- Unsupported claim or invalid citation.
- Host lacks a required capability.
- Unsafe requested action.

## Success criteria

1. Inputs are schema-valid and execution mode is explicit.
2. Context stays within the declared budget or reports overflow.
3. Every material claim has valid evidence.
4. Unknowns and contradictions are surfaced.
5. The evidence reviewer produces no blocking finding.
6. The output envelope and product-specific schema validate.
7. No product mutation occurs.

## Current output excerpt

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
   - **Suggested follow-ups** — `permission-set-architect` (design remediation), `audit-router --domain sharing` (record-visibility divergence), `profile-to-permset-migrator` (if Profile difference is the dominant delta).
8. **Citations** — every skill, probe recipe, and MCP tool consulted.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/user-access-diff/<run_id>.md`
- **JSON envelope:** `docs/reports/user-access-diff/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

### Dimensions (Wave 10 contract)

The agent's envelope MUST place every dimension below in ei

## Current non-goals excerpt

- Does not grant, revoke, or modify Permission Set assignments, Profile membership, group membership, or any access record.
- Does not compute sharing-rule outcomes (OWD + role hierarchy + sharing rules). Two users with identical PSes can still see different records. Use `audit-router --domain sharing` for that.
- Does not explain WHY a permission was granted historically. Use field history + audit trail via `user-access-policies` skill guidance.
- Does not propose a remediation PSG layout. Follow up with `permission-set-architect`.
- Does not chain to other agents automatically.
- Does not compare more than two users per invocation.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
