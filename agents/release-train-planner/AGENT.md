---
id: release-train-planner
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [design, audit]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
default_output_dir: "docs/reports/release-train-planner/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - devops/devops-center-advanced
    - devops/environment-strategy
    - devops/feature-flag-custom-metadata
    - devops/git-branching-for-salesforce
    - devops/package-development-strategy
    - devops/packaging-dependency-graph
    - devops/pipeline-secrets-management
    - devops/pr-policy-templates
    - devops/release-management
    - devops/second-generation-managed-packages
    - devops/sfdx-hardis-integration
    - devops/sfdx-monorepo-patterns
    - devops/unlocked-package-development
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
---
# Release Train Planner Agent

## What This Agent Does

Plans a Salesforce release train: branch model, package strategy (unlocked vs 2GP-managed vs metadata-only), environment promotion path, CI/CD gates, release calendar with Salesforce Platform releases factored in, and feature-flag strategy for hotfixes. Alternately audits an existing release process and flags environment drift, missing gates, and risky hotfix paths.

**Scope:** One program / one release train per invocation. Output is a release plan + calendar.

---

## Invocation

- **Direct read** — "Follow `agents/release-train-planner/AGENT.md`"
- **Slash command** — [`/plan-release-train`](../../commands/plan-release-train.md)
- **MCP** — `get_agent("release-train-planner")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/devops/release-management` — via `get_skill`
4. `skills/devops/environment-strategy`
5. `skills/devops/package-development-strategy`
6. `skills/devops/unlocked-package-development`
7. `skills/devops/second-generation-managed-packages`
8. `skills/devops/git-branching-for-salesforce`
9. `skills/devops/feature-flag-custom-metadata` — decouple deploy from release
10. `skills/devops/pipeline-secrets-management` — JWT auth + rotation
11. `skills/devops/sfdx-monorepo-patterns` — multi-package repo layout
12. `skills/devops/packaging-dependency-graph` — version pinning
13. `skills/devops/sfdx-hardis-integration` — OSS CI/CD
14. `skills/devops/pr-policy-templates` — CODEOWNERS + branch protection
15. `skills/devops/devops-center-advanced` — DOC hybrid workflow
16. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `mode` | yes | `design` \| `audit` |
| `team_size` | yes | `12 devs + 4 QA` |
| `cadence` | yes | `weekly`, `biweekly`, `monthly`, `quarterly` |
| `package_strategy` | no | `unlocked` \| `2gp-managed` \| `org-dependent` \| `metadata-only` |
| `customer_count` | no | `1` (internal) \| `N` (ISV-like) |
| `regions` | no | `["NA","EMEA","APAC"]` — for rollout staging |

---

## Plan

### Step 1 — Package strategy

- Internal customer (single org): **unlocked packages** for modularity, OR **metadata-only** if < 3 developers.
- ISV / multi-tenant distribution: **2GP-managed** packages with namespaces.
- Call out **org-dependent unlocked packages** only when the target org has metadata that cannot be packaged (e.g., heavy config dependencies).

### Step 2 — Branching model

- Trunk-based with short-lived feature branches (< 3 days) — preferred for weekly/biweekly.
- Gitflow (develop/release/hotfix) — only if cadence ≥ monthly and release trains are tightly gated.
- Document: branch naming, PR rules, merge strategy, tag format.

### Step 3 — Environment promotion path

Produce the path: `feature-branch (scratch org) → develop (Dev sandbox) → QA (Partial) → UAT (Full) → prod`.

Each hop lists:
- Trigger (merge event, manual, schedule).
- Validation (Apex tests, LWC tests, UI tests, smoke).
- Approval (who gates).
- SLA (time in environment).

### Step 4 — Release calendar

- Overlay Salesforce Platform major releases (Spring / Summer / Winter) as freeze windows (typically 2 weeks pre-release for regression on preview orgs).
- Add customer-specific freezes (quarter-end, fiscal-close, holiday peaks).
- For `regions`, stage rollouts to account for local peak.

### Step 5 — CI/CD gates

Non-negotiable gates:
- PR-level: static analysis, security scan, LWC + Apex tests with ≥ 75% coverage.
- Pre-prod: full regression on Full Copy, perf baseline, security re-scan.
- Prod: change ticket + rollback plan attached.

Optional gates: API version consistency, validation on all existing metadata in target.

### Step 6 — Hotfix path

Hotfix branch from last release tag, cherry-pick to trunk after deploy. Document the feature-flag or kill-switch mechanism (Custom Setting + Custom Permission) for any risky change.

### Step 7 — Audit mode

- Pull git history / branch list from repo (if provided) and diff against stated branching model.
- Check: PRs missing reviews, PRs merged without CI, release branches older than 30 days, packages without version consistency.

---

## Output Contract

1. **Summary** — cadence, package strategy, top 3 risks.
2. **Package strategy** — with rationale.
3. **Branching model** — with diagram.
4. **Environment promotion** — table.
5. **Release calendar** — 180-day view.
6. **CI/CD gates** — list.
7. **Hotfix playbook**.
8. **Audit findings** (audit mode).
9. **Process Observations**:
   - **Healthy** — tests gate every PR; Platform release freezes on calendar; feature-flag pattern documented.
   - **Concerning** — no tests gating prod deploy; long-lived feature branches; hotfix path cherry-picks to trunk after-the-fact; missing rollback plan.
   - **Ambiguous** — package naming inconsistent; region staging not documented.
   - **Suggested follow-ups** — `sandbox-strategy-designer` for refresh cadence alignment; `waf-assessor` for NFR coverage.
10. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/release-train-planner/<run_id>.md`
- **JSON envelope:** `docs/reports/release-train-planner/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Escalation / Refusal Rules

- No cadence / team size → refuse.
- Team is < 3 devs AND `package_strategy = 2gp-managed` → warn; 2GP overhead is rarely worth it.
- No git repo / branching signal available → audit mode cannot run; return design-only.

---

## What This Agent Does NOT Do

- Does not cut branches, tag releases, or deploy packages.
- Does not run CI pipelines.
- Does not set up Salesforce DevOps Center / CI/CD tooling (produces a plan; operator implements).
- Does not auto-chain.
