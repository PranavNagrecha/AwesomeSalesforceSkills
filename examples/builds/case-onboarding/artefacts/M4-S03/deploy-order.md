# Deploy order — `M4-S03`, the before-save stamping Flow

Components: `Flow:Case_BeforeSave_StampEntitlementAndCalendar`,
`FlowTest:Case_BeforeSave_StampEntitlementAndCalendar_Test`, `Settings:Flow`.
`flow-governance-policy.yaml` is a build artefact and is deliberately **not** a manifest member.

---

## 0. Rebuild record — F-38: a Create-triggered `FlowTest` takes `InputTriggeringRecordInitial` **only**

**This step has been rebuilt twice, both times for F-38, and the org corrected its own first
answer between them.** The rule the org has now settled, and the one the skill is being corrected
to carry:

> **`recordTriggerType Create` → `InputTriggeringRecordInitial` only.
> `Update` / `CreateAndUpdate` → both `Initial` and `Updated`.**

### The three runs

| Run | `flowtests/…_Test.flowtest-meta.xml` | Org verdict (`reports/MOCK-DEPLOY-M4.md`) |
|---|---|---|
| Build `2026-09-12T08-11-40Z` | `Updated` only | **run 2 rejected**: *"The test point for elementApiName \"Start\" is missing a parameter of type InputTriggeringRecordInitial."* |
| Rebuild `2026-09-12T08-30-00Z` | `Initial` + `Updated` | **run 3 rejected**, the mirror message: *"The test point for elementApiName \"Start\" contains the incompatible parameter value \"$Record\" of type InputTriggeringRecordUpdated. Remove the parameter or change the record trigger type."* |
| Rebuild `2026-09-12T08-40-00Z` (this one) | `Initial` only | to be validated in run 4 |

Run 3 accepted **54 of 55** components — every other artefact in this step and in the build, F-37
closed, only the `FlowTest` outstanding.

### What changed in this rebuild, and only this

The `<parameters>` block carrying `<type>InputTriggeringRecordUpdated</type>` was **removed** from
the `Start` test point. The `InputTriggeringRecordInitial` block added in the previous rebuild
stays exactly as it was, and is now the whole test input. Nothing else in the file moved, and the
other five artefacts — the flow, `settings/Flow.settings-meta.xml`, `package.xml`,
`flow-governance-policy.yaml` and `no-account-fallback-note.md` — are **byte-identical to the very
first build** across all three runs (SHA-256 confirmed at each one). The flow validated against the
org on first contact in run 2 and has never been reopened.

### Why the guide's sample pointed the wrong way

`api_meta.txt` L74351–74365 supplies **both** parameters, and L74326–74327 enumerates both types
without scoping either to a trigger type. Neither fact is wrong; the sample's flow is
**update-triggered**, and the skill's own worked `FlowTest`
(`flow/record-triggered-flow-patterns` `references/metadata-examples.md` § 4) is the after-save
`Opportunity_AfterSave_ClosedWon` test, which is where the two-parameter shape belongs — the file
even says so: *"The two `$Record` parameters below are what makes this a **transition** test."*
This step inherited that shape for a create-triggered flow, where there is no transition to
express. `InputTriggeringRecordInitial` alone is the record being inserted.

`flow/record-triggered-flow-patterns` is being corrected in parallel with a Create-triggered
`FlowTest` example and a checker rule for the `Create → Initial only` direction. This artefact did
not wait for it and **no skill file was edited by any of these runs.**

### UNVERIFIED — what is still not settled by the guide

The rule above is **proven live and unstated in the guide**: nothing in `api_meta.txt` marks
either parameter required, forbids `Updated` on a create, or connects `FlowTestParameterType` to
`recordTriggerType` at all. Both org messages are the authority, and the guide is silent on both.
That is the same shape as F-27's `casePriority` (`artefacts/M3-S03/deploy-order.md` § 0) and F-36's
`notifyToTemplate` (`decisions.md` **D-M4S04-01**). Two things this build still cannot settle:

1. The converse half of the rule — that a `CreateAndUpdate` flow requires **both** — is inferred
   from the guide's sample and from run 3's error text, not observed. No flow in this build is
   `CreateAndUpdate`, so nothing here tests it.
2. What a create-context `Initial` payload *means* to the engine: the record as submitted is the
   only reading available, and it is what this file supplies.

### The flywheel line for the M4 gate

F-38 is the third org-only constraint in this build that no checker in the library could have
caught (F-27 `casePriority`, F-36 `notifyToTemplate`, F-38 here), the second where a builder's
UNVERIFIED marker named the constraint before a deploy proved it — and the **first where two
successive org round-trips were needed to establish the rule**, because the first rejection
("missing `Initial`") is satisfied by both the two-parameter shape and the correct one-parameter
shape. An error message that narrows the space without closing it is worth the skill carrying
verbatim, alongside the rule.

---

## 0b. The F-27 decision this step was told to make, and which way it went

The step's `notes` (amendment `2026-09-12T04:50:22Z`) put two options to the builder: derive
`Priority` from `Severity__c` / `Support_Tier__c` and **overwrite** the Email-to-Case intake
default, or **accept `Medium`** for email cases — *"and say which in deploy-order.md"*. This is
that sentence.

**Option 2 was taken: the flow derives `Priority` and overwrites on the `Email-Support` and
`Email-Billing` origins.**

That is not this step's choice to make and it was not made here. The `milestone:M3` human gate,
approved `2026-09-12T06:24:17Z`, records it as gate decision (2):

> *"D-M3S03-02: option 2 — M4-S03 derives Priority from Severity__c/Support_Tier__c and
> OVERWRITES the routing-address default for Email-\* origins (M4-S03 notes already say so); this
> also closes F-32 because the before-save flow runs before Priority_Required_On_Agent_Save
> evaluates."*

`decisions.md` **D-M3S03-02** is the entry that raised the three options; the gate closed it on
option 2. This step implements the approved option and adds nothing to it.

**Where the null guard still holds.** `inputs.note` says the flow *"writes only when the field is
null and never overwrites an agent's value"* (assumption **A2**, from deferred **Q14**). That rule
is unchanged for `EntitlementId` and `BusinessHoursId` — both are guarded by an explicit
`IsNull` condition — and is superseded **for `Priority` on the two email origins only**. On every
other origin, including `Web` and a manually created Case, `Priority` is still written only when it
arrives null, which is what keeps A2 intact for a human's value.

Implemented as one condition set on `Decision_Derive_Priority`:

| # | Condition | Meaning |
|---|---|---|
| 1 | `$Record.Origin EqualTo Email-Support` | the routing address already set `Medium` (`M3-S03`) — overwrite it |
| 2 | `$Record.Origin EqualTo Email-Billing` | same |
| 3 | `$Record.Priority IsNull` | web and API cases — the A2 null guard |

`(1 OR 2 OR 3)` is the "may this flow write `Priority`?" half of both outcomes. A Case that
matches none of the three keeps the Priority a human typed: default outcome
`Priority_Entered_By_A_Human_Is_Kept`.

---

## 1. UNVERIFIED — the Priority **values** are derived, not answered

**This is the single item on this step that a human has to confirm before deploy.** The gate chose
the *mechanism*. No answered clarification anywhere in this build states which `CasePriority` value
a Severity 1, a Premier or a Standard case should end up with. `M3-S03`'s own
`web-to-case-form-contract.md` § 7 already recorded the same gap from the other side: *"no answered
clarification states which `CasePriority` value each channel should end up with."*

The mapping written into the flow, and the chain that produced each row:

| Outcome | Written value | What grounds the row | What does **not** |
|---|---|---|---|
| `Severity__c = Severity 1` | `High` | `requirement.md` L18 "Severity 1 outages are 24/7 and never pause" — the only unconditional urgency statement in the requirement; `Severity__c` has exactly one value (`artefacts/M1-S01/objects/Case/fields/Severity__c.field-meta.xml`) | nothing says the value is `High` rather than a 4th, `Critical`-style value the org does not carry |
| `Support_Tier__c = Premier` | `High` | Q38: Premier is promised 4 business hours against Standard's 1 business day, so Premier outranks Standard; the M3 gate named `Support_Tier__c` as a derivation input, so leaving it unused would not implement option 2 | nothing says a Premier case is *urgent*; tier is a contractual speed, and mapping it onto `Priority` conflates two mechanisms. This is the weakest row in the table |
| everything else writable | `Medium` | `M3-S03` already sets `casePriority` `Medium` on both routing addresses (F-27), so `Medium` is this build's established intake value | — |

**The values themselves are grounded, the mapping is not.** `High`, `Medium` and `Low` are copied
from `skills/admin/case-management-setup/references/metadata-examples.md` § 1
(`standardValueSets/CasePriority.standardValueSet-meta.xml`, `Medium` carrying `<default>true</default>`)
— the same file `artefacts/M1-S01/standardValueSets/CaseOrigin.standardValueSet-meta.xml` was
copied from. **No `CasePriority` value set exists anywhere under `artefacts/`**, so no checker in
this build can assert that `High` is a value this org actually carries; only a deploy or a live
org can.

**Two readings that were considered and rejected, both defensible:**

- *Severity-only* — `Severity 1` → `High`, everything else `Medium`, leaving `Support_Tier__c`
  unread. Rejected because the gate's option 2 names `Support_Tier__c` as a derivation input;
  implementing a rule that never reads it would be answering a different question than the one
  approved.
- *Tier-only* — `Premier` → `High`, `Standard` → `Medium`, ignoring severity. Rejected because
  `requirement.md` L18 is the stronger statement of the two and a Severity 1 case on a Standard
  account would land `Medium`.

**Remedy, one edit:** the Process Owner confirms the three rows above. The change is two
`<stringValue>` elements in one file, and it is the same shape as `D-M4S02-02`'s `720` — a
computed value shown rather than asserted, carried to the M4 gate rather than presented as
answered.

---

## 2. Deploy order

| # | Component | Built by | Why here |
|---|---|---|---|
| 1 | `CustomField Account.Region__c`, `Account.Support_Tier__c`, `Case.Severity__c`; `StandardValueSet CaseOrigin`; `CustomObject Case` | `M1-S01` | The flow's conditions name all four. A flow referencing a field that does not exist yet fails at deploy, not at run time (`record-triggered-flow-patterns/references/metadata-examples.md` § 7 step 2) |
| 2 | `Settings:BusinessHours` — `US Support`, `EMEA Support` | `M4-S01` | `Get_EMEA_Support_Calendar` and `Get_US_Support_Calendar` filter on `Name`. They are **run-time** dependencies, not deploy-time ones: the flow deploys against an org with no such calendars and simply stamps nothing |
| 3 | `EntitlementProcess` + `MilestoneType` | `M4-S02` | Also run-time, not deploy-time: `Get_Active_Entitlement` reads `Entitlement`, a standard object. Without `M4-S02` deployed, a stamped `EntitlementId` enters no process |
| 4 | **`Settings:Flow`** | **this step** | `enableFlowDeployAsActiveEnabled` decides whether step 5 activates or lands Draft. Deploying it *after* the flow changes what the flow deploy meant (`flow-governance/references/metadata-examples.md` § 8 row 2) |
| 5 | **`Flow:Case_BeforeSave_StampEntitlementAndCalendar`** and **`FlowTest:…_Test`** | **this step** | Deploy the test **with** the flow, not after (`flow-governance` § 8 row 4) |
| 6 | `EscalationRules Case` | `M4-S04` | Not a dependency of this step; this step is a dependency of *its activation*. `artefacts/M4-S04/escalation-activation-runbook.md` § 4 R1: entry 2 is `businessHoursSource = Case` and must not be activated before this flow is live |

### Components outside this step that this step's behaviour depends on

- `settings/Entitlement.settings-meta.xml` (`enableEntitlements`) — **owned by no step in this
  plan** (`decisions.md` **O-M4S02-01**). Without it every entitlement this flow stamps is inert.
- `settings/Case.settings-meta.xml` (`M3-S03`) — the two routing addresses whose
  `casePriority Medium` § 0 overwrites.

### Validate-only command, for a human to run

This agent does not run it, and nothing in this loop deploys.

```bash
sf project deploy validate \
  --manifest .sfskills/builds/case-onboarding/artefacts/M4-S03/package.xml \
  --target-org <sandbox-alias> \
  --test-level RunLocalTests
```

---

## 3. `<apiVersion>` 67.0, and the one place the cited skill says 66.0

The flow carries `<apiVersion>67.0</apiVersion>`, matching `package.xml` `<version>67.0</version>`
and the build-wide 67.0 the `milestone:M3` gate accepted (decision 6, `O-M3S03-01`/F-31). It is
copied from this step's own cited template, `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`,
which carries `67.0`.

`flow/record-triggered-flow-patterns/references/metadata-examples.md` writes `66.0` in all three of
its worked flows. The difference is recorded rather than hidden, and it changes nothing here: the
policy floor is `min_api_version: 59`, and every element this flow uses has a version floor far
below both — `RecordBeforeSave` 48.0, `triggerOrder` 54.0, `FlowTest` 55.0,
`<testType>WithAssertion</testType>` 66.0.

---

## 4. `Settings:Flow` carries one field, on purpose

`settings/Flow.settings-meta.xml` sets `enableFlowDeployAsActiveEnabled` and nothing else. The
skill's § 1 example carries thirteen fields, and twelve of them are org-wide governance decisions
no clarification in this build asks about — `isFlowBlockAccessToSessionIDEnabled`,
`enableFlowInterviewSharingEnabled`, `enableFlowUseApexExceptionEmail` and the rest each change what
*every* flow in the org may do. A case-intake build is not the change that should make them.

Two things to know before deploying the one field that is set:

- **UNVERIFIED — partial settings deploys.** Whether a `FlowSettings` file containing one element
  leaves the org's other twelve values untouched, or resets them, is not stated in either cited
  skill. `api_meta.txt` L116824–116826 says only that there is one settings file per settings
  component. Confirm against a sandbox retrieve before deploying to production.
- **`true` has a production cost the guide states outright:** *"deploying an active process or flow
  in a production org causes your Apex tests to run. If Apex tests don't launch your org's required
  percentage of active processes and autolaunched flows, the deployment is rolled back"*
  (`api_meta.txt` L116877, quoted in `flow-governance/references/metadata-examples.md` § 1). The
  build's only Apex is `M4-S05`, which is not built. **A production deploy of this step at
  `<status>Active</status>` can therefore be rolled back for a reason that has nothing to do with
  this flow.** The sandbox path is unaffected — the same field defaults to `true` in non-production
  orgs.

`<status>Active</status>` is what the step's own acceptance test for `check_flow_governance.py`
describes and what `require_flow_test_for_active` in the policy is written against. It is also the
one status choice here that a human should re-read at the gate, because `M4-S04`'s escalation rules
deliberately ship `<active>false</active>` and this flow does not.

---

## 5. UNVERIFIED / ungrounded — what this step could not settle

| # | Item | Why it is open |
|---|---|---|
| U1 | **The Priority mapping** (§ 1) | The largest of these. Mechanism approved at the M3 gate; values derived |
| U2 | **A before-save flow has no documented fault-path shape** | `flow/flow-element-naming-conventions` Pattern 5 wants each fault routed to `LogFault_<Parent>`, and `templates/flow/FaultPath_Template.md` defines that target as one that logs *"via an `Application_Log__c` record"* (line 11) — summarised by the cited skill as *"capture `{!$Flow.FaultMessage}`, write one `Application_Log__c` row"* (`record-triggered-flow-patterns/references/metadata-examples.md` L20–21). A `RecordBeforeSave` flow may contain no `recordCreates` at all (`check_record_triggered_flow_patterns.py` rule 2), so that target cannot exist here. The four `faultConnector`s therefore route to the next Decision — the interview continues on the documented fallback instead of stopping silently, which is what rule 4 exists to prevent — and `check_flow_element_naming_conventions.py` reports four `W-FAULT-TARGET` WARNs for it (advisory; exit 0). **Neither cited skill documents what a before-save fault path should look like.** That is a gap in the library, not a defect in this file |
| U3 | **`Entitlement.Status EqualTo Active`** | `Active` is copied from `skills/admin/entitlements-and-milestones/references/metadata-examples.md` § 8 (`WHERE Status = 'Active'`), and `references/gotchas.md` #11 confirms `Status` carries `Filter` so it is filterable. The **full** `Status` picklist is not enumerated in any file this step read |
| ~~U4~~ | ~~**The `FlowTest`'s `InputTriggeringRecord*` parameters**~~ | **CLOSED by F-38, over two org round-trips.** The rule is `recordTriggerType Create` → `Initial` only; `Update`/`CreateAndUpdate` → both. This file now supplies `Initial` alone. See § 0, which also records the two halves the guide still leaves unstated: nothing in `api_meta.txt` marks either parameter required or ties `FlowTestParameterType` to `recordTriggerType`, and the `CreateAndUpdate` → both half is inferred rather than observed |
| U5 | **`Get_Active_Entitlement` takes the first matching row** | `getFirstRecordOnly true` with no sort. An account with two active entitlements gets an arbitrary one. No clarification says what to do with two, and `assumption A27` fixes the *process* count at two without saying anything about entitlement records per account |
| U6 | **`flow-governance-policy.yaml` `owner:`** | Set to `Service Operations`, the **role** Q90 answered. Q90 did not name an individual, and `D-M4S01-02` already rejected inventing one. The flow `<description>`'s `Owner:` marker says the same and carries the same OPEN |
| U7 | **The `Flow.settings` naming advisory** | `check_flow_governance.py:711` globs the metadata-format name `Flow.settings`; this build uses DX `-meta.xml` naming throughout, so the checker reports *"Active flows but no settings/Flow.settings"* even though `settings/Flow.settings-meta.xml` is written. The artefact keeps the build's convention; the checker gap is recorded, not worked around. This is the documented expected outcome in the step's own acceptance test |
| U8 | **No `CasePriority` standard value set under `artefacts/`** | So `High` and `Medium` are unassertable by any checker here (§ 1). Pre-existing: `M3-S03` `web-to-case-form-contract.md` § 7 recorded it first |

### Three decision-checker advisories that are design, not defect

`check_flow_decision_element_patterns.py` is not one of this step's declared acceptance tests. It
was run anyway (`metadata-builder` Step 8 runs every cited skill's checker) and exited 0 with five
WARNs. Three of them say `$Record.Origin`, `$Record.Severity__c` and `Get_Account.Support_Tier__c`
are *"compared to a text value but no outcome tests it with IsNull or IsBlank"*. The check is
per-field and does not see the `OR` structure: a null in any of the three falls to
`Standard_Or_Untiered_And_Priority_Writable`, whose own condition 3 (`Priority IsNull`) is exactly
the guard the WARN asks for. A fourth WARN reports `Decision_Derive_Priority` has no
`defaultConnector` — correct, and deliberate: its default outcome is "change nothing", and a
before-save flow has no element that expresses that other than ending. The fifth reports the three
decisions chain three deep; they are three sequential segments (entitlement, calendar, priority),
not nested branching, and flattening them would merge three independent concerns into one element.

---

## 6. Verification, after a human deploys it

**Setup.** Setup → Process Automation → Flows → Flow Trigger Explorer, filtered to Case. The flow
appears once in the before-save context at run order 10, and the version marked *Active* is the one
just deployed.

**SOQL** (`record-triggered-flow-patterns/references/metadata-examples.md` § 8):

```sql
SELECT ApiName, Label, IsActive, ProcessType, TriggerType, RecordTriggerType,
       TriggerObjectOrEventLabel, TriggerOrder, IsOutOfDate
FROM FlowDefinitionView
WHERE TriggerObjectOrEventLabel = 'Case' AND TriggerType = 'RecordBeforeSave'
```

`IsActive = false` after a production deploy is § 4's rollback, not a build defect.

**Runtime**, one case per intake channel — the test `entitlements-and-milestones/references/gotchas.md`
#2 asks for explicitly:

```sql
SELECT Id, CaseNumber, Origin, Priority, Severity__c, EntitlementId, BusinessHoursId, AccountId
FROM Case
WHERE CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

Four things to read off it:

1. An `Email-Support` case on a Premier EMEA account: `Priority High` (**overwritten** from the
   routing address's `Medium` — this is the F-27 behaviour under test), `BusinessHoursId` = EMEA
   Support, `EntitlementId` populated.
2. A `Web` case with no account: `Priority` derived, `BusinessHoursId` = US Support,
   `EntitlementId` null — the documented fallback (`no-account-fallback-note.md`).
3. A Case an agent created by hand with a Priority already chosen: that Priority survives (A2).
4. Any row with `BusinessHoursId` null: the flow did not run, or both calendar lookups missed.
   Cross-check against `artefacts/M4-S04/escalation-monitoring-note.md`, which reads the same
   column as a failure signal.
