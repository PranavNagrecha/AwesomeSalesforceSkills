# Feedback Log

Reverse chronological. See `README.md` for the triage verdicts and cadence.

---

## 2026-04-19 — Cursor invocation review (all 75 agents)

**Anchor:** `2026-04-19-cursor-invocation-review`
**Source:** External AI assistant (Cursor) — `/Users/pranavnagrecha/Desktop/agent-informal-invocation-analysis.md` (~1,170 lines, not committed). Same reviewer as the 2026-04-19 flow-builder entry below.
**Decision owner:** Pranav Nagrecha + Claude Opus 4.7.
**Decided on:** 2026-04-19.

### Context

Second external review from Cursor. Unlike the earlier flow-builder-only transcript, this one covers **the entire agent roster** alphabetically, with per-agent friction bullets. Structure:

1. 15-mode invocation catalog (MCP, informal chat, slash, bundle, queue, harness, PR review, subagent, advisory, etc.)
2. Per-agent section for all 75 folders — intent, contract snapshot, 2-4 risk/mitigation bullets, repeated QA PASS boilerplate.
3. Quick Picker table mapping "what you have" → "which channel."

Repo-ownership note: the user has explicitly decided we're **doubling down on MCP adoption** going forward. This shaped triage below.

### Verified before triage

- `requires_org` flag has only one runtime consumer: `scripts/smoke_test_agents.py`, where it's printed as a label (not execution-gating). Full sweep via grep confirmed no MCP / bundle / CLI gating on this flag.
- `lwc-auditor`, `security-scanner`, `soql-optimizer` all document `target_org_alias: no` in their Inputs tables — their frontmatter `requires_org: true` contradicts the body. Reviewer's flag is factually correct.
- `docs/installing-single-agents.md`, `docs/consumer-responsibilities.md`, `docs/MIGRATION.md` all exist and match the reviewer's characterization.

### Verdicts

#### 1. `requires_org` is mis-set on 3 static-scan agents

**Reviewer's claim:** "YAML marks `requires_org: true` but bundle on disk is usually enough" (re: `lwc-auditor`). Same pattern on `security-scanner` (force-app tree walker) and `soql-optimizer` (file/folder scope).

**Verdict:** ACCEPT.

**Shipped:** flipped `requires_org: true → false` on the three agents. Body specs were already honest (`target_org_alias: no (optional, enables X)`); this just makes the frontmatter agree with the spec. No behavior change, no refusal change — smoke test now correctly reports these as no-org-required.

**Provenance:** this commit.

---

#### 2. 15-mode invocation catalog is a real doc gap

**Reviewer's claim:** nothing in the repo consolidates the channels; it's scattered across `installing-single-agents.md`, `consumer-responsibilities.md`, per-agent AGENT.md Invocation sections, and `CAPABILITY_MATRIX.md`.

**Verdict:** ACCEPT.

**Shipped:** new `docs/agent-invocation-modes.md`. Adopted the catalog with attribution. Reframed with **MCP as Channel 1** (the canonical channel) because of the strategic priority on MCP. The doc explicitly lists what MCP currently exposes (20 tools) and what's missing (4 gaps tracked as next-round candidates: `list_deprecated_redirects`, `get_invocation_modes`, `automation_graph_for_sobject` probe tool, `emit_envelope` persistence helper).

**Provenance:** this commit.

---

#### 3. Agent-pair overlap disambiguation

**Reviewer's claim:** repeated per-agent friction — `permission-set-architect` vs `user-access-diff`, `orchestrator` vs `flow-builder`, `dev-skill-builder` vs `apex-builder`/`lwc-builder`, `validator` (ambiguous verb), deprecated-name muscle memory.

**Verdict:** ACCEPT.

**Shipped:** new `agents/_shared/AGENT_DISAMBIGUATION.md`. Five axes:

- Build-time vs run-time (most common misroute)
- Design vs audit vs diff
- Author skill docs vs emit code scaffolds
- "Validate" disambiguation (library-structure vs compile-deploy vs input-schema)
- `orchestrator` is the queue router, not ad-hoc work

Plus the full 19-entry deprecated-name redirect table.

**For MCP:** the doc includes a short "For MCP clients" section with the explicit rule "ask a clarifying question before `get_agent` when the request matches multiple agents on these axes."

**Provenance:** this commit.

---

#### 4. Per-agent vague-prompt mitigations (repeated bullets)

**Reviewer's claim:** every `design`+`audit` agent gets the same "needs scoping before blueprint" warning; every static scanner gets "bundle is enough"; every narrative agent gets "label as desk-level."

**Verdict:** DEFER.

**Rationale:** the repetition suggests a standardized warning schema rendered automatically in AGENT.md — but that's a bigger doc-generation refactor than we should ship reactively. For now the disambiguation doc (item 3) covers the most common misroutes; per-agent warning normalization can wait for a sprint where we own the full AGENT.md generator.

**Revisit:** 2026-Q3.

---

#### 5. Deprecated-folder @-mention hard redirect in informal chat

**Reviewer's claim:** `@validation-rule-auditor` still resolves to the stub; no automatic redirect in informal chat.

**Verdict:** DEFER — but add MCP-side fix to the queue.

**Rationale:** informal chat is the model's job — the `AGENT.md` stub + `AGENT_DISAMBIGUATION.md` give the model what it needs to redirect, and a doc-only solution is fragile. The real fix is at the MCP layer: a `list_deprecated_redirects` tool that surfaces the mapping programmatically so MCP clients can never route to a stub. Tracked in `docs/agent-invocation-modes.md` as MCP gap #1.

**Revisit:** next MCP sprint.

---

#### 6. QA PASS boilerplate repeated 75 times

**Observational, no action.** Reviewer's per-agent QA line is identical: "`validate_repo.py --agents` reports 0 errors; this folder is in the validated set." Accurate — our own smoke agrees (75/75). Not additional signal.

**Verdict:** NO-OP. Repetition noted; not a change request.

---

### Summary

| Item | Verdict | Commit |
|---|---|---|
| `requires_org` fix on 3 agents | ACCEPT | this |
| 15-mode invocation catalog | ACCEPT | this |
| Agent disambiguation map | ACCEPT | this |
| Per-agent warning schema | DEFER (2026-Q3) | — |
| Deprecated-name hard redirect | DEFER → MCP sprint | — |
| QA boilerplate | NO-OP | — |

**Net:** 3 accept / 2 defer / 1 no-op. Loop works as designed — external review in, triaged, shipped in one day.

**MCP queue (from this review, for the MCP double-down):**

1. `list_deprecated_redirects` — routes old names to routers automatically.
2. `get_invocation_modes` — surfaces `docs/agent-invocation-modes.md` as a tool resource.
3. `automation_graph_for_sobject` probe tool — lift the recipe from `agents/_shared/probes/` into an executable tool.
4. `emit_envelope` helper — implement `docs/consumer-responsibilities.md` persistence so every consumer gets it for free.

---

## 2026-04-19 — Cursor (another AI assistant) review of `agents/flow-builder`

**Source:** External AI assistant (Cursor 3.1.15) session transcript supplied by repo owner.
**Session path:** `/Users/pranavnagrecha/Downloads/cursor_flow_builder_functionality_in_sa.md` (not committed — summarized below).
**Decision owner:** Pranav Nagrecha (repo owner) + Claude Opus 4.7 (AI pair).
**Decided on:** 2026-04-19.

### Context

Cursor was asked three questions about `agents/flow-builder`:
1. How does it work? (descriptive)
2. Is the build good or bad? Does it work in real life? (evaluative)
3. If you had to make it better, what would you do? Research only. (prescriptive)

Cursor's summary was accurate and fair. It correctly distinguished the chat-style (`AGENT.md`) and gated harness (`GATES.md` + `scripts/run_builder.py` + `scripts/builder_plugins/flow.py`) paths, and correctly identified that **compile-valid ≠ correct behavior** as the honest gap. It then offered a prioritized improvement roadmap.

Full transcript is available from the session owner; below is the suggestion list with our verdict on each.

---

### Cursor's prioritized roadmap

#### P1 — "Automation-graph preflight + flow-analyzer integration"

> *"Before generating a new record-triggered flow, systematically pull all active flows + triggers + relevant invocables for the SObject. Move from 'refuse when messy' to 'informed merge/extend' with less human archaeology."*

**Verdict: ACCEPT (lightweight).**

**What ships now:**
- New shared probe recipe `agents/_shared/probes/automation-graph-for-sobject.md` — documents the SOQL for enumerating active flows + triggers + process builders + workflow rules + validation rules + invocables on a given SObject. Other agents (apex-builder, automation-migration-router) can opt into it without a plugin change.
- `agents/flow-builder/AGENT.md` gets a new **Step 0 — Automation graph preflight** that points at the probe and makes "have you looked at what already exists on this SObject?" an explicit, documented pre-decision-tree step.

**What does NOT ship now:**
- **Hard Gate B.5 refusal** when ≥3 overlapping flows are found. Reason: we want real-user signal on the right threshold before we make the harness refuse — a too-aggressive gate blocks teams that have legitimate reasons for multiple flows (per-record-type, per-profile). Tracked as a follow-up if the probe surfaces the pattern in the wild.

**Provenance:** commit `<pending>`.

---

#### P2 — "Flow Testing / API version matrix"

> *"AGENT.md explicitly does not emit Flow Test metadata — regression protection is still on you. Emit minimal Flow Test templates with a version matrix (supported on 60.0+ only)."*

**Verdict: DEFER.**

**Rationale:**
- Flow Test metadata API has meaningful gaps pre-Spring '24 (60.0); supported element coverage differs per release.
- The transcript itself flagged this as *research direction*, not a prescription — it said "research what is officially supported per release, what breaks across API versions."
- Emitting a test we can't run deterministically is worse than emitting nothing: failing tests that block valid deploys destroy trust faster than missing tests.
- **Revisit:** 2026-Q3, after Summer '26 release notes. At that point, if the Flow Test API is stable 60.0+ and covers record-triggered happy paths, promote to ACCEPT.

**Provenance:** no commit.

---

#### P3 — "Static limit-smell analysis"

> *"Detect loops containing DML, Get Records inside loops, nested loops, N+1 subflow calls. Narrative already lists these; automating P0/P1 flags in the envelope is research into XML shapes and false-positive rates."*

**Verdict: ACCEPT.**

**What ships now:**
- `FlowBuilderPlugin._check_flow_xml` extended to walk each `<loops>` element's downstream connectors and flag:
  - **P0:** DML elements (recordCreates/Updates/Deletes) reachable inside a loop body.
  - **P0:** Get Records (recordLookups) reachable inside a loop body.
  - **P1:** Subflow calls reachable inside a loop body (N+1).
  - **P1:** Nested loops (O(n*m) paths).
- Findings surface through the existing Gate C static path — no schema change needed.
- False-positive note: the walker uses a cycle-stopping DFS from each loop's `<nextValueConnector>` target, bounded by `<noMoreValuesConnector>`. Known trade-off: complex flows with asymmetric exit paths may miss a body element. Acceptable for v1 — real-user triage will tune it.

**Provenance:** commit `<pending>`.

---

#### P4 — "Mode unification + eval golden envelopes"

> *"AGENT.md describes probes, refusals, and deliverables; the harness enforces a different contract (schema, requirements file, grounding). Drift confuses users and evals. Documented 'modes' with explicit capability matrix."*

**Verdict: ACCEPT (doc-only for now).**

**What ships now:**
- New `agents/_shared/CAPABILITY_MATRIX.md` — a single table per builder agent listing:
  - What **Advisory mode** (chat-only, reads AGENT.md) enforces vs promises.
  - What **Harness mode** (`scripts/run_builder.py`) enforces vs promises.
  - The delta between them (what chat users lose when they skip the harness).
- Agents get a one-line pointer at the top of their AGENT.md linking to this matrix.

**What does NOT ship now:**
- **Single source of truth for inputs** across slash commands, MCP `get_agent`, and Cursor prompts. That's a real refactor (shared JSON schema imports across three call sites). Tracked for a later sprint.

**Provenance:** commit `<pending>`.

---

### Cursor's secondary research directions (not in the prioritized list)

#### "Retrieve-and-diff after validate"

> *"After validate succeeds, retrieve the same components and diff against emitted source (catches silent normalization). Worth a spike on whether this is stable enough for CI noise."*

**Verdict: DEFER.**

**Rationale:** Salesforce normalizes Flow XML on save in ways that are cosmetically noisy (element reordering, attribute normalization, default-value injection). A naive diff produces 80% false positives. Useful only with a structural-equivalence comparator, which is its own project.

**Revisit:** 2027-Q1 or earlier if a stable Flow-XML canonicalizer library lands in the community.

---

#### "Structured requirement IR + ambiguity scoring"

> *"Intermediate representation (triggers, entities, decisions, side effects, non-goals) that Gate C checks for internal consistency. NLP or rule-based missing dimension detection (idempotency, delete path, bulk volume, run-as, recursion)."*

**Verdict: DEFER.**

**Rationale:** The current Gate A (10-word floor) + Gate A.5 (approved REQUIREMENTS.md) catches 80% of bad inputs at 5% of the engineering cost. A structured IR is the right long-term move but changes the shape of `inputs.schema.json` across six builder plugins. Not this quarter.

**Revisit:** 2026-Q4, bundled with a larger inputs-schema refactor.

---

#### "Field-level grounding depth"

> *"Picklist value existence, required fields, encrypted fields, history tracking implications — what describe can prove vs what only compile catches."*

**Verdict: DEFER — split into two.**

- **Picklist value existence** — likely ACCEPT in a follow-up (we already have the probe, just not wired into Gate B).
- **Encrypted / FLS / history-tracking implications** — research direction; defer.

**Revisit:** next flow-builder sprint.

---

#### "Observability / Flow debug requirements in deliverables"

> *"Flow debug / interview workflows: what your flow-interview-debugging skill should require in every deliverable (debug steps, log patterns). Error monitoring: Custom Error Log vs Platform Events vs Apex invocable logging — governance and cost."*

**Verdict: ACCEPT-ADJACENT.**

**What ships now:** nothing — but noted that `skills/flow/flow-interview-debugging` (added 2026-04-18 in the 50-skill pack) already covers the debugging angle. The operational/ops-log angle is out of scope for the flow-builder agent itself; it belongs in a separate `ops-log-designer` agent that does not yet exist.

**Revisit:** when someone files an issue asking flow-builder to "also give me the error-logging strategy."

---

#### "Eval fixtures beyond happy path"

> *"Expand eval fixtures: overlapping RT flows, invalid subflow refs, missing fault paths, wrong API version, packaged namespace edge cases. Golden envelopes: expected confidence, grounding.unresolved, refusal codes for each fixture."*

**Verdict: PARTIALLY SHIPPED (pre-this-feedback).**

The 2026-04-19 prior commit (`155b6c4`) added 10 new negative fixtures (negative-ambiguous-input + negative-bad-skill) across admin/architect/data/devops/security-skill-builder, and graded 10 envelopes end-to-end. Flow-builder specifically already has three fixtures (live-green + negative-ambiguous + negative-bad). The edge cases Cursor listed (overlapping RT flows, invalid subflow refs, wrong API version) are net-new — those are next.

**Revisit:** 2026-Q2 — add one fixture per edge case listed.

---

### Summary of this entry

| Item | Verdict | Commits |
|---|---|---|
| Automation-graph preflight (shared probe + AGENT.md Step 0) | ACCEPT | pending |
| Flow Test metadata emission | DEFER (2026-Q3) | — |
| Static limit-smell analyzer | ACCEPT | pending |
| Capability matrix doc | ACCEPT | pending |
| Retrieve-and-diff after validate | DEFER (2027-Q1) | — |
| Structured requirement IR | DEFER (2026-Q4) | — |
| Field-level grounding (picklist subset) | DEFER (next sprint) | — |
| Observability deliverables | ACCEPT-ADJACENT (handled by existing skill) | — |
| Fixture edge cases | PARTIALLY SHIPPED + DEFER extras (2026-Q2) | `155b6c4` (partial) |

**Net:** 3 accept / 4 defer / 1 hybrid / 1 already-shipped.

**Follow-up trigger:** if a second independent reviewer flags Flow Test emission or structured IR before the revisit date, the DEFER converts to ACCEPT immediately per the review cadence rule ("on receiving similar feedback twice, upgrade").
