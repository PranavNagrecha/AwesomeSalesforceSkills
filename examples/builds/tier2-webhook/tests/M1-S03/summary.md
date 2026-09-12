# step-tester — M1-S03 — molecular test results

Build `tier2-webhook` · step `M1-S03` · type `automation` · owner `apex-builder` ·
run 3 (S2-F-04 / S2-F-05 fixes) · status entering this run: `built`.

All commands run verbatim from the build directory
`.sfskills/builds/tier2-webhook/` via the `skills` symlink, except
`build_plan.py`, which is invoked from the repo root with the build-relative
plan path (matching the form recorded in this step's own `runs[]`).

Run 2 was tested clean with this same five-test suite and then **failed the
operator's org dry run** (`reports/MOCK-DEPLOY-M1.md` run 3: `URL.getSalesforceBaseUrl()`
removed after v58.0 on two call sites — S2-F-04 — and a SOQL `WHERE` filter on the
LongTextArea field `Request_Payload__c` — S2-F-05). Run 3 changed exactly those two
call sites and the two `WHERE` clauses; every other file is byte-identical to run 2
(`artefacts/M1-S03/deploy-order.md` § 0). This run re-executes every test against the
run-3 artefacts rather than trusting the prior green result, and separately verifies
by inspection that both fixes actually landed in the files under test (see table).

| Test | Type | Result | First line of output |
|---|---|---|---|
| XML well-formedness (always-on) | `xml` | PASS | 12/12 `*-meta.xml` files parse; apiVersion 67.0 on all; both `.trigger` files declare `after update`, `<status>Active</status>` |
| package.xml consistency (always-on) | `manifest` | SKIPPED-NOT-APPLICABLE | Apex exception (build-orchestration.md §5): apex-builder ships no manifest; M1-S05 (type `docs`, `metadata-builder`, depends_on M1-S03) carries the members |
| `check_apex_queueable_patterns.py --manifest-dir artefacts/M1-S03` | `checker` | PASS (exit 0) | "Scanned 12 Apex file(s), 1 implementing Queueable; 0 ERROR, 0 WARN, 0 ADVISORY." |
| `check_callouts_and_http_integrations.py --manifest-dir artefacts/M1-S03 --fail-on HIGH` | `checker` | PASS (exit 0) | "Scanned 12 Apex file(s); 0 callout finding(s)." |
| `check_platform_events_apex.py --manifest-dir artefacts/M1-S03` | `checker` | PASS (exit 0) | "Scanned 12 Apex file(s) and 0 object file(s); 0 platform-event finding(s)." |
| `check-outputs` (precondition for all three checker tests) | — | OK | `{"ok": true, "missing": [], "empty": [], "malformed": []}` — all 20 declared outputs present |
| Brace/paren/bracket balance (tester's own mechanical scan, comments/strings stripped; not a declared test) | — | OK | 12/12 files balanced |
| Fix verification: S2-F-04 (`getOrgDomainUrl` replaces `getSalesforceBaseUrl`) | — | CONFIRMED | zero `getSalesforceBaseUrl` hits in `.cls` files; `getOrgDomainUrl()` present at both call sites |
| Fix verification: S2-F-05 (no `WHERE` filter on the LongTextArea field) | — | CONFIRMED | zero `Request_Payload__c` `WHERE` hits; select-then-pick helpers present |
| Manual acceptance test | `manual` | DEFERRED to M1 gate | "Two-point code read... EventBus.publish inspected; no credential leakage" — see Manual Checklist below |

**Overall: `passed: true`. 5 declared tests ran (2 always-on + 3 checkers), 0 failed, 1 manual deferred.**

## Failure detail

None. All runnable tests passed.

## Manual checklist (for the milestone gate, never ticked here)

> Two-point code read at the M1 gate, tickable from this step's artefacts alone.
> Expected: A reviewer opens `Tier2EscalationService.cls` and `Tier2WebhookQueueable.cls`
> and confirms (a) the `EventBus.publish` call is in the service, in the escalating
> transaction, and its `List<Database.SaveResult>` is inspected with a failure writing an
> `Integration_Failure__c` row — not discarded, and not moved inside the Queueable;
> (b) no class anywhere sets an `X-API-Key` or `Authorization` header, reads a credential
> value, or names a literal hostname, and every endpoint is composed as `callout:OnCall_Tool`
> plus a path through `templates/apex/HttpClient.cls`.

Classification: usable (names two specific, independently observable outcomes; not
strict Gherkin but tickable from the artefacts alone per
`admin/acceptance-criteria-given-when-then`'s testability bar). Clause (a) verified
by inspection this run: `Tier2EscalationService.cls:76` assigns
`List<Database.SaveResult> publishResults = EventBus.publish(events);`, walks it, and
a rejection appends an `Integration_Failure__c` row — in the service, not the Queueable.
Clause (a) is accurate and tickable exactly as written.

**Clause (b) still names the dropped `HttpClient` template — recorded verbatim above,
flagged again this run.** Remedy B dropped `templates/apex/HttpClient.cls` before run 2
was ever built; it was never shipped in run 2 or run 3
(`Tier2WebhookQueueable.cls:25`: "No HttpClient wrapper ... in this build (remedy B)").
The underlying security property clause (b) is actually testing — no literal hostname,
no Apex-set `X-API-Key`/`Authorization` header, endpoint composed as
`callout:OnCall_Tool` — is satisfied and confirmed by inspection this run
(`Tier2WebhookQueueable.cls:235`: `req.setEndpoint('callout:' + NAMED_CREDENTIAL);`, no
`Authorization`/`X-API-Key` `setHeader` call anywhere in the class). But a reviewer
ticking clause (b) literally against the named `HttpClient.cls` mechanism at the M1 gate
would find that file absent from the artefacts. This is a stale plan-text defect carried
unchanged from run 2's own `results.json`; it is a wording problem in the acceptance
test's `description`, correctable only by `amend-step --prose-only` (the step's own
writer for exactly this situation per `standards/build-orchestration.md` §2), not by this
agent. Recorded again rather than silently re-passed through.

## Process Observations

**Healthy.**
- Every declared checker exits 0 with zero findings at any severity (not merely zero
  blocking findings) — `tests/M1-S03/checker{1,2,3}_*.txt`.
- `check-outputs` confirms all 20 declared outputs present, non-empty, and (for the 12
  XML files among them) parseable — `tests/M1-S03/check_outputs.txt`.
- All 12 Apex files are brace/paren/bracket/string balanced under a mechanical scan
  that strips comments and string literals first — `tests/M1-S03/brace_balance_output.txt`.
- Both run-3 fixes (S2-F-04, S2-F-05) are verifiably present in the artefacts under
  test, not merely asserted in `deploy-order.md`'s narrative — see
  `results.json.detail.run3_fix_verification`.

**Concerning.**
- **No library checker compiles Apex, and this step has still never been compiled.**
  Run 2 passed every declared checker, the XML parse and the brace-balance scan, and
  then failed the org on two faults — a removed-after-58.0 method name and a filter on
  an unfilterable field type — that none of those checks can see: a checker matches
  syntax and pattern shape, not the version-gated legality of a method name or the
  platform's SOQL-filterability rules for a field's declared type. Run 3's fixes are
  confirmed present by grep, which proves the *text* changed; it does not prove the
  *code compiles*. The org is the only compiler in this loop (`agents/_shared/AGENT_CONTRACT.md`
  Gate C: there is no offline Apex compiler in the `sf` CLI), and this package's only
  compile attempt so far — run 2 — failed. Run 3 has not yet been through
  `mock_deploy.py`. This is the single most important fact for whoever reads this
  result next: **`passed: true` here means "every check this loop can run without an
  org passed," not "this will deploy."**
- **P1 carried from the build envelope, not re-litigated here:** remedy B dropped
  `templates/apex/TriggerHandler.cls` (→ `TriggerControl` → `Trigger_Setting__mdt`), so
  this build ships no trigger kill switch and no data-load bypass for `CaseTrigger` —
  `artefacts/M1-S03/deploy-order.md` §4. Not re-verified this run; named so it is not
  lost between `tested` and the milestone gate.
- **Manifest-check confirmation, not a new finding:** M1-S03 (an `automation` step, one
  of the seven metadata types the always-on `manifest` check would otherwise fail on
  absence) has no `package.xml` anywhere in its own or its `depends_on` (`M1-S01`,
  `M1-S02`) artefacts for its own members — confirmed this run that `M1-S01`/`M1-S02` do
  each carry a `package.xml`, but neither lists this step's `ApexClass`/`ApexTrigger`
  members, so the exception is correctly triggered rather than incidentally true. Cross-
  checked against `plan.json steps[M1-S05]` (`type: docs`, `agent: metadata-builder`,
  `depends_on` includes `M1-S03`, `status: pending`).
- **Plan-text/artefact mismatch in the manual test's own wording — see Manual checklist
  above.** Unchanged from run 2; still not fixed at the plan level.
- **A second, pre-existing plan-text defect (not this run's to fix):** the step's own
  acceptance-test `description` for the callouts checker says it "fails on a test with
  setMock after startTest," which is the opposite of what the checker's code does (it
  fails on setMock with **no preceding** startTest). Repeated from run 2's record only
  because a future reader of `PLAN.md` debugging a failure from the prose alone would be
  misled.

**Ambiguous.**
- Whether the org already has an `after update` trigger on `Case` is not settled by
  any of the 45 clarifications; `CaseTrigger.trigger` assumes none exists. If one does,
  this is a `trigger-consolidator` problem, not a redeploy problem.

**Suggested follow-ups (recommendations only; none invoked).**
- `build-doc-keeper` — next in the loop now that this step is `tested`: PLAN.md,
  decisions.md and traceability.md should carry the P1 kill-switch loss, the manual
  test's stale HttpClient clause, and the manifest Apex-exception note.
- `build-step-runner` — only if a future amendment changes this step's artefacts again;
  not needed now, since nothing here failed.

## Citations

- `agents/step-tester/AGENT.md` — this agent's own playbook (Steps 1-8, the acceptance-test
  dispatch table, the Apex-exception manifest rule).
- `agents/_shared/AGENT_CONTRACT.md` — 8-section shape, Process Observations requirement,
  confidence rubric (overridden per step-tester Step 7), Gate C (no offline Apex compiler).
- `agents/_shared/DELIVERABLE_CONTRACT.md` — atomic-write rule, envelope/extensions split.
- `agents/_shared/REFUSAL_CODES.md` — refusal enum (not triggered this run).
- `AGENT_RULES.md` — run-time rules, org-write ban.
- `standards/build-orchestration.md` §4 (step types, Apex row note), §5 (acceptance-test
  types, checker-scope rules, the Apex exception, check-outputs gating `built`/`tested`).
- `agents/_shared/schemas/build-plan.schema.json` — `acceptanceTest`/`step`/`run` shapes.
- `skills/devops/metadata-api-retrieve-deploy/SKILL.md` — package.xml `<types>`/`<members>`/
  `<name>` grammar and wildcard semantics (not exercised this run — no manifest to check).
- `skills/devops/salesforce-dx-project-structure/SKILL.md` — source-format filename→type
  mapping (`classes/`, `triggers/`, `-meta.xml` siblings) confirmed against this step's tree.
- `skills/devops/metadata-api-coverage-gaps/SKILL.md` — coverage-gap exclusion list (not
  applicable — `ApexClass`/`ApexTrigger` are fully supported types; no exclusion needed).
- `skills/admin/uat-and-acceptance-criteria/SKILL.md` — UAT-script tickability bar applied
  to the manual test's classification.
- `skills/admin/acceptance-criteria-given-when-then/SKILL.md` — Given/When/Then testability
  bar (named observable outcome, per-clause) applied to the manual test.
- `artefacts/M1-S03/deploy-order.md` — §0 (the rebuild record, S2-F-04/S2-F-05, what
  changed in run 3), §4 (P1 kill-switch loss), §5 (UNVERIFIED items), §9 (symbol
  grounding).
- `reports/MOCK-DEPLOY-M1.md` — named, not re-read line-by-line this run — the operator's
  run-2 dry-run failure record that run 3 responds to.
