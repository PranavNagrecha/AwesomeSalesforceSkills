# Deploy order — M3-S02

Build: `northwind-sales` · Milestone: M3 (The discount approval and the rep's panel) · Step type: `automation` (declarative) · API version 62.0

This note is written by `agents/metadata-builder` Step 7 and is text for a human. Nothing in it is
executed by this agent or by any acceptance test.

Sourced from `skills/admin/approval-processes/references/metadata-examples.md` ("Where the files live",
the worked two-step Opportunity discount approval and its "How to read it", "The workflow actions the
process references", "package.xml", "Retrieve, lint, deploy"),
`skills/admin/approval-processes/SKILL.md` ("Questions to Ask Before Configuring", "Locking and Recall
Rules", "Deployable Metadata Shape", "Recommended Workflow" steps 3–7),
`skills/admin/approval-processes/references/gotchas.md` ("Blank Approver Fields Fail at Runtime",
"Activation Freezes the Step Structure Permanently", "A Record Enters Exactly One Process, Chosen by an
Order the Metadata Does Not Carry", "`userHierarchyField` Approvers Are Silently Illegal Without
`nextAutomatedApprover`", "Approval Actions Are Workflow Actions, and They Live in a Different File",
"The Lock Is Not Optional…", "Recall Does Not Undo Every Side Effect"),
`skills/admin/approval-processes/templates/approval-design-template.md` (Irreversible Decisions,
Overview, Entry Criteria, Step Design, Submission/Outcome/Recall Actions, Operational Checks),
`skills/admin/email-templates-and-alerts/references/gotchas.md` ("An Alert With No `recipients` And No
`ccEmails` Deploys Clean And Never Sends", "`senderAddress` Is Only Legal When `senderType` Is
`OrgWideEmailAddress`", "Half The Recipient Types Are Inert Without A Companion `field` Or `recipient`
Value", "Delete The Alert Before The Template, Never The Other Way Round"),
`skills/admin/email-templates-and-alerts/references/metadata-and-sender-identity.md` ("Org-wide email
address (the sender)"), `skills/admin/validation-rules/SKILL.md` ("Questions to Ask Before Configuring",
row 2) and `skills/admin/validation-rules/references/gotchas.md` ("A Workflow Field Update Re-Saves the
Record and Validation Rules Do Not Run Again"),
`skills/admin/change-management-and-deployment/references/metadata-examples.md` § 1, and this build's own
`artefacts/M3-S01/deploy-order.md` § 1.

**There is no org-validated approval process anywhere in this repository.** `find examples -type d -name
approvalProcesses` and `find examples -name '*.workflow-meta.xml'` both return nothing, and
`grep -ril approvalprocess examples/` returns nothing: the committed `case-onboarding` example — the one
build that survived real `checkOnly` deploys — ships no `ApprovalProcess` and no `Workflow` file. Every
element below is therefore grounded on a skill's fenced example, never on an artefact an org has accepted.
The nearest org-validated neighbours are `case-onboarding`'s `EmailFolder` / `EmailTemplate` pair
(`examples/builds/case-onboarding/artefacts/M3-S02/email/`), which M3-S01 already used, and its
`EscalationRules`, which is a different type. Where that matters below it is marked `UNVERIFIED
(2026-09-19):` on the line it affects.

## 0. Why API version 62.0

`plan.json` carries no `api_version` key, so `agents/metadata-builder/AGENT.md` ("Inputs") falls back to
`62.0`. Every step already built in this build declares the same number, and this step's `package.xml`
keeps it — so `scripts/mock_deploy.py`'s highest-version scan across the selected steps still sees one
version for the whole build. `approval-processes/references/metadata-examples.md` shows `62.0` in its own
`package.xml` fence, and neither `ApprovalProcess` (28.0+) nor `Workflow` (13.0+) has a version floor above
it. Raising the whole build's API version stays a plan-level decision, as M1-S02, M2-S05 and M3-S01 each
recorded.

## 1. The names this step copied, character for character

`artefacts/M3-S01/deploy-order.md` § 1 is the contract. These three strings were copied from its middle
column, not retyped:

| Where it lands here | The exact string | M3-S01's file behind it |
|---|---|---|
| `ApprovalProcess` → `<emailTemplate>` | `Sales_Approvals/Discount_Approval_Request` | `email/Sales_Approvals/Discount_Approval_Request.email-meta.xml` |
| `Workflow` → `<alerts><fullName>Notify_Owner_Discount_Approved</fullName>` → `<template>` | `Sales_Approvals/Discount_Approved` | `email/Sales_Approvals/Discount_Approved.email-meta.xml` |
| `Workflow` → `<alerts><fullName>Notify_Owner_Discount_Rejected</fullName>` → `<template>` | `Sales_Approvals/Discount_Rejected` | `email/Sales_Approvals/Discount_Rejected.email-meta.xml` |

**The two alert `fullName` values differ from the ones M3-S01's table used as placeholders, and that is
expected.** M3-S01 wrote `Notify_Submitter_Approved` / `Notify_Submitter_Rejected` — the worked example's
names — while saying in the same breath that they "are **not** this step's to own… If M3-S02 picks
different alert names, the three template strings in the middle column still stand unchanged."
`plan.json.steps[M3-S02].inputs.alerts` names `Notify_Owner_Discount_Approved` and
`Notify_Owner_Discount_Rejected`, and the step's own `manual` acceptance test spells both out, so the plan
is what was followed. What has to agree is internal to this step: each `<alerts><fullName>` and the
matching `<action><name>` inside the approval process, which `check_approval_design.py` resolves by exact
string and reported clean.

**No submit alert exists, deliberately.** Q33 lists four events; three send mail. Submit is sent by the
process's own `<emailTemplate>` element — "Omit the element to use the default approval-request template",
so naming it there replaces the platform default and no `WorkflowAlert` is involved. Adding an
`initialSubmissionActions` alert would send the manager two emails. Recall sends nothing.

## 2. Order inside this step, and why it is not optional

Both types ship in one `package.xml`, so one manifest deploy satisfies the ordering by itself. The order
matters for a split deploy, and it is the one ordering fact in this step that a reader cannot infer:

| # | Component | Because |
|---|---|---|
| 1 | `EmailTemplate` ×3 + `EmailFolder` (**M3-S01, not this step**) | `WorkflowAlert.template` is "Required. Named reference to an `EmailTemplate`. This email template isn't required to exist in the zip file, but it must exist in Metadata API" — validated against the *target org*. The process's `<emailTemplate>` is the same kind of reference. |
| 2 | `Workflow:Opportunity` — the two alerts and the four field updates | The approval process's action elements are only `WorkflowActionReference` pointers, "a `name` and a `type`… resolved against the object's workflow file at deploy time". "This is a separate metadata type in a separate directory, and it must be deployed first." A referenced alert or field update that is missing fails the deploy. |
| 3 | `ApprovalProcess:Opportunity.Discount_Approval` | Last: it names all six workflow actions and one email template. |

`skills/admin/approval-processes/references/metadata-examples.md` ("Retrieve, lint, deploy") states the same
sequence as separate commands: email and workflows first, the process second.

**Field updates and alerts are not "part of" the approval process.** They are `WorkflowFieldUpdate` and
`WorkflowAlert`, both living inside `workflows/Opportunity.workflow-meta.xml`, which is a `Workflow`
component in the manifest with member `Opportunity`. The approval file carries nothing but the six strings
that point at them. Rename one field update and the process still carries the old `<name>`; the match is
exact and the deploy fails on an unresolved reference.

**On the way back out, the order reverses.** Retirement is two deployments: remove or re-point the alerts
and the process's `emailTemplate` first, then delete the templates, then the folder.

## 3. Dependencies on components outside this step

| This step names | Which must already exist as | Built by |
|---|---|---|
| `Discount__c` (entry-criteria formula), `<field>Discount__c</field>` (approval page) | `CustomField` `Opportunity.Discount__c` (Percent, precision 5, scale 2) | M1-S01 |
| `Approval_Status__c` (all four field updates) | `CustomField` `Opportunity.Approval_Status__c`, restricted picklist `Pending` / `Approved` / `Rejected` | M1-S01 |
| `RecordType.DeveloperName = "Enterprise"` / `"Renewal"` | `RecordType` `Opportunity.Enterprise`, `Opportunity.Renewal` | M1-S01 |
| `Sales_Approvals/Discount_Approval_Request`, `…/Discount_Approved`, `…/Discount_Rejected` | `EmailTemplate` ×3 inside `EmailFolder` `Sales_Approvals` | M3-S01 |
| `Name`, `Owner`, `Amount` (approval page fields) | standard Opportunity fields | the platform |
| `<userHierarchyField>Manager</userHierarchyField>` | the standard `User.Manager` field, **populated per user** | org data — see § 5 |

**The three literal values are the picklist's, not the worked example's.** The skill's example writes
`Pending Approval` and `Draft`; M1-S01's field is a *restricted* picklist whose three values are `Pending`,
`Approved`, `Rejected`, so each `<literalValue>` was substituted to match the field definition. A literal
outside a restricted value set is a deploy-time or save-time failure, not a cosmetic difference.

**`Approved` is load-bearing beyond this step.** `artefacts/M2-S03/objects/Opportunity/validationRules/
Opportunity_Discount_Requires_Approval.validationRule-meta.xml` reads
`NOT(ISPICKVAL(Approval_Status__c, "Approved"))`. `Set_Approval_Status_Approved` writes exactly that
string. Change either and the discount rule stops recognising an approved deal.

**The entry criteria and that validation rule use the same threshold in the same representation.** The rule's
formula carries `Discount__c > 0.20`; this file's `<formula>` carries the same comparison, XML-escaped as
`Discount__c &gt; 0.20`. Decoded, the two are character-identical. D8 and assumption A35 are why the number
is `0.20` and not `20`: a Percent field "is expressed divided by 100 in formulas", and only the formula half
of that is grounded in this library.

`UNVERIFIED (2026-09-19):` **no cited reference shows an `entryCriteria` written as a `<formula>` at all.**
The element name is documented — `approval-processes/SKILL.md` ("`criteriaItems` **or** `formula`, never
both") and the design template's Entry Criteria row — but every fenced example in the library uses
`criteriaItems`. Two things follow that only an org can settle: whether `RecordType.DeveloperName` resolves
inside an approval entry-criteria formula (it does inside a validation rule, which is where M2-S03 uses it),
and whether the formula's `0.20` is read the same way here as in a validation rule. Both are worth watching
in the M3 mock deploy; the deploy itself will catch a formula the platform refuses to compile.

## 4. The process ships `active` true, and what that costs

`<active>true</active>`, against `approval-processes/SKILL.md` Recommended Workflow step 4 ("keeping
`active` at `false` until the target org has the actions"). That override is decision **D9** and assumption
**A36**, grounded on the two places that state the Active requirement for a *named* submission:
`admin/approval-process-apex-patterns/references/metadata-examples.md:49-53` and that skill's
`templates/approval-process-apex-patterns-template.md:30`. M3-S03's Apex passes the bare developer name
`Discount_Approval` to `setProcessDefinitionNameOrId`, which is exactly the named submission both lines
describe, and every workflow action and email template it references ships in this same build — so the
split-deploy condition the deploy-inactive guidance waits for is met at deploy time.

Three consequences, all of them the human's:

1. **Approval process ORDER is not in the metadata and must be set by hand in Setup after deploy.** The guide
   is quoted in `references/gotchas.md`: "The metadata doesn't include the order of active approval
   processes. Sometimes you have to reorder the approval processes in the destination org after
   deployment." Setup → Process Automation → Approval Processes, filtered to Opportunity. This is assumption
   **A34**, and it is the one post-deploy action this step cannot perform or verify.
2. **Order affects only the standard Submit for Approval button.** M3-S03's Apex names the process
   explicitly, so its submissions cannot be silently rerouted no matter what else sits on Opportunity. A
   record submitted through the standard button, by contrast, "evaluates entry criteria for all processes
   applicable to the submitter", in the org's order, and the first match wins. If Northwind's production org
   already carries an Opportunity approval process — no clarification on this build covers that, which is
   why A34 exists — a broader process sorted first will swallow submissions this one was written for.
3. **Activation freezes the step structure permanently.** "After an approval process is activated, you can't
   add, delete, or change the order of the steps or change its reject or skip behavior, even if the process
   is inactive." Deploying active is activating. The frozen set here is: one step, no `rejectBehavior`
   (not allowed on a first step), no `ifCriteriaNotMet`. Everything else — entry criteria, the approver,
   the actions, `allowRecall`, `recordEditability`, `approvalPageFields` — stays changeable.

`UNVERIFIED (2026-09-19):` **nothing in the cited skills states whether an `ApprovalProcess` deployed with
`active` true is validated more strictly than an inactive one** — for instance whether its approver or
submitter references must resolve at deploy rather than at submission. The skill documents the approver
failure as a *runtime* one (§ 5). If the M3 mock deploy rejects this component, flipping `<active>` to
`false` and activating by hand in Setup is the one-line fallback, and it costs only the Apex preflight D9
was written for.

## 5. The approver is a hierarchy field, and its failure mode is at run time

`<nextAutomatedApprover>` carries `<userHierarchyField>Manager</userHierarchyField>` and
`<useApproverFieldOfRecordOwner>true</useApproverFieldOfRecordOwner>`, so step 1 reads `Manager` on the
**record owner's** user record, not the submitter's. Q27 restricts submission to the owner, so the two are
the same person today; they stop being the same the moment an opportunity is reassigned or sales ops
submits through the bypass path Q27 names as exceptional.

The element is not optional decoration: "If you exclude this field, then no approval step can use a user
hierarchy field to automatically assign the approver." `check_approval_design.py` raises HIGH on that
combination and reported clean here.

**Every user who can own an Enterprise or Renewal opportunity needs `Manager` populated, or their
submission fails at run time.** `references/gotchas.md`, "Blank Approver Fields Fail at Runtime": "One record
has that field blank. Submission fails even though the process design itself looks valid." Nothing in this
metadata catches it, no deploy catches it, and the skill states plainly that "there is no built-in fallback".
Two populations to check in the target org before UAT:

- **The 12 reps.** Each needs `Manager` set to one of the two managers.
- **The 2 managers themselves.** With `useApproverFieldOfRecordOwner` true the field is read on the *owner*,
  so a manager-owned Enterprise deal above 20% routes to *that manager's* manager. If the two managers have
  no `Manager`, a deal they own cannot be submitted at all. No clarification on this build covers whether
  managers own deals; the requirement's "12 reps, 2 managers" does not say.

The skill's own remedy is a pre-submission validation rule or a fallback queue. This build has neither, and
adding one is a plan change, not this step's to make.

## 6. The interplay with M2-S03, stated once so nobody has to re-derive it

`admin/validation-rules` is cited on this step for one reason, and this is it. Its `references/gotchas.md`
("A Workflow Field Update Re-Saves the Record and Validation Rules Do Not Run Again") quotes the Apex
Developer Guide: when a workflow field update re-saves the record, "custom validation rules, flows,
duplicate rules, processes built with Process Builder, and escalation rules aren't run again."

All four field updates in this step are workflow field updates. Two things follow:

- **Good:** `Set_Approval_Status_Approved` cannot be blocked by
  `Opportunity_Discount_Requires_Approval`. The approval outcome always lands.
- **Watch:** the same exemption means the rule is not a database invariant against these updates. This step's
  `<entryCriteria>` carries **no `StageName` filter** — unlike the skill's worked example, whose process-level
  criteria exclude `Closed Won,Closed Lost` — so an already-Closed Won opportunity can be submitted, and a
  recall then fires `Clear_Approval_Status` (operation `Null`) and commits a Closed Won record above 20%
  discount with a blank Approval Status: exactly the state M2-S03 exists to prevent, reached without the rule
  running. The record is not corrupt and nothing silently breaks — the rule fires again on the *next* ordinary
  edit of that record, which is when the rep discovers it — but it is worth a line at the M3 gate. The entry
  criteria are `plan.json.steps[M3-S02].inputs.entry_criteria_formula` verbatim, so narrowing them is a
  planner decision (`amend-step`), not a builder one.

Q33's "recall clears the status" is delivered by `operation` `Null` rather than a literal, which is why a
recalled record shows a blank Approval Status rather than `Rejected`. Recall reverses nothing else: the
submit email has already been sent and the skill says so outright — "Recall is not rollback".

## 7. The sender, and the one silent failure this file could have had

Both alerts carry `<senderType>CurrentUser</senderType>` and no `<senderAddress>`. That is decision
**D-M3S01-01**, recorded from M3-S01's § 4: no verified `OrgWideEmailAddress` is known to exist in any
target org for this build, the sender question was never asked, and these are internal emails between a rep
and their own manager. `senderAddress` is illegal alongside `CurrentUser` — "You can only specify a value in
this field if the `senderType` is set to `OrgWideEmailAddress`" — so the pairing here is the one that needs
nothing provisioned.

`UNVERIFIED (2026-09-19):` **no verified org-wide address is known to exist for this build.** If Northwind
later wants a shared sales-ops sender, it is a *deploy prerequisite*, not metadata: the address must exist
and be verified in the target org first. `IsVerified` defaults to `false` and "is only cleared by clicking a
link mailed to the mailbox owner, which no deploy can do for you". The committed case-onboarding build hit
exactly this as finding F-28 — a real `--dry-run` rejected its component with `support-noreply@acme.example
is an invalid From email address`.

Both alerts carry a non-empty `<recipients><type>owner</type></recipients>`. This is worth stating because
the failure it avoids is invisible: "A `.workflow` file whose alert carries a `template`, a `description`
and a `senderType` but an empty recipient set deploys successfully, appears in Setup, is selectable from
Flow — and delivers nothing. There is no runtime error and no entry in the debug log to look for."
`owner` is also one of the two recipient types that need no companion `field` or `recipient` element, so
there is nothing further to populate. No checker in this build reads recipients; the step's fifth `manual`
acceptance test is what covers it.

## 8. How to read this step's checkers

| Declared test | Command | What its exit code stands for |
|---|---|---|
| `scope: build` | `check_approval_design.py --manifest-dir artefacts artefacts` | `Scanned 1 approval-process metadata file(s); 0 finding(s) detected.`, score 100, **exit 0, zero repair passes**. The exit code stands for: the process has a step; the step has an `assignedApprover`; `userHierarchyField` is paired with `nextAutomatedApprover`; `allowedSubmitters` and `entryCriteria` are both present on an active process; `recordEditability` is a valid enum value; `finalApprovalRecordLock` is not true alongside `AdminOnly`; all six `<action>` references resolve to a definition in `workflows/Opportunity.workflow-meta.xml`; `<emailTemplate>` resolves to one of M3-S01's three `*.email-meta.xml` files; and all four action blocks plus `recallActions` are populated. It is bare — any finding at any severity, REVIEW included, exits 1 — so a 0 is not resting on suppressed findings. |
| `scope: step` | `check_email_templates.py --manifest-dir artefacts/M3-S02` | **Exit 1, and the artefacts are not why.** See below. |

**The declared email-template checker scans nothing on this step, and exits 1 for saying so.** Run verbatim
from the build directory it printed:

```text
ERROR artefacts/M3-S02: no email template artefact found — expected `*.email`,
`*.email-meta.xml`, or a body file under an `email/` directory
Scanned 0 email template file(s); no files matched the provided paths.
```

That is correct behaviour, not a bug: `is_template_artefact()` matches `*.email`, `*.email-meta.xml`, and
body files under an `email/` directory, and this step writes none of those — the three templates and their
folder are M3-S01's outputs and writing copies here would duplicate manifest members. The test was added by
`amend-step --add-checker` on 2026-09-19 to clear a § 5 warning, and its own description anticipated a
correction ("if this checker takes a different form, correct the command with `amend-step --file`"); the
argument form is right and the *path* is what cannot work.

Two remedies, and the second is the one to take:

- Point it at the whole tree, `scope: "build"`. Measured: `check_email_templates.py --manifest-dir artefacts`
  prints `Scanned 6 email template file(s); 0 finding(s) detected.` and exits 0, under `--strict` as well. Be
  clear about what that buys: it re-lints M3-S01's six files, which M3-S01's own test already covers. This
  checker never opens a `.workflow` file, so it asserts nothing about this step's two alerts.
- Or drop the test and accept the § 5 warning, on the ground that `admin/email-templates-and-alerts` is cited
  here for the alert element shape rather than for template content.

**No checker in this build resolves an alert's `<template>`.** `check_approval_design.py` resolves the
*process's* `emailTemplate` only (`audit_file`, `text_of(root, "emailTemplate")`), and
`check_email_templates.py` never reads a `.workflow` file. The two strings in § 1's table are therefore
covered by the M3-S01 name contract, this note, and the first org deploy — nothing automated.

**One more § 5 warning stands on this step and should keep standing.** `build_plan.py next` advises
declaring `check_validation_rules.py` because `admin/validation-rules` is cited. It should not be declared:
this step writes no `ValidationRule`, so that checker would scan nothing and fail exactly as the email one
does. The skill is cited as context for § 6, which is a reading of another step's artefact.

For evidence rather than as a declared test, the approval checker was also run at step scope:
`check_approval_design.py --manifest-dir artefacts/M3-S02 artefacts/M3-S02` → score 100, **exit 1**, one
`REVIEW`: "emailTemplate 'Sales_Approvals/Discount_Approval_Request' could not be resolved because the tree
contains no `*.email-meta.xml` files". That is the cross-step reference showing through, and it is precisely
why the plan declares the test at build scope. Every other assertion in the file passed identically at both
scopes.

## 9. Repair after the first build

This step was built once (`2026-09-19T16:38:52Z`), set `blocked`, amended twice, and is being
rebuilt here. What changed and why:

1. **The email-templates checker test declared at step scope was withdrawn.**
   `check_email_templates.py --manifest-dir artefacts/M3-S02` asserted nothing about this step:
   `is_template_artefact()` matches `*.email`, `*.email-meta.xml`, and a body file under an
   `email/` directory, and this step's four declared outputs contain none of those, by design —
   the three templates and their folder are M3-S01's outputs (§ 1), and a copy here would
   duplicate manifest members. § 8 above already records the measured evidence: the same command
   pointed at `artefacts` (build scope) scans all six template files and exits 0. Withdrawing the
   step-scope test does not weaken coverage — nothing it could have asserted about *this* step's
   two alerts was ever inside its reach; `check_approval_design.py` resolves the alert names by
   exact string against `workflows/Opportunity.workflow-meta.xml`, and no checker in this build
   opens a `.workflow` file to read an alert's `<template>` (§ 8, last paragraph).

2. **`inputs.entry_criteria_formula` was narrowed to exclude `Closed Won` and `Closed Lost`.**
   § 6 above records the interplay this closes: a workflow field update re-saves the record
   without re-running custom validation rules — "custom validation rules, flows, duplicate rules,
   processes built with Process Builder, and escalation rules aren't run again"
   (`validation-rules/references/gotchas.md`, quoting the Apex Developer Guide). Before this
   repair, the entry criteria carried no `StageName` filter, so an already-Closed-Won or
   Closed-Lost opportunity could still be submitted; a **submit then recall** on that record fires
   `Clear_Approval_Status` (`operation` `Null`), which re-saves the record without re-running
   `Opportunity_Discount_Requires_Approval`. That commits a closed, above-20%-discount record with
   a blank Approval Status — exactly the state M2-S03 exists to prevent, reached without the rule
   running once. Wrapping the original three-clause formula in an outer `AND(...)` with
   `NOT(ISPICKVAL(StageName, "Closed Won"))` and `NOT(ISPICKVAL(StageName, "Closed Lost"))` closes
   the path at the only point this step owns: once an opportunity is Closed Won or Closed Lost it
   can no longer enter the process at all, so there is nothing left for a recall to re-save into
   that state. § 6's "Watch" bullet still describes the pre-repair design and is left as written —
   it is the record of why this repair was made, not the current behaviour; read it together with
   this section.

**The `UNVERIFIED (2026-09-19)` marker on `RecordType.DeveloperName` inside an entry-criteria
`<formula>` (§ 3) stands, unchanged.** It was never about `StageName` or about how many clauses
the `AND(...)` carries — it is about whether `formula` is a legal `entryCriteria` child at all
(every fenced example in the library uses `criteriaItems` instead) and, if it is, whether
`RecordType.DeveloperName` resolves inside it. Adding two more `NOT(ISPICKVAL(StageName, "..."))`
clauses does not touch that question; only the M3 mock deploy can. `ISPICKVAL` against
`StageName` is otherwise a well-worn pattern in this build — M2-S03's own validation rule uses it
— so the two new clauses are not a *second* open question of their own; the existing marker
already covers the whole formula, including the clauses just added.

## 10. What to check after deploy, in the org

- **Set the process order** (§ 4). Setup → Process Automation → Approval Processes, filtered to Opportunity.
- **Confirm `Manager` is populated** on all 12 reps and, if managers own deals, on both managers (§ 5).
- **Submit one record as a real rep, not as System Administrator**, then run the `ProcessInstance` /
  `ProcessInstanceWorkitem` queries in `approval-processes/references/metadata-examples.md` to confirm which
  process was entered and who holds the work item. `ProcessDefinition.State` should read `Active`.
- **Watch the emails**: one on submit (from the process's `emailTemplate`, to the manager), one on the
  outcome (to the owner). Two on submit means an `initialSubmissionActions` alert crept in.
- **Check the record lock as a rep and as the manager.** `recordEditability` is `AdminOnly`, so the manager
  approves or rejects but cannot edit; only Modify All Data / Modify All Records can. Both final-lock
  booleans are `false`, so the record unlocks on either outcome.
- **Recall one pending request** and confirm Approval Status goes blank, not `Rejected`.
- **Read the rejection email as a rep** and confirm the Approval History related list is actually on the
  Opportunity page it points at. `<showApprovalHistory>true</showApprovalHistory>` is set, which is the close
  condition on observation **O-M3S01-01**; the related list still has to be on the layout, and page layouts
  are M1-S02's.

## 11. Validate-only command for a human

`agents/metadata-builder` never runs this. It is text to copy.

`scripts/mock_deploy.py` assembles the selected steps' artefacts and hands them to `sf project deploy start
--dry-run` (`checkOnly: true`). The `--dry-run` is hard-coded inside the script — there is no flag that turns
it off, no deploy option, and nothing about the dry run is the operator's to pass or to forget.

This step cannot be validated alone: its alerts and its `<emailTemplate>` reference three templates that
must exist in the target org, and an org that has only ever received `--dry-run` runs holds none of them.
Validate M3 as a whole:

```bash
python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json \
  --org-alias <your-sandbox-alias> \
  --milestone M3 \
  --mode manifest
```

Against an org that has never received M1, add M1's fields and record types too — nothing this build
validated before is actually in that org, because a `--dry-run` saves nothing. Results land under
`reports/mock-deploy/<UTC timestamp>/`.

What that run can tell you: whether the entry-criteria formula compiles, whether `RecordType.DeveloperName`
is legal in an approval formula, whether `<formula>` is accepted in place of `criteriaItems`, whether the six
workflow-action references resolve, whether a restricted picklist accepts each `<literalValue>`, whether
`operation` `Null` is legal on that field, and whether an `active` process is accepted at deploy (§ 4). What
it cannot tell you: anything about `User.Manager` being populated (§ 5), anything about which process a
record enters (§ 4, order is not in the metadata), and whether either email actually arrives.

For a production target the sequence is different: `sf project deploy validate` returning a job id, then
`sf project deploy quick`, per `change-management-and-deployment/references/metadata-examples.md` § 3, which
carries its own `UNVERIFIED (2026-09-04)` caveat on `sf` CLI flag spellings — if a flag is rejected, run
`sf project deploy validate --help` rather than guessing a synonym.
