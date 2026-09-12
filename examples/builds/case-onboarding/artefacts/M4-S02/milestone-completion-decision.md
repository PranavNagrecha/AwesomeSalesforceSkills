# Milestone completion — M4-S02 records the decision, M4-S05 builds it

This step writes **no completion mechanism**, and it was offered no choice of one.
`plan.json` `steps[M4-S02].inputs.note` is explicit: *"Q50 is settled by D10 and built by
M4-S05: this step writes no completion mechanism and offers the builder no choice of one;
milestone-completion-decision.md records D10 and points at M4-S05."* This file is that record.

---

## 1. Why a completion mechanism is needed at all

`skills/admin/entitlements-and-milestones/references/gotchas.md` gotcha 8 — *"Nothing completes a
milestone; a milestone stays open until something writes CompletionDate"*:

> `CaseMilestone` supports only `describeLayout(), describeSObjects(), query(), retrieve(),
> update()` — there is no `create()` and no `delete()` (object_reference.txt:63347–63348).
> Salesforce creates the rows when a case enters the process; `CompletionDate` … and `StartDate`
> are the only fields carrying the `Update` property (object_reference.txt:63373–63380).
> `IsCompleted` and `IsViolated` are derived and not updateable.

The consequence, stated by the same gotcha, is the failure this build is avoiding: *"First-response
milestones show as violated on cases where the agent demonstrably replied."* Without a writer of
`CompletionDate`, the two processes in this step count down and every First Response milestone
eventually reports violated, whatever the agent did.

The same gotcha gives the rule this step obeys: **"Ship the completion mechanism with the process,
never after it."** In this plan "with the process" means *in the same milestone* — M4-S05 — not in
this step.

## 2. The decision — D10, verbatim from `plan.json` `decisions[]`

> Mark the First Response milestone complete with an after-update Apex trigger on Case that stamps
> `CaseMilestone.CompletionDate`, not with entitlement-process completion criteria and not with a Flow.

Grounding recorded with the decision:

- `automation-selection` was read end to end and found **not** to cover the question: Q2 → Q13 → Q15
  selects *Entitlement milestones* as the SLA engine — which is the ground for **this** step — but no
  leaf in Q13, Q14 or Q15 says who writes `CompletionDate`.
- `references/metadata-examples.md` § 9 is the shape the Apex follows (one query, one DML, bulk-safe).
- `skills/apex/entitlement-apex-hooks` declares exactly this artefact — an after-update trigger on
  Case that writes `CompletionDate` to open `CaseMilestone` records, plus its test class.

### Alternatives rejected, as recorded on D10

| Rejected | Why |
|---|---|
| Satisfiable completion criteria on the entitlement process | **No completion-criteria element is documented anywhere in the cited skill's metadata reference.** `milestoneCriteriaFilterItems` is a *start* criterion (api_meta.txt:59198–59201), not a completion one. This step could not have written such an element without inventing it. |
| A record-triggered Flow stamping `CompletionDate` | `metadata-examples.md` § 9 documents the Flow path as an invocable wrapper around the same Apex, so it adds a component without removing the Apex. |
| Leaving completion manual | gotcha 8: every first-response milestone then reports violated on cases the agent demonstrably answered. |

### What Q50's answer did and did not settle

Q50's recorded answer is the accepted proposed default: *"Satisfiable completion criteria on the
first outbound EmailMessage, **or** a Flow that stamps CompletionDate — chosen explicitly, not
assumed."* It names two options and requires an explicit choice. **D10 is that explicit choice**, and
it chose neither of Q50's two — it chose Apex — for the reason in the table above: the declarative
option's element does not exist in the cited reference, and the Flow option wraps the Apex rather
than replacing it. That divergence is the decision working as designed, not a contradiction.

## 3. Where it is built — `M4-S05`

`plan.json` `steps[M4-S05]`, `type: automation`, agent `apex-builder`, status `pending`:

| Declared output |
|---|
| `artefacts/M4-S05/triggers/CaseMilestoneTrigger.trigger` (+ `.trigger-meta.xml`) |
| `artefacts/M4-S05/classes/CaseMilestoneService.cls` (+ `.cls-meta.xml`) |
| `artefacts/M4-S05/classes/CaseMilestoneServiceTest.cls` (+ `.cls-meta.xml`) |

D10's own `consequences` field records what that costs: *"This is the only Apex in the build, so
M4-S05 is the only step under the 75% coverage gate and the only one whose artefacts a deploy will
compile. Violation polling is deliberately not built."*

## 4. The binding between the two steps, so nothing is lost at the gate

The Apex in M4-S05 selects open milestones by **milestone type name**. The name it must match is the
one this step writes:

| Written here | Value | The Apex must match |
|---|---|---|
| `milestoneTypes/First Response.milestoneType-meta.xml` | file base name `First Response` | `MilestoneType.Name = 'First Response'` — the § 9 query filter |
| `recurrenceType` | `none` | one instance per process run, so a single open row per case |
| `minutesToComplete` (Premier) | `240` | not read by the Apex; the target is the platform's |
| `minutesToComplete` (Standard) | `720` — **DERIVED, not answered**, see `deploy-order.md` § 3 | not read by the Apex |

**Carried to the M4 gate:** M4-S05 is `pending`. Until it is built and deployed, the two processes in
this step are *tracking-only* — they will open `CaseMilestone` rows and never close them. That is a
known, sequenced state, not a defect in this step; it becomes a defect only if this step's metadata
reaches an org without M4-S05's.

## 5. Two deferred questions that touch completion, and what was assumed instead

| Q | Status | Assumption used here |
|---|---|---|
| **Q49** — *what ends the commitment: the case closing, or something we stamp ourselves?* | deferred | **A9** — the commitment ends when the milestone is completed and the *process* ends when the case is closed. Written as `exitCriteriaFilterItems` = `Case.Status equals Closed`. `gotchas.md` gotcha 9 warns that this makes a reopen a fresh commitment; see `deploy-order.md` § 4. |
| **Q52** — *do we ever stop the SLA clock, and who is allowed to?* | deferred | **A10** — the clock is never stopped in this phase. No stop reason and no stop permission is configured, and `enableMilestoneStoppedTime` is not set by this step (it lives in `settings/Entitlement.settings-meta.xml`, which no step in this plan owns — `deploy-order.md` § 5). |

## Sources

- `plan.json` `decisions[D10]`, `assumptions[A9, A10, A24, A27]`, `clarifications[Q49, Q50, Q52, Q53]`,
  `steps[M4-S02].inputs.note`, `steps[M4-S05]`
- `skills/admin/entitlements-and-milestones/references/gotchas.md` gotchas 8, 9
- `skills/admin/entitlements-and-milestones/references/metadata-examples.md` §§ 1, 2, 9
