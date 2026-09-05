# Gotchas - Subflows And Reusability

Line citations are `grep -n` offsets into the Metadata API Developer Guide
(`api_meta.pdf`, Summer '26 / v66 extract) and the Apex Developer Guide
(`salesforce_apex_developer_guide.pdf`).

## A Subflow Still Shares The Parent Transaction

**What happens:** Teams assume limits or rollback boundaries reset after a subflow call.

**When it occurs:** Reuse is treated like process isolation instead of a call inside the same overall transaction.

**How to avoid:** Review limits, DML, and fault behavior across parent and child together.

The guide describes `FlowSubflow` as an element that "references another flow, which it
calls at run time" (L72625-72627) - a call, not a new interview boundary. Record-triggered
automation runs inside the save (steps 3 and 14 of the order of execution) and the commit
is step 19 (`apexdev.txt` L15440, L15470, L15478), so the per-transaction budget the
Developer Limits sheet lists - 100 SOQL queries and 150 DML statements synchronously
(`salesforce_app_limits_cheatsheet.txt` L53-65) - is what parent *and* child spend from.
UNVERIFIED (2026-09-05): the commonly quoted "2,000 executed elements per flow interview"
figure is not present in the extracted Developer Limits sheet or the Metadata API guide;
treat it as unconfirmed until read from a current limits page.

---

## Variable Names Become API Surface

**What happens:** Inputs and outputs are renamed casually, and parent flows start failing or returning blank values.

**When it occurs:** Teams treat subflow variables as local implementation detail instead of a caller contract.

**How to avoid:** Name variables intentionally and treat contract changes like release-managed interface changes.

Salesforce says this outright in both the `isInput` and `isOutput` field descriptions:
"Disabling input or output access for an existing variable can break the functionality of
applications and pages that call the flow and access the variable. For example, you can
access variables from URL parameters, processes, and other flows" (L72898-72903,
L72925-72930).

---

## Reuse Can Hide Side Effects

**What happens:** A child flow that started as a simple lookup now creates records, sends notifications, and mutates unrelated fields.

**When it occurs:** New callers keep adding "just one more" behavior to the shared child flow.

**How to avoid:** Separate pure reusable logic from parent-specific side effects and challenge any child flow whose scope keeps widening.

---

## Extraction Can Increase Complexity If The Boundary Is Wrong

**What happens:** The parent becomes shorter on screen, but the end-to-end design is harder to understand.

**When it occurs:** Teams extract logic for aesthetics rather than because the contract is genuinely reusable.

**How to avoid:** Extract only when reuse, maintainability, and stable contract design all improve together.

---

## The Subflow Element Has No Fault Connector At All

**What happens:** An author adds a fault path to every Create/Update/Get in a flow, reaches
the Subflow element, and finds there is nowhere to attach one. If the child throws, the
parent has no branch to take.

**When it occurs:** Any time a shared child does DML, a callout, or a Get that can fail,
and the caller was designed as if `<subflows>` behaved like `<recordUpdates>`.

**How to avoid:** Treat a status output as the fault path. The `FlowSubflow` field table
lists exactly five fields - `connector`, `flowName`, `inputAssignments`,
`outputAssignments`, `storeOutputAutomatically` (L72628-72660) - and `faultConnector` is
not among them, although it *is* a field on `FlowActionCall` (L68476),
`FlowApexPluginCall` (L69688), `FlowRecordCreate` (L70965), `FlowRecordDelete` (L71046),
`FlowRecordLookup` (L71120), `FlowRecordUpdate` (L71283) and `FlowWait` (L72993). So the
child must catch its own faults internally (its DML elements *do* have `faultConnector`),
set an `isOutput` boolean, and let the parent branch on it with a Decision. See
`references/metadata-examples.md` § 2 for the shape and
`templates/flow/FaultPath_Template.md` for what the branch should then do.

---

## A Parent Calls The Active Version, And Cannot Pin One

**What happens:** A team activates version 4 of a shared child to serve one new caller.
Every other parent silently switches to version 4 on its next run, with no deployment and
no change to the parents themselves.

**When it occurs:** On the activation, not on the deploy - so it does not show up in any
change set, PR diff, or deployment log for the affected parents.

**How to avoid:** Treat "activate the child" as a release event for every caller, and keep
the caller list in the child's `description` field. The guide is unambiguous:
`FlowSubflow.flowName` "must be an API name of a flow and it can't contain an appended
hyphen and version number" (L72638-72643). Compare `Flow.fullName`, where the version
suffix *is* legal - "`sampleFlow-3` specifies version 3 of the flow whose unique name is
`sampleFlow`. If you don't specify a version number, the flow is the latest version"
(L68147-68151). You can version-pin for deployment; you cannot version-pin an invocation.

---

## isInput And isOutput Default To False, So A New Variable Is Invisible

**What happens:** A variable is added to the child, the parent's `<inputAssignments>`
names it, and the value never arrives - or an output comes back blank with no error.

**When it occurs:** Any variable created in API version 25.0 or later, or in Flow Builder
from Summer '12 onward. The defaults flipped: variables created in API 24.0 or Flow
Builder Spring '12 and earlier defaulted to `True` for both flags (L72891-72897,
L72918-72924).

**How to avoid:** Set `<isInput>` and `<isOutput>` explicitly on every variable in the
child - including the ones you intend to stay private, so the intent is visible in the
diff. `isInput` governs being "set at the start of the flow using URL parameters,
Visualforce controllers, or subflow inputs" (L72886-72888); `isOutput` governs whether the
value "can be accessed from Visualforce controllers and other flows" (L72914-72916).

---

## outputAssignments Reads Backwards From inputAssignments

**What happens:** Hand-edited or generated XML swaps the two ends of an output mapping.
The deploy succeeds against the schema and the parent variable stays at its default.

**When it occurs:** Most often when an assistant pattern-matches `<inputAssignments>` -
where `name` is the child's variable and `value` is the parent's expression - onto
`<outputAssignments>`, which is not symmetric.

**How to avoid:** Remember which side each field belongs to. In
`FlowSubflowOutputAssignment`, `assignToReference` is the "Unique name for the variable in
the **parent** flow" (L72679) and `name` is the "Unique name for the variable in the
**referenced** flow" (L72681). In `FlowSubflowInputAssignment`, `name` is again the
referenced flow's variable and `value` carries the parent's `FlowElementReferenceOrValue`
(L72662-72672). Both `name` fields point at the child; only `assignToReference` points at
the parent. The package checker enforces this direction.

---

## A Stray FlowDefinition Overrides Every status Field In The Deploy

**What happens:** You deploy the child with `<status>Active</status>`, the deploy reports
success, and the org still runs an older version.

**When it occurs:** When the package contains a `flowDefinitions` directory left over
from a pre-API-44 project layout, or copied from an old repo.

**How to avoid:** Ship `Flow` members only; leave `flowDefinitions` empty. "If you deploy
with flow definitions, the active version numbers in the flow definitions override the
status fields in the flows. For example, the active version number in the flow definition
is version 3, and the latest version of the flow is version 4 with the status field as
`Active`. After you deploy your flow, the active version is version 3" (L73929-73934, and
identically at L73198-73202). `FlowDefinition.activeVersionNumber` is "The version number
of the active flow" (L73943). The same upgrade note also warns that a flow shipped with no
`status` value at all "is deployed or retrieved with a `status` value of `Draft`"
(L73188-73190) - a `Draft` child is not callable by a parent.

---

## runInMode Is Declared Per Flow, So The Boundary Can Widen Record Access

**What happens:** A child built for one admin-triggered caller is set to
`SystemModeWithoutSharing`. A second, user-facing parent adopts it, and that parent's
users now read records the sharing model was meant to hide.

**When it occurs:** On the *second* caller. The first caller's behaviour was correct, so
nothing in the child's own history flags the change in blast radius.

**How to avoid:** Keep shared children on `DefaultMode` unless the escalation is the
documented reason the child exists. `runInMode` is a field on `Flow`, not on
`FlowSubflow`, and its values are `DefaultMode` ("How the flow is launched determines
whether the flow runs in user context or in system context"), `SystemModeWithSharing`
(respects OWD, role hierarchy, sharing rules, manual sharing, teams and territories but
not object or field permissions) and `SystemModeWithoutSharing` ("The flow can access all
data", API 49.0+) - all at L68374-68390. Because each flow carries its own value, the
child's setting is what governs inside the child.

---

## A Subflow Cannot Roll Back What The Parent Already Wrote

**What happens:** An author reaches for a Roll Back Records element inside a shared child
to undo a partial write, and it is not available.

**When it occurs:** Whenever the reusable unit is being asked for transaction control
rather than for a decision or a derivation - Pattern 4 territory in SKILL.md.

**How to avoid:** Move the unit to invocable Apex, which has real `Database.setSavepoint`
semantics, or restructure so the parent performs all DML after the child returns.
`FlowRecordRollback` "Rolls back the current transaction and cancels its pending record
changes... **Available only in screen flows**" (L71253-71256), and an element called
through `<subflows>` is an autolaunched flow, not a screen flow.

---

## A Child That Writes Can Re-Enter Itself Through The Save Order

**What happens:** A shared child updates a record whose own after-save flow calls the same
child. The second pass runs against partially-updated state, and the interaction is
invisible from either flow's canvas.

**When it occurs:** When a child performs DML on an object that has a record-triggered
parent using that same child - a loop that only appears once a second caller is wired up.

**How to avoid:** Keep shared children read-only wherever the reuse case allows it, and
where it does not, guard re-entry at the parent (see `flow/recursion-and-re-entry-prevention`).
The recursion is real, not theoretical: "When a process or flow executes a DML operation,
the affected record goes through the save procedure" (`apexdev.txt` L15468), and during a
recursive save the platform "skips steps 9 (assignment rules) through 17 (roll-up summary
field in the grandparent record)" (`apexdev.txt` L15414-15415) - so the second pass does
not behave like the first. The Developer Limits sheet caps "Total stack depth for any Apex
invocation that recursively fires triggers due to insert, update, or delete statements" at
16 (`salesforce_app_limits_cheatsheet.txt` L69); the checker's self-reference rule catches
only the direct case.

---

## Type And Collection Mismatches Surface At Run Time, Not Deploy Time

**What happens:** The parent passes a record collection into a child variable declared as
a single record, or a Number into a String. The metadata deploys; the interview fails.

**When it occurs:** After a refactor of the child, when the caller was not redeployed - the
two files are validated independently and nothing checks them against each other.

**How to avoid:** Match `dataType` and `isCollection` on both sides of every assignment and
run the package checker over parent and child together before deploying either. Both fields
are on `FlowVariable`: `dataType` is Required with values including `Boolean`, `Currency`,
`Date`, `DateTime`, `Number`, `Multipicklist`, `Picklist`, `String`, `sObject` and `Time`
(L72862-72878), and `isCollection` "Indicates whether the variable is a collection of
values... In API version 32.0 and later, a collection variable can be of any data type"
(L72880-72884). UNVERIFIED (2026-09-05): whether a collection passed to a child is aliased
or copied - that is, whether the child mutating it changes the parent's variable - is not
stated in the Metadata API guide; assume nothing and return an explicit `isOutput`
collection if the caller needs the modified version.
