# Deploy order — M3-S02 (Classic case-intake email templates)

Built by `agents/metadata-builder` under `agents/build-step-runner`. Nothing here was
deployed, and no `sf` command below was run by an agent.

`api_version` is `62.0`. `plan.json` carries no `api_version`, so the agent default in
`agents/metadata-builder/AGENT.md` (Inputs) applies; 62.0 is also what the other seven
`artefacts/*/package.xml` in this build already carry and what the cited reference's own
worked manifest uses (`skills/admin/email-templates-and-alerts/references/metadata-and-sender-identity.md:95`).

## Order inside this step

| # | Component | Type | Why it must come at this point |
|---|---|---|---|
| 1 | `case_intake` | `EmailFolder` | A template's `fullName` is folder-qualified — `Folder/Developer_Name` (`metadata-and-sender-identity.md:10`, `:12`) — so the folder is the name-space the other two components live in. The folder file sits *alongside* the folder directory, not inside it (`:9`) |
| 2 | `case_intake/Case_Acknowledgement` | `EmailTemplate` | Body `.email` + `.email-meta.xml` are one component in two files (`:10`, worked pair at `:29`–`:56`). Both files must be in the same request; neither half deploys alone |
| 3 | `case_intake/Case_Escalated_To_Tier2` | `EmailTemplate` | Same shape. Order between components 2 and 3 is free — neither references the other |

**All three ship in one request.** The cited reference's own `package.xml`
(`metadata-and-sender-identity.md:83`–`:97`) lists `EmailFolder` and two `EmailTemplate`
members in a single manifest, which is the form `package.xml` in this directory copies. No
two-deployment split is needed on the additive path.

**The inversion above is an inference, and is marked as one.** Neither cited skill states
intra-request ordering for `EmailFolder` versus `EmailTemplate`. What the skill states
explicitly is the *deletion* order — "The same ordering applies to the folder: the folder
goes last" (`email-templates-and-alerts/references/gotchas.md:183`) — and the additive
order in the table is that same dependency read in reverse. Treat it as the safe sequence
if the single request is ever split, not as a quoted rule.

`sender-identity-note.md` and this note are documentation, not metadata. They are not in
`package.xml` and nothing deploys them.

## `package.xml` member forms, and which of them are grounded

| Element | Value written | Grounding |
|---|---|---|
| `EmailFolder` member | `case_intake` | `metadata-and-sender-identity.md:88` — the worked manifest's member is the bare folder name (`Support_Templates`) |
| `EmailTemplate` members | `case_intake/Case_Acknowledgement`, `case_intake/Case_Escalated_To_Tier2` | `:91`–`:93` (`Support_Templates/Case_Web_Acknowledgement`), and `:10` / `:12` for the `Folder/Developer_Name` rule |
| No `*` wildcard on `EmailTemplate` | members enumerated | `:10` ("no `*` wildcard; list `Folder/Developer_Name` explicitly") and `gotchas.md:151` ("neither folders nor email templates support the `*` wildcard") |
| No trailing slash on the folder member | `case_intake`, not `case_intake/` | `gotchas.md:147`, `:153`–`:158` require the trailing slash for a **nested** folder member only. `case_intake` is flat, so the bare form is the reference's own form at `:88` |
| `<version>` | `62.0` | see header |

**File stem carries the `fullName`; `<name>` is the label.** `case_intake.emailFolder-meta.xml`
makes the folder's `fullName` `case_intake`, which is the string `package.xml` and every
template path use; `<name>Case Intake</name>` inside the file is the display label. The
naming rule is quoted at `:9` — "`FolderName.folderType-meta.xml`".

**Not grounded: the 255-character `<description>` ceiling.** Neither cited skill states any
`description` limit for `EmailTemplate` or `EmailFolder`. The ceiling is carried from this
build's own mock-deploy finding F-15 (`admin` access metadata, a different type), not from a
cited reference. It is recorded here rather than asserted as Salesforce behaviour. Nothing in
this step hangs on it: the two descriptions are 163 and 182 characters.

**Grounded ceilings that do apply.** The Classic subject limit is 230 characters
(`metadata-and-sender-identity.md:60`); the two subjects are 67 and 62. `type`/`uiType`/`style`/`letterhead`
are written as the one row of `gotchas.md:136` that a rule-driven template may use —
`Aloha` / `text` / `none` / `letterhead` omitted / `encodingKey` present.

## Dependencies on components OUTSIDE this step

### Must be in place before this manifest lands

| # | Dependency | Step / owner | What breaks without it |
|---|---|---|---|
| 1 | Nothing in Salesforce metadata | — | This manifest is self-contained. The folder and both templates reference no queue, user, calendar, field or class. It deploys into an empty org |
| 2 | The org-wide addresses `support@acme.example` and `billing@acme.example`, verified | IT / CRM admin lead, in Setup — **no metadata type** (`metadata-and-sender-identity.md:66`) | Nothing at deploy time: **no artefact of this step sets a sender**, because `EmailTemplate` has no sender element (element set at `:44`–`:55`). They are needed before the first *send*, and `IsVerified` defaults to `false` (`:74`; `gotchas.md:96`). Full record in `sender-identity-note.md` § 1 |

### Needed at send time, not at deploy time

The merge fields resolve against the record the consuming rule fires on
(`metadata-and-sender-identity.md:61`), and a field that is missing or blank renders blank
rather than failing anything (`gotchas.md:21`–`:34`). So these are send-time dependencies:

| Merge field | Where it comes from |
|---|---|
| `{!Case.Subject}`, `{!Case.CaseNumber}`, `{!Case.Priority}` | standard `Case` fields |
| `{!Case.Origin}` | standard field, but its **values** (`Email`, `Web`, `Phone`) are defined by `artefacts/M1-S01/standardValueSets/CaseOrigin.standardValueSet-meta.xml` — this step's `depends_on: ["M1-S01"]` |
| `{!Case.Thread_Id}` in the acknowledgement subject | the Email-to-Case thread token, written in exactly the form the reference's own worked subject uses (`:52`), kept per Q64 |

### Downstream consumers of these two templates

| Consumer | Element that names this step's output | Grounding for "templates first, rules second" |
|---|---|---|
| **M3-S04** — `autoResponseRules/Case.autoResponseRules-meta.xml` | `<template>case_intake/Case_Acknowledgement</template>`, plus the `senderEmail` / `senderName` / `replyToEmail` this step only *records* | `admin/assignment-rules/references/metadata-examples.md:88` ("`template` is `Folder/Developer_Name`"), `:221` ("Every template, queue, and business-hours name must already exist in the target org"), `:253` ("Deploy queues and templates first … then the rules") |
| **M4-S04** — `escalationRules/Case.escalationRules-meta.xml` | `<assignedToTemplate>case_intake/Case_Escalated_To_Tier2</assignedToTemplate>` on the 480-minute reassigning action | `admin/escalation-rules/references/metadata-examples.md:231` ("then queues and Classic email templates, then the escalation rules that name them") and `:153` ("Every queue, user, calendar, and template named here must already exist in the target org, or the deploy fails on the reference, not on the rule") |

### The stale folder prefix both consumer skills will hand you

This is the one line in this note most likely to prevent a failed deploy downstream.

Both consumer skills' worked examples file these templates in the shared unfiled folder,
because those examples were written without this build's folder:

- `skills/admin/escalation-rules/references/metadata-examples.md:95` writes
  `<assignedToTemplate>unfiled$public/Case_Escalated_To_Tier2</assignedToTemplate>` — the
  **same developer name** this step builds, under a different folder.
- `skills/admin/assignment-rules/references/metadata-examples.md:148` and `:159` write
  `<template>unfiled$public/Case_Web_Acknowledgement</template>` on the two auto-response
  entries.

This build files both templates in `case_intake`, so the consumers must write:

| Consumer | Correct reference | Not |
|---|---|---|
| M4-S04 | `case_intake/Case_Escalated_To_Tier2` | `unfiled$public/Case_Escalated_To_Tier2` |
| M3-S04 | `case_intake/Case_Acknowledgement` | `unfiled$public/Case_Web_Acknowledgement` |

Grounded at `metadata-and-sender-identity.md:12`: "Rules reference the template as
`Support_Templates/Case_Web_Acknowledgement`. Templates in the shared unfiled folder are
referenced as `unfiled$public/<Developer_Name>`." The `unfiled$public` prefix is correct only
for a template that actually sits in the shared unfiled folder; neither of these does. Copying
the skill's example literally produces a reference that resolves to nothing, and per
`escalation-rules:153` the deploy then fails on the reference rather than on the rule.

Note also that M3-S04's own developer name differs from the skill example's: this build
builds `Case_Acknowledgement` (one template for both channels, per Q28/Q60), not the
example's channel-split `Case_Web_Acknowledgement` / `Case_Email_Acknowledgement` pair.

### One consumer this step does NOT have

`M3-S03` declares `depends_on: [… "M3-S02" …]`, but none of its declared outputs references a
template of this step. The element that looks as though it should is `webToCase.defaultResponseTemplate`
in `settings/Case.settings-meta.xml`, and `skills/admin/case-management-setup/references/metadata-examples.md:407`–`:412`
is explicit that it is **not** the acknowledgement email: the guide scopes it to "email
responses to cases that are submitted through a Self-Service portal", a feature unavailable to
new orgs since Spring '12, and the customer acknowledgement is an `AutoResponseRules` entry
instead. Do not wire `case_intake/Case_Acknowledgement` into that element.

### If these ever come out again

Two deployments, in this order, per `gotchas.md:177`–`:185`: first remove or re-point the
auto-response entry (M3-S04) and the escalation action's `assignedToTemplate` (M4-S04); then,
in a second deployment, delete the templates; the folder goes last. The reason is that a
template reference "isn't required to exist in the zip file, but it must exist in Metadata
API" — it is validated against the target org, not against the payload.

## Elements and constraints this step could NOT ground

Recorded rather than invented, per `standards/build-orchestration.md` § 8.

1. **The 255-character `<description>` ceiling** — see above. Not in either cited skill;
   carried from this build's mock-deploy record. Both values are well under it.
2. **Intra-request ordering between `EmailFolder` and `EmailTemplate`** — see above. Inferred
   by inverting the documented deletion order.
3. **No `WorkflowAlert`, and no `workflows/Case.workflow-meta.xml` in this step.** The step's
   `outputs[]` declares neither, and Q63's recorded answer rules out "a parallel Flow email
   alert on the same event". `gotchas.md:68`–`:110` documents `WorkflowAlert` at length —
   including that `senderAddress` is legal only with `senderType` `OrgWideEmailAddress` — and
   that is precisely the type that would have carried a sender for these templates. Nothing in
   this build consumes an alert, so none was written. If a future step needs one, that gotcha is
   where the sender element actually lives.
4. **Whether `support@acme.example` is itself the Email-to-Case routing address.** `plan.json`
   Q22 and `answers-key.md`'s "Acknowledgement" row read this differently, and the cited skills'
   prohibition (`metadata-and-sender-identity.md:78`) bites under one reading and not the other.
   Recorded in full in `sender-identity-note.md` § 2 and left to a human. No element of this step
   turns on it, because `EmailTemplate` has no sender element; the element that does is M3-S04's
   `senderEmail`.

## Validate-only command for a human to run

Never run by an agent in this loop — `agents/metadata-builder/AGENT.md` Step 7 and the
`REFUSAL_SECURITY_GUARD` rule. Copy the artefacts into a DX source tree first; the path below
is relative to that tree, not to this build directory. This manifest has no prerequisite
deploy, so it may go on its own, ahead of M3-S03, M3-S04 and M4-S04.

```bash
sf project deploy start \
    --manifest manifest/package.xml \
    --dry-run \
    --target-org <your-sandbox-alias>
```

`--dry-run` on `deploy start` is the sandbox form. `sf project deploy validate` is the
production form — it requires Apex tests and returns a job id for a later
`sf project deploy quick` (`admin/change-management-and-deployment/references/metadata-examples.md:124`–`:155`).

After a green dry run, four things a human checks that no exit code covers:

1. Setup → Email Templates shows the **Case Intake** folder as Public / Read Only, and both
   templates inside it (`metadata-and-sender-identity.md:25` — a template in a private folder is
   invisible to the rule engine that sends it).
2. The org-wide addresses exist and are verified, before any send:

   ```sql
   SELECT Id, Address, DisplayName, Purpose, IsAllowAllProfiles, IsVerified
   FROM OrgWideEmailAddress
   WHERE Address IN ('support@acme.example', 'billing@acme.example')
   ```

   Requires View Setup and Configuration (`:77`).
3. Sandbox deliverability, which is system-only after a refresh and must be raised before the
   send is testable at all (`:79`; Q78 also commits to scrubbing Contact emails first).
4. Both consumers use the `case_intake/` prefix, not `unfiled$public/` — the section above.
