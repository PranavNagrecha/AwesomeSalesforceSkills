# Gotchas - Flow Testing

Grounding: `api_meta.txt` = Metadata API Developer Guide, `apexdev.txt` = Apex Developer
Guide, `apexrefguide.txt` = Apex Reference Guide (Summer '26 / v66 extracts, line numbers
as cited).

## Gotcha 1: Debug runs feel safer than they are

**What happens:** A successful manual debug session creates false confidence. Nothing is
persisted, so the next change has nothing to regress against.

**When it occurs:** Teams substitute diagnostics for repeatable regression coverage,
usually because the debug window is the only testing surface they have seen.

**How to avoid:** Use Debug to learn, then convert the important path into a durable test
asset — a `FlowTest` component for the three types that support one, an Apex test driving
`Flow.Interview` for autolaunched flows, `references/metadata-examples.md` §2 and §5.

---

## Gotcha 2: Fault paths rarely get covered accidentally

**What happens:** Production failures appear in scenarios nobody ever tested, because the
fault route only executes when the DML it guards actually fails.

**When it occurs:** Test data is created only for the expected happy path.

**How to avoid:** Assert on the fault route from the happy-path side too. `HasError`
against an element API name is a `FlowComparisonOperator` from API version 64.0
(`api_meta.txt` L74196); asserting it is `false` proves the clean path stayed clean, which
is the half of fault coverage a `FlowTest` can actually reach.

---

## Gotcha 3: Flow tests do not replace boundary tests

**What happens:** A flow test passes, but the invocable Apex or custom screen component
still behaves incorrectly.

**When it occurs:** Teams assume the orchestration test covers every dependency in full
depth.

**How to avoid:** Pair the flow-level test with a test at the boundary's own layer — Apex
`@IsTest` for invocable methods, Jest for screen components (`lwc/lwc-testing`).

---

## Gotcha 4: Test data quality drives test value

**What happens:** Tests pass because they rely on accidental org state rather than
deliberate setup.

**When it occurs:** The test design does not define what data each path truly needs.

**How to avoid:** For `FlowTest`, the record images are inline JSON in
`sobjectValue` — nothing is read from the org, so the images have to be complete. For
Apex, `flowTestDataSources` names an Apex class as the data source (`dataSourceType` =
`ApexClass`), available from API version 66.0 (`api_meta.txt` L74070–74090), which is the
supported way to point a flow test at a factory instead of at inline literals.

---

## Gotcha 5: A FlowTest can only assert at the start and the end of the flow

**What happens:** `testPoints.elementApiName` is required and accepts exactly two values,
`Start` and `Finish` (`api_meta.txt` L74143–74150). There is no way to name a Decision, a
Loop or a Get Records element as a test point, so no assertion can observe the interview
mid-run. A team that plans "assert after the Decision, then assert after the Update" finds
the shape simply does not exist.

**When it occurs:** Whenever a flow's interesting state is transient — a collection built
inside a loop, a value overwritten by a later assignment, a branch that leaves no trace on
the record.

**How to avoid:** Give each branch a flow-scoped variable to write, and assert on the
variables from the `Finish` point. `references/metadata-examples.md` §1 adds `assignedTier`
for exactly this reason: it has no runtime purpose beyond being assertable.

---

## Gotcha 6: Flow tests cannot mock an action call — the callout really fires

**What happens:** `FlowTestPoint.isUseMockOuput` is documented as "Reserved for future
use" (`api_meta.txt` L74152 — the field name's misspelling is the guide's, not a typo
here). There is no other mocking field anywhere in `FlowTest`, `FlowTestPoint`,
`FlowTestAssertion` or `FlowTestParameter`. An Apex action, an External Services callout,
or an email alert inside the flow executes for real when the flow test runs.

**When it occurs:** The first time a flow test is run against a flow that calls out, in
any org connected to a live endpoint — including a sandbox pointed at a vendor's staging
system that counts requests.

**How to avoid:** Keep the callout behind an invocable Apex method and test that method
with `HttpCalloutMock` in Apex, where mocking is supported. Structure the flow so the
`FlowTest` proves routing around the action's result rather than the action itself, and
run flow tests only in an org whose Named Credentials point somewhere disposable.

---

## Gotcha 7: There is no FlowTest for a screen flow

**What happens:** The type's own scope sentence names three flow kinds: "before you
activate a record-triggered, autolaunched, or Data Cloud-triggered flow, you can test it"
(`api_meta.txt` L73961–73962). Screen flows, platform-event-triggered flows and
scheduled-only flows are absent. This is not a limitation on what a screen-flow test can
assert — there is no screen-flow flow test at all.

**When it occurs:** A team standardises on "every flow ships with a FlowTest" as a release
gate and then discovers the gate is unsatisfiable for half the catalogue.

**How to avoid:** Split the gate by flow type. Screen flows get Jest coverage on their
custom components plus a scripted manual pass; `flow/screen-flows` owns that surface.
`flow/flow-governance` owns the release rule itself.

---

## Gotcha 8: Supplying only the initial record image tests a create, not an update

**What happens:** `FlowTestParameter.type` distinguishes `InputTriggeringRecordInitial`
from `InputTriggeringRecordUpdated`, and both require `leftValueReference` = `$Record`
(`api_meta.txt` L74296–74320). A test point that supplies only the initial image gives the
interview no "after" state. For a flow with
`doesRequireRecordChangedToMeetCriteria` set, the entry evaluation compares the two images
— with one image there is no change to detect.

**When it occurs:** Copying a create-triggered flow's test onto an update-triggered flow,
which is the most common way a second FlowTest gets written.

**How to avoid:** For any flow whose `recordTriggerType` is `Update` or `CreateAndUpdate`,
supply both parameter types in the same `Start` test point, and make the two images differ
in the field the entry criteria actually watch. `references/metadata-examples.md` §2 moves
`Claim_Amount__c` from 4,000 to 25,000 while holding `Status__c` constant.

---

## Gotcha 9: Every reference in a flow test is an unresolved string

**What happens:** `leftValueReference` is typed `string` in both `FlowTestCondition` and
`FlowTestParameter` (`api_meta.txt` L74185–74189, L74296–74302). Nothing in the type
binds it to a variable or element that exists. The Apex side behaves the same way and says
so explicitly: `getVariableValue` "checks for the existence of the variable at run time
only, not at compile time", and "if the specified variable can't be found in that flow,
the method returns null" (`apexrefguide.txt` L158148–158153).

**When it occurs:** After a rename. Renaming a flow variable or element updates every
reference *inside* the flow and none of the strings in the flow tests or the Apex.

**How to avoid:** Treat variable and element API names as the flow's public API and stop
renaming them. In Apex, assert `isNotNull` on the raw `Object` before casting, so a null
lookup fails loudly instead of comparing null to null. **UNVERIFIED (2026-09-05):**
whether a `FlowTest` with an unresolvable `leftValueReference` fails to deploy, fails at
run time, or evaluates against null is not stated in `api_meta.txt`. Deploy one
deliberately broken test into a scratch org once and record which it is.

---

## Gotcha 10: Flow.Interview.start() cannot launch a record-triggered flow

**What happens:** `start()` "starts an instance (interview) for an autolaunched or user
provisioning flow" and "can be used only with flows that have one of these types: •
Autolaunched Flow • User Provisioning Flow" (`apexrefguide.txt` L158156–158177). A
record-triggered flow is not startable this way, no matter that its `processType` is also
`AutoLaunchedFlow` — the presence of a `triggerType` is what makes it triggered rather
than launchable (`api_meta.txt` L72496–72499).

**When it occurs:** An LLM or a developer reaches for the familiar Apex idiom to "unit
test" a record-triggered flow, because Apex is where their testing instincts live.

**How to avoid:** Exercise a record-triggered flow from Apex the only way that works — do
the DML that triggers it, then query the outcome. Reserve `Flow.Interview` for genuinely
autolaunched flows, as in `references/metadata-examples.md` §5.

---

## Gotcha 11: Apex test data isolation reaches into the flow the test fires

**What happens:** "By default, Apex test methods (API version 24.0 and later) can't access
pre-existing org data such as standard objects, custom objects, and custom settings data.
They can only access data that they create" (`apexdev.txt` L40725–40727), and critically,
"this access restriction to test data applies to all code running in test context. For
example, if a test method causes a trigger to execute and the test can't access
organization data, the trigger won't be able to either" (`apexdev.txt` L40760–40761). A
flow that reads routing configuration from a custom object gets zero rows inside an Apex
test, takes its not-found branch, and the test asserts behaviour that never occurs in
production.

**When it occurs:** Any flow with a Get Records against reference data — assignment
matrices, tier thresholds, region tables — driven from an Apex test rather than a
`FlowTest`.

**How to avoid:** Create the reference rows in `@TestSetup` alongside the transactional
data. The exemptions the guide lists are org-management and metadata objects — User,
Profile, Organization, CronTrigger, RecordType, ApexClass, ApexTrigger, ApexComponent,
ApexPage (`apexdev.txt` L40728–40738) — which is a further argument for holding flow
configuration in Custom Metadata rather than a custom object.

---

## Gotcha 12: Trimming the Workflow log category to ERROR deletes the fault-path evidence

**What happens:** `FLOW_ELEMENT_FAULT`, the event that records "fault path taken", is
emitted in the Workflow category at "WARNING and above", while `FLOW_ELEMENT_ERROR` is
emitted at "ERROR and above" (`apexdev.txt` L38777–38793). Log levels run lowest to
highest as ERROR, WARN, INFO, DEBUG, FINE, FINER, FINEST and are cumulative — "if you
select FINE, the log also includes all events logged at the DEBUG, INFO, WARN, and ERROR
levels" (`apexdev.txt` L38389–38392). Setting Workflow to ERROR to keep a log under its
size cap therefore removes the single line that says the fault route ran, while leaving
the noisier error events in place.

**When it occurs:** During the exact investigation that needs the evidence — a large
transaction whose log is being trimmed to stay readable.

**How to avoid:** Debug a fault path at Workflow = FINER or above.
`FLOW_ELEMENT_LIMIT_USAGE`, `FLOW_START_INTERVIEW_LIMIT_USAGE` and
`FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` — the events carrying per-element SOQL, DML, CPU and
heap consumption — are all FINER-only (`apexdev.txt` L38793–38838, L38874–38890). See
`flow/flow-interview-debugging`.

---

## Gotcha 13: A stale flowDefinitions file overrides the status you tested

**What happens:** "If you deploy with flow definitions, the active version numbers in the
flow definitions override the status fields in the flows. For example, the active version
number in the flow definition is version 3, and the latest version of the flow is version
4 with the status field as Active. After you deploy your flow, the active version is
version 3" (`api_meta.txt` L73925–73930). The version your tests exercised and the version
serving users can differ after a single deploy.

**When it occurs:** In repos that still carry `flowDefinitions/*.flowDefinition` files
from before API version 44.0, where the guide now recommends using the Flow object's own
`status` to activate and deactivate (`api_meta.txt` L73921–73924).

**How to avoid:** Delete the `flowDefinitions` directory once flows are on the modern file
naming, and confirm the live version number after every deploy rather than assuming it.
`flow/flow-governance` owns activation policy; this skill only cares that the version
under test is the version that runs.

---

## Gotcha 14: An admin and a user can run different versions of the same flow

**What happens:** "When a flow user invokes an autolaunched flow, the active flow version
runs. If there's no active version, the latest version runs. When a flow admin invokes a
flow, the latest version always runs" (`apexrefguide.txt` L158178–158181). An Apex test
run by an admin exercises the newest saved version; the same code path in production, run
by an integration user, executes the active one.

**When it occurs:** Any org where flow versions accumulate — which is every org, since
saving in Flow Builder creates a version rather than replacing one.

**How to avoid:** Wrap the interview in `System.runAs()` for a user with the production
profile when version selection matters, and pin the flow test itself with
`flowTestFlowVersions.flowVersionNumber` where API version 66.0 is available
(`api_meta.txt` L74053–74064). **UNVERIFIED (2026-09-05):** the guide does not state which
version a `FlowTest` runs against when `flowTestFlowVersions` is omitted.
