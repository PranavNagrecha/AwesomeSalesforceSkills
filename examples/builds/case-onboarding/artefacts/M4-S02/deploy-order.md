# Deploy order — M4-S02 (Entitlement processes and the First Response milestone type)

Written by `agents/metadata-builder` on every run, per its AGENT.md Step 7. **Nothing in this build
deploys.** The command in § 7 is validate-only text for a human to copy; this agent ran no `sf`
command of any kind.

**Note on declaration:** this file is *not* in `plan.json` `steps[M4-S02].outputs[]` — five paths are
declared and this is not one of them. It is written anyway because the human's deploy reads it, the
same undeclared-`deploy-order.md` pattern `decisions.md` **O-M3S02-03** records for M3-S01…M3-S04 and
`artefacts/M4-S01/deploy-order.md` records for M4-S01. It is reported again in this run's envelope as
an undeclared artefact rather than left for a reader to notice.

---

## 0. Checker status — the W4 ambiguity block is closed, at the skill, not the artefact

This step was first run at `2026-09-12T07:20:25Z` and ended **blocked** (`ambiguity`) on two **W4**
findings promoted to failures by `--strict`. **The block is now closed and no artefact in this step
changed.** The record of what happened is kept below, because the reasoning is what a reader needs at
the gate.

**Resolved at the source.** Commit `a18f9164d` (`admin/entitlements-and-milestones` v1.1.2) moves the
"neither `<timeTriggers>` nor `<successActions>`" finding from **WARN to INFO**, so `--strict` never
promotes it. The grounding is the one fact this step could not establish from the skill as it then
stood: **api_meta.txt:59162–59169 lists `successActions` and `timeTriggers` with no "Required."
qualifier** — unlike, say, `apiVersion` at api_meta.txt:5481 — so a milestone with no actions at all
is a documented-legal shape, "intended when completion is driven by a trigger/flow and no
notification is wanted." That is exactly this build's design: D10 puts completion in M4-S05's
after-update Apex trigger, and no clarification asks for a milestone notification.

The same commit **split a conflated code rather than weakening a check**: the stale-`timeLength` case
that used to also emit W4 — *"fires before the milestone starts … a stale timeLength left behind when
`minutesToComplete` was shortened"* — is now its own code **W7**, still a WARN and still
strict-promoted. Nothing that was a real failure stopped being one. W4 keeps its historical code so
existing references resolve.

**This vindicates the block rather than reversing it.** The two repairs rejected below are still the
wrong answers; the right answer was that neither repair was needed, which is a fact about the skill,
not about the XML. Same shape as `decisions.md` **D-M4S01-01**, where the rule moved and the artefact
did not.

**Re-run of the declared acceptance test, verbatim, from the build directory, against byte-identical
files** (`plan.json` `steps[M4-S02].acceptance_tests[0]`):

```text
$ python3 skills/admin/entitlements-and-milestones/scripts/check_entitlements_and_milestones.py \
    --manifest-dir artefacts --strict
INFO  W4  [First_Response_Premier.entitlementProcess-meta.xml] Milestone 'First_Response_Premier /
          First Response' has neither <timeTriggers> nor <successActions>: no warning or completion
          action is configured; the milestone still counts down and reports violation — intended when
          completion is driven by a trigger/flow and no notification is wanted; confirm that is the
          design.
INFO  W4  [First_Response_Standard.entitlementProcess-meta.xml] … (same finding)

0 error(s), 0 warning(s), 2 info note(s).
OK: no ERROR findings.
EXIT=0
```

The INFO line asks for one confirmation — *"confirm that is the design."* **It is:** `milestone-completion-decision.md`
records D10, which puts the `CompletionDate` writer in M4-S05's after-update Apex trigger, and § 0 of
this file records that no clarification anywhere in this build names a milestone notification's
recipient, offset, sender or template. Both processes are therefore deliberately action-less.

The file that was rejected is byte-for-byte the file that now passes. No repair pass was spent.

---

### Kept as the record: what the block was, and the two repairs that were rejected

The finding, as it read before `a18f9164d`:

```text
WARN  W4  … Milestone '… / First Response' has neither <timeTriggers> nor <successActions>. It
          counts down and nothing observable happens at any point.

0 error(s), 2 warning(s), 0 info note(s).
--strict: failing on 2 warning(s).
EXIT=1
```

**Every other rule in the checker passed then, including the one `--strict` was added for.** Run at step
scope (`--manifest-dir artefacts/M4-S02`) the same files produce four **W6** findings — "this tree
holds no BusinessHours settings file, so the name was not resolved against anything" — and exit 0.
Run at build scope, where M4-S01's `settings/BusinessHours.settings-meta.xml` is visible, all four W6
findings **disappear and no W3 replaces them**: `US Support` resolves against a real `<name>` in that
file, on the process and on the milestone override, for both processes. That is the cross-reference
the plan's own test rationale says `--strict` exists to make real, and it is green. The ERROR set —
E1 `minutesToComplete`, E2 two defaults on one `versionMaster`, E3 the `workflowTimeTriggerUnit` enum,
E4 the `SObjectType` / `recurrenceType` enums — is clean, as are W1, W2 and W5.

### Why W4 could not be repaired here (the reasoning that produced the block)

W4 clears only if each milestone carries `<timeTriggers>` or `<successActions>`. Both are lists of
`WorkflowActionReference` — `name` plus a `type` from `Alert | FieldUpdate | FlowAction |
OutboundMessage | Task` (`references/metadata-examples.md` § 2, "How to read it") — and the reference
file is equally explicit that **"the referenced component must exist in the org or in the same
deploy"** (§ 3). Two facts make that unsatisfiable from this step's inputs:

1. **No step in this plan builds a `Workflow` file.** Searched every `steps[].outputs[]` in
   `plan.json`: there is no `workflows/Case.workflow-meta.xml` and no `WorkflowAlert` or
   `WorkflowFieldUpdate` anywhere in M1–M5. The two email templates this build does own
   (`Case_Acknowledgement`, `Case_Escalated_To_Tier2`, both `M3-S02`) are `EmailTemplate` components
   consumed by the auto-response and escalation rules, not `WorkflowAlert`s.
2. **No clarification asks for a first-response warning or violation notification.** The whole `sla`
   question group (Q38–Q53, Q90–Q92) was read: Q45 answers the notify question for the **escalation
   rule** (M4-S04), not for a milestone. Nothing names a recipient, an offset, a sender or a template
   for a milestone alert, and `requirement.md` does not ask for one. Writing the action would mean
   inventing its name, its offset, its recipients and the template it sends — four values with no
   source.

### The two repairs that would have passed the gate, and why neither was written

Both were built on scratch copies **outside the build directory** and never applied to the artefact —
the same procedure `decisions.md` **D-M4S01-01** records for M4-S01's blocked run.

| Repair | Checker result (`--strict`, with the BusinessHours settings file present) | Why it was rejected |
|---|---|---|
| **A** — `timeTriggers` carrying `<actions><name>First_Response_Warning</name><type>Alert</type></actions>` | `0 error(s), 0 warning(s), 2 info note(s)` · **EXIT=0** | Names an `Alert` that exists in no step of this plan and in no answered clarification. `metadata-examples.md` § 3: a milestone action naming a component that is missing "fails the whole deploy, not just the milestone." It turns a visible warning into an invisible deploy failure, and the `-60` offset, the recipient and the template would all be invented. |
| **B** — `timeTriggers` with **no** `<actions>` child at all | `0 error(s), 0 warning(s), 2 info note(s)` · **EXIT=0** | The skill documents no action-less time trigger — every `timeTriggers` block in `metadata-examples.md` (§§ 2, 7) carries at least one `actions` entry, and whether `actions` is a required child is stated nowhere, so the shape is **UNVERIFIED**. It also clears the warning's letter while leaving its substance true: a trigger with no action still means "nothing observable happens." |

**The two variants produce byte-identical checker output.** That is the point: the checker cannot
distinguish an invented-but-dangling action from no action at all, so passing it here would be the
same trap as trimming M4-S01's 24/7 calendar to Mon–Fri — green gate, wrong artefact, invisible to
every downstream check.

### The three ways forward that were offered, and which one was taken

1. Amend the acceptance test to drop `--strict`. **Not taken** — it would have lost the W3 calendar
   assertion `--strict` exists for.
2. Scope a `Workflow:Case` step carrying the alerts and field updates the triggers would name. **Not
   taken** — a re-plan needing new clarifications (who is warned, at what offset, from which sender,
   with which template) and at least two Case custom fields the field updates would stamp
   (`SLA_Breached__c`, `First_Response_Met__c` in the skill's example), neither of which exists in
   this build.
3. **Taken.** Deepen `admin/entitlements-and-milestones` to settle whether these elements are
   required, and scope the finding accordingly — commit `a18f9164d`, above. The artefact did not
   move; the rule did, and it moved because the guide said so.

The files below are on disk exactly as first built — no rebuild, no repair pass, no edit.

---

## 1. What this step deploys

| Type | Member | File |
|---|---|---|
| `MilestoneType` | `First Response` | `milestoneTypes/First Response.milestoneType-meta.xml` |
| `EntitlementProcess` | `First_Response_Premier` | `entitlementProcesses/First_Response_Premier.entitlementProcess-meta.xml` |
| `EntitlementProcess` | `First_Response_Standard` | `entitlementProcesses/First_Response_Standard.entitlementProcess-meta.xml` |

Both types support the `*` wildcard (`metadata-examples.md` § 6, api_meta.txt:88377 and 59306).
Members are named explicitly anyway, because this step's `manifest` acceptance test asserts two-way
member ↔ file consistency and a wildcard cannot be checked in that direction — the same convention
every earlier `package.xml` in this build follows.

`<version>67.0</version>`, matching `M3-S03`, `M3-S04` and `M4-S01`. `plan.json` carries **no**
`api_version` key (verified), so this is the build's prevailing convention rather than a plan value;
`M1-S01`, `M1-S02`, `M2-S01`…`M3-S02` carry `62.0` and the build is split 9 files to 3. Worth one
line at the M5 packaging gate, not a rebuild here.

## 2. Deploy order

**Inside this step — one order, and it is not optional:**

1. `MilestoneType` — `First Response`
2. `EntitlementProcess` — both files

`metadata-examples.md` § 7: *"`MilestoneType` … must resolve for the process's `milestoneName` …
references to bind. Deploying them in one package is the reliable way; the platform resolves
intra-package references."* § 1 says the same from the other end: *"A milestone must exist as a
`MilestoneType` component before any process can reference it by `milestoneName`. This is the step
that makes an `EntitlementProcess` deploy rather than fail."* The single `package.xml` in this
directory is what makes that one request.

**Dependencies on components outside this step:**

| Prerequisite | Owner | Why it must land first |
|---|---|---|
| `Settings:BusinessHours` — the `US Support` calendar | **M4-S01** (`documented`) | Both processes and both milestone overrides name `US Support`. A process naming a calendar the org does not have fails the deploy, or silently counts on a calendar nobody reviewed (checker W3). |
| `CustomObject:Case` and `Account.Support_Tier__c` | **M1-S01** (`documented`) | `SObjectType` is `Case`; `exitCriteriaFilterItems` filters `Case.Status`. `Support_Tier__c` (values `Premier`, `Standard`) is what selects *which* of these two processes an account's entitlement points at — `workbook/01-objects-and-fields.md` **CWB-OBJ-009** already records that binding. |
| `Settings:Entitlement` with `enableEntitlements` true | **nobody — see § 5** | Entitlement Management is an org switch. Everything in this step is inert while it is off. |
| The `CompletionDate` writer | **M4-S05** (`pending`) | Not a deploy-order constraint — this step deploys without it — but without it every First Response milestone opens and never closes. See `milestone-completion-decision.md` § 4. |

**Where this step sits in the build-wide sequence:** position 10 of 10 (SLA), after routing
(`M3-S04`) and after `M4-S01`'s calendars.

## 3. `minutesToComplete` 720 for Standard is DERIVED, not answered — the one number carried to the gate

Premier is not in question. Q38's answer is *"a first response within 4 business hours"*,
`4 × 60 = 240`, and this step's own manual acceptance test pins it: *"the Premier process carries
`minutesToComplete` 240"*.

**Standard is.** Q38 says *"standard accounts within 1 business day"* and nothing anywhere in this
build converts a business *day* into minutes. `minutesToComplete` is an int and the checker's **E1**
makes it mandatory, so the file cannot be written without choosing a number.

**What was written and how it was derived:** `720`. The chain, each link traceable:

1. Q51 makes the Case's calendar the SLA authority, and a process carries exactly one
   `<businessHours>` name, so the process calendar is the Case default calendar.
2. Q40 and `answers-key.md` name that calendar: *"unknown accounts default to US. US is the default
   calendar."* `artefacts/M4-S01/settings/BusinessHours.settings-meta.xml` confirms `US Support`
   carries `<default>true</default>`.
3. That file gives `US Support` as 08:00:00.000Z → 20:00:00.000Z, Monday to Friday — **12 open hours,
   720 business minutes, per day.** `requirement.md` L17 says the same ("the US works New York
   08:00–20:00").
4. `minutesToComplete` counts business minutes on that calendar, so one full open day is 720.

**The two readings this rejects, both defensible, neither sourced:**

| Reading | Minutes | Why it was not taken |
|---|---|---|
| One conventional 8-hour working day | `480` | Neither calendar in this build is an 8-hour day (US is 12, EMEA is 10). 480 would also collide numerically with M4-S04's 8-business-hour escalation threshold, making the first-response target and the escalation timer indistinguishable. |
| "By the end of the next business day" — a calendar-date promise | not expressible | The milestone model has only an integer minute target; there is no next-business-day element. |
| One full **EMEA** open day (08:00–18:00) | `600` | The process can name only one calendar, and `US Support` is the default one. An EMEA-account Standard case therefore gets a 720-minute target counted on US hours — see § 4. |

**This is an UNCONFIRMED placeholder, exactly like M4-S01's 14-holiday seed** (`decisions.md`
**D-M4S01-02**): computed rather than recalled, shown rather than asserted, and carried to the gate.
**Remedy:** the Process Owner confirms what "1 business day" means contractually — 720, 480, or a
next-business-day promise that needs a different design — before this file is deployed to production.
The edit is one integer in one file.

## 4. UNVERIFIED and ungrounded — every element this step could not settle from the cited skills

Each of these is recorded rather than guessed, per the grounding rule that cost two earlier steps a
rebuild.

### 4.1 The process file names are not the names a retrieve will produce — UNVERIFIED

`plan.json` declares `First_Response_Premier.entitlementProcess-meta.xml` and
`First_Response_Standard.…`, and this step wrote exactly those paths because the plan's `outputs[]`
is the file list. But `metadata-examples.md` "Where the files live" and `gotchas.md` gotcha 12 both
state the file name is **derived, not chosen**: it is `slaProcess.NameNorm`, *"the lowercase version
of the `name` field"*, with `_v<n>` appended when versioning is on (api_meta.txt:59078–59084). The
guide's own example turns `gold_support` into `gold_support_v2.entitlementProcess`.

So a retrieve from a real org would return `first_response_premier.entitlementProcess-meta.xml` —
lowercased — not the mixed-case name declared here. The skill's instruction is unambiguous: *"never
hand-write the first one: create the process, retrieve `EntitlementProcess`, and edit the file the
org gave you."* This build is `design-only` with no org, so that cannot be done here.

`<name>` was set to match the declared file base name (`First_Response_Premier` /
`First_Response_Standard`) so the two agree with each other. **Remedy:** after the first deploy,
retrieve `EntitlementProcess` and reconcile these file names — and the `package.xml` members below —
against what the org returns. Expect a rename to lowercase.

### 4.2 The `package.xml` member form for `EntitlementProcess` — UNVERIFIED

`metadata-examples.md`'s table gives the member as `premier_support_v1` — the file base name, i.e.
NameNorm with the version suffix. With versioning **off** (§ 4.3) there is no `_v<n>` suffix, and the
reference documents no worked example of the versioning-off member form. The members above are the
declared file base names, which is the only form consistent with the two-way manifest check. Settled
by the same retrieve as § 4.1.

### 4.3 No versioning elements written — grounded, but the consequence is worth stating

`versionMaster`, `versionNumber`, `isVersionDefault` and `versionNotes` are **absent** from both
files, deliberately. Assumption **A24** (from deferred Q92) records that entitlement versioning is
off. `gotchas.md` gotcha 12 is explicit about what happens if they are written anyway in such an org:
those fields are available *"in organizations that have entitlement versioning enabled"* only, and an
admin who adds them without the switch *"deploys, and gets either a failure or a second independent
process."*

Two consequences, both benign here and both real:

- The checker's **E2** (two defaults on one `versionMaster`) and **W5** (no default for a
  `versionMaster`) are both skipped, because the checker short-circuits on an empty `versionMaster`.
  Neither rule is being evaded — there is no version master to check.
- **Changing either SLA later is not an in-place edit.** `metadata-examples.md` § 7 records that
  `SlaProcess` supports no `create()` or `update()`, so the safe change procedure is a new versioned
  file — which first requires turning `enableEntitlementVersioning` on. Gotcha 12: deploy that switch
  *"as a separate, earlier change than the first versioned process."* Q92's owner question is still
  unanswered.

### 4.4 One calendar per process, against Q51's "the Case's calendar is the authority" — a real tension

Q51's answer is *"The Case's calendar is the authority for the first-response SLA; set the process and
milestone calendars to match it explicitly rather than relying on a default."* This step did set both
explicitly — `<businessHours>US Support</businessHours>` on each process **and** on each milestone
override, which is the "explicitly, not by default" half. It cannot do the "match the Case's
calendar" half, because:

- `admin/business-hours-and-holidays` `gotchas.md` **#5**: *"Milestones read the process calendar, not
  the Case calendar, unless told otherwise… Neither reads `Case.BusinessHoursId` by default."* There
  is no `businessHoursSource` element on an entitlement process — that element belongs to escalation
  rules (`gotchas.md` #3), which is why M4-S04 can follow the Case and this step cannot.
- `<businessHours>` takes one calendar name. M4-S03's before-save Flow stamps `Case.BusinessHoursId`
  to `EMEA Support` **or** `US Support` from `Account.Region__c` (Q40). One static name cannot be both.

`US Support` was chosen as the one name because it is the org default (`<default>true</default>` in
M4-S01's file) and the documented fallback for unknown accounts (Q40, `answers-key.md`).

**The consequence, stated plainly for the gate:** an EMEA-region case counts its first-response
milestone on **US Support** hours (08:00–20:00 New York) while its *escalation* timer counts on
**EMEA Support** hours (08:00–18:00 London, `businessHoursSource = Case`, Q43). The two SLA clocks on
the same case run on different calendars and pause on different holidays. `gotchas.md` #5 names this
exact divergence as the failure it exists to prevent — *"a Case with a regional calendar can escalate
on the regional clock while its first-response milestone counts on the process calendar"* — and its
prescribed fix is to *"choose one authority per SLA policy."*

**Remedy, for the M4 gate, none of it this step's to choose:** either (a) accept the divergence and
record it; (b) split each tier into a US and an EMEA process (four processes, contradicting assumption
**A27**, which fixes the count at two — a re-plan); or (c) re-point M4-S04's Tier 2 entry to
`businessHoursSource = Static` on `US Support` so both clocks agree, which contradicts Q43's answered
`businessHoursSource = Case`. **Not resolvable inside this step.**

### 4.5 `entryStartDateField` = `SlaStartDate` — a documented default, not an answered value

No clarification asks when the *entitlement* clock starts. Q42 answers the question for the
**escalation rule** (`CaseCreation`, "because the requirement measures from creation") and its scope
is M4-S04, not this step. `SlaStartDate` is the value `metadata-examples.md` § 2 uses in its worked
example, annotated *"The clock starts when the case enters the process"*, and it is one of the five
documented values (`SlaStartDate, CreatedDate, ClosedDate, LastModifiedDate, StopStartDate`,
api_meta.txt:59110–59117). Recorded as **a skill default**, not as a decision.

If the gate decides the first-response clock must measure from case creation to match the escalation
timer, the change is `<entryStartDateField>CreatedDate</entryStartDateField>` in both files.

### 4.6 `<active>true</active>` — chosen, and not the same choice M4-S04 made

M4-S04 ships its escalation rule **inactive** (Q47: *"Deploy the rule inactive, then activate inside a
defined comparison window"*). Q47 is answered against the escalation rule and names no other
component; no clarification covers entitlement-process activation. `metadata-examples.md` § 2's worked
example carries `<active>true</active>`, and an inactive process tracks nothing, so `true` was written.

Worth one line at the gate: the build's two SLA engines will go live on different switches — the
milestones the moment this deploys, the escalation rule only when a human activates it.

### 4.7 `exitCriteriaFilterItems` = `Case.Status equals Closed` — A9, with gotcha 9 attached

Assumption **A9** (from deferred Q49) is *"the entitlement process ends when the case is closed"*, and
it is written exactly as the § 2 worked example writes it. `gotchas.md` **gotcha 9** is the attached
warning: `none` recurrence means the milestone occurs once *"until the entitlement process exits"*, so
with this exit criterion **closing and reopening a case starts a fresh first-response timer** on a
conversation that has been running all week. The gotcha's suggested alternative is a boolean such as
`Case.SLA_Complete__c equals true`, stamped once — which would need a new Case field no step owns.

Q49's remedy at the gate: confirm whether a reopen is a new commitment. If it is not, this needs the
field and a stamp, which is a re-plan.

## 5. What this step does NOT write, and who does

| Not written | Why | Where it belongs |
|---|---|---|
| `settings/Entitlement.settings-meta.xml` (`enableEntitlements`, `enableEntitlementVersioning`, `enableMilestoneStoppedTime`) | Not in `steps[M4-S02].outputs[]`, and `metadata-builder` writes only declared metadata. **No step in this plan owns it.** | **Gap, carried to the M4 gate.** `enableEntitlements` is the master switch — every file in this step is inert without it (`metadata-examples.md` § 5). `enableMilestoneStoppedTime` is the one `gotchas.md` #10 says to turn on *before* go-live, not after the first dispute. |
| `EntitlementTemplate` | Not declared; `metadata-examples.md` § 4 shows it and nothing in the plan asks for one. | Relevant if Acme wants entitlements auto-created with a calendar — `gotchas.md` #11 notes a Flow cannot write `Entitlement.BusinessHoursId`, so the template is how a calendar gets on an entitlement. Not in this phase. |
| `workflows/Case.workflow-meta.xml` | See § 0. | Nowhere in this plan. |
| The `CompletionDate` writer | D10 assigns it to M4-S05. | `milestone-completion-decision.md`. |
| Anything that stamps `Case.EntitlementId` | Q48 / M4-S03's before-save Flow. `gotchas.md` **#2**: without `EntitlementId` on the Case, *"no milestone timers appear… the entitlement process only triggers when `Case.EntitlementId` is populated at case creation."* | **M4-S03** (`pending`). Until it is built, these processes are unreachable — no case will ever enter one. |

## 6. Files written

```text
artefacts/M4-S02/
├── entitlementProcesses/
│   ├── First_Response_Premier.entitlementProcess-meta.xml    declared
│   └── First_Response_Standard.entitlementProcess-meta.xml   declared
├── milestoneTypes/
│   └── First Response.milestoneType-meta.xml                 declared
├── milestone-completion-decision.md                          declared
├── package.xml                                               declared
└── deploy-order.md                                           undeclared (§ preamble)
```

DX source format, directory-per-type, per `skills/devops/salesforce-dx-project-structure`.

## 7. Validate-only command, for a human to run — this agent ran nothing

Validate-only. It does not save to the org. Run it only after M4-S01's `Settings:BusinessHours` and
`Settings:Entitlement` (§ 5) are in the target, and run it against a sandbox.

```bash
sf project deploy validate \
  --manifest .sfskills/builds/case-onboarding/artefacts/M4-S02/package.xml \
  --source-dir .sfskills/builds/case-onboarding/artefacts/M4-S02 \
  --target-org acme-sandbox
```

The retrieve that settles § 4.1 and § 4.2, also for a human:

```bash
sf project retrieve start \
  --metadata MilestoneType EntitlementProcess \
  --target-org acme-sandbox
```
