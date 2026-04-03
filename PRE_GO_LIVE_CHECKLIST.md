# PRE_GO_LIVE_CHECKLIST.md
# Salesforce Skills Library — Public Release Readiness

<!--
PURPOSE: Checklist of everything that must be done before this repo goes public on GitHub.
Each section is self-contained. An agent can execute sections independently.
Mark items DONE as they are completed.
-->

---

## 1. Repository Packaging (Must-Have)

### 1.1 Add LICENSE file
- [ ] Create `LICENSE` in repo root
- [ ] Use MIT or Apache 2.0 (owner decision)
- [ ] Copyright line: Pranav Nagrecha, 2026

### 1.2 Add .gitignore
- [ ] Create `.gitignore` in repo root
- [ ] Include at minimum:
  ```
  __pycache__/
  *.py[cod]
  *.pyo
  .venv/
  venv/
  .env
  *.sqlite
  .DS_Store
  .claude/
  .cursor/
  .idea/
  .vscode/
  *.local.json
  ```
- [ ] Verify `.claude/settings.local.json` (contains hardcoded `/Users/user/...` path) is excluded

### 1.3 Remove internal agent session docs
These files are internal build-session artifacts that will confuse public users:
- [ ] Remove or move `CODEX_HANDOFF.md` (agent briefing doc for Codex sessions)
- [ ] Remove or move `EXIT_DOC.md` (agent handoff summary between Codex and Claude)
- [ ] Remove or move `CURSOR_TEST_SCRIPT.md` (internal testing prompts for Cursor)

Decision: delete them, move them to a `.internal/` gitignored folder, or leave them and accept the transparency. Owner call.

### 1.4 Add CODE_OF_CONDUCT.md
- [ ] Create `CODE_OF_CONDUCT.md` using the Contributor Covenant (https://www.contributor-covenant.org/)
- [ ] Reference it from README

### 1.5 Add SECURITY.md
- [ ] Create `SECURITY.md` with vulnerability reporting instructions
- [ ] Even a simple "email me at X" is fine

---

## 2. README Rewrite (Must-Have)

The current README is written for agents building skills. It needs to speak to humans who find the repo on GitHub.

### 2.1 Update structure to follow this narrative arc:
- [ ] **What this is** — one paragraph, plain language. "A library of Salesforce practitioner skills designed to be used as AI coding assistant context."
- [ ] **Why it exists** — the pain point. Platform knowledge is scattered, tribal, and hard to codify for AI assistants.
- [ ] **How to use it** — three clear paths:
  1. Drop the repo into your AI IDE (Cursor, Claude Code, Copilot) as project context
  2. Search skills from the command line (`search_knowledge.py`)
  3. Browse the generated catalog (`docs/SKILLS.md`)
- [ ] **Skill domains table** — with accurate, current counts
- [ ] **Domain maturity indicator** — label domains as Mature / Growing / Planned so users know what to expect
- [ ] **How to contribute** — link to CONTRIBUTING.md
- [ ] **How it works** — brief architecture (registry, retrieval, sync pipeline)
- [ ] **License**

### 2.2 Fix stale metadata
- [ ] Update skill domain counts (README says "Admin: 15, Apex: 3, LWC: 1" but actual is Admin: 20, Apex: 19, LWC: 9, Flow: 6, etc.)
- [ ] Update version number (currently says 0.2.0, should be at least 1.0.0 for public release)
- [ ] Confirm "Last Updated" date is current

### 2.3 Add badges
- [ ] License badge
- [ ] Python version badge
- [ ] Skill count badge (optional — can be static)

---

## 3. CHANGELOG Update (Must-Have)

- [ ] The CHANGELOG last entry is 0.3.0 from March 13. There have been 46+ skills built since then.
- [ ] Add entries for all skills built after 0.3.0
- [ ] Write a 1.0.0 release entry summarizing the full library state at launch
- [ ] Keep the [Unreleased] section for post-launch work

---

## 4. Script UX Fixes (Should-Have)

### 4.1 Add --help to all scripts
These scripts currently **execute** when you pass `--help` instead of printing usage:
- [ ] `scripts/build_index.py` — add argparse or `--help` guard
- [ ] `scripts/build_knowledge.py` — add argparse or `--help` guard
- [ ] `scripts/build_registry.py` — add argparse or `--help` guard
- [ ] `scripts/generate_docs.py` — add argparse or `--help` guard

### 4.2 Document Python version
- [ ] Add minimum Python version to README (test and confirm — likely 3.9+)
- [ ] Add `python_requires` or a note in requirements.txt

---

## 5. Existing Skill Quality Improvements (Should-Have)

These skills are structurally complete but have thin practitioner content. A quick enrichment pass would bring them to release quality.

### 5.1 test-class-standards (Apex)
Path: `skills/apex/test-class-standards/`
Missing:
- [ ] Test data factory design patterns (multi-object factories, user setup, sharing context)
- [ ] Concrete `SeeAllData=true` anti-pattern example with failure scenario
- [ ] Mixed DML example (setup vs non-setup object in same transaction)
- [ ] `Test.isRunningTest()` guidance (when to use, when to avoid)
- [ ] Custom Metadata in tests
- [ ] Mocking beyond HTTP callouts (`Test.createStub()`, custom interfaces)
- [ ] More explicit RIGHT/WRONG code pairs

### 5.2 batch-apex-patterns (Apex)
Path: `skills/apex/batch-apex-patterns/`
Missing:
- [ ] Concrete scope-size tuning guidance (when to use 10 vs 50 vs 200, with reasoning)
- [ ] Batch chaining patterns and limits
- [ ] Schedulable + Batch integration
- [ ] Retry logic and partial failure handling
- [ ] Lock contention and `FOR UPDATE` in batch context
- [ ] Stateful misuse anti-pattern (large Map in instance vars across scopes)
- [ ] `Iterable<SObject>` vs `QueryLocator` decision criteria

### 5.3 sandbox-strategy (Admin)
Path: `skills/admin/sandbox-strategy/`
Missing:
- [ ] Refresh frequency guidance (when Full Copy vs Partial Copy)
- [ ] Sandbox allocation limits per edition
- [ ] Partial Copy template and data subset strategies
- [ ] Scratch org vs sandbox decision tree
- [ ] Concrete masking tool recommendations or implementation steps

### 5.4 approval-processes (Admin)
Path: `skills/admin/approval-processes/`
Missing:
- [ ] Delegated approvers and substitute approver setup
- [ ] Batch/mass approve patterns
- [ ] Queue-based approval routing
- [ ] Approval step conditions ("when does this step fire")
- [ ] Record editability during approval for different user personas
- [ ] `AutomatedProcess` user and system-context bypass behavior

### 5.5 apex-security-patterns (Apex)
Path: `skills/apex/apex-security-patterns/`
Missing:
- [ ] `stripInaccessible` edge cases (most fields stripped, `getRemovedFields()`, audit/logging)
- [ ] Guest user and community user sharing/FLS context
- [ ] Named Credential auth context vs user context
- [ ] `System.runAs` patterns for security tests
- [ ] User-mode vs system-mode SOQL tradeoffs and decision guidance
- [ ] `Schema.sObjectType.X.isAccessible()` vs `stripInaccessible` decision tree

### 5.6 flow-custom-property-editors (Flow)
Path: `skills/flow/flow-custom-property-editors/`
Missing:
- [ ] Exact `configurationEditor` registration in `.js-meta.xml`
- [ ] Event names and payloads (`configuration_editor_input_value_changed`)
- [ ] `builderContext` and `inputVariables` shapes
- [ ] How to test property editors in isolation

### 5.7 orchestration-flows (Flow)
Path: `skills/flow/orchestration-flows/`
Missing:
- [ ] Concrete stage/step/work-item implementation guidance
- [ ] Orchestration limits and instance behaviors
- [ ] API for monitoring and querying work items
- [ ] When to prefer orchestrations vs approvals vs custom Flow

---

## 6. Cross-Cutting Content Gaps (New Skills — Added to Backlog)

These are new skills added to `SKILLS_BACKLOG.md`. They fill gaps that cut across domains and are things a senior Salesforce person would look for.

- [ ] **ADM-025: order-of-execution** — Where triggers, flows, validation rules, assignment rules, workflow rules, and process builder fire relative to each other. Foundational.
- [ ] **FLW-014: flow-debugging-and-troubleshooting** — How to trace flow failures in production. Debug logs, `$Flow.FaultMessage`, Flow fault emails, debug interview reading.
- [ ] **FLW-015: flow-versioning-and-deployment** — Version management, activation/deactivation, deploying flows across sandboxes, retirement of old versions.
- [ ] **APX-020: governor-limits-quick-reference** — A pure reference card with every limit number, context (sync vs async vs batch), and the common patterns that hit each one.

---

## 7. GitHub Repository Setup (Do at Launch)

### 7.1 Repository settings
- [ ] Set repo to Public
- [ ] Add description: "Practitioner-written Salesforce skill library for AI coding assistants"
- [ ] Add topics: `salesforce`, `apex`, `lwc`, `flow`, `ai-skills`, `code-review`, `salesforce-development`
- [ ] Set default branch to `main`

### 7.2 Issue templates
- [ ] Create `.github/ISSUE_TEMPLATE/skill-proposal.md` (matches CONTRIBUTING.md reference)
- [ ] Create `.github/ISSUE_TEMPLATE/bug-report.md`
- [ ] Create `.github/ISSUE_TEMPLATE/improvement.md`

### 7.3 PR template
- [ ] Create `.github/PULL_REQUEST_TEMPLATE.md` matching the PR format in CONTRIBUTING.md

### 7.4 GitHub Actions
- [ ] Create `.github/workflows/validate.yml` that runs `python3 scripts/validate_repo.py` on PR
- [ ] Optionally run `python3 scripts/skill_sync.py --all` and check for dirty state

### 7.5 Release
- [ ] Tag the release: `git tag v1.0.0`
- [ ] Create a GitHub Release with summary of what's included
- [ ] Link to the generated `docs/SKILLS.md` catalog

---

## 8. SKILLS_BACKLOG.md Cleanup (Should-Have)

The backlog is a great internal tool but reads as "half the work isn't done" to a public audience.

Options (pick one):
- [ ] **Option A:** Rename to `ROADMAP.md` and reframe TODO items as "Planned" features
- [ ] **Option B:** Move to a GitHub Projects board and keep the repo clean
- [ ] **Option C:** Keep as-is and add a note at the top: "This is the project roadmap. Contributions welcome for any TODO item."

---

## Execution Order

Recommended order for an agent executing this checklist:

1. Section 1 (repo packaging) — mechanical, no judgment calls
2. Section 2 (README rewrite) — needs owner voice but can be drafted
3. Section 3 (CHANGELOG) — mechanical
4. Section 5 (skill quality) — content work, can be parallelized by domain
5. Section 6 (new skills) — already in backlog, pick up via normal workflow
6. Section 4 (script UX) — low priority, quick fixes
7. Section 7 (GitHub setup) — do at launch time
8. Section 8 (backlog cleanup) — owner decision

---

*Created: 2026-03-15*
*Purpose: Reference checklist for public GitHub release*
