# Gotchas — Entitlements and Milestones

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Entitlement Templates Cannot Be Attached to Products in Lightning Experience

**What happens:** Admins create entitlement templates in Setup, then navigate to a Product2 record in Lightning Experience expecting to find an "Entitlement Templates" related list. The related list is absent. There is no Lightning-compatible UI to link a template to a product. If the admin relies on this for automated entitlement creation when an opportunity closes, nothing is created.

**When it occurs:** Any org running Lightning Experience that uses Products & Price Books for support contracts and relies on entitlement templates to auto-create entitlements. This is silent — no error is thrown when the template is not attached; entitlements simply are not created.

**How to avoid:** In Lightning, build a Record-Triggered Flow on `OpportunityLineItem` insert (when `Opportunity.StageName = 'Closed Won'`) or on `Order` activation that creates an `Entitlement` record programmatically, referencing the entitlement template ID. The template controls default field values (process, business hours, duration) but the Flow must create the actual entitlement. Document this Flow as the canonical entitlement creation mechanism so future admins do not re-introduce the Classic reliance.

---

## Gotcha 2: Missing EntitlementId on Case Silently Disables All Milestone Tracking

**What happens:** Entitlement processes and milestones are fully configured and activated, but no milestone timers appear on cases. No warning or violation actions fire. The Milestone Tracker component on the case record shows nothing.

**When it occurs:** Cases created via Email-to-Case, Web-to-Case, or the API where the `EntitlementId` lookup is not explicitly set. The entitlement process only triggers when `Case.EntitlementId` is populated at case creation (or updated shortly after, within the process start window). An entitlement can exist on the Account without being stamped on the Case.

**How to avoid:** Build a Before-Save Record-Triggered Flow on Case creation that queries the active entitlement for the case's account and populates `EntitlementId`. Test by creating cases through each intake channel (Email-to-Case, Web-to-Case, API, UI) and verifying the Milestone Tracker activates on all channels. Add this check to the go-live validation checklist.

---

## Gotcha 3: Milestone Timer Pauses Do Not Cancel Already-Queued Violation Actions

**What happens:** After a violation action is scheduled (the milestone's time limit is reached), an admin updates the case's entitlement business hours or otherwise attempts to pause/extend the timer. The violation action fires at the originally scheduled time regardless. The timer state and the action scheduler are not retroactively synchronized.

**When it occurs:** Orgs that change business hours mid-flight, or that attempt to "extend" a milestone after the timer has already expired. It also occurs when a sandbox copy is taken at a certain time and then restored — the action timestamps are frozen relative to when they were scheduled.

**How to avoid:** Treat milestone violation actions as immutable once the timer expires. If SLA commitments change, update the entitlement process version and apply the new version to future cases. For in-flight exceptions, handle them manually (complete the milestone in the UI or update the case field directly) rather than relying on timer manipulation. Communicate clearly to operations teams that mid-flight SLA extensions must go through a defined exception process.

---

## Gotcha 4: Entitlement Process Versions Lock In-Flight Cases

**What happens:** An admin needs to change a milestone's time limit (e.g., from 4 hours to 2 hours for a new contract tier). They update the existing entitlement process and republish it. Cases that were already on the old process version continue using the old time limits and old action thresholds. The admin believes the change is live org-wide, but open cases are unaffected.

**When it occurs:** Any time an existing entitlement process is modified and a new version is published. Salesforce creates a new process version; existing cases retain a reference to the version that was active when their entitlement was applied.

**How to avoid:** When releasing a new entitlement process version, identify open cases on the old version using a report filtered by `Case.Entitlement.EntitlementProcess.Name` and the old version label. For critical changes, build a Flow to reassign entitlements on open cases to the new version. Communicate the cutover date and cutover scope to support leadership before publishing the new version.

---

## Gotcha 5: Independent Recurrence Milestones Can Stack and Create Alert Floods

**What happens:** An entitlement process uses Independent recurrence on a milestone with a short time limit (e.g., 1 hour). Cases go unworked for several hours. The milestone timer fires multiple violation actions in rapid succession as each independent instance expires. The support team receives a flood of email alerts for a single case.

**When it occurs:** Independent recurrence milestones that reset based on a case field update or elapsed time, combined with cases that are unworked for longer than one recurrence interval. Each unresolved instance continues running independently.

**How to avoid:** Use Independent recurrence only when each recurrence genuinely represents a distinct SLA commitment (e.g., each customer comment). For general response SLAs, prefer No Recurrence. If Independent recurrence is required, gate violation email alerts with a suppression check — for example, only send the violation email if `Case.Status != 'Waiting on Customer'`. This prevents alert storms for stalled cases that are legitimately awaiting customer input.

---

## Gotcha 6: Milestone action thresholds are offsets from the target, not percentages — and they do not scale

**What happens:** A team sets a first-response milestone to 240 minutes with warnings "at 75% and
90%", then later shortens the milestone to 120 minutes. The warnings keep firing at 180 and 216
minutes elapsed — which is now *after* the breach, so the warning arrives later than the violation.
Nobody edited the warnings, so nobody suspects them.

**When it occurs:** Any time `minutesToComplete` changes on a milestone that already has time
triggers. The `EntitlementProcessMilestoneTimeTrigger` type carries `timeLength` (int) and
`workflowTimeTriggerUnit` (`Minutes` | `Hours` | `Days`) and nothing else numeric
(api_meta.txt:59204–59224). `timeLength` is "the length of time between the time trigger activation
and the milestone target completion date"; negative values "correspond to warning time triggers" and
positive values "correspond to violation time triggers" (api_meta.txt:59213–59219). There is no
percentage anywhere in the model, and no element that ties a trigger to `minutesToComplete`.

**How to avoid:** Treat every `timeLength` as a hand-derived constant. Record the intended percentage
in `versionNotes` or the design doc, and re-derive all of them in the same edit that changes
`minutesToComplete` — `references/metadata-examples.md` § 7 shows `-60` becoming `-30` when a
240-minute milestone becomes 120. The checker reports each trigger's offset against the milestone
target so a stale one is visible in lint output rather than in a breach report.

---

## Gotcha 7: Recurrence lives on the milestone type, so changing it changes every process at once

**What happens:** An admin needs the "Case Update" milestone to recur independently on the Platinum
process while staying sequential on Standard. They open the milestone, switch the recurrence, and
both processes change.

**When it occurs:** Whenever more than one entitlement process names the same milestone. Recurrence
is a field on `MilestoneType` — `recurrenceType`, valid values `none`, `recursIndependently`,
`recursChained` (api_meta.txt:88337–88345) — and `MilestoneType` is a standalone component in the
`milestoneTypes` directory (api_meta.txt:88325). The per-process `EntitlementProcessMilestoneItem`
field table has no recurrence field at all (api_meta.txt:59158–59202): a process can override the
milestone's timing, calendar, criteria and actions, but not how it repeats.

**How to avoid:** Decide recurrence at the milestone-type level and name the type after its recurrence
behaviour, not after its business meaning — "Case Update (Chained)" rather than "Case Update" — so the
shared object is obvious to the next admin. When two tiers genuinely need different recurrence for the
same concept, create two milestone types. Query `MilestoneType` and `SlaProcess` together before
editing to see how many processes a type serves.

---

## Gotcha 8: Nothing completes a milestone; a milestone stays open until something writes CompletionDate

**What happens:** First-response milestones show as violated on cases where the agent demonstrably
replied. The team assumes the timer is broken. It is not — the milestone was never told the reply
happened.

**When it occurs:** On every milestone whose completion criteria are not satisfiable by the platform
alone. `CaseMilestone` supports only `describeLayout(), describeSObjects(), query(), retrieve(),
update()` — there is no `create()` and no `delete()` (object_reference.txt:63347–63348). Salesforce
creates the rows when a case enters the process; `CompletionDate` ("the date and time the milestone
was completed") and `StartDate` are the only fields carrying the `Update` property
(object_reference.txt:63373–63380). `IsCompleted` and `IsViolated` are derived and not updateable.

**How to avoid:** Ship the completion mechanism with the process, never after it. Either set the
milestone's completion criteria so the platform can satisfy them, or deploy the Apex/Flow that stamps
`CompletionDate` — the bulk-safe shape is in `references/metadata-examples.md` § 9. Add a query for
`CaseMilestone WHERE IsCompleted = false AND TargetDate < TODAY` grouped by milestone type to the
go-live checks; a type where nothing ever completes is a missing stamp, not a missed SLA.

---

## Gotcha 9: The process exit is the boundary for recurrence, so closing and reopening restarts everything

**What happens:** A case is closed, then reopened two days later for a related question. The
first-response milestone — configured as non-recurring precisely so it fires once — starts a fresh
timer, and the case breaches a response SLA on a conversation that has been running all week.

**When it occurs:** Whenever the process exit criteria are satisfied and later stop being satisfied.
The guide defines non-recurrence in terms of the process, not the case: `none` means "the milestone
occurs only one time **until the entitlement process exits**" (api_meta.txt:88339–88341). With exit
criteria of `Case.Status equals Closed`, closing the case exits the process and re-opening it enters
the process again.

**How to avoid:** Write exit criteria that describe the end of the *commitment*, not the end of the
current status. A boolean such as `Case.SLA_Complete__c equals true`, stamped once by the resolution
milestone's success action, survives a reopen; `Status = Closed` does not. If reopens are legitimately
new commitments, say so explicitly in `versionNotes` so the second first-response timer is a decision
rather than a surprise.

---

## Gotcha 10: A stopped case freezes the SLA clock, and the elapsed time you report is not the elapsed time you promised

**What happens:** Support reports 98% SLA attainment. The customer's own records say otherwise. Both
are reading real numbers — the org has been stopping the clock on cases awaiting customer response,
and the milestone's elapsed time excludes every stopped interval.

**When it occurs:** `Case.IsStopped` is a plain boolean carrying `Create`, `Update`, `Filter`, `Group`
and `Sort` (object_reference.txt:62486–62502) — meaning any Flow, trigger, integration user or agent
with edit access can stop an entitlement process on a case, and `Case.StopStartDate` records when it
happened but is read-only (object_reference.txt:62685–62693). The stopped interval is invisible in the
milestone UI unless `enableMilestoneStoppedTime` is `true` in `Entitlement.settings-meta.xml`, which
is what surfaces the *Stopped Time* and *Actual Elapsed Time* fields (api_meta.txt:115646–115655).

**How to avoid:** Turn `enableMilestoneStoppedTime` on before go-live, not after the first dispute —
it is a display switch, so enabling it costs nothing and enabling it late means the earlier cases
still cannot be explained. Restrict who can write `Case.IsStopped` (field-level security plus a
validation rule requiring a stop reason), and report attainment with the stopped time visible beside
it. `entryStartDateField` even accepts `StopStartDate` as the process start (api_meta.txt:59116), so
in an org that stops cases routinely, check which date the process is actually counting from.

---

## Gotcha 11: A Flow can create an Entitlement but cannot set its business hours or its status

**What happens:** The Lightning replacement Flow creates entitlements successfully, then every case
using them runs its milestones on the wrong calendar — or the entitlement sits inactive and nothing
the Flow does makes it active.

**When it occurs:** On any Flow, Apex or integration that builds `Entitlement` records field by field.
`Entitlement` does support `create()` and `update()` (object_reference.txt:110182–110184), but
`BusinessHoursId` — documented as **"Required. ID of the BusinessHours associated with the
entitlement"** — carries only `Filter, Group, Nillable, Sort` and neither `Create` nor `Update`
(object_reference.txt:110216–110222). `Status` likewise carries only `Filter, Nillable`
(object_reference.txt:110364–110371); it is derived from `StartDate` and `EndDate`, which *are*
createable and updateable.

**How to avoid:** Let the entitlement template carry the calendar. `EntitlementTemplate` has its own
`businessHours` field (api_meta.txt:59328–59330), so a Flow that stamps the template reference plus
`AccountId`, `StartDate`, `EndDate` and `SlaProcessId` gets a correctly calendared entitlement without
writing the field it cannot write. To make an entitlement active, set `StartDate` to today or earlier
and `EndDate` in the future — never try to write `Status`. Verify with the `Entitlement` query in
`references/metadata-examples.md` § 8 rather than trusting the Flow's debug output.

---

## Gotcha 12: The version fields are inert until versioning is switched on, and the file name is not yours to choose

**What happens:** An admin adds `versionMaster` and `versionNumber` to a retrieved process file,
deploys, and gets either a failure or a second independent process. Later, hand-writing a file named
after the process's display name produces "component not found" on retrieve.

**When it occurs:** In any org where `enableEntitlementVersioning` is still `false`. The Object
Reference marks `IsVersionDefault`, `VersionMaster`, `VersionNotes` and `VersionNumber` as available
"in API version 28.0 and later **in organizations that have entitlement versioning enabled**"
(object_reference.txt:270688–270693, 270752–270758, 270763–270769, 270775–270781). The switch itself
is `enableEntitlementVersioning` in the entitlement settings file (api_meta.txt:115638–115642). The
file name is derived, not chosen: it is `slaProcess.NameNorm`, "the lowercase version of the `name`
field", with `_v<n>` appended when versioning is on — the guide's own example turns `gold_support`
into `gold_support_v2.entitlementProcess` (api_meta.txt:59078–59084, object_reference.txt:270717–270727).

**How to avoid:** Deploy `enableEntitlementVersioning` as a separate, earlier change than the first
versioned process, and confirm it in **Setup > Entitlement Settings** before writing any version
fields. For file names, never hand-write the first one: create the process, retrieve
`EntitlementProcess`, and edit the file the org gave you. Keeping process `name` values lowercase and
underscore-separated makes the derived file name predictable, which matters when the same file must
be diffed across sandboxes.
