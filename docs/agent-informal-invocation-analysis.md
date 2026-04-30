# Agent library — full usage feedback & per-agent analysis

**Audience:** Anyone routing work to `AwesomeSalesforceSkills/agents/`: you in Cursor, other LLMs, or thin wrappers (MCP, slash commands, CI). Includes the informal pattern you described (`@agents/<name>/` + short intent) **and** every other practical way these agents are meant to be used.

**Scope:** One consolidated feedback doc: **(1)** all usage modes and consumption patterns, **(2)** how informal chat differs from the authored happy path, **(3)** per-agent analysis (alphabetical), **(4)** a **local structural QA** pass (`validate_repo.py --agents`, no org) with per-agent PASS lines and an explicit list of what was *not* executed (org probes, LLM runs). This is **not** a full Layer 1–3 validation sign-off — see `docs/validation/README.md` for org-backed QA.

**Related library docs:** [`docs/installing-single-agents.md`](installing-single-agents.md) (MCP vs bundle export), [`docs/consumer-responsibilities.md`](consumer-responsibilities.md) (persist reports, JSON envelope, no silent dimension drops), [`docs/MIGRATION.md`](MIGRATION.md) (routers vs deprecated folders).

**Repo reality:** Runtime agents assume **bounded invocations** (domain flags, modes, file paths). Quality tracks whether the workspace has `force-app/`, probes under `agents/_shared/probes/`, and whether the consumer honors the deliverable contract (disk + envelope).

---

## Usage modes — all the ways to use these agents (full catalog)

These are **orthogonal** to “which agent”: the same agent can be invoked through multiple channels. Pick the channel that matches how much structure you already have.

### 1. Informal Cursor / Composer chat (folder @-mention)

- **Pattern:** `@AwesomeSalesforceSkills/agents/<id>/` (or `@AGENT.md`) plus natural language (“build a flow”, “analyze this field”, “diff two users”).
- **Strengths:** Fastest mental loop; works well for **repo-grounded** agents (`code-reviewer`, `security-scanner`, `soql-optimizer`, scaffolds) when paths are obvious.
- **Risks:** Wrong agent family (e.g. **skill builder** vs **runtime builder**), missing **modes** (`design` vs `audit`), missing **`--domain`** for `audit-router`, or **hallucinated org inventory** when nothing is pasted and MCP is not used.
- **Mitigation:** Name artifacts (`Object.Field`, Flow API name, file glob, two User Ids) in the same message; ask the model to confirm **class** (`build` vs `runtime`) before generating.

### 2. Authored happy path inside each `AGENT.md`

- **Pattern:** Copy the invocation section from the agent folder (flags, scopes, examples).
- **Strengths:** Highest fidelity to the harness the author expected; reduces parameter drift.
- **Best for:** Routers (`audit-router`, `automation-migration-router`), multi-mode designers, anything with **`REFUSAL_CODES`** or strict output envelopes.

### 3. Slash commands / IDE command wrappers

- **Pattern:** Commands shipped with bundle export (see `installing-single-agents.md`: `.cursor/commands/…`, `.claude/commands/…`, etc.) or your own wrapper that pastes a frozen prompt + paths.
- **Strengths:** Repeatable; can bake in **default_output_dir** and report naming; good for teams.
- **Best for:** `user-access-diff`-style flows, repeated audits, “same command, different org alias” workflows.

### 4. Queue + orchestrator (`MASTER_QUEUE.md`)

- **Pattern:** `agents/orchestrator/AGENT.md` drives **skill-building** and maintenance rows (RESEARCH → builders → `validator`), not ad-hoc “fix my Flow in org X.”
- **Strengths:** Clear ownership and status; scales library maintenance.
- **Best for:** `*-skill-builder`, `content-researcher`, `task-mapper`, `currency-monitor`, `validator`.
- **Do not force-fit:** A vague “build a flow” ticket usually belongs on **`flow-builder`** directly, not the orchestrator, unless you encoded that work as a queue task.

### 5. MCP server (`get_agent`, full library)

- **Pattern:** SfSkills MCP serves agents + dependency graph; client never hand-copies `AGENT.md` alone (avoids missing probes/skills — see `installing-single-agents.md`).
- **Strengths:** Stays current with repo; best **live-org** companion when the server integrates with `sf` / org reads.
- **Best for:** Org-grounded runtime agents when you want grounded queries without copying bundles.

### 6. Bundle export (drop-in consumer project)

- **Pattern:** `scripts/export_agent_bundle.py --agent <id> --rewrite-paths --out …` then copy into another repo.
- **Strengths:** Air-gapped or customer projects get **probes + skills + shared contracts** together; slash commands can ship beside the agent.
- **Best for:** Shipping **one** agent to a delivery team (`user-access-diff`, `audit-router`, `security-scanner`) without vendoring the whole monorepo.

### 7. PR and branch review (git-native)

- **Pattern:** Paste PR description + `@` changed paths; use **`release-planner`** for notes/risk, **`code-reviewer`** / **`security-scanner`** / **`soql-optimizer`** on touched `force-app/` trees.
- **Strengths:** No org required for static agents; fits “review this branch” culture.
- **Pair with:** `deployment-risk-scorer` only when you can supply **target-org truth** (MCP or manifest comparison honestly scoped).

### 8. Local “quality gate” before push (developer habit)

- **Pattern:** Before `git push`, run mental checklist via **`security-scanner`**, **`soql-optimizer`**, **`lwc-auditor`** on what you touched.
- **Strengths:** Cheap; reduces noisy PR comments.
- **Limitation:** Not a substitute for CI compilation/tests — this doc is not QA.

### 9. Multi-agent pipelines (choreographed sequences)

- **Pattern:** Chain outputs: e.g. **`content-researcher`** → **`admin-skill-builder`** / **`dev-skill-builder`** → **`validator`**; **`object-designer`** → **`data-model-reviewer`**; **`field-impact-analyzer`** → **`flow-analyzer`** / **`apex-refactorer`**; **`audit-router`** (inventory) → **`automation-migration-router`** (`analyze`/`plan` only).
- **Strengths:** Each step has narrower inputs; later steps cite earlier deliverables on disk (`docs/reports/...`).
- **Risk:** Skipping **persist + envelope** between steps breaks machine follow-on — see `consumer-responsibilities.md`.

### 10. Advisory, pre-sales, and architecture desk work (little or no org)

- **Pattern:** **`org-assessor`**, **`waf-assessor`**, **`sandbox-strategy-designer`**, **`release-train-planner`**, **`bulk-migration-planner`** with narratives, diagrams, and NFRs pasted into chat.
- **Strengths:** Good slide-deck and decision-log fodder.
- **Risk:** Scores read as authoritative when they are **opinion + evidence-light** — label outputs as desk-level unless evidence is attached.

### 11. Delivery and change readiness (promotion planning)

- **Pattern:** **`changeset-builder`** / manifest lists; **`data-loader-pre-flight`** before loads; **`custom-metadata-and-settings-designer`** for config promotion strategy.
- **Strengths:** Turns vague “we’re deploying Friday” into checklists and dependency ordering reminders.
- **Risk:** Dependency graphs and “what breaks in prod” still need human + tooling verification.

### 12. Incident, load, and data-governance moments

- **Pattern:** **`data-loader-pre-flight`**, **`duplicate-rule-designer`**, **`deployment-risk-scorer`** (with honest scoping), **`entitlement-and-milestone-designer`** when SLAs misfire.
- **Strengths:** Framed as “go/no-go + questions,” not magic answers.

### 13. Training, onboarding, and rubric teaching

- **Pattern:** Use an agent’s `AGENT.md` + linked **skills** as a **reading syllabus** (“study `audit-router` + `audit_harness` classifier for X”).
- **Strengths:** Grounds juniors in library conventions (`AGENT_CONTRACT`, probes, refusal codes).
- **Not:** Automated grading — still human-led.

### 14. Cursor subagents / delegated tasks (or any router-LLM)

- **Pattern:** Parent session passes **agent id**, **mode**, **paths**, and **stop conditions**; child loads only that `AGENT.md` + dependencies.
- **Strengths:** Context isolation; can parallelize **`code-reviewer`** vs **`lwc-auditor`** on different paths.
- **Risk:** Child ignores **consumer-responsibilities** unless the parent system prompt enforces write-to-disk + envelope.

### 15. Deprecated folders as **routing hints** only

- **Pattern:** User @-mentions `validation-rule-auditor` etc.; correct behavior is to **redirect** to **`audit-router`** with the right `--domain` (or **`automation-migration-router`** + `source_type`).
- **Strengths:** Old names still discoverable in muscle memory.
- **See:** Per-agent deprecated sections below.

---

## How informal @folder use relates to the happy path

- **Happy path:** Slash commands, queue rows in `MASTER_QUEUE.md`, and the invocation blocks inside each `AGENT.md` (plus MCP/bundle when consuming outside this repo).
- **Informal path:** Folder @-mention + short natural language → higher risk of **wrong agent** (skill builder vs runtime builder) unless the prompt names **artifacts** or **outcomes**.
- **Consolidation:** Prefer **`audit-router`** for retired auditors and **`automation-migration-router`** for retired migrators — see `docs/MIGRATION.md`.

---

## QA — methodology & full pass results (local, no org)

**When:** 2026-04-19  
**Command:** `python3 scripts/validate_repo.py --agents` from `AwesomeSalesforceSkills/` (agents only; no skills validation, no Salesforce CLI auth, no metadata deploy).  
**Outcome:** **0 ERROR**, **0 WARN** across **75** discovered `agents/*/AGENT.md` files.

**What this gate proves:** Frontmatter validates against `agents/_shared/schemas/agent-frontmatter.schema.json`; required sections exist in canonical order (full runtime contract, lighter `class: build` contract, or minimum stub for `status: deprecated`); backticked citations resolve under `skills/`, `templates/`, `standards/`, `agents/_shared/probes/`, and peer `agents/<id>/` folders; optional `inputs.schema.json` parses and meets shape rules; `harness: designer_base` constraints apply where declared; every non-deprecated `class: runtime` agent is wrapped by at least one `commands/*.md` referencing its `AGENT.md`; MCP agent roster in `mcp/sfskills-mcp/src/sfskills_mcp/agents.py` is consistent with on-disk folders.

**What this gate does not prove:** Probe SOQL executes successfully in a live org; IDE slash-command wiring; LLM adherence to Plan / Output Contract / refusal codes; golden eval quality; or consumer tools writing `docs/reports/<agent>/<run_id>.{md,json}` per `docs/consumer-responsibilities.md`. Those require **Layer 1–3** runs in `docs/validation/README.md` (org-connected scripts and/or model harnesses).

**Artifacts:** No dated `docs/validation/agent_smoke_*` or `probe_report_*` files were created for this pass (per request to avoid leaving test-run outputs).

---

## Per-agent analysis (alphabetical by `id`)

### `agents/admin-skill-builder/`

**Status:** STABLE  
**Title:** Admin Skill Builder Agent  

**Declared intent (trimmed from `AGENT.md`):** Builds skills for the **Admin** and **BA** roles across any Salesforce cloud. Specializes in declarative configuration, process automation selection, UI layout, security configuration, data management, and business analysis artifacts. Consumes a Content Researcher brief before writing. Hands off to the Validator when done. **Scope:** Admin and BA role skills  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Writes **skills** (markdown packages) for Admin/BA domains — not runtime org work.
- Informal ‘@folder fix permissions’ will misfire: this agent expects **queue rows** or `/new-skill` style intent plus a **Content Researcher** brief.
- Best vague prompt: name the **skill path** or backlog row, and whether the audience is admin vs BA.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/agentforce-action-reviewer/`

**Status:** STABLE  
**Title:** Agentforce Action Reviewer Agent  

**Declared intent (trimmed from `AGENT.md`):** Reviews an Agentforce agent (Topics + Actions + Persona + Guardrails) against best-practice. Checks that every Action has a clear input/output contract, a documented side-effect surface, a test, a grounding citation, and that the surrounding Topic has appropriate example utterances. Produces a per-action scorecard + a rollup on Topic coherence + a guardrails  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Needs **exported** agent definitions + Apex + tests for grounded scoring; org-connected reads are ideal.
- Vague ‘review Agentforce’ without artifacts → generic rubric checklist — still useful but not evidence-based.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/agentforce-builder/`

**Status:** STABLE  
**Title:** Agentforce Builder Agent  

**Declared intent (trimmed from `AGENT.md`):** Takes a requirements statement — what the agent action should do, for whom, on which object — and scaffolds a complete Agentforce action: the `@InvocableMethod` Apex class using `templates/agentforce/AgentActionSkeleton.cls`, the matching topic YAML using `templates/agentforce/AgentTopic_Template.md`, a JSON agent definition derived from `templates/agentforc  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=False`.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Emits **scaffolds** (Invocable Apex + topic YAML + JSON + eval stub) — aligns well with vague ‘Agentforce action’ prompts if object + user story exist.
- Low risk without org because it does not claim deployed state.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/apex-builder/`

**Status:** STABLE  
**Title:** Apex Builder Agent  

**Declared intent (trimmed from `AGENT.md`):** Produces Apex scaffolds for every canonical Apex surface: trigger + handler, service class, selector, domain class, controller (Aura / LWC / VF), batch, queueable, schedulable, invocable, REST resource, SOAP web service, platform-event subscriber, change-data-capture subscriber, custom iterator, async-continuation, and the matching test class. Each scaffold   

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=False`.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Broad scaffold catalog; vague prompts often pick the **wrong Apex surface** (batch vs queueable vs service).
- Minimum viable intent: **one** surface type + inputs/outputs + where files should land in `force-app/`.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/apex-refactorer/`

**Status:** STABLE  
**Title:** Apex Refactorer Agent  

**Declared intent (trimmed from `AGENT.md`):** Takes an existing Apex class the user points at, compares it against the canonical patterns in `templates/apex/`, and returns a refactored version plus a test class. Targets: trigger bodies lifted into `TriggerHandler`, raw DML lifted to `BaseService`, raw SOQL lifted to `BaseSelector`, ad-hoc `HttpCallout` lifted to `HttpClient`, `System.debug` calls replac  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=False`.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Requires a **concrete class path** in workspace; excellent Cursor fit when @-mentioning the class file too.
- Without templates under `templates/apex/` in context, pattern alignment weakens.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/approval-process-auditor/`

**Status:** DEPRECATED  
**Title:** Approval Process Auditor — DEPRECATED (Wave 3b-1)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=approval_process`.  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/approval-to-flow-orchestrator-migrator/`

**Status:** DEPRECATED  
**Title:** Approval Process → Flow Orchestrator Migrator — DEPRECATED (Wave 3a)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`automation-migration-router`](../automation-migration-router/AGENT.md) with `--source-type=approval_process`.  

- **Replacement:** Use `automation-migration-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/architect-skill-builder/`

**Status:** STABLE  
**Title:** Architect Skill Builder Agent  

**Declared intent (trimmed from `AGENT.md`):** Builds skills for the **Architect** role across any Salesforce cloud. Specializes in solution design patterns, platform selection guidance, scalability planning, multi-org strategy, technical debt assessment, WAF reviews, and cross-cloud architecture. Consumes a Content Researcher brief. Hands off to Validator when done. **Scope:** Architect role skills only  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Same harness as admin builder but for **architect** skills under `skills/architect/`.
- Vague ‘architecture’ prompts are dangerously broad — narrow to **one pattern** (multi-org, integration style, scalability lever).
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/assignment-and-auto-response-rules-designer/`

**Status:** STABLE  
**Title:** Assignment & Auto-Response Rules Designer Agent  

**Declared intent (trimmed from `AGENT.md`):** Two modes: - **`design` mode** — given a routing scenario on Lead or Case (by source, geography, product, tier, language, or custom predicate), produces the Assignment Rule + Auto-Response Rule configuration that routes incoming records to the right queue / owner and sends the right templated response. Output is a rule-entry table, the queue / group design,   

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- `design` works from narrative routing rules; `audit` needs org truth for queues and active rules.
- Ambiguity hotspot: **Lead vs Case**, and whether Omni-Channel overlaps routing — say which channel.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/audit-router/`

**Status:** STABLE  
**Title:** Audit Router Agent  

**Declared intent (trimmed from `AGENT.md`):** Dispatches one of the audit domains in the [`audit_harness`](../_shared/harnesses/audit_harness/README.md) into its domain-specific classifier, returning a uniform output envelope: inventory + findings (P0/P1/P2 with domain-scoped codes) + optional mechanical patches + Process Observations + citations. Replaces 15 single-mode auditor agents whose logic was 8  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Central audit entry: must supply **`--domain`** (or spell domain in prose) + scope.
- Informal ‘audit my org’ is too wide — model should refuse bounded scope or ask which **audit_harness** domain.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/automation-migration-router/`

**Status:** STABLE  
**Title:** Automation Migration Router Agent  

**Declared intent (trimmed from `AGENT.md`):** Dispatches one of four source automation types (`wf_rule`, `process_builder`, `approval_process`, or `auto`) into the matching migration path, returning an inventory, a target design (Flow or Orchestrator), a parallel-run validation plan, and a rollback. Replaces the four retired migrator agents — `workflow-rule-to-flow-migrator`, `process-builder-to-flow-mi  

- **Contract snapshot:** `class=runtime`, `modes=['analyze', 'plan', 'migrate']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Needs **source_type** (`wf_rule`, `process_builder`, `approval_process`, `auto`) and object/process scope.
- Even if you never **migrate**, `analyze`/`plan` modes are valuable with exports or describe output.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/bulk-migration-planner/`

**Status:** STABLE  
**Title:** Bulk Migration Planner Agent  

**Declared intent (trimmed from `AGENT.md`):** Takes a data-integration requirement — volume, latency, source system, direction, consistency needs — and produces a concrete implementation plan selecting the right pattern via `standards/decision-trees/integration-pattern-selection.md`: Bulk API 2.0, Platform Events, Pub/Sub API, REST Composite, Salesforce Connect, or an inbound Apex REST endpoint. The out  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=False`.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Integration/data-move **pattern selection** at architecture depth — good for ‘large volume sync’ vagueness if you add source + latency.
- Output is planning narrative, not runnable ETL.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/business-hours-and-holidays-configurator/`

**Status:** STABLE  
**Title:** Business Hours & Holidays Configurator Agent  

**Declared intent (trimmed from `AGENT.md`):** Designs and audits the Business Hours and Holidays configuration that every time-sensitive Salesforce feature keys off: Entitlement Processes + Milestones, Escalation Rules, Omni-Channel presence, Case business-hours math (`BusinessHours.diff`, `BusinessHours.add`), Email Routing Hours on email-to-case channels, and Approval Process "N days" constructs. Outp  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Cross-cuts SLAs, escalations, Omni — excellent when symptoms are ‘wrong business time math’.
- Needs **timezone + holiday calendar** facts; model will invent holidays if you do not supply jurisdiction.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/case-escalation-auditor/`

**Status:** DEPRECATED  
**Title:** Case Escalation Auditor — DEPRECATED (Wave 3b-2)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=case_escalation`. The full rule set (missing assignment defaults, black-hole queues, expired entitlements, milestone violation rates, business-hour overlap, stale escalation targets) is preserved verbatim in [`classifiers/case_escalation.md`](../_shared/harnesses/audit_harness/classifiers/  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/changeset-builder/`

**Status:** STABLE  
**Title:** Change Set Builder Agent  

**Declared intent (trimmed from `AGENT.md`):** Two modes: - **`build` mode** — given a feature description or a list of artifact names, produces a complete, dependency-ordered Change Set manifest for deployment from a sandbox (source org) to a target org. Output is a component list, a dependency graph, a deployment order, a destructive-changes list if applicable, and the post-deploy activation checklist.  

- **Contract snapshot:** `class=runtime`, `modes=['build', 'validate']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- `build` can run from **feature description + repo paths**; `validate` expects manifest against org.
- Weak spot: transitive metadata dependencies — model should enumerate **unknown unknowns** explicitly.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/code-reviewer/`

**Status:** STABLE  
**Title:** Code Reviewer Agent  

**Declared intent (trimmed from `AGENT.md`):** Reviews Apex classes, triggers, LWC components, and Flows against this library's skills and the Salesforce Well-Architected Framework. Produces prioritised findings with remediation code.  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Best vague-intent agent for ‘review my Salesforce code’ **when** `@force-app` paths are implied or attached.
- Explicitly ties to library skills + WAF — good discipline for LLM tone.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/content-researcher/`

**Status:** STABLE  
**Title:** Content Researcher Agent  

**Declared intent (trimmed from `AGENT.md`):** Deep-researches a specific Salesforce skill topic across all 4 source tiers before any skill builder writes a single word. Produces a structured research brief that grounds every factual claim, surfaces contradictions, and identifies gotchas. Skill builders consume this brief — they do not do their own research. **Scope:** One skill topic per invocation. Out  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Upstream **research brief** for all skill builders — strongest when you give **one topic** + target skill path.
- Informal ‘research Salesforce’ needs boundaries (release, product area, doc tier) or the model freelances.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/csv-to-object-mapper/`

**Status:** STABLE  
**Title:** CSV to Object Mapper Agent  

**Declared intent (trimmed from `AGENT.md`):** Given a CSV file header (or a schema description), produces a mapping to an existing or new sObject: column → field decisions with type inference, naming per `templates/admin/naming-conventions.md`, External ID candidate identification, required-field detection, and a Data Loader CSV mapping file. The agent handles the specific case a Salesforce admin or BA   

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=False`.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Paste **header line** → strong mapping; one of the tightest input-output agents.
- Weak if CSV is wide and dirty types — ask for sample rows.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/currency-monitor/`

**Status:** STABLE  
**Title:** Currency Monitor Agent  

**Declared intent (trimmed from `AGENT.md`):** Watches Salesforce release notes (3 major releases per year: Spring, Summer, Winter) and flags skills whose content may be stale. For each flagged skill, inserts an UPDATE TODO row into `MASTER_QUEUE.md` so the relevant skill builder can review and refresh it. Does NOT update skill content — only flags. **Scope:** Repo-wide scan against one release. Output i  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Maintenance agent tied to **release cadence** and `MASTER_QUEUE.md` hygiene.
- Rarely the right @-mention for interactive ‘help me now’ work unless you are explicitly doing **stale-skill sweeps**.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/custom-metadata-and-settings-designer/`

**Status:** STABLE  
**Title:** Custom Metadata & Custom Settings Designer Agent  

**Declared intent (trimmed from `AGENT.md`):** Two modes: - **`design` mode** — given a configuration scenario (feature flag, environment-specific config, business rule table, API endpoint registry, tax rate table, etc.), produces the correct artifact design: Custom Metadata Type vs List Custom Setting vs Hierarchy Custom Setting, with fields, protection, usage pattern in Apex / Flow / Formula, default r  

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Chooses CMDT vs hierarchy custom settings vs list custom settings — needs **mutability** and **environment dimension**.
- Audit mode needs metadata visibility.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/data-loader-pre-flight/`

**Status:** STABLE  
**Title:** Data Loader Pre-Flight Agent  

**Declared intent (trimmed from `AGENT.md`):** Given a planned data load — sObject, volume, source CSV or mapping, intent (insert / upsert / update / delete) — produces a go/no-go checklist covering every org-side concern that will turn a load into an incident: active automation on the object, validation rules without bypass, sharing recalculation cost at the target volume, duplicate rule interactions, r  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Incident-prevention checklist — great vague fit for ‘we are loading data’ if you name object + operation.
- Cannot certify safety without org settings (validation rules, triggers, dupe rules) — user must paste or allow read.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/data-model-reviewer/`

**Status:** STABLE  
**Title:** Data Model Reviewer Agent  

**Declared intent (trimmed from `AGENT.md`):** Reviews the data model of a target domain (a parent object + its descendants, or a list of related objects): relationship patterns (Lookup vs Master-Detail), cross-object rollups, External ID strategy, junction objects, data-growth forecast, and candidate indexes. Produces a health report scored against `skills/data/data-model-design-patterns`, `skills/data/  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Needs object list or ‘domain’ boundary; otherwise review becomes generic ER advice.
- Better when paired with **ERD** or `object-designer` output.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/data-skill-builder/`

**Status:** STABLE  
**Title:** Data Skill Builder Agent  

**Declared intent (trimmed from `AGENT.md`):** Builds skills for the **Data** role across any Salesforce cloud. Specializes in data modeling, SOQL/SOSL, data migration, Bulk API, data quality, archival, and analytics data patterns. Consumes a Content Researcher brief before writing. Hands off to Validator when done. **Scope:** Data role skills only. Domain: `data`. Dev/Admin/Architect go to their agents.  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Produces **data-role** skills (SOQL, migration, quality) — not hands-on DML or loads.
- Pair with `content-researcher` output; otherwise expect generic skill text.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/deployment-risk-scorer/`

**Status:** STABLE  
**Title:** Deployment Risk Scorer Agent  

**Declared intent (trimmed from `AGENT.md`):** Before a user deploys a change set / package / SFDX delta, this agent compares what's about to land against the live target org (via MCP) and returns a risk score with a breaking-change list: deleted fields still referenced, validation rule changes, required-field additions on populated tables, picklist value removals in use, API version downgrades, and prof  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Authoring assumes **diff vs live target**; if org reads are off-limits, reframe as **manifest-based risk** only.
- High hallucination risk if model pretends to know what is deployed.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/dev-skill-builder/`

**Status:** STABLE  
**Title:** Dev Skill Builder Agent  

**Declared intent (trimmed from `AGENT.md`):** Builds skills for the **Dev** role across any Salesforce cloud. Specializes in Apex, LWC, Flow (developer patterns), Metadata API, SFDX, integrations, and programmatic customization. Consumes a Content Researcher brief before writing. Hands off to Validator when done. **Scope:** Dev role skills only. Covers domains: `apex`, `lwc`, `flow`, `integration`, `dev  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Produces **dev-role** skills (Apex/LWC/Flow developer patterns, tooling).
- Do not confuse with `apex-builder` / `lwc-builder` (those emit **code scaffolds**, not skill library pages).
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/devops-skill-builder/`

**Status:** STABLE  
**Title:** DevOps Skill Builder Agent  

**Declared intent (trimmed from `AGENT.md`):** Builds skills for the **DevOps / Release Engineering** role across any Salesforce cloud. Specializes in source control strategy, branching models, CI/CD pipelines, sandbox orchestration, deployment tooling (SFDX, Metadata API, Change Sets, DX projects, Unlocked Packages, 2GP), environment management, release management, automated testing gates, and observabi  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Produces **DevOps/release** skills — branching, CI, packaging strategy as documentation.
- Good fit when you say ‘how should we release’ **without** needing `deployment-risk-scorer` diff-vs-org truth.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/duplicate-rule-designer/`

**Status:** STABLE  
**Title:** Duplicate Rule Designer Agent  

**Declared intent (trimmed from `AGENT.md`):** Given an sObject (typically Lead, Contact, Account, or a custom object with human-identity data), designs the **Matching Rule + Duplicate Rule** pair that enforces the org's dedup policy: which fields to match, with what fuzzy-vs-exact logic, what action to take on user-created vs API-created duplicates, which profiles/PSes are exempt, and how the rule inter  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Needs dedup **policy** (fuzzy vs exact, block vs alert) and key fields; good for Lead/Contact/Account stories.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/email-template-modernizer/`

**Status:** STABLE  
**Title:** Email Template Modernizer Agent  

**Declared intent (trimmed from `AGENT.md`):** Audits email templates (Classic HTML, Visualforce, Lightning) in the target org, identifies deprecation risk (Classic HTML + Visualforce are on the long-term decline), merge-field breakage, and brand/accessibility drift. Produces a modernization plan: which templates to migrate to Lightning Email Templates, which to retire, and which to keep as-is, plus per-  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Needs template bodies or org access; otherwise modernization advice is generic.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/entitlement-and-milestone-designer/`

**Status:** STABLE  
**Title:** Entitlement & Milestone Designer Agent  

**Declared intent (trimmed from `AGENT.md`):** Two modes: - **`design` mode** — given a Service-Cloud SLA description (contract terms, response time, resolution time, business-hours coverage, entitlement-to-account relationships, case-to-entitlement resolution logic), produces the full Entitlement Management design: Entitlement Processes, Milestones (with time trigger formulas), Success / Warning / Viola  

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- SLA math + business hours coupling — say **service contract vs account** model early.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/experience-cloud-admin-designer/`

**Status:** STABLE  
**Title:** Experience Cloud Admin Designer Agent  

**Declared intent (trimmed from `AGENT.md`):** Two modes: - **`design` mode** — given an Experience Cloud scenario (customer portal, partner community, help center, B2B store front, guest microsite), produces the full admin setup plan: site template choice, audience model, member license type, profile + PSG composition per audience, sharing set vs criteria-based sharing set vs share group decisions, gues  

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Huge surface (sites, audiences, auth) — vague prompts should trigger **scoping questions**, not a full blueprint in one shot.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/field-audit-trail-and-history-tracking-governor/`

**Status:** DEPRECATED  
**Title:** Field Audit Trail & History Tracking Governor — DEPRECATED (Wave 3b-2)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=field_audit_trail_history_tracking`. The full rule set (regulatory-floor coverage, 20-field saturation, dead tracks, formula/roll-up/auto-number tracked anti-patterns, non-Shield regulated-profile warning, retention-policy gaps on Shield orgs, archival-pipeline stale detection) is preserve  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/field-impact-analyzer/`

**Status:** STABLE  
**Title:** Field Impact Analyzer Agent  

**Declared intent (trimmed from `AGENT.md`):** Given a field on an sObject, produces a blast-radius report: every Apex class, trigger, Flow, LWC, report, dashboard, formula, validation rule, workflow field update, approval process, email template, record type, page layout, permission set, and integration endpoint that references the field, together with a classification of each reference (read / write /   

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Your ‘analyze a field’ poster child: still needs **Object.Field** + repo (or dependency report).
- Without repo search, Flow/Apex references in org-only metadata will be missed unless exported.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/flow-analyzer/`

**Status:** STABLE  
**Title:** Flow Analyzer Agent  

**Declared intent (trimmed from `AGENT.md`):** For a given Flow or sObject, decides whether the automation is in the right tool per `standards/decision-trees/automation-selection.md` (Flow vs Apex vs Agentforce), reviews existing Flow definitions for bulkification and fault-path compliance against `skills/flow/flow-bulkification/SKILL.md` and `templates/flow/FaultPath_Template.md`, and flags co-existing   

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Needs Flow **file** or pasted XML; ‘analyze flows’ without path → ask for glob under `force-app/main/default/flows/`.
- Good for tool-choice + bulkification narrative vs `flow-builder` which designs forward.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/flow-builder/`

**Status:** STABLE  
**Title:** Flow Builder Agent  

**Declared intent (trimmed from `AGENT.md`):** Given a business requirement, designs the correct Flow: Flow type (record-triggered / scheduled / auto-launched / screen / orchestration), trigger configuration, element-by-element plan, fault path, subflow decomposition, bulkification safeguards, and a test design. Output is a design document + optional Flow XML skeleton the user drops into Flow Builder. **  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Your ‘build a flow’ poster child: works from prose but benefits enormously from **trigger type** + **CRUD context**.
- Risk: invented API names for elements — tie to naming templates and object fields explicitly.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/flow-orchestrator-designer/`

**Status:** STABLE  
**Title:** Flow Orchestrator Designer Agent  

**Declared intent (trimmed from `AGENT.md`):** Two modes: - **`design` mode** — given a multi-step human-or-mixed workflow (e.g. "3-stage contract review with legal, procurement, and customer sign-off"), produces a Flow Orchestrator design: stages, steps, work-item assignees, interactive vs background step mix, transition criteria, restart/recall behavior, and the subflows each step invokes. - **`audit`   

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Multi-human workflows — vague ‘orchestration’ prompts confuse with **record-triggered Flow**; clarify human steps vs system automation.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/integration-catalog-builder/`

**Status:** STABLE  
**Title:** Integration Catalog Builder Agent  

**Declared intent (trimmed from `AGENT.md`):** Builds a catalog of every live integration endpoint reachable from the org: Named Credentials, Remote Site Settings, Connected Apps, Auth Providers, and the certificates/keys backing them. Cross-references which integration user / PSG owns each, what Apex/Flow artifacts reference them, and scores each endpoint on age, posture (OAuth flow, token scope), rotat  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Inventory agent — without Named Credential / Remote Site exports you get a **methodology** not a catalog.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/knowledge-article-taxonomy-agent/`

**Status:** STABLE  
**Title:** Knowledge Article Taxonomy Agent  

**Declared intent (trimmed from `AGENT.md`):** Designs or audits the taxonomy behind a Salesforce Knowledge implementation — data categories, article types / record types, channel-level visibility (Internal App, Customer, Partner, Public Knowledge Base, Pardot, Einstein search), language coverage, and authoring lifecycle. The agent also decides, per body of content, whether it belongs in Knowledge vs an   

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Taxonomy + channel visibility — needs audience (internal vs partner vs public) or design will overfit.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/lead-routing-rules-designer/`

**Status:** STABLE  
**Title:** Lead Routing Rules Designer Agent  

**Declared intent (trimmed from `AGENT.md`):** Designs or audits lead routing: assignment rules, queue topology, territory assignment, round-robin distribution, SLA gates, and conversion-handoff to Opportunity/Contact/Account. Produces a routing map that ties each lead source + geography + product to an owner (queue or user) with failover, round-robin, and SLA. In audit mode, it scores existing assignmen  

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Overlaps mentally with assignment rules — clarify **territory vs queue vs assignment rules** which layer owns truth.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/lightning-record-page-auditor/`

**Status:** DEPRECATED  
**Title:** Lightning Record Page Auditor — DEPRECATED (Wave 3b-2)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=lightning_record_page`. The full rule set (Dynamic Forms adoption, component count, related-list strategy, Path element, visibility filters, mobile-form-factor, dead pages) is preserved verbatim in [`classifiers/lightning_record_page.md`](../_shared/harnesses/audit_harness/classifiers/ligh  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/list-view-and-search-layout-auditor/`

**Status:** DEPRECATED  
**Title:** List View & Search Layout Auditor — DEPRECATED (Wave 3b-2)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=list_view_search_layout`. The full rule set (deleted-field filters, sensitive-data leaks via All-Users sharing, zero-member groups, duplicate list views, lookup-dialog disambiguators, search-layout gaps, list view charts on deleted fields) is preserved verbatim in [`classifiers/list_view_s  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/lwc-auditor/`

**Status:** STABLE  
**Title:** LWC Auditor Agent  

**Declared intent (trimmed from `AGENT.md`):** Audits a Lightning Web Component bundle for accessibility, performance, security, and testing gaps. Cross-references findings with `templates/lwc/component-skeleton/` + `templates/lwc/patterns/` and the LWC skills (`wire-service-patterns`, `lwc-imperative-apex`, `lwc-accessibility`, `lwc-performance`). Produces a ranked findings list with paste-ready fixes.   

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- YAML marks `requires_org: true` but **bundle on disk** is usually enough — great for @folder + `force-app/.../lwc/`.
- Informal use: attach the component folder, mention a11y/perf focus if you care.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/lwc-builder/`

**Status:** STABLE  
**Title:** LWC Builder Agent  

**Declared intent (trimmed from `AGENT.md`):** Produces a full Lightning Web Component bundle for a described feature: `.js`, `.html`, `.css`, `.js-meta.xml`, `__tests__/*.test.js`, and — where the component binds to server data — the matching `@AuraEnabled(cacheable=true)` Apex controller class stub. Every bundle conforms to `templates/lwc/component-skeleton/`, uses `templates/lwc/patterns/` where one f  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=False`.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Scaffold generator; vague ‘LWC for X’ works if X includes **data source** (Apex vs wire) and **record context**.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/my-domain-and-session-security-auditor/`

**Status:** DEPRECATED  
**Title:** My Domain & Session Security Auditor — DEPRECATED (Wave 3b-2)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=my_domain_session_security`. The full rule set spanning My Domain (enhanced-domain deployment, legacy-hostname traffic, Experience Cloud site hosts, SSO IDP URLs), MFA (coverage, bypass grants, passkey readiness), session (timeout, re-auth, HTTPS, clickjack, browser-close, concurrent-sessi  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/object-designer/`

**Status:** STABLE  
**Title:** Object Designer Agent  

**Declared intent (trimmed from `AGENT.md`):** Given a business concept (a plain-English description like "we need to track maintenance contracts"), produces a Setup-ready object design: standard-vs-custom decision, API name, label, record types, canonical fields with types and naming, lookup/master-detail relationships, key validation rules, indexing plan, sharing posture, and the deployment order. The   

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Good early-phase vague prompt (‘model contracts’) — outputs standard vs custom decision and field shapes.
- Still need sharing intent (internal vs partner) to avoid wrong MD/Lookup defaults.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/omni-channel-routing-designer/`

**Status:** STABLE  
**Title:** Omni-Channel Routing Designer Agent  

**Declared intent (trimmed from `AGENT.md`):** Designs or audits an Omni-Channel routing configuration across Case, Chat/Messaging, and Lead. Produces queue topology, routing-config (push vs most-available vs skills-based vs external), capacity model per presence status, service channel mapping, and a bot-to-agent handoff plan. The agent either (a) greenfields a new Omni-Channel design from business inpu  

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Capacity + routing config — informal prompts often omit **channel types** (chat vs messaging vs case).
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/orchestrator/`

**Status:** STABLE  
**Title:** Orchestrator Agent  

**Declared intent (trimmed from `AGENT.md`):** Reads `MASTER_QUEUE.md`, finds the next actionable task, routes it to the correct specialized agent, tracks status, and commits progress. It does not build skills, write content, or do research. It is the single entry point for autonomous queue execution. **Scope:** One task per invocation. Routes → waits → updates status → commits → stops. ---  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Queue driver: reads `MASTER_QUEUE.md`, routes builders — **not** a substitute for `flow-builder` when you say ‘build a flow’.
- Informal use still requires pointing at **the queue row** or accepting the model will grep the queue blindly.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/org-assessor/`

**Status:** STABLE  
**Title:** Org Assessor Agent  

**Declared intent (trimmed from `AGENT.md`):** Assesses a Salesforce org or SFDX project against the Well-Architected Framework. Produces a scored report with a prioritised remediation roadmap.  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Desk-level WAF scoring — honest when framed as **repo + narrative** assessment, not live compliance attestation.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/org-drift-detector/`

**Status:** DEPRECATED  
**Title:** Org Drift Detector — DEPRECATED (Wave 3b-2)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=org_drift`. The full rule set (library-prescribed patterns probed against the org, gap / bloat / fork / orphan / stale-skill classification, security-gap P0 escalation, Named-Credential-vs-Remote-Site drift) is preserved verbatim in [`classifiers/org_drift.md`](../_shared/harnesses/audit_h  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/path-designer/`

**Status:** STABLE  
**Title:** Path Designer Agent  

**Declared intent (trimmed from `AGENT.md`):** Two modes: - **`design` mode** — given a stage / status picklist on a supported object (Opportunity, Lead, Case, Contract, Order, Custom Object with a compatible picklist), produces a Sales Path / Service Path / generic Path design: step-by-step Key Fields, Guidance for Success, celebration triggers, and a validation-rule harness that reinforces the picklist  

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Paths tie to **picklists** — need object + path type (Sales vs Service) + stage field API name.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/permission-set-architect/`

**Status:** STABLE  
**Title:** Permission Set Architect Agent  

**Declared intent (trimmed from `AGENT.md`):** Two modes, selectable via input: - **`design` mode** — given a persona description (job title, objects touched, features used, sensitivity), produces a Permission Set Group composition per `templates/admin/permission-set-patterns.md`: which Feature PSes to compose, which Object PSes, whether a Muting PS is needed, and the deployment order. - **`audit` mode**  

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- `design` from persona works; `audit` needs live assignments / PSG composition.
- Overlaps conceptually with `user-access-diff` — architect answers ‘what should be’, diff answers ‘what differs between two users’.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/picklist-governor/`

**Status:** DEPRECATED  
**Title:** Picklist Governor — DEPRECATED (Wave 3b-1)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=picklist`.  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/process-builder-to-flow-migrator/`

**Status:** DEPRECATED  
**Title:** Process Builder → Flow Migrator — DEPRECATED (Wave 3a)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`automation-migration-router`](../automation-migration-router/AGENT.md) with `--source-type=process_builder`.  

- **Replacement:** Use `automation-migration-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/profile-to-permset-migrator/`

**Status:** STABLE  
**Title:** Profile → Permission Set Migrator Agent  

**Declared intent (trimmed from `AGENT.md`):** Given one profile (or a set of profiles scoped by name filter) in the target org, decomposes the profile into a Permission Set + Permission Set Group layout that minimizes the profile to its mandatory residue (license assignment, default record type, default app, page layout assignments, login IP ranges, login hours, session settings) and moves every migrata  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Without profile XML export, output skews to **methodology** and hypothetical perm sets — still valuable.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/prompt-library-governor/`

**Status:** DEPRECATED  
**Title:** Prompt Library Governor — DEPRECATED (Wave 3b-2)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=prompt_library`. The full rule set (duplicate-cluster detection, grounding citation checks, Trust Layer masking for PII, data-residency vs model-choice, owner + version hygiene, stale templates, no-eval tests, model-choice documentation) is preserved verbatim in [`classifiers/prompt_librar  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/quick-action-and-global-action-auditor/`

**Status:** DEPRECATED  
**Title:** Quick Action & Global Action Auditor — DEPRECATED (Wave 3b-2)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=quick_action` for the audit mode. The `design` mode migrates separately to Wave 3c's `designer_base` harness (as `action-designer`). The audit rule set (deleted-field refs, deactivated Flows, orphan VF pages, deleted LWCs, invisible actions not surfaced on any layout, duplicate/standard-mi  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/record-type-and-layout-auditor/`

**Status:** DEPRECATED  
**Title:** Record Type & Layout Auditor — DEPRECATED (Wave 3b-1)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=record_type_layout`.  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/release-planner/`

**Status:** STABLE  
**Title:** Release Planner Agent  

**Declared intent (trimmed from `AGENT.md`):** Generates structured release notes and risk assessments from a git diff, component list, or sprint summary. Flags breaking changes, sharing model impacts, and governor limit risks.  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Git diff / component list in → release notes — excellent informal fit for ‘what shipped this sprint’.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/release-train-planner/`

**Status:** STABLE  
**Title:** Release Train Planner Agent  

**Declared intent (trimmed from `AGENT.md`):** Plans a Salesforce release train: branch model, package strategy (unlocked vs 2GP-managed vs metadata-only), environment promotion path, CI/CD gates, release calendar with Salesforce Platform releases factored in, and feature-flag strategy for hotfixes. Alternately audits an existing release process and flags environment drift, missing gates, and risky hotfi  

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=False`.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Program-level branching + packaging — needs team size, edition, and **1GP/2GP/unlocked** preference or advice stays generic.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/report-and-dashboard-auditor/`

**Status:** DEPRECATED  
**Title:** Report & Dashboard Auditor — DEPRECATED (Wave 3b-1)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=report_dashboard`.  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/reports-and-dashboards-folder-sharing-auditor/`

**Status:** DEPRECATED  
**Title:** Reports & Dashboards Folder Sharing Auditor — DEPRECATED (Wave 3b-2)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=reports_dashboards_folder_sharing`. Distinct from `report_dashboard` (which audits content quality); this classifier audits the sharing layer. The full rule set (Enhanced Folder Sharing enablement, inactive-group shares, manage-level over-privilege, All-Internal-Users + PII, running-user i  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/sales-stage-designer/`

**Status:** STABLE  
**Title:** Sales Stage Designer Agent  

**Declared intent (trimmed from `AGENT.md`):** Designs or audits the Opportunity sales process: stages, probabilities, forecast categories, required fields per stage, stage-gate validation, pipeline-review cadence, and Collaborative Forecasts rollups. Produces a stage ladder that a sales ops team can take to Setup (Sales Process, Opportunity stage picklist, Path, Forecasts) plus the backing validation ru  

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Forecast + stage gates — tie to **forecast type** (collaborative vs custom) if known.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/sandbox-strategy-designer/`

**Status:** STABLE  
**Title:** Sandbox Strategy Designer Agent  

**Declared intent (trimmed from `AGENT.md`):** Designs or audits the sandbox + scratch-org strategy for a Salesforce program: which sandbox types for which workstreams, refresh cadence, seeding strategy, scratch-org pools for feature branches, masking/anonymization for production data, and the handoff between scratch → Developer Pro → Partial → Full. Produces a concrete environment ladder with refresh ca  

- **Contract snapshot:** `class=runtime`, `modes=['design', 'audit']`, `requires_org=False`.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Strong for ‘how many sandboxes’ questions — low dependency on org reads.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/security-scanner/`

**Status:** STABLE  
**Title:** Security Scanner Agent  

**Declared intent (trimmed from `AGENT.md`):** Walks a `force-app/` tree and flags CRUD/FLS violations, sharing leaks, hardcoded secrets, missing `with sharing` declarations, and callouts that bypass Named Credentials. Cross-references every finding with the canonical fix in `templates/apex/SecurityUtils.cls` and the sharing decision tree. Returns a severity-ranked report with remediation code. **Scope:*  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Static `force-app/` scan — high signal for vague ‘security review’ when repo is present.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/security-skill-builder/`

**Status:** STABLE  
**Title:** Security Skill Builder Agent  

**Declared intent (trimmed from `AGENT.md`):** Builds skills for the **Security / Compliance / IAM** role across any Salesforce cloud. Specializes in identity and access (SSO, MFA, delegated authentication, JIT provisioning), sharing and visibility (OWD, role hierarchy, sharing rules, manual shares, territory sharing, restriction rules, scoping rules), permission architecture (Profiles, Permission Sets,   

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Produces **security/compliance** skills — IAM, Shield, monitoring — as authored guidance.
- Not a substitute for `security-scanner` on `force-app/` when you want concrete findings.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/sharing-audit-agent/`

**Status:** DEPRECATED  
**Title:** Sharing Audit Agent — DEPRECATED (Wave 3b-2)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=sharing`. The full rule set (data-skew hot owners, guest-user Modify-All-Data freeze, OWD vs data-class mismatch, Apex Managed Sharing where declarative would work, missing criteria-based rules, rule sprawl, flat role hierarchy, recalc-cost estimation, inactive-queue references) is preserv  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/soql-optimizer/`

**Status:** STABLE  
**Title:** SOQL Optimizer Agent  

**Declared intent (trimmed from `AGENT.md`):** Scans a user-specified scope (file, folder, or entire `force-app/`) for SOQL anti-patterns — queries inside loops, missing selective filters, SELECTing unused fields, filtering on non-indexed fields at high volume, missing `WITH SECURITY_ENFORCED` — and produces ranked fix recommendations with before/after code. Consults data-skew and LDV skills for high-vol  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Point at path or whole `force-app/` — good for vague ‘SOQL smells’ if scope is implied.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/task-mapper/`

**Status:** STABLE  
**Title:** Task Mapper Agent  

**Declared intent (trimmed from `AGENT.md`):** Maps the complete task universe for a given Salesforce Cloud × Role cell. Researches official Salesforce docs and Trailhead to identify every distinct practitioner task that role performs in that cloud. Compares against existing skills. Inserts confirmed-gap TODO rows into `MASTER_QUEUE.md`. Does NOT build skills — it only populates the queue. **Scope:** One  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Maps **role × cloud task universe** vs repo coverage — great for roadmaps, heavy for quick fixes.
- Needs explicit **Cloud × Role cell**; otherwise output is not actionable.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/test-class-generator/`

**Status:** STABLE  
**Title:** Test Class Generator Agent  

**Declared intent (trimmed from `AGENT.md`):** Generates a bulk-safe Apex test class for a target class, targeting ≥ 85% code coverage, using the canonical test factories in `templates/apex/tests/`. Produces positive, negative, bulk (200-record), and non-admin (`System.runAs`) scenarios by default. Stubs HTTP callouts via `MockHttpResponseGenerator` when the target makes callouts. Output is ready to past  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=False`.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Needs target class + factories in repo; watch for **assertion-light** tests that only chase coverage.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/trigger-consolidator/`

**Status:** STABLE  
**Title:** Trigger Consolidator Agent  

**Declared intent (trimmed from `AGENT.md`):** Finds every Apex trigger on a given sObject across the user's `force-app` tree, checks the target org (if connected) for additional triggers, and produces a consolidation plan that lifts them all into a single `<Object>TriggerHandler extends TriggerHandler` class using the canonical framework from `templates/apex/TriggerHandler.cls` + `templates/apex/Trigger  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=False`.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Needs object API name + triggers in repo (optional org for extra triggers) — good for ‘too many triggers on Case’ style prompts.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/user-access-diff/`

**Status:** STABLE  
**Title:** User Access Diff Agent  

**Declared intent (trimmed from `AGENT.md`):** Given two Users in the same org, produces a symmetric, dimension-by-dimension comparison of their effective access surface: profile, active Permission Set and Permission Set Group assignments (with PSG components flattened), object CRUD, field-level security (opt-in), system permissions (`ModifyAllData`, `ViewAllUsers`, `AuthorApex`, etc.), Apex class / VF p  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Needs **two User Ids** (or usernames) + ideally permission set exports; `_shared/probes/` structures the comparison.
- Do not confuse with `permission-set-architect` (design) vs this (delta between principals).
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/validation-rule-auditor/`

**Status:** DEPRECATED  
**Title:** Validation Rule Auditor — DEPRECATED (Wave 3b-1)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=validation_rule`.  

- **Replacement:** Use `audit-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/validator/`

**Status:** STABLE  
**Title:** Validator Agent  

**Declared intent (trimmed from `AGENT.md`):** Validates and synchronizes a skill package against both structural gates (`validate_repo.py`) and quality gates (`standards/skill-content-contract.md`). Called by every skill-building agent before a commit. Fixes errors it can fix automatically; escalates what it cannot. **Scope:** One skill at a time. Never validates in bulk unless explicitly called with `-  

- **Contract snapshot:** `class=build`, `modes=['single']`, `requires_org=False`.
- **Builder vs runtime:** This is a **library/skill** workflow agent unless `id` ends with something runtime-specific; vague feature requests may belong under `dev-skill-builder` vs `apex-builder` etc.
- **Repo coupling:** Stronger when `skills/` templates and `AGENT_RULES.md` / `AGENT_CONTRACT.md` are in workspace context.
- Structural + contract validation for **skills** (`validate_repo.py`, content contract).
- Wrong tool if you meant ‘validate my Apex compiles’ — that is CI/compiler, not this agent.
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/waf-assessor/`

**Status:** STABLE  
**Title:** Well-Architected Framework Assessor Agent  

**Declared intent (trimmed from `AGENT.md`):** Runs a Well-Architected Framework (WAF) assessment against a Salesforce implementation across the five pillars: **Trusted**, **Easy**, **Adaptable**, **Resilient**, **Composable**. Scores each pillar, surfaces the top 3 concerns per pillar with org evidence, and produces a remediation backlog ordered by severity × cost-to-fix. Also documents NFRs and maps th  

- **Contract snapshot:** `class=runtime`, `modes=['single']`, `requires_org=True`.
- **Org coupling:** Grounding improves with **read-only org**, MCP, or pasted Tooling/Metadata exports — otherwise label outputs as *desk-level*.
- Pillar-scored narrative — best when you attach **evidence** (diagrams, policies, key objects).
- **Not QA:** Analysis only — does not assert pass/fail against automated smoke tests.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/workflow-and-pb-migrator/`

**Status:** DEPRECATED  
**Title:** Workflow & Process Builder Migrator — DEPRECATED (Wave 3a)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`automation-migration-router`](../automation-migration-router/AGENT.md) with `--source-type=auto`.  

- **Replacement:** Use `automation-migration-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

### `agents/workflow-rule-to-flow-migrator/`

**Status:** DEPRECATED  
**Title:** Workflow Rule → Flow Migrator — DEPRECATED (Wave 3a)  

**Declared intent (trimmed from `AGENT.md`):** Replaced by [`automation-migration-router`](../automation-migration-router/AGENT.md) with `--source-type=wf_rule`.  

- **Replacement:** Use `automation-migration-router` as the active entry point.
- **Folder role:** Redirect + migration context only; informal @-mention should resolve to the replacement router and copy forward the right **domain** or **source_type** flags from that router's `AGENT.md`.
- **Informal-use analysis:** Still tempting by **legacy muscle memory** names (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, …). Treat these folders as **signposts**, not execution contracts.
- **QA (local structural harness, 2026-04-19):** PASS — `python3 scripts/validate_repo.py --agents` at repo root reported **0 errors**; this folder’s `AGENT.md` is in the validated set (schema, sections, citations, optional `inputs.schema.json`, harness rules, slash-command coverage for non-deprecated runtime). **Not exercised here:** org probe SOQL (`validate_probes_against_org.py`), `smoke_test_agents.py` (needs `sf org`), skill factuality, or LLM Plan execution — see `docs/validation/README.md`.

---

## Filename note

This file is still named `agent-informal-invocation-analysis.md` for stable links. Its contents are the **full** usage feedback (all invocation modes above + per-agent sections), not only informal @-folder chat.

---

## Quick picker: which usage mode?

| You have… | Lean on… |
|-----------|-----------|
| Only Cursor chat and a vague sentence | Mode **1** + force the model to name **artifacts** (paths, Ids, domains); expect more clarifying questions. |
| Time to copy flags from `AGENT.md` | Mode **2** — lowest drift for routers and multi-mode agents. |
| A team that wants the same prompt every time | Mode **3** (slash commands) or **6** (bundle + shipped commands). |
| Library maintenance / new skills | Modes **4** + **9** (`orchestrator`, researchers, builders, `validator`). |
| Another repo or “don’t copy the whole monorepo” | Mode **5** (MCP) or **6** (bundle export). |
| A git branch or PR | Mode **7** (+ static agents); add org truth only when honest. |
| Pre-sales / steering committee | Mode **10** — label confidence; attach evidence. |
| Two-step “design then verify” | Mode **9** — write intermediate reports to disk per `consumer-responsibilities.md`. |

---

## Closing synthesis (single feedback thread)

- **Same agent, many doors:** Nothing stops you from running e.g. `security-scanner` via informal @-mention, via a slash command, inside a PR review prompt, or as a delegated subagent — the **agent contract** is the same; only **context packaging** and **post-run hygiene** (reports on disk, JSON envelope) change.
- **Where value concentrates:** **Routers** (`audit-router`, `automation-migration-router`) for breadth; **static repo agents** for daily dev loops; **MCP/bundles** when probes and skills must not be dropped on the floor (`installing-single-agents.md` incident narrative).
- **What informal use cannot fix:** Org-complete inventory without **read path** (org, MCP, or paste). Modes **1** and **10** in particular need honesty about evidence vs inference.
- **Per-agent detail:** Every stable and deprecated folder is still analyzed above in **alphabetical** order — use that when choosing *which* agent; use **Usage modes** when choosing *how* to run it.
- **Structural QA (2026-04-19):** The **QA — methodology** section plus each agent’s **QA (local structural harness)** line record the local `validate_repo.py --agents` pass; treat org/LLM layers separately when you wire Layer 1–3 validation.

