# Validation — How SfSkills verifies itself against a real Salesforce org

**Status:** Wave 9, April 2026.

Every skill, agent, and probe in this repo is verified against a live Salesforce org via three automated harnesses. Unlike the structural validators (which check "does the AGENT.md have 8 sections?"), these harnesses check **behavior** — does the SOQL actually execute, does the field actually exist, does the agent's declared dependencies actually resolve.

---

## The three validation layers

### Layer 1 — Probe SOQL Correctness

**What:** Every probe recipe under `agents/_shared/probes/*.md` contains fenced SOQL blocks. This harness extracts every query, substitutes placeholders with live-org values, and executes them via `sf data query`. Failures are classified against the six modes in `skills/admin/salesforce-object-queryability`.

**Script:** `scripts/validate_probes_against_org.py`

**Run:**
```bash
python3 scripts/validate_probes_against_org.py --target-org <alias>
```

**Output:** `docs/validation/probe_report_<date>.md`

**What it caught when first run:**
- `ApexClass.Body` can't be filtered in WHERE
- `MatchingRule.IsActive` doesn't exist (it's `RuleStatus`)
- `FlowDefinitionView.DeveloperName` doesn't exist (it's `ApiName`)
- `PermissionsEditPublicReports` doesn't exist on `PermissionSet`
- SOQL aggregates don't accept `AS alias`
- `DefaultCurrencyIsoCode` only exists in multi-currency orgs
- Territory2 queries need to be gated behind "ETM enabled" check

All six were real probe bugs that would have produced wrong output in any customer org. Now fixed. Re-run enforces they stay fixed.

**Special statuses:**
- ⏭️ `EXPECTED-SKIP` — object gated by a feature not enabled in the org (Territory2, Field Service, Health Cloud). The probe correctly documents this as optional.
- ✅ `SUCCESS-VIA-TOOLING` — query needed Tooling API instead of Data API. Automatic routing for known Tooling-only objects (`ApexClass`, `Flow`, etc.).

---

### Layer 2 — Agent Smoke Tests

**What:** Every `class: runtime, status != deprecated` agent gets six structural + dependency checks:

1. Required 8 sections present + in order
2. All Mandatory Read citations resolve to real files
3. Declared `dependencies` frontmatter cover all body citations
4. Slash-command (`commands/<alias>.md`) exists
5. `inputs.schema.json` (if present) is valid JSON Schema
6. Declared probes executable (per Layer 1 report)

**Script:** `scripts/smoke_test_agents.py`

**Run:**
```bash
python3 scripts/smoke_test_agents.py --target-org <alias>
# Or one agent:
python3 scripts/smoke_test_agents.py --target-org <alias> --agent user-access-diff
```

**Output:**
- Rollup: `docs/validation/agent_smoke_rollup_<date>.md`
- Per-agent: `docs/validation/agent_smoke_<date>/<agent-id>.md`

Each per-agent report has a **human TL;DR at the top** and a **machine-readable JSON block at the bottom**, plus a reviewer checklist.

---

### Layer 3 — Skill Factuality Sampling

**What:** Scans SKILL.md files for testable claims (`SObject.Field` references, governor limit numbers, SOQL patterns) and verifies them against the live org's `describe` output. Skills are classified as "testable" (makes platform-fact claims) or "guidance" (pure design content). Only testable ones are verified.

**Script:** `scripts/validate_skill_factuality.py`

**Run:**
```bash
python3 scripts/validate_skill_factuality.py --target-org <alias> --sample 200
```

**Output:** `docs/validation/skill_factuality_<date>.md`

**What counts as a "wrong claim":** a field reference like `SomeObject.FieldName` where the object exists in the org but the field doesn't. The harness is conservative — custom fields (`__c`), feature-gated fields (like `Account.IsPersonAccount`), and relationship traversals (like `Account.Owner`) are classified as **unverifiable**, not wrong.

---

## Summary of results (baseline run — 2026-04-17)

| Layer | Metric | Result |
|---|---|---|
| 1 — Probes | Queries run | 21 |
| 1 — Probes | Passed | 21 (100%) |
| 1 — Probes | Failed | 0 |
| 1 — Probes | Real probe bugs fixed | 6 |
| 2 — Agents | Runtime agents smoke-tested | 42 |
| 2 — Agents | Passed | 42 (100%) |
| 2 — Agents | Failed | 0 |
| 3 — Skills | Sample size | 200 |
| 3 — Skills | Testable skills | 63 |
| 3 — Skills | Factual errors detected | 0 |

**Zero silent drops.** Every probe failure is either a success, an expected-skip (documented feature gate), or surfaces as a visible classification.

---

## When to re-run

| Trigger | Layer(s) to re-run |
|---|---|
| Probe recipe edited | Layer 1 |
| AGENT.md edited | Layer 2 |
| New SKILL.md authored that references field names | Layer 3 |
| Salesforce API version bump (e.g. v66 → v68) | All three |
| New runtime agent added | Layer 2 |
| Consumer reports wrong output from an agent | All three |

Run all three in sequence:
```bash
python3 scripts/validate_probes_against_org.py --target-org <alias>
python3 scripts/smoke_test_agents.py --target-org <alias>
python3 scripts/validate_skill_factuality.py --target-org <alias> --sample 200
```

Each writes a dated report to `docs/validation/`. Commit the reports with the change that prompted them — the reports become part of the audit trail.

---

## CI integration

The validation harnesses require live-org access, so they run on **manual GitHub Actions dispatch** (not on every PR — that would require a shared sandbox token).

Workflow: `.github/workflows/org-validation.yml`. Triggered via Actions → Run Workflow. Requires the `SFDX_AUTH_URL` secret to be configured in repo settings.

PR-level validation (structural only, no org) continues to run automatically via `.github/workflows/validate.yml`.

---

## What this doesn't catch (acknowledged gaps)

- **LLM reasoning quality** — the agents' Plan sections get followed by an AI. These harnesses don't evaluate whether the AI's output actually solves the user's problem, only whether the structure is correct. That's what `evals/golden/` is for (eval harness described in `skills/agentforce/agentforce-eval-harness`).
- **Managed-package content** — skills referencing managed-package fields (`HIFS__`, `npsp__`, etc.) can't be verified in an org where those packages aren't installed.
- **Behavioral drift between releases** — a Spring release may change a governor limit number. Factuality checks catch field-name drift; they don't catch limit-number drift. Currency monitor handles that separately.
- **Cross-agent interactions** — if two agents are recommended to run in sequence, these harnesses don't test the handoff. Each agent is smoke-tested in isolation.

---

## See also

- `skills/admin/salesforce-object-queryability` — the failure-mode taxonomy these reports use
- `agents/_shared/probes/README.md` — how probe recipes are structured
- `docs/installing-single-agents.md` — how consumers install agents (Wave 8)
- `docs/multi-ai-parity.md` — the parity contract that validation enforces
