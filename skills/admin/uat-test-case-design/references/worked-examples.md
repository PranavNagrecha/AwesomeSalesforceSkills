# Worked Examples — The UAT Test-Case Set for the Acme Case-Intake Build

One build, one executable script set. The build is the Service Cloud case-intake solution in
`skills/admin/case-management-setup/references/worked-example-case-intake.md`.
`skills/admin/acceptance-criteria-given-when-then/references/worked-examples.md` turned its six
requirements into Given/When/Then criteria. **This file turns those criteria into the manual test
cases a human runs**, in the field schema SKILL.md § The Canonical UAT Case Schema defines — and it
is the artefact `standards/build-orchestration.md` § 5 collects when a step declares an acceptance
test of type `manual` ("a checklist line the human ticks at the milestone gate").

Boundaries, so nothing here is written twice:

| Concern | Owned by |
|---|---|
| The requirement statements and their `REQ-nnn` ids | `admin/requirements-gathering-for-sf` |
| The Given/When/Then form of each `AC-nnn.n`, and what proves it | `admin/acceptance-criteria-given-when-then` § 4 |
| Programme scope: environment rationale, persona roster, defect taxonomy, sign-off | `admin/uat-and-acceptance-criteria` §§ 2, 4, 5 |
| Which sandbox type, its capacity and its refresh floor | `admin/sandbox-strategy` § Type Capacities and Refresh Windows |
| Post-refresh isolation (deliverability, `.invalid`, CronTriggers) | `devops/sandbox-data-isolation-gotchas` |
| The matrix that closes the `REQ → step → artefact → test` loop | `admin/requirements-traceability-matrix` § 3 |
| The five acceptance-test runners and the deploy deny-list | `standards/build-orchestration.md` § 5 |
| **The executable script: steps, per-step expected results, evidence, pass rule, automation verdict** | **this skill** |

---

## 1. Id conventions, and why there are three id spaces and not one

| Id | Shape | Minted by | Example |
|---|---|---|---|
| `REQ-nnn` | requirement | `admin/requirements-traceability-matrix` § ID Conventions | `REQ-001` |
| `AC-nnn.n` | criterion, scoped to its requirement | `admin/acceptance-criteria-given-when-then` § 1 | `AC-001.3` |
| `US-CI-nn` | story, mirrored from the agile tool | `admin/uat-and-acceptance-criteria` § 1 | `US-CI-01` |
| `UAT-CI-nnn` | **programme** case — the row the RTM's `test_id` column carries | `admin/uat-and-acceptance-criteria` § 3 | `UAT-CI-002` |
| `TC-CI-nnn` | **script** case — one executable run, this file's unit | **this skill** | `TC-CI-005` |

`TC-` is not a rename of `UAT-`. One programme case can only carry one result, and several criteria
under one requirement have different personas, different seed data and different oracles — so
`UAT-CI-002` ("mail to `billing@` is routed and acknowledged") decomposes into `TC-CI-002` (routing,
Jo's seat, a SOQL oracle) and `TC-CI-005`/`TC-CI-006` (acknowledgement, an external mailbox, an email
oracle). That is SKILL.md § One AC Scenario → One UAT Case applied downward, not a fourth numbering
scheme: every `TC-` row carries its `programme_case_id`, so the RTM keeps exactly the ids it had.

Rule the checker enforces: **`TC-` ids are unique, well-formed, and every `ac_id` resolves to a
criterion in the criteria file** when one is present in the manifest directory.

---

## 2. The run context every case inherits

Written once. A case that restates it is duplicating the programme file; a case that omits it is not
reproducible.

```yaml
run_context:
  build: "Acme Case Intake — release 2026.R3"
  sandbox: UAT1                      # Full; type decided in admin/sandbox-strategy, not here
  sandbox_refreshed_on: 2026-08-24
  build_deployed_on: 2026-08-26
  ui: "Lightning Experience desktop"  # formFactor Large; see § 6, gotcha on form factor
  email_deliverability: "All Email"
  contact_emails_scrubbed: true       # to qa+<n>@acme.example.invalid
  personas:
    P-TIER1:   { user: jo.tan@acme.com.uat1,   profile: "Minimum Access — Salesforce", grants: ["Support_Agent"] }
    P-BILLING: { user: mia.ross@acme.com.uat1, profile: "Minimum Access — Salesforce", grants: ["Billing_Case_Access"] }
    P-MANAGER: { user: dee.olu@acme.com.uat1,  profile: "Standard User",               grants: ["Support_Agent", "Support_Manager"] }
    P-DATA:    { user: sam.ito@acme.com.uat1,  profile: "Standard User",               grants: ["Data_Load_Operator"] }
    P-EXT:     { user: "external submitter — no Salesforce licence",                   grants: [] }
  permission_gate: "For every persona, PermissionSetGroup.Status = 'Updated' before the tester logs in"
  no_persona_is_an_administrator: true
```

`permission_gate` is a real query, not a ritual. `PermissionSetGroup.Status` is a filterable,
restricted picklist with the values `Updated` ("The group is current"), `Outdated` ("The group
requires recalculation"), `Updating` ("The group is in recalculation mode") and `Failed`
(`object_reference.txt` L217708–217712; the same four values are on the metadata type at
`api_meta.txt` L95345–95352). So the precondition "the tester has the permissions" is checkable
before the run instead of discovered as a false-fail during it:

```sql
SELECT DeveloperName, Status
FROM   PermissionSetGroup
WHERE  DeveloperName IN ('Support_Agent')
```

---

## 3. The thirteen cases

Each case gives: the criterion it proves, the seat it runs from, what is seeded, numbered steps with
a per-step expected result, what evidence closes it, the pass rule, and whether it should stay
manual. Steps name a Setup destination as **"Setup → search for X"** rather than a menu path,
because Setup's tree is documented only in Salesforce Help, which is not a citable source here.

### TC-CI-001 — a Severity 4 web case lands in Tier 1 General

`ac_id: AC-001.1` · `req_id: REQ-001` · `story_id: US-CI-01` · `programme_case_id: UAT-CI-001` ·
persona **P-EXT** submits, **P-TIER1** verifies · `negative_path: false`

**Seed:** Account `Contoso Inc` (`Region__c = US`), no Premier entitlement. `Support_Case_Routing` is
the only active Case assignment rule.

| # | Step | Expected result |
|---|---|---|
| 1 | As P-TIER1, run `SELECT COUNT() FROM Case WHERE CreatedDate = TODAY` and record the number | A baseline count is recorded; nothing is asserted yet |
| 2 | Open the published web-to-case form in a private browser window (no Salesforce session) | The form renders and accepts input without a login |
| 3 | Submit with `Severity__c = 4`, subject `TC-CI-001 web intake`, an email address ending `.invalid`, and no billing routing address | The form returns its confirmation page; no error |
| 4 | As P-TIER1, run `SELECT Id, CaseNumber, Origin, Owner.Name, Owner.Type FROM Case WHERE Subject = 'TC-CI-001 web intake'` | Exactly one row; `Origin = 'Web'`; `Owner.Name = 'Tier 1 General'`; **`Owner.Type = 'Queue'`** |
| 5 | Open that case and expand the **Case History** related list | A row shows the owner being set, attributed to the CaseSettings automated-change user, not to the submitter |

**Why step 4 asserts `Owner.Type` and not just the name.** `Case.OwnerId` is polymorphic and
"Refers To Group, User" (`object_reference.txt` L62575–62587), and `Group.Type` is a required,
filterable, restricted picklist whose values include `Queue` — "Public group that includes all the
User records that are members of a queue" (`object_reference.txt` L154307–154312, L154341–154342). A
user happening to be named "Tier 1 General" would pass a name-only assertion.

**Why step 5 is in the script.** `CaseSettings.defaultCaseUser` "Specifies the user listed in the
Case History related list for automated case changes from: Assignment rules, Escalation rules,
On-Demand Email-to-Case, Cases logged in the Self-Service portal" (`api_meta.txt` L111705–111710).
That is what separates "the rule assigned it" from "someone assigned it", and it is only readable if
`Case.OwnerId` is a tracked field — history "is available for **tracked fields** of the object"
(`object_reference.txt` L62818–62819).

**Evidence:** SOQL result set from step 4 (pasted into the run sheet) + screenshot of the Case
History related list from step 5.
**Pass rule:** all five steps meet their expected result. Step 4 alone is not a pass.
**Automation candidate:** `apex` — `Database.DMLOptions.assignmentRuleHeader` puts the rule inside a
test transaction. Kept manual for this release only because the web form itself is the entry point.

---

### TC-CI-002 — a billing-address email case lands in Billing, not Tier 1

`ac_id: AC-001.2` · `req_id: REQ-001` · `story_id: US-CI-01` · `programme_case_id: UAT-CI-002` ·
persona **P-EXT** sends, **P-TIER1** verifies · `negative_path: false`

**Seed:** routing address `billing@acme.example` verified, its `caseOrigin` set to `Email`; queue
`Billing_Queue` exists and is Case-enabled.

| # | Step | Expected result |
|---|---|---|
| 1 | As P-TIER1, confirm the routing address is verified: **Setup → search for "Email-to-Case"**, open the routing address list | `billing@acme.example` shows a verified state |
| 2 | From an external mailbox, send a plain-text mail to `billing@acme.example`, subject `TC-CI-002 billing intake` | The mail is accepted by the receiving MTA; no bounce within 5 minutes |
| 3 | As P-TIER1, run `SELECT Id, Origin, Owner.Name, Owner.Type FROM Case WHERE Subject = 'TC-CI-002 billing intake'` | Exactly one row; `Origin = 'Email'`; `Owner.Name = 'Billing Queue'`; `Owner.Type = 'Queue'` |
| 4 | On that case, open the related email record and read its direction | The inbound message is recorded against the case |

**Evidence:** SOQL result set from step 3; screenshot of the case with the inbound email.
**Pass rule:** steps 2–4 all meet expectation. A bounce at step 2 is `Blocked`, not `Fail` — it is an
environment result, not a build result.
**Automation candidate:** `none` — the trigger is a message arriving from outside the org, which no
in-transaction oracle observes.

---

### TC-CI-003 — a case matching no rule entry lands on the declared default (negative)

`ac_id: AC-001.3` · `req_id: REQ-001` · `story_id: US-CI-01` · `programme_case_id: UAT-CI-001` ·
persona **P-EXT** submits, **P-MANAGER** verifies · `negative_path: true`

**Seed:** a field combination that matches no entry in `Support_Case_Routing` — recorded in the seed
note by value, not as "something that doesn't match".

| # | Step | Expected result |
|---|---|---|
| 1 | As P-MANAGER, read the declared default: **Setup → search for "Support Settings"**, note the Default Case Owner and its type | A queue named `Tier_1_General`, owner type Queue |
| 2 | Submit the web form with the non-matching field combination, subject `TC-CI-003 fallthrough` | The form returns its confirmation page |
| 3 | Run `SELECT Id, Owner.Name, Owner.Type, CreatedBy.Name FROM Case WHERE Subject = 'TC-CI-003 fallthrough'` | `Owner.Name = 'Tier 1 General'`; `Owner.Type = 'Queue'` |
| 4 | Confirm on the same row that the owner is **not** the submitting or integration user | `Owner.Type` is `Queue`, never `User` |

**Why this case exists at all.** `CaseSettings.defaultCaseOwner` "Specifies the default owner of a
case when assignment rules fail to locate an owner" and `defaultCaseOwnerType` "Specifies whether the
default case owner is a user or a queue" (`api_meta.txt` L111700–111703). The rule therefore has two
outcomes, and only a criterion pins which queue the second one is. A script that tests only matching
inputs leaves the fall-through undefined and undefended.

**Evidence:** screenshot of the Support Settings default owner (step 1) + SOQL result set (step 3).
The screenshot matters: the setting is what makes the SOQL result *correct* rather than merely
observed.
**Pass rule:** step 3 **and** step 4. A pass on step 3 with `Owner.Type = 'User'` is a fail.
**Automation candidate:** `apex`.

---

### TC-CI-004 — a 200-row backlog load routes the way a UI case does (bulk)

`ac_id: AC-001.4` · `req_id: REQ-001` · `story_id: US-CI-01` · `programme_case_id: UAT-CI-005` ·
persona **P-DATA** · `negative_path: false`

**Seed:** `cases_backlog_200.csv` with mixed `Origin` values; one UI-created control case per distinct
field combination, created before the load.

| # | Step | Expected result |
|---|---|---|
| 1 | As P-DATA, open Data Loader and authenticate against the **UAT1** server host, not production | The session banner names the sandbox host |
| 2 | Settings → set **Import batch size** to `200` and select **Use SOAP API** | Both values persist after Save |
| 3 | Settings → paste the id of `Support_Case_Routing` into the **Assignment rule** field | The field holds the rule id; it is not blank |
| 4 | Insert → object `Case` → source `cases_backlog_200.csv` → map fields → run | The run completes and Data Loader writes a `success` file and an `error` file |
| 5 | Open the `success` CSV and the `error` CSV | 200 rows in `success`, 0 rows in `error`; the success rows carry newly generated record ids |
| 6 | Run `SELECT Origin, Owner.Name, COUNT(Id) FROM Case WHERE CreatedDate = TODAY GROUP BY Origin, Owner.Name` | The owner distribution equals the control set's, per `Origin` |

**The three platform facts this case is pinned to.** Data Loader's "maximum import batch size is 200
records for SOAP API and 10000 records for Bulk API… If the **Use Bulk API 2.0** option is selected,
then neither batch size is used because Bulk API 2.0 handles batch size automatically"
(`salesforce_data_loader.txt` L351–359) — so step 2 is what makes this a single-transaction limit
test rather than an unspecified load. The **Assignment rule** setting "Specify the ID of the
assignment rule to use for inserts, updates, and upserts… The assignment rule overrides Owner values
in your CSV file" (`salesforce_data_loader.txt` L379–383) — leave step 3 out and the CSV's owner
column wins and the case silently proves nothing. And step 5 has real artefacts to attach: "Data
Loader generates two CSV output files… One file name begins with `success`, and the other starts with
`error`", where the success file carries "a column with the newly generated record IDs" and the error
file "contains the rejected records, with a column that describes why the load failed"
(`salesforce_data_loader.txt` L1135–1137, L1153–1155).

**Evidence:** both output CSVs, attached whole. Not a screenshot of a row count.
**Pass rule:** step 5 **and** step 6. 200 successes with the wrong owner distribution is a fail.
**Automation candidate:** `none` — an Apex test proves the rule, not the tool, and the three load
paths disagree about whether rules run by default (see `admin/acceptance-criteria-given-when-then`
§ 6, which already sourced that comparison).

---

### TC-CI-005 — the web acknowledgement is sent, from the org-wide address

`ac_id: AC-002.1` · `req_id: REQ-002` · `story_id: US-CI-02` · `programme_case_id: UAT-CI-002` ·
persona **P-EXT** submits, **P-TIER1** verifies · `negative_path: false`

**Seed:** auto-response rule `Case_Acknowledgement` active; its `Origin = Web` entry uses the Classic
template `Support_Templates/Case_Web_Acknowledgement` and the org-wide address
`support@acme.example`; a QA-readable mailbox at `qa+5@acme.example.invalid`.

| # | Step | Expected result |
|---|---|---|
| 1 | As P-TIER1, confirm deliverability: **Setup → search for "Deliverability"** | Access level reads `All Email` |
| 2 | Confirm the seeded contact email on the test account ends `.invalid` and is QA-readable | The address matches the scrubbed pattern |
| 3 | Submit the web form with that address, subject `TC-CI-005 ack` | Confirmation page returns |
| 4 | Read the QA mailbox within 10 minutes | **Exactly one** acknowledgement arrives; its `From` is `support@acme.example`; its body contains the case number |
| 5 | **Setup → search for "Email Log Files"**, request the log covering the test window | The log shows one delivery to the test address and none from a routing address |

**Evidence:** the received message headers (`From`, `Message-ID`) + the Email Log File row.
**Pass rule:** step 4 **exactly once** and step 5. Two acknowledgements is a fail, not a warning.
**Automation candidate:** `none` — the oracle is a message outside the org.

> **UNVERIFIED (2026-09-05):** step 1's Setup destination and step 5's Email Log Files feature are
> documented only in Salesforce Help, which cannot be fetched for this repo. The *behaviour* being
> tested is grounded (see TC-CI-006); the navigation is not. Confirm the destinations in the sandbox
> before handing this script to a tester.

---

### TC-CI-006 — an email-origin case does not get the web acknowledgement (negative)

`ac_id: AC-002.2` · `req_id: REQ-002` · `story_id: US-CI-02` · `programme_case_id: UAT-CI-002` ·
persona **P-EXT** sends, **P-TIER1** verifies · `negative_path: true`

**Seed:** routing address `support@acme.example` with `caseOrigin = Email`; the same QA mailbox.

| # | Step | Expected result |
|---|---|---|
| 1 | From the QA mailbox, send to `support@acme.example`, subject `TC-CI-006 email intake` | Mail accepted, no bounce |
| 2 | Run `SELECT Id, Origin FROM Case WHERE Subject = 'TC-CI-006 email intake'` | One row; `Origin = 'Email'` |
| 3 | Read the QA mailbox | The reply uses `Case_Email_Acknowledgement`, **not** `Case_Web_Acknowledgement` |
| 4 | Read the Email Log File row for the test window | No delivery whose template is the web acknowledgement |

**The attribute the whole case turns on.** Auto-response rules send "automatic email responses to
lead or case submissions based on the attributes of the submitted record" (`api_meta.txt`
L25196–25197), and the attribute here is `Case.Origin`, which each channel stamps from its own
setting — the routing address's `caseOrigin` "Specifies the default case origin for cases created
through this routing address" (`api_meta.txt` L112028–112029). So step 2 is not decoration: if
`Origin` is wrong, step 3's result is meaningless whichever way it goes.

**Evidence:** SOQL row (step 2) + the received message (step 3).
**Pass rule:** step 2 **and** step 3. Step 3 alone cannot distinguish "the right entry fired" from
"the wrong channel stamped the wrong Origin".
**Automation candidate:** `none`.

---

### TC-CI-007 — a case worked inside the window does not escalate (negative)

`ac_id: AC-003.2` · `req_id: REQ-003` · `story_id: US-CI-04` · `programme_case_id: UAT-CI-004` ·
persona **P-TIER1** acts, **P-MANAGER** verifies · `negative_path: true`

**Seed:** one case on `Northwind Ltd` (`Region__c = EMEA`) carrying the `EMEA Support Hours` calendar;
the non-Severity-1 escalation entry has `disableEscalationWhenModified = true` and
`minutesToEscalation = 480`. Book the elapsed window in the UAT calendar before the run — this case
occupies a working day.

| # | Step | Expected result |
|---|---|---|
| 1 | As P-MANAGER, record the starting owner: `SELECT Id, OwnerId, Owner.Name, BusinessHoursId, CreatedDate FROM Case WHERE Id = :caseId` | Owner is the Tier 1 queue; `BusinessHoursId` is the EMEA calendar, not null |
| 2 | As P-TIER1, open the case and change `Status` from `New` to `Working`, then save | The save succeeds; `Status` is `Working` |
| 3 | Wait past the 8-business-hour target on the EMEA calendar | — (elapsed time, not an assertion) |
| 4 | Run `SELECT Field, OldValue, NewValue, CreatedDate, CreatedBy.Name FROM CaseHistory WHERE CaseId = :caseId AND Field = 'Owner' ORDER BY CreatedDate` | **No** owner-change row after step 2's timestamp |
| 5 | Confirm no escalation notification reached the case owner's mailbox | No mail from the escalation template in the window |

**Why step 5 is separate from step 4.** An escalation action is not only a reassignment:
`EscalationAction` carries `assignedTo`, `assignedToType` (`User` or `Queue`), `assignedToTemplate`
("the template to use for the email that is automatically sent to the new owner"), `notifyCaseOwner`,
`notifyEmail`, `notifyTo` and `notifyToTemplate` (`api_meta.txt` L59483–59517). An entry configured to
notify without reassigning leaves `CaseHistory` empty, so a case whose only oracle is step 4 passes a
negative test that should have failed.

**Evidence:** the `CaseHistory` query result (empty result set, captured with its timestamp) + the
mailbox screenshot.
**Pass rule:** step 4 returns no post-edit owner row **and** step 5 finds no notification.
**Automation candidate:** `none` — escalation runs on elapsed business time, and "Escalation rules are
run only during these hours" (`object_reference.txt` L53105), which a synchronous test cannot advance.

---

### TC-CI-008 — the milestone warns before the first-response target

`ac_id: AC-004.1` · `req_id: REQ-004` · `story_id: US-CI-07` · `programme_case_id: UAT-CI-004` ·
persona **P-TIER1** owns, **P-MANAGER** verifies the alert · `negative_path: false`

**Seed:** a Premier case on `Northwind Ltd` inside `Premier_Support_v1`; the First Response milestone
has `minutesToComplete = 240` on the EMEA calendar and a time trigger with `timeLength = -60`.

| # | Step | Expected result |
|---|---|---|
| 1 | Confirm the case entered the process: `SELECT Id, SlaStartDate, EntitlementId FROM Case WHERE Id = :caseId` | `SlaStartDate` is **not** null |
| 2 | Read the milestone: `SELECT CaseId, MilestoneType.Name, TargetDate, IsCompleted, IsViolated, TimeRemainingInMins, BusinessHoursId FROM CaseMilestone WHERE CaseId = :caseId` | One open row; `IsCompleted = false`; `TargetDate` is 240 business minutes after `SlaStartDate` |
| 3 | Let 180 business minutes pass with no first response | — |
| 4 | Re-run the step-2 query | `IsCompleted` still `false`; `IsViolated` still `false`; `TimeRemainingInMins` is positive |
| 5 | Confirm the case owner received the warning alert | Exactly one warning notification, before `TargetDate` |

**The sign is the requirement.** `timeLength` is "the length of time between the time trigger
activation and the milestone target completion date… **Negative values** indicate that the target
completion date hasn't yet arrived and correspond to **warning** time triggers. **Positive values**
indicate that the target completion date has passed and correspond to **violation** time triggers"
(`api_meta.txt` L59213–59218). Step 4 is what distinguishes the two: a violation trigger would also
send one mail, but `IsViolated` would be true and `TimeRemainingInMins` negative.

**Evidence:** both `CaseMilestone` query results (before and at the warning) + the alert.
**Pass rule:** steps 4 **and** 5. A notification with `IsViolated = true` is a fail against this
criterion even though a mail arrived.
**Automation candidate:** `none` — time-based.

---

### TC-CI-009 — a non-Premier case never enters the process (negative)

`ac_id: AC-004.3` · `req_id: REQ-004` · `story_id: US-CI-07` · `programme_case_id: UAT-CI-004` ·
persona **P-TIER1** · `negative_path: true`

**Seed:** one case on `Contoso Inc`, which holds no Premier entitlement.

| # | Step | Expected result |
|---|---|---|
| 1 | Create the case as P-TIER1 with subject `TC-CI-009 no entitlement` | The case saves |
| 2 | Run `SELECT Id, SlaStartDate, EntitlementId FROM Case WHERE Subject = 'TC-CI-009 no entitlement'` | `SlaStartDate` is null **and** `EntitlementId` is null |
| 3 | Run `SELECT Id FROM CaseMilestone WHERE CaseId = :caseId` | Zero rows |
| 4 | Leave the case untouched past 240 minutes, then confirm no warning or violation notification was sent | No notification for this case in the window |

**Evidence:** both query results (step 2, and the empty result set at step 3, captured with its
timestamp) + the mailbox check.
**Pass rule:** all four. An empty `CaseMilestone` result with a non-null `SlaStartDate` is a fail —
it means the case entered the process and the milestone simply has not been created yet.
**Automation candidate:** `none` for step 4; steps 2–3 alone are `apex`.

---

### TC-CI-010 — a Tier 1 agent can edit a case in their queue

`ac_id: AC-005.1` · `req_id: REQ-005` · `story_id: US-CI-06` · `programme_case_id: UAT-CI-006` ·
persona **P-TIER1** · `negative_path: false`

**Seed:** Case OWD `Private`; one case owned by the queue `Tier_1_General`, of which Jo is a member;
`Support_Agent` grants Case `allowRead` and `allowEdit`.

| # | Step | Expected result |
|---|---|---|
| 1 | Confirm the permission gate: `SELECT DeveloperName, Status FROM PermissionSetGroup WHERE DeveloperName = 'Support_Agent'` | `Status = 'Updated'` — not `Outdated`, `Updating` or `Failed` |
| 2 | As P-TIER1, open the case from the Tier 1 queue list view | The record renders; the Status field is editable |
| 3 | Change `Status` from `New` to `Working` and save | The save succeeds with no error banner |
| 4 | Run `SELECT Id, Status FROM Case WHERE Id = :caseId` | `Status = 'Working'` |
| 5 | Run `SELECT RecordId, HasReadAccess, HasEditAccess, MaxAccessLevel FROM UserRecordAccess WHERE UserId = :joId AND RecordId = :caseId` | `HasEditAccess = true`; `MaxAccessLevel` is `Edit` or higher |

**Evidence:** screenshot of the saved record + the `UserRecordAccess` row.
**Pass rule:** steps 3, 4 **and** 5. Step 5 is what makes the pass reusable: it records *why* the
edit succeeded, so a later sharing change that breaks it is diffable.
**Automation candidate:** `apex` — "With the System method `runAs`, you can write test methods that
change the user context to an existing user or a new user. Then that user's sharing rules and
object-level and field-level permissions are enforced" (`apexdev.txt` L41325–41328). Steps 3–5 move
into a test; step 2's *rendering* does not, which is why the case stays manual until the UI settles.

---

### TC-CI-011 — object edit without record access is still no edit (negative)

`ac_id: AC-005.2` · `req_id: REQ-005` · `story_id: US-CI-06` · `programme_case_id: UAT-CI-006` ·
persona **P-BILLING** · `negative_path: true`

**Seed:** one case owned by `Tier_2_Support_Queue`; Mia holds `Billing_Case_Access` with Case
`allowRead` and `allowEdit` but is **not** a member of that queue. Mia is set up *without* any grant
that would let her in — the absence is the test condition, not an oversight.

| # | Step | Expected result |
|---|---|---|
| 1 | Confirm the grant Mia does hold, and that it does not include `viewAllRecords` or `modifyAllRecords` on Case | Object CRUD present; neither "all records" flag set |
| 2 | As P-BILLING, open every list view available on Case and search for the case number | The record appears in none of them |
| 3 | Paste the record id directly into the browser address bar | Access is denied; the record body does not render |
| 4 | Run `SELECT RecordId, HasReadAccess, HasEditAccess, MaxAccessLevel FROM UserRecordAccess WHERE UserId = :miaId AND RecordId = :caseId` | `HasReadAccess = false`; `MaxAccessLevel = 'None'` |
| 5 | Confirm no **restriction rule** and no **scoping rule** is active on Case in this org | Neither exists — so steps 2–4 are attributable to the sharing model |

**Why step 1 and step 5 exist.** `allowEdit` is "Required. Indicates whether the object referenced by
the object field can be edited by the users assigned to this permission set" — an *object*-level
capability (`api_meta.txt` L95077–95080). The two fields that override sharing are named separately:
`modifyAllRecords` and `viewAllRecords` grant access "regardless of the sharing settings for the
object" and are "Similar to the Modify All Data user permission, but limited to the individual object
level" (`api_meta.txt` L95085–95092, L95109–95116). Step 1 rules them out. Step 5 rules out the two
rule types that would make steps 2–4 pass for the wrong reason: `UserRecordAccess` "doesn't consider
whether a user's access is blocked due to a restriction rule" (`object_reference.txt` L303130–303131,
L303228–303230), and a **scoping rule** "controls the default records that your users see **without
restricting access**" (`api_meta.txt` L106019–106020) — so a scoping rule alone would empty the list
views at step 2 while leaving step 3 wide open.

**Evidence:** screenshot of the access-denied page (step 3) + the `UserRecordAccess` row (step 4).
**Pass rule:** steps 2, 3 **and** 4 together. Step 2 alone is not a deny.
**Automation candidate:** `apex`, inside `System.runAs`, asserting on `UserRecordAccess` rather than
on a UI outcome.

---

### TC-CI-012 — closing with an empty resolution is rejected, against the right field (negative)

`ac_id: AC-006.1` · `req_id: REQ-006` · `story_id: US-CI-08` · `programme_case_id: UAT-CI-003` ·
persona **P-TIER1** · `negative_path: true`

**Seed:** validation rule `Close_Requires_Resolution` active; one case owned by Jo, `Status =
'Working'`, `Resolution__c` blank.

| # | Step | Expected result |
|---|---|---|
| 1 | As P-TIER1, open the case and confirm `Resolution__c` is blank and visible on the layout | The field renders and is empty |
| 2 | Set `Status` to `Closed`, leave `Resolution__c` blank, and save | The save is **rejected** |
| 3 | Read the error text | It is exactly `Enter a resolution before closing this case.` |
| 4 | Note where the message renders | Against the `Resolution__c` field, not at the top of the page |
| 5 | Reload the record and run `SELECT Id, Status, Resolution__c FROM Case WHERE Id = :caseId` | `Status` is still `Working` |
| 6 | Confirm no owner change and no acknowledgement or escalation mail was produced by the rejected attempt | `CaseHistory` has no new row; no mail in the window |

**Steps 4 and 6 are the two that people drop, and both are grounded.** `errorMessage` is "Required.
The message that appears if the validation rule fails. The message must be 255 characters or less",
and `errorDisplayField` decides where it lands — "If you do not specify a value or the field isn't
visible on the page layout, the value changes automatically to Top of Page" (`api_meta.txt`
L45402–45403, L45388–45391). So a message that appears at the top of the page is evidence that
`errorDisplayField` is unset *or* that the field is off the layout, and step 1 is what tells the two
apart. Step 6 is provable rather than optimistic because a custom validation rule runs at **step 5**
of the save order while assignment rules are step 9, auto-response step 10 and escalation step 12
(`apexdev.txt` L15442, L15449, L15450, L15461) — a rejected save never reaches any of them.

**Evidence:** screenshot showing the error text *and* the field it is anchored to (one image, both
facts) + the SOQL row from step 5.
**Pass rule:** steps 2, 3, 4 **and** 5. Correct text at the top of the page is a fail against this
criterion.
**Automation candidate:** `apex` — `Database.update(record, false)` and `SaveResult.getErrors()` is a
complete in-transaction oracle for steps 2, 3 and 5; step 4's *placement* is not observable from Apex.

---

### TC-CI-013 — a 200-row close via Data Loader rejects only the offending rows (bulk)

`ac_id: AC-006.4` · `req_id: REQ-006` · `story_id: US-CI-08` · `programme_case_id: UAT-CI-005` ·
persona **P-DATA** · `negative_path: true`

**Seed:** 200 cases in `Status = 'Working'`, of which 40 have `Resolution__c` blank; a CSV setting
`Status = 'Closed'` on all 200.

| # | Step | Expected result |
|---|---|---|
| 1 | As P-DATA, set Import batch size `200` and **Use SOAP API** | Settings persist |
| 2 | Update → object `Case` → source CSV → map `Id`, `Status` → run | The run completes; both output files are written |
| 3 | Open the `success` CSV | 160 rows |
| 4 | Open the `error` CSV | 40 rows, each carrying `FIELD_CUSTOM_VALIDATION_EXCEPTION` and the rule's exact message |
| 5 | Confirm no row failed on a governor limit | No row's failure reason names CPU time, SOQL or DML limits |
| 6 | Run `SELECT Status, COUNT(Id) FROM Case WHERE Id IN :loadedIds GROUP BY Status` | 160 `Closed`, 40 `Working` |

**Evidence:** both output CSVs + the step-6 aggregate.
**Pass rule:** steps 3, 4, 5 **and** 6. 160/40 with a limit error inside the 40 is a fail: the rule
is not what rejected them.
**Automation candidate:** `apex` — `Database.update(records, false)` over 200 records reproduces this
exactly, including the partial-success shape.

---

## 4. The same thirteen as a lintable record

This is what `scripts/check_uat_case.py` reads. Save it as `uat-cases.yaml` beside the criteria file
and run:

```bash
# one case file
python3 skills/admin/uat-test-case-design/scripts/check_uat_case.py --file uat-cases.yaml

# a whole UAT folder — cases, criteria and run sheet linted together
python3 skills/admin/uat-test-case-design/scripts/check_uat_case.py --manifest-dir ./uat/

# after execution, gate the RTM handover
python3 skills/admin/uat-test-case-design/scripts/check_uat_case.py --manifest-dir ./uat/ --rtm-gate
```

Abbreviated to five cases; the remaining eight follow the same shape. The five are chosen
so the block lints clean on its own — each requirement it names carries a negative case.

```yaml
project: "Acme Case Intake — 2026.R3"
sandbox: UAT1
test_cases:
  - case_id: TC-CI-003
    ac_id: AC-001.3
    req_id: REQ-001
    story_id: US-CI-01
    programme_case_id: UAT-CI-001
    persona: "P-EXT submits; P-MANAGER verifies — Support_Agent + Support_Manager"
    sandbox: UAT1
    negative_path: true
    permission_setup:
      - "PermissionSetGroup Support_Agent Status = Updated before login"
      - "DO NOT assign System Administrator to any tester"
    data_setup:
      - "One web submission whose field values match no entry in Support_Case_Routing"
      - "CaseSettings default case owner recorded before the run"
    precondition: "UAT1, build of 2026-08-26, Lightning Experience desktop"
    steps:
      - step: "Read the declared default owner: Setup > search for Support Settings"
        expected: "Default Case Owner is the queue Tier_1_General"
      - step: "Submit the web form with the non-matching combination, subject TC-CI-003 fallthrough"
        expected: "The form returns its confirmation page"
      - step: "SELECT Id, Owner.Name, Owner.Type FROM Case WHERE Subject = 'TC-CI-003 fallthrough'"
        expected: "Owner.Name = Tier 1 General and Owner.Type = Queue"
      - step: "Confirm the owner is not the submitting or integration user"
        expected: "Owner.Type is Queue, never User"
    evidence:
      - type: screenshot
        of: "Support Settings default case owner"
      - type: soql
        of: "SELECT Id, Owner.Name, Owner.Type FROM Case WHERE Subject = 'TC-CI-003 fallthrough'"
    pass_rule: "Steps 3 and 4 both meet expectation; Owner.Type = User is a fail"
    automation_candidate: apex
    automation_rationale: "Database.DMLOptions.assignmentRuleHeader runs the rule inside a test transaction"
    pass_fail: "Not Run"

  - case_id: TC-CI-005
    ac_id: AC-002.1
    req_id: REQ-002
    story_id: US-CI-02
    programme_case_id: UAT-CI-002
    persona: "P-EXT submits; P-TIER1 verifies — Support_Agent"
    sandbox: UAT1
    negative_path: false
    permission_setup:
      - "PermissionSetGroup Support_Agent Status = Updated"
      - "DO NOT assign System Administrator to any tester"
    data_setup:
      - "Auto-response rule Case_Acknowledgement active, Origin = Web entry uses Case_Web_Acknowledgement"
      - "Seeded contact email rewritten to qa+5@acme.example.invalid and readable by QA"
    precondition: "Deliverability is All Email; contact emails scrubbed after the 2026-08-24 refresh"
    steps:
      - step: "Confirm deliverability: Setup > search for Deliverability"
        expected: "Access level reads All Email"
      - step: "Confirm the seeded contact email ends .invalid and is QA-readable"
        expected: "Address matches the scrubbed pattern"
      - step: "Submit the web form with that address, subject TC-CI-005 ack"
        expected: "Confirmation page returns"
      - step: "Read the QA mailbox within 10 minutes"
        expected: "Exactly one acknowledgement, From support@acme.example, body contains the case number"
      - step: "Setup > search for Email Log Files; request the log covering the test window"
        expected: "One delivery to the test address, none from a routing address"
    evidence:
      - type: email-log
        of: "Email Log File row for qa+5@acme.example.invalid in the test window"
      - type: screenshot
        of: "Received message headers showing From and Message-ID"
    pass_rule: "Step 4 arrives exactly once and step 5 shows no routing-address sender"
    automation_candidate: none
    automation_rationale: "The oracle is a message delivered outside the org; no in-transaction assertion observes it"
    pass_fail: "Not Run"

  - case_id: TC-CI-006
    ac_id: AC-002.2
    req_id: REQ-002
    story_id: US-CI-02
    programme_case_id: UAT-CI-002
    persona: "P-EXT sends; P-TIER1 verifies — Support_Agent"
    sandbox: UAT1
    negative_path: true
    permission_setup:
      - "PermissionSetGroup Support_Agent Status = Updated"
      - "DO NOT assign System Administrator to any tester"
    data_setup:
      - "Routing address support@acme.example with caseOrigin Email"
      - "One inbound mail from the QA mailbox qa+6@acme.example.invalid"
    precondition: "Deliverability is All Email; the QA mailbox is readable by the tester"
    steps:
      - step: "Send to support@acme.example from the QA mailbox, subject TC-CI-006 email intake"
        expected: "Mail accepted with no bounce inside 5 minutes"
      - step: "SELECT Id, Origin FROM Case WHERE Subject = 'TC-CI-006 email intake'"
        expected: "One row with Origin = Email"
      - step: "Read the QA mailbox"
        expected: "The reply uses Case_Email_Acknowledgement, not Case_Web_Acknowledgement"
      - step: "Read the Email Log File row for the test window"
        expected: "No delivery whose template is the web acknowledgement"
    evidence:
      - type: soql
        of: "SELECT Id, Origin FROM Case WHERE Subject = 'TC-CI-006 email intake'"
      - type: screenshot
        of: "Received message showing which template rendered"
    pass_rule: "Steps 2 and 3 together; step 3 alone cannot tell a wrong entry from a wrong Origin"
    automation_candidate: none
    automation_rationale: "The oracle is a message delivered outside the org"
    pass_fail: "Not Run"

  - case_id: TC-CI-011
    ac_id: AC-005.2
    req_id: REQ-005
    story_id: US-CI-06
    programme_case_id: UAT-CI-006
    persona: "P-BILLING — Billing_Case_Access, not a member of Tier_2_Support_Queue"
    sandbox: UAT1
    negative_path: true
    permission_setup:
      - "Assign Billing_Case_Access only"
      - "Confirm neither viewAllRecords nor modifyAllRecords is set on Case for that grant"
      - "DO NOT add Mia to Tier_2_Support_Queue — the absence is the test condition"
    data_setup:
      - "One case owned by the Tier_2_Support_Queue, Case OWD Private"
      - "No restriction rule and no scoping rule active on Case"
    precondition: "UAT1, Lightning Experience desktop, Mia logged in as herself"
    steps:
      - step: "Confirm the grant Mia holds excludes viewAllRecords and modifyAllRecords on Case"
        expected: "Object CRUD present; neither all-records flag set"
      - step: "Open every list view available on Case and search for the case number"
        expected: "The record appears in none of them"
      - step: "Paste the record id directly into the browser address bar"
        expected: "Access is denied; the record body does not render"
      - step: "SELECT RecordId, HasReadAccess, HasEditAccess, MaxAccessLevel FROM UserRecordAccess WHERE UserId = :miaId AND RecordId = :caseId"
        expected: "HasReadAccess = false and MaxAccessLevel = None"
      - step: "Confirm no restriction rule and no scoping rule is active on Case"
        expected: "Neither exists, so the deny is attributable to the sharing model"
    evidence:
      - type: screenshot
        of: "Access-denied page from the direct record id"
      - type: soql
        of: "UserRecordAccess row for (Mia, case)"
    pass_rule: "Steps 2, 3 and 4 together; step 2 alone is not a deny"
    automation_candidate: apex
    automation_rationale: "System.runAs enforces the user's sharing and object/field permissions; assert on UserRecordAccess"
    pass_fail: "Not Run"

  - case_id: TC-CI-013
    ac_id: AC-006.4
    req_id: REQ-006
    story_id: US-CI-08
    programme_case_id: UAT-CI-005
    persona: "P-DATA — Data_Load_Operator (API Enabled, Case Edit)"
    sandbox: UAT1
    negative_path: true
    permission_setup:
      - "Assign Data_Load_Operator"
      - "DO NOT assign System Administrator to the loader user"
    data_setup:
      - "200 cases in Status Working, 40 with Resolution__c blank"
      - "CSV setting Status = Closed on all 200 rows, keyed by Id"
    precondition: "Data Loader authenticated against the UAT1 server host, not production"
    steps:
      - step: "Set Import batch size 200 and select Use SOAP API"
        expected: "Both settings persist after Save"
      - step: "Update object Case from the CSV, mapping Id and Status, and run"
        expected: "The run completes and both output files are written"
      - step: "Open the success CSV"
        expected: "160 rows"
      - step: "Open the error CSV"
        expected: "40 rows, each with FIELD_CUSTOM_VALIDATION_EXCEPTION and the rule's exact message"
      - step: "Confirm no row failed on a governor limit"
        expected: "No failure reason names CPU time, SOQL or DML limits"
      - step: "SELECT Status, COUNT(Id) FROM Case WHERE Id IN :loadedIds GROUP BY Status"
        expected: "160 Closed and 40 Working"
    evidence:
      - type: loader-csv
        of: "Data Loader success and error output files, attached whole"
      - type: soql
        of: "Status aggregate over the loaded ids"
    pass_rule: "Steps 3, 4, 5 and 6; a limit error inside the 40 is a fail"
    automation_candidate: apex
    automation_rationale: "Database.update(records, false) over 200 records reproduces the partial-success shape exactly"
    pass_fail: "Not Run"
```

---

## 5. The same set as a markdown table

For story tools that hold a table but not YAML. The checker accepts this shape too; column headers
are matched case-insensitively and `case_id`, `ac_id`, `req_id`, `persona`, `sandbox`, `steps`,
`evidence`, `pass_rule` and `automation_candidate` must all be present.

| case_id | ac_id | req_id | story_id | persona | sandbox | negative | steps | evidence | pass_rule | automation_candidate |
|---|---|---|---|---|---|---|---|---|---|---|
| TC-CI-001 | AC-001.1 | REQ-001 | US-CI-01 | P-EXT submits, P-TIER1 verifies | UAT1 | no | 5 | soql; screenshot | Owner.Type = Queue and the history row is attributed to the automated-change user | apex |
| TC-CI-002 | AC-001.2 | REQ-001 | US-CI-01 | P-EXT sends, P-TIER1 verifies | UAT1 | no | 4 | soql; screenshot | Origin = Email and Owner.Name = Billing Queue | none |
| TC-CI-003 | AC-001.3 | REQ-001 | US-CI-01 | P-EXT submits, P-MANAGER verifies | UAT1 | **yes** | 4 | screenshot; soql | Owner is the declared default queue, never a user | apex |
| TC-CI-004 | AC-001.4 | REQ-001 | US-CI-01 | P-DATA | UAT1 | no | 6 | loader-csv; soql | 200 successes AND the owner distribution equals the control set | none |
| TC-CI-005 | AC-002.1 | REQ-002 | US-CI-02 | P-EXT submits, P-TIER1 verifies | UAT1 | no | 5 | email-log; screenshot | Exactly one acknowledgement, from the org-wide address | none |
| TC-CI-006 | AC-002.2 | REQ-002 | US-CI-02 | P-EXT sends, P-TIER1 verifies | UAT1 | **yes** | 4 | soql; screenshot | Origin = Email AND the email template is the email one | none |
| TC-CI-007 | AC-003.2 | REQ-003 | US-CI-04 | P-TIER1 acts, P-MANAGER verifies | UAT1 | **yes** | 5 | soql; screenshot | No owner-change history row AND no notification | none |
| TC-CI-008 | AC-004.1 | REQ-004 | US-CI-07 | P-TIER1 owns, P-MANAGER verifies | UAT1 | no | 5 | soql; screenshot | Warning fires while IsViolated is false and TimeRemainingInMins is positive | none |
| TC-CI-009 | AC-004.3 | REQ-004 | US-CI-07 | P-TIER1 | UAT1 | **yes** | 4 | soql | SlaStartDate null AND zero CaseMilestone rows | none |
| TC-CI-010 | AC-005.1 | REQ-005 | US-CI-06 | P-TIER1 | UAT1 | no | 5 | screenshot; soql | Save succeeds AND UserRecordAccess records why | apex |
| TC-CI-011 | AC-005.2 | REQ-005 | US-CI-06 | P-BILLING | UAT1 | **yes** | 5 | screenshot; soql | List views empty AND direct id denied AND HasReadAccess false | apex |
| TC-CI-012 | AC-006.1 | REQ-006 | US-CI-08 | P-TIER1 | UAT1 | **yes** | 6 | screenshot; soql | Rejected with the exact message, anchored to Resolution__c | apex |
| TC-CI-013 | AC-006.4 | REQ-006 | US-CI-08 | P-DATA | UAT1 | **yes** | 6 | loader-csv; soql | 160/40 split with no governor-limit failure | apex |

Coverage the checker reads off this table: 13 cases, 7 negative, 2 bulk, 5 personas, 0 System
Administrators, and every one of REQ-001…REQ-006 carrying at least one negative case.

---

## 6. The run sheet

Filled at execution, one row per attempt. A re-run after a fix is a **new row**, not an edit — the
first result is what the defect was raised against and deleting it deletes the audit trail.

```csv
run_id,case_id,tester,executed_on,result,evidence_ref,defect_id,notes
R-001,TC-CI-001,jo.tan@acme.com.uat1,2026-09-01,Pass,ev/TC-CI-001-owner.png,,
R-002,TC-CI-002,jo.tan@acme.com.uat1,2026-09-01,Pass,ev/TC-CI-002-soql.txt,,
R-003,TC-CI-003,dee.olu@acme.com.uat1,2026-09-01,Fail,ev/TC-CI-003-owner.png,DEF-2026R3-002,Owner was the integration user; catch-all entry sits above the specific entries
R-004,TC-CI-004,sam.ito@acme.com.uat1,2026-09-01,Fail,ev/TC-CI-004-error.csv,DEF-2026R3-007,14 of 200 rows rejected on Account lookup
R-005,TC-CI-005,jo.tan@acme.com.uat1,2026-09-02,Blocked,ev/TC-CI-005-note.md,,Deliverability was System Email Only after an unannounced refresh
R-006,TC-CI-006,jo.tan@acme.com.uat1,2026-09-02,Not Run,,,Blocked behind R-005
R-007,TC-CI-007,dee.olu@acme.com.uat1,2026-09-02,Pass,ev/TC-CI-007-history.txt,,
R-008,TC-CI-008,dee.olu@acme.com.uat1,2026-09-02,Pass,ev/TC-CI-008-milestone.txt,,
R-009,TC-CI-009,jo.tan@acme.com.uat1,2026-09-02,Pass,ev/TC-CI-009-sla.txt,,
R-010,TC-CI-010,jo.tan@acme.com.uat1,2026-09-02,Pass,ev/TC-CI-010-access.txt,,
R-011,TC-CI-011,mia.ross@acme.com.uat1,2026-09-02,Fail,ev/TC-CI-011-record.png,DEF-2026R3-004,Record rendered read-only instead of denying
R-012,TC-CI-012,jo.tan@acme.com.uat1,2026-09-02,Fail,ev/TC-CI-012-error.png,DEF-2026R3-011,Correct text but rendered at top of page
R-013,TC-CI-013,sam.ito@acme.com.uat1,2026-09-02,Pass,ev/TC-CI-013-error.csv,,
R-014,TC-CI-003,dee.olu@acme.com.uat1,2026-09-03,Pass,ev/TC-CI-003-owner-rerun.png,,Re-run after DEF-2026R3-002 fix
R-015,TC-CI-011,mia.ross@acme.com.uat1,2026-09-03,Pass,ev/TC-CI-011-denied.png,,Re-run after DEF-2026R3-004 fix
R-016,TC-CI-005,jo.tan@acme.com.uat1,2026-09-03,Pass,ev/TC-CI-005-maillog.txt,,Deliverability restored
R-017,TC-CI-006,jo.tan@acme.com.uat1,2026-09-03,Pass,ev/TC-CI-006-mail.png,,
R-018,TC-CI-012,jo.tan@acme.com.uat1,2026-09-03,Pass,ev/TC-CI-012-anchored.png,,Re-run after DEF-2026R3-011 fix
```

`result` uses the enum `{Pass, Fail, Blocked, Not Run}`. `Blocked` is not a soft `Fail`: R-005 is an
environment condition, and reporting it as a `Fail` would have raised a build defect against a
correct build. The distinction is what makes the "Environment" category in the defect taxonomy usable.

This sheet references all thirteen cases, while § 4's YAML block is abbreviated to five. Copy both
into one folder and the checker will correctly report the eight it cannot resolve — that is the
run-sheet integrity check doing its job, not a defect in the example. Extend the YAML to all thirteen
before linting them together.

`--rtm-gate` reads the **latest** row per case, which is why a re-run is a new row: R-014 is what
turns `REQ-001` green, and R-003 stays in the file as the evidence DEF-2026R3-002 was raised against.

---

## 7. Defect triage

Severity (P1–P4) and the six categories are defined in `admin/uat-and-acceptance-criteria`
§ Defect Classification and are not restated. What this table adds is the **script-level** columns —
which case found it, which criterion it violates, and whether the case is re-runnable once fixed.

| defect_id | case_id | ac_id | severity | category | summary | owner | status | blocks_release | re-run |
|---|---|---|---|---|---|---|---|---|---|
| DEF-2026R3-002 | TC-CI-003 | AC-001.3 | P1 | automation | Fall-through case owned by the integration user; catch-all rule entry sits above the specific entries | dee.olu@acme.com | Closed | yes | R-014 Pass |
| DEF-2026R3-004 | TC-CI-011 | AC-005.2 | P1 | sharing | Billing agent can open a Tier 2 queue case by direct record id | dee.olu@acme.com | Closed | yes | R-015 Pass |
| DEF-2026R3-007 | TC-CI-004 | AC-001.4 | P3 | data | 14 of 200 backlog rows fail on Account lookup after production merges | sam.ito@acme.com | Deferred | no | not re-run |
| DEF-2026R3-011 | TC-CI-012 | AC-006.1 | P2 | configuration | Validation message renders at top of page, not against `Resolution__c` | dee.olu@acme.com | Closed | no | R-018 Pass |
| — | TC-CI-005 | AC-002.1 | — | environment | Deliverability reverted to `System Email Only` after an unannounced refresh; logged, not raised as a build defect | release manager | Closed | no | R-016 Pass |

Two rules that keep this table honest, and both are script-level, not programme-level:

1. **A defect names the criterion, not the screen.** DEF-2026R3-011 is "AC-006.1's message placement
   assertion failed", which is arguable against a spec. "The error looked wrong" is not.
2. **A `Blocked` row never becomes a defect id.** R-005 has no `defect_id` because nothing was
   wrong with the build. It still gets an owner and a closing note, because a sandbox refreshed
   mid-cycle is a process defect even when the build is fine.

---

## 8. The automation verdict, and the platform fact behind each

`automation_candidate` is one of `apex`, `flow-test`, `none`. It is a property of the **oracle**, not
of the behaviour: if the only way to observe the expected result is to wait for a clock, read a
mailbox, or look at a rendered page, the case is manual no matter how much of the build is code.

| Verdict | When it applies | The fact behind it |
|---|---|---|
| `apex` | The expected result is observable inside the save transaction or from a query the test can run | `System.runAs` changes the user context and "that user's sharing rules and object-level and field-level permissions are enforced" (`apexdev.txt` L41325–41328); custom validation rules run at step 5 of the save order for every request source (`apexdev.txt` L15442) |
| `flow-test` | The behaviour is a record-triggered, autolaunched or Data Cloud-triggered flow | `FlowTest` "Represents the metadata associated with a flow test. Before you activate a **record-triggered, autolaunched, or Data Cloud-triggered** flow, you can test it to verify its expected results" (`api_meta.txt` L73961–73962). Screen flows and rule engines are out of its scope, so they cannot take this verdict |
| `none` | The oracle is outside the transaction: elapsed business time, a mailbox, or a rendered UI | "Escalation rules are run only during these hours" (`object_reference.txt` L53105); milestone warning-vs-violation is decided by the sign of `timeLength` measured against the target date (`api_meta.txt` L59213–59218) |

None of the thirteen cases takes `flow-test`, and that is information rather than an omission: the
one Flow in this build (`Case_Set_Calendar`, a before-save record-triggered flow) is in `FlowTest`'s
scope and should carry one — it is simply covered as a precondition here (TC-CI-007 step 1 asserts
`BusinessHoursId` is set) rather than as a case of its own.

---

## 9. What this file does not decide

- **Whether the criteria are the right ones.** `admin/acceptance-criteria-given-when-then` owns the
  Given/When/Then and its grounding; a script that argues with its criterion is a defect against the
  criterion, raised there.
- **Whether UAT1 should be a Full sandbox.** Inherited from `admin/uat-and-acceptance-criteria` § 2.1,
  which routed it there via `admin/sandbox-strategy` § Type Capacities and Refresh Windows.
- **Who signs off, and on what.** `admin/uat-and-acceptance-criteria` § 5.
- **Whether the `apex` verdicts get written.** That is `apex/test-class-standards` and
  `agents/test-class-generator/AGENT.md`. This file records the verdict and the reason; it does not
  generate the test.
- **The Setup navigation in steps 1 and 5 of TC-CI-005.** Flagged UNVERIFIED above and left as an open
  item for the sandbox pass, not resolved here.
