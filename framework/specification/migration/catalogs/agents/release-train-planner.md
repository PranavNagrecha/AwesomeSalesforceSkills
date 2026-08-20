# V2 Migration Profile: `release-train-planner`

## Current source

- Path: `agents/release-train-planner/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `False`
- Modes: `design, audit`

## Current purpose

Plans a Salesforce release train: branch model, package strategy (unlocked vs 2GP-managed vs metadata-only), environment promotion path, CI/CD gates, release calendar with Salesforce Platform releases factored in, and feature-flag strategy for hotfixes. Alternately audits an existing release process and flags environment drift, missing gates, and risky hotfix paths.

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
| `mode` | yes | `design` \| `audit` |
| `team_size` | yes | `12 devs + 4 QA` |
| `cadence` | yes | `weekly`, `biweekly`, `monthly`, `quarterly` |
| `package_strategy` | no | `unlocked` \| `2gp-managed` \| `org-dependent` \| `metadata-only` |
| `customer_count` | no | `1` (internal) \| `N` (ISV-like) |
| `regions` | no | `["NA","EMEA","APAC"]` — for rollout staging |

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

## Current non-goals excerpt

- Does not cut branches, tag releases, or deploy packages.
- Does not run CI pipelines.
- Does not set up Salesforce DevOps Center / CI/CD tooling (produces a plan; operator implements).
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
