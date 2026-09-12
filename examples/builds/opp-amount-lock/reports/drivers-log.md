# Driver's log — opp-amount-lock (scenario 4: a one-line ask at `scale: ask`)

Recorded by the dry-run operator (Fable) driving as the requester (Sales Ops). One block per phase; the § 3.1
five-line summary closes the file when the build is done.

## Clarify (2026-09-12 06:00–06:15)

- Sizing line printed by the clarifier: `scale: ask (D=1 metadata type, S=1 skill with question table, O=1 object, integration=no; no override)`.
- Questions: 13 harvested (admin/validation-rules 7 rows + admin/requirements-gathering-for-sf 7 rows, 1 dedup); **7 blocking put to the human, 6 pre-filled from defaults**. One round. The human answered all 7 in `CLARIFICATIONS.md` and ran `ingest-answers` once.
- Files the human read: `CLARIFICATIONS.md` (1). Minutes: ~4 to answer.
- Friction (product defects, each fixed or filed the same day):
  1. `init --force` crashed with `SameFileError` when re-initialising to record the tier → `set-scale` writer added (11cac2999) and the same-file copy skipped.
  2. Contract § 3.1's own worked example cited `admin/formula-fields-and-rollups`, which does not exist (→ `admin/formula-fields`, a4a07d869).
  3. The clarifier's printed next command was `gate go` straight after the answers; the CLI refused the plan half (plan not verified) AFTER writing the clarifications half — the alias was not atomic, and the ask-scale order is answer → plan → verify → go. Fixed the same day; G1 nevertheless stands as approved by the requester's own answers.
  4. Judgment call the AGENT.md text does not settle: two adjacent Opportunity skills surfaced on vocabulary and were excluded under the citation-quality bar (kept S=1); a stricter reading triples the question count with rows about splits/teams/forecasts.
- Human decisions so far: 1 (the `clarifications` gate, written by the half-applied `go`).

## Plan (06:20–06:35)

- Planner (Sonnet) wrote 1 milestone / 1 step / 4 tests via `set-plan`; `validate` 0 WARN; `render` emitted `RUN.md`. No human action in this phase.
- Friction filed: (5) the six pre-filled informational rows (Q8–Q13) stay `open` in plan.json and render with a blank `Answer:` — § 3.1 says they "land pre-filled"; the planner carried them as `assumptions[]` instead. CLI/clarifier fix needed: record the default as the answer with `default_source`. (6) `human_gate` forced `false` on a step that grants a bypass permission — the single `go` gate must make that visible (RUN.md lists the permission set). (7) the planner's literal `adr_required: true` on two small decisions overstates ADR candidacy.

## Verify + go (06:35–06:40)

- Verifier (Opus): one round, three lenses pass, 10 warnings, 0 blockers → `verified`. No human action.
- Human decision 2: `gate go approve` — signed after reading `RUN.md` (65 lines) and `PLAN.md`. Files read so far: 3. RUN.md put the bypass permission-set grant in front of the human (W1), which is the point of the ask tier's single gate.
- Friction filed (from the verifier): (8) `amend-step` is refused at `planned`/`verified`, so § 3.1's "fix a testability refutation in place" is unreachable when it is needed; (9) `human_gate` is not amendable at all; (10) plan-verifier's Step 4 table / security guard and metadata-builder's Step 2 table had no ask branch — fixed the same day; (11) `RUN.md` listed the human's own answers under "Defaults applied (source: none)" — render fixed the same day; (12) the `go` alias re-stamped the already-approved clarifications gate with a new timestamp (harmless, noted).

## Build (06:42–07:00)

- Runner (Opus, metadata-builder inline): 3 artefacts + package.xml, both checkers exit 0, `built` — then RESET by the operator: the artefact carried a four-clause formula the operator had restated in the launch brief, while the plan input held five (with a blank guard). Lesson recorded: the operator must not restate plan inputs in a brief; plan inputs are the authority.
- Operator dry-run probe on a scratch copy (the human's own validation, not an agent's): the plan's guard `NOT(ISBLANK(StageName))` — copied from the skill's own "GOOD" block — does not compile ("Field StageName is a picklist field. Picklist fields are only supported in certain functions."); `NOT(ISBLANK(TEXT(StageName)))` validates 3/3. Skill defect filed and fixed the same day (validation-rules SKILL.md GOOD block + new checker rule VR-PICK-01). This is scenario 4's first flywheel turn.
- `amend-step` (inputs formula + test 0 description) applied at `pending`; rebuild requested from the same runner with context intact.
- Friction filed: (13) `set-status … running` without `--envelope` records a dangling `envelopes/<step>/running.json` path; (14) a passing `checker` test can carry a stale finding-count in its description — descriptions should assert exit/blocking counts, not advisory counts; (15) runner/builder have no route to reconcile an operator correction with a plan input other than stopping — correct behaviour, but the operator needs `amend-step` in hand before relaunch.

## Rebuild + test (07:45–08:00)

- Rebuild (same runner, context intact via message): rule generated from the plan input, byte-for-byte round-trip; CustomPermission/PermissionSet/package.xml unchanged. Tester (Sonnet): 4/4 pass (VR checker exit 0 with one INFO; CP checker output matches the plan's declared text verbatim). No human action.
- Friction filed: (16) step-tester's playbook does not say in one place what to do when it notices a milestone-level manual test while working a step (it inferred "record, don't tick" from the out-of-scope refusal row) — one sentence added to the playbook the same day.

## Document (08:05)

- Doc-keeper (Sonnet) at ask: RUN.md re-rendered (status tested, latest run passed), step `documented`; workbook and traceability skipped by design. No human action.
- Friction filed: (17) RUN.md printed an aggregate pass line, not the per-checker exit codes § 3.1 promises — renderer fixed the same day; (18) § 3.1 froze `decisions.md` at ask, leaving four real decisions homeless (envelope only) — rule changed the same day: decisions.md is appended at every scale, only workbook + traceability are skipped at ask.

## Verify milestone + accept (08:20–08:30)

- Milestone verifier (Opus, one page): `ready-with-findings`, F-01..F-11 (three P1: unassigned permission set, no sfdx-project.json for the printed sf command, PermissionSet full-replace on a taken name). Human decision 3: `gate accept approve` after reading `RUN.md` and `reports/MILESTONE-M1-REPORT.md` (files read: 5 in total across the run).
- Friction filed (from the verifier): (19) the sizing rule counts metadata types before the answers create supporting artefacts — § 3.1 to say D counts types that need their own step; (20) `set-milestone`'s printed hint is not scale-aware (`milestone:M1 approve` vs the promised `accept`); (21) milestone-verifier Step 10 HIGH is unreachable at ask (a milestone may declare only a manual test) and Step 11's example hard-codes `envelopes/M2/`; (22) "one page" vs eleven findings — evidence moved to the envelope.

## Summary (§ 3.1 five-line block)

```text
scale:     ask (D=1 S=1 O=1 X=no; override: none — verifier later counted D=3 from the answers; accepted as ask)
questions: 7 asked · 6 defaults applied · 0 deferred · rounds 1
gates:     go approved 06:39 (clarifications half at 06:13 by a non-atomic alias, fixed) · accept approved 08:30 · rejections 0 · re-plans 0 · rebuilds 1 (operator error, and a skill defect found by the org)
reads:     CLARIFICATIONS.md, RUN.md, PLAN.md, RUN.md (again, after rebuild), MILESTONE-M1-REPORT.md (5 reads, 4 distinct files)
minutes:   clarify ~15 · plan+verify ~30 · build+test ~75 (incl. reset, probe, rebuild) · document+verify ~40 · read+decide ~12 · total ~170 wall-clock, of which the human's share ≈ 20
```

Verdict on the human experience: three decisions and four files is the right shape for a one-line ask; the wall-clock was dominated by 22 product defects found and fixed the same day (CLI ×8, agent playbooks ×7, skills ×2, contract ×5). The second ask-scale run should take a fraction of this.
