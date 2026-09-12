# Mock deploy — milestone M4 in progress (validation only, nothing deployed)

## Run 1 — 2026-09-12, source mode, M1 + M2 + M3-S01..S04 + M4-S01 + M4-S04 as built (API 67.0)

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --step M1-S01 … --step M3-S04 --step M4-S01 --step M4-S04`
(M4-S02 excluded: `blocked` at run time; M4-S03/S05 not built.)

**Failed — 44 components, 43 ok, 2 errors.** The M4-S01 `Settings:BusinessHours` (three calendars, 14 holidays)
validated on first contact with the org. The two failures:

| Component | Error |
|---|---|
| `AutoResponseRule Case.Case_Acknowledgement` | `support-noreply@acme.example is an invalid From email address` — **F-28**, the known org prerequisite (no verified org-wide address in `sfskills-dev`); unchanged |
| `EscalationRules Case` | `notifyToTemplate is required` — **new** |

**F-36 (HIGH, build + skill).** Both escalation entries set `notifyCaseOwner` `true` without `notifyToTemplate`. The
guide documents `notifyToTemplate` (api_meta L59517, "Specifies the template to user for the notification email")
with no Required marker; the org requires it whenever a notification is requested (UNVERIFIED in guide, proven live).
`admin/escalation-rules`' checker had no rule for it (metadata-examples.md mentions the element twice, gotchas never).
Remedy: checker rule E8 (ERROR) + gotcha + example in the skill; M4-S04 rebuilt with a folder-qualified
`notifyToTemplate` chosen from the plan's template inputs (not restated here — plan inputs are the authority).

## Run 2 — 2026-09-12, source mode, every built step M1-S01 … M4-S05 (API 67.0)

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --step M1-S01 … --step M4-S05`

**Failed — 58 components, 52 ok, 7 errors on 3 components.** Validated on first contact: the M4-S02 entitlement
processes + milestone type, the rebuilt M4-S04 escalation rule (F-36 closed — `notifyToTemplate` accepted), the M4-S03
flow `Case_BeforeSave_StampEntitlementAndCalendar` itself, `Flow.settings`, and the M4-S05 `CaseMilestoneTrigger` and
`CaseMilestoneService` (compiled). The failures:

| Component | Error |
|---|---|
| `AutoResponseRule Case.Case_Acknowledgement` | F-28, unchanged (org prerequisite) |
| `ApexClass CaseMilestoneServiceTest` (×5) | `Variable does not exist: TestDataFactory` |
| `FlowTest Case_BeforeSave_StampEntitlementAndCalendar_Test` | `The test point for elementApiName "Start" is missing a parameter of type InputTriggeringRecordInitial.` |

**F-37 (HIGH, build + skill/agent).** The test class uses `templates/apex/tests/TestDataFactory.cls` "by relative
path" as the skill and the step's `templates[]` instruct, but nothing ships it: the template is a canonical building
block to be copied into the consuming project (`templates/README.md`), and no step's `outputs[]` carries it. The
class compiles only in an org that already has a `TestDataFactory`. Remedy: M4-S05's outputs gain
`classes/TestDataFactory.cls` (+ meta) copied verbatim from the template; `apex/entitlement-apex-hooks` and the
apex-builder playbook state that a test referencing a template class ships that class in the same step (or the plan
owns it in an earlier step); planner v6 adds a shared "Apex foundations" step when more than one Apex step needs it.

**F-38 (HIGH, build + skill).** A `FlowTest` on a Create-triggered flow must still supply `InputTriggeringRecordInitial`
on the `Start` test point; M4-S03's builder marked exactly this UNVERIFIED (U4) because the skill documents only the
Initial/Updated pair for update-triggered flows. Remedy: `flow/record-triggered-flow-patterns` metadata-examples gain
a Create-triggered FlowTest with both parameters and the checker gains a rule; M4-S03 rebuilt with the parameter.

## Run 3 — 2026-09-12, source mode, every built step after the F-37 / F-38 rebuilds (API 67.0)

**Failed — 55 components, 54 ok, 2 errors.** **F-37 closed**: `TestDataFactory` shipped, all four Apex classes and
the trigger compiled. F-28 unchanged. The FlowTest failed again with the mirror message: `The test point for
elementApiName "Start" contains the incompatible parameter value "$Record" of type InputTriggeringRecordUpdated. Remove
the parameter or change the record trigger type.`

**F-38, corrected.** For a **Create**-triggered flow the FlowTest's Start test point takes `InputTriggeringRecordInitial`
ONLY; `InputTriggeringRecordUpdated` is incompatible (there is no prior/updated pair on a create). The guide's sample
(api_meta L74351–74365) shows both parameters because its flow is update-triggered, and the skill's example copied
that shape for a create-triggered flow. Rule for the skill and its checker: `recordTriggerType Create` → Initial only;
`Update`/`CreateAndUpdate` → both. M4-S03 rebuilt a third time: remove the Updated parameter.

## Run 4 — 2026-09-12, source mode, every built step after the third M4-S03 build (API 67.0)

**55 components, 55 ok, 1 error — the only failure is F-28** (the auto-response sender, an org prerequisite outside
this build's power). Every M4 artefact validates: three business-hours calendars and 14 holidays, two entitlement
processes and the milestone type, the before-save flow with its Create-triggered FlowTest (Initial parameter only),
Flow settings, the escalation rule with its notification template, and the four Apex classes plus the trigger (compiled).
F-36, F-37 and F-38 closed at the source and proven by the org. Output: `reports/mock-deploy/2026-09-12T08-40-36Z/`.
