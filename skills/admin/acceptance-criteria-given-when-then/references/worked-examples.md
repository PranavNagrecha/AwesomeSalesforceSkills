# Worked Examples — Given/When/Then Criteria for the Acme Case Intake Build

One scenario, worked end to end: the Service Cloud case-intake solution built in
`skills/admin/case-management-setup/references/worked-example-case-intake.md`. That file produced the
configuration workbook and the deployable metadata. **This file produces the acceptance criteria** —
six requirements, each written as Given/When/Then that names the sandbox, the persona, the seed data,
the Salesforce artefact under test, the checker or query that proves it, and whether it can be
automated. `admin/uat-and-acceptance-criteria` then wraps these into a UAT programme; it consumes the
`ac_id`s below and never restates their syntax.

Boundaries, so nothing here is written twice:

| Concern | Owned by |
|---|---|
| The requirement statements and their `REQ-nnn` ids | `admin/requirements-gathering-for-sf` § The Requirements Catalogue |
| Forward/backward traceability of those ids | `admin/requirements-traceability-matrix` § ID Conventions |
| The workbook rows the criteria test | `admin/configuration-workbook-authoring` |
| The story stem the AC block lives inside | `admin/user-story-writing-for-salesforce` |
| The per-case UAT field schema (`case_id`, `data_setup`, …) | `admin/uat-test-case-design` § The Canonical UAT Case Schema |
| Environment, persona roster, defect log, sign-off | `admin/uat-and-acceptance-criteria` |
| Which automation tool builds the behaviour | `standards/decision-trees/automation-selection.md` |
| **The Given/When/Then form of each criterion, and what proves it** | **this skill** |

---

## 1. Id conventions used here

- `REQ-nnn` — requirement id, from `admin/requirements-traceability-matrix` § ID Conventions:
  assigned during elicitation, immutable, never reused. This is the join key every criterion carries.
- `AC-nnn.n` — acceptance-criterion id, scoped to its requirement (`AC-001.2` is the second criterion
  of `REQ-001`). The UAT script's `ac_id` column points at these.
- `US-CI-nn` — story id, mirrored from the agile tool.
- `CWB-XXX-nnn` — configuration-workbook row id.

**`FG-XXX` ids map 1:1 to `REQ-XXX` ids.** The workbook's `source_req_id` column is documented as
"the RTM `req_id`" in `admin/configuration-workbook-authoring/SKILL.md` § Per-Row Schema, but the
worked rows in that skill's `references/examples.md` show `FG-014`, `FG-031`, `FG-051` — fit-gap row
ids. The two id spaces are one-to-one: the requirements catalogue carries the pairing on each row as
`downstream.fit_gap_row` (`admin/requirements-gathering-for-sf/references/worked-examples.md` § 2),
so `REQ-001 ↔ FG-001`. Write `req_id` in acceptance criteria; translate to `FG-` only when writing
into a workbook that already uses it. Do not renumber either space to make them match — record the
pairing.

---

## 2. The six requirements

| req_id | Requirement statement | Workbook row | Story | Artefact under test | Rule type? |
|---|---|---|---|---|---|
| REQ-001 | A case created through any channel is owned by the queue that works it, and by a known queue when nothing matches. | CWB-AUT-001 | US-CI-01 | `assignmentRules/Case.assignmentRules-meta.xml` | yes |
| REQ-002 | A web-form submitter gets the web acknowledgement; an email submitter does not get the web one. | CWB-AUT-002 | US-CI-02 | `autoResponseRules/Case.autoResponseRules-meta.xml` | yes |
| REQ-003 | A case untouched for 8 business hours re-routes to Tier 2, on the account's regional calendar. | CWB-AUT-004, CWB-AUT-006 | US-CI-04 | `escalationRules/Case.escalationRules-meta.xml`, `settings/BusinessHours.settings-meta.xml` | yes |
| REQ-004 | A Premier first-response milestone warns the owner before the target, not after it. | CWB-AUT-005 | US-CI-07 | `entitlementProcesses/Premier_Support_v1.entitlementProcess-meta.xml` | no |
| REQ-005 | A Tier 1 agent can edit a case in their queue; a Billing agent cannot edit a Tier 2 case. | CWB-PS-001 | US-CI-06 | `permissionsets/Support_Agent.permissionset-meta.xml` | no |
| REQ-006 | A case cannot be closed without a resolution. | extends CWB-VR-001 | US-CI-08 | `objects/Case/validationRules/Close_Requires_Resolution.validationRule-meta.xml` | yes |

"Rule type" means the behaviour is implemented by a criteria-driven rule engine — assignment,
auto-response, escalation, duplicate, validation. Every rule-type requirement needs a criterion for
the **non-matching** case as well as the matching one, because the rule engines all define a
fall-through and the AC is what pins it. The checker enforces this.

---

## 3. The shared Background

Written once; every scenario below inherits it. Personas are the UAT roster from
`admin/uat-and-acceptance-criteria/references/worked-examples.md` § 2.3 — no row is a System
Administrator, because an admin bypasses FLS and most sharing in the UI and so proves nothing about
the persona.

```gherkin
Background:
  Given the sandbox is "UAT1" (Full), refreshed 2026-08-24, build deployed 2026-08-26
    And email deliverability is "All Email" and seeded contact emails end ".invalid"
    And a user "Jo"  = jo.tan@acme.com.uat1,    profile "Minimum Access — Salesforce", PSG "Support_Agent"
    And a user "Mia" = mia.ross@acme.com.uat1,  profile "Minimum Access — Salesforce", PS  "Billing_Case_Access"
    And a user "Dee" = dee.olu@acme.com.uat1,   profile "Standard User", PS "Support_Agent" + "Support_Manager"
    And a user "Sam" = sam.ito@acme.com.uat1,   profile "Standard User", PS "Data_Load_Operator"
    And the Case OWD is "Private" and every queue has DoesIncludeBosses = true
    And queues "Tier_1_General", "Tier_2_Support_Queue", "Billing_Queue" exist and are Case-enabled
    And Account "Northwind Ltd" has Region__c = "EMEA"; Account "Contoso Inc" has Region__c = "US"
    And Account "Northwind Ltd" holds an active Premier entitlement
    And Case.OwnerId and Case.Status are enabled for field history tracking
```

The last line is not housekeeping. `CaseHistory` "Represents historical information about changes
that have been made to the associated Case", and history "is available for **tracked fields** of the
object" (`object_reference.txt` L63138–63139, L62819). Several criteria below use a `CaseHistory`
query as their oracle; if the field is not tracked the query returns nothing and the criterion cannot
fail-safe. Declaring the tracking in the Background is what makes the oracle real.

---

## 4. The criteria

### REQ-001 — Assignment routes to the right queue, and to a known queue when nothing matches

```gherkin
Scenario: AC-001.1 — a Severity 4 web case with no special origin lands in Tier 1 General
  Given Sam has published the web form and "Support_Case_Routing" is the only active Case assignment rule
    And Account "Contoso Inc" exists with no Premier entitlement
   When a visitor submits the web form with Severity__c = 4 and no billing routing address
   Then the case Owner is the queue "Tier_1_General"
    And Case.Origin is "Web"

Scenario: AC-001.2 — a billing-address email case lands in Billing, not Tier 1
  Given the routing address "billing@acme.example" is verified and its caseOrigin is "Email"
   When an external sender emails billing@acme.example
   Then the case Owner is the queue "Billing_Queue"

Scenario: AC-001.3 (negative) — a case matching no rule entry lands on the declared default, not nowhere
  Given a case whose field values match none of the entries in "Support_Case_Routing"
   When the case is created through the web form
   Then the case Owner is the CaseSettings defaultCaseOwner, which is the queue "Tier_1_General"
    And the case is not left owned by the submitting or integration user

Scenario: AC-001.4 (bulk) — a 200-row backlog load routes the same way a UI case does
  Given a 200-row CSV of backlog cases with mixed Origin values
    And Data Loader's "Assignment rule" setting holds the id of "Support_Case_Routing"
   When Sam runs the load as one SOAP batch
   Then all 200 rows succeed with 0 errors
    And each row's Owner equals the Owner a UI-created case with the same field values receives
```

| Field | Value |
|---|---|
| Sandbox | UAT1 (Full) |
| Persona / permission | Sam — `Data_Load_Operator` (API Enabled, Case Create) for AC-001.4; unauthenticated visitor / external sender for AC-001.1–.3 |
| Seed data | 1 Account per region; 1 verified routing address; 200-row CSV; a UI control case per distinct field combination |
| Artefact | `assignmentRules/Case.assignmentRules-meta.xml`, `settings/Case.settings-meta.xml` (`defaultCaseOwner`) |
| Proof | `python3 skills/admin/assignment-rules/scripts/check_assignment_rules.py --manifest-dir ./force-app/` for the metadata, then `SELECT Id, CaseNumber, Origin, Owner.Name, Owner.Type FROM Case WHERE CreatedDate = TODAY` — `Owner.Type` must read `Queue` |
| Automatable | **Apex** for AC-001.1–.3; **manual** for AC-001.4 (see § 6) |

Why AC-001.3 is not optional: `CaseSettings.defaultCaseOwner` "Specifies the default owner of a case
when assignment rules fail to locate an owner" (`api_meta.txt` L111700–111701), and rule entries are
evaluated in file order — "Rules are processed in the order they appear within the AssignmentRules
container" (`api_meta.txt` L23712–23713). So "the rule assigns it" has two outcomes, not one, and
only the AC decides which queue the second one is. `Owner.Type` is a real oracle because
`Case.OwnerId` "Refers To Group, User" (`object_reference.txt` L62575–62587) and `Group.Type` is a
required, filterable picklist whose values include `Queue` (`object_reference.txt` L154307–154312,
L154341–154342).

---

### REQ-002 — The web acknowledgement fires for Web-to-Case only

```gherkin
Scenario: AC-002.1 — a web submission gets the web acknowledgement from the org-wide address
  Given the auto-response rule "Case_Acknowledgement" is active
    And its first entry matches Case.Origin = "Web" and uses template "Support_Templates/Case_Web_Acknowledgement"
    And that entry's senderEmail is the org-wide address "support@acme.example"
   When a visitor submits the web form with a valid email address
   Then exactly one acknowledgement is sent to the submitted address
    And its From address is "support@acme.example"
    And its body contains the case number

Scenario: AC-002.2 (negative) — an email-origin case does not get the web acknowledgement
  Given the routing address "support@acme.example" sets caseOrigin = "Email"
   When an external sender emails support@acme.example
   Then no email using template "Case_Web_Acknowledgement" is sent
    And the email acknowledgement template "Case_Email_Acknowledgement" is used instead

Scenario: AC-002.3 (negative) — the acknowledgement never comes from the routing address
  Given the auto-response entry's senderEmail is an org-wide address, not a routing address
   When either channel creates a case
   Then no outbound acknowledgement has a From address equal to a Email-to-Case routing address
    And no second case is created from the acknowledgement
```

| Field | Value |
|---|---|
| Sandbox | UAT1, deliverability `All Email`, seeded contact emails scrubbed to `qa+n@acme.example.invalid` |
| Persona / permission | External submitter (no Salesforce licence); Jo — `Support_Agent` — reads the resulting case |
| Seed data | One web submission with a scrubbed address; one inbound email from a scrubbed address; a mailbox the QA team can read |
| Artefact | `autoResponseRules/Case.autoResponseRules-meta.xml`, `email/Support_Templates/*.email`, `settings/Case.settings-meta.xml` (`webToCase.caseOrigin`, `emailToCase.routingAddresses[].caseOrigin`) |
| Proof | Setup → Email Log Files entry for the recipient address in the test window, plus `SELECT Id, Origin FROM Case WHERE CreatedDate = TODAY` to confirm each channel stamped the Origin the entry filters on |
| Automatable | **Manual** — the oracle is an email arriving outside the org |

Grounding. Auto-response rules send "automatic email responses to lead or case submissions based on
the attributes of the submitted record" (`api_meta.txt` L25196–25197), and the entry order inside the
rule is what selects one template over another — the `AutoResponseRule` type "Represents whether a
rule is active or not and **the order in which the entry is processed** in the rule"
(`api_meta.txt` L25236–25237). The attribute AC-002.1 and AC-002.2 pivot on is `Case.Origin`, which
each channel stamps from its own setting: `WebToCaseSettings.caseOrigin` "Specifies the default case
origin for cases created through this web form" (`api_meta.txt` L112133–112134) and the routing
address's `caseOrigin` "Specifies the default case origin for cases created through this routing
address" (`api_meta.txt` L112031–112033). The entry's sender is `senderEmail` / `senderName`
(`api_meta.txt` L25279–25283); its template is `template`, and the guide notes "Lightning email
templates aren't packageable. We recommend using a Classic email template."
(`api_meta.txt` L25285–25288) — which is why the artefact row names `.email` Classic templates.

> A tighter oracle would be `SELECT Id, Incoming, FromAddress, Subject FROM EmailMessage WHERE
> ParentId = :caseId AND Incoming = false`. **UNVERIFIED (2026-09-05):** the guides confirm
> `EmailMessage` exists for orgs using Email-to-Case or Enhanced Email
> (`object_reference.txt` L103975–103976), but none of the eight extracted guides states that an
> **auto-response rule** send is written back as an `EmailMessage` row. Confirm in the sandbox before
> making that query the sole oracle; until then the Email Log File is the proof and the query is a
> convenience.

---

### REQ-003 — Escalation after the business-hours SLA

```gherkin
Scenario: AC-003.1 — an untouched EMEA case escalates at 8 business hours, not 8 clock hours
  Given a case on Account "Northwind Ltd" (Region__c = "EMEA")
    And Case.BusinessHoursId is the "EMEA Support Hours" calendar (08:00–18:00 Europe/London)
    And the escalation entry for non-Severity-1 cases has businessHoursSource = "Case"
    And its escalationStartTime is "CaseCreation" and minutesToEscalation is 480
   When the case is created Friday 17:30 London and no one touches it
   Then the escalation action does not run on Saturday or Sunday
    And the case Owner becomes the queue "Tier_2_Support_Queue" on the following Monday morning

Scenario: AC-003.2 (negative) — a case worked inside the window does not escalate
  Given the same case and calendar
    And disableEscalationWhenModified is true on that entry
   When Jo edits the case 2 business hours after creation
   Then the escalation action never runs
    And Case.Owner is still Jo's queue at the end of the window

Scenario: AC-003.3 (negative) — a regional holiday does not consume SLA time
  Given a Holiday record attached to "EMEA Support Hours" covering the next working day
   When a case is created the evening before that holiday and left untouched
   Then the 8-business-hour target skips the holiday
    And the escalation lands on the first working morning after it

Scenario: AC-003.4 — a Severity 1 case escalates on the clock, by design
  Given the Severity 1 escalation entry has businessHoursSource = "None"
   When a Severity 1 case is created Saturday 02:00
   Then the escalation action runs 60 minutes later, on the weekend
```

| Field | Value |
|---|---|
| Sandbox | UAT1; the clock test needs a real elapsed window or a `SlaStartDate` / `CreatedDate` back-date, so book it first in the UAT calendar |
| Persona / permission | Dee — `Support_Agent` + `Support_Manager`, so queue-owned cases are visible via `DoesIncludeBosses` |
| Seed data | One EMEA account, one US account, one Holiday record on the EMEA calendar dated inside the test window, one Severity 1 case |
| Artefact | `escalationRules/Case.escalationRules-meta.xml`, `settings/BusinessHours.settings-meta.xml`, `flows/Case_Set_Calendar.flow-meta.xml` |
| Proof | `python3 skills/admin/business-hours-and-holidays/scripts/check_business_hours_and_holidays.py --manifest-dir ./force-app/`, then `SELECT Id, CaseNumber, BusinessHoursId, OwnerId, CreatedDate FROM Case WHERE Id = :caseId` and `SELECT Field, OldValue, NewValue, CreatedDate, CreatedBy.Name FROM CaseHistory WHERE CaseId = :caseId AND Field = 'Owner' ORDER BY CreatedDate` |
| Automatable | **Manual** (time-based; see § 6) |

Grounding. `BusinessHours` "Specifies the business hours of your support organization. **Escalation
rules are run only during these hours.**" and "If business hours are associated with any Holiday
records, then business hours and escalation rules associated with business hours are suspended during
the dates and times specified as holidays." (`object_reference.txt` L53105, L53107–53108). The entry
fields the criteria pin are real: `businessHoursSource` takes `None` / `Case` / `Static`,
`escalationStartTime` takes `CaseCreation` / `CaseLastModified`, `disableEscalationWhenModified`
"Indicates whether the escalation is disabled when the record is modified", and `minutesToEscalation`
is "The number of minutes until the escalation occurs" (`api_meta.txt` L59449–59476, L59499). Entry
order matters here too: "Escalation rules are processed in the order they appear in the
EscalationRules container" (`api_meta.txt` L59421–59423), so AC-003.4 has to say Severity 1 is the
**first** entry or it will never be reached. The `CaseHistory` oracle is attributable because the
`defaultCaseUser` in CaseSettings is "the user listed in the Case History related list for automated
case changes from: Assignment rules, Escalation rules, On-Demand Email-to-Case…"
(`api_meta.txt` L111705–111712) — so `CreatedBy.Name` on the history row distinguishes an escalation
from a human reassignment.

---

### REQ-004 — The entitlement milestone warns before the target

```gherkin
Scenario: AC-004.1 — the owner is warned 60 minutes before the first-response target
  Given a Premier case on Account "Northwind Ltd" that has entered "Premier_Support_v1"
    And the "First Response" milestone has minutesToComplete = 240 on the EMEA calendar
    And the milestone has a time trigger with timeLength = -60 and workflowTimeTriggerUnit = "Minutes"
   When 180 business minutes pass with no first response
   Then the warning action fires once
    And the case owner receives the warning alert
    And the milestone is still open

Scenario: AC-004.2 — a response before the target closes the milestone and cancels the warning
  Given the same case, 30 business minutes after it entered the process
   When Jo sends a first response that satisfies the milestone completion criteria
   Then CaseMilestone.IsCompleted is true
    And CaseMilestone.CompletionDate is set
    And no warning action fires afterwards

Scenario: AC-004.3 (negative) — a non-Premier case never enters the process
  Given a case on Account "Contoso Inc", which holds no Premier entitlement
   When the case is created and left untouched past 240 minutes
   Then Case.SlaStartDate is null
    And no CaseMilestone row exists for the case
    And no warning or violation action fires
```

| Field | Value |
|---|---|
| Sandbox | UAT1; the process version under test must be the one whose `isVersionDefault` is true |
| Persona / permission | Jo — `Support_Agent`; Dee verifies the alert as the escalation recipient |
| Seed data | One Premier account with an active Entitlement, one non-Premier account, one case each |
| Artefact | `entitlementProcesses/Premier_Support_v1.entitlementProcess-meta.xml`, `settings/BusinessHours.settings-meta.xml` |
| Proof | `SELECT CaseId, MilestoneType.Name, TargetDate, CompletionDate, IsCompleted, IsViolated, TimeRemainingInMins, BusinessHoursId FROM CaseMilestone WHERE CaseId IN :caseIds` plus `SELECT Id, SlaStartDate, EntitlementId FROM Case WHERE Id IN :caseIds` |
| Automatable | **Manual** (time-based) |

Grounding. The warning-vs-violation distinction is the **sign** of one integer:
`EntitlementProcessMilestoneTimeTrigger.timeLength` is "The length of time between the time trigger
activation and the milestone target completion date… **Negative values** indicate that the target
completion date hasn't yet arrived and correspond to **warning** time triggers. **Positive values**
indicate that the target completion date has passed and correspond to **violation** time triggers."
(`api_meta.txt` L59210–59217). An AC that says "warn the owner before the SLA is missed" without the
sign is satisfiable by a violation trigger, and the build will pass review. The milestone's own clock
comes from `EntitlementProcessMilestoneItem.businessHours` and `minutesToComplete` — "The number of
minutes from when the case enters the entitlement process that the milestone occurs"
(`api_meta.txt` L59191–59192), and `useCriteriaStartTime` decides whether the clock starts at process
entry or when the milestone criteria are met (`api_meta.txt` L59197–59200), which is exactly the
ambiguity AC-004.1's Given removes. Every field the oracle queries is a real `CaseMilestone` field:
`TargetDate` "The date and time the milestone must be completed", `IsCompleted`, `IsViolated`,
`CompletionDate`, `TimeRemainingInMins`, `BusinessHoursId` (`object_reference.txt` L63342–63343, L63376–63410, L63441–63446, L63492–63497), and
`Case.SlaStartDate` "Shows the time that the case entered an entitlement process"
(`object_reference.txt` L62659–62666).

Name the version. Entitlement process files carry the version in the filename — "an entitlement
process named 'gold_support' can have the file name 'gold_support_v2.entitlementProcess'"
(`api_meta.txt` L59075–59081) — so an AC that says "the Premier_Support process" is ambiguous the
moment versioning is on. The criteria above pin `Premier_Support_v1`.

---

### REQ-005 — The permission set grants case edit, and only where sharing allows

```gherkin
Scenario: AC-005.1 — a Tier 1 agent can edit a case they can see
  Given the permission set "Support_Agent" has Case objectPermissions allowRead = true and allowEdit = true
    And the Case OWD is "Private"
    And a case owned by the queue "Tier_1_General", of which Jo is a member
   When Jo changes Status from "New" to "Working"
   Then the save succeeds
    And Case.Status is "Working"

Scenario: AC-005.2 (negative) — object edit without record access is still no edit
  Given Mia holds "Billing_Case_Access" with Case allowRead = true and allowEdit = true
    And a case owned by the queue "Tier_2_Support_Queue", of which Mia is not a member
   When Mia opens that case's record id directly by URL
   Then the platform returns "insufficient privileges"
    And the case does not appear in any list view available to Mia

Scenario: AC-005.3 (negative) — removing the permission set removes the capability, not just the tab
  Given Jo's "Support_Agent" assignment is removed
   When Jo attempts the same Status change on the same queue-owned case
   Then the save is rejected for insufficient access
    And Case.Status is unchanged
```

| Field | Value |
|---|---|
| Sandbox | UAT1 |
| Persona / permission | Jo (`Support_Agent`), Mia (`Billing_Case_Access`) — neither is an administrator |
| Seed data | One case owned by `Tier_1_General`, one owned by `Tier_2_Support_Queue`, queue memberships as in the Background |
| Artefact | `permissionsets/Support_Agent.permissionset-meta.xml`, `permissionsets/Billing_Case_Access.permissionset-meta.xml`, `queues/*.queue-meta.xml` |
| Proof | `SELECT RecordId, HasEditAccess, HasReadAccess FROM UserRecordAccess WHERE UserId = :userId AND RecordId IN :caseIds` — one row per (persona, case) pair the criteria name |
| Automatable | **Apex**, inside `System.runAs` |

Grounding, and the reason AC-005.2 exists. `PermissionSetObjectPermissions.allowEdit` is "Required.
Indicates whether the object referenced by the object field can be edited by the users assigned to
this permission set" (`api_meta.txt` L95077–95080) — an **object**-level capability. The same type
marks `modifyAllRecords` and `viewAllRecords` as the ones that apply "**regardless of the sharing
settings for the object**" (`api_meta.txt` L95086–95090, L95110–95113); `allowEdit` carries no such
clause, which is why a criterion that stops at "the permission set grants edit" is only half a
requirement. Record access is the other half, and for queue-owned cases it comes from queue
membership and `DoesIncludeBosses` — "Indicates whether records shared with users in this group are
also shared with users higher in the role hierarchy" (`object_reference.txt` L154213–154226).

---

### REQ-006 — The validation rule blocks closing without a resolution

```gherkin
Scenario: AC-006.1 (negative) — closing with an empty resolution is rejected with a named message
  Given the validation rule "Close_Requires_Resolution" on Case is active
    And a case owned by Jo with Status = "Working" and Resolution__c blank
   When Jo sets Status to "Closed"
   Then the save is rejected
    And the error message is exactly "Enter a resolution before closing this case."
    And the message appears against the Resolution__c field
    And Case.Status is still "Working"

Scenario: AC-006.2 — closing with a resolution succeeds
  Given the same case with Resolution__c = "Replaced the licence key"
   When Jo sets Status to "Closed"
   Then the save succeeds
    And Case.Status is "Closed"

Scenario: AC-006.3 (negative) — a blocked close produces no downstream side effects
  Given the same blocked save from AC-006.1
   When the save is rejected
   Then no owner change is recorded on the case
    And no acknowledgement or escalation email is sent for that attempt

Scenario: AC-006.4 (bulk) — a 200-row close via Data Loader rejects only the offending rows
  Given a 200-row CSV setting Status = "Closed", of which 40 rows leave Resolution__c blank
   When Sam runs the update as one SOAP batch
   Then 160 rows succeed
    And 40 rows fail with "FIELD_CUSTOM_VALIDATION_EXCEPTION" and the rule's exact message
    And no row fails on a governor limit
```

| Field | Value |
|---|---|
| Sandbox | UAT1 |
| Persona / permission | Jo — `Support_Agent`; Sam — `Data_Load_Operator` for AC-006.4 |
| Seed data | 200 cases in Status "Working", 40 with `Resolution__c` blank; one control case with a resolution |
| Artefact | `objects/Case/validationRules/Close_Requires_Resolution.validationRule-meta.xml`, `objects/Case/fields/Resolution__c.field-meta.xml` |
| Proof | The Data Loader error CSV for AC-006.4, plus `SELECT Id, Status, Resolution__c FROM Case WHERE Id IN :caseIds` for the record state |
| Automatable | **Apex** (`Database.update(records, false)` and assert `SaveResult.getErrors()`) |

Grounding, and why AC-006.3 is a real criterion rather than padding. A custom validation rule runs at
**step 5** of the save order — "Runs most system validation steps again… and runs any custom
validation rules" — while assignment rules are step 9, auto-response rules step 10, escalation rules
step 12 and entitlement rules step 15 (`apexdev.txt` L15442, L15449, L15450, L15461, L15471). A
blocked save therefore reaches none of them, and an AC that promises both a rejection and a
notification for the same attempt is unsatisfiable by construction. The message text is testable
because `errorMessage` is "Required. The message that appears if the validation rule fails. The
message must be 255 characters or less", and `errorDisplayField` decides where it appears —
"If you do not specify a value or the field isn't visible on the page layout, the value changes
automatically to Top of Page" (`api_meta.txt` L45402–45403, L45388–45392). That is why AC-006.1
asserts the field the message lands against, not just the text.

---

## 5. The same six as a lintable record

This is what `scripts/check_ac_format.py` reads. Save it as `acceptance-criteria.yaml` beside the
story file and run:

```bash
# one criteria record
python3 scripts/check_ac_format.py --file acceptance-criteria.yaml

# every criteria file in a folder, YAML and markdown together
python3 scripts/check_ac_format.py --manifest-dir ./docs/stories/
```

```yaml
project: "Acme Case Intake — 2026.R3"
acceptance_criteria:
  - ac_id: AC-001.1
    req_id: REQ-001
    story_id: US-CI-01
    persona: "Web visitor (unauthenticated); case read by Support_Agent PSG"
    sandbox: UAT1
    artefact: "assignmentRules/Case.assignmentRules-meta.xml"
    seed_data: "Account Contoso Inc (Region__c = US), no Premier entitlement"
    test_type: apex
    negative: false
    given: "the web form is published and Support_Case_Routing is the only active Case assignment rule"
    when: "a visitor submits the form with Severity__c = 4 and no billing routing address"
    then: "the case Owner is the queue Tier_1_General and Case.Origin is Web"
    proof: "SELECT Id, Origin, Owner.Name, Owner.Type FROM Case WHERE Id = :caseId"

  - ac_id: AC-001.3
    req_id: REQ-001
    story_id: US-CI-01
    persona: "Web visitor (unauthenticated)"
    sandbox: UAT1
    artefact: "settings/Case.settings-meta.xml"
    seed_data: "one case whose values match no rule entry"
    test_type: apex
    negative: true
    given: "a case whose field values match none of the entries in Support_Case_Routing"
    when: "the case is created through the web form"
    then: "the case Owner is the CaseSettings defaultCaseOwner, the queue Tier_1_General"
    proof: "SELECT Id, Owner.Name, Owner.Type FROM Case WHERE Id = :caseId"

  - ac_id: AC-002.1
    req_id: REQ-002
    story_id: US-CI-02
    persona: "External submitter; case read by Support_Agent PSG"
    sandbox: UAT1
    artefact: "autoResponseRules/Case.autoResponseRules-meta.xml"
    seed_data: "one web submission from qa+1@acme.example.invalid"
    test_type: manual
    negative: false
    given: "the Case_Acknowledgement rule is active and its Origin = Web entry uses Case_Web_Acknowledgement from support@acme.example"
    when: "a visitor submits the web form with a valid email address"
    then: "exactly one acknowledgement reaches the submitted address, from support@acme.example, containing the case number"
    proof: "Setup > Email Log Files entry for the recipient in the test window"

  - ac_id: AC-002.2
    req_id: REQ-002
    story_id: US-CI-02
    persona: "External sender; case read by Support_Agent PSG"
    sandbox: UAT1
    artefact: "autoResponseRules/Case.autoResponseRules-meta.xml"
    seed_data: "one inbound email to support@acme.example from qa+2@acme.example.invalid"
    test_type: manual
    negative: true
    given: "the routing address support@acme.example sets caseOrigin to Email"
    when: "an external sender emails support@acme.example"
    then: "no message using Case_Web_Acknowledgement is sent, and Case_Email_Acknowledgement is used instead"
    proof: "Setup > Email Log Files, plus SELECT Id, Origin FROM Case WHERE Id = :caseId"

  - ac_id: AC-003.1
    req_id: REQ-003
    story_id: US-CI-04
    persona: "Support manager Dee — Support_Agent + Support_Manager"
    sandbox: UAT1
    artefact: "escalationRules/Case.escalationRules-meta.xml"
    seed_data: "one EMEA case created Friday 17:30 Europe/London, untouched"
    test_type: manual
    negative: false
    given: "the case carries the EMEA Support Hours calendar and its escalation entry uses businessHoursSource Case with minutesToEscalation 480"
    when: "the case is created Friday 17:30 London and no one touches it"
    then: "no escalation action runs at the weekend and the case Owner becomes Tier_2_Support_Queue on Monday morning"
    proof: "SELECT Field, OldValue, NewValue, CreatedDate, CreatedBy.Name FROM CaseHistory WHERE CaseId = :caseId AND Field = 'Owner'"

  - ac_id: AC-003.2
    req_id: REQ-003
    story_id: US-CI-04
    persona: "Tier 1 agent Jo — Support_Agent PSG"
    sandbox: UAT1
    artefact: "escalationRules/Case.escalationRules-meta.xml"
    seed_data: "same EMEA case, edited 2 business hours after creation"
    test_type: manual
    negative: true
    given: "the same case and calendar, with disableEscalationWhenModified true on that entry"
    when: "Jo edits the case 2 business hours after creation"
    then: "the escalation action never runs and the Owner is unchanged at the end of the window"
    proof: "SELECT Field, CreatedDate FROM CaseHistory WHERE CaseId = :caseId AND Field = 'Owner'"

  - ac_id: AC-004.1
    req_id: REQ-004
    story_id: US-CI-07
    persona: "Tier 1 agent Jo — Support_Agent PSG; alert verified by Dee"
    sandbox: UAT1
    artefact: "entitlementProcesses/Premier_Support_v1.entitlementProcess-meta.xml"
    seed_data: "one Premier case on Northwind Ltd inside Premier_Support_v1"
    test_type: manual
    negative: false
    given: "the First Response milestone has minutesToComplete 240 on the EMEA calendar and a time trigger with timeLength -60 minutes"
    when: "180 business minutes pass with no first response"
    then: "the warning action fires once, the owner receives the alert, and the milestone is still open"
    proof: "SELECT CaseId, TargetDate, IsCompleted, IsViolated, TimeRemainingInMins FROM CaseMilestone WHERE CaseId = :caseId"

  - ac_id: AC-004.3
    req_id: REQ-004
    story_id: US-CI-07
    persona: "Tier 1 agent Jo — Support_Agent PSG"
    sandbox: UAT1
    artefact: "entitlementProcesses/Premier_Support_v1.entitlementProcess-meta.xml"
    seed_data: "one case on Contoso Inc, which holds no Premier entitlement"
    test_type: manual
    negative: true
    given: "a case on an account that holds no Premier entitlement"
    when: "the case is created and left untouched past 240 minutes"
    then: "Case.SlaStartDate is null, no CaseMilestone row exists, and no warning or violation action fires"
    proof: "SELECT Id, SlaStartDate FROM Case WHERE Id = :caseId; SELECT Id FROM CaseMilestone WHERE CaseId = :caseId"

  - ac_id: AC-005.1
    req_id: REQ-005
    story_id: US-CI-06
    persona: "Tier 1 agent Jo — Support_Agent PSG, member of Tier_1_General"
    sandbox: UAT1
    artefact: "permissionsets/Support_Agent.permissionset-meta.xml"
    seed_data: "one case owned by the Tier_1_General queue, Status New"
    test_type: apex
    negative: false
    given: "Support_Agent grants Case allowRead and allowEdit, the Case OWD is Private, and Jo is a member of Tier_1_General"
    when: "Jo changes Status from New to Working"
    then: "the save succeeds and Case.Status is Working"
    proof: "SELECT RecordId, HasEditAccess FROM UserRecordAccess WHERE UserId = :joId AND RecordId = :caseId"

  - ac_id: AC-005.2
    req_id: REQ-005
    story_id: US-CI-06
    persona: "Billing agent Mia — Billing_Case_Access, not a member of Tier_2_Support_Queue"
    sandbox: UAT1
    artefact: "permissionsets/Billing_Case_Access.permissionset-meta.xml"
    seed_data: "one case owned by the Tier_2_Support_Queue"
    test_type: apex
    negative: true
    given: "Mia holds Billing_Case_Access with Case allowRead and allowEdit but is not a member of Tier_2_Support_Queue"
    when: "Mia opens that case's record id directly by URL"
    then: "the platform returns insufficient privileges and the case appears in no list view available to Mia"
    proof: "SELECT RecordId, HasReadAccess, HasEditAccess FROM UserRecordAccess WHERE UserId = :miaId AND RecordId = :caseId"

  - ac_id: AC-006.1
    req_id: REQ-006
    story_id: US-CI-08
    persona: "Tier 1 agent Jo — Support_Agent PSG"
    sandbox: UAT1
    artefact: "objects/Case/validationRules/Close_Requires_Resolution.validationRule-meta.xml"
    seed_data: "one case owned by Jo, Status Working, Resolution__c blank"
    test_type: apex
    negative: true
    given: "the Close_Requires_Resolution rule is active and the case has Status Working with Resolution__c blank"
    when: "Jo sets Status to Closed"
    then: "the save is rejected with the message 'Enter a resolution before closing this case.' against Resolution__c, and Status is still Working"
    proof: "Database.update(case, false) returns a SaveResult whose getErrors() carries the message"

  - ac_id: AC-006.2
    req_id: REQ-006
    story_id: US-CI-08
    persona: "Tier 1 agent Jo — Support_Agent PSG"
    sandbox: UAT1
    artefact: "objects/Case/validationRules/Close_Requires_Resolution.validationRule-meta.xml"
    seed_data: "the same case with Resolution__c populated"
    test_type: apex
    negative: false
    given: "the same case with Resolution__c set to 'Replaced the licence key'"
    when: "Jo sets Status to Closed"
    then: "the save succeeds and Case.Status is Closed"
    proof: "SELECT Id, Status FROM Case WHERE Id = :caseId"
```

---

## 6. Automatable, and the platform fact that decides it

| req_id | Verdict | The fact behind the verdict |
|---|---|---|
| REQ-001 (AC-001.1–.3) | **Apex** | `Database.DMLOptions.assignmentRuleHeader` takes `useDefaultRule` or `assignmentRuleId` and is set on the record before `insert` (`apexdev.txt` L8530–8560). Write it into the criterion, because `useDefaultRule` "affects only the default assignment rule and does not disable other existing assignment rules on the object" (`apexrefguide.txt` L148033–148034), and with no assignment rules in the org, API 30.0 and later leaves the case **unassigned** rather than falling to the default owner (`apexdev.txt` L8566–8569). |
| REQ-001 (AC-001.4) | **Manual** | The three load paths disagree about whether rules run at all: Data Loader's "Assignment rule" setting is blank unless populated and "overrides Owner values in your CSV file" (`salesforce_data_loader.txt` L379–383); Bulk API 2.0's `assignmentRuleId` is Optional on the job resource (`api_asynch.txt` L1591–1595); REST "defaults to using the active assignment rules" when the header is absent (`api_rest.txt` L691–694). An Apex test proves the rule, not the tool, so the tool has to be exercised by hand. |
| REQ-002 | **Manual** | The oracle is an email arriving at an address outside the org. Nothing in the transaction observes it. |
| REQ-003 | **Manual** | Escalation is time-based and runs on the business-hours clock (`object_reference.txt` L53105); the criterion's whole point is elapsed working time, which a synchronous test cannot advance. |
| REQ-004 | **Manual** | Milestone time triggers are the same shape — `timeLength` measured against the target completion date (`api_meta.txt` L59210–59217). |
| REQ-005 | **Apex** | `System.runAs` blocks run DML in the target user's context and are the supported way to mix user setup with data in one test (`apexdev.txt` L8905–8910). Assert on `UserRecordAccess`, not on a UI outcome. |
| REQ-006 | **Apex** | Validation runs at step 5 of the save order (`apexdev.txt` L15442), inside the transaction, so `Database.update(records, false)` and `SaveResult.getErrors()` are a complete oracle — including the bulk case. |

"Automatable" is a property of the **oracle**, not of the behaviour. If the only way to observe the
Then is to wait for a clock or read a mailbox, the criterion is manual no matter how much of the
build is code.

---

## 7. The same criteria as a markdown table

The checker accepts this shape too, for story tools that hold a table but not a YAML block. Column
headers are matched case-insensitively; `Given`, `When`, `Then`, `AC`/`ac_id`, `REQ`/`req_id`,
`Persona`, `Test type` and `Artefact` must all be present.

| ac_id | req_id | persona | test_type | artefact | negative | given | when | then | proof |
|---|---|---|---|---|---|---|---|---|---|
| AC-001.1 | REQ-001 | Web visitor; case read by Support_Agent PSG | apex | assignmentRules/Case.assignmentRules-meta.xml | no | Support_Case_Routing is the only active Case assignment rule | a visitor submits the web form with Severity__c = 4 | the case Owner is the queue Tier_1_General and Origin is Web | SELECT Origin, Owner.Name, Owner.Type FROM Case WHERE Id = :caseId |
| AC-001.3 | REQ-001 | Web visitor | apex | settings/Case.settings-meta.xml | yes | a case matches no entry in Support_Case_Routing | the case is created through the web form | the Owner is the CaseSettings defaultCaseOwner, the queue Tier_1_General | SELECT Owner.Name, Owner.Type FROM Case WHERE Id = :caseId |
| AC-006.1 | REQ-006 | Tier 1 agent Jo — Support_Agent PSG | apex | objects/Case/validationRules/Close_Requires_Resolution.validationRule-meta.xml | yes | the rule is active and Resolution__c is blank on a Working case | Jo sets Status to Closed | the save is rejected with "Enter a resolution before closing this case." and Status is still Working | Database.update(case, false) SaveResult.getErrors() |

---

## 8. What this file does not decide

- **Which automation builds each behaviour.** REQ-003's escalation could be an escalation rule, a
  scheduled Flow or Apex; `standards/decision-trees/automation-selection.md` owns that call, and the
  case-intake build already recorded it (CWB-AUT-004). The criteria are written so that any of the
  three would satisfy them — which is the test that they describe behaviour and not implementation.
- **The sandbox type.** UAT1 is Full because `admin/uat-and-acceptance-criteria/references/worked-examples.md`
  § 2.1 routed it there; this file inherits the decision rather than re-deriving it.
- **The exact validation-rule formula.** REQ-006 pins the message and the field it lands against.
  `templates/admin/validation-rule-patterns.md` owns the formula.
- **Whether an auto-response send is queryable.** Flagged UNVERIFIED under REQ-002 and left as an
  open item for the sandbox pass, not resolved here.
