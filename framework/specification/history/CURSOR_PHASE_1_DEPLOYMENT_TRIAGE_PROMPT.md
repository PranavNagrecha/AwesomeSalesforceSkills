# Cursor Prompt: PR 1 - Native SfSkills Cursor Plugin and Deployment Failure Triager

You are working in the `AwesomeSalesforceSkills` / SfSkills repository as a senior Python engineer, Salesforce tooling architect, Cursor plugin engineer, and agent QA engineer.

Implement one reviewable pull request only:

> Build a locally installable native Cursor plugin and ship an evidence-grounded Deployment Failure Triager as its first product.

Do not implement the full Platform Foundation v2 proposal. Do not continue into Apex test triage, scratch-org behavioral QA, a capability graph, a general workflow engine, Backlog v2, all-command schemas, all-agent migration, or a Claude rewrite.

When this PR is complete, stop and return the required review report. A human will inspect and test the diff before any next phase.

---

## Product outcome

After this PR, a user should be able to:

1. Install or symlink a native SfSkills Cursor plugin locally with one supported helper command.
2. Reload Cursor and see a bounded Salesforce skill/router surface, focused subagents, `/triage-deployment`, `/sfskills-doctor`, and the SfSkills MCP server.
3. Give `/triage-deployment` either:
   - a Salesforce deployment job ID and target-org alias; or
   - a local Salesforce CLI deployment-result JSON fixture/file.
4. Receive a structured diagnosis with evidence, confidence, affected components, likely shared root causes, an ordered remediation plan, unknowns, and safe verification commands.
5. Receive an independent evidence-review pass that rejects unsupported claims and unsafe actions.
6. See an explicit partial/refusal result when the org, job, index, or evidence is unavailable.

This is the first product vertical slice. Add only the reusable infrastructure this product directly requires.

---

## Read before editing

Inspect the current branch rather than trusting stale documentation. At minimum, read relevant portions of:

- `README.md`
- `CLAUDE.md`
- `AGENT_RULES.md`
- `agents/_shared/AGENT_CONTRACT.md`
- `agents/_shared/DELIVERABLE_CONTRACT.md`
- `agents/_shared/CAPABILITY_MATRIX.md`
- `agents/_shared/schemas/`
- `scripts/build_plugin.py`
- `scripts/export_skills.py`
- `scripts/validate_repo.py`
- `scripts/search_knowledge.py`
- `scripts/smoke_test_agents.py`
- `scripts/execute_agent_fixture.py`
- `.github/workflows/org-validation.yml`
- `docs/validation/README.md`
- `mcp/sfskills-mcp/src/sfskills_mcp/server.py`
- the MCP Salesforce CLI wrapper, redaction, timeout, annotations, and tests
- existing deployment-related agents, commands, skills, templates, probes, and fixtures

Inspect current official Cursor plugin, skill, subagent, command, MCP, and hook formats before choosing file shapes. Inspect the installed/current Salesforce CLI help for deployment report JSON behavior.

Verify these repository facts and record corrections:

- the repository already has runtime agents and Claude loaders;
- current live-org QA is mostly probe/factuality/structure validation, not seeded end-to-end agent reasoning;
- the current Cursor export is based on flattened `.mdc` rules;
- missing search index behavior can look like an empty successful search;
- broad agents can declare large mandatory dependency sets.

Create `docs/product-v2/pr-1-deployment-triage-plan.md` before implementation. Keep it specific to this PR. Record baseline tests, artifact ownership, planned files, context limits, risks, and acceptance criteria. Then implement; do not stop after the plan.

---

## Design rules

1. User job first. A new abstraction must be required by installability or deployment triage.
2. Context is a budget. Do not load the full skill corpus or a union of every deployment-related skill.
3. Use progressive disclosure. Start from bounded routers; load detailed skill/reference files conditionally.
4. Use subagents for noisy or independently verifiable work.
5. Pass structured facts and evidence references, not complete subagent transcripts.
6. Normalize and bound MCP output before it enters model context.
7. Every material diagnosis needs a resolvable evidence reference.
8. Product Salesforce tools remain read-only.
9. Do not expose all 48 existing agents as Cursor subagents.
10. Do not expose 1,034 flattened `.mdc` files as the recommended plugin.
11. Preserve legacy Cursor rules export as an explicit compatibility option.
12. Be truthful about local versus cloud hook coverage and unavailable live-org tests.
13. Keep generated artifacts deterministic and add `--check` behavior.
14. Stop after this PR.

---

## Safety boundary

No product path may:

- start, quick-deploy, cancel, retry, or modify a Salesforce deployment;
- deploy metadata;
- perform DML or data import;
- execute anonymous Apex;
- change permissions or users;
- install/uninstall packages;
- create/delete/refresh orgs or sandboxes;
- expose credentials or auth URLs.

The new deployment tool retrieves an existing deployment result only.

Local report/telemetry files are allowed when redacted and gitignored. No Salesforce mutation is allowed in this PR.

---

## Required implementation

### 1. Native Cursor plugin

Add a deterministic native Cursor plugin build using the current supported Cursor plugin format. Use a source/build split consistent with the repo, for example:

```text
integrations/cursor/                 canonical adapter sources
scripts/build_cursor_plugin.py      builder and --check
dist/cursor/sfskills/               generated package
```

Adjust the exact paths only when existing conventions justify it.

The generated plugin must include:

- valid plugin metadata;
- a concise top-level Salesforce router skill;
- the 11 domain router skills, or a smaller measured equivalent that still covers the corpus;
- native Cursor subagents listed below;
- `/triage-deployment`;
- `/sfskills-doctor`;
- SfSkills MCP configuration;
- safety/telemetry hooks required below.

Do not duplicate canonical skill prose by hand. Reuse or generate from canonical sources.

Do not package all 1,034 skills as top-level auto-discoverable skills in this PR. Detailed knowledge remains available through bounded routing and MCP `get_skill`/search paths.

Keep `scripts/export_skills.py --target cursor` or its current equivalent available as `legacy-rules` compatibility behavior. Update docs so the native plugin is recommended and the flat rules export is labeled legacy.

### 2. Local plugin install helper

Provide one supported local install path, such as:

```bash
python3 scripts/install_cursor_plugin.py --link
```

It must:

- detect the repository root;
- build before install;
- locate Cursor's supported local plugin directory;
- link or copy without silently replacing an unrelated install;
- support dry-run/check behavior;
- print reload, verify, and uninstall instructions;
- avoid any public Marketplace claim.

Add deterministic tests for path handling and overwrite protection.

### 3. Focused native subagents

Create no more than five custom Cursor subagents for this PR. Use current native Cursor frontmatter and `readonly: true` where supported.

#### `sf-context-librarian`

Selects the smallest relevant SfSkills files for the observed deployment failure categories. Returns paths, relevance reasons, and estimated context cost. It does not diagnose the deployment.

#### `sf-repo-mapper`

Finds affected local metadata/source files and references. Returns compact file/line evidence and unknowns. Read-only.

#### `sf-org-grounder`

Calls only approved read-only SfSkills MCP tools. Returns normalized facts, evidence IDs, truncation state, and unknowns. It must not return unbounded raw output.

#### `deployment-failure-triager`

Performs the diagnosis from the compact context, repository map, and org/result evidence.

#### `sf-evidence-reviewer`

Independently checks the draft for unsupported claims, missing citations, contradictions, unsafe actions, overconfidence, and failure to declare unknowns.

Do not add a generic orchestrator unless current Cursor behavior demonstrably requires one. The `/triage-deployment` command may coordinate the five roles directly.

Keep prompts concise and single-purpose. The parent should receive structured summaries, not internal transcripts.

### 4. Canonical deployment triage agent and command

Add a canonical runtime agent named `deployment-failure-triager` using existing repository contracts, plus the native Cursor command `/triage-deployment`.

Support these input modes:

```text
A. deployment job ID + optional target-org alias
B. local Salesforce CLI deployment-result JSON path
C. explicitly supported CI result file/path, only if a reliable parser already exists or can be added without broad scope
```

Do not guess a job ID or silently use the most recent deployment.

Add typed validation only for this new command/agent. Do not migrate the other commands.

The result must contain:

- `completed`, `partial`, `refused`, or `failed` status using the smallest backward-compatible extension to the existing envelope if needed;
- normalized failure groups;
- primary and contributing root-cause hypotheses;
- confidence with explanation;
- evidence references for every material claim;
- affected components and local source paths when resolvable;
- duplicate-symptom/common-root-cause grouping;
- ordered remediation plan;
- safe verification commands shown but not executed;
- unknowns and evidence gaps;
- context/provenance summary;
- evidence-review outcome.

Do not include automatic fixes or deployment execution.

### 5. Read-only MCP deployment result tool

Add one normalized read-only MCP tool, preferably:

```text
get_deployment_result(job_id, target_org=None, wait_minutes=0, failure_limit=100, cursor=None)
```

Use the official Salesforce CLI deployment report operation or an equally read-only official API.

Requirements:

- explicit job ID required;
- no `use-most-recent` default;
- JSON output;
- reuse existing Salesforce CLI execution, timeout, redaction, and error helpers;
- normalize CLI-version result variants into one stable schema;
- separate component failures, Apex test failures, coverage issues, warnings, and general messages;
- deduplicate repeated symptoms when safe while preserving occurrence counts;
- stable evidence IDs;
- pagination or bounded output;
- explicit `truncated`, `next_cursor`, and source-count information;
- include relevant CLI/API/version metadata;
- no credentials or auth values;
- no local or org mutation.

Use existing MCP annotations correctly. Add captured fixtures for at least:

- successful retrieval with component failures;
- deployment test failures;
- coverage failure/warning;
- many repeated failures;
- in-progress result;
- unknown/expired job ID;
- unauthenticated org;
- CLI timeout;
- malformed/unexpected JSON;
- redaction-shaped error content.

### 6. Context pack and structured handoff

Add a pilot-specific context definition, not a repository-wide dependency engine.

The deployment triager context pack must have:

- a core read set;
- conditional packs keyed to observed failure classes;
- deterministic ordering;
- file existence validation;
- selection reasons;
- estimated token/file counts;
- explicit overflow state.

Starting budget:

```text
target domain skill/reference files: <= 8
hard limit: <= 12 unless explicit overflow
single MCP result in model context: <= 32 KiB
```

If a result exceeds the limit, paginate, aggregate, or return a bounded summary. Never silently drop evidence.

Add the smallest validated handoff shape necessary. It should include equivalents of:

```json
{
  "run_id": "...",
  "task": "...",
  "facts": [],
  "evidence_refs": [],
  "hypotheses": [],
  "unknowns": [],
  "recommended_next_agent": null,
  "context_metrics": {
    "files_loaded": 0,
    "estimated_tokens": 0,
    "tool_output_bytes": 0,
    "truncated": false
  }
}
```

Do not pass full chat or subagent transcripts between roles.

### 7. Context telemetry and context-rot QA

Write redacted local run telemetry under a gitignored path, for example:

```text
.sfskills/runs/<run-id>/
```

Capture:

- selected files and selection reasons;
- estimated tokens;
- tool-output bytes before/after normalization when available;
- evidence IDs;
- subagents invoked;
- truncation/pagination;
- unresolved citations;
- compaction observation events when Cursor exposes them.

Use a `preCompact` hook only for observation/logging. Do not claim it can prevent or rewrite compaction if current Cursor behavior does not allow that.

Add tests for:

- irrelevant skill distractors;
- a very large result;
- duplicate symptoms;
- contradictory local and org evidence;
- missing org authentication;
- malformed job ID;
- second deployment question after a long first interaction, where automatable;
- pre/post compaction behavior where automatable;
- evidence reviewer receiving a deliberately unsupported diagnosis.

Where full Cursor execution cannot be automated in CI, separate deterministic tests from a documented manual Cursor smoke script/checklist. Do not label manual checks automated.

### 8. Safety hooks

Add a native Cursor `beforeShellExecution` guard and, for local Cursor where supported, `beforeMCPExecution` guard.

Use fail-closed behavior for security-critical checks where supported.

Allow only the product's known read-only Salesforce operations. Deny or require explicit user intervention for state-changing Salesforce commands, including:

- project deploy start/validate/quick/cancel/resume when initiated by the agent;
- data insert/update/delete/import/upsert;
- anonymous Apex;
- permission/user/package/org mutation;
- destructive metadata operations.

The product may call `sf project deploy report --job-id ... --json` through the MCP wrapper.

Test bypass attempts involving:

- semicolons;
- pipes;
- `&&` and `||`;
- shell substitution;
- nested shells;
- aliases;
- reordered flags;
- misleading strings or filenames;
- direct legacy `sfdx` forms where still relevant.

Do not implement a fragile allow/deny list based only on substring presence.

Document that some MCP hooks may not execute in Cursor cloud agents. Do not promise identical local/cloud policy coverage when the host does not provide it.

### 9. Doctor and missing-index behavior

Implement a focused `/sfskills-doctor` command/script. Do not build a general runtime CLI.

Check:

- repository/plugin version;
- plugin build/install state;
- Python dependencies;
- MCP entrypoint;
- Salesforce CLI availability/version;
- authenticated org aliases without secrets;
- search-index presence/freshness;
- current target-org configuration when available.

Provide human and JSON output with stable statuses.

Fix direct search so a missing index returns explicit `index_missing` and a nonzero exit code rather than appearing as zero matches. Update MCP search to return a corresponding explicit status. Do not break router-based skill discovery that does not require the index.

### 10. Documentation

Add concise docs for:

- native local Cursor install/uninstall;
- plugin contents;
- `/sfskills-doctor`;
- `/triage-deployment` inputs and examples;
- fixture-only mode;
- live read-only mode;
- what data is stored locally;
- product safety boundary;
- local versus cloud hook limitations;
- legacy `.mdc` export;
- known limitations;
- no public Marketplace claim under the current license.

Do not update unrelated architecture documentation or duplicate changing counts manually across many files.

---

## Tests and QA required in this PR

Run the repository's practical baseline and record exact results. Use the actual commands supported by the branch, including equivalents of:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_repo.py --agents
python3 scripts/build_plugin.py --check
python3 scripts/export_skills.py --check
```

Add focused tests for:

- Cursor plugin deterministic build and drift check;
- install helper dry-run/path safety;
- native component presence;
- missing-index CLI and MCP behavior;
- deployment result normalization variants;
- pagination/truncation;
- stable evidence IDs;
- redaction and timeout paths;
- command input validation;
- context selection budget and overflow;
- broken selected path;
- structured handoff validation;
- unsupported-claim reviewer fixture;
- shell/MCP policy bypass attempts;
- partial/refusal outputs;
- existing MCP tool-count or manifest expectations updated from canonical registration rather than hardcoded carelessly.

If live credentials are available, retrieve an existing failed deployment result read-only and record the run. Do not start a deployment. If credentials or a suitable job ID are unavailable, mark live verification not run and use captured fixtures. Do not fabricate a pass.

---

## Explicitly out of scope

Do not implement any of the following in this PR:

- Apex Test Failure Triager;
- scratch-org creation or fixture deployment;
- general workflow engine;
- capability registry/graph;
- full command specification migration;
- Backlog v2;
- full decision-tree compiler;
- migration of all existing agent dependencies to context packs;
- Claude plugin modernization;
- public Cursor Marketplace submission;
- more than the five focused subagents listed above;
- customer-org mutation tools;
- automated deployment remediation.

A small targeted fix to an existing shared contract is allowed only when the Deployment Failure Triager cannot produce a valid honest result without it. Document the reason.

---

## Acceptance criteria

The PR is complete only when all applicable criteria are met:

1. A deterministic native Cursor plugin builds successfully and has a drift check.
2. A local helper installs/links it without manual copying or unsafe overwrite.
3. Cursor's recommended path uses bounded router skills, not 1,034 flat rules.
4. Legacy flat rules export still works as an explicitly legacy option.
5. The plugin includes MCP configuration, `/sfskills-doctor`, `/triage-deployment`, and no more than five focused subagents.
6. `/triage-deployment` works from a credential-free local fixture.
7. It can retrieve an existing deployment result read-only when credentials/job ID are available.
8. The MCP tool cannot start, modify, cancel, quick-deploy, or retry a deployment.
9. Large results are bounded/paginated with explicit truncation.
10. Material diagnoses cite stable evidence IDs and relevant local/skill paths.
11. Duplicate symptoms can be grouped under a shared root cause without losing counts/evidence.
12. Context target is at most 8 domain skill/reference files and never silently exceeds 12.
13. No single MCP result over 32 KiB is injected without pagination/normalization.
14. Parent/subagent handoffs are structured and do not contain complete transcripts.
15. The independent reviewer catches the seeded unsupported claim.
16. Missing index, org, job, evidence, and auth states are explicit partial/refusal/error states.
17. Safety hooks pass compound-command bypass tests and fail closed where supported.
18. No org mutation capability is added.
19. Existing tests remain green or any intentional compatibility change is narrowly documented.
20. Docs contain tested local install, verification, use, and uninstall steps.
21. The phase plan and final report state exactly which live tests ran.

---

## Required final report

When the PR is complete, stop. Do not begin Apex triage or real-org QA.

Return:

1. `What changed`
2. `User-visible workflow`
3. `Files added, changed, generated, and deleted`
4. `Architecture decisions`
5. `Subagents and responsibilities`
6. `Context-budget measurements`
7. `MCP read-only and safety analysis`
8. `Tests run with exact results`
9. `Live-org verification run` or `Live-org verification not run`
10. `Manual Cursor verification still required`
11. `Known limitations`
12. `Risks and migration notes`
13. `Review checklist`
14. `Items explicitly deferred`

Do not hide warnings or unrun tests. Do not continue beyond this PR.
