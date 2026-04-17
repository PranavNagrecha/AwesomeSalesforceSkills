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
