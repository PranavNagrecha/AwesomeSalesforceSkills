# The build loop, told through five builds

**Who this is for:** anyone asked to make a Salesforce change with this library
who wants to see what the requirement-to-build loop does before running it.
If you are changing the loop's agents or tooling, read the contract,
[`standards/build-orchestration.md`](../standards/build-orchestration.md), instead.

The loop takes one requirement and produces a deploy-ready build. Along the way
it asks the questions the skills say must be asked, plans, tries to refute its
own plan, then builds and tests each step and has every milestone verified. A
human signs a gate between stages. It never deploys. This page walks through
the five worked examples committed under
[`examples/builds/`](../examples/builds/), smallest first, and then says what
they have in common.

Every number below is quoted from a README, named in brackets: **[index]** is
[`examples/builds/README.md`](../examples/builds/README.md), any other name is
that example folder's `README.md`. Where they disagree, the README is right.

## The loop in one screen

| Stage | Command | What it leaves behind | Human gate |
|---|---|---|---|
| Clarify | `/clarify-requirements` | `plan.json`, `CLARIFICATIONS.md` (every question with a proposed default) | **answers**: each blocking question answered or deferred |
| Plan | `/plan-build` | scope, decisions (each citing a decision-tree branch), milestones, steps | none |
| Verify | `/verify-plan` | three adversarial lenses per step: executability, grounding, testability | **plan** approval |
| Build | `/run-build <build-dir> <milestone>` | per step: artefacts, checker output, docs; then a milestone acceptance report | **milestone** acceptance, plus a `step:<id>` gate on every step the planner marks human-gated (credentials, permission sets, deletions) |

`/build-from-requirements` walks the whole loop. `plan.json` is the single
source of truth and `scripts/build_plan.py` is the only thing that writes it.
No agent signs a gate (§ 2–3 of the contract).

**Ceremony scales to the ask** (§ 3.1). The clarifier counts four signals:
metadata types that need their own step (D), cited skills with a question table
(S), objects named (O) and whether an integration or migration is implied (X).
It prints a sizing line, and the tier is the highest one any single signal
reaches:

| Tier | Plan shape | Gates | Docs |
|---|---|---|---|
| `ask` | 1 milestone, 1 step | two decisions, `go` and `accept` | one rendered `RUN.md` |
| `feature` | 1 milestone, up to 5 steps | clarifications, plan, milestone (+ step gates) | traceability required, workbook optional |
| `project` | 2–6 milestones | the full set | workbook, traceability, decisions |

The guarantees stay the same at every tier. Every cited skill is read and its
questions harvested, every checker runs verbatim, every agent run leaves an
envelope, and a human decides every gate.

## 1. One ask, one step: `opp-amount-lock`

[`examples/builds/opp-amount-lock/`](../examples/builds/opp-amount-lock/README.md),
`scale: ask`. Start here.

The ask is one line from Sales Ops: lock Opportunity Amount once the deal is
Closed Won. The clarifier harvested **13 questions** from the cited skills. The
requester answered the **7 blocking** ones and **6 defaults** were applied
[opp-amount-lock]. The plan is **1 milestone, 1 step, 4 tests**, and verification
took **one round with 10 warnings and 0 blockers** [opp-amount-lock].
The step, `M1-S01`, is owned by `metadata-builder` and cites
`admin/validation-rules` and `admin/custom-permissions`. The bypass permission
set rides inside that step, so the one up-front gate is where a human sees that
access is being granted [index].

The interesting part is the rebuild. The plan's blank guard,
`NOT(ISBLANK(StageName))`, was copied from the skill's own GOOD example and did
not compile. `NOT(ISBLANK(TEXT(StageName)))` validated **3/3** in the operator's
dry run, and the skill gained checker rule `VR-PICK-01` the same day
[opp-amount-lock]. The loop caught a defect in the library it reads from.

The human side is two gate decisions: `go` signs the clarifications and plan
together, and `accept` signs the milestone. That makes **3 gate records** and
**0 numbered org dry runs**, just one operator probe on a scratch copy [index].
The folder's README tallies it as "three human decisions, four files read"
[opp-amount-lock]. The page read at both gates is
[`RUN.md`](../examples/builds/opp-amount-lock/RUN.md). The milestone report is
`ready-with-findings` with **F-01..F-11**. The driver's log records the
**22 product defects** the run surfaced and fixed [opp-amount-lock].

## 2. An integration feature: `tier2-webhook`

[`examples/builds/tier2-webhook/`](../examples/builds/tier2-webhook/README.md), `scale: feature`.

The build covers an external and a named credential, a Case trigger, a webhook
Queueable with a finalizer, a platform event and an hourly channel-health
Schedulable. That came to **5 steps** in **1 milestone**, with **plan v2 after two
verification rounds** and **45 questions** answered [tier2-webhook]. There are
**four gate records** [index]: clarifications, plan, one step gate (rejected,
then re-approved after an amendment), and the milestone (accepted, rejected,
re-approved) [tier2-webhook].

This build taught the loop that compile-only Apex evidence is not enough
[index]. There were **thirteen validate-only runs** against a developer org.
Runs 1–5 compiled the Apex and ran no tests. Run 6 was the first with tests
executing, and it **failed all 28 test methods** [tier2-webhook]. Six findings
followed, one layer at a time: the tests never ran as a permissioned user; the
shared factory populated a null lookup; no persona held Create on the platform
event; the finalizer was uncovered; a re-enqueued job ran to its designed
failure; and `RunSpecifiedTests` applies the 75% rule per class. Each became a
library rule or a recorded decision. The milestone was re-signed
on run 13, when the **35-member** release package validated with
**41/41 components, 37/37 tests and 89.9% coverage** [tier2-webhook].

## 3. The large project: `case-onboarding`

[`examples/builds/case-onboarding/`](../examples/builds/case-onboarding/README.md),
project tier. It is the largest example and ran before the `ask` and `feature`
tiers existed, which is why it asked **97 clarifications**, with 25 deferred
[case-onboarding].

The planner and verifier went back and forth **five rounds**, with blockers
falling **19 → 11 → 13 → 1 → 0**. They ended on **plan v5: 5 milestones,
22 steps, 130 acceptance tests, 28 assumptions** [case-onboarding]. Two steps
are blocked by design and ship nothing: Omni-Channel waits on deferred answers,
and the sandbox strategy waits on inputs nobody supplied. Both reasons are in
`PLAN.md`. The build has **thirteen gates**: clarifications, plan, six step
gates and five milestone gates [case-onboarding].

Its lesson is that **the org is the last reviewer** [index]. After every
milestone the build went to a developer org in validate-only mode,
**32 numbered runs** in all (M1 10, M2 3, M3 6, M4 4, M5 9) [index]. Each of
the **18 distinct** org rejections became a checker rule, gotcha or example in
the library [case-onboarding]. The final manifest-mode run validates
**60/60 components at API 67.0** except for one named org prerequisite: F-28,
a verified sender address [case-onboarding].

Two milestone gates (G4, G5) were first signed on compile-only Apex evidence.
Once the dry runs executed tests, they found four defects no checker or
verifier could see. After the repairs the build's Apex validates as the
persona, **4/4 tests at 84.4% coverage**, and both gates were re-signed
[case-onboarding].

## 4. The broad project: `northwind-sales`

[`examples/builds/northwind-sales/`](../examples/builds/northwind-sales/README.md),
project tier. It is the broadest example in technology. The requirement asks
for an Enterprise sales process that leaves the SMB pipeline alone, and the
build covers record types, stages, layouts, permission sets, a profile overlay,
validation rules with a bypass, an approval process, Apex, a Lightning web
component, a record page, reporting and the signed deliverables
[northwind-sales].

It ran **sixteen steps, four milestones and nine human gates**, from its first
clarification on 12 September 2026 to acceptance on 3 October 2026. Clarifying produced
**65 questions and 43 assumptions**, and the plan was approved as v2 after a
verifier round [northwind-sales]. **16 runs reached the org** across 17
folders, two of them plan-only (M1 4, M2 3, M3 5, M4 4 [index]). They taught
**fourteen facts**, `N3-F-01..08` and `N4-F-01..06`. Its README pairs each
org message with the skill rule, gotcha or tool fix that now enforces it
[northwind-sales].

This build is also where the loop learned that **step docs can be rendered**
[index]. From M3 onward `scripts/render_step_docs.py` wrote the documentation
in seconds, where the agent version had cost 250k–450k tokens a step. The
whole build took roughly **nine hours** of sprint time across three weeks.
Builders ran on Opus at 12–25 minutes a step and testers on Sonnet at 2–8
minutes, and from M2 onward the operator did the verification at fourteen
minutes a milestone [northwind-sales]. The driver's log lists **72 friction
items**, and the compiled deliverables include a **73-case UAT pack**
[northwind-sales].

It also lists what the loop could not see: runtime behaviour (approval routing
when the owner has no Manager, the product gate after a line-item deletion),
the Jest suite (a build directory has no harness), the report and dashboard
until their new report type exists, and two deploy-time risks. Each one is an owned step in the
cutover runbook
[`artefacts/M4-S04/deploy-order.md`](../examples/builds/northwind-sales/artefacts/M4-S04/deploy-order.md)
[northwind-sales].

## 5. Skipping the loop: the two cold starts

**Run 1,
[`cold-start-lead-source`](../examples/builds/cold-start-lead-source/README.md).**
A fresh session got the repository and one client sentence: copy a Lead's Lead
Source onto the converted Opportunity. It found the right skill on its first
search and produced a correct design in about **7 minutes and 27 tool calls**
[cold-start-lead-source]. It also skipped the loop. It asked **3** questions
and answered them itself, where the ask tier would have put about **13**. It
ran **no** checkers before calling the work done, and it left a design doc in a
scratch directory instead of a record a second person could audit. The README
puts it in one line: "The library worked cold; the orchestration loop was
invisible cold." The cause was that `CLAUDE.md` described the loop 260 lines
down as a layer, not as the entry point for a client ask. The fix was the
"Two Ways In" opening `CLAUDE.md` now has [cold-start-lead-source].

**Run 2,
[`cold-start-case-escalation-email`](../examples/builds/cold-start-case-escalation-email/README.md).**
The same experiment on a different ask, after the fix. The session found the
loop, sized it `feature` (two objects), and drove it to `done` unaided. It
harvested **19** questions from three skills, answered the **4** blocking ones
as the client and defaulted the other **15**. It signed three gates and ran the
declared checkers [cold-start-case-escalation-email]. The record cost
**~31 minutes, 140 tool calls and 390k tokens**, against run 1's **~7 minutes,
27 calls and 177k** [cold-start-case-escalation-email].

The loop still let something through. The plan declared one flow checker, and
an undeclared one, `flow-element-naming-conventions`, later reported
**3 errors** [cold-start-case-escalation-email]. That gap was filed for the
planner, and `validate` now warns when a cited skill's checker is undeclared
(§ 3.1 "CLI deltas").

---

## The five side by side

All figures are from the [index] table, which counts them from each `plan.json`.

| Build | Tier | Questions | Steps | Milestones | Gate records | Org dry runs |
|---|---|---|---|---|---|---|
| opp-amount-lock | ask | 13 | 1 | 1 | 3 | 0 (one operator probe) |
| tier2-webhook | feature | 45 | 5 | 1 | 4 | 13 |
| northwind-sales | project | 65 | 16 | 4 | 9 | 16 |
| case-onboarding | project (default) | 97 | 22 (2 blocked by design) | 5 | 13 | 32 |
| cold-start-lead-source | none (loop not found) | none recorded | none | none | 0 | 0 |
| cold-start-case-escalation-email | feature | 19 | 1 | 1 | 3 | 0 |

## What all five show

- **Questions come from the skills, and they are never capped.** The tier
  decides how many questions go to the human in one round, not how many are
  harvested.
- **Files are not the last word.** Checkers and verifiers read files, and
  validate-only org runs still found rules that no checker held. The
  [index](../examples/builds/README.md#the-org-as-teacher) lists every such
  refusal and where it lives now.
- **Validate-only has limits, and each build names them.** Runtime behaviour,
  Jest, data and permission-set assignment are carried as runbook steps and UAT
  lines. See
  [What the loop could not see](../examples/builds/README.md#what-the-loop-could-not-see).
- **Every gate in these examples was signed by a stand-in** for the requester:
  the dry-run operator, or in the cold start the session itself. Each gate
  record says so. Nothing in any folder was deployed [index].

## Run one yourself

1. Read § 3.1 of
   [`standards/build-orchestration.md`](../standards/build-orchestration.md).
   The tier is counted, not picked by feel; `init --scale <tier>` overrides it.
2. In Claude Code, run `/build-from-requirements` (the whole loop) or
   `/run-build <build-dir> <milestone>` (one milestone).
   [`commands/build-from-requirements.md`](../commands/build-from-requirements.md)
   has the exact command sequence.
3. To check a build against an org you control, run
   `python3 scripts/mock_deploy.py <plan.json> --org-alias <alias> --milestone M1`.
   It has no deploy option.
4. To keep a finished build as an example, run
   `python3 scripts/build_plan.py export <plan.json> <dest-dir>`. It refuses
   until `validate` passes.

Next: the [examples index](../examples/builds/README.md), or the [docs index](README.md).
