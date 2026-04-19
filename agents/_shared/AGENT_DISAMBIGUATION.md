# Agent Disambiguation

**When two agents sound like they do the same thing, this doc tells you which one is right.**

Sourced from the Cursor 2026-04-19 review, which flagged these specific pairs as confusable during informal invocation. Logged at `feedback/FEEDBACK_LOG.md#2026-04-19-cursor-invocation-review`.

**For AI assistants:** if the user's request matches both sides of any pair below, **ask a clarifying question** before routing — do not guess.

---

## Axis 1: Build-time vs Run-time (class: build vs class: runtime)

The most common misroute. A `class: build` agent authors library content (skills, queue rows, research briefs). A `class: runtime` agent does Salesforce work against a repo or org.

| User says | They probably want | Common wrong landing |
|---|---|---|
| "Write a skill about X" | `content-researcher` → `<role>-skill-builder` → `validator` | `apex-builder` / `flow-builder` / `lwc-builder` (wrong — those emit code, not documentation) |
| "Fix permissions for user X" | `permission-set-architect` (audit mode) OR `user-access-diff` | `admin-skill-builder` (wrong — this authors admin skill docs, not fixes) |
| "Build me a flow that does X" | `flow-builder` | `orchestrator` (wrong — orchestrator routes queue rows) OR `dev-skill-builder` (wrong — authors dev docs) |
| "Review my Apex" | `code-reviewer` OR `security-scanner` OR `soql-optimizer` | `dev-skill-builder` (wrong — authors dev docs) |
| "Research Salesforce X for me" | `content-researcher` | `waf-assessor` / `org-assessor` (wrong axis — those score, not research) |

**Rule of thumb:** if the expected output is a **file under `skills/<domain>/<slug>/`**, it's a skill-builder. If the expected output is **code in `force-app/`** or **a report in `docs/reports/`**, it's a runtime agent.

---

## Axis 2: Design vs Audit vs Diff

Many agents have `design` and `audit` modes. A third class of agents compare two principals (**diff**). These are often confused.

| Agent | Verb | Input | Output |
|---|---|---|---|
| `permission-set-architect` (design mode) | **Design** | Persona description | PSG composition to build |
| `permission-set-architect` (audit mode) | **Audit** | Existing PSG / profile | Findings + remediation |
| `user-access-diff` | **Diff** | Two User Ids | Symmetric comparison of their effective access |
| `object-designer` | **Design** | Business concept | Setup-ready object design |
| `data-model-reviewer` | **Audit** | Object list / domain | Data model health report |

**Rule of thumb:** design = "what should be", audit = "what exists and what's wrong", diff = "how do two principals differ."

If the user says *"compare user A to user B"* → `user-access-diff`. If they say *"what should access look like for this role"* → `permission-set-architect --mode=design`. If they say *"audit permissions in prod"* → `permission-set-architect --mode=audit`.

---

## Axis 3: Author skill docs vs emit code scaffolds

| User says | Skill-doc agent (writes docs) | Code-scaffold agent (writes Apex/LWC/Flow) |
|---|---|---|
| "Apex best practices" | `dev-skill-builder` | `apex-builder` |
| "LWC component" | `dev-skill-builder` | `lwc-builder` |
| "Flow patterns" | `dev-skill-builder` | `flow-builder` |
| "Agentforce action" | `dev-skill-builder` | `agentforce-builder` |
| "How should we release?" | `devops-skill-builder` | `changeset-builder` / `release-train-planner` |
| "Security patterns" | `security-skill-builder` | `security-scanner` |
| "Data model patterns" | `data-skill-builder` | `object-designer` / `data-model-reviewer` |

**Rule of thumb:** if the user wants **to learn**, route to a skill-builder. If they want **working code in their repo**, route to a runtime builder or scaffold agent.

---

## Axis 4: "Validate" means three different things

The word "validate" is ambiguous. Three agents / tools are commonly conflated:

| User intent | Right tool |
|---|---|
| "Validate my skill package structure" | `validator` (runs `validate_repo.py` + skill content contract) |
| "Validate my Apex compiles" | `sf project deploy validate` (CLI, not an agent) — or the `flow-builder` / `apex-builder` harness Gate C |
| "Validate user inputs at Gate A" | built into every builder agent's `inputs.schema.json`; not a separate tool |

If the user says *"validate my code"* → ask: do you mean library structure (skill format), deploy-validate to an org, or input-schema check? All three exist; they don't substitute for each other.

---

## Axis 5: "Orchestrator" does NOT mean "orchestrate this ad-hoc work"

`agents/orchestrator/` is the **queue orchestrator**. It reads `MASTER_QUEUE.md`, picks the next row, and dispatches to the right skill-builder.

It does **not**:

- Take a free-form request like "design and then audit this flow"
- Coordinate runtime agents for a one-off delivery
- Replace `flow-builder` just because the user says "orchestrate a flow design"

If the user has an ad-hoc multi-step runtime task, they should **invoke each runtime agent directly in sequence** (Channel 10 in `docs/agent-invocation-modes.md`), not reach for `orchestrator`.

---

## Deprecated-name muscle memory

Typing `@<old-agent>` lands on a deprecation stub. **Redirect immediately**; do not execute.

| Old name | New invocation |
|---|---|
| `validation-rule-auditor` | `audit-router --domain=validation_rule` |
| `picklist-governor` | `audit-router --domain=picklist` |
| `record-type-and-layout-auditor` | `audit-router --domain=record_type_layout` |
| `report-and-dashboard-auditor` | `audit-router --domain=report_dashboard` |
| `reports-and-dashboards-folder-sharing-auditor` | `audit-router --domain=reports_dashboards_folder_sharing` |
| `approval-process-auditor` | `audit-router --domain=approval_process` |
| `case-escalation-auditor` | `audit-router --domain=case_escalation` |
| `lightning-record-page-auditor` | `audit-router --domain=lightning_record_page` |
| `list-view-and-search-layout-auditor` | `audit-router --domain=list_view_search_layout` |
| `my-domain-and-session-security-auditor` | `audit-router --domain=my_domain_session_security` |
| `org-drift-detector` | `audit-router --domain=org_drift` |
| `prompt-library-governor` | `audit-router --domain=prompt_library` |
| `quick-action-and-global-action-auditor` | `audit-router --domain=quick_action` |
| `sharing-audit-agent` | `audit-router --domain=sharing` |
| `field-audit-trail-and-history-tracking-governor` | `audit-router --domain=field_audit_trail_history_tracking` |
| `workflow-rule-to-flow-migrator` | `automation-migration-router --source-type=wf_rule` |
| `process-builder-to-flow-migrator` | `automation-migration-router --source-type=process_builder` |
| `approval-to-flow-orchestrator-migrator` | `automation-migration-router --source-type=approval_process` |
| `workflow-and-pb-migrator` | `automation-migration-router --source-type=auto` |

Full migration map with preserved rule-by-rule equivalence: `docs/MIGRATION.md`.

---

## For MCP clients

When `list_agents` returns the roster, the AI consuming it should:

1. Not pick a `class: build` agent for a runtime request or vice versa.
2. Not pick a deprecated agent — prefer the canonical replacement from this doc.
3. When the user's request matches multiple agents on Axes 1–5, ask one clarifying question before `get_agent`.

A future `list_deprecated_redirects` MCP tool (tracked in `docs/agent-invocation-modes.md`) will automate step 2.
