# Test summary — M4-S05

Step: After-update Apex trigger on Case that completes the First Response milestone, plus its
test class. Owning agent: `apex-builder`. Design-only build, no org — no deploy or Apex test
execution is possible; this run is limited to structural checks and the declared checker.

**This run supersedes `2026-09-12T08-24-48Z`**, which was written against the pre-rebuild tree
(six declared outputs, three Apex files). The step was reset `tested → failed → pending` after
the operator's dry-run found F-37 (`classes/TestDataFactory.cls` missing), `outputs[]` was
amended to eight paths, and the step was rebuilt at run `2026-09-12T08-32-00Z`. This run tests
that rebuilt state.

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| `xml` (always-on) | xml | pass — all 4 `-meta.xml` files parse | — |
| `manifest` (always-on) | manifest | skipped-not-applicable | The Apex exception (owning agent `apex-builder`): members are aggregated into the build-level manifest by M5-S05. See `results.json.details.manifest`. |
| `python3 skills/apex/entitlement-apex-hooks/scripts/check_entitlement_apex_hooks.py --manifest-dir artefacts/M4-S05` | checker | pass — exit 0, `check-outputs` ok | `scanned 4 Apex file(s) under artefacts/M4-S05: 0 ERROR, 0 WARN` |
| Given/When/Then reviewer-identifier-provenance test | manual | deferred to milestone gate | n/a — not runnable here |

**Supplemental (not a declared acceptance test, run per this invocation's explicit instruction):**
a brace/paren/bracket balance check (comments and string literals stripped) on all four Apex
files, including the rebuild's `TestDataFactory.cls`. All four balanced. Raw output:
`tests/M4-S05/brace-balance.txt`. Not counted toward `passed`/`failed`.

## Checker detail — four files, not three

The declared checker (`acceptance_tests[0]`) scanned 4 Apex files this run, versus 3 in the
superseded run: `classes/TestDataFactory.cls`, added by the F-37 rebuild, is now present and
cleared every rule cleanly — it contains no `CaseMilestone` reference at all, so the checker's
domain rules (`EAH001`–`EAH008`) are inert on it, and its one loop (`bulkInsertStandardSet`)
holds no SOQL or DML inside it. `check-outputs` confirmed all 8 declared outputs present,
non-empty and (for the XML ones) parseable before this checker ran, per
`standards/build-orchestration.md` § 5's precondition that `checker` and `check-outputs` both
gate `built` and `tested` together.

## Manifest check detail

Step type `automation`, owning agent `apex-builder`. Per `standards/build-orchestration.md` § 5
**The Apex exception**, an `apex-builder`-owned `automation` step declares no `package.xml` and
none was found under `artefacts/M4-S05/`. This matches `plan.json`
`steps[M4-S05].acceptance_tests[2].expected`: "skipped-not-applicable, naming M5-S05 as the step
that carries the ApexClass and ApexTrigger members." `M5-S05` (type `docs`, `metadata-builder`,
`depends_on` this step) is the step that will write the aggregating build-level manifest — now
for four `ApexClass`/`ApexTrigger` members instead of three, per the rebuild.

One thing worth flagging rather than silently normalizing: `artefacts/M4-S02/package.xml`
(a dependency of this step) does exist — but it is M4-S02's own manifest for M4-S02's own metadata
type, not a manifest for this step's Apex members, and the Apex exception applies to this step
regardless of a dependency's own manifest. It is not treated as satisfying anything here.

## Manual test classification (Given/When/Then)

`acceptance_tests[3]` (`manual`):

> Given no offline Apex compiler exists in the sf CLI, when the step is accepted, then the
> reviewer confirms every non-platform identifier in the emitted code is quoted from
> `skills/apex/entitlement-apex-hooks/references/examples.md` or from the cited template, and
> that `CaseMilestoneServiceTest` asserts `CompletionDate` is non-null after the trigger runs.

Shape check against `skills/admin/acceptance-criteria-given-when-then` and
`skills/admin/uat-and-acceptance-criteria`: the Given names the precondition (no offline
compiler), the When names the trigger event (step accepted), and the Then names two concrete,
observable outcomes (identifier provenance against a named file, and a named assertion in a named
test method) rather than a vague quality judgment. Usable as written — carried to
`skipped_manual[]` verbatim for the milestone gate, not ticked here. Text is unchanged from the
pre-rebuild step, so the classification carries over unchanged; the reviewer's identifier check
now also covers `classes/TestDataFactory.cls`, whose identifiers are a verbatim copy of
`templates/apex/tests/TestDataFactory.cls` (confirmed by `diff`, per `deploy-order.md` § 0), not
freestyled.

## No org test run

This is a design-only build with no org on file. No `sf` command, no deploy, and no Apex test
execution occurred in this run or in any run preceding it (`apex-builder`'s own Gate C, the
operator's dry-run validation at `reports/MOCK-DEPLOY-M4.md`, and `build-step-runner`'s
relocation pass). The declared `checker` and the always-on `xml` structural check are the only
things any agent in this build can verify about correctness before an org exists; the manual test
and the four `not_covered` items in `artefacts/M4-S05/deploy-order.md` §§ 3–5 remain unverified
against real Salesforce behavior until then.
