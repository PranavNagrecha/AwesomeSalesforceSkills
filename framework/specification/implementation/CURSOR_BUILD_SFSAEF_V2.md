# Cursor Master Prompt — Build SfSkills as the Salesforce AI Engineering Framework

You are working locally in the current SfSkills / AwesomeSalesforceSkills repository as the implementation team for a product whose architecture is owned by the attached **SfSkills — Salesforce AI Engineering Framework Specification 0.9.0**.

Your role is implementation, integration, testing, and evidence production. Do not redesign the product casually. When implementation reality contradicts the specification, record the conflict, choose the safest behavior, add an ADR, and preserve the requirement for product-owner review.

## Mission

Evolve the current SfSkills repository from a Salesforce skill library into a locally usable, evidence-grounded Salesforce AI Engineering Framework that:

- preserves the existing 1,034-skill knowledge corpus and working compatibility paths;
- ships a native Cursor product rather than 1,034 flattened rules;
- solves real Salesforce engineering jobs through typed products;
- gathers bounded read-only Salesforce/project evidence;
- controls context and survives long conversations/compaction;
- uses focused subagents and structured handoffs;
- links every material diagnosis to evidence;
- independently reviews consequential outputs;
- can be replayed and audited;
- proves behavior through fixtures, actual host smoke tests, and disposable scratch-org known truth;
- remains portable to Claude Code and future VS Code/Copilot and Agentforce Vibes adapters.

Build the complete V2 release-candidate architecture on one local branch using reviewable local commits and milestone tags. Do not push, publish, open a pull request, upload to a marketplace, or modify any remote.

If you cannot complete every milestone, do not disguise partial work. Stop at the last fully passing milestone, produce the exact failure/partial review package, and identify the blocker. Depth and truthful evidence are more important than breadth or file count.

---

# Inputs

You have:

1. The current local SfSkills repository, which may already contain Phase 1/Phase 2 work and uncommitted changes.
2. The extracted specification package containing:
   - numbered requirements under `spec/`;
   - JSON Schemas under `schemas/`;
   - product definitions under `products/`;
   - core/product agent contracts under `agents/`;
   - command specs under `commands/specs/`;
   - evidence-tool specs under `mcp/tool-specs/`;
   - policies under `security/`;
   - QA scenarios and thresholds under `qa/`;
   - host adapter requirements under `adapters/`;
   - a tested reference kernel under `reference-kernel/`;
   - artifact-level migration ledgers under `migration/catalogs/`, including explicit dispositions for every uploaded baseline skill, canonical agent, command, and MCP tool;
   - a concrete optional project-inspector reference component;
   - the exact return-package contract under `implementation/REVIEW_RETURN_CONTRACT.md`.

Read these first, in order:

```text
README.md
SPEC_INDEX.md
spec/000-status-and-conformance.md
spec/010-vision-and-scope.md
spec/020-design-principles.md
spec/040-reference-architecture.md
spec/050-runtime-and-state-machine.md
spec/080-context-engine.md
spec/090-evidence-and-claim-model.md
spec/100-tool-and-mcp-broker.md
spec/110-security-and-authority.md
spec/140-quality-and-evaluation.md
spec/150-real-org-qa.md
spec/160-host-adapters-and-portability.md
products/README.md
commands/API_REFERENCE.md
mcp/TOOL_REFERENCE.md
agents/CONTRACT_REFERENCE.md
implementation/IMPLEMENTATION_SEQUENCE.md
implementation/REVIEW_RETURN_CONTRACT.md
implementation/requirements.csv
migration/catalogs/V2_DISPOSITION_LEDGER.md
migration/catalogs/current-skills.csv
migration/catalogs/current-agents.csv
migration/catalogs/current-commands.csv
migration/catalogs/current-mcp-tools.csv
```

Then inspect the complete current repository. Do not trust stale README counts, prior reports, or prior ZIP claims more than the actual branch.

---

# Non-negotiable product rules

These override convenience and implementation shortcuts.

1. **User job first.** Do not create generalized infrastructure without at least one current product consumer and test.
2. **Product Salesforce authority is read-only.** No product agent/tool may deploy, DML, run anonymous Apex, assign permissions, alter users, install packages, create/delete orgs, promote work items, or otherwise mutate Salesforce.
3. **Scratch QA setup is separate.** Controlled mutation is allowed only in versioned setup/teardown code for a verified disposable scratch org. That code is never exposed as a model tool.
4. **Unknown tool means deny.** MCP annotations are hints, not enforcement.
5. **Explicit target identity.** Never silently choose the first project, default org, most recent deployment, or most recent test run.
6. **SfSkills is not the target SFDX project.** Local project inspection is optional enrichment. Prefer explicit `project_path`, then one unambiguous active workspace/bounded root, otherwise standalone. Multiple candidates produce `ambiguous`.
7. **Context is a budget.** Starting defaults: 3–5 core knowledge files; target total <=8; hard <=12; one injected tool page <=32 KiB; no full transcript handoff; preserve output/review reserve.
8. **Evidence before confidence.** Every material claim must resolve to evidence. Skill guidance does not prove target state.
9. **Independent review.** Consequential product output cannot be `completed` with a blocking deterministic lint or evidence-review finding.
10. **Honest states.** Use `completed`, `partial`, `refused`, or `failed` with explicit impact. No silent truncation, target substitution, or omitted live test.
11. **Thin model, thick system.** Deterministic code owns parsing, identifiers, schemas, normalization, pagination, redaction, policy, state, and hard grading.
12. **Small native subagent surface.** Do not expose all existing agents. A subagent must justify isolated context or independent review.
13. **Use official tools where they are authoritative.** Prefer Salesforce CLI / official Salesforce DX MCP for raw operations; add SfSkills wrappers for policy, normalization, evidence, bounded output, and product aggregation.
14. **No unrestricted Salesforce DX MCP.** Do not configure `all`, `ALLOW_ALL_ORGS`, or broad write-capable toolsets for product execution.
15. **Actual host proof.** File-shape tests do not prove Cursor behavior. Test discovery, command invocation, subagents, MCP, review, and output in actual Cursor.
16. **No fabricated completeness.** No placeholder product may be labelled complete or stable.
17. **Local Git only.** No push, PR, marketplace, release publication, or remote mutation.
18. **Exact review evidence.** Every claimed test/run must appear in the return ZIP with command, cwd, output, duration, and real exit code.

---

# Current-repository preservation

The current branch may contain valid work not represented in an earlier patch/ZIP. Before editing:

1. Record:
   - repository root;
   - branch and HEAD;
   - `git status --short` and full status;
   - remotes without credentials;
   - local branches/tags;
   - untracked files relevant to V2;
   - current Python, Node, Salesforce CLI, Cursor, MCP package, and OS versions.
2. Save a timestamped local backup outside the repository:
   - `git diff` and `git diff --cached`;
   - archive of untracked V2 files;
   - current file inventory;
   - no secrets.
3. Do not delete, reset, or overwrite user work merely to obtain a clean tree.
4. If the current work is coherent, commit it locally with an honest message before starting V2 integration. If it is not coherent, preserve it on a local backup branch or patch and document the choice.
5. Create or switch to:

```text
product/sfskills-v2-local
```

Do not rewrite already-reviewed local milestone tags.

---

# Baseline

Run the actual repository’s supported equivalents of:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_repo.py --agents
python3 scripts/build_plugin.py --check
python3 scripts/export_skills.py --check
```

Also run current MCP tests and any V2 tests already present.

Capture exact logs and exit codes. If the baseline is red, determine whether the failure exists before your changes. Do not declare it unrelated without reproducing it at the baseline commit or preserved pre-change tree.

Create:

```text
docs/product-v2/current-state.md
```

It must contain actual counts, existing V2/Phase files, known warnings, generated ownership, current adapter behavior, test results, and divergence from the specification.

---

# Canonical implementation ownership

Use repository conventions where sensible, but preserve these ownership rules:

- Existing `skills/` packages remain canonical Salesforce knowledge.
- V2 product/agent/command/tool/policy/context definitions are canonical machine-readable inputs.
- Schemas are canonical machine contracts.
- Runtime/core code consumes definitions and schemas.
- Cursor/Claude/Copilot/Vibes artifacts are generated adapters where practical.
- Generated distributions are never hand-edited.
- Existing commands/agents remain compatibility surfaces unless deliberately migrated.
- The specification is versioned in the repository under a stable path such as `framework/specification/`.

A reasonable target layout is described in `migration/recommended-repository-layout.md`. You may adapt paths to existing conventions, but record any material change in an ADR and in the return traceability matrix.

Do not build a generalized capability graph or workflow engine unless at least two implemented products require the exact shared abstraction and tests prove it reduces complexity. A generated product catalog for adapters is acceptable; a second hand-maintained source of truth is not.

---

# Milestone execution

Implement all milestones in order. Make a local commit and annotated local tag only after that milestone’s required gates pass. Continue automatically through routine passing milestones. Stop and package evidence on a P0 blocker.

## M0 — Specification adoption and branch repair

### Implement

- Import the specification, schemas, product/agent/command/tool definitions, policies, scenarios, and reference kernel.
- Add a repository validator for:
  - duplicate requirement IDs;
  - JSON/schema validation;
  - broken definition references;
  - unknown product/agent/tool/command IDs;
  - unowned generated output;
  - context-pack limits;
  - read-only policy violations;
  - scenario product references;
  - generated command/tool/agent contract drift;
  - command error statuses and side-effect policy;
  - tool retry/cache/target-binding safety;
  - agent collaborator and authority escalation violations.
- Generate a requirement traceability working file from `implementation/requirements.csv`.
- Load and verify the complete artifact-level migration ledgers under `migration/catalogs/`. Reconcile them against the actual branch before changing architecture. Every current skill, canonical agent, command, and MCP tool must retain an explicit disposition: preserve, compatibility-only, migrate, promote, deprecate-with-replacement, or remove-with-evidence. Never silently delete, flatten, duplicate, or auto-promote an artifact.
- Produce a machine-checkable migration reconciliation report that identifies additions, removals, renamed IDs, stale ledger entries, and any divergence from the uploaded baseline. A count match alone is insufficient.
- Compare the current branch’s Phase 1/Phase 2 implementation to P01/P02 requirements. Preserve stronger working code.
- Integrate the provided project-inspector behavior or prove the existing implementation is stronger.
- Separate Phase 1 and Phase 2 work into truthful commit ranges if previous work mixed them.
- Add a deterministic review-package builder scaffold that implements the return contract.

### Do not

- create product stubs merely to make definitions appear implemented;
- bulk-convert all legacy commands/agents;
- infer migration completion from aggregate counts;
- invent references or ownership links merely to clear orphan warnings;
- discard current working code because names differ.

### Gate

- baseline status explained;
- framework validators pass;
- reference-kernel tests pass;
- migration reconciliation covers every actual current skill, canonical agent, command, and MCP tool with no silent loss;
- specification can be checked from a clean checkout;
- review-package scaffold has tests;
- clean local tag `sfskills-v2-m0-spec-adopted`.

## M1 — Deterministic V2 core

### Run/state

Implement:

- run IDs and state transitions from SFAEF-050;
- explicit mode, authority, target identities, host capabilities, versions, and terminal status;
- backward-compatible output-envelope v2, including `persisted` and nullable paths for no-persist behavior;
- checkpoint/resume validation.

### Context

Implement:

- context candidates and manifests;
- required core plus conditional packs;
- deterministic ordering, deduplication, selection reasons, estimated token/byte cost;
- target <=8 and hard <=12 defaults;
- <=32 KiB model-visible tool pages;
- explicit overflow/truncation;
- stage checkpoints and second-task isolation;
- no transcript handoff.

### Evidence

Implement:

- stable evidence and claim IDs;
- typed support/contradiction links;
- provenance, target identity, timestamps, source digest, classification, truncation, upstream version;
- deterministic unsupported-claim, missing-reference, contradiction, stale/truncated, and secret evidence lint;
- deterministic confidence rationale;
- structured output rendering from validated JSON.

### Policy and broker

Implement:

- authority profiles;
- deny-by-default tool policy;
- explicit org allowlist/pinning;
- shell command parser/guard with compound/nested bypass tests;
- product-read-only broker interface;
- normalized error classes;
- redaction before persistence/model exposure;
- run-local telemetry and replay bundle.

### Doctor and search

Implement focused `sfskills-doctor` / `/sfskills-doctor` behavior for:

- repository and definition version;
- generated artifact drift;
- Python/Node/Salesforce CLI/MCP availability/version;
- native plugin build/install status;
- authenticated org aliases without secrets;
- explicit target identity;
- index presence/freshness;
- host capability status.

Fix direct missing-index behavior to return explicit `index_missing` and a nonzero CLI exit where applicable. Do not break router-based discovery that does not need the index.

### Gate

- deterministic core unit tests;
- schema and definition validation;
- policy adversarial tests;
- context distractor/overflow/checkpoint tests;
- evidence lint tests;
- review bundle/replay tests;
- existing repository tests/exports remain green or narrow intentional changes are documented;
- tag `sfskills-v2-m1-core`.

## M2 — Native Cursor, P01, and P02

### Native Cursor plugin

Build a deterministic native Cursor plugin using the current installed/supported format. Verify current Cursor documentation/behavior rather than relying on stale examples.

The default plugin must include:

- valid plugin metadata;
- one concise Salesforce entry skill;
- bounded domain/product router skills;
- focused V2 subagents required for P01/P02;
- `/sfskills-doctor`;
- `/triage-deployment`;
- `/triage-apex-tests`;
- restricted SfSkills evidence broker MCP configuration;
- applicable safety and telemetry hooks;
- no 1,034 flattened rules as the recommended path.

Preserve current flat `.mdc` export as explicitly legacy compatibility.

Add a local install helper that:

- builds before install;
- uses the current supported Cursor local plugin directory;
- supports link/copy, dry-run, check, and uninstall;
- does not overwrite an unrelated installation;
- prints exact reload/verification steps;
- makes no Marketplace claim.

### Subagents

Prove, in actual Cursor, the safest working configuration for:

- `sf-context-librarian`;
- `sf-project-inspector`;
- `sf-org-grounder` or parent-performed MCP fallback;
- `sf-evidence-reviewer`;
- `deployment-failure-triager`;
- `apex-test-failure-triager`.

Do not assume a `readonly` subagent can or cannot call MCP; test the current host. If host constraints conflict, keep product behavior and authority by moving the MCP call to the parent/restricted broker and passing normalized evidence to a read-only role. Record the capability result.

### P01 Deployment Failure Triage

Implement the complete product definition:

- fixture input and existing job ID input;
- explicit target org;
- optional external project path/discovery;
- read-only `get_deployment_result` normalization;
- component/test/coverage/warning/general grouping;
- stable evidence IDs;
- duplicate symptom clustering with counts;
- target/job mismatch defense;
- source mapping only when a project is selected;
- root causes, confidence rationale, action order, unknowns, safe verification;
- independent review and valid envelope;
- no deploy/retry/cancel/quick-deploy.

### P02 Apex Test Failure Triage

Implement:

- fixture and existing test-run retrieval;
- explicit target org;
- method/stack/coverage/timing normalization;
- shared-root-cause clustering;
- assertion, Mixed DML, callout mock, limits, sharing, async, and common setup cases;
- optional source/automation enrichment;
- no test execution in ordinary product mode;
- independent review and valid envelope.

### Actual Cursor smoke

Perform, in actual Cursor:

1. local plugin install/reload;
2. skill/command/subagent discovery;
3. doctor;
4. P01 fixture run;
5. P02 fixture run;
6. evidence reviewer catches a seeded unsupported claim;
7. restricted MCP invocation path;
8. standalone mode without a Salesforce project;
9. explicit external project mode if a suitable project is available;
10. long/distractor/second-task test where the host permits.

Capture sanitized evidence. File existence is not a host pass.

### Live read-only verification

If suitable credentials and existing failed deployment/test IDs are available, retrieve them read-only. Do not create failures in a customer/non-disposable org. Record `not_run` when unavailable.

### Gate

- all P01/P02 deterministic and fixture scenarios;
- actual Cursor smoke;
- no product mutation;
- context/evidence thresholds;
- clean tag `sfskills-v2-m2-triage`.

## M3 — P03 and disposable behavioral QA

### P03 Access Path Explainer

Implement `/why-cant-user` and product definition for:

- user/license/profile/permission sets/groups/muting;
- object CRUD;
- field access;
- record types/business process where relevant;
- record ownership/hierarchy/sharing rules/teams/manual/Apex sharing;
- restriction rules and territories where available;
- record access evidence;
- UI/action visibility versus platform access;
- automation/validation blockers when evidenced;
- first blocking layer and granting paths;
- least-privilege remediation options shown, never applied.

Minimize sensitive user/record data. Do not dump full permission metadata into context.

### Scratch-org lab

Implement the architecture in `qa/scratch-org-lab.md`:

- protected Dev Hub allowlist;
- one-day scratch org with unique scenario marker;
- setup scripts outside model tool surfaces;
- product read-only after evidence creation;
- actual product path and selected skill contents;
- deterministic grade;
- sanitization and secret scan;
- unconditional destroy and deletion proof.

Implement scenario fixtures for at least:

- six P01 scenarios;
- seven P02 scenarios;
- six P03 scenarios.

If credentials are not configured, implement and test all guards/fixtures locally, mark live scratch execution `not_run`, and do not claim behavioral qualification. If credentials are configured, run the scenarios and preserve exact evidence.

### Baseline comparison

Run the same fixture/scenario set with:

- vanilla Cursor/model and raw evidence;
- selected skills without the full framework where practical;
- full SfSkills framework.

Report required-finding recall, unsupported claims, evidence validity, status, safety, context cost, duration, and qualitative usefulness. Do not publish a single accuracy number without the full method.

### Gate

- P03 actual Cursor fixture smoke;
- access scenario suite;
- scratch guards and cleanup tests;
- real scratch results or explicit not-run status;
- benchmark report;
- tag `sfskills-v2-m3-behavioral-qa`.

## M4 — P04 through P06 flagship expansion

Implement, one at a time, reusing the shared core:

1. P04 Change Impact Planner;
2. P05 Automation Transaction Profiler;
3. P06 Release Readiness Review.

For each:

- implement typed command, product agent, conditional context pack, output, broker tools, fixtures, evidence review, actual Cursor fixture smoke, docs, and limitations;
- avoid raw metadata dumps;
- distinguish static/deployed/runtime evidence;
- never apply changes, execute deployments, or mutate orgs;
- add only shared abstractions demonstrated by at least two products;
- compare context and quality before/after any shared refactor.

Gate each product internally, then tag the milestone `sfskills-v2-m4-flagship`.

## M5 — P07 through P12 beta portfolio

Implement end-to-end beta paths for:

- P07 Security Posture Review;
- P08 Integration Incident Triage;
- P09 Data Migration Reconciliation;
- P10 Org Health Assessment;
- P11 Agentforce Quality Engineer;
- P12 Multi-Org Drift Analysis.

Requirements:

- no placeholder-only command;
- at least one rich happy fixture and one failure/partial fixture per product;
- product/agent/command/tool/context definitions consumed by runtime;
- deterministic evidence lint and independent review;
- actual Cursor command discovery and fixture execution;
- data minimization and product-read-only policy;
- explicit beta label and limitations;
- no claim of scratch qualification unless run.

Do not build ten additional products beyond the specification. Quality and shared-core proof are more important than inventory.

Tag `sfskills-v2-m5-beta-portfolio`.

## M6 — Portability, hardening, and local release candidate

### Claude

Verify current Claude compatibility and at least P01/P02 fixture execution through the intended Claude adapter or existing plugin path. Do not rewrite every existing Claude agent. Fix only product-path and contract incompatibilities.

### Additional host proof

Implement one proof-of-concept adapter for either:

- VS Code/GitHub Copilot using Agent Skills/custom agents/MCP; or
- Agentforce Vibes using its current project/org/tool capabilities.

It must prove one product fixture path and emit a host capability record. It need not equal Cursor release maturity.

### Portable package

Evaluate Agent Plugins packaging. Build it only if current licensing and format permit a truthful local/private package. Do not claim public marketplace readiness without a licensing decision.

### Hardening

- deterministic generated builds and `--check`;
- install/uninstall polish;
- version alignment;
- truthful generated counts/docs;
- targeted stale queue pointer fix;
- targeted output-envelope/no-persist fix;
- legacy compatibility documentation;
- current security, QA, and compatibility reports;
- no dead temporary architecture.

### Release status

- P01–P03 may be release-candidate only if required behavioral/host gates ran and passed.
- P04–P06 may be beta/RC according to actual evidence.
- P07–P12 remain beta unless stronger evidence exists.
- If scratch credentials were unavailable, the overall product remains beta regardless of fixture quality.

Tag the clean local head:

```text
sfskills-v2-rc1-local
```

Do not publish.

---

# Implementation details that must remain consistent

## Product execution pipeline

```text
command / typed input
  -> preflight and target attestation
  -> policy review and run plan
  -> context librarian
  -> optional project inspector
  -> fixture loader or org grounder through restricted broker
  -> product agent
  -> deterministic claim/evidence lint
  -> independent evidence reviewer
  -> structured output and run bundle
```

A host may combine stages when necessary, but it must preserve isolation of independent review and all typed artifacts.

## Project inspector

Use the provided reference component or a stronger existing implementation. Required behavior:

1. explicit `project_path` first;
2. current active workspace with `sfdx-project.json`;
3. bounded workspace roots;
4. one candidate -> selected;
5. no candidate -> standalone;
6. multiple candidates -> ambiguous, never guess;
7. path traversal/symlink escape protection;
8. source mapping is optional enrichment;
9. no local file modifications.

## Evidence broker

Every result includes:

- tool ID and version;
- run ID;
- target org/project/job identity;
- capture time;
- evidence items with stable IDs and digests;
- source/retained counts;
- truncation and continuation;
- redaction state;
- upstream operation/version;
- structured error when not OK.

Prefer official Salesforce DX MCP/CLI. Do not expose the unrestricted upstream MCP server to product agents if the host cannot intercept calls safely.

## Context and compaction

Persist context manifests and checkpoints at deterministic stage boundaries. If Cursor exposes `preCompact`, use it for observation/checkpoint triggering only; do not claim it prevents or rewrites compaction. After compaction/restart, rehydrate from checkpoint/evidence store and verify target/policy/version continuity.

## Output and review

The human report is rendered from structured claims/findings. `completed` requires:

- valid required evidence;
- valid references;
- no blocking deterministic lint;
- no blocking independent-review finding;
- no undisclosed truncation/ambiguity/host gap;
- valid output schema.

## Existing agents and commands

Use `migration/catalogs/agents/` as migration guidance. Existing specialists are catalog capabilities, not automatic native subagents. Do not invent skill citations merely to clear orphan warnings. Do not type all 67 legacy commands unless a command is touched or promoted.

---

# Required tests throughout

## Deterministic

- schemas and definitions;
- stable IDs;
- state transitions;
- context ordering/dedup/budget/overflow;
- evidence support/contradiction/confidence;
- pagination and result bounds;
- redaction and secret-shaped values;
- tool and shell policy;
- explicit target mismatch;
- project discovery/ambiguity/path safety;
- run bundle/replay;
- generated artifact drift;
- review package integrity/offline reconstruction.

## Product fixtures

For every product:

- happy path;
- missing mandatory input;
- unavailable optional enrichment;
- malformed evidence;
- target mismatch where relevant;
- oversized result/truncation;
- contradictory evidence;
- seeded unsupported draft reviewed;
- unsafe request/refusal;
- status/output validation.

## Context rot

- irrelevant skill distractors;
- long evidence;
- duplicate symptoms;
- long first task then unrelated second task;
- checkpoint/resume;
- compaction where host exposes it;
- instruction injection inside handoff/evidence.

## Security

- semicolons, pipes, `&&`, `||`, substitutions, nested shells, wrappers, aliases, reordered flags, legacy `sfdx`;
- unknown/misleading MCP tools;
- prompt injection in metadata, records, logs, comments, filenames, errors;
- wrong org/default changes;
- cached job/test from another org;
- secrets in stdout/stderr/JSON;
- non-scratch target in QA setup;
- cleanup failure path.

## Host

- actual plugin discovery;
- command discovery;
- actual subagent invocation;
- actual MCP path;
- actual output/reviewer behavior;
- install/uninstall;
- host capability record.

Do not call a manual check automated. Do not call a parser unit test an end-to-end product test.

---

# Documentation and product experience

Create concise user docs for:

- what SfSkills V2 is and is not;
- local Cursor install, verify, uninstall;
- fixture first-run;
- org authentication and explicit target selection;
- each product command with inputs/examples/statuses;
- standalone versus project/live/hybrid modes;
- local run data and deletion;
- product read-only boundary;
- scratch QA boundary;
- host/cloud limitations;
- legacy export and compatibility;
- current quality report and exact QA date;
- licensing/Marketplace limitation.

Do not duplicate changing counts manually. Generate them from canonical definitions/inventory.

The first useful fixture run should require one command and one artifact/job input. Users should never have to choose among dozens of agents.

---

# Quality and market proof

The product is not successful because it has more files, skills, agents, or tools.

Report:

- successful local installs;
- time to first useful result;
- required-finding recall;
- unsupported material claim rate;
- evidence validity;
- root-cause rank;
- status correctness;
- product mutation and policy violations;
- context files/tokens and tool bytes;
- truncation/compaction outcomes;
- second-run/repeat behavior where measurable;
- comparison with vanilla host/model.

Do not claim broad market share or generic accuracy. The 40% goal is sustained use within a deliberately measured early-adopter cohort, as defined in the research package.

---

# Stop conditions

Stop immediately and package a blocked review artifact when:

- you cannot prove the Salesforce target is a disposable scratch org before QA mutation;
- product code requires Salesforce mutation to function;
- a credential or secret may have entered tracked/review artifacts;
- baseline/user work would be destroyed;
- a required host/tool safety guarantee cannot be enforced and no restricted-broker fallback exists;
- a specification contradiction affects safety or product truth;
- required tests repeatedly fail and continuing would hide the defect.

For ordinary implementation choices, use the specification and best engineering judgment. Do not stop merely to ask whether to name a file differently.

---

# Required final return artifact

Build the exact ZIP required by:

```text
implementation/REVIEW_RETURN_CONTRACT.md
```

The return ZIP must be self-contained and reconstructable. At minimum it contains:

- Git bundle with baseline/head/tags;
- full sanitized source archive at head;
- exact changed files;
- exact test logs and exit codes;
- generated Cursor plugin and install evidence;
- actual Cursor host smoke evidence;
- representative full run bundles for every implemented product;
- scenario/benchmark results;
- context/evidence/security reports;
- scratch-org creation/deletion proof when run;
- requirement traceability;
- secret scan;
- checksums and package-validator output.

The review-package builder has two explicit modes:

- **completion mode**: must fail if the tree is dirty, a required test failed, a claimed file/log is absent, generated output is stale, checksums fail, the Git bundle cannot reconstruct the head, or secrets are found;
- **blocked mode**: may package failing required-test logs only when `MANIFEST.json.status` is `blocked` or `failed`, the last passing milestone/qualification is stated honestly, and all package-integrity, reconstruction, checksum, cleanliness, and secret-scan controls still pass.

Blocked mode never converts a failing implementation into a completed milestone.

Name the ZIP:

```text
sfskills-v2-cursor-return-YYYYMMDD-HHMMSS.zip
```

---

# Final response format

When finished or blocked, return only a precise implementation report containing:

1. Branch, baseline SHA, head SHA, local milestone tags.
2. Milestones completed and the highest truthful product qualification.
3. Products implemented and their status.
4. Architecture actually implemented and material deviations from SFAEF.
5. Subagents and actual host capability results.
6. Context/evidence/policy measurements.
7. Tests run with exact pass/fail counts.
8. Actual Cursor smoke results.
9. Live read-only org tests run or `not_run`.
10. Scratch-org scenarios run or `not_run`, with cleanup status.
11. Baseline comparison results.
12. Known limitations and P0/P1 defects.
13. Review ZIP absolute path and SHA-256.
14. Confirmation that no push, publication, PR, marketplace submission, or customer-org mutation occurred.

Do not hide warnings, skipped work, unrun live tests, or failed checks. Do not claim stable V2 unless the specification’s release gates actually pass.
