# Driver's log — case-onboarding (scenario 1: an entire project at `scale: project`), written retrospectively

Recorded by the dry-run operator (Fable) from the gate records, mock-deploy reports and milestone reports on file; the
build predates the driver's-log template, so times are the gate timestamps and reads are reconstructed from the gate notes.

## Gates and decisions so far

| Gate | Status | When (UTC) | By |
|---|---|---|---|
| `clarifications` | approved | 2026-09-05T15:50 | dry-run operator (Fable, answers from an |
| `plan` | approved | 2026-09-05T19:35 | dry-run operator (Fable, on the owner's  |
| `step:M1-S01` | approved | 2026-09-05T19:35 | dry-run operator (Fable; design-only, no |
| `milestone:M1` | approved | 2026-09-09T20:30 | dry-run operator (Fable; design-only, no |
| `step:M2-S01` | approved | 2026-09-05T21:15 | dry-run operator (Fable; design-only, no |
| `step:M2-S02` | approved | 2026-09-11T23:58 | dry-run operator (Fable; design-only, no |
| `step:M2-S03` | approved | 2026-09-12T00:38 | dry-run operator (Fable; design-only, no |
| `step:M2-S04` | approved | 2026-09-12T00:38 | dry-run operator (Fable; design-only, no |
| `step:M2-S05` | approved | 2026-09-12T01:22 | dry-run operator (Fable; design-only, no |
| `milestone:M2` | approved | 2026-09-12T03:10 | dry-run operator (Fable; design-only, no |
| `milestone:M3` | approved | 2026-09-12T06:24 | dry-run operator (Fable; design-only, no |
| `milestone:M4` | approved | 2026-09-12T09:23 | dry-run operator (Fable; design-only, no |
| `milestone:M5` | pending |  |  |

- Clarifications: 97 harvested; 84 blocking; 25 deferred (M3-S05 and M5-S02 blocked on them).
- Step runs recorded: 121; org-driven resets (mock-deploy findings that forced a rebuild): 8.
- Distinct org findings across the mock-deploy reports (F-ids): 18 — every one closed at the source (checker rule + gotcha + example) or recorded as a deploy prerequisite.
- Human decisions so far: the gates above (G1, G2, six step gates, four milestone gates) plus the operator amendments recorded in each step's `amendments[]`.
- Files a human read per gate: the gate notes name them — PLAN.md and the milestone report at each G, the step's deploy-order.md at each step gate, the mock-deploy summary before G3 onward.

## Phase notes (retrospective)

- Clarify: 97 questions in three rounds; 25 deferred. Too many for a human in one sitting — the ask/feature tiers (§ 3.1) exist because of this run.
- Plan: v5 after five verify rounds (blockers 19 → 11 → 13 → 1 → 0). The verifier's refutations were the highest-value reading of the whole run.
- Build: milestones M1–M4 built, tested, documented, verified; every milestone needed at least one org round-trip to find a platform rule no checker encoded. The org, not the library, was the last reviewer each time — which is what turned each finding into a checker rule.
- Human experience: the loop asked for a decision only at gates and printed the next command each time; the cost was reading long reports (M3 and M4 milestone reports > 1,000 words) and re-signing after amendments.

## Summary (§ 3.1 five-line block) — written at G5

- M5 compile (retrospective note, 2026-09-12): the workbook compile's own diligence run found 30 Section-6 rows without their decision-tree branch, one un-escaped regex cell, six requirements with only a positive manual test and 14 acceptance-criteria format errors — all written by earlier per-step doc-keeper runs and caught only when the four compile-time checkers ran on the collated documents. Repair pass at the compile; contract note: the per-step doc-keeper should run `check_workbook.py` on its own section rows before `documented`.
- M5-S04 repair pass (2026-09-12): UAT and AC checkers now clear (negative cases derived from the artefacts, not invented); the workbook checker's 8 remaining rows are queues and business-hours calendars that carry no automation choice — the checker's rule was over-broad, fixed at the skill before the tester runs.
- M5-S04 documented (2026-09-12): the five compiled documents are described by rows written after the compile, so they do not appear in the compiled workbook itself — a self-referential gap with no further compile step to pick it up; planner v6 should place the compile last and let it include its own rows. M5-S05 (build-level manifest) launched.
- M5-S05 built (2026-09-12): the build-level manifest — 29 types, 56 members, every member backed by a file. Manifest-mode dry run of the entire build: 60/60 except F-28 (the verified sender address the org must hold). F-43 closed: the Apex now travels in a manifest. Tester running; then doc-keeper, the M5 verifier and G5.
- M5-S05 tested (2026-09-12): the whole-tree manifest check (117 files, 56 members, 0 missing either way) — the step-tester playbook has no carve-out for a build-level manifest step, recorded as a playbook gap. Doc-keeper running; the M5 verifier and G5 follow.
- M5-S05 documented (2026-09-12): D-M5S05-01..05; every M5 step documented or blocked by design. The M5 milestone verifier is running; G5 is the thirteenth and last gate.
- M5 verified (2026-09-12T12:52Z): `not-ready` on the blocked-step rule alone (M5-S02); confidence LOW by the playbook's one-trigger branch; references 0 unresolved, merged manifest 56 members with zero drift, 3/3 milestone tests pass. Findings F-52..F-58; F-54 (HIGH) is the one that matters — the compiled workbook has no assumptions register (16 of 28 assumptions in no compiled document, 0 with an owner) and M5-S04's own manual test says it must. The step tester could not have caught it (manual test); the milestone verifier did. Operator decision: re-run M5-S04 (documented → running) against F-52/53/54/56/57 before G5 rather than accept F-54 as phase 2 — the data is in plan.json, the render is one doc-keeper run. Process notes: (a) manual acceptance tests are only ever read at the milestone, so a compile step whose contract is a manual test has no earlier tripwire — planner v6: give compile steps a checker that asserts the section exists; (b) `check_rtm.py`'s "0 orphans" is step→row only; member→row coverage needs a rule; (c) `assumptions[]` has no `owner` field in the schema — the manual test asks for one the data cannot hold.
- M5-S04 re-compiled (2026-09-12T13:35Z): F-54 closed (28-row assumptions register, steps constrained, owner role joined from the linked clarification — plan.json still has no owner field), F-57 closed, F-53 tagged phase 2 in the UAT pack, F-52/F-56 partial because their canonical fixes live in other steps' outputs (a compile run may not write there — contract gap: a milestone finding that spans steps has no single owner). Paused here by the owner; next is the M5-S04 tester, doc-keeper, then G5.
- M5-S04 re-documented (2026-09-12T16:17Z): D-M5S04-05..08 appended; G5 approved 16:19:33Z — build status done.

## Summary (§ 3.1 five-line block) — written at G5, 2026-09-12

1. Ask: a Service Cloud case-intake setup (queues, assignment, escalation, entitlements, email-to-case, Apex hooks, reports, a config workbook) — sized project by default (no `scale` existed when it started); 22 steps in 5 milestones, 2 blocked by design (Omni-Channel on deferred answers, sandbox strategy on inputs never supplied).
2. Human decisions: 13 gates (clarifications, plan, six step gates, five milestone gates) plus per-step amendments; each gate note names the report and the decisions it accepts. Files read per gate: PLAN.md, the milestone report, the step's deploy-order.md, the mock-deploy summary.
3. Cost: 97 clarifications in three rounds (too many — the ask/feature tiers exist because of this), plan v5 after five verify rounds, ~125 step runs, 8 org-driven resets; roughly seven days of elapsed operator time.
4. Quality: every milestone reached a manifest-mode dry run against a real org; the whole build validates 60/60 at API 67.0 except one named org prerequisite (F-28). 58 org and verifier findings (F-1..F-58); every one is a checker rule, gotcha or example in the library, or a recorded prerequisite. The milestone verifier caught what step testers cannot (F-54).
5. Driver's grade: the loop asked only at gates and always printed the next command; the pain was report length (M3/M4/M5 reports > 1,000 words), re-signing after amendments, and process gaps the operator had to bridge (compile-step manual tests with no tripwire; findings spanning steps with no owner; a results file that does not say which artefacts it tested). Design-only; nothing deployed.
- Reopened after done (2026-09-12T16:50Z) — F-59: the first tests-executing dry run (a capability that did not exist when G4/G5 were signed) fails all three Apex test methods for the reasons scenario 2 found today. The org's message names no field; the fix is the one already in the library. Human experience: two "done" builds were signed on compile-only Apex evidence — the milestone verifier must refuse compile-only evidence when the manifest carries ApexClass (contract item 45). Repair path as scenario 2: M4-S05 documented → running → tester → doc-keeper → run 5 → gate notes amended.
- Run 5 probe (2026-09-12T17:25Z) — F-60: the shipped Tier 1 persona cannot create a Case with a Subject. The access model granted the object and one custom field and nothing else, and every check in the loop was satisfied by that. It took an Apex test executing as the persona to expose it, which the loop could not do until `--test-level` existed today. This is the strongest argument in the retrospective for "the org is the last reviewer" — and for a checker that asks whether an object grant carries the field grants a persona needs. Repairs queued behind the cap: M2-S02 (field permissions), M4-S05 (system-mode seeding), M5-S05 (manifest member), run 6, gate notes amended.
- Envelope quality (2026-09-12T18:35Z): the M4-S05 repair agent's envelope used citation types (`agent`, `artefact`, `report`, `example_build`) and lowercase `confidence_impact` values outside the schema enum, and reported the envelope without saying it validated. Caught by the repo test that validates every live envelope. Operator normalized the enum values (original type kept in `original_type`). Playbook item: every agent's last step must be `validate_envelope.py` on its own envelope and the report must quote its output — the contract says so and three of today's Sonnet runs skipped it.
- Run 6 probe (2026-09-12T17:47Z): the persona can work a case (F-59/F-60 closed by the org). The last two failures are the test choosing "any active entitlement process" and getting the org's own — F-61, a one-line query fix, and a rule for the entitlement skill. Each org round-trip today cost ~4 minutes and removed one layer; no rebuild was launched without a probe first.
- Run 7 probe (2026-09-12T17:57Z) — F-62: with the persona finally able to reach the milestone, the service's milestone write is refused in the persona's user context and the refusal is swallowed by a partial-success DML the test never asserted on. Decision at the plan level: the stamp is a system-integrity write, so that one query and update move to an explicit system-mode boundary with a comment; the test asserts the result's errors are empty. First shipped-code change forced by the org in this build; every prior finding was metadata or test harness. Agent resumed with the diagnosis.
- Run 8 probe (2026-09-12T18:2xZ): Succeeded, 4/4, 84% — the build's Apex now passes in the org as the persona. Four org findings (F-59..F-62) in one afternoon on a build five milestone verifiers had passed; every one invisible without tests executing as the persona, and every one now a library rule or a recorded decision. The retrospective's headline changes: the loop's tests are necessary, the org is sufficient, and `--test-level` should have existed on day one.

## Reopened and re-signed (2026-09-12) — addendum to the five-line block

- What changed after G5: the first tests-executing dry runs (a capability that did not exist at signing) found four defects a compile could not show — F-59 (tests never ran as a permissioned user), F-60 (the shipped Tier 1 persona could not create a Case: object grant, one custom field, nothing else), F-61 (the test picked any active entitlement process and got the org's own), F-62 (the milestone stamp refused in the persona's context and swallowed by a partial-success DML). Repairs: M2-S02 (seven standard Case fields), M4-S05 (runAs harness, system-mode seeding, named process, an explicit system-mode boundary on the milestone write — the build's only shipped-code change), M5-S05 (+1 member). Run 8 probe: Succeeded, 4/4, 84.4%; run 9 as shipped: 61/61 with F-28 the only error.
- Cost of the reopen: 9 dry runs (4–9 plus probes), 8 Sonnet runs, 2 library commits, about three hours of operator time alongside scenario 2's reopen.
- Grade revision: line 4 of the block ("every finding is a checker rule…") now includes F-60's rule (PSVP-FLS-01), which fires on the pre-repair permission set; line 5's list of process gaps gains "no Apex test executed as the persona until today", the largest gap the loop had. G4 and G5 re-signed on this evidence without fresh verifier passes (budget) — the gate notes carry the delta, and a future session should re-run the M4 and M5 verifiers.
