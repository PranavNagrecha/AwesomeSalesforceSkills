# Worked Example — One Release, Fully Planned

One release worked end to end: **moving 84 sales reps off a Classic-style Opportunity page layout onto a Lightning record page with Path and Dynamic Forms.** Every artefact below is filled in, not templated, so it can be copied and edited.

The technical deployment of these components is *not* this skill's job — see `admin/change-management-and-deployment` for promotion mechanics and `devops/release-management` for the train. This file covers the people side: who is affected, what they are told, how they are trained, and how you know it landed.

---

## 1. The ship list — what actually deploys, and who owns each piece

| Piece | Metadata type | Owning skill |
|---|---|---|
| Lightning record page `Opportunity_Rep_Page` | `FlexiPage` | `admin/lightning-record-page-configuration` |
| Page assignment (app + record type + profile + form factor) | `CustomApplication.profileActionOverrides` | `admin/lightning-record-page-configuration` |
| Field sections replacing the layout | Dynamic Forms on the FlexiPage | `admin/dynamic-forms-and-actions` |
| `Opportunity_Enterprise_Path` | `PathAssistant` | `admin/path-and-guidance` |
| Record type `Enterprise` / `SMB` split in the page assignment | `RecordType` | `admin/record-types-and-page-layouts` |
| `Close_Plan__c` field access | `PermissionSet` | `admin/permission-set-architecture` |
| Assignment of that permission set to 84 users | `PermissionSetAssignment` **records** (data, not metadata) | `admin/permission-set-architecture` |
| Walkthrough for the new Close Plan section | `Prompt` | `admin/in-app-guidance-and-walkthroughs` |

Two grounded facts shape the whole plan:

- A Lightning record page assignment is keyed on **app + `pageOrSobjectType` + `recordType` + `profile` + `formFactor`** (`AppProfileActionOverride`, Metadata API Developer Guide, `CustomApplication`). "The new Opportunity page" is therefore never one thing — it is one thing *per profile and record type*.
- `PermissionSetAssignment` is a standard object whose supported calls include `create()` and `delete()` (Object Reference). Deploying the permission set gives nobody access; a per-user data operation does. That single fact drives the sequencing in §3.

---

## 2. Change impact assessment by persona

| Persona | What changes on screen | What changes in process | What permission changes ship | Impact |
|---|---|---|---|---|
| Sales Rep (84) | Layout replaced by FlexiPage; Path header on Opportunity; fields regrouped into Dynamic Forms sections; Close Plan section appears from Proposal onward | Stage advance now reads the Path guidance instead of a wiki page; Close Plan captured in-record instead of in a deck | `Opportunity_Path_Rep` permission set grants `Close_Plan__c` (Edit) | High |
| Sales Manager (12) | Same page, plus the Close Plan section is read-only for them | Coaching conversation now anchored to Path key fields | `Opportunity_Path_Manager` grants `Close_Plan__c` (Read) | Medium |
| Sales Ops (3) | No page change — they work from list views and reports | They own the Path coaching text and the adoption reports after go-live | No change | Medium |
| Renewals (9, `SMB` record type) | **No change** — the `SMB` record type keeps the old assignment | None | None | None — but they must be told *nothing* changes, or they will assume it did |
| Integration user (2, API-only) | Nothing. These users never load a Lightning page, so no Path, no Dynamic Forms, no prompt reaches them | Field-level security on `Close_Plan__c` still governs their writes | Must be evaluated: does the integration write `Close_Plan__c`? | Silent — see `gotchas.md` |

The Renewals row and the integration row are the two most commonly missing rows. Both are audiences of the *communication*, not of the *training*.

---

## 3. The plan artefact

This is the machine-checkable record. Save it as `change-plan.yaml` in the project repo and lint it with `scripts/check_change_management_and_training.py`.

```yaml
change_plan:
  id: CM-2026-OPP-PATH
  title: "Opportunity page modernization - Path + Dynamic Forms"
  deploy_date: "2026-10-14"
  release_window_check: "Winter '27 upgrade date for this instance confirmed on trust.salesforce.com; see admin/salesforce-release-preparation"
  owner: "rev-ops-lead@example.com"
  status: planned

personas:
  - id: P-REP
    label: "Sales Rep"
    headcount: 84
    screen_change: "Layout replaced by FlexiPage with Path header and Dynamic Forms sections"
    process_change: "Close Plan captured in-record from Proposal stage onward"
    permission_change: "Opportunity_Path_Rep grants Close_Plan__c Edit"
    training_format: hands-on-lab
    training_env: "UAT2 (Full sandbox), refreshed after the production deploy is validated"
    owner: "sales-enablement@example.com"
    status: planned
    reads:
      - skills/admin/dynamic-forms-and-actions
      - skills/admin/path-and-guidance
  - id: P-MGR
    label: "Sales Manager"
    headcount: 12
    screen_change: "Same page; Close Plan section read-only"
    process_change: "Pipeline review reads Path key fields"
    permission_change: "Opportunity_Path_Manager grants Close_Plan__c Read"
    training_format: live-demo
    training_env: "UAT2 (Full sandbox)"
    owner: "sales-enablement@example.com"
    status: planned
    reads:
      - skills/admin/permission-set-architecture
  - id: P-OPS
    label: "Sales Ops"
    headcount: 3
    screen_change: "None - works from list views and reports"
    process_change: "Owns Path coaching text and the adoption reports after go-live"
    permission_change: "None"
    training_format: quick-reference
    training_env: "Production"
    owner: "rev-ops-lead@example.com"
    status: planned
    reads:
      - skills/admin/reports-and-dashboards
  - id: P-RENEWALS
    label: "Renewals (SMB record type)"
    headcount: 9
    screen_change: "None - the SMB record type keeps its existing page assignment"
    process_change: "None"
    permission_change: "None"
    training_format: none
    training_env: "None"
    owner: "rev-ops-lead@example.com"
    status: planned
  - id: P-INTEGRATION
    label: "Integration users (API-only)"
    headcount: 2
    screen_change: "None - these users never load a Lightning page"
    process_change: "None; field-level security on Close_Plan__c still governs writes"
    permission_change: "Under review - does the ERP sync write Close_Plan__c?"
    training_format: none
    training_env: "None"
    owner: "integrations-lead@example.com"
    status: blocked

communications:
  - id: MSG-01
    audience: P-MGR
    channel: manager-cascade
    when: D-15
    owner: "rev-ops-lead@example.com"
    subject: "Heads-up: Opportunity page changes on 14 Oct, and what we need from you"
    status: planned
  - id: MSG-02
    audience: P-REP
    channel: email
    when: D-10
    owner: "sales-enablement@example.com"
    subject: "Your Opportunity page changes on 14 Oct - 45 minutes of lab time booked"
    status: planned
  - id: MSG-03
    audience: P-RENEWALS
    channel: email
    when: D-10
    owner: "rev-ops-lead@example.com"
    subject: "No change for SMB renewals on 14 Oct"
    status: planned
  - id: MSG-04
    audience: P-INTEGRATION
    channel: email
    when: D-10
    owner: "integrations-lead@example.com"
    subject: "Close_Plan__c field added to Opportunity - confirm your sync mapping"
    status: planned
  - id: MSG-05
    audience: all
    channel: chatter
    when: D0
    owner: "sales-enablement@example.com"
    subject: "The new Opportunity page is live"
    status: planned
  - id: MSG-06
    audience: P-REP
    channel: in-app-guidance
    when: D0
    owner: "sales-enablement@example.com"
    subject: "Walkthrough: filling in the Close Plan section"
    status: planned
  - id: MSG-07
    audience: P-REP
    channel: email
    when: D+14
    owner: "sales-enablement@example.com"
    subject: "Two weeks in - what is working and what is not"
    status: planned

adoption_metrics:
  - id: AM-01
    label: "Did the affected reps come back at all"
    source: LoginHistory
    query: "SELECT UserId, COUNT(Id) logins FROM LoginHistory WHERE LoginTime = LAST_N_DAYS:14 AND UserId IN :repIds GROUP BY UserId"
    target: "80 of 84 reps with at least one login in the first 5 business days"
    owner: "rev-ops-lead@example.com"
    status: planned
  - id: AM-02
    label: "Did they engage with the walkthrough"
    source: PromptAction
    query: "SELECT LastResult, COUNT(Id) FROM PromptAction WHERE PromptVersionId = :closePlanPromptVersionId GROUP BY LastResult"
    target: "LastResult = Finish for 60% of displayed reps within 14 days"
    owner: "sales-enablement@example.com"
    status: planned
  - id: AM-03
    label: "Did the behaviour actually change"
    source: Opportunity
    query: "SELECT COUNT(Id) FROM Opportunity WHERE StageName = 'Proposal' AND Close_Plan__c != NULL AND LastModifiedDate = LAST_N_DAYS:14"
    target: "70% of Proposal-stage Opportunities carry a Close Plan by week 4"
    owner: "rev-ops-lead@example.com"
    status: planned
  - id: AM-04
    label: "Data quality on the fields the Path surfaces"
    source: Opportunity
    query: "SELECT StageName, COUNT(Id) FROM Opportunity WHERE CreatedDate = LAST_N_DAYS:30 AND NextStep = NULL GROUP BY StageName"
    target: "Blank NextStep below 15% at Proposal and later"
    owner: "rev-ops-lead@example.com"
    status: planned

feedback_loop:
  - id: FB-01
    channel: chatter-group
    audience: P-REP
    when: D0
    owner: "sales-enablement@example.com"
    status: planned
  - id: FB-02
    channel: survey
    audience: P-REP
    when: D+14
    owner: "sales-enablement@example.com"
    status: planned
  - id: FB-03
    channel: manager-cascade
    audience: P-MGR
    when: D+21
    owner: "rev-ops-lead@example.com"
    status: planned
```

**How to read it**

- `when` is always relative to deploy (`D-10`, `D0`, `D+14`). Calendar dates rot the moment the deploy slips; relative offsets survive a slip and the checker enforces the `D±n` form.
- Every row carries an `owner`. A row without a named owner is a row nobody sends.
- `status: blocked` on `P-INTEGRATION` is the point of the artefact: an unanswered question about an integration is visible in the plan rather than discovered at go-live.
- `training_format: none` is a legal answer. It records that the persona was *considered* and deliberately not trained — which is different from being forgotten.
- `reads` entries are repo paths; the checker resolves them so a plan cannot cite a skill that does not exist.
- `MSG-01` lands before `MSG-02` on purpose: managers should never hear about a change to their team's screen from their team.

**The sequencing rule this artefact encodes**

`MSG-02` (D-10) tells reps the page changes on the 14th. It does **not** tell them the Close Plan field is available, because `PermissionSetAssignment` records are created as part of the deploy runbook, not before it. Announcing a field ahead of its assignment produces a wave of "I can't see it" tickets from users who read the email and went looking. See `gotchas.md` §7.

---

## 4. Training plan

| Persona | Format | Environment | Length | Timing | Why this format |
|---|---|---|---|---|---|
| Sales Rep | Hands-on lab, 8–10 people per session | UAT2 Full sandbox | 45 min | D-7 to D-3 | The change is muscle memory (where fields now live), which reading cannot fix |
| Sales Manager | Live demo + Q&A | UAT2 Full sandbox | 30 min | D-12 | They need to answer their team's questions, not perform the task |
| Sales Ops | Quick reference doc | Production | — | D-5 | They already know the objects; they need the new report definitions |
| Renewals | None | — | — | — | Deliberately untrained; MSG-03 tells them why |
| Integration users | None | — | — | — | No UI surface; MSG-04 is a mapping request, not training |

**The sandbox rule.** Train in a sandbox that carries the change, and refresh the training sandbox **after** the production deploy is validated, never before:

- Refreshing before the deploy gives you a copy of the *old* production page assignment — reps practise on the layout they are about to lose.
- A Full sandbox has a mandatory minimum interval between refreshes (per-type intervals are documented in `devops/sandbox-refresh-and-templates`), so a mistimed refresh locks the training org into the wrong state for weeks. **UNVERIFIED (2026-09-04): the existence and length of the per-type minimum refresh interval is not stated in the eight extracted PDFs (Metadata API, Object Reference, Apex, Data Loader, Bulk API, App Limits, REST); help.salesforce.com cannot be fetched. The claim rests on `skills/devops/sandbox-refresh-and-templates/SKILL.md` "Refresh Intervals by Sandbox Type".**
- For the lab itself the practical sequence is: deploy to UAT2 → run the deploy validation → run the labs on UAT2 → deploy to production → refresh UAT2 from the now-current production. That way the lab shows the shipping configuration and the post-go-live training org matches production.

**What each lab exercise must contain** — the exercise, not the tour:

```markdown
### Lab 2 — Advance an Enterprise Opportunity to Proposal (Sales Rep, 12 min)

Persona login:  training.rep01@acme.com.uat2      Record type: Enterprise
Starting data:  OPP-TR-0012 "Northwind Expansion", stage Qualification
Steps:
  1. Open OPP-TR-0012 from the "My Open Opportunities" list view.
  2. Click "Proposal" on the Path. Read the key fields it asks for.
  3. Fill Next Step and Close Plan. Mark Current Status Complete.
  4. Save. Note that the Close Plan section was not visible at Qualification.
Pass:  the record saves at Proposal with Close Plan populated
Fail:  "You do not have access to Close_Plan__c" -> the persona login is missing
       Opportunity_Path_Rep; stop and report, do not work around it
```

The Fail line is doing real work. A lab account missing the permission set assignment is the *same* defect the whole org will hit on go-live day, discovered a week early.

---

## 5. In-app guidance

Configuration belongs to `admin/in-app-guidance-and-walkthroughs`. This plan only decides *what* to build and *who* sees it.

| Decision | Value | Grounded in |
|---|---|---|
| Metadata type | `Prompt` — suffix `prompt`, stored in the `prompts` folder, API 46.0+ | Metadata API Developer Guide, `Prompt` |
| Guidance kind | Walkthrough, 4 steps (`stepNumber` 1–4; a walkthrough may have up to 10 consecutive steps) | Metadata API Developer Guide, `PromptVersion.stepNumber` |
| Prompt kind | `displayType` = `Targeted` (points at the Close Plan section), API 52.0+ | Metadata API Developer Guide, `PromptVersion.displayType` |
| Audience | `userAccess` = `SpecificPermissions` with a custom permission, **not** `userProfileAccess` = `SpecificProfiles` | Metadata API Developer Guide, `PromptVersion.userAccess` / `userProfileAccess` |
| Visibility rule | `uiFormulaRule` criterion `{!$Permission.CustomPermission.Opportunity_Path_Rollout}` | Metadata API Developer Guide, `UiFormulaCriterion.leftValue` |
| End date | `endDate` = D+60, so the walkthrough retires itself | Metadata API Developer Guide, `PromptVersion.endDate` |

Copy limits that constrain the writing, straight from the guide's field table: `title` maximum 36 characters, `actionButtonLabel` maximum 25, `dismissButtonLabel` maximum 15, and `body` up to 4,000 characters in API 60.0 and later (240 for floating and targeted prompts in earlier versions). Draft the four step titles to 36 characters before anyone builds the prompt — rewriting copy after configuration is the avoidable part.

Because the audience is a custom permission rather than a profile, the same permission set that grants `Close_Plan__c` can also carry the custom permission. One assignment then does two jobs: it opens the field and it turns on the walkthrough, for exactly the same 84 people, on exactly the same day.

---

## 6. Adoption metrics, as queries

Adoption claims that cannot be written as a query are opinions. The four metrics in §3 are reproduced here with what each one can and cannot tell you.

**AM-01 — presence.** `LoginHistory` is queryable (`describeSObjects()`, `query()`, `retrieve()`) but the Object Reference is explicit that only users with **Manage Users** or **Monitor Login History** can access it, except that from API 37.0 every user can retrieve their own records. The enablement lead running the adoption report usually has neither permission and will get an empty result rather than an error. Assign the access, or hand the query to someone who has it.

```sql
SELECT UserId, MIN(LoginTime) firstLogin, COUNT(Id) logins
FROM LoginHistory
WHERE LoginTime = LAST_N_DAYS:14
  AND UserId IN :repIds
GROUP BY UserId
```

Filtering `LoginType` needs care. The `LoginType` picklist includes `Application`, `Remote Access 2.0` (OAuth), `SAML Sfdc Initiated SSO`, `Lightning Login` and `Help And Training`, among others. In an SSO org a human browser login is a SAML value, not `Application` — so the widely copied `LoginType = 'Application'` filter returns near-zero for exactly the orgs most likely to use it. Check which values your org actually produces before filtering:

```sql
SELECT LoginType, LoginSubType, COUNT(Id)
FROM LoginHistory
WHERE LoginTime = LAST_N_DAYS:7
GROUP BY LoginType, LoginSubType
```

**AM-02 — engagement with the guidance.** `PromptAction` (API 46.0+) records one row per user per prompt version, with `TimesDisplayed`, `TimesActionTaken`, `TimesDismissed`, `TimesSnoozed`, `StepNumber`, `StepCount` and a `LastResult` picklist of `CustomAction`, `Dismiss`, `Error`, `Finish` (walkthroughs only), `NoAction`, `NotSeen` and `Snooze`. This is the one place the platform tells you whether guidance was consumed rather than merely published.

```sql
SELECT LastResult, COUNT(Id) users, AVG(StepNumber) avgStepReached
FROM PromptAction
WHERE PromptVersionId = :closePlanPromptVersionId
GROUP BY LastResult
```

A high `Dismiss` count with a low `Finish` count is the signal to rewrite the copy. A high `NotSeen` count means the targeting is wrong — usually the custom permission was not assigned.

**AM-03 / AM-04 — behaviour.** Record counts are the only metric that answers "did the process change". Report definitions rather than one-off queries, so Sales Ops can own them:

| Report | Type | Filters | Grouping | Schedule |
|---|---|---|---|---|
| `Close Plan Completion by Rep` | Opportunities | Stage in (Proposal, Negotiation, Closed Won); Close Date this quarter | Rows: Owner; Columns: Close Plan blank / populated | Weekly to the manager cascade, weeks 1–6 |
| `Stage Age Before vs After` | Opportunities with history | Stage change date in last 90 days | Rows: Stage; Summary: avg days in stage | Weekly, compared to the pre-go-live baseline |

Capture the baseline for both reports **before** the deploy. Without it, week-4 numbers have nothing to be better than.

**What you cannot measure: list-view usage.** The `ListView` object (API 32.0+) exposes `DeveloperName`, `IsSoqlCompatible`, `LastModifiedById`, `LastReferencedDate`, `LastViewedDate`, `Name`, `NamespacePrefix` and `SobjectType` — there is no user field and no usage counter on it. "How many reps opened the new list view" is not a question the platform answers, and a plan that promises it will quietly drop the metric later. Say so at planning time and substitute a record-behaviour metric (AM-03) instead.

---

## 7. Feedback loop

Three channels, three different jobs, all in the artefact as `feedback_loop` rows:

| Row | Channel | Opens | Job | Closes |
|---|---|---|---|---|
| FB-01 | Chatter group, named in MSG-05 | D0 | Catch the go-live day breakages while they are still cheap | D+30, archived with a summary post |
| FB-02 | Two-question survey, linked from MSG-07 | D+14 | Get the quiet majority who never post in Chatter | D+21 |
| FB-03 | Manager cascade, MGR one-to-ones | D+21 | Surface the "I've gone back to the spreadsheet" cases that nobody writes down | D+35 |

The loop is only a loop if something comes back. Two rules make that true:

1. Every FB-01 thread gets a reply naming what will happen — fixed, deferred with a date, or won't fix with a reason. Silence trains people out of reporting.
2. FB-02 results and the AM-01 to AM-04 numbers go into the same weekly review. A metric that dropped and a survey comment explaining why are the same finding; read apart they produce the wrong action.

---

## 8. Linting this artefact

```bash
python3 skills/admin/change-management-and-training/scripts/check_change_management_and_training.py \
  --file change-plan.yaml \
  --repo-root .
```

The checker enforces the schema this file demonstrates: every communication has an audience, channel, `D±n` timing and owner; every persona has a training format and an owner; every adoption metric has a query; every id is unique; every `audience` resolves to a persona (or `all`); every `reads` path exists. It exits `1` on any ISSUE.

---

## Where each artefact goes next

| Artefact | Consumed by |
|---|---|
| Persona rows (§2, §3) | `agents/config-workbook-author/AGENT.md` — the workbook's stakeholder and training sections |
| Impact assessment (§2) | `agents/story-drafter/AGENT.md` — enablement and comms stories in the release backlog |
| Ship list (§1) | `admin/change-management-and-deployment` — the deployment manifest |
| Training sandbox timing (§4) | `devops/sandbox-refresh-and-templates` — the refresh request |
| Release-window check (§3 `release_window_check`) | `admin/salesforce-release-preparation` — seasonal upgrade date for the instance |
| In-app guidance decisions (§5) | `admin/in-app-guidance-and-walkthroughs` — the `Prompt` build |
| Adoption reports (§6) | `admin/reports-and-dashboards` — report and dashboard build |
