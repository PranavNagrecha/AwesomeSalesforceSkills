# Driver's log — tier2-webhook (scenario 2: an integration feature; expected `scale: feature`)

Recorded by the dry-run operator (Fable) driving as the requester (Support Engineering lead). Applies scenario 4's
lessons: plan inputs are never restated in a brief; format questions are settled by an operator dry-run probe before
any rebuild; the tier is whatever the printed sizing rule says.

## Init (09:00)

- `init` without `--scale`; the clarifier sizes it. Requirement: Named Credential + External Credential (API key),
  Apex callout (queueable, retry, failure record), platform event + publish, trigger/flow on the escalation.

## Clarify (10:00–10:20)

- Sizing line printed a priori: `scale: feature (D=6 metadata types, S=7 skills with question tables, O=3 objects, integration=implied; no override)` — correct by the table. The clarifier then re-tiered to `project` because 24 of 45 harvested rows were blocking, applying the ask tier's eight-blocking test "by analogy". The operator reverted to `feature` with `set-scale --force`: § 3.1 states that test for ask only, and every one of the 24 is a real integration question (auth model, idempotency, retry classes, failure record shape, volume, who resends).
- Friction filed: (1) § 3.1 has no feature-tier statement on blocking-question count or rounds — fixed the same day (no cap; one round; re-tier only when the D/S/O/X recount crosses a threshold); (2) `set-clarifications` pre-fills informational defaults only at ask, while the tier table implies feature inherits it — CLI fixed the same day; (3) the clarifier's playbook uses `owner_hint` and a null `owner_role`, neither of which the schema defines — playbook aligned to the schema (`asked_by`, non-empty `owner_role`).
- Questions: 45 harvested from 8 skills + 2 decision trees; **24 blocking put to the human, 21 informational**. Human reads so far: `CLARIFICATIONS.md` (1).

## Answer + G1 (10:20–10:35)

- The requester answered 24 blocking questions in `CLARIFICATIONS.md` in one round (~12 minutes of reading and typing), ran `ingest-answers` once, and signed `gate clarifications approve` — human decision 1. 20 defaults were pre-filled by the CLI after the feature-tier fix; 1 informational row without a default stays open for the planner to carry as an assumption.
- Reads so far: `CLARIFICATIONS.md` (1). Planner (Opus) launched at feature tier: one milestone, ≤ 5 steps.

## Plan (10:35–11:30)

- Planner (Opus): 1 milestone, 5 steps (the feature ceiling exactly), 14 decisions (11 on a quoted tree branch), 12 assumptions; `validate` 0 WARN. Two requester answers were refuted by the library and re-decided in the plan: Q23 (Automated Process holds no permission sets — D14 widens the assignee set) and Q9 (publish-then-callout in one Queueable is unbuildable — D10 moves the publish to the escalating transaction). No human action; verifier (Opus) launched.
- Friction filed: (4) § 4 / metadata-builder Step 2 name no home for NamedCredential / ExternalCredential — reasoned onto `access` via the step's skills[]; tables should name the types; (5) the five-step ceiling collides with the mandatory Apex manifest (`docs`) step — one of five is consumed by the aggregating package.xml, so a feature with three Apex features cannot fit; proposal: the manifest step does not count toward the ceiling; (6) "ERROR-only exit policy" is a different flag per checker (bare / `--min-severity ERROR` / absence of `--strict` / `--fail-on HIGH`) and two checkers expose no flag and exit 1 on WARN; (7) feature tier has no compiled artefact view between PLAN.md and the doc-keeper's workbook; (8) `check_apex_scheduled.py` and `check_apex_scheduled_jobs.py` coexist (one is a delegating alias) and the playbook's `ls check_*.py` cannot tell them apart.

## Verify round 1 (11:30–12:40)

- Verifier (Opus): executability pass; grounding FAIL (PV-001 no FLS on Case.Tier2_Notified_At__c; PV-002 queue-name → Group Id lookup ungrounded — apex/apex-hardcoded-id-elimination has the example but was not cited); testability FAIL (PV-003 M1-S04 has no test that can fail on an empty directory). 9 warnings. `plan-rejected`, v1 archived; planner resumed for v2 (round 2 of 2). No human action.
- Friction filed (from the verifier): (9) plan-verifier's playbook carries ask carve-outs but none for feature (org-only manual test row; CRITICAL threshold undefined at feature); (10) `amend-step` is refused at `planned`/`plan-rejected`, so a testability-only defect forces a full re-plan at every tier; (11) the feature Gates cell under-counts — a `human_gate: true` step legitimately adds a `step:` gate; (12) the envelope `outcome` enum cannot express `plan-rejected`; (13) the rejection is invisible in `PLAN.md`/`status` ("blockers: none" under `plan-rejected` reads as rejected-for-no-reason); (14) checker exit forms differ (four flag styles; 7 of 9 exit 0 on an empty dir), so "a test that can fail" is an accident of which checker a step cites; (15) branch quotes transliterated by the planner (→ vs ->) — the grounding row needs a normalisation clause.

## Re-plan v2 (12:40–13:20)

- Planner (resumed with context): PV-001 → field permission on Case.Tier2_Notified_At__c in Tier2_Webhook_Admin (A13/A14); PV-002 → apex/apex-hardcoded-id-elimination cited with the Group-lookup shape bound in inputs; PV-003 → M1-S04 declares the error-handling checker that fails on an empty dir; W1/W2/W3/W6/W7 folded. `validate` 0 WARN; version 2. Verifier resumed for round 2 (last). No human action.
- Friction filed: (16) `check_apex_hardcoded_id_elimination.py` takes `--src`, a fourth argument form — the skill PV-002 required could not declare its checker.

## Verify round 2 + G2 (13:20–13:55)

- Verifier (resumed): all three blockers cleared (each re-probed, not trusted); 9 warnings; `verified`. Human decision 2: `gate plan approve` after reading `PLAN.md`. Reads so far: `CLARIFICATIONS.md`, `PLAN.md` (2). M1-S01 runner (Opus) launched.
- Friction filed: (17) three of ten checkers have no severity control and seven exit 0 on an empty tree — "a test that can fail" is an accident of which checker a step cites; contract § 5 paragraph added the same day; (18) the rejection was invisible in the rendered views — `render`/`status` now surface verification blockers (fix in flight); (19) `amend-step` at `planned`/`plan-rejected` for inputs/tests (fix in flight).

## Build M1-S01 (13:55–14:40)

- Runner (Opus, metadata-builder inline): 17/17 outputs, three checkers exit 0 first pass, `built`. Cross-step finding: M1-S02's field-permission input covered the required `Status__c`, which the platform refuses to deploy (api_meta L95020) — the operator amended M1-S02's inputs (eleven fields) while it was still `pending`; no rebuild needed. Tester (Sonnet) launched.
- Friction filed: (20) an `object-model` step writing twelve fields cited no field-creation skill — `admin/custom-field-creation` holds the FieldType enum the builder needed; planner reading-list gap, recorded in the envelope only because no writer can add a skill to a claimed step; (21) the persistence clause (Wave 10 docs/reports pair) contradicts build-dir-only invocations — contract needs a build-scoped clause; (22) the runner's confidence table has no row for "the build under me is MEDIUM"; (23) zsh word-splitting bit a checker loop (unquoted `$var`) — playbooks that script declared commands must quote-and-eval.
- Skills cited by M1-S03/M1-S04 below bar at this moment: apex/trigger-framework 7/12 (fix running), apex/test-class-standards 8/12, apex/apex-hardcoded-id-elimination 8/12, apex/apex-outbound-email-patterns 8/12, apex/error-handling-framework 9/12 — being raised before those steps run.

## Document M1-S01 + step gate M1-S02 (14:40–15:00)

- Doc-keeper (Sonnet): decisions D-M1S01-01..08, traceability 7 rows (first keyed by Q id — checker rejected the key form; re-keyed to REQ-001..007 with the Q id as source, the convention the case-intake build uses); workbook skipped at feature (recorded). Human decision 3: `gate step:M1-S02 approve` after reading the step in `PLAN.md` — the credential, named credential and permission-set grant. Reads so far: `CLARIFICATIONS.md`, `PLAN.md` ×2 (3).
- Friction filed: (24) the doc-keeper playbook lets a build without an elicitation pass drift to Q-ids as `req_id`; the convention (mint REQ ids, Q in source) needs one sentence in Step 5; (25) `metadata-api-coverage-gaps` is cited by the tester playbook for manifest exclusions but its content is deploy-mechanism gaps — citation-fit gap.

## Build M1-S02 (15:00–15:15)

- Runner (Opus, metadata-builder inline): External Credential (SecuredEndpoint, named principal, custom AuthHeader), Named Credential, permission set with 12 FLS rows (Status__c excluded), both checkers exit 0, `built`. Tester (Sonnet) launched; operator dry run of M1-S01+M1-S02 run alongside.
- Friction filed: (26) the clarifier never asked the on-call tool's endpoint URL or the credential parameter name the API key is stored under — the requirement says "HTTPS REST endpoint, API key" and no cited Questions-to-Ask row asks for the URL or the parameter name; `apex/apex-named-credentials-patterns` needs both rows; the builder shipped a placeholder URL and an AuthHeader with no `parameterValue` rather than invent them; (27) the skill's own example carries the same dangling `$Credential.<EC>.ApiToken` reference with no declared parameter.

## Dry run 1 + M1-S02 reset (15:15–15:30)

- Operator dry run of M1-S01 + M1-S02: 22/23 ok; the External Credential needs the AuthHeader `parameterValue` and the permission set's principal grant cascaded (S2-F-02/S2-F-03). Tester (Sonnet) had passed the step 5/5 — no library check sees a missing parameter value.
- The fix needed two facts the clarifier never asked (endpoint URL, key parameter name). Because the step gate was already signed, admitting them cost the human two extra decisions: `gate step:M1-S02 reject` (decision 4) → `amend-step` → `gate step:M1-S02 approve` (decision 5). The CLI's guard is right (an input change invalidates a signature); the cost is the unasked question, not the guard. Runner resumed for the rebuild.
- Human decisions so far: 5. Reads: 3 files.

## Rebuild M1-S02 + dry run 2 (15:30–15:45)

- Runner (resumed): two values changed from the amended inputs, permission set and package.xml byte-identical. Operator dry run 2 of M1-S01 + M1-S02: 23/23 — S2-F-02 closed on deploy, S2-F-03 cleared with it. Tester (Sonnet) re-running the step. No human action in this phase.
- Friction (from the runner): (28) both declared checkers passed the credential the org rejected — no library rule sees a missing AuthHeader `parameterValue`; skill fix queued (rule + two Questions-to-Ask rows + the example's dangling `ApiToken`).

## Document M1-S02 (15:45–16:00)

- Doc-keeper (Sonnet): decisions D-M1S02-01..06, traceability REQ-008/009 (REQ-005/006 amended in place), workbook deferred at feature. M1-S03 runner (Opus) launched; M1-S04 runner still building.
- Friction filed: (29) build-doc-keeper Step 8 says rows are "keyed by req_id plus step_id", which contradicts `check_rtm.py`'s req_id uniqueness — the doc-keeper wrote duplicate rows, hit the error, and corrected to the case-intake precedent (multi-step requirements stay on the originating row; later steps fold into artefact_paths/test_result); playbook sentence to fix; (30) the workbook at feature is "optional" with no rule for when the first step should start it — the doc-keeper deferred rather than begin piecemeal.

## Build M1-S04 → P0 → plan amendment (16:00–16:20)

- Runner (Opus, apex-builder inline): Schedulable + Queueable + test, three checkers exit 0, `built` — with a P0 it refused to decide: `include_logger: true` wired ApplicationLogger, which needs Application_Log__c + Logger_Setting__mdt that no step ships (Q16: "no log object"); and the alert recipient was unbound (Q24 named a team). Operator/requester decided at the plan: `include_logger: false` on BOTH Apex steps (the failure record is the visible log), recipients = active assignees of Tier2_Webhook_Admin. M1-S04 reset → amended → rebuilding; M1-S03 amended while still pending and its runner told to re-read the step. No gate involved (inputs on un-gated steps), so no extra human decision counted.
- Friction filed: (31) `templates[]` and `outputs[]` can disagree with no gate — the provenance rule pulls template classes into a step that `check-outputs` never sees, and `validate` does not warn when two Apex steps share a template with no owning step; (32) a runner-discovered P0 has no status distinct from `built` — it reaches plan.json only as prose in `runs[].result`; (33) the planner wired a logger whose own skill lists two hard object prerequisites without planning them — planner Step 6 should cross-check a template's declared prerequisites (error-handling-framework code-examples § 9) against the plan's outputs.

## M1-S03 blocked → remedy B (16:20–16:35)

- apex-builder refused (REFUSAL_INPUT_AMBIGUOUS) before writing a file: three mandated templates (TriggerHandler → TriggerControl → Trigger_Setting__mdt; BaseService and HttpClient → ApplicationLogger → Application_Log__c + Logger_Setting__mdt) cannot ship because no step ships those objects. The right refusal: the org would have said the same at deploy. Operator/requester decided remedy B at the plan (drop the three templates; build-local trigger/handler with a static guard, direct HttpRequest against `callout:OnCall_Tool`, no appended path) — amended while `blocked`, then `blocked → running`, runner resumed. Not a gate decision.
- Friction filed: (34) `templates[]` is validated for existence, never for what a template needs — both Apex steps of this build were blocked by that gap after plan v2 passed three lenses; `validate` should grep each cited `templates/apex/**` file for other template classes and `__c`/`__mdt` tokens and WARN when the closure is covered by no step's `outputs[]`; (35) the feature ceiling carves out only the manifest step, but § 4's Apex row prescribes an Apex-foundations step for shared templates — a correctly shaped plan here wanted six functional steps; (36) `amend-step` replaces `inputs` wholesale, so a superseded key (`recipients`) survived beside the new `alert_recipients` — a `--prose-only`/key-level amendment or a "superseded_by" convention is needed.

## Document M1-S04 (16:35–16:50)

- Doc-keeper (Sonnet): D-M1S04-01..07, REQ-010; workbook not started (build-wide choice at feature). M1-S03's artefacts landed mid-run from the concurrent remedy-B build; the append-only, re-read-before-append discipline held. Named-credentials skill fix (S2-F-02) launched in the freed slot.
- Friction filed: (37) two agents writing the same build's shared files (decisions.md, traceability.md, plan.json via CLI) is safe only by convention — the contract should state "append-only + re-read before append" for shared markdown and note the CLI's whole-file read-modify-write on plan.json.

## Build M1-S03 (remedy B) + dry run 3 (16:50–17:40)

- Runner (Opus, apex-builder inline): 20 declared outputs + 5 undeclared (two verbatim template copies, deploy-order.md), three checkers exit 0, no Id literals, `built`; tester passed 5/5. Operator dry run 3 of M1-S01..S04: M1-S04 compiled clean; M1-S03 failed on two roots the org alone could see — `URL.getSalesforceBaseUrl()` removed after API 58 (freestyled from memory, no cited skill carries it) and a SOQL filter on a LongTextArea in a test. Reset → runner resumed with both fixes. No human decision.
- Friction filed: (38) no library checker can compile Apex — the org is the only compiler in the loop, so every Apex step costs one dry-run round trip minimum; a cheap partial: a checker rule for known-removed methods (getSalesforceBaseUrl) and a rule for WHERE clauses on fields whose manifest type is LongTextArea/Html; (39) `apex/pdf-generation-patterns` still teaches the removed method; (40) `apex/apex-named-credentials-patterns` § 6 and the callouts checker disagree on setMock/startTest ordering.

## Rebuild M1-S03 (run 3) + dry run 4 (17:40–17:50)

- Runner (resumed): three call sites changed, 21 files byte-identical. Operator dry run 4 of M1-S01..S04: 38/38 — S2-F-04 and S2-F-05 closed by the org; all of the feature's Apex now compiles. Tester (Sonnet) re-running M1-S03. No human decision.
- Lesson recorded by the runner (S3-F-06): a corpus grep proves a method name is spelled somewhere, not that it is legal at the step's apiVersion — attestation is necessary, not sufficient; the org remains the only compiler in the loop.

## Test M1-S03 (run 3) + document (17:50–18:10)

- Tester (Sonnet): 5/5, and it grep-verified both org fixes landed. The operator re-worded manual clause (b) by prose-only amendment (it still named the dropped HttpClient template — the reviewer would have looked for a file that isn't there). Doc-keeper (Sonnet) launched. No human decision.
- Friction filed: (41) a manual test's prose can name a mechanism the plan later drops — the prose-only path exists, but nothing flags the staleness until a tester reads it; the amend-step that dropped the template should have prompted a prose review of tests naming it.

## Document M1-S03 + M1-S05 launch (18:10–18:30)

- Doc-keeper (Sonnet): D-M1S03-01..08, six REQ rows minted, seven updated; RTM 16 rows, 0 orphans. Its D-M1S03-08 ("the prose-only amendment was a no-op") was partly a false alarm: the manual clause had changed; what still named the dropped template was the checker test's description, now re-worded too. M1-S05 (build manifest) runner launched. No human decision.
- Friction filed: (42) a prose-only amendment's success line does not print the changed text, so a reviewer cannot see what changed without diffing `amendments[].before` — print a one-line diff summary.

## Build M1-S05 + manifest dry run (18:30–18:55)

- Runner (Opus, metadata-builder inline): build-level package.xml, 7 types / 33 members / no wildcards, TestDataFactory de-duplicated by hash; deploy-order.md reconciles the plan's input order (permission set before its fields) to the order that deploys. Operator manifest-mode dry run 5 (milestone M1): 38/38 — the shape a real deployment uses. Tester (Sonnet) running. No human decision.
- Friction filed: (43) the step's `inputs.members` listed 11 ApexClass and the artefacts carried 13 (the two template copies from the rebuilds) — runner Step 5 says inputs win, the step's manifest test says artefacts win; the manifest step must follow the artefacts, and the contract should say so for aggregating steps; (44) the plan's input deploy order put PermissionSet ahead of the fields it grants — planner rule: field permissions after fields.

## Test + document M1-S05 (18:55–19:10)

- Tester (Sonnet): 4/4 incl. the build-wide two-way manifest check (33/33, TestDataFactory re-hashed across both steps and the template). Doc-keeper launched; milestone verifier next. No human decision.

## Document M1-S05 + milestone verification (19:10–)

- Doc-keeper (Sonnet): D-M1S05-01..05; RTM 16 rows, 0 orphans; all five steps documented. Milestone verifier (Opus) launched — its one-page-plus report is the `milestone:M1` gate's evidence.

## Verify milestone + accept (19:10–19:50)

- Milestone verifier (Opus): `ready-with-findings`, 12/12 cross-step checks resolved by reading and re-hashing, S2-F-06..10 (the P1: no Apex test has ever executed — the dry run ran at no-test level). Human decision 6: `gate milestone:M1 approve` after reading `reports/MILESTONE-M1-REPORT.md`. Reads: 4 distinct files (CLARIFICATIONS.md, PLAN.md, the step's deploy-order.md at the step gate, the milestone report). Build `done`.
- Friction filed: (45) `scripts/mock_deploy.py` cannot run Apex tests during validation — a validate-only deploy can (`--test-level RunSpecifiedTests`); flag to add; (46) milestone-verifier's report-shape and HIGH carve-outs are ask-only — feature clauses missing; (47) no CLI writer for a documented step's stale `inputs{}` keys (prose-only reaches notes/test descriptions only) — three items reached the gate uncorrectable.

## Summary (§ 3.1 five-line block)

```text
scale:     feature (D=6 S=7 O=3 X=implied; override: none — clarifier re-tiered to project by a rule that did not exist for feature; operator reverted)
questions: 24 asked · 20 defaults applied · 0 deferred · rounds 1
gates:     clarifications 10:20 · step:M1-S02 15:00 (rejected + re-approved after an unasked fact) · plan 10:23 (round 2) · milestone:M1 19:50 · rejections 1 (own) · re-plans 1 · rebuilds 5 (org-found: 4; plan-found: 1)
reads:     CLARIFICATIONS.md, PLAN.md ×2, M1-S02 deploy-order.md, MILESTONE-M1-REPORT.md (5 reads, 4 distinct files)
minutes:   clarify ~40 (24 answers) · plan+verify ~110 (two rounds) · build+test ~330 (five steps, five rebuilds, six dry runs) · document+verify ~150 · read+decide ~35 · total ≈ 11 h wall-clock, human share ≈ 1 h
```

Verdict on the human experience: six decisions and four files for a five-step integration feature is right; the wall-clock was spent on 47 product defects found and fixed the same day (CLI ×9, playbooks ×12, skills ×8, contract ×11, tooling ×2, library gaps ×5) plus five org-only findings that no offline check could see — the org is the only Apex compiler in the loop, and the next flag (run tests during validation) closes the last blind spot.

## Reopened after done (2026-09-12T13:10Z) — S2-F-11

- The first dry run with Apex tests executing (`--test-level RunSpecifiedTests`, new today) failed all 28 test methods: the tests never `runAs` a user holding `Tier2_Webhook_Admin`, and the deploying user has no FLS on fields shipped in the same package, so every user-mode SOQL/DML call fails. Compile-only validation (runs 1–5) had passed 60/60, and the milestone was accepted on that. Human experience: a **false green** at the gate — the gate notes cited "validated" and the tool's summary never said "0 tests ran" (fixed today: the summary now prints the test level on every run). Decision: skill rule → re-run M1-S03/M1-S04 for their tests → run 7 → re-sign. Contract gap filed: (44) a done build has no change-request path; re-running a documented step is legal by the state machine but nothing records *why the acceptance was reopened* except this log — the gate record should carry a `reopened` note; (45) `--test-level NoTestRun` must never be the evidence for an Apex milestone — milestone-verifier Step "org evidence" should refuse a compile-only run when the manifest carries ApexClass; (46) the test-class scan should require a test method, not a class-level `@IsTest`.
- M1-S03 test repair built (2026-09-12T16:14Z, Sonnet): all 19 methods wrapped in runAs of a TestUserFactory user holding Tier2_Webhook_Admin; no assertion changed; four checkers clean, new rule 0. Two things the playbook did not carry: (47) an Apex step has no package.xml of its own (§ 5 Apex exception), so a class added in a repair must also be added to M1-S05's manifest by a separate step touch — recorded as S4-F-02 in M1-S03/deploy-order.md § 0b; (48) `check_test_class_standards.py` is not among M1-S03's declared acceptance tests, so the rule that would have caught S2-F-11 was only run because the brief said so — planner v6: every Apex step that ships a test class declares the test-class-standards checker. M1-S04 repair running; M1-S03 tester queued behind the cap.
- M1-S04 test repair built (2026-09-12T16:30Z, Sonnet): 11 methods wrapped in runAs; pure insertions (whitespace-insensitive diff); declared checkers clean; the new rule 0 on the repaired file, 1 on the pre-repair file (the rule works). Open ambiguity for dry run 7: two methods now query PermissionSetAssignment / CronTrigger / AsyncApexJob in user mode as a Standard User holding only Tier2_Webhook_Admin — whether that read is permitted is an org answer. Friction: (49) `amend-step` refuses `depends_on` once a step has left pending, so a repair that introduces a cross-step dependency (M1-S04 → M1-S03's TestUserFactory) can only record it in prose — the CLI needs a narrow `--depends-on` amendment allowed at documented/running.
- Run 7 (2026-09-12T16:50Z): 0/30 again, one layer deeper — S2-F-12: the shared TestDataFactory template populates `AccountId` with null and user-mode DML (the 67.0 default) checks FLS on it; the Standard User lacks create on `Case.AccountId` in this org. Found by an operator probe on a scratch copy (describe + getDmlFieldNames) in one dry run — ten minutes, no rebuild. Human experience: the loop's own tests could not have seen this (no org), and the org's message names no field; the probe pattern (wrap the failing seed, print field names) belongs in the deployment-error skill. Template fix queued (slot), then both Apex steps re-run a second time.
- Second-round repairs (2026-09-12T17:00–17:10Z): both Apex steps refreshed to the corrected factory (verbatim, diff empty), tested (all declared checkers clean; new rule 0 findings) and documented (D-M1S03-12, D-M1S04-11). Eight Sonnet runs in all for two findings — the per-step ceremony (repair → test → document, twice per step) is the cost the cold-start run 2 named too. Observation: three agents in a row reported "M1-S04 still ships a pre-fix copy" after it had already been repaired — each read the sibling step's files at launch and none re-read before reporting; a stale cross-step observation is cheap here but would mislead a human at a gate. M1-S05 manifest re-run running (adds TestUserFactory); dry run 8 follows the moment it is built.
- Run 8 (2026-09-12T17:07Z): 28/29 pass, 74% coverage. The last failure is a real design defect no compile could show — S2-F-13: nobody granted Create on the platform event, so every escalation logs a spurious failure and the event is dropped. Found by the same probe pattern in one dry run. The org has now been the last reviewer three times today on Apex this build declared "tested" — every one a user-mode permission the design never wrote down. Library rule queued; M1-S02 repair next; coverage obligation (finalizer paths) recorded for the gate.
- Run 9 (2026-09-12T17:17Z): 30/30 pass. Three org findings today (S2-F-11/12/13), each one layer under the last, each a user-mode permission the design never wrote down; each closed by a skill rule and a repair. What remains is coverage (70.8% vs 75%) — S2-F-14, finalizer paths untested. The tool said "Failed" with no errors and no failures and left the human to infer why; fixed in words next. Operator error to record: four agents were briefly running against a cap of three.
- Run 11 (2026-09-12T17:56Z): 35/35 pass, 86% aggregate — and still "Failed", because RunSpecifiedTests demands 75% per class and the escalation service sits at 54%. The reason was in the raw result under a key the summary never printed; the operator read it by hand. Two tool lines fix this class of confusion (print coverage warnings; say "coverage floor" in words). S2-F-16 repair resumed on the same agent.

## Re-sign (2026-09-12T18:35Z) — the five-line block, revised

1. Ask: a Tier 2 escalation webhook (credentials, Apex trigger + Queueable + finalizer, platform event, hourly health check) — `scale: feature`, 5 steps, 1 milestone. The 12:57Z acceptance was on compile-only Apex evidence; reopened the same day when tests could execute.
2. Human decisions: clarifications, plan (v2), one step gate (rejected and re-approved after an amendment), milestone (accepted, rejected, re-approved on run 13). Every gate note names the run it rests on.
3. Cost of the reopen: 6 org findings (S2-F-11..16), 13 dry runs in all (runs 6–13 today), ~14 Sonnet runs (repairs, testers, doc-keepers) and 3 library commits — roughly four hours of operator time, all on test harness and permissions, none on the shipped logic.
4. Quality now: the 35-member release package validates in the org as a production deploy would — 41/41 components, 37/37 tests, 89.9% coverage, no coverage warnings. Three of the six findings are library rules that fire on the pre-repair artefacts.
5. Driver's grade: the loop's own tests could not see any of the six; the org saw each in one four-minute run; the operator probe pattern (wrap the failing statement, print the field names or the rows) found every root cause without a rebuild. The ceremony cost was the repair → test → document triple per finding; the discoverability and false-green problems are fixed in the tool and the contract items are filed. Design-only; nothing deployed.
