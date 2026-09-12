# Gotchas — Record Triggered Flow Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Grounding: save-order positions and versioned behaviour from the Apex Developer Guide
(`apexdev.txt`, *Triggers and Order of Execution*, L15402–15490); metadata field names,
enums, version floors and numeric limits from the Metadata API Developer Guide
(`api_meta.txt`); queryable verification fields from the Object Reference
(`object_reference.txt`). PDF sources are listed in `references/well-architected.md`.

## The Wrong Save Context Creates Architecture Debt Fast

**What happens:** A same-record field update is implemented in after-save, and the org pays the cost forever through extra DML and re-entry risk.

**When it occurs:** Teams choose after-save by default instead of checking whether the requirement is only about the current record.

**How to avoid:** Start with before-save unless the design clearly needs committed side effects.

---

## Broad Entry Criteria Makes Debugging Look Random

**What happens:** The flow appears to run unpredictably because it fires on unrelated updates and collides with other automations.

**When it occurs:** Start conditions are set to run on every update without field-specific logic or prior-value checks.

**How to avoid:** Use explicit criteria and changed-field logic wherever the business event is narrower than "any save."

---

## Flow And Apex Still Share The Same Object Lifecycle

**What happens:** Admins design a record-triggered flow as if it owns the object, but an Apex trigger or validation rule changes the outcome.

**When it occurs:** Mixed-automation orgs with declarative and programmatic logic on the same object.

**How to avoid:** Review record-triggered flows alongside order-of-execution neighbors instead of in isolation.

---

## `$Record__Prior` Only Helps If The Logic Actually Uses It

**What happens:** A flow is configured to run on update, but it does not compare the old and new value of the important field.

**When it occurs:** Teams rely on broad start criteria and forget to encode the real business transition.

**How to avoid:** Use prior-value comparisons or equivalent start logic whenever the requirement depends on a field changing, not merely being present.

---

## A Before-Save Assignment Persists With No Update Element At All

**What happens:** An agent writes a before-save flow, assigns `$Record.Field__c`, then adds an `Update Records` element "so the change saves." The extra element is a second DML on a record the platform was already about to write, and on some objects it re-enters the save procedure.

**When it occurs:** Whenever the author's mental model comes from Apex `after insert` (where you *must* re-query and update) rather than Apex `before insert` (where mutating `Trigger.new` is enough).

**How to avoid:** A `RecordBeforeSave` flow runs at save-order step 3 and the record is written at step 7 (`apexdev.txt` L15440, L15447) — the assignment is part of that write. The correct before-save flow contains `decisions` and `assignments` only, and no `recordCreates` / `recordUpdates` / `recordDeletes` / `actionCalls` / `subflows` (`references/metadata-examples.md` § 1). `scripts/check_record_triggered_flow_patterns.py` fails the build on any of those inside a before-save flow.

---

## "Meets The Condition" And "Changed To Meet The Condition" Are Different Flows

**What happens:** Entry criteria say `StageName = 'Closed Won'`. Every subsequent edit to a Closed Won opportunity — an owner change, a description tweak, a batch backfill — satisfies that condition again and the flow creates another Task. Nobody notices until a report counts duplicates.

**When it occurs:** On any state-shaped criterion, and especially under a data load that touches historical records.

**How to avoid:** Set `<doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>` on the `<start>` element: "If set to `true`, conditions evaluate to `true` only if the record didn't meet the required conditions before the triggering update but now meets the conditions after the update" — API 50.0+ (`api_meta.txt` L72322–72325). Note it is defined against a triggering **update**, which is why the after-save example uses `recordTriggerType` `Update`, not `CreateAndUpdate`.

---

## `filterFormula` And `filters` Are Two Different Fields, And Only One Of Them Has A Transition Switch

**What happens:** An author moves entry criteria into `<filterFormula>` because it is more expressive, and the transition guard silently disappears — `doesRequireRecordChangedToMeetCriteria` is documented against *conditions*, not against a formula.

**When it occurs:** During refactors, when criteria outgrow the simple `field / operator / value` shape of `FlowRecordFilter`.

**How to avoid:** `filterFormula` is "a formula that's used to filter what records execute the flow during a save. Available only in record-triggered flows", API 55.0+ (`api_meta.txt` L72390–72392); `filters` is a separate `FlowRecordFilter[]` field with its own `filterLogic`. Use `filters` + `doesRequire…` whenever the requirement is a transition, and reserve `filterFormula` for state tests a filter row cannot express. UNVERIFIED (2026-09-05): whether the two can be combined on one Start element, and how they interact if so, is not stated in `api_meta.txt` — verify in a sandbox before relying on it.

---

## A Recursive Save Skips Steps 9 Through 17 — Including After-Save Flows

**What happens:** An after-save flow updates a record, that update re-enters the save procedure, and the developer expects the after-save flow to fire again. It does not, at that nesting level. Assignment rules, workflow rules, escalation rules and roll-up recalculation are skipped too. The result is a design that behaves one way when a user saves and a different way when automation saves.

**When it occurs:** Any time a flow, trigger, or process performs DML on an object whose own save procedure is already in flight.

**How to avoid:** Read the note the guide puts directly above the 20-step list: "During a recursive save, Salesforce skips steps 9 (assignment rules) through 17 (roll-up summary field in the grandparent record)" (`apexdev.txt` L15414–15415). Step 14 — after-save record-triggered flows — is inside that window; steps 3, 4 and 8 (before-save flows, before triggers, after triggers) are not. Never reason about recursion from the flat 20-step list alone, and never rely on the skip as a recursion guard: it disappears the moment the second save originates outside the first.

---

## `triggerOrder` Is Not Set By Default, And Two Unset Flows Have No Declared Sequence

**What happens:** Two after-save flows on Opportunity both run. Which one runs first is not something you configured, and the answer can change. The symptom is a field that is correct in one org and stale in another with identical metadata.

**When it occurs:** Whenever a second record-triggered flow lands on an object in the same save context — usually because two teams each shipped "one small flow."

**How to avoid:** `<triggerOrder>` takes an int "from 1 to 2,000", API 54.0+ (`api_meta.txt` L68438–68441), and is queryable as `FlowDefinitionView.TriggerOrder` (`object_reference.txt` L139763–139769). Set it explicitly on every record-triggered flow, spaced by 10, and assert on it in the pipeline — a null `TriggerOrder` on any object with more than one flow in the same `TriggerType` is the finding. UNVERIFIED (2026-09-05): what the platform does when two flows carry the *same* `triggerOrder` value, or when both are null, is not stated in `api_meta.txt` or `object_reference.txt`; the guide points to a Salesforce Help page ("Guidelines for Defining the Run Order of Record-Triggered Flows for an Object") that cannot be fetched. Do not tell a customer the tie resolves any particular way — remove the tie instead.

---

## A Before-Save Flow Loses Every Field Contest With A Before Trigger

**What happens:** A flow and an Apex before-trigger both write `Rating`. The trigger's value is what saves — every time, not intermittently. An admin adds a condition to the flow to "fix" it and nothing changes, because the flow finished before the trigger started.

**When it occurs:** On any object where declarative and programmatic automation grew independently.

**How to avoid:** The steps are consecutive and documented: "3. Executes record-triggered flows that are configured to run before the record is saved. 4. Executes all before triggers" (`apexdev.txt` L15440–15441). The ordering is fixed, so the fix belongs in the later writer — condition the trigger, or give the field one owner. Note the corollary for after-save: after triggers are step 8 and after-save flows are step 14 (L15448, L15470), so an after-save flow reads whatever Apex left behind, not what the user typed.

---

## Scheduled Paths Batch Up To 200 Interviews, And The Default Is The Maximum

**What happens:** A scheduled path that does one Get and one Update per record works in a sandbox with ten records and fails in production, because 200 interviews were batched into one transaction and shared its governor budget.

**When it occurs:** On any scheduled path that performs per-record DML, callouts, or a Get that returns many rows — that is, most of them.

**How to avoid:** `<maxBatchSize>` is "the maximum number of scheduled path interviews to execute in a single batch, from 1 to 200. Default is 200" (`api_meta.txt` L71397–71398). Set it explicitly rather than inheriting 200, and size it against the per-interview work. Related: an `AsyncAfterCommit` path (`<pathType>`, `api_meta.txt` L71412–71415) runs as post-commit logic — "Asynchronous paths in record-triggered flows", `apexdev.txt` L15489 — outside the triggering transaction, so it cannot roll the save back and it may observe data that changed after the save. UNVERIFIED (2026-09-05): the running user and sharing context of a scheduled path is not stated in `api_meta.txt` or `apexdev.txt`; `<runInMode>` is a flow-level setting (L68374–68390) with no documented per-path override, so do not claim the path runs in system mode without proving it.

---

## There Is No After-Delete Record-Triggered Flow

**What happens:** A design says "when the Opportunity is deleted, write an audit row and notify the owner." The author looks for an after-delete trigger type, does not find one, and either abandons the requirement or reaches for Apex without knowing why.

**When it occurs:** On archival, audit, and cleanup requirements — the ones that surface late, usually after a mass delete has already happened.

**How to avoid:** `FlowTriggerType` offers `RecordBeforeDelete` — "Deleting a record triggers an autolaunched flow before the record is deleted from the database", API 50.0+ (`api_meta.txt` L72536–72538) — and no after-delete value anywhere in the enum (L72495–72547). Everything you need from the record must be copied out of `$Record` inside the before-delete flow, while the row still exists (`references/metadata-examples.md` § 3). Two delete paths are documented as not reaching Apex trigger evaluation at all: "Cascading delete operations. Only records that initiate a delete cause trigger evaluation" and reparenting from a merge (`apexdev.txt` L15523–15524) — while merges themselves do fire a delete event for the losing records (L15356–15357). UNVERIFIED (2026-09-05): that cascade list is written for Apex triggers; neither guide states whether record-triggered delete flows follow the same rule. Prove cascade coverage in a sandbox before an archival design depends on it.

---

## A Stale `FlowDefinition` Silently Pins Production To An Old Version

**What happens:** The deploy succeeds, the new flow version appears in Setup, and the org keeps running the old one. Nothing in the deploy output says so.

**When it occurs:** In repos that predate API 44.0 and still carry a `flowDefinitions/` directory, or in a package built by copying an older one.

**How to avoid:** "If you deploy with flow definitions, the active version numbers in the flow definitions override the status fields in the flows … the active version number in the flow definition is version 3, and the latest version of the flow is version 4 with the status field as `Active`. After you deploy your flow, the active version is version 3" (`api_meta.txt` L73929–73932, repeated L73198–73201). The guide's own upgrade checklist says the `flowDefinitions` directory should be empty and each active flow should carry `<status>Active</status>` (L73187–73189). Assert on `FlowDefinitionView.IsOutOfDate` after every deploy (`object_reference.txt` L139267–139273) — `true` means the active version is not the latest.

---

## The Flow's Own `apiVersion` Moves It In The Save Order

**What happens:** A flow retrieved from a legacy org, redeployed unchanged, runs in a different position relative to entitlement rules than a flow built today. Milestone and entitlement behaviour differs between two flows that look identical in Flow Builder.

**When it occurs:** During org migrations, package upgrades, and any retrieve-then-redeploy that preserves the original `<apiVersion>`.

**How to avoid:** "In API version 53.0 and earlier, after-save record-triggered flows run after entitlements are executed" (`apexdev.txt` L15509; repeated in the versioned-behaviour list at L44657). `<apiVersion>` is a real behavioural setting on the Flow, not metadata bookkeeping — "The API version that defines the execution behavior of the flow", API 50.0+ (`api_meta.txt` L68075–68078). Set it deliberately on every flow you ship and record it in the deploy notes.

---

## A Missing `faultConnector` Turns A Failure Into Silence

**What happens:** The related-record Update hits a validation rule, a record lock, or FLS. The interview stops. No log row, no Task, no error the user connects to the save they just did.

**When it occurs:** Most often at volume and out of hours, when the failing element is on a scheduled path nobody is watching.

**How to avoid:** `faultConnector` — "specifies which node to execute if the attempt … results in an error" — is declared on `FlowRecordCreate` (`api_meta.txt` L70965), `FlowRecordLookup` (L71120), `FlowRecordUpdate` (L71283) and `FlowRecordDelete` (L71046). Put one on every such element and land it on the shape in `templates/flow/FaultPath_Template.md`: one `Application_Log__c` row carrying `{!$Flow.FaultMessage}` and `{!$Flow.InterviewGuid}`. The terminal logger itself carries no fault path — that is deliberate, and the checker exempts any element that is the target of a `faultConnector`. For before-save, where there is no post-commit place to log, `FlowCustomError` is the documented alternative: it "roll[s] back a change that triggered a flow and inform[s] the user exactly what caused the error" (`api_meta.txt` L70006–70008).

---

## 11. A Create-Triggered `FlowTest` Takes One `$Record` Parameter, Not The Pair

**What happens:** A `FlowTest` is written the same way for every record-triggered flow — an `InputTriggeringRecordInitial` parameter plus an `InputTriggeringRecordUpdated` parameter on the Start test point, copied from the after-save transition-test shape in `references/metadata-examples.md` § 4.1. On a **Create**-triggered flow that shape does not deploy. Neither does dropping to `InputTriggeringRecordUpdated` alone, which is the other shape someone reaches for when told "Create means no prior value, so use the Updated one." Only `InputTriggeringRecordInitial` alone validates.

**When it occurs:** Any `FlowTest` against a flow whose Start element has `<recordTriggerType>Create</recordTriggerType>`. This was proven live, twice, in the same afternoon (case-onboarding milestone M4-S03, `sf project deploy start --dry-run`, API 67.0, 2026-09-12) — not read out of the Metadata API Developer Guide, which documents `FlowTestParameter`'s fields (`api_meta.txt` L74305–74306) and the `FlowTestParameterType` enum (L74326–74327) but states no relationship between `type` and the target flow's `recordTriggerType` anywhere in either guide.

Both runs produced org error text that is worth quoting exactly, because the fix for one looks like the other mistake:

- Start test point carrying `InputTriggeringRecordUpdated` only: `The test point for elementApiName "Start" is missing a parameter of type InputTriggeringRecordInitial.`
- Start test point carrying **both** parameters: `The test point for elementApiName "Start" contains the incompatible parameter value "$Record" of type InputTriggeringRecordUpdated. Remove the parameter or change the recordTriggerType for the flow.`
- Start test point carrying `InputTriggeringRecordInitial` only: validates.

**The trap is specifically in the first message.** "Missing a parameter of type InputTriggeringRecordInitial" reads as "add that parameter" — true, but incomplete. Run 2's version of that exact message came from a test point that already had `InputTriggeringRecordUpdated` sitting on it; adding `InputTriggeringRecordInitial` *alongside* it (the natural reading of the error) produces the second message instead of a pass. The same missing-Initial message is satisfied by two different shapes — "has Updated, needs Initial added" and "has neither, needs Initial added" — and only replacing `InputTriggeringRecordUpdated` with `InputTriggeringRecordInitial`, not adding to it, is the one that validates.

**How to avoid:** Match the parameter to `recordTriggerType`, not to a copy-pasted template: `Create` → `InputTriggeringRecordInitial` only. `Update` → both (`references/metadata-examples.md` § 4.1 — the guide's own sample, L74351–74365, is an update-triggered flow). `CreateAndUpdate` → UNVERIFIED (2026-09-12): not observed live in either direction, and not stated in `api_meta.txt` or `apexdev.txt` — do not guess which shape it wants; prove it in a sandbox first. `scripts/check_record_triggered_flow_patterns.py` rule 9 checks this automatically by resolving the `FlowTest`'s `<flowApiName>` against the matching flow's `<recordTriggerType>` in the same manifest, ERRORing on the two Create shapes above and flagging `CreateAndUpdate` as INFO-only, unenforced.
