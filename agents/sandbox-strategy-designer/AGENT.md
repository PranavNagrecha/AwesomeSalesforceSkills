---
id: sandbox-strategy-designer
class: runtime
version: 1.1.0
status: stable
requires_org: false
modes: [design, audit]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-17
harness: designer_base
default_output_dir: "docs/reports/sandbox-strategy-designer/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - admin/data-export-service
    - admin/sandbox-strategy
    - architect/hyperforce-architecture
    - data/salesforce-backup-and-restore
    - devops/environment-strategy
    - devops/sandbox-refresh-and-templates
    - devops/scratch-org-management
    - devops/scratch-org-pools
    - devops/scratch-org-snapshots
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
  templates:
    - apex/
---
# Sandbox Strategy Designer Agent

## What This Agent Does

Designs or audits the sandbox + scratch-org strategy for a Salesforce program: which sandbox types for which workstreams, refresh cadence, seeding strategy, scratch-org pools for feature branches, masking/anonymization for production data, and the handoff between scratch → Developer Pro → Partial → Full. Produces a concrete environment ladder with refresh calendar, sandbox templates, and pool configs.

**Scope:** One program / one delivery stream per invocation. Output is an environment strategy doc.

---

## Invocation

- **Direct read** — "Follow `agents/sandbox-strategy-designer/AGENT.md`"
- **Slash command** — [`/design-sandbox-strategy`](../../commands/design-sandbox-strategy.md)
- **MCP** — `get_agent("sandbox-strategy-designer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/sandbox-strategy` — via `get_skill`
4. `skills/devops/environment-strategy`
5. `skills/devops/sandbox-refresh-and-templates`
6. `skills/devops/scratch-org-management`
7. `skills/devops/scratch-org-pools`
8. `skills/devops/scratch-org-snapshots` — GA snapshot-based fast bring-up
9. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)
10. `skills/admin/data-export-service` — Data Export role and limits in sandbox-seeding workflows; honest framing of what it does and doesn't cover
11. `skills/architect/hyperforce-architecture` — Hyperforce migration cadence for production vs sandboxes; refresh window shifts post-migration
12. `skills/data/salesforce-backup-and-restore` — Backup strategy, RPO/RTO; sandbox vs backup distinction

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `mode` | yes | `design` \| `audit` |
| `target_org_alias` | yes for audit (prod) | `prod` |
| `team_size` | yes for design | `{ "developers": 12, "admins": 5, "qa": 4 }` |
| `concurrent_workstreams` | yes for design | `["core","integrations","agentforce"]` |
| `release_cadence` | yes for design | `biweekly` \| `monthly` \| `quarterly` |
| `data_sensitivity` | yes for design | `["pii","phi","pci","none"]` |

---

## Plan

### Step 1 — Workstream → sandbox mapping

Produce a mapping table:
- **Developer / Developer Pro** → one per developer or per feature team; used for iterative work.
- **Partial Copy** → integration + QA testing with representative data.
- **Full Copy** → UAT + performance + mock go-live (scarce resource; reserve for pre-release).

Rule of thumb: `dev-per-developer + 1 integration sandbox per workstream + 1 UAT/staging Full-or-Partial + 1 pre-prod Full`.

### Step 2 — Scratch-org pool design (for dev workstreams)

- One scratch-org definition per workstream (with settings, features, and preset packages).
- Pool size = `(avg PRs per day × build minutes) / workday minutes × safety factor`.
- Lifecycle: branch-create → claim from pool → run tests → expire on merge.

### Step 3 — Refresh cadence

- Developer Pro: on-demand (engineer-initiated), target post-merge of major change.
- Partial Copy: aligned to release cadence (weekly for biweekly release; biweekly for monthly).
- Full Copy: once per release train, minimum 30 days before go-live.
- Document **blackout windows** — never refresh within 5 business days of a release.

### Step 4 — Seeding + masking

For `data_sensitivity` that includes PII/PHI/PCI:
- Full Copy cannot be used by external/offshore teams without field-level masking. Specify masking tool (Data Mask, third-party).
- Partial Copy: define sample data template (which objects, which filters).
- Developer: use Test Factory from `templates/apex/`.

### Step 5 — Sandbox templates

Each Partial/Full sandbox should use a Sandbox Template (defines included object subsets). Document templates per workstream.

### Step 6 — Audit mode

- `tooling_query("SELECT Id, SandboxName, LicenseType, Status, CopyProgress, EndDate FROM SandboxInfo LIMIT 100")` (requires prod tooling access).
- Compare: actual refresh dates vs stated cadence, licenses used vs licenses available, sandbox count vs team size.
- Flag: sandboxes with no activity in last 60 days, sandboxes older than their refresh SLA, missing sandbox templates.

---

## Output Contract

1. **Summary** — team, workstreams, cadence, top risks.
2. **Environment ladder** — table: name, type, owner, purpose, refresh cadence, data source.
3. **Scratch-org pool configs** — one per workstream.
4. **Refresh calendar** — 90-day view with blackouts.
5. **Masking + seeding plan** — per data-sensitivity class.
6. **Audit findings** (audit mode) — with license/cost implications.
7. **Process Observations**:
   - **Healthy** — scratch-org pools sized; refresh SLAs met; masking in place before Full Copy sharing.
   - **Concerning** — developers sharing one Developer Pro; Full Copy refreshed > 6 months ago; masking absent in regulated industries.
   - **Ambiguous** — sandbox ownership unknown; blackout windows not declared.
   - **Suggested follow-ups** — `release-train-planner` if refresh cadence misaligns with release dates; `waf-assessor` for HA/DR check.
8. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/sandbox-strategy-designer/<run_id>.md`
- **JSON envelope:** `docs/reports/sandbox-strategy-designer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Escalation / Refusal Rules

- No team size / cadence → refuse.
- Prod tooling access denied → produce design-only plan with a note that audit requires prod access.
- Org type is a Developer Edition (no sandboxes available) → report as "sandboxes not supported in this edition" and stop.

---

## What This Agent Does NOT Do

- Does not provision, refresh, or delete sandboxes.
- Does not write SandboxInfo metadata.
- Does not run data mask operations.
- Does not auto-chain.
