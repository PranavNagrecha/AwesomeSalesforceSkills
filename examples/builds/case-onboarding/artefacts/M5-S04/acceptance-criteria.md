# Acceptance Criteria — Acme Software Case Onboarding on Service Cloud

Compiled by `agents/build-doc-keeper`'s `M5-S04` compile run. Given/When/Then shape: `skills/admin/acceptance-criteria-given-when-then/references/worked-examples.md` § 5. Collated from `artefacts/M5-S03/story-backlog.md`'s per-story criteria and its own "Requirements Traceability Matrix" section, which is the only place a criterion is already joined to a `req_id` — a criterion not already tied to one there is reproduced below for completeness but is **not** given a fabricated `req_id` in the lintable record; see "Criteria not traced to a requirement" at the end.

Lint with: `python3 skills/admin/acceptance-criteria-given-when-then/scripts/check_ac_format.py --file artefacts/M5-S04/acceptance-criteria.md`

---

## Background (shared by every criterion below)

Reproduced from `story-backlog.md`'s own shared Background: Case OWD is `Private`; the only sharing rule is `Support_Cases_To_Tier_2`; nobody holds `View All`/`Modify All` on Case; no role hierarchy exists; every tester runs Lightning desktop (Q83); the sandbox itself is **UNVERIFIED** — Q75 is deferred and `M5-S02` is `blocked`, so no criterion below can name one.

### US-CASE-001 — Tier 1 agent receives a support email as a routed, acknowledged case

**As a** Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`,
**I want** a customer email arriving at `support@acme.example` to become a Case that is
already owned by my queue and already acknowledged when I first see it,
**So that** the requirement's one-minute promise is met on the channel that carries roughly
400 of the 460 cases a day and no customer waits on a human to press send.

1. [REQ-005, REQ-034, REQ-036, REQ-050, REQ-053] *Given* the `support@acme.example` routing address is live and I hold `PSG_Tier1_Prod`,
  *When* a customer sends mail to that address,
  *Then* a Case exists with Origin `Email-Support`, Owner the `Tier_1_General` queue, and it
  appears in my `Tier_1_General_Queue` list view.
2. [REQ-032, REQ-037, REQ-055] *Given* that same Case has just been created,
  *When* I read the customer's mailbox,
  *Then* one acknowledgement has arrived from `support-noreply@acme.example` with sender
  name `Acme Support`, carrying the case number, and exactly one — not two.
3. [REQ-054] *Given* mail arrives from a sender the org does not authorise,
  *When* the routing address processes it,
  *Then* no Case is created and the mail bounces rather than becoming work (Q80).
4. [REQ-031] *Given* a Case whose Origin is blank or carries a value outside the three known ones,
  *When* a save is attempted without the `Bypass_Case_Intake_Validation` permission,
  *Then* the save fails on Origin with "Set Origin to Email-Support, Email-Billing or Web
  before saving this case."

### US-CASE-002 — Billing specialist receives a finance email in the Billing queue

**As a** Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`,
**I want** a customer email arriving at `billing@acme.example` to land in the Billing queue
rather than in general support,
**So that** finance queries are worked by the two finance staff who can answer them instead
of being triaged twice and answered late.

1. [REQ-005, REQ-024, REQ-034, REQ-036, REQ-053] *Given* the `billing@acme.example` routing address is live and I hold `PSG_Billing_Prod`,
  *When* a customer sends mail to that address,
  *Then* a Case exists with Origin `Email-Billing` and Owner the `Billing` queue, and it
  appears in my `Billing_Queue` list view.
2. [REQ-024] *Given* that Case is open in the Billing queue,
  *When* I open it,
  *Then* it carries the Billing record type and its page shows no severity concept.
3. [no req_id in story-backlog.md's matrix] *Given* the same Case,
  *When* a Tier 1 support agent opens its record id directly,
  *Then* access is denied — Case OWD is Private and no sharing rule targets `Billing_Team`
  or the Billing record type.
4. [no req_id in story-backlog.md's matrix] *Given* a finance case whose Origin was never stamped,
  *When* a save is attempted without the bypass permission,
  *Then* the save fails on Origin with the Origin error message and the case is not routed.

### US-CASE-003 — Tier 1 agent receives a web-form case through the fall-through entry

**As a** Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`,
**I want** a case submitted on the public website form to reach my queue with an
acknowledgement already sent,
**So that** the roughly 60 web submissions a day are worked on the same one-minute promise
as email and none of them sits unowned.

1. [REQ-005, REQ-035, REQ-036, REQ-053] *Given* Web-to-Case is enabled and the website form posts the contract M3-S03 defines,
  *When* a visitor submits the form,
  *Then* a Case exists with Origin `Web` and Owner the `Tier_1_General` queue, reached
  through the assignment rule's catch-all entry rather than through a criteria match.
2. [REQ-032, REQ-037, REQ-055] *Given* that Case has just been created,
  *When* the submitter reads their mailbox,
  *Then* one acknowledgement carrying the case number has arrived from
  `support-noreply@acme.example`.
3. [REQ-035] *Given* the website form omits a field the Case validation rules read,
  *When* the submission is processed,
  *Then* the save is blocked and the case never appears in the queue — the web channel
  holds no bypass permission.
4. [no req_id in story-backlog.md's matrix] *Given* a web case is in the queue,
  *When* a Billing specialist opens its record id directly,
  *Then* access is denied: the Support record type is shared only to `Support_Tier_2`.

### US-CASE-004 — Tier 1 agent logs a case by hand and it routes like the other two channels

**As a** Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`,
**I want** a case I type in myself to route and acknowledge exactly as an emailed one does,
**So that** the roughly 20 cases a day we log by hand are not the ones that quietly get no
owner, no clock and no acknowledgement.

1. [REQ-013, REQ-036, REQ-053] *Given* I am on a Case page and the layout shows "Assign using active assignment rule",
  *When* I tick that box and save,
  *Then* Owner becomes the `Tier_1_General` queue and one acknowledgement is sent.
2. [REQ-013] *Given* the same new Case,
  *When* I leave that box unticked and save,
  *Then* the Case remains owned by me and no acknowledgement is sent — the box is shown but
  is **not** pre-ticked, and nothing in this build pre-ticks it.
3. [REQ-030] *Given* I am creating a Case and have left Priority empty,
  *When* I save,
  *Then* the save fails on Priority with "Set a Priority before saving this case."
4. [REQ-031] *Given* I am creating a Case and have left Origin empty,
  *When* I save,
  *Then* the save fails on Origin with the Origin error message.

### US-CASE-005 — Tier 1 agent is refused a Billing case, and can prove it

**As a** Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`,
**I want** a Billing case to be genuinely unreachable for me rather than merely absent from
my list views,
**So that** finance data is confined to the two staff who are meant to see it and the
restriction survives someone pasting a record id into a URL.

1. [REQ-010, REQ-020, REQ-054] *Given* a Case of the Billing record type owned by the `Billing` queue,
  *When* I open its record id directly in Lightning desktop,
  *Then* access is denied at the record, not merely hidden — I am not the owner, not a
  `Billing` queue member, and no sharing rule names `Billing_Team` or the Billing type.
2. [REQ-010] *Given* the same Billing case,
  *When* I search for it and when I open every Case list view available to me,
  *Then* no row is shown for it in any of them.
3. [REQ-010, REQ-020, REQ-028] *Given* my `PSG_Tier1_Prod` assignment,
  *When* the assignment is inspected,
  *Then* it grants the Billing record type neither as default nor as visible, and grants no
  `View All` or `Modify All` on Case.
4. [REQ-029] *Given* a Support case I do not own,
  *When* I open it,
  *Then* I can work it — proving the refusal above is record-scoped and has not broken the
  access this persona does need.

### US-CASE-006 — Tier 2 engineer works an escalated Support case they do not own

**As a** Tier 2 support engineer on the `Acme Support Tier 2` profile holding
`PSG_Tier2_Prod`,
**I want** to open and edit any Support case whoever owns it, and to pick my work from a
list,
**So that** an escalation reaches an engineer who can act on it immediately instead of
waiting for a manual share.

1. [REQ-019, REQ-029] *Given* a Support case owned by the `Tier_1_General` queue,
  *When* I open it,
  *Then* I can edit it — the `Support_Cases_To_Tier_2` criteria rule shares every Support
  case to the `Support_Tier_2` group at Edit, including records owned by others.
2. [REQ-023, REQ-048] *Given* I am starting my shift,
  *When* I open the `Tier_2_Queue` list view,
  *Then* it lists the cases waiting in `Tier_2_Engineering` and is the surface I work from.
3. [REQ-029, REQ-054] *Given* a Case of the Billing record type,
  *When* I open its record id directly,
  *Then* access is denied — the sharing rule filters on `RecordTypeId equals Support` and
  nothing extends Billing cases to this group.
4. [REQ-019] *Given* a Support case owned by the Automated Process identity at intake,
  *When* I open it before any assignment has landed,
  *Then* I can still edit it, because the rule includes records owned by all users.

### US-CASE-007 — Tier 1 agent sees a first-response clock on the right calendar

**As a** Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`,
**I want** a new case to arrive with its SLA clock already running against the calendar its
account's region implies,
**So that** a Premier customer in London is measured on London hours rather than on New York
hours and we do not report a breach that never happened.

1. [REQ-040, REQ-045] *Given* an account whose contracted tier is Premier,
  *When* a case is created against it,
  *Then* the first-response target is 4 business hours, on the `First_Response_Premier`
  process.
2. [REQ-041, REQ-045] *Given* an account on the standard tier,
  *When* a case is created against it,
  *Then* the first-response target is 1 business day, on the `First_Response_Standard`
  process.
3. [REQ-038] *Given* a case created at 17:00 London time on a Friday,
  *When* the clock is read on Saturday and again on Monday morning,
  *Then* it has not ticked over the weekend and the remaining time is unchanged.
4. [REQ-038] *Given* a case created on a date the calendar lists as a holiday,
  *When* the clock is read the next working morning,
  *Then* the holiday did not consume any of the target.
5. [REQ-045] *Given* a case created against no account at all,
  *When* it saves,
  *Then* it saves — the stamp falls back rather than blocking intake.

### US-CASE-008 — Tier 2 engineer receives a case that went untouched for 8 business hours

**As a** Tier 2 support engineer on the `Acme Support Tier 2` profile holding
`PSG_Tier2_Prod`,
**I want** an untouched support case to arrive in my queue with a handover notice of its
own,
**So that** nothing sits unworked for a day and the handover is visible to a human rather
than inferred from a changed owner field.

1. [REQ-023, REQ-033, REQ-043] *Given* an open Support case created 8 business hours ago and not touched since,
  *When* the escalation rule is active and evaluates it,
  *Then* it is reassigned to `Tier_2_Engineering` and the Tier 2 handover notice is sent —
  a notice distinct from the customer acknowledgement.
2. [REQ-043] *Given* an open case flagged `Severity 1`,
  *When* 8 elapsed hours pass across a weekend,
  *Then* it escalates anyway, because that entry runs on no calendar and observes no
  holidays.
3. [REQ-043] *Given* a case that was closed inside the window,
  *When* the rule evaluates,
  *Then* no escalation fires and no reassignment is made — closed cases are excluded by an
  explicit criterion, not by assumption.
4. [REQ-043] *Given* the rule as this build ships it,
  *When* a tester looks for an escalation at all,
  *Then* none occurs, because the rule is deliberately inactive and activation is a separate
  deploy inside an agreed comparison window.

### US-CASE-009 — Tier 1 agent's first reply stops the first-response clock

**As a** Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`,
**I want** the First Response milestone to close when I actually start work on a case,
**So that** our SLA reporting measures response rather than measuring whether someone
remembered to close a milestone by hand.

1. [REQ-042, REQ-044] *Given* an open case with a running First Response milestone and Status `New`,
  *When* I move Status off `New`,
  *Then* the milestone's completion date is stamped and the clock stops.
2. [REQ-042] *Given* a case whose Status is already off `New`,
  *When* I edit any other field,
  *Then* no second completion is stamped and the existing completion date is unchanged.
3. [no req_id in story-backlog.md's matrix] *Given* a case with no entitlement attached and therefore no running milestone,
  *When* I move Status off `New`,
  *Then* the edit saves and nothing errors.
4. [no req_id in story-backlog.md's matrix] *Given* 200 cases updated at once,
  *When* Status moves off `New` on all of them,
  *Then* every one completes without a limit error.

### US-CASE-010 — Billing specialist works from the Billing queue list view

**As a** Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`,
**I want** one list that shows the finance cases waiting to be picked up,
**So that** two people can cover the queue without asking each other what is outstanding.

1. [REQ-048, REQ-049] *Given* I hold `PSG_Billing_Prod`,
  *When* I open the `Billing_Queue` list view on Case,
  *Then* it lists the open cases owned by the `Billing` queue and is the surface I pick work
  from — Billing pulls, it is not pushed to.
2. [REQ-054] *Given* a Support case is open in another queue,
  *When* I look at that same list view,
  *Then* no row is shown for it, and opening its record id is denied.
3. [REQ-049] *Given* I take a case from the list,
  *When* ownership moves from the queue to me,
  *Then* it leaves the queue list view, so the list shows what is genuinely unclaimed.

### US-CASE-011 — Tier 2 lead reviews escalated open cases weekly

**As a** Tier 2 support engineer acting as the Tier 2 lead, on the `Acme Support Tier 2`
profile holding `PSG_Tier2_Prod`,
**I want** a saved report I can open every week without rebuilding it,
**So that** we can confirm next month that the escalation path is still firing, rather than
discovering months later that it silently stopped.

1. [REQ-051] *Given* I hold `PSG_Tier2_Prod`,
  *When* I open `Escalated_Open_Cases` in the `Support_Operations` folder,
  *Then* it runs and returns open Cases opened in the last 30 days.
2. [REQ-051] *Given* the report as this build ships it,
  *When* I compare its rows against the cases the escalation engine actually flagged,
  *Then* it **over-reports** — the Escalated criterion is absent from the file and its own
  description says so.
3. [no req_id in story-backlog.md's matrix] *Given* a Tier 1 support agent,
  *When* they open the same report folder,
  *Then* folder access governs what they see, and Billing cases remain unreachable to them
  through a report exactly as they are through a list view.

---

## Lintable record

```yaml
project: "Acme Software Case Onboarding on Service Cloud — M5"
acceptance_criteria:
  - ac_id: AC-005.1
    req_id: REQ-005
    story_id: US-CASE-001
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`StandardValueSet:CaseOrigin`"
    test_type: manual
    negative: false
    given: "the `support@acme.example` routing address is live and I hold `PSG_Tier1_Prod`"
    when: "a customer sends mail to that address"
    then: "a Case exists with Origin `Email-Support`, Owner the `Tier_1_General` queue, and it appears in my `Tier_1_General_Queue` list view."
    proof: "Tester's direct observation on the US-CASE-001 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-034, REQ-036, REQ-050, REQ-053]

  - ac_id: AC-005.2
    req_id: REQ-005
    story_id: US-CASE-002
    persona: "Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`StandardValueSet:CaseOrigin`"
    test_type: manual
    negative: false
    given: "the `billing@acme.example` routing address is live and I hold `PSG_Billing_Prod`"
    when: "a customer sends mail to that address"
    then: "a Case exists with Origin `Email-Billing` and Owner the `Billing` queue, and it appears in my `Billing_Queue` list view."
    proof: "Tester's direct observation on the US-CASE-002 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-024, REQ-034, REQ-036, REQ-053]

  - ac_id: AC-005.3
    req_id: REQ-005
    story_id: US-CASE-003
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`StandardValueSet:CaseOrigin`"
    test_type: manual
    negative: false
    given: "Web-to-Case is enabled and the website form posts the contract M3-S03 defines"
    when: "a visitor submits the form"
    then: "a Case exists with Origin `Web` and Owner the `Tier_1_General` queue, reached through the assignment rule's catch-all entry rather than through a criteria match."
    proof: "Tester's direct observation on the US-CASE-003 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-035, REQ-036, REQ-053]

  - ac_id: AC-010.1
    req_id: REQ-010
    story_id: US-CASE-005
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`CustomObject:Case`"
    test_type: manual
    negative: true
    given: "a Case of the Billing record type owned by the `Billing` queue"
    when: "I open its record id directly in Lightning desktop"
    then: "access is denied at the record, not merely hidden — I am not the owner, not a `Billing` queue member, and no sharing rule names `Billing_Team` or the Billing type."
    proof: "Tester's direct observation on the US-CASE-005 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-020, REQ-054]

  - ac_id: AC-010.2
    req_id: REQ-010
    story_id: US-CASE-005
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`CustomObject:Case`"
    test_type: manual
    negative: true
    given: "the same Billing case"
    when: "I search for it and when I open every Case list view available to me"
    then: "no row is shown for it in any of them."
    proof: "Tester's direct observation on the US-CASE-005 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-010.3
    req_id: REQ-010
    story_id: US-CASE-005
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`CustomObject:Case`"
    test_type: manual
    negative: true
    given: "my `PSG_Tier1_Prod` assignment"
    when: "the assignment is inspected"
    then: "it grants the Billing record type neither as default nor as visible, and grants no `View All` or `Modify All` on Case."
    proof: "Tester's direct observation on the US-CASE-005 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-020, REQ-028]

  - ac_id: AC-013.1
    req_id: REQ-013
    story_id: US-CASE-004
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Layout:Case-Case Support Layout` \\| `Layout:Case-Case Billing Layout`"
    test_type: manual
    negative: false
    given: "I am on a Case page and the layout shows \"Assign using active assignment rule\""
    when: "I tick that box and save"
    then: "Owner becomes the `Tier_1_General` queue and one acknowledgement is sent."
    proof: "Tester's direct observation on the US-CASE-004 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-036, REQ-053]

  - ac_id: AC-013.2
    req_id: REQ-013
    story_id: US-CASE-004
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Layout:Case-Case Support Layout` \\| `Layout:Case-Case Billing Layout`"
    test_type: manual
    negative: true
    given: "the same new Case"
    when: "I leave that box unticked and save"
    then: "the Case remains owned by me and no acknowledgement is sent — the box is shown but is **not** pre-ticked, and nothing in this build pre-ticks it."
    proof: "Tester's direct observation on the US-CASE-004 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-019.1
    req_id: REQ-019
    story_id: US-CASE-006
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`PermissionSet:Case_Tier2` \\| `PermissionSetGroup:PSG_Tier2_Prod`"
    test_type: manual
    negative: false
    given: "a Support case owned by the `Tier_1_General` queue"
    when: "I open it"
    then: "I can edit it — the `Support_Cases_To_Tier_2` criteria rule shares every Support case to the `Support_Tier_2` group at Edit, including records owned by others."
    proof: "Tester's direct observation on the US-CASE-006 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-029]

  - ac_id: AC-019.2
    req_id: REQ-019
    story_id: US-CASE-006
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`PermissionSet:Case_Tier2` \\| `PermissionSetGroup:PSG_Tier2_Prod`"
    test_type: manual
    negative: false
    given: "a Support case owned by the Automated Process identity at intake"
    when: "I open it before any assignment has landed"
    then: "I can still edit it, because the rule includes records owned by all users."
    proof: "Tester's direct observation on the US-CASE-006 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-020.1
    req_id: REQ-020
    story_id: US-CASE-005
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`PermissionSet:Case_Tier1` \\| `PermissionSetGroup:PSG_Tier1_Prod`"
    test_type: manual
    negative: true
    given: "a Case of the Billing record type owned by the `Billing` queue"
    when: "I open its record id directly in Lightning desktop"
    then: "access is denied at the record, not merely hidden — I am not the owner, not a `Billing` queue member, and no sharing rule names `Billing_Team` or the Billing type."
    proof: "Tester's direct observation on the US-CASE-005 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-020, REQ-054]

  - ac_id: AC-020.2
    req_id: REQ-020
    story_id: US-CASE-005
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`PermissionSet:Case_Tier1` \\| `PermissionSetGroup:PSG_Tier1_Prod`"
    test_type: manual
    negative: true
    given: "my `PSG_Tier1_Prod` assignment"
    when: "the assignment is inspected"
    then: "it grants the Billing record type neither as default nor as visible, and grants no `View All` or `Modify All` on Case."
    proof: "Tester's direct observation on the US-CASE-005 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-020, REQ-028]

  - ac_id: AC-023.1
    req_id: REQ-023
    story_id: US-CASE-006
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Queue:Tier_2_Engineering` \\| `Group:Support_Tier_2`"
    test_type: manual
    negative: false
    given: "I am starting my shift"
    when: "I open the `Tier_2_Queue` list view"
    then: "it lists the cases waiting in `Tier_2_Engineering` and is the surface I work from."
    proof: "Tester's direct observation on the US-CASE-006 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-048]

  - ac_id: AC-023.2
    req_id: REQ-023
    story_id: US-CASE-008
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Queue:Tier_2_Engineering` \\| `Group:Support_Tier_2`"
    test_type: manual
    negative: false
    given: "an open Support case created 8 business hours ago and not touched since"
    when: "the escalation rule is active and evaluates it"
    then: "it is reassigned to `Tier_2_Engineering` and the Tier 2 handover notice is sent — a notice distinct from the customer acknowledgement."
    proof: "Tester's direct observation on the US-CASE-008 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-033, REQ-043]

  - ac_id: AC-024.1
    req_id: REQ-024
    story_id: US-CASE-002
    persona: "Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Queue:Billing` \\| `Group:Billing_Team`"
    test_type: manual
    negative: false
    given: "the `billing@acme.example` routing address is live and I hold `PSG_Billing_Prod`"
    when: "a customer sends mail to that address"
    then: "a Case exists with Origin `Email-Billing` and Owner the `Billing` queue, and it appears in my `Billing_Queue` list view."
    proof: "Tester's direct observation on the US-CASE-002 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-024, REQ-034, REQ-036, REQ-053]

  - ac_id: AC-024.2
    req_id: REQ-024
    story_id: US-CASE-002
    persona: "Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Queue:Billing` \\| `Group:Billing_Team`"
    test_type: manual
    negative: false
    given: "that Case is open in the Billing queue"
    when: "I open it"
    then: "it carries the Billing record type and its page shows no severity concept."
    proof: "Tester's direct observation on the US-CASE-002 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-028.1
    req_id: REQ-028
    story_id: US-CASE-005
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`CustomObject:Case`"
    test_type: manual
    negative: true
    given: "my `PSG_Tier1_Prod` assignment"
    when: "the assignment is inspected"
    then: "it grants the Billing record type neither as default nor as visible, and grants no `View All` or `Modify All` on Case."
    proof: "Tester's direct observation on the US-CASE-005 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-020, REQ-028]

  - ac_id: AC-029.1
    req_id: REQ-029
    story_id: US-CASE-005
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`SharingRules:Case`"
    test_type: manual
    negative: false
    given: "a Support case I do not own"
    when: "I open it"
    then: "I can work it — proving the refusal above is record-scoped and has not broken the access this persona does need."
    proof: "Tester's direct observation on the US-CASE-005 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-029.2
    req_id: REQ-029
    story_id: US-CASE-006
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`SharingRules:Case`"
    test_type: manual
    negative: false
    given: "a Support case owned by the `Tier_1_General` queue"
    when: "I open it"
    then: "I can edit it — the `Support_Cases_To_Tier_2` criteria rule shares every Support case to the `Support_Tier_2` group at Edit, including records owned by others."
    proof: "Tester's direct observation on the US-CASE-006 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-029]

  - ac_id: AC-029.3
    req_id: REQ-029
    story_id: US-CASE-006
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`SharingRules:Case`"
    test_type: manual
    negative: true
    given: "a Case of the Billing record type"
    when: "I open its record id directly"
    then: "access is denied — the sharing rule filters on `RecordTypeId equals Support` and nothing extends Billing cases to this group."
    proof: "Tester's direct observation on the US-CASE-006 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-054]

  - ac_id: AC-030.1
    req_id: REQ-030
    story_id: US-CASE-004
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`ValidationRule:Case.Priority_Required_On_Agent_Save`"
    test_type: manual
    negative: true
    given: "I am creating a Case and have left Priority empty"
    when: "I save"
    then: "the save fails on Priority with \"Set a Priority before saving this case.\""
    proof: "Tester's direct observation on the US-CASE-004 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-031.1
    req_id: REQ-031
    story_id: US-CASE-001
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`ValidationRule:Case.Origin_Must_Be_Known`"
    test_type: manual
    negative: false
    given: "a Case whose Origin is blank or carries a value outside the three known ones"
    when: "a save is attempted without the `Bypass_Case_Intake_Validation` permission"
    then: "the save fails on Origin with \"Set Origin to Email-Support, Email-Billing or Web before saving this case.\""
    proof: "Tester's direct observation on the US-CASE-001 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-031.2
    req_id: REQ-031
    story_id: US-CASE-004
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`ValidationRule:Case.Origin_Must_Be_Known`"
    test_type: manual
    negative: true
    given: "I am creating a Case and have left Origin empty"
    when: "I save"
    then: "the save fails on Origin with the Origin error message."
    proof: "Tester's direct observation on the US-CASE-004 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-032.1
    req_id: REQ-032
    story_id: US-CASE-001
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EmailTemplate:case_intake/Case_Acknowledgement`"
    test_type: manual
    negative: false
    given: "that same Case has just been created"
    when: "I read the customer's mailbox"
    then: "one acknowledgement has arrived from `support-noreply@acme.example` with sender name `Acme Support`, carrying the case number, and exactly one — not two."
    proof: "Tester's direct observation on the US-CASE-001 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-037, REQ-055]

  - ac_id: AC-032.2
    req_id: REQ-032
    story_id: US-CASE-003
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EmailTemplate:case_intake/Case_Acknowledgement`"
    test_type: manual
    negative: false
    given: "that Case has just been created"
    when: "the submitter reads their mailbox"
    then: "one acknowledgement carrying the case number has arrived from `support-noreply@acme.example`."
    proof: "Tester's direct observation on the US-CASE-003 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-037, REQ-055]

  - ac_id: AC-033.1
    req_id: REQ-033
    story_id: US-CASE-008
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EmailTemplate:case_intake/Case_Escalated_To_Tier2`"
    test_type: manual
    negative: false
    given: "an open Support case created 8 business hours ago and not touched since"
    when: "the escalation rule is active and evaluates it"
    then: "it is reassigned to `Tier_2_Engineering` and the Tier 2 handover notice is sent — a notice distinct from the customer acknowledgement."
    proof: "Tester's direct observation on the US-CASE-008 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-033, REQ-043]

  - ac_id: AC-034.1
    req_id: REQ-034
    story_id: US-CASE-001
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AssignmentRules:Case`"
    test_type: manual
    negative: false
    given: "the `support@acme.example` routing address is live and I hold `PSG_Tier1_Prod`"
    when: "a customer sends mail to that address"
    then: "a Case exists with Origin `Email-Support`, Owner the `Tier_1_General` queue, and it appears in my `Tier_1_General_Queue` list view."
    proof: "Tester's direct observation on the US-CASE-001 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-034, REQ-036, REQ-050, REQ-053]

  - ac_id: AC-034.2
    req_id: REQ-034
    story_id: US-CASE-002
    persona: "Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AssignmentRules:Case`"
    test_type: manual
    negative: false
    given: "the `billing@acme.example` routing address is live and I hold `PSG_Billing_Prod`"
    when: "a customer sends mail to that address"
    then: "a Case exists with Origin `Email-Billing` and Owner the `Billing` queue, and it appears in my `Billing_Queue` list view."
    proof: "Tester's direct observation on the US-CASE-002 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-024, REQ-034, REQ-036, REQ-053]

  - ac_id: AC-035.1
    req_id: REQ-035
    story_id: US-CASE-003
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Settings:Case` (Web-to-Case)"
    test_type: manual
    negative: false
    given: "Web-to-Case is enabled and the website form posts the contract M3-S03 defines"
    when: "a visitor submits the form"
    then: "a Case exists with Origin `Web` and Owner the `Tier_1_General` queue, reached through the assignment rule's catch-all entry rather than through a criteria match."
    proof: "Tester's direct observation on the US-CASE-003 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-035, REQ-036, REQ-053]

  - ac_id: AC-035.2
    req_id: REQ-035
    story_id: US-CASE-003
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Settings:Case` (Web-to-Case)"
    test_type: manual
    negative: true
    given: "the website form omits a field the Case validation rules read"
    when: "the submission is processed"
    then: "the save is blocked and the case never appears in the queue — the web channel holds no bypass permission."
    proof: "Tester's direct observation on the US-CASE-003 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-036.1
    req_id: REQ-036
    story_id: US-CASE-001
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AssignmentRules:Case`"
    test_type: manual
    negative: false
    given: "the `support@acme.example` routing address is live and I hold `PSG_Tier1_Prod`"
    when: "a customer sends mail to that address"
    then: "a Case exists with Origin `Email-Support`, Owner the `Tier_1_General` queue, and it appears in my `Tier_1_General_Queue` list view."
    proof: "Tester's direct observation on the US-CASE-001 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-034, REQ-036, REQ-050, REQ-053]

  - ac_id: AC-036.2
    req_id: REQ-036
    story_id: US-CASE-002
    persona: "Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AssignmentRules:Case`"
    test_type: manual
    negative: false
    given: "the `billing@acme.example` routing address is live and I hold `PSG_Billing_Prod`"
    when: "a customer sends mail to that address"
    then: "a Case exists with Origin `Email-Billing` and Owner the `Billing` queue, and it appears in my `Billing_Queue` list view."
    proof: "Tester's direct observation on the US-CASE-002 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-024, REQ-034, REQ-036, REQ-053]

  - ac_id: AC-036.3
    req_id: REQ-036
    story_id: US-CASE-003
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AssignmentRules:Case`"
    test_type: manual
    negative: false
    given: "Web-to-Case is enabled and the website form posts the contract M3-S03 defines"
    when: "a visitor submits the form"
    then: "a Case exists with Origin `Web` and Owner the `Tier_1_General` queue, reached through the assignment rule's catch-all entry rather than through a criteria match."
    proof: "Tester's direct observation on the US-CASE-003 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-035, REQ-036, REQ-053]

  - ac_id: AC-036.4
    req_id: REQ-036
    story_id: US-CASE-004
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AssignmentRules:Case`"
    test_type: manual
    negative: false
    given: "I am on a Case page and the layout shows \"Assign using active assignment rule\""
    when: "I tick that box and save"
    then: "Owner becomes the `Tier_1_General` queue and one acknowledgement is sent."
    proof: "Tester's direct observation on the US-CASE-004 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-036, REQ-053]

  - ac_id: AC-037.1
    req_id: REQ-037
    story_id: US-CASE-001
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AutoResponseRules:Case`"
    test_type: manual
    negative: false
    given: "that same Case has just been created"
    when: "I read the customer's mailbox"
    then: "one acknowledgement has arrived from `support-noreply@acme.example` with sender name `Acme Support`, carrying the case number, and exactly one — not two."
    proof: "Tester's direct observation on the US-CASE-001 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-037, REQ-055]

  - ac_id: AC-037.2
    req_id: REQ-037
    story_id: US-CASE-003
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AutoResponseRules:Case`"
    test_type: manual
    negative: false
    given: "that Case has just been created"
    when: "the submitter reads their mailbox"
    then: "one acknowledgement carrying the case number has arrived from `support-noreply@acme.example`."
    proof: "Tester's direct observation on the US-CASE-003 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-037, REQ-055]

  - ac_id: AC-038.1
    req_id: REQ-038
    story_id: US-CASE-007
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Settings:BusinessHours`"
    test_type: manual
    negative: false
    given: "a case created at 17:00 London time on a Friday"
    when: "the clock is read on Saturday and again on Monday morning"
    then: "it has not ticked over the weekend and the remaining time is unchanged."
    proof: "Tester's direct observation on the US-CASE-007 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-038.2
    req_id: REQ-038
    story_id: US-CASE-007
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Settings:BusinessHours`"
    test_type: manual
    negative: false
    given: "a case created on a date the calendar lists as a holiday"
    when: "the clock is read the next working morning"
    then: "the holiday did not consume any of the target."
    proof: "Tester's direct observation on the US-CASE-007 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-040.1
    req_id: REQ-040
    story_id: US-CASE-007
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EntitlementProcess:First_Response_Premier`"
    test_type: manual
    negative: false
    given: "an account whose contracted tier is Premier"
    when: "a case is created against it"
    then: "the first-response target is 4 business hours, on the `First_Response_Premier` process."
    proof: "Tester's direct observation on the US-CASE-007 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-045]

  - ac_id: AC-041.1
    req_id: REQ-041
    story_id: US-CASE-007
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EntitlementProcess:First_Response_Standard`"
    test_type: manual
    negative: false
    given: "an account on the standard tier"
    when: "a case is created against it"
    then: "the first-response target is 1 business day, on the `First_Response_Standard` process."
    proof: "Tester's direct observation on the US-CASE-007 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-045]

  - ac_id: AC-042.1
    req_id: REQ-042
    story_id: US-CASE-009
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`MilestoneType:First Response`"
    test_type: manual
    negative: false
    given: "an open case with a running First Response milestone and Status `New`"
    when: "I move Status off `New`"
    then: "the milestone's completion date is stamped and the clock stops."
    proof: "Tester's direct observation on the US-CASE-009 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-044]

  - ac_id: AC-042.2
    req_id: REQ-042
    story_id: US-CASE-009
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`MilestoneType:First Response`"
    test_type: manual
    negative: false
    given: "a case whose Status is already off `New`"
    when: "I edit any other field"
    then: "no second completion is stamped and the existing completion date is unchanged."
    proof: "Tester's direct observation on the US-CASE-009 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-043.1
    req_id: REQ-043
    story_id: US-CASE-008
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EscalationRules:Case`"
    test_type: manual
    negative: false
    given: "an open Support case created 8 business hours ago and not touched since"
    when: "the escalation rule is active and evaluates it"
    then: "it is reassigned to `Tier_2_Engineering` and the Tier 2 handover notice is sent — a notice distinct from the customer acknowledgement."
    proof: "Tester's direct observation on the US-CASE-008 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-033, REQ-043]

  - ac_id: AC-043.2
    req_id: REQ-043
    story_id: US-CASE-008
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EscalationRules:Case`"
    test_type: manual
    negative: false
    given: "an open case flagged `Severity 1`"
    when: "8 elapsed hours pass across a weekend"
    then: "it escalates anyway, because that entry runs on no calendar and observes no holidays."
    proof: "Tester's direct observation on the US-CASE-008 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-043.3
    req_id: REQ-043
    story_id: US-CASE-008
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EscalationRules:Case`"
    test_type: manual
    negative: true
    given: "a case that was closed inside the window"
    when: "the rule evaluates"
    then: "no escalation fires and no reassignment is made — closed cases are excluded by an explicit criterion, not by assumption."
    proof: "Tester's direct observation on the US-CASE-008 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-043.4
    req_id: REQ-043
    story_id: US-CASE-008
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EscalationRules:Case`"
    test_type: manual
    negative: true
    given: "the rule as this build ships it"
    when: "a tester looks for an escalation at all"
    then: "none occurs, because the rule is deliberately inactive and activation is a separate deploy inside an agreed comparison window."
    proof: "Tester's direct observation on the US-CASE-008 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-044.1
    req_id: REQ-044
    story_id: US-CASE-009
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`ApexTrigger:CaseMilestoneTrigger`"
    test_type: manual
    negative: false
    given: "an open case with a running First Response milestone and Status `New`"
    when: "I move Status off `New`"
    then: "the milestone's completion date is stamped and the clock stops."
    proof: "Tester's direct observation on the US-CASE-009 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-044]

  - ac_id: AC-045.1
    req_id: REQ-045
    story_id: US-CASE-007
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Flow:Case_BeforeSave_StampEntitlementAndCalendar`"
    test_type: manual
    negative: false
    given: "an account whose contracted tier is Premier"
    when: "a case is created against it"
    then: "the first-response target is 4 business hours, on the `First_Response_Premier` process."
    proof: "Tester's direct observation on the US-CASE-007 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-045]

  - ac_id: AC-045.2
    req_id: REQ-045
    story_id: US-CASE-007
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Flow:Case_BeforeSave_StampEntitlementAndCalendar`"
    test_type: manual
    negative: false
    given: "an account on the standard tier"
    when: "a case is created against it"
    then: "the first-response target is 1 business day, on the `First_Response_Standard` process."
    proof: "Tester's direct observation on the US-CASE-007 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-045]

  - ac_id: AC-045.3
    req_id: REQ-045
    story_id: US-CASE-007
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Flow:Case_BeforeSave_StampEntitlementAndCalendar`"
    test_type: manual
    negative: false
    given: "a case created against no account at all"
    when: "it saves"
    then: "it saves — the stamp falls back rather than blocking intake."
    proof: "Tester's direct observation on the US-CASE-007 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-048.1
    req_id: REQ-048
    story_id: US-CASE-006
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`ListView:Case.Tier_2_Queue`"
    test_type: manual
    negative: false
    given: "I am starting my shift"
    when: "I open the `Tier_2_Queue` list view"
    then: "it lists the cases waiting in `Tier_2_Engineering` and is the surface I work from."
    proof: "Tester's direct observation on the US-CASE-006 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-048]

  - ac_id: AC-048.2
    req_id: REQ-048
    story_id: US-CASE-010
    persona: "Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`ListView:Case.Tier_2_Queue`"
    test_type: manual
    negative: false
    given: "I hold `PSG_Billing_Prod`"
    when: "I open the `Billing_Queue` list view on Case"
    then: "it lists the open cases owned by the `Billing` queue and is the surface I pick work from — Billing pulls, it is not pushed to."
    proof: "Tester's direct observation on the US-CASE-010 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-049]

  - ac_id: AC-049.1
    req_id: REQ-049
    story_id: US-CASE-010
    persona: "Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`ListView:Case.Billing_Queue`"
    test_type: manual
    negative: false
    given: "I hold `PSG_Billing_Prod`"
    when: "I open the `Billing_Queue` list view on Case"
    then: "it lists the open cases owned by the `Billing` queue and is the surface I pick work from — Billing pulls, it is not pushed to."
    proof: "Tester's direct observation on the US-CASE-010 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-049]

  - ac_id: AC-049.2
    req_id: REQ-049
    story_id: US-CASE-010
    persona: "Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`ListView:Case.Billing_Queue`"
    test_type: manual
    negative: false
    given: "I take a case from the list"
    when: "ownership moves from the queue to me"
    then: "it leaves the queue list view, so the list shows what is genuinely unclaimed."
    proof: "Tester's direct observation on the US-CASE-010 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-050.1
    req_id: REQ-050
    story_id: US-CASE-001
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`ListView:Case.Tier_1_General_Queue`"
    test_type: manual
    negative: false
    given: "the `support@acme.example` routing address is live and I hold `PSG_Tier1_Prod`"
    when: "a customer sends mail to that address"
    then: "a Case exists with Origin `Email-Support`, Owner the `Tier_1_General` queue, and it appears in my `Tier_1_General_Queue` list view."
    proof: "Tester's direct observation on the US-CASE-001 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-034, REQ-036, REQ-050, REQ-053]

  - ac_id: AC-051.1
    req_id: REQ-051
    story_id: US-CASE-011
    persona: "Tier 2 support engineer acting as the Tier 2 lead, on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Report:Support_Operations/Escalated_Open_Cases`"
    test_type: manual
    negative: false
    given: "I hold `PSG_Tier2_Prod`"
    when: "I open `Escalated_Open_Cases` in the `Support_Operations` folder"
    then: "it runs and returns open Cases opened in the last 30 days."
    proof: "Tester's direct observation on the US-CASE-011 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-051.2
    req_id: REQ-051
    story_id: US-CASE-011
    persona: "Tier 2 support engineer acting as the Tier 2 lead, on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Report:Support_Operations/Escalated_Open_Cases`"
    test_type: manual
    negative: false
    given: "the report as this build ships it"
    when: "I compare its rows against the cases the escalation engine actually flagged"
    then: "it **over-reports** — the Escalated criterion is absent from the file and its own description says so."
    proof: "Tester's direct observation on the US-CASE-011 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-053.1
    req_id: REQ-053
    story_id: US-CASE-001
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AssignmentRules:Case`"
    test_type: manual
    negative: false
    given: "the `support@acme.example` routing address is live and I hold `PSG_Tier1_Prod`"
    when: "a customer sends mail to that address"
    then: "a Case exists with Origin `Email-Support`, Owner the `Tier_1_General` queue, and it appears in my `Tier_1_General_Queue` list view."
    proof: "Tester's direct observation on the US-CASE-001 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-034, REQ-036, REQ-050, REQ-053]

  - ac_id: AC-053.2
    req_id: REQ-053
    story_id: US-CASE-002
    persona: "Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AssignmentRules:Case`"
    test_type: manual
    negative: false
    given: "the `billing@acme.example` routing address is live and I hold `PSG_Billing_Prod`"
    when: "a customer sends mail to that address"
    then: "a Case exists with Origin `Email-Billing` and Owner the `Billing` queue, and it appears in my `Billing_Queue` list view."
    proof: "Tester's direct observation on the US-CASE-002 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-024, REQ-034, REQ-036, REQ-053]

  - ac_id: AC-053.3
    req_id: REQ-053
    story_id: US-CASE-003
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AssignmentRules:Case`"
    test_type: manual
    negative: false
    given: "Web-to-Case is enabled and the website form posts the contract M3-S03 defines"
    when: "a visitor submits the form"
    then: "a Case exists with Origin `Web` and Owner the `Tier_1_General` queue, reached through the assignment rule's catch-all entry rather than through a criteria match."
    proof: "Tester's direct observation on the US-CASE-003 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-035, REQ-036, REQ-053]

  - ac_id: AC-053.4
    req_id: REQ-053
    story_id: US-CASE-004
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AssignmentRules:Case`"
    test_type: manual
    negative: false
    given: "I am on a Case page and the layout shows \"Assign using active assignment rule\""
    when: "I tick that box and save"
    then: "Owner becomes the `Tier_1_General` queue and one acknowledgement is sent."
    proof: "Tester's direct observation on the US-CASE-004 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-036, REQ-053]

  - ac_id: AC-054.1
    req_id: REQ-054
    story_id: US-CASE-001
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`CustomObject:Case` (record-level sharing/OWD)"
    test_type: manual
    negative: true
    given: "mail arrives from a sender the org does not authorise"
    when: "the routing address processes it"
    then: "no Case is created and the mail bounces rather than becoming work (Q80)."
    proof: "Tester's direct observation on the US-CASE-001 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-054.2
    req_id: REQ-054
    story_id: US-CASE-005
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`CustomObject:Case` (record-level sharing/OWD)"
    test_type: manual
    negative: true
    given: "a Case of the Billing record type owned by the `Billing` queue"
    when: "I open its record id directly in Lightning desktop"
    then: "access is denied at the record, not merely hidden — I am not the owner, not a `Billing` queue member, and no sharing rule names `Billing_Team` or the Billing type."
    proof: "Tester's direct observation on the US-CASE-005 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-020, REQ-054]

  - ac_id: AC-054.3
    req_id: REQ-054
    story_id: US-CASE-006
    persona: "Tier 2 support engineer on the `Acme Support Tier 2` profile holding `PSG_Tier2_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`CustomObject:Case` (record-level sharing/OWD)"
    test_type: manual
    negative: true
    given: "a Case of the Billing record type"
    when: "I open its record id directly"
    then: "access is denied — the sharing rule filters on `RecordTypeId equals Support` and nothing extends Billing cases to this group."
    proof: "Tester's direct observation on the US-CASE-006 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-054]

  - ac_id: AC-054.4
    req_id: REQ-054
    story_id: US-CASE-010
    persona: "Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`CustomObject:Case` (record-level sharing/OWD)"
    test_type: manual
    negative: true
    given: "a Support case is open in another queue"
    when: "I look at that same list view"
    then: "no row is shown for it, and opening its record id is denied."
    proof: "Tester's direct observation on the US-CASE-010 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."

  - ac_id: AC-055.1
    req_id: REQ-055
    story_id: US-CASE-001
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Settings:Case` (Email-to-Case deliverability)"
    test_type: manual
    negative: false
    given: "that same Case has just been created"
    when: "I read the customer's mailbox"
    then: "one acknowledgement has arrived from `support-noreply@acme.example` with sender name `Acme Support`, carrying the case number, and exactly one — not two."
    proof: "Tester's direct observation on the US-CASE-001 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-037, REQ-055]

  - ac_id: AC-055.2
    req_id: REQ-055
    story_id: US-CASE-003
    persona: "Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Settings:Case` (Email-to-Case deliverability)"
    test_type: manual
    negative: false
    given: "that Case has just been created"
    when: "the submitter reads their mailbox"
    then: "one acknowledgement carrying the case number has arrived from `support-noreply@acme.example`."
    proof: "Tester's direct observation on the US-CASE-003 persona's real Profile + PSG, per story-backlog.md's shared Background and this criterion's own Then."
    also_serves: [REQ-037, REQ-055]

  - ac_id: AC-005.90
    req_id: REQ-005
    story_id: "US-CASE-001"
    persona: "Tier 1 support agent on the Acme Support Tier 1 profile holding PSG_Tier1_Prod"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`ValidationRule:Case.Origin_Must_Be_Known`"
    test_type: manual
    negative: true
    given: "a Case whose Origin is blank or carries a value outside the three known ones"
    when: "a save is attempted without the Bypass_Case_Intake_Validation permission"
    then: "the save fails on Origin with "Set Origin to Email-Support, Email-Billing or Web before saving this case.""
    proof: "Attempt the save as the persona and read the returned validation error."
    derived_from: "US-CASE-001 AC-4 (story-backlog.md); artefacts/M3-S01/objects/Case/validationRules/Origin_Must_Be_Known.validationRule-meta.xml"
  - ac_id: AC-023.90
    req_id: REQ-023
    story_id: "US-CASE-006"
    persona: "Tier 2 support engineer on the Acme Support Tier 2 profile holding PSG_Tier2_Prod"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`SharingRules:Case`"
    test_type: manual
    negative: true
    given: "a Case of the Billing record type"
    when: "a Tier 2 engineer opens its record id directly"
    then: "access is denied — the Support_Cases_To_Tier_2 sharing rule filters on RecordTypeId equals Support and nothing extends Billing cases to this group"
    proof: "Open the Billing case's record id directly and observe the access-denied result."
    derived_from: "US-CASE-006 AC-3 (story-backlog.md); artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml"
  - ac_id: AC-033.90
    req_id: REQ-033
    story_id: "US-CASE-008"
    persona: "Tier 2 support engineer on the Acme Support Tier 2 profile holding PSG_Tier2_Prod"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EmailTemplate:case_intake/Case_Escalated_To_Tier2`"
    test_type: manual
    negative: true
    given: "the escalation rule as this build ships it (active=false, Q47)"
    when: "a tester looks for the Tier 2 handover notice at all"
    then: "none is sent, because the rule that fires the template is deliberately inactive and activation is a separate deploy inside an agreed comparison window"
    proof: "Confirm no Case_Escalated_To_Tier2 delivery occurs in the Email Log Files for the test window."
    derived_from: "US-CASE-008 AC-4 (story-backlog.md); artefacts/M4-S04/escalationRules/Case.escalationRules-meta.xml"
  - ac_id: AC-034.90
    req_id: REQ-034
    story_id: "US-CASE-001"
    persona: "Tier 1 support agent on the Acme Support Tier 1 profile holding PSG_Tier1_Prod"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AssignmentRules:Case`"
    test_type: manual
    negative: true
    given: "mail arrives from a sender the org does not authorise"
    when: "the support@acme.example routing address processes it"
    then: "no Case is created and the mail bounces rather than becoming work"
    proof: "Send from an unauthorised sender and confirm no Case row exists for it."
    derived_from: "US-CASE-001 AC-3 (story-backlog.md); artefacts/M3-S03/settings/Case.settings-meta.xml"
  - ac_id: AC-036.90
    req_id: REQ-036
    story_id: ""
    persona: "Tier 1 support agent on the Acme Support Tier 1 profile holding PSG_Tier1_Prod"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AssignmentRules:Case`"
    test_type: manual
    negative: true
    given: "a case's field values match none of the entries in Case_Intake_Routing"
    when: "the case is created through any channel"
    then: "the catch-all entry (no criteriaItems, no booleanFilter) routes it to the Tier_1_General queue rather than leaving it unowned"
    proof: "Create a case matching no named routing entry and read its Owner."
    derived_from: "workbook/06-automation.md CWB-AUT-010 notes (the assignment rule's own catch-all entry)"
  - ac_id: AC-037.90
    req_id: REQ-037
    story_id: "US-CASE-004"
    persona: "Tier 1 support agent on the Acme Support Tier 1 profile holding PSG_Tier1_Prod"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`AutoResponseRules:Case`"
    test_type: manual
    negative: true
    given: "a case is created through manual UI entry rather than Email-to-Case or Web-to-Case"
    when: "the case is saved"
    then: "no acknowledgement is sent — Case_Acknowledgement's single entry matches Origin in Email-Support, Email-Billing or Web only, deliberately excluding agent-entered cases"
    proof: "Create a case by hand and confirm no acknowledgement email is sent."
    derived_from: "workbook/06-automation.md CWB-AUT-011 notes; US-CASE-004 AC-2 (story-backlog.md)"
  - ac_id: AC-040.90
    req_id: REQ-040
    story_id: ""
    persona: "Tier 1 support agent on the Acme Support Tier 1 profile holding PSG_Tier1_Prod"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EntitlementProcess:First_Response_Premier`"
    test_type: manual
    negative: true
    given: "an account holds no Premier entitlement (Support_Tier__c is Standard or blank)"
    when: "a case is created against it"
    then: "the case is not tracked by First_Response_Premier — First_Response_Standard's 1-business-day target applies instead"
    proof: "Create a case on a non-Premier account and read CaseMilestone / SlaProcess for the case."
    derived_from: "workbook/06-automation.md CWB-AUT-015/016 notes (the two entitlement processes)"
  - ac_id: AC-041.90
    req_id: REQ-041
    story_id: ""
    persona: "Tier 1 support agent on the Acme Support Tier 1 profile holding PSG_Tier1_Prod"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EntitlementProcess:First_Response_Standard`"
    test_type: manual
    negative: true
    given: "an account holds an active Premier entitlement"
    when: "a case is created against it"
    then: "the case is not tracked by First_Response_Standard — First_Response_Premier's 4-business-hour target applies instead"
    proof: "Create a case on a Premier account and read CaseMilestone / SlaProcess for the case."
    derived_from: "workbook/06-automation.md CWB-AUT-015/016 notes (the two entitlement processes)"
  - ac_id: AC-053.90
    req_id: REQ-053
    story_id: ""
    persona: "Tier 1 support agent on the Acme Support Tier 1 profile holding PSG_Tier1_Prod"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`ValidationRule:Case.Origin_Must_Be_Known`"
    test_type: manual
    negative: true
    given: "a case's Origin is blank or unrecognised"
    when: "the case is evaluated for channel-specific UAT proof"
    then: "it cannot be attributed to any of the three defined intake channels and the validation rule blocks its save before it can be tested as a channel case"
    proof: "Attempt the save with a blank/unknown Origin and confirm the validation error."
    derived_from: "workbook/05-validation-rules.md CWB-VR-002; US-CASE-001 AC-4 (story-backlog.md)"
```

*67 lintable criterion record(s), one per (req_id, story AC-index) pair the story backlog's own matrix names — a criterion serving several req_ids appears once per req_id it serves, `also_serves` naming the rest so the repetition is traceable rather than silent.*

```yaml
project: "Acme Software Case Onboarding on Service Cloud — build-wide manual tests"
acceptance_criteria:
  - ac_id: AC-003.61
    req_id: REQ-003
    story_id: ""
    persona: "Build/milestone-gate reviewer (M1-S01)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M1-S01/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "B01"
    when: "artefacts/M1-S01/ is listed"
    then: "two businessProcess-meta.xml files exist beside the two recordType-meta.xml files, each record type's <businessProcess> carries the BARE process name (not Case.Support Process), and package.xml lists BusinessProcess with object-qualified members."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-004.61
    req_id: REQ-004
    story_id: ""
    persona: "Build/milestone-gate reviewer (M1-S01)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M1-S01/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "the Case org-wide default is what makes 'a Tier 1 agent cannot open a Billing case' true"
    when: "artefacts/M1-S01/objects/Case/Case.object-meta.xml is read"
    then: "it carries <sharingModel>Private</sharingModel> and <externalSharingModel>Private</externalSharingModel> as direct children of <CustomObject>, and no separate settings file anywhere in the build claims to carry the OWD. Tickable from this step's own artefacts at the M1 gate; the machine assertion that the OWD is not looser than the sharing rule's grant is M2-S05's build-scoped check_sharing_model.py test, which needs both files."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-013.61
    req_id: REQ-013
    story_id: ""
    persona: "Build/milestone-gate reviewer (M1-S02)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M1-S02/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: false
    given: "Q24"
    when: "each layout file is read"
    then: "<layoutSections> is preceded by the assignment-rule checkbox default set on, and every field a validation rule attaches an error to (assumption A13) is present on both layouts."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-016.61
    req_id: REQ-016
    story_id: ""
    persona: "Build/milestone-gate reviewer (M2-S01)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M2-S01/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "the bypass exists to let API-created cases skip the Case validation rules"
    when: "permissionsets/Case_Intake_Integration.permissionset-meta.xml is read"
    then: "it grants Bypass_Case_Intake_Validation and nothing else — no objectPermissions, no fieldPermissions, no userPermissions — and deploy-order.md carries the post-deploy instruction that this permission set is assigned to the integration/automated-process identity only and to no human user, with a named owner for that assignment."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-022.61
    req_id: REQ-022
    story_id: ""
    persona: "Build/milestone-gate reviewer (M2-S04)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M2-S04/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: false
    given: "the step claims to have built the work pools"
    when: "artefacts/M2-S04/ is listed"
    then: "all six components are present and named: queues Tier_1_General, Tier_2_Engineering and Billing, and groups Support_Tier_1, Support_Tier_2 and Billing_Team, and every queue's <queueSobject><sobjectType> is Case (Q30)."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-023.61
    req_id: REQ-023
    story_id: ""
    persona: "Build/milestone-gate reviewer (M2-S04)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M2-S04/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "Q88 fixes the per-queue email posture"
    when: "the three queue files are read"
    then: "Tier_1_General carries no <email> (work is pushed by Omni-Channel, not emailed), Billing carries the billing@ queue address, and Tier_2_Engineering carries the Tier 2 shared mailbox."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-024.61
    req_id: REQ-024
    story_id: ""
    persona: "Build/milestone-gate reviewer (M2-S04)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M2-S04/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "Q29 says membership changes monthly and must not require a deploy"
    when: "the three group files are read"
    then: "no <users> element names an individual username in any queue or group file — membership is expressed by public group and role only — and a support manager confirms the three public-group memberships match the current rosters."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-025.61
    req_id: REQ-025
    story_id: ""
    persona: "Build/milestone-gate reviewer (M2-S04)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M2-S04/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: false
    given: "skills/admin/data-skew-and-sharing-performance SKILL.md:88 defines ownership data skew as a single user or queue owning more than 10,000 records of one object, and this build routes roughly 480 cases a day to Tier_1_General as the catch-all"
    when: "queue-retirement-runbook.md is read"
    then: "it records that 10,000-record threshold, names who monitors the open-case count owned by each queue, and states the split-into-buckets remedy that skill documents."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-029.61
    req_id: REQ-029
    story_id: ""
    persona: "Build/milestone-gate reviewer (M2-S05)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M2-S05/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "assumption A1 reads deferred Q13 as a record-level restriction"
    when: "artefacts/M1-S01/objects/Case/Case.object-meta.xml and artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml are read together"
    then: "Case.object-meta.xml carries <sharingModel>Private</sharingModel>, the only criteria-based rule shares Support-record-type cases to the Support_Tier_2 public group, no rule names the Billing record type or the Billing_Team group as a target, and case-visibility-model.md states in one sentence why a Tier 1 agent therefore cannot open a Billing case and names Case.object-meta.xml as the file the default lives on."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-030.61
    req_id: REQ-030
    story_id: ""
    persona: "Build/milestone-gate reviewer (M3-S01)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M3-S01/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "the checker fails the step on a REVIEW finding ONLY because --strict is declared on its command"
    when: "the two validationRule files are read"
    then: "each errorConditionFormula opens with NOT($Permission.Bypass_Case_Intake_Validation) (Q56), tests emptiness with ISBLANK(TEXT(<picklist>)) rather than ISPICKVAL(<picklist>, \"\") alone, names only component fields and never a compound address field (Q59), and carries a final error message a customer-facing agent can act on rather than a placeholder (Q93)."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-032.61
    req_id: REQ-032
    story_id: ""
    persona: "Build/milestone-gate reviewer (M3-S02)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M3-S02/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: false
    given: "the acknowledgement is sent from support@ — the same address Email-to-Case listens on (Q22) —"
    when: "sender-identity-note.md and the two .email bodies are read"
    then: "the note names the org-wide address each template sends from (support@ for Case_Acknowledgement, billing@ for finance replies), states the self-addressed-loop risk that arises because support@ is both sender and inbound routing address, records that exactly one acknowledgement reaches the customer per case and that mail from the routing address's own sender is rejected rather than becoming a new case, and neither body hardcodes a recipient address."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-034.61
    req_id: REQ-034
    story_id: ""
    persona: "Build/milestone-gate reviewer (M3-S03)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M3-S03/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "check_email_to_case_configuration.py is not declared here (see the step note)"
    when: "settings/Case.settings-meta.xml is read"
    then: "both routing addresses carry their own caseOrigin (Email-Support, Email-Billing) and no caseOwner, unauthorizedSenderAction is Bounce, overEmailLimitAction is Requeue, saveEmailHeaders is true on both, and the webToCase block carries exactly its three documented children — enableWebToCase true and a caseOrigin that is a live CaseOrigin value from M1-S01, with defaultResponseTemplate deliberately unset because the guide scopes it to Self-Service portal responses rather than to the customer acknowledgement, which is M3-S04's auto-response rule."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-035.61
    req_id: REQ-035
    story_id: ""
    persona: "Build/milestone-gate reviewer (M3-S03)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M3-S03/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "Q66's answer itself says to confirm how the website form posts"
    when: "web-to-case-form-contract.md is read"
    then: "it states whether the form posts directly to Web-to-Case or through middleware, the Origin value each path stamps, and — per case-management-setup § 4 — that the HTML form itself is not metadata and has no metadata type, so it is authored and hosted outside this build."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-036.61
    req_id: REQ-036
    story_id: ""
    persona: "Build/milestone-gate reviewer (M3-S04)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M3-S04/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "the checker above now proves that exactly one rule is active, this test carries what the exit code cannot see. Given Q25 and Q26"
    when: "Case.assignmentRules-meta.xml is read"
    then: "the active rule's entries route on Case.Origin (Origin only this phase — Premier gets a faster SLA in M4-S02, not a different owner; G3 decision 3, decisions.md D-M3S04-02) only (both present at save); the last entry is a catch-all with no criteriaItems and no booleanFilter, assigned to the Tier_1_General queue built in M2-S04; and every assignedTo names a queue developer name that exists under artefacts/M2-S04/queues/."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-037.61
    req_id: REQ-037
    story_id: ""
    persona: "Build/milestone-gate reviewer (M3-S04)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M3-S04/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "Q28 and Q63"
    when: "Case.autoResponseRules-meta.xml is read"
    then: "exactly one acknowledgement entry can match any given case — no second entry and no parallel Flow email alert on the same event — and its template names the Classic template M3-S02 built, folder-qualified."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-022.62
    req_id: REQ-022
    story_id: ""
    persona: "Build/milestone-gate reviewer (M3-S05)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M3-S05/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "Q32-Q35 were deferred at G1 and this step is blocked on them (assumptions A4-A7)"
    when: "the M3 gate is reached"
    then: "each of the four carries a named owner and a due date on the record, and the gate is signed knowing M3-S05 ships nothing in this phase and Tier 1 works the Tier 1 General queue list view (M5-S01) in the interim."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-022.63
    req_id: REQ-022
    story_id: ""
    persona: "Build/milestone-gate reviewer (M3-S05)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M3-S05/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "this step is unblocked in a later phase"
    when: "the five metadata artefacts are read together"
    then: "Case_Channel names the routing configuration Tier_1_Push, Tier_1_Push names the Tier 1 General queue developer name built in M2-S04, Available_For_Cases names Case_Channel under <channels>, and Tier_1_Presence names Available_For_Cases in both presenceStatusOnDecline and presenceStatusOnPushTimeout — the queue-name half being the assertion no checker in the library can make at any scope."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-038.61
    req_id: REQ-038
    story_id: ""
    persona: "Build/milestone-gate reviewer (M4-S01)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M4-S01/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: false
    given: "the step claims to have built the calendars"
    when: "artefacts/M4-S01/settings/BusinessHours.settings-meta.xml is read"
    then: "all three are present and named: EMEA Support (Europe/London 08:00-18:00 Mon-Fri), US Support (America/New_York 08:00-20:00 Mon-Fri, the org default) and Severity 1 24x7."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-040.61
    req_id: REQ-040
    story_id: ""
    persona: "Build/milestone-gate reviewer (M4-S02)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M4-S02/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: false
    given: "assumption A27"
    when: "artefacts/M4-S02/ is listed"
    then: "it holds exactly two entitlementProcesses files (First_Response_Premier, First_Response_Standard) and exactly one milestoneTypes file (First Response), the Premier process carries minutesToComplete 240, and both processes name a <businessHours> that is a <name> in M4-S01's BusinessHours settings file."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-045.61
    req_id: REQ-045
    story_id: ""
    persona: "Build/milestone-gate reviewer (M4-S03)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M4-S03/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "the flow claims to stamp three fields"
    when: "the flow XML is read"
    then: "it sets Case.EntitlementId, Case.BusinessHoursId and Case.Priority, each guarded so it writes only into a null value (assumption A2), and the no-matching-account path is the documented fallback rather than a fault. The entitlement-to-process cross-reference is NOT asserted here: check_entitlements_and_milestones.py is carried by M4-S02 at build scope. S3: the flow's <description> carries the 'Owner:' marker and at least 60 characters, its <interviewLabel> is present, its <apiVersion> is 59 or higher and its <runInMode> is DefaultMode — all four are policy requirements check_flow_governance.py enforces, and the reviewer confirms them here as well because the checker reports them by file rather than by field."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-057.61
    req_id: REQ-057
    story_id: ""
    persona: "Build/milestone-gate reviewer (M4-S04)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M4-S04/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "the rule ships inactive (Q47)"
    when: "the sandbox proof is signed off"
    then: "a named owner activates it inside an agreed comparison window and records the first hour's escalation count. The checker's W1 finding ('no rule in this file is active') is the expected state here, not a defect."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-057.62
    req_id: REQ-057
    story_id: ""
    persona: "Build/milestone-gate reviewer (M4-S04)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M4-S04/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "Q46 measures 8 business hours"
    when: "Case.escalationRules-meta.xml is read"
    then: "the Tier 2 entry's minutesToEscalation is 480 (8 x 60), not 8; its businessHoursSource is Case with no <businessHours> child; it reassigns to the queue developer name Tier_2_Engineering built in M2-S04; and the Severity 1 entry's businessHoursSource is None. check_business_hours_and_holidays.py is not declared on this step — at artefacts/M4-S04 it prints 'No BusinessHours settings file found' and exits 0 vacuously, because the calendars are M4-S01's artefacts; M4's milestone test runs it at --manifest-dir artefacts, which is where the 24/7 calendar assertion lives."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-048.61
    req_id: REQ-048
    story_id: ""
    persona: "Build/milestone-gate reviewer (M5-S01)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M5-S01/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "the three views are Queue-scoped"
    when: "each listView file is read"
    then: "its <queue> names a queue developer name that exists under artefacts/M2-S04/queues/, and the Tier 1 General view is present as Tier 1's interim pull surface while M3-S05 is blocked."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-057.63
    req_id: REQ-057
    story_id: ""
    persona: "Build/milestone-gate reviewer (M4-S05)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M4-S05/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: false
    given: "no offline Apex compiler exists in the sf CLI"
    when: "the step is accepted"
    then: "the reviewer confirms every non-platform identifier in the emitted code is quoted from skills/apex/entitlement-apex-hooks/references/examples.md or from the cited template, and that CaseMilestoneServiceTest asserts CompletionDate is non-null once an open milestone's Case has been updated."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-058.61
    req_id: REQ-058
    story_id: ""
    persona: "Build/milestone-gate reviewer (M5-S02)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M5-S02/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "B08"
    when: "the M5 gate is reached"
    then: "team_size, concurrent_workstreams, release_cadence and data_sensitivity each have a named owner and a due date, and the gate is signed knowing M5-S02 ships nothing until they are answered — sandbox-strategy-designer refuses the run at its own first step without them."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-058.62
    req_id: REQ-058
    story_id: ""
    persona: "Build/milestone-gate reviewer (M5-S02)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M5-S02/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "this step is unblocked in a later phase"
    when: "sandbox-proof-plan.md is read"
    then: "its Post-Refresh Tasks section names both Email-to-Case routing addresses and the website form endpoint as things that must be re-pointed before any test runs (Q74), and states that no refresh is booked inside the UAT window (assumption A21)."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-053.61
    req_id: REQ-053
    story_id: ""
    persona: "Build/milestone-gate reviewer (M5-S03)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M5-S03/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: false
    given: "Q77 and Q84"
    when: "story-backlog.md is read"
    then: "each of the three intake channels — email, web and manual UI — has its own story, every story names a tester persona holding the real profile plus permission set group (PSG_Tier1_Prod, PSG_Tier2_Prod, PSG_Billing_Prod) rather than the admin profile, and every story carries at least three Given/When/Then criteria including a permission-denial path (Q80)."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-057.64
    req_id: REQ-057
    story_id: ""
    persona: "Build/milestone-gate reviewer (M5-S04)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M5-S04/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: false
    given: "25 clarifications were deferred at G1"
    when: "the workbook's assumptions section is read"
    then: "all 25 appear as named rows with an owner who can close each one, and each names the steps it constrains — compiled from assumptions[].steps[] rather than from step-note prose, which is why every step recording a deferral now also carries a structured \"assumptions\" key in its inputs{}."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-057.65
    req_id: REQ-057
    story_id: ""
    persona: "Build/milestone-gate reviewer (M5-S04)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M5-S04/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "two steps ship nothing in this phase"
    when: "the compiled documents are read"
    then: "M3-S05 and M5-S02 each appear with their blocked reason verbatim — 'deferred: Q32, Q33, Q34, Q35' and 'borrowed agent requires team_size, concurrent_workstreams, release_cadence, data_sensitivity' — and the UAT pack carries no case that depends on either."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-057.66
    req_id: REQ-057
    story_id: ""
    persona: "Build/milestone-gate reviewer (M5-S05)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M5-S05/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "(not stated in this plan's acceptance-test wording)"
    when: "(not stated in this plan's acceptance-test wording)"
    then: "W12 (1 of 3): a release owner confirms the deploy-order note contains no deploy command, only a validate-only command they may choose to run themselves."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-057.67
    req_id: REQ-057
    story_id: ""
    persona: "Build/milestone-gate reviewer (M5-S05)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M5-S05/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "two steps ship nothing in this phase"
    when: "deploy-order.md and package.xml are read"
    then: "M3-S05 and M5-S02 are listed as excluded with their blocked reasons verbatim rather than silently absent, and no Omni-Channel or sandbox component appears as a manifest member."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-057.68
    req_id: REQ-057
    story_id: ""
    persona: "Build/milestone-gate reviewer (M5-S05)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M5-S05/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "the build-level manifest aggregates every step's members"
    when: "package.xml is read"
    then: "the order in deploy-order.md follows admin/case-management-setup/references/metadata-examples.md § 5 — StandardValueSet before the business processes and record types, queues and groups before the assignment and escalation rules that name them, Settings named explicitly as Case and Flow because feature settings do not accept the wildcard — and ApexClass and ApexTrigger members from M4-S05 are present here, because that step declares no manifest of its own (B09)."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-001.61
    req_id: REQ-001
    story_id: ""
    persona: "Build/milestone-gate reviewer (M1)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M1/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "assumption A26 fixed the record-type count at two"
    when: "record-type-decision.md is read"
    then: "it states that the count was decided in the plan (not by the builder), names D5's criteria-based sharing rule on RecordTypeId as what settled Q1's conditional, and shows the Status and Reason value sets for each of the two processes."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-021.61
    req_id: REQ-021
    story_id: ""
    persona: "Build/milestone-gate reviewer (M2)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M2/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "(not stated in this plan's acceptance-test wording)"
    when: "(not stated in this plan's acceptance-test wording)"
    then: "The support manager and the admin lead jointly confirm that no named user is hard-coded in any queue or group and that the Billing visibility reading taken from deferred Q13 (assumption A1) is the one they want."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-022.64
    req_id: REQ-022
    story_id: ""
    persona: "Build/milestone-gate reviewer (M3)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M3/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "M3-S05 is blocked on deferred Q32-Q35"
    when: "the milestone gate is reached"
    then: "the support manager acknowledges that no Omni-Channel push is built in this phase, that Tier 1 works the Tier 1 General queue list view (M5-S01) in the interim, and that Q32-Q35 have a named owner and a due date."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-043.61
    req_id: REQ-043
    story_id: ""
    persona: "Build/milestone-gate reviewer (M4)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M4/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: false
    given: "Q27 flagged two by-design post-save OwnerId writers (Omni-Channel and the escalation rule)"
    when: "owner-writer-map.md is read alongside the escalation runbook"
    then: "both handoffs are described and neither contradicts the assignment rule."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-022.65
    req_id: REQ-022
    story_id: ""
    persona: "Build/milestone-gate reviewer (M5-W03)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M5-W03/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "the requirement's 'we must be able to prove it works in a sandbox before customers see it'"
    when: "the M5 gate is reached"
    then: "the release owner records that the sandbox proof plan is OUTSTANDING because M5-S02 is blocked, names the owner and due date for team_size, concurrent_workstreams, release_cadence and data_sensitivity, and every one of the 25 deferred clarifications has a named owner and a due date. standards/build-orchestration.md section 3 allows the gate over a step blocked with a recorded reason; what it does not allow is a tick against a document nobody wrote."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-029.62
    req_id: REQ-029
    story_id: ""
    persona: "Build/milestone-gate reviewer (M5-B04)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M5-B04/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "a Billing case owned by the Billing queue in the sandbox the release owner stands up for UAT"
    when: "a Tier 1 agent opens its record URL"
    then: "access is denied - confirmed by the admin lead against a real user, not inferred from the sharing metadata. If no such sandbox exists when the gate is reached, the gate is signed recording this check as outstanding rather than ticked; the metadata half of the assertion is carried by M2-S05's build-scoped check_sharing_model.py test and its manual test, both of which pass on artefacts alone."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-032.62
    req_id: REQ-032
    story_id: ""
    persona: "Build/milestone-gate reviewer (M5-B06)"
    sandbox: "N/A — this criterion checks a build artefact or plan record, not a live org"
    artefact: "artefacts/M5-B06/ or the compiled milestone report (plan.json manual acceptance test)"
    test_type: manual
    negative: true
    given: "the acknowledgement is sent from support@, which is also a live inbound Email-to-Case routing address (Q22)"
    when: "the loop test runs in the sandbox the release owner stands up for UAT - a case created by email from an external address"
    then: "the acknowledgement observed - then no second case is created from the acknowledgement itself and no acknowledgement-to-itself loop appears in the email log. If no such sandbox exists when the gate is reached, the gate is signed recording this check as outstanding rather than ticked."
    proof: "The reviewer's own read of the named artefact against the plan's own manual-test wording."

  - ac_id: AC-013.90
    req_id: REQ-013
    story_id: ""
    persona: "Tier 1 support agent (build reviewer confirming M1-S02's own artefact)"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`Layout:Case-Case Support Layout`"
    test_type: manual
    negative: true
    given: "an agent creates a case by hand and leaves "Assign using active assignment rule" unticked"
    when: "the agent saves the case"
    then: "the Case remains owned by the agent and no acknowledgement is sent — the box is shown but is not pre-ticked, and nothing in this build pre-ticks it"
    proof: "Create a case with the checkbox unticked and confirm Owner and the absence of an acknowledgement."
    derived_from: "US-CASE-004 AC-2 (story-backlog.md); artefacts/M1-S02/layouts/ (showRunAssignmentRulesCheckbox)"
  - ac_id: AC-040.90
    req_id: REQ-040
    story_id: ""
    persona: "Process owner (build reviewer confirming M4-S02's own artefact)"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EntitlementProcess:First_Response_Premier`"
    test_type: manual
    negative: true
    given: "an account holds no Premier entitlement"
    when: "a case is created against it"
    then: "First_Response_Premier does not track it; First_Response_Standard applies instead"
    proof: "Read CaseMilestone / SlaProcess for a case on a non-Premier account."
    derived_from: "workbook/06-automation.md CWB-AUT-015/016 notes (the two entitlement processes)"
  - ac_id: AC-043.90
    req_id: REQ-043
    story_id: ""
    persona: "Tier 2 support engineer (build reviewer confirming M4-S04's own artefact)"
    sandbox: "UNVERIFIED — Q75 deferred, M5-S02 blocked (see story-backlog.md Background)"
    artefact: "`EscalationRules:Case`"
    test_type: manual
    negative: true
    given: "a Support case was closed before the 8-business-hour window elapsed"
    when: "the escalation rule evaluates it"
    then: "no escalation or reassignment fires — closed cases are excluded by an explicit criterion, not by assumption"
    proof: "Close a case inside the window and confirm no escalation/reassignment occurred."
    derived_from: "US-CASE-008 AC-3 (story-backlog.md); artefacts/M4-S04/escalationRules/Case.escalationRules-meta.xml"
```

*39 additional criterion record(s), one per `manual` acceptance test plan.json declares on a step or milestone across the whole build (not just the M5 story backlog) — added here so `uat-test-cases.yaml`'s `ac_id` references have something to resolve against, per `agents/build-doc-keeper/AGENT.md` Step 10's cross-check requirement. `req_id` for a step that already carries its own manual-test row in `traceability.md` is taken from that row; for a step or milestone with none (blocked steps, and the `docs`/compile steps M5-S03/S04/S05), the closest-fit already-existing requirement is used and named in `compile_uat.py`'s `FALLBACK_REQ` / `MILESTONE_FALLBACK_REQ` tables — a disclosed approximation, not a fabricated requirement.*


---

## Criteria not traced to a requirement

The story backlog's own matrix does not name a `req_id` for every criterion it carries (its own "Coverage check" section says so: "32 of 35 requirements... map to at least one story" — the inverse gap, criteria with no requirement, is this list). Each is already reproduced verbatim above; none is dropped, and none is given an invented `req_id` here:

- `US-CASE-002` AC-3
- `US-CASE-002` AC-4
- `US-CASE-003` AC-4
- `US-CASE-009` AC-3
- `US-CASE-009` AC-4
- `US-CASE-011` AC-3

