# Deploy order — M3-S01

Build: `northwind-sales` · Milestone: M3 (The discount approval and the rep's panel) · Step type: `ui` · API version 62.0

This note is written by `agents/metadata-builder` Step 7 and is text for a human. Nothing in it is
executed by this agent or by any acceptance test.

Sourced from `skills/admin/email-templates-and-alerts/references/metadata-and-sender-identity.md`
("Where the files live", "Folder", "Classic text template used by an auto-response rule", "Org-wide
email address (the sender)", "package.xml and CLI"),
`skills/admin/email-templates-and-alerts/references/gotchas.md` (the `uiType`/`type`/`style`/`letterhead`
coupling table, "`senderAddress` Is Only Legal When `senderType` Is `OrgWideEmailAddress`", "An Alert
With No `recipients` And No `ccEmails` Deploys Clean And Never Sends", "Classic And Lightning Templates
Live In Different Folder Types, In Different Directories", "Delete The Alert Before The Template, Never
The Other Way Round"), `skills/admin/email-templates-and-alerts/SKILL.md` ("Questions to Ask Before
Configuring", "Recommended Workflow" steps 2–4 and 6),
`skills/admin/approval-processes/references/metadata-examples.md` ("Where the files live", the worked
two-step Opportunity discount approval, "The workflow actions the process references", "package.xml",
"Retrieve, lint, deploy"), `skills/admin/approval-processes/SKILL.md` ("Questions to Ask Before
Configuring" row 7, "Deployable Metadata Shape"),
`skills/admin/change-management-and-deployment/references/metadata-examples.md` § 1, and the
org-validated artefacts under `examples/builds/case-onboarding/artefacts/M3-S02/email/`.

## 0. Why API version 62.0

`plan.json` carries no `api_version` key, so `agents/metadata-builder/AGENT.md` ("Inputs") falls back to
`62.0`. Every step already built in this build declares the same number — all seven `package.xml` files
under `artefacts/` carry `<version>62.0</version>` — so `scripts/mock_deploy.py`'s highest-version scan
across the selected steps still sees one version for the whole build rather than a step that silently
raises it.

Two of the cited sources disagree about the current number and neither changes the decision:
`email-templates-and-alerts/references/metadata-and-sender-identity.md` and
`approval-processes/references/metadata-examples.md` both show `62.0` in their own `package.xml` fences,
while `change-management-and-deployment/references/metadata-examples.md` § 1 quotes the guide's
"Currently the valid value is 66.0" and shows `66.0`. Nothing in this step has a version floor above
62.0: `EmailFolder` and `EmailTemplate` are both long-standing types, and none of the eight elements
written here carries a version note in any cited reference. Raising the whole build's API version is a
plan-level decision, not this step's — it is the same open item M1-S02 and M2-S05 recorded.

## 1. The names M3-S02 must copy, not retype

**This table is the contract.** M3-S02 builds the `ApprovalProcess` and the `Workflow` file, and both
reference what this step wrote **by exact string**. `check_approval_design.py` at the M3 milestone's
build scope resolves `emailTemplate` by walking `*.email-meta.xml` and reconstructing
`<parent directory name>/<file stem>` (`skills/admin/approval-processes/scripts/check_approval_design.py`,
`load_email_templates`), so the directory name and the file stem — not the `<name>` label inside the XML
— are what has to match. Copy the middle column character for character.

| What M3-S02 writes | The exact string it must carry | Where that string comes from |
|---|---|---|
| `ApprovalProcess` → `<emailTemplate>` | `Sales_Approvals/Discount_Approval_Request` | `email/Sales_Approvals/Discount_Approval_Request.email-meta.xml` |
| `Workflow` → `<alerts><fullName>Notify_Submitter_Approved</fullName>` → `<template>` | `Sales_Approvals/Discount_Approved` | `email/Sales_Approvals/Discount_Approved.email-meta.xml` |
| `Workflow` → `<alerts><fullName>Notify_Submitter_Rejected</fullName>` → `<template>` | `Sales_Approvals/Discount_Rejected` | `email/Sales_Approvals/Discount_Rejected.email-meta.xml` |
| The milestone `package.xml` (M4-S04 aggregates it) | `EmailFolder` member `Sales_Approvals`; `EmailTemplate` members as above, all three listed | `artefacts/M3-S01/package.xml` |

Two spellings that are easy to get wrong and are **not** interchangeable:

- The folder's **developer name** is `Sales_Approvals`, with the underscore. That is the file stem
  (`Sales_Approvals.emailFolder-meta.xml`), the `package.xml` member, and the first half of every
  template reference. The folder's **label** is `Sales Approvals`, with a space, and it lives only in the
  `<name>` element inside the folder file. The org-validated pair in
  `examples/builds/case-onboarding/artefacts/M3-S02/email/case_intake.emailFolder-meta.xml` is the same
  shape: file stem `case_intake`, `<name>Case Intake</name>`, manifest member `case_intake`.
- The two alert `fullName` values above (`Notify_Submitter_Approved`, `Notify_Submitter_Rejected`) are
  **not** this step's to own — they are named here because M3-S02 must make its `<alerts><fullName>` and
  the approval process's `<action><name>` agree with each other, and because they are the names the
  worked example in `approval-processes/references/metadata-examples.md` uses for exactly these two
  alerts. If M3-S02 picks different alert names, the three template strings in the middle column still
  stand unchanged.

**There is no fourth template and no alert for the approval request.** Q33's answer lists four events;
only three of them send mail. Submit is sent by the approval process itself through its `<emailTemplate>`
element — "Omit the element to use the default approval-request template"
(`approval-processes/references/metadata-examples.md`, "How to read it"), so naming it there is what
replaces the platform default, and **no `WorkflowAlert` is involved**. Recall sends nothing at all.
M3-S02 should not create an alert for the submit event; doing so would send the manager two emails.

## 2. Order inside this step

| # | Component | Because |
|---|---|---|
| 1 | `EmailFolder:Sales_Approvals` | The folder is the container. "A template in a private folder is invisible to the rule engine for other users; keep rule templates in a public folder" (`metadata-and-sender-identity.md`, "Folder"), and `EmailTemplate` members are addressed as `Folder/Developer_Name` — there is no address for a template whose folder does not exist. |
| 2 | `EmailTemplate:Sales_Approvals/Discount_Approval_Request` | Order among the three templates is free; none references another. |
| 3 | `EmailTemplate:Sales_Approvals/Discount_Approved` | Same. |
| 4 | `EmailTemplate:Sales_Approvals/Discount_Rejected` | Same. |

The single `package.xml` in this directory covers all four, so one manifest deploy satisfies the
ordering by itself. A split-source deploy is `sf project deploy start --source-dir <…>/email`, which
carries the folder file and the folder directory together.

**On the way back out, the order reverses and it matters more.** `WorkflowAlert.template` is validated
against the *target org*, not against the deployment payload: "This email template isn't required to
exist in the zip file, but it must exist in Metadata API" (`email-templates-and-alerts/references/gotchas.md`,
"Delete The Alert Before The Template"). Removing one of these templates while M3-S02's alert or the
approval process still points at it fails validation. Retirement is two deployments — alerts and the
approval process's `emailTemplate` first, then the templates, and the folder last.

## 3. Dependencies on components outside this step

| This step names | Which must already exist as | Built by |
|---|---|---|
| `{!Opportunity.Discount__c}` | `CustomField` `Opportunity.Discount__c` (Percent, precision 5, scale 2) | M1-S01 (`objects/Opportunity/fields/Discount__c.field-meta.xml`) |
| `{!Opportunity.Approval_Status__c}` | `CustomField` `Opportunity.Approval_Status__c` (restricted picklist: Pending, Approved, Rejected) | M1-S01 (`objects/Opportunity/fields/Approval_Status__c.field-meta.xml`) |
| `{!Opportunity.Name}`, `{!Opportunity.Amount}`, `{!Opportunity.StageName}`, `{!Opportunity.CloseDate}` | standard Opportunity fields | the platform |

`depends_on` for this step is `["M1-S01"]` and that is the whole of it. Nothing here references a record
type, a business process, a permission set, a path or a layout, so M1-S02 and every M2 step may deploy
before or after in any order.

Three consequences the deploy will not spell out:

- **A merge field that does not resolve is not a deploy error.** "Merge fields resolve only for the
  record the rule fires on and its parents" (`metadata-and-sender-identity.md`); the matching gotcha's
  worked failure is a template expecting `{!Opportunity.Account.Name}` sent from a context that does not
  supply Opportunity, which "arrives with blanks or broken copy". All six merge fields above are on the
  Opportunity itself — no parent traversal — and every one of the three templates is sent from an
  Opportunity approval context, so the context question is closed for this step. It reopens the moment
  anyone adds a `{!Opportunity.<Parent>.<Field>}` field to one of these bodies.
- **Field-level security is not granted here and is not this step's to grant.** A rep who cannot read
  `Discount__c` gets a blank in the email, not an error. Those grants are M2-S01 and M2-S02's.
- **The bodies do not repeat the `%` sign after `{!Opportunity.Discount__c}`.** The field's `<type>` is
  `Percent` with `precision` 5 and `scale` 2 (M1-S01's field file). `UNVERIFIED (2026-09-19):` **no cited
  reference states how a `Percent` field renders inside a Classic email template merge**, so whether the
  merged value arrives as `25.00%` or as `25.00` is a question for the first real send, not something
  established here. Leaving the sign off is the choice that cannot produce `25.00%%`; if the send shows a
  bare number, adding one `%` to each of the three bodies is the whole fix.

## 4. The sender decision, recorded explicitly

**The three files in this step carry no sender, and that is correct rather than an omission.** The
`EmailTemplate` element set in `metadata-and-sender-identity.md` has eight elements — `available`,
`description`, `encodingKey`, `name`, `style`, `subject`, `type`, `uiType` — and none of them is a
sender. The same reference says why: "There is no metadata type for org-wide addresses; they are created
in Setup → Organization-Wide Addresses and must be verified from the mailbox." The From address is set on
the *consumer*, and for two of these three templates the consumer is M3-S02's `WorkflowAlert`
(`senderType`, and `senderAddress` only when `senderType` is `OrgWideEmailAddress`).

**No sender was decided for this build, and no org-wide address is on file.** Searching the answered
clarifications, `requirement.md` and `decisions.md` for `org-wide` / `sender` / `from address` /
`no-reply` / `reply-to` returns one unrelated hit (Q48, a Path expand preference) and one unrelated
phrase in `decisions.md` ("org-wide default", about OWD sharing). The sender question is one the cited
skill says must be asked — `email-templates-and-alerts/SKILL.md`, "Who does the email come from, and who
answers replies?" — and it was never asked on this build.

`UNVERIFIED (2026-09-19):` **no verified `OrgWideEmailAddress` is known to exist in any target org for
this build.** Nothing in this step depends on one, so the step is not blocked. Two things do depend on
it, and both belong to whoever signs the M3 gate:

1. **M3-S02 must choose a `senderType` for each of the two alerts.** The worked example in
   `approval-processes/references/metadata-examples.md` deliberately shows both shapes —
   `Notify_Submitter_Approved` uses `<senderType>CurrentUser</senderType>` with no address, and
   `Notify_Submitter_Rejected` uses `<senderType>OrgWideEmailAddress</senderType>` with
   `<senderAddress>sales-ops@acme.example</senderAddress>`. **The default recommendation from this step
   is `CurrentUser` on both**, because it needs nothing provisioned and these are internal emails between
   a rep and their own manager. `senderAddress` is illegal alongside it: "You can only specify a value in
   this field if the `senderType` is set to `OrgWideEmailAddress`" (`gotchas.md`).
2. **If the answer is instead a shared sales-ops mailbox, it is a deploy prerequisite, not metadata.**
   The address must exist and be verified in the *target* org before the alert deploys; `IsVerified`
   defaults to `false` and "is only cleared by clicking a link mailed to the mailbox owner, which no
   deploy can do for you". This is the failure the committed case-onboarding build hit as finding
   **F-28** — a real `--dry-run` rejected its component with `support-noreply@acme.example is an invalid
   From email address`, and it was carried as a G3 deploy prerequisite rather than rebuilt
   (`examples/builds/case-onboarding/decisions.md` **D-M3S04-03**). The same trap applies here, one step
   later in the chain.

**One related caveat on the merged status line.** `Discount_Approved.email` and
`Discount_Rejected.email` each carry `Approval status now on the record:
{!Opportunity.Approval_Status__c}`. Q33 puts the field update and the email in the same approval event,
which in M3-S02 means a `FieldUpdate` and an `Alert` sitting in the same `finalApprovalActions` /
`finalRejectionActions` block. `UNVERIFIED (2026-09-19):` **nothing in the cited skills establishes
whether the field update inside an approval action block runs before the alert in the same block.** The
only ordering rule either skill states is about steps, not actions: "Document order **is** execution
order. Up to 30 steps per process" (`approval-processes/SKILL.md`, `approvalStep[]` row). The line is
worded as an observation of the record rather than as an assertion of the outcome, so a stale merge reads
as merely redundant rather than as a contradiction of the subject line — but the fact it reports is worth
one look during the M3 mock deploy or UAT, and if it does read stale the fix is to delete that one line
from both bodies, not to re-order anything.

## 5. Assumption A27, and what it actually rests on

`Discount_Rejected.email` points the rep at the Approval History related list instead of quoting the
manager's comments, which is assumption **A27** and the reason the approval row's fit-gap verdict is
partial. The assumption's own wording is that "no `{!ApprovalRequest.*}` merge field is documented
anywhere in this library". That is very nearly true and worth stating precisely, because a future reader
who greps will find two hits:

- `skills/admin/quote-to-cash-process/references/gotchas.md:49` mentions `{!ApprovalRequest.ApproverName}`
  in passing, as an example of something CPQ Advanced Approvals cannot see.
- `skills/flow/pause-elements-and-wait-events/SKILL.md:117–118` uses `{!ApprovalRequest.CreatedDate}`,
  but as a **Flow resource** inside a pause configuration, not as an email merge field.

Neither documents a merge field for the approval **comments**, neither appears in a fenced email-template
example, and neither is in a skill this step cites. So A27's conclusion stands exactly as recorded — the
comments are not writable into this body from anything this library grounds — while its stated premise is
one word too absolute. The mechanism that delivers the comments instead is `showApprovalHistory`, which
M3-S02 sets to `true` on the approval process (`approval-processes/references/metadata-examples.md`, last
element of the worked process). **If M3-S02 omits or falses that element, this email points at a related
list the rep cannot see**, and A27 stops being a documented gap and becomes a broken promise.

## 6. How to read this step's checker

One checker is declared, and it asserted something real.

| Declared test | Command | What its exit code stands for |
|---|---|---|
| step scope | `check_email_templates.py --manifest-dir artefacts/M3-S01` | `Scanned 6 email template file(s); 0 finding(s) detected.`, score 100, exit 0, zero repair passes. Six files, not seven: `Sales_Approvals.emailFolder-meta.xml` is not a template artefact by the checker's own test (`is_template_artefact`), so the folder is unlinted here — the `manifest` acceptance test and section 1 above are what cover it. What the exit code stands for: every one of the three bodies contains at least one `{!` merge field, all three `-meta.xml` files parse and carry a non-empty `<subject>`, and no file in the step carries a hardcoded email address. It exits 0 under `--strict` as well, which was confirmed rather than assumed — so the 0 is not resting on suppressed REVIEW findings. |

What that checker does **not** assert, and what covers each gap instead:

- It does not check the `uiType` / `type` / `style` / `letterhead` coupling. The step's fifth acceptance
  test is a `manual` tick for exactly that, and all three files carry `uiType` `Aloha`, `type` `text`,
  `style` `none`, no `letterhead`, `available` `true` and `encodingKey` `UTF-8` — row 1 of the
  two-shapes-only table in `gotchas.md`.
- It does not check the 230-character Classic subject ceiling. Measured here: 75, 38 and 74 characters.
- It does not resolve a merge field against the object. Section 3's table is the manual trace.
- It does not see the approval process at all. That cross-reference is the M3 milestone's first
  acceptance test (`check_approval_design.py --manifest-dir artefacts artefacts`), which runs only once
  M3-S02 exists.

## 7. What to check after deploy, in the org

- **The folder is public and read-only.** Setup → Classic Email Templates. A template in a private folder
  is invisible to the rule engine for other users (`metadata-and-sender-identity.md`, "Folder"); the
  approval engine has the same problem.
- **The templates are Classic, not Lightning.** `EmailTemplate.UiType` should read `Aloha` on all three.
  A Lightning template cannot be referenced by an approval process at all — "Lightning email templates
  aren't packageable. We recommend using a Classic email template."
- **Send one of each against a record whose optional fields are empty**, per
  `email-templates-and-alerts/SKILL.md` Recommended Workflow step 6: one email, not two; the expected From
  address; every merge field resolved. The From address is the one to watch — see section 4.
- **Read the rejection email as a rep, not as an admin**, and confirm the Approval History related list is
  actually on the page it points at.

## 8. Validate-only command for a human

`agents/metadata-builder` never runs this. It is text to copy.

`scripts/mock_deploy.py` assembles the selected steps' artefacts and hands them to
`sf project deploy start --dry-run` (`checkOnly: true`). The `--dry-run` is hard-coded inside the script —
there is no flag that turns it off and no deploy option — so nothing about the dry run is the operator's
to pass or to forget.

This step is self-contained against an org that already holds M1-S01's two fields, so it can be validated
on its own:

```bash
python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json \
  --org-alias <your-sandbox-alias> \
  --step M3-S01 \
  --mode manifest
```

Against an org that has never received M1, add `--milestone M1` so the two custom fields travel with it —
a `--dry-run` never saved M1's earlier runs, so nothing this build validated before is actually in that
org. `--mode manifest` matches how the earlier steps were validated. Results land under
`reports/mock-deploy/<UTC timestamp>/`.

What that run can and cannot tell you: it can catch a malformed folder or template file, a member form the
platform rejects, and a `type`/`uiType`/`style` combination the platform refuses. It **cannot** tell you
that a merge field resolves — an unresolvable merge field is valid metadata that renders a blank — and it
cannot tell you anything about the sender, because no sender is in these files (section 4). The whole of
M3 is worth validating together once M3-S02 exists, because that is the first run in which the approval
process's `emailTemplate` reference is checked against a real org.

For a production target the sequence is different: `sf project deploy validate` returning a job id, then
`sf project deploy quick`, per `change-management-and-deployment/references/metadata-examples.md` § 3,
which carries its own `UNVERIFIED (2026-09-04)` caveat on `sf` CLI flag spellings — if a flag is rejected,
run `sf project deploy validate --help` rather than guessing a synonym.
