# Worked Example — A UAT Programme for the Acme Case Intake Release

One feature, worked end to end: the Service Cloud case-intake solution built in
`skills/admin/case-management-setup/references/worked-example-case-intake.md`. That file produced the
configuration workbook and the deployable metadata. This file produces the **UAT programme** that
decides whether it goes live: the plan header, the environment, the test users, the script, the
defect log, and the sign-off record.

Boundaries, so nothing here is written twice:

| Concern | Owned by |
|---|---|
| The Given/When/Then form of an acceptance criterion | `admin/acceptance-criteria-given-when-then` |
| The per-case field schema (`case_id`, `story_id`, `ac_id`, `persona`, `data_setup`, …) | `admin/uat-test-case-design` § The Canonical UAT Case Schema |
| The story text the ACs hang off | `admin/user-story-writing-for-salesforce` |
| Sandbox type, capacity, refresh floor | `admin/sandbox-strategy` |
| Post-refresh isolation (deliverability, `.invalid`, CronTriggers, Named Credentials) | `devops/sandbox-data-isolation-gotchas` |
| Deploy vehicle, `DeployOptions`, release guardrails | `admin/change-management-and-deployment` |
| Code freeze, cutover window, hypercare | `devops/go-live-cutover-planning` |
| **The programme: environment, personas, script, defects, regression, sign-off** | **this skill** |

---

## 1. Requirements carried over from the build

Acme Software, B2B support, moving off a shared mailbox. The stories under test are the ones the
workbook rows implement. Story ids are assigned here so each UAT case has something to trace to.

| Story | From workbook row | Statement |
|---|---|---|
| US-CI-01 | CWB-AUT-001 | As a customer, when I submit the web form, my case reaches Tier 1 General so an agent picks it up. |
| US-CI-02 | CWB-AUT-001, CWB-AUT-002, CWB-INT-001 | As a finance requester, when I email `billing@acme.example`, my case reaches the Billing queue and I get an acknowledgement from `support@`. |
| US-CI-03 | CWB-VR-001 | As a support manager, I need Severity 1 cases to carry a description and an account so Tier 2 can act without chasing. |
| US-CI-04 | CWB-AUT-004, CWB-AUT-006 | As a support manager, I need the SLA clock to pause outside regional business hours so weekend cases are not auto-escalated. |
| US-CI-05 | CWB-AUT-001 | As a data owner, when I load a backlog of cases, they route by the same rules as cases created in the UI. |
| US-CI-06 | CWB-SHR-001 | As a security owner, I need Billing staff to see only Billing-queue cases. |

---

## 2. UAT plan header

**Release:** 2026.R3 — Service Cloud Case Intake
**Plan id:** UAT-2026R3-CASE-INTAKE
**BA / QA lead:** owns this file. **Business owner:** Head of Support.

### 2.1 Environment: why Full, not Partial

| Decision | Value | Source |
|---|---|---|
| Sandbox type | Full (`UAT1`) | `admin/sandbox-strategy` § Sandbox Type Decision Matrix routes "UAT, regression, or production rehearsal with realistic volume" to a Full sandbox — best parity, highest cost |
| Why not Partial Copy | The release contains an assignment rule that fires on a 200-row backlog load (US-CI-05) and an escalation rule that reads case age across the whole open backlog. A Partial Copy holds 5 GB, or 10,000 records per selected object plus children, so the open-case volume that makes the escalation queue behave like production is not there. | `admin/sandbox-strategy` § Type Capacities and Refresh Windows |
| Why not Developer | No production data at all; every routing test would run against records the tester invented, which is exactly the data shape the rules were written against. | `admin/sandbox-strategy` § Sandbox Type Decision Matrix |
| Refresh floor | Full sandboxes can be refreshed every 29 days — so the UAT window has to be planned around the refresh, not the other way round. | `admin/sandbox-strategy` § Type Capacities and Refresh Windows |
| Entitlement check | Enterprise Edition ships with **0** Full sandboxes by default; Acme's Full sandbox is an add-on purchase. Confirm the allocation before promising a Full-sandbox UAT. | `admin/sandbox-strategy` § What Your Org Actually Owns |

**Refresh date: 2026-08-24. The build was deployed on 2026-08-26. Nothing is refreshed again until
sign-off.** The refresh is the first line of the plan header because a refresh after the build
deletes the build (gotcha 6).

### 2.2 Deliverability

US-CI-02's acceptance criterion is an email arriving. Three levels exist — `No Access`,
`System Email Only`, `All Email` — and a new sandbox created through Setup defaults to
`System Email Only`, which suppresses workflow email alerts and `Messaging.sendEmail()` while still
letting password resets through. A sandbox refreshed from an older one may inherit whatever it had
before, including `All Email`, so the setting is **read** after every refresh rather than assumed
(`devops/sandbox-data-isolation-gotchas` § Email Deliverability — What Is and Is Not Controlled
Automatically).

Raising it to `All Email` is not free. On refresh Salesforce appends `.invalid` to every
**User.Email** value, but **Contact, Lead and Person Account email fields are copied verbatim from
production** (same section). Acme's auto-response rule sends to the case contact. So:

1. Deliverability → `All Email` (recorded in the plan, with the date and who set it).
2. Before any email test, the contact emails on the seeded test accounts are rewritten to
   `qa+<n>@acme.example.invalid`.
3. Production contact records in `UAT1` are left alone and no test case is allowed to touch them.

### 2.3 Test users — one per persona, none of them an admin

Usernames in a sandbox carry the sandbox name appended: `jo.tan@acme.com` becomes
`jo.tan@acme.com.uat1` in a sandbox named `uat1`, and that suffix is ignored when the metadata is
deployed onward (api_meta.txt L2705–2719, "Maintaining User References"). The same passage is why
a user that exists **only** in the sandbox is a release risk: if a deployed component references a
username the destination org does not have, Salesforce raises an error and the deployment stops
until the reference is resolved. UAT users are therefore created from real production users, not
invented.

| Persona | Test user (sandbox) | Profile | Permission sets / PSG | What only this persona can prove |
|---|---|---|---|---|
| Tier 1 agent | `jo.tan@acme.com.uat1` | Minimum Access — Salesforce | `Support_Agent` PSG (Case CRUD, Email-to-Case reply, Omni presence) | Web and email routing land where an agent actually sees them |
| Tier 2 engineer | `raj.patel@acme.com.uat1` | Minimum Access — Salesforce | `Support_Agent`, `Support_Tier2` | Escalated cases arrive and are editable |
| Billing agent | `mia.ross@acme.com.uat1` | Minimum Access — Salesforce | `Billing_Case_Access` | Billing sees Billing and nothing else (US-CI-06) |
| Support manager | `dee.olu@acme.com.uat1` | Standard User | `Support_Agent`, `Support_Manager` | Queue-owned cases visible via `doesIncludeBosses` |
| Data owner | `sam.ito@acme.com.uat1` | Standard User | `Data_Load_Operator` (API Enabled, Case Create) | The backlog load routes under a real load profile, not admin |

**No row says System Administrator.** An admin bypasses FLS and most sharing in the UI, so a pass
from an admin proves the feature exists, not that the persona can use it
(`admin/uat-test-case-design` § Permission Setup Discipline; gotcha 2 in this skill).

---

## 3. The UAT script — 6 cases

Each row's Given/When/Then is the acceptance criterion verbatim; the per-case field schema is the
sibling's (`admin/uat-test-case-design` § The Canonical UAT Case Schema) and is not restated here.

| Case | Story / AC | Persona | Given / When / Then | Type | Expected result |
|---|---|---|---|---|---|
| UAT-CI-001 | US-CI-01 / AC-01.1 | Tier 1 agent | **Given** the web form is published and no assignment rule other than `Support_Case_Routing` is active; **When** a visitor submits the form with Severity 4 and no matching routing address; **Then** the case Owner is the `Tier_1_General` queue and Origin is `Web`. | positive | `Case.Owner.Name = "Tier 1 General"`, `Case.Origin = "Web"` |
| UAT-CI-002 | US-CI-02 / AC-02.1 | Tier 1 agent | **Given** deliverability is `All Email` and the routing address `billing@acme.example` is verified; **When** an external sender emails `billing@acme.example`; **Then** the case Owner is the `Billing_Queue`, and one acknowledgement is sent from the org-wide address `support@acme.example` — not from the routing address. | positive | Owner = `Billing_Queue`; exactly one outbound acknowledgement; `From` = `support@acme.example` |
| UAT-CI-003 | US-CI-03 / AC-03.2 | Tier 1 agent | **Given** validation rule `CWB-VR-001` is active; **When** the agent sets Severity = 1, leaves Description empty and clicks Save; **Then** the save is rejected with the rule's error message and no case is created. | **negative** | Save blocked; error text matches the rule verbatim; record count unchanged |
| UAT-CI-004 | US-CI-04 / AC-04.1 | Support manager | **Given** the case account has `Region__c = EMEA` and the EMEA calendar runs 08:00–18:00 London; **When** a case is created Friday 17:30 London and untouched; **Then** the 8-business-hour escalation target lands Monday morning, not Saturday. | positive, time-based | Escalation target timestamp is the next business morning |
| UAT-CI-005 | US-CI-05 / AC-05.1 | Data owner | **Given** a 200-row CSV of backlog cases with mixed Origin values and the Data Loader **Assignment rule** setting populated with the `Support_Case_Routing` rule id; **When** the load runs as one SOAP batch; **Then** all 200 rows succeed, every row's Owner matches the rule that a UI-created case with the same values gets, and no row fails on a limit. | **bulk / limit** | 200 success rows, 0 errors; owner distribution equals the UI control set |
| UAT-CI-006 | US-CI-06 / AC-06.1 | Billing agent | **Given** the Billing agent holds only `Billing_Case_Access`; **When** they open the record id of a `Tier_2_Support_Queue` case directly by URL; **Then** the platform returns "insufficient privileges" rather than the record. | **negative, sharing** | Access denied on direct URL; case absent from every list view available to the persona |

### Why UAT-CI-005 is written the way it is

The bulk case is the one that fails silently if it is written loosely, so its preconditions carry
the platform facts:

- **Batch size.** Data Loader's maximum import batch is **200 records for SOAP API and 10,000 for
  Bulk API**; with Bulk API 2.0 selected neither batch-size setting is used at all because Bulk API
  2.0 sizes batches itself (`salesforce_data_loader.txt` L351–360). Pinning the case to one
  200-row SOAP batch is what makes it a *limit* test: it puts the whole file through the automation
  in the largest single transaction the tool will send.
- **The limits that batch is being tested against.** A synchronous transaction gets 100 SOQL
  queries, 150 DML statements and 10,000 ms of CPU; asynchronous gets 200, 150 and 60,000 ms
  (`apexdev.txt` L19544, L19554, L19579). A rule chain that is fine for one record and dies at 200
  is exactly what this case is for.
- **Assignment rules do not run by themselves.** Data Loader has an **Assignment rule** setting:
  "Specify the ID of the assignment rule to use for inserts, updates, and upserts… applies to
  inserts, updates, and upserts on cases and leads. **The assignment rule overrides Owner values in
  your CSV file**" (`salesforce_data_loader.txt` L379–383). Leave it empty and the CSV's OwnerId —
  or the load user — wins. The three API paths do not agree with each other, which is the point of
  gotcha 7:

  | Path | Default when nothing is specified |
  |---|---|
  | Data Loader | The Assignment rule setting is blank by default; rules do not run |
  | Bulk API 2.0 job | `assignmentRuleId` is **Optional** on the job resource (`api_asynch.txt` L1591–1595) — absent means no rule |
  | REST API | "If the header is not provided with a request, REST API defaults to using the active assignment rules" (`api_rest.txt` L691–694) |

  So a case that passes when the developer inserts records through REST can fail when the data
  owner loads the same rows through Data Loader. UAT-CI-005 pins the tool **and** the setting.

---

## 4. Defect classification, with what each looks like here

Severity (P1–P4) is defined in `SKILL.md` § Defect Classification for Salesforce and is not
repeated. What UAT actually gets wrong is the **second** axis — the category, which decides who
fixes it and whether it is a fix at all.

| Category | Test that finds it | Concrete defect on this release | Fixed by | Typical severity |
|---|---|---|---|---|
| **Configuration** | UAT-CI-003 | The validation rule fires on Severity 1 **and** Severity 2 because the criteria used `<= 2`; the error text names Severity 1 only | Admin, in the rule | P2 |
| **Automation** | UAT-CI-001 | The catch-all entry sits above the Billing entry, so every case matches the catch-all first and `Billing_Queue` never receives one | Admin, entry order in the assignment rule | P1 |
| **Data** | UAT-CI-005 | 14 of 200 rows fail on a required lookup because the backlog CSV carries account names that were merged in production after the export | Data owner, in the file — **not** a build defect | P3, does not block |
| **Sharing / security** | UAT-CI-006 | The Billing agent can open the Tier 2 case: the queue was created without `doesIncludeBosses` and a sharing rule grants Read to the whole Support role branch | Admin, sharing model | **P1 — blocks release** |
| **Training / expectation** | UAT-CI-002 | The tester reports "no acknowledgement email" — the email did send, to a `.invalid` contact address that the tester could not check. Nothing on the platform is wrong. | BA, by fixing the test data and the script step — **not a defect against the build** | Closed as "not a defect" |
| **Environment** | UAT-CI-004 | The escalation target is right but no notification arrives because deliverability was reset by an unannounced refresh | Release manager, environment — logged so the pattern is visible, then closed | P3 |

Two rules that keep this table honest:

1. **A defect names the story it violates, not the screen it was noticed on.** "Case went to the
   wrong queue" is a symptom; "US-CI-01 AC-01.1 not met: Owner = Tier 1 General expected, Billing
   Queue observed" is a defect (gotcha 9).
2. **"Training" and "Environment" are dispositions, not a bin for anything inconvenient.** Each one
   still gets an owner and a closing note, because the pattern — testers with no reachable inbox,
   sandboxes refreshed mid-cycle — is a process defect even when the build is fine.

### Defect log rows for this release

```yaml
- defect_id: DEF-2026R3-004
  case_id: UAT-CI-006
  story_id: US-CI-06
  severity: P1
  category: sharing
  summary: "Billing agent can open a Tier 2 queue case by direct URL"
  expected: "Insufficient privileges"
  actual: "Case record renders read-only"
  owner: dee.olu@acme.com
  status: Open
  blocks_release: true
- defect_id: DEF-2026R3-007
  case_id: UAT-CI-005
  story_id: US-CI-05
  severity: P3
  category: data
  summary: "14/200 backlog rows fail on Account lookup after production merges"
  expected: "200 success rows"
  actual: "186 success, 14 INVALID_CROSS_REFERENCE_KEY"
  owner: sam.ito@acme.com
  status: Deferred
  blocks_release: false
```

---

## 5. Sign-off record

Sign-off is a record, not an email thread. The four things that make it re-readable a year later
are **what** was tested, **where**, **which build**, and **what was knowingly accepted**.

| Field | Value |
|---|---|
| Decision | No-Go at first pass (2026-09-01) → Go (2026-09-03) after DEF-2026R3-004 was fixed and UAT-CI-006 was re-run |
| Build tested | Validation id `0Af5g00000XyZ12CAB`, validated against production 2026-09-02 |
| Environment | `UAT1`, Full sandbox, refreshed 2026-08-24, deliverability `All Email` |
| Cases | 6 authored, 6 executed, 6 passed on the re-run; 1 negative, 1 bulk |
| Open defects at sign-off | 0 × P1, 0 × P2, 1 × P3 deferred (DEF-2026R3-007, owner `sam.ito@acme.com`, target 2026-09-19) |
| Approvers | Head of Support (business owner), BA/QA lead, release manager |

**A go decision is not valid unless the negative cases ran.** Six passes of which none is a negative
proves the feature works when used correctly, not that it is safe (gotcha 10). Here the go rests on
UAT-CI-003 and UAT-CI-006 having been executed and passed, and the sign-off record names them.

### Validation before the sign-off, quick deploy after it

The build was validated against production *during* UAT, not after it, so the go decision is
followed by a deploy that runs no tests:

- A validation is `deploy()` with `checkOnly` = `true` — it writes nothing
  (`admin/change-management-and-deployment` § The Deploy Contract).
- A quick deploy (`deployRecentValidation()`) skips the Apex test run, and only if: the components
  "have been validated successfully for the target environment **within the last 10 days**", the
  tests in the target org passed, and coverage is met — at least 75% overall with triggers covered,
  or 75% per deployed class and trigger when `RunSpecifiedTests` was used (api_meta.txt L4860–4868).

That 10-day window is the real constraint on a UAT schedule: a validation taken at the start of a
three-week UAT cycle is dead by sign-off and the tests re-run in the deployment window. The plan
schedules the validation for the day sign-off is expected, not the day the build lands.

---

## 6. Pre-UAT environment checklist

Every line is a claim about the platform, so each carries its source. Run it after the refresh and
before the first tester logs in.

- [ ] **Sandbox type matches the risk.** Full for volume-sensitive UAT; if this is a Partial Copy,
      write down which cases it *cannot* prove — a Partial Copy is capped at 5 GB or 10,000 records
      per selected object plus children (`admin/sandbox-strategy` § Type Capacities).
- [ ] **Refresh date recorded, and no refresh scheduled inside the UAT window.** A Full sandbox can
      be refreshed every 29 days; refreshing over live work destroys the metadata and test data in
      it (`admin/sandbox-strategy` § Type Capacities; `admin/sandbox-strategy` →
      `references/gotchas.md` § Refreshing Over Active Work).
- [ ] **Deliverability read, not assumed.** Setup → Deliverability. New sandboxes default to
      `System Email Only`; refreshed ones may inherit `All Email`
      (`devops/sandbox-data-isolation-gotchas` § Email Deliverability).
- [ ] **Contact / Lead emails scrubbed before deliverability is raised.** Only `User.Email` gets
      `.invalid` appended on refresh; Contact, Lead and Person Account emails are copied verbatim
      (same section).
- [ ] **Scheduled jobs and Named Credentials reviewed.** CronTriggers are copied and are not
      deactivated; Named Credential endpoints still point at production (same skill,
      §§ Scheduled Job Carry-Over, Integration Endpoint Carry-Over).
- [ ] **Test users exist per persona, with the sandbox username suffix, and none is an admin.**
      Sandbox usernames carry the sandbox name (`user@acme.com` → `user@acme.com.uat1`) and the
      suffix is ignored on deploy; a username that exists only in the sandbox stops a later
      deployment (api_meta.txt L2705–2719).
- [ ] **Mobile is a separate pass where the story mentions it.** A Lightning record page assigned
      with `formFactor` = `Large` covers the Lightning Experience desktop only; `Small` is the
      Salesforce mobile app on a phone or tablet (api_meta.txt L39827–39836).
- [ ] **Data-load tool and its assignment-rule setting pinned in the test case**, not left to the
      tester (`salesforce_data_loader.txt` L379–383).
- [ ] **Validation deploy scheduled to land inside the 10-day quick-deploy window** relative to the
      expected sign-off date (api_meta.txt L4860–4868).

---

## 7. The plan as a lintable record

The whole programme above compresses into one YAML file that
`scripts/check_uat_and_acceptance_criteria.py` lints. Save it as `uat-plan.yaml` alongside the test
script and run:

```bash
# one plan record
python3 scripts/check_uat_and_acceptance_criteria.py --file uat-plan.yaml

# the whole UAT folder: plan records and markdown scripts together
python3 scripts/check_uat_and_acceptance_criteria.py --manifest-dir ./uat/
```

```yaml
plan_id: UAT-2026R3-CASE-INTAKE
release: "2026.R3 - Service Cloud Case Intake"
status: signed_off
environment:
  sandbox_name: UAT1
  sandbox_type: Full
  refreshed_on: 2026-08-24
  build_deployed_on: 2026-08-26
  email_deliverability: All Email
  contact_emails_scrubbed: true
  scheduled_jobs_aborted: true
  validation_id: 0Af5g00000XyZ12CAB
  validated_on: 2026-09-02
personas:
  - persona_id: P-TIER1
    name: Tier 1 agent
    profile: Minimum Access - Salesforce
    permission_sets: Support_Agent
    test_user: jo.tan@acme.com.uat1
  - persona_id: P-BILLING
    name: Billing agent
    profile: Minimum Access - Salesforce
    permission_sets: Billing_Case_Access
    test_user: mia.ross@acme.com.uat1
  - persona_id: P-MANAGER
    name: Support manager
    profile: Standard User
    permission_sets: Support_Agent;Support_Manager
    test_user: dee.olu@acme.com.uat1
  - persona_id: P-DATA
    name: Data owner
    profile: Standard User
    permission_sets: Data_Load_Operator
    test_user: sam.ito@acme.com.uat1
test_cases:
  - case_id: UAT-CI-001
    story_id: US-CI-01
    ac_id: AC-01.1
    persona: P-TIER1
    sandbox: UAT1
    negative_path: false
    bulk_path: false
    expected_result: "Case Owner is the Tier 1 General queue and Origin is Web"
    pass_fail: Pass
  - case_id: UAT-CI-002
    story_id: US-CI-02
    ac_id: AC-02.1
    persona: P-TIER1
    sandbox: UAT1
    negative_path: false
    bulk_path: false
    expected_result: "Owner is Billing_Queue and one acknowledgement is sent from support@acme.example"
    pass_fail: Pass
  - case_id: UAT-CI-003
    story_id: US-CI-03
    ac_id: AC-03.2
    persona: P-TIER1
    sandbox: UAT1
    negative_path: true
    bulk_path: false
    expected_result: "Save is rejected with the validation rule error and no case is created"
    pass_fail: Pass
  - case_id: UAT-CI-004
    story_id: US-CI-04
    ac_id: AC-04.1
    persona: P-MANAGER
    sandbox: UAT1
    negative_path: false
    bulk_path: false
    expected_result: "Escalation target lands on the next business morning, not Saturday"
    pass_fail: Pass
  - case_id: UAT-CI-005
    story_id: US-CI-05
    ac_id: AC-05.1
    persona: P-DATA
    sandbox: UAT1
    negative_path: false
    bulk_path: true
    expected_result: "200 rows succeed and owner distribution equals the UI control set"
    pass_fail: Pass
  - case_id: UAT-CI-006
    story_id: US-CI-06
    ac_id: AC-06.1
    persona: P-BILLING
    sandbox: UAT1
    negative_path: true
    bulk_path: false
    expected_result: "Insufficient privileges on direct URL and case absent from all list views"
    pass_fail: Pass
defects:
  - defect_id: DEF-2026R3-004
    case_id: UAT-CI-006
    severity: P1
    category: sharing
    owner: dee.olu@acme.com
    status: Closed
  - defect_id: DEF-2026R3-007
    case_id: UAT-CI-005
    severity: P3
    category: data
    owner: sam.ito@acme.com
    status: Deferred
sign_off:
  decision: Go
  decided_on: 2026-09-03
  business_owner: Head of Support
  qa_lead: BA/QA lead
  build_version: 0Af5g00000XyZ12CAB
  sandbox: UAT1
  known_issues: "DEF-2026R3-007 deferred, owner sam.ito@acme.com, target 2026-09-19"
source_skills:
  - admin/uat-test-case-design
  - admin/acceptance-criteria-given-when-then
  - admin/sandbox-strategy
  - devops/sandbox-data-isolation-gotchas
  - admin/change-management-and-deployment
```

What the checker enforces on that file, and why each rule exists:

| Rule | Gotcha it defends |
|---|---|
| Every case has `story_id` and `ac_id` | 9 — defects logged against symptoms, not stories |
| Every case's `persona` resolves to a declared persona, and no persona is System Administrator | 2 — admin testers hide sharing and FLS defects |
| Every case names a `sandbox` matching `environment.sandbox_name` | 5, 6, 11 — the environment is part of the result |
| `environment.refreshed_on` is before `build_deployed_on` | 6 — a refresh after the build deletes the build |
| At least one case has `negative_path: true` and one has `bulk_path: true` | 10, 8 — a script of happy paths is not evidence |
| Every defect's `case_id` resolves to a declared case | 9 |
| `sign_off.decision: Go` requires zero open P1/P2 defects | § Sign-off, above |
| No unfilled placeholders anywhere | a template shipped as a plan |

---

## 8. What this example does not decide

- **Whether the feature should exist.** That is `admin/requirements-gathering-for-sf` and
  `admin/user-story-writing-for-salesforce`.
- **How the individual cases are decomposed from ACs.** `admin/uat-test-case-design` § One AC
  Scenario → One UAT Case.
- **The cutover itself** — freeze, window, hypercare — `devops/go-live-cutover-planning`.
- **Whether any of these cases should be automated instead.** Time-based and bulk paths are the two
  strongest candidates; see `flow/flow-testing` and `apex/test-class-standards`. UAT-CI-005 in
  particular is a manual proxy for a bulk Apex test and should be promoted to one once the routing
  logic stops changing.
