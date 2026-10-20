---
id: access-path-explainer
class: runtime
version: 1.0.1
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-08-20
updated: 2026-10-19
default_output_dir: "docs/reports/access-path-explainer/"
output_formats:
  - markdown
  - json
multi_dimensional: false
compatible_mcp: "get_user_access_evidence"
expected_mcp_calls: 4
dependencies:
  skills:
    - security/record-access-troubleshooting
    - admin/sharing-and-visibility
    - security/permission-set-groups-and-muting
    - admin/approval-processes
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
---
# Access Path Explainer

## What This Agent Does

Explain why a specific Salesforce user can or cannot perform an operation on a named resource, layer by layer. Works from a local JSON fixture via `get_user_access_evidence` (`result_path`) in this milestone; live retrieve is opt-in and read-only. Stops at diagnosis and an ordered human plan.

**Scope:** one P03 invocation — one explicit target set per run.

---

## Invocation

- **Direct read** — follow this playbook with the typed inputs below
- **Slash command** — [`/why-cant-user`](../../commands/why-cant-user.md)
- **MCP** — `get_agent("access-path-explainer")`

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md` (run-time agents: no org writes, no invented citations)
3. `agents/_shared/DELIVERABLE_CONTRACT.md`

### Domain skills
4. `skills/security/record-access-troubleshooting` — record-level access diagnosis
5. `skills/admin/sharing-and-visibility` — OWD, role hierarchy, and sharing layers
6. `skills/security/permission-set-groups-and-muting` — PSG and muting permission sets
7. `skills/admin/approval-processes` — read only when the remedy under consideration is "submit for approval", or a record-lock (pending approval) is among the findings: submitter rules, approver resolution, `recordEditability`

Keep the access reading list small: only the three core Mandatory Reads (4-6), read 7 when its trigger applies, plus context-pack files triggered by the observed blocking layer.

---

## Inputs

Typed schema: `agents/access-path-explainer/inputs.schema.json`.

Validated by `pipelines.product.command_inputs.validate_why_cant_user_inputs`.

| `user` | required | Typed command input |
| `resource` | required | Typed command input |
| `operation` | required | Typed command input |
| `result_path` | optional fixture | Path to captured JSON for `get_user_access_evidence` |
| `item_limit` | optional | Bounded page size (default 100) |

If required fields are missing, refuse with `REFUSAL_MISSING_INPUT`. Never guess a user, org, job, or snapshot.

---

## Plan

1. **Validate inputs.** Run `validate_why_cant_user_inputs`. No silent defaults.
2. **Ground evidence.** Parse via `pipelines/product/user_access_result.py` → `normalize_user_access`. Live/MCP: `get_user_access_evidence` with `result_path` in fixture mode. Honor `truncated` / `next_cursor`. Bound payloads at 32 KiB.
3. **Select context.** Keep Mandatory Reads plus at most a few conditional references from observed finding types.
4. **Diagnose** only from evidence IDs. Separate primary vs contributing hypotheses. Undeclared gaps stay unknowns. Trace in this order, and do not reason about fields, validation rules, or approvals until step (a) is settled:
   a. **Record access is hypothesis zero.** Does the user have edit access to THIS record (owner, role hierarchy, sharing rule, team, manual or Apex share), and is a working comparison user's success explained by Modify All Data, Modify All Records, or View All on the object rather than by the mechanism under suspicion? With an org: run `SELECT RecordId, HasReadAccess, HasEditAccess, MaxAccessLevel FROM UserRecordAccess WHERE UserId = '<user>' AND RecordId = '<record>'` for the user and for the comparison user (read-only; the human runs it). Without an org (fixture or metadata only): read the object's OWD, the role hierarchy, sharing rules and criteria, the record owner assumption, and the object permissions on the user's profile and permission sets; record each as an unknown, not a finding, until evidence confirms it.
   b. Object and field permissions (CRUD/FLS, including muting), then validation rules and automation that block the save.
   c. Record lock. If the record is pending approval, `recordEditability: AdminOnly` means only users with Modify All Data OR Modify All Records on the object can edit it (Metadata API guide, `ProcessDefinition`, `recordEditability`: "Users with the 'Modify All Data' permission" and "Users with the 'Modify All Records' object-level permission for the given object"); `AdminOrCurrentApprover` adds the assigned approver. Cite `skills/admin/approval-processes`.
5. **Plan remediation** as ordered human steps. Show verification commands; do not execute them. When the remedy is "submit for approval", name which of these the human must verify before telling the user to submit: (i) submitter rules of the approval process (owner-only, or `allowedSubmitters` listing the user, role, or group); (ii) approver resolution (is the Manager field populated on the submitter, does the queue or related-user lookup resolve to an active user); (iii) recall and lock state (is the record already pending approval, and who can recall it). An approval remedy that skips these checks is not a remedy.
6. **Evidence review.** Independent pass via `pipelines/product/evidence_lint.py`.
7. **Persist.** Envelope + markdown under `docs/reports/access-path-explainer/`.

---

## Output Contract

Envelope plus markdown. Set `outcome` to `completed`, `partial`, `refused`, or `failed`.

Must include P03-specific findings, confidence, evidence IDs on material claims, unknowns, context/provenance, evidence-review verdict, and **Process Observations**.

Every cited line must support the specific claim it is attached to, and mechanisms that cannot explain the reported symptom are not listed.

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/access-path-explainer/<run_id>.md`
- **JSON envelope:** `docs/reports/access-path-explainer/<run_id>.json`
- Product runs MAY also write redacted telemetry under `.sfskills/runs/<run_id>/` (gitignored).
- **Atomic write:** both `docs/reports` files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` renders the report inline and emits the envelope as a fenced JSON block.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** `get_user_access_evidence` / a local JSON fixture plus this agent's typed inputs. This agent does NOT generate ad-hoc code to substitute for those surfaces.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** if evidence is truncated, set `outcome: partial` and record the gap in unknowns — never omit it.

---

## Escalation / Refusal Rules

| Condition | Code |
| --- | --- |
| Missing required inputs | `REFUSAL_MISSING_INPUT` |
| Ambiguous org/user/snapshot | `REFUSAL_INPUT_AMBIGUOUS` |
| Org alias given but unauthenticated | `REFUSAL_ORG_UNREACHABLE` |
| Request to mutate Salesforce | `REFUSAL_OUT_OF_SCOPE` |

Partial results are valid when evidence is truncated: `outcome: partial`.

---

## What This Agent Does NOT Do

- Does not assign permissions, mutate sharing, or change profiles.
- Execute verification commands
- Pretend a missing search index is an empty library
- Load more than 12 domain skill/reference files without declaring overflow
