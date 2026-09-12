# Story backlog — Acme Software case intake on Service Cloud (M5-S03)

Drafted by `agents/story-drafter` under `agents/build-step-runner`, from
`.sfskills/builds/case-onboarding/CLARIFICATIONS.md` (`discovery_artifact_kind:
requirements-list`). Nothing here was deployed and no org was read — this build is
`build_mode: design-only`.

Lint with:

```bash
python3 skills/admin/user-story-writing-for-salesforce/scripts/check_invest.py \
  --manifest-dir artefacts/M5-S03
```

---

## Summary

**Feature scope.** Acme Software case intake on Service Cloud: email, web and manual Case
creation with routing, first-response SLA and escalation for Tier 1, Tier 2 and Billing.

**Backlog shape.** 11 stories across 4 epics. Sizing: 3 S, 6 M, 2 L, 0 XL — no story is
committed at XL, so nothing needs splitting before handoff. MoSCoW: 9 Must, 2 Should,
0 Could, 0 Won't.

**What this backlog is for.** It is the specification the M5 sandbox proof is built from.
The M5 milestone goal requires that *each of the three intake channels has been tested
separately by a named tester on a real profile, and the deny cases fail closed*, so every
story here names a tester persona holding the real Profile plus Permission Set Group
(Q77), carries at least three Given/When/Then criteria, and carries at least one criterion
that is a restriction rather than a capability (Q80). The compiled UAT case pack and the
canonical acceptance-criteria document are **not** in this step — `agents/build-doc-keeper`
writes both at M5-S04 from these criteria.

**Confidence: MEDIUM.** Every persona, queue, record type, error string, calendar and
template named below is quoted from an artefact this build already produced, so the
criteria are falsifiable rather than aspirational. Confidence is held below HIGH for three
reasons, all recorded in Process Observations: no `target_org_alias` was supplied, so every
fit tier is a library-only reading and no license probe ran; `release_capacity_points` was
not supplied, so the MoSCoW 60% rule could not be evaluated; and the sandbox these stories
are proven in cannot be named, because Q75 is deferred and M5-S02 (the sandbox proof plan)
is `blocked`.

---

## Persona anchors

Three personas, one per team, exactly as Q77 requires — a named tester per team on the real
profile and permission sets, never the administrator. Every anchor below resolves to a file
in this build.

| Persona (as used in every `As a` stem) | Profile | Permission Set Group | Record types worked | Working surface | Anchored to |
|---|---|---|---|---|---|
| Tier 1 support agent | `Acme Support Tier 1` | `PSG_Tier1_Prod` (composes `Case_Agent_Core`, `Case_Tier1`) | Support | `Tier_1_General_Queue` list view on Case | `artefacts/M2-S03/profiles/Acme Support Tier 1.profile-meta.xml`, `artefacts/M2-S02/permissionsetgroups/PSG_Tier1_Prod.permissionsetgroup-meta.xml`, `artefacts/M5-S01/objects/Case/listViews/Tier_1_General_Queue.listView-meta.xml` |
| Tier 2 support engineer | `Acme Support Tier 2` | `PSG_Tier2_Prod` (composes `Case_Agent_Core`, `Case_Tier2`) | Support | `Tier_2_Queue` list view on Case | `artefacts/M2-S03/profiles/Acme Support Tier 2.profile-meta.xml`, `artefacts/M2-S02/permissionsetgroups/PSG_Tier2_Prod.permissionsetgroup-meta.xml`, `artefacts/M5-S01/objects/Case/listViews/Tier_2_Queue.listView-meta.xml` |
| Billing specialist | `Acme Billing` | `PSG_Billing_Prod` (composes `Case_Agent_Core`, `Case_Billing`) | Billing | `Billing_Queue` list view on Case | `artefacts/M2-S03/profiles/Acme Billing.profile-meta.xml`, `artefacts/M2-S02/permissionsetgroups/PSG_Billing_Prod.permissionsetgroup-meta.xml`, `artefacts/M5-S01/objects/Case/listViews/Billing_Queue.listView-meta.xml` |

**Background shared by every story below** (the permission-precondition block from
`admin/acceptance-criteria-given-when-then` § "Permission-Precondition Block"):

- Case OWD (`sharingModel`) is `Private`; `externalSharingModel` is `Private`
  (`artefacts/M1-S01/objects/Case/Case.object-meta.xml`).
- The only sharing rule in the build is `Support_Cases_To_Tier_2`, criteria
  `RecordTypeId equals Support`, shared to group `Support_Tier_2` at `Edit`
  (`artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml`). No rule targets
  `Billing_Team` or the Billing record type.
- Nobody in this build holds `View All`, `Modify All`, `View All Data` or `Modify All Data`
  on Case (`artefacts/M2-S05/case-visibility-model.md` § "Bypasses and Narrowing").
- No role hierarchy is assumed: no role developer name exists anywhere in this build.
- Every tester runs Lightning desktop (Q83). No mobile form factor is in scope this phase.
- Before every UAT session the triager confirms each PSG's recalculation is finished, so a
  stale group is reported as Blocked and not as a build defect (Q96).
- The sandbox is **UNVERIFIED** — see Process Observations. Q72 names the Partial Copy
  template objects (Account, Contact, Case, Entitlement, EmailMessage); Q75 (which sandbox,
  refreshed when) is deferred and M5-S02 is `blocked`, so no story below names one.

---

## Story backlog

### Epic A — The three intake channels, proven separately (Q84)

Q84's answer is the reason this epic has one story per channel rather than one story for
"intake": *test each of the three intake channels separately rather than proving the easy
half once*. The email channel is split again by data variation (support@ versus billing@)
because the two addresses route to different queues and are worked by different personas,
and a single story cannot carry two `As a` clauses without persona drift.

#### US-CASE-001 — Tier 1 agent receives a support email as a routed, acknowledged case

**As a** Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`,
**I want** a customer email arriving at `support@acme.example` to become a Case that is
already owned by my queue and already acknowledged when I first see it,
**So that** the requirement's one-minute promise is met on the channel that carries roughly
400 of the 460 cases a day and no customer waits on a human to press send.

**Acceptance Criteria:**

- *Given* the `support@acme.example` routing address is live and I hold `PSG_Tier1_Prod`,
  *When* a customer sends mail to that address,
  *Then* a Case exists with Origin `Email-Support`, Owner the `Tier_1_General` queue, and it
  appears in my `Tier_1_General_Queue` list view.
- *Given* that same Case has just been created,
  *When* I read the customer's mailbox,
  *Then* one acknowledgement has arrived from `support-noreply@acme.example` with sender
  name `Acme Support`, carrying the case number, and exactly one — not two.
- *Given* mail arrives from a sender the org does not authorise,
  *When* the routing address processes it,
  *Then* no Case is created and the mail bounces rather than becoming work (Q80).
- *Given* a Case whose Origin is blank or carries a value outside the three known ones,
  *When* a save is attempted without the `Bypass_Case_Intake_Validation` permission,
  *Then* the save fails on Origin with "Set Origin to Email-Support, Email-Billing or Web
  before saving this case."

**Complexity:** M · **Fit tier:** Standard · **NFR class:** — · **Training impact:**
email-blast · **MoSCoW:** Must

**Recommended agents:** `assignment-and-auto-response-rules-designer`,
`email-template-modernizer` · **Recommended skills:** `admin/email-to-case-configuration`,
`admin/assignment-rules`, `admin/email-templates-and-alerts`

**Dependencies:** REQ-034 routing address live; the `support-noreply@acme.example` org-wide
address verified (deploy prerequisite P4); sandbox deliverability raised above System Email
Only and Contact emails scrubbed first (Q78, prerequisite P6).

**Notes:** the bounce criterion is the deny case this channel owes Q80. Volume is ~400/day
and the entry path matters: prove this with real inbound mail, not a Data Loader insert.

#### US-CASE-002 — Billing specialist receives a finance email in the Billing queue

**As a** Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`,
**I want** a customer email arriving at `billing@acme.example` to land in the Billing queue
rather than in general support,
**So that** finance queries are worked by the two finance staff who can answer them instead
of being triaged twice and answered late.

**Acceptance Criteria:**

- *Given* the `billing@acme.example` routing address is live and I hold `PSG_Billing_Prod`,
  *When* a customer sends mail to that address,
  *Then* a Case exists with Origin `Email-Billing` and Owner the `Billing` queue, and it
  appears in my `Billing_Queue` list view.
- *Given* that Case is open in the Billing queue,
  *When* I open it,
  *Then* it carries the Billing record type and its page shows no severity concept.
- *Given* the same Case,
  *When* a Tier 1 support agent opens its record id directly,
  *Then* access is denied — Case OWD is Private and no sharing rule targets `Billing_Team`
  or the Billing record type.
- *Given* a finance case whose Origin was never stamped,
  *When* a save is attempted without the bypass permission,
  *Then* the save fails on Origin with the Origin error message and the case is not routed.

**Complexity:** M · **Fit tier:** Standard · **NFR class:** — · **Training impact:**
email-blast · **MoSCoW:** Must

**Recommended agents:** `assignment-and-auto-response-rules-designer`,
`permission-set-architect` · **Recommended skills:** `admin/email-to-case-configuration`,
`admin/assignment-rules`, `admin/sharing-and-visibility`

**Dependencies:** REQ-024 `Billing` queue exists with `Billing_Team` membership; the Billing
queue's non-routing mailbox `billing-queue@acme.example` created before the escalation rule
is activated (deploy prerequisite P2).

**Notes:** split from US-CASE-001 by data variation because the persona differs — Q77 gives
Billing its own named tester, and a story cannot carry two `As a` clauses.

#### US-CASE-003 — Tier 1 agent receives a web-form case through the fall-through entry

**As a** Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`,
**I want** a case submitted on the public website form to reach my queue with an
acknowledgement already sent,
**So that** the roughly 60 web submissions a day are worked on the same one-minute promise
as email and none of them sits unowned.

**Acceptance Criteria:**

- *Given* Web-to-Case is enabled and the website form posts the contract M3-S03 defines,
  *When* a visitor submits the form,
  *Then* a Case exists with Origin `Web` and Owner the `Tier_1_General` queue, reached
  through the assignment rule's catch-all entry rather than through a criteria match.
- *Given* that Case has just been created,
  *When* the submitter reads their mailbox,
  *Then* one acknowledgement carrying the case number has arrived from
  `support-noreply@acme.example`.
- *Given* the website form omits a field the Case validation rules read,
  *When* the submission is processed,
  *Then* the save is blocked and the case never appears in the queue — the web channel
  holds no bypass permission.
- *Given* a web case is in the queue,
  *When* a Billing specialist opens its record id directly,
  *Then* access is denied: the Support record type is shared only to `Support_Tier_2`.

**Complexity:** M · **Fit tier:** Standard · **NFR class:** — · **Training impact:**
email-blast · **MoSCoW:** Must

**Recommended agents:** `assignment-and-auto-response-rules-designer`, `object-designer`
· **Recommended skills:** `admin/case-management-setup`, `admin/assignment-rules`,
`admin/validation-rules`

**Dependencies:** REQ-035; the HTML form is authored and hosted outside this build, so the
form contract in `artefacts/M3-S03/web-to-case-form-contract.md` is a precondition the web
team owns; sandbox form endpoint re-pointed away from production on every refresh (Q74).

**Notes:** criterion 3 is the channel's deny case, and it is why the form's required fields
are a contract: an omitted field is a silently lost request, not a visible error.

#### US-CASE-004 — Tier 1 agent logs a case by hand and it routes like the other two channels

**As a** Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`,
**I want** a case I type in myself to route and acknowledge exactly as an emailed one does,
**So that** the roughly 20 cases a day we log by hand are not the ones that quietly get no
owner, no clock and no acknowledgement.

**Acceptance Criteria:**

- *Given* I am on a Case page and the layout shows "Assign using active assignment rule",
  *When* I tick that box and save,
  *Then* Owner becomes the `Tier_1_General` queue and one acknowledgement is sent.
- *Given* the same new Case,
  *When* I leave that box unticked and save,
  *Then* the Case remains owned by me and no acknowledgement is sent — the box is shown but
  is **not** pre-ticked, and nothing in this build pre-ticks it.
- *Given* I am creating a Case and have left Priority empty,
  *When* I save,
  *Then* the save fails on Priority with "Set a Priority before saving this case."
- *Given* I am creating a Case and have left Origin empty,
  *When* I save,
  *Then* the save fails on Origin with the Origin error message.

**Complexity:** M · **Fit tier:** Config · **NFR class:** — · **Training impact:**
**enablement-session** · **MoSCoW:** Must

**Recommended agents:** `object-designer`, `assignment-and-auto-response-rules-designer`
· **Recommended skills:** `admin/record-types-and-page-layouts`, `admin/assignment-rules`,
`admin/validation-rules`

**Dependencies:** REQ-013; both layouts carry `showRunAssignmentRulesCheckbox` (M1-S02).

**Notes:** **Q24 agent-training line.** Q24's answer asks for the checkbox *defaulted on*.
`decisions.md` D-M1S02-03 and O-M3S04-01 record that no metadata element in the cited skill
pre-ticks it, so half of Q24 is unbuilt and unbuildable here. The second criterion states
the consequence as an observable outcome rather than hiding it: without the tick, ~20 cases
a day are owned by their creator and get no acknowledgement
(`artefacts/M3-S04/owner-writer-map.md` § 5). Training impact is therefore
enablement-session, not email-blast — this is the one behaviour in the whole build that a
human has to remember every single time.

### Epic B — The deny cases fail closed (Q80, assumption A15)

#### US-CASE-005 — Tier 1 agent is refused a Billing case, and can prove it

**As a** Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`,
**I want** a Billing case to be genuinely unreachable for me rather than merely absent from
my list views,
**So that** finance data is confined to the two staff who are meant to see it and the
restriction survives someone pasting a record id into a URL.

**Acceptance Criteria:**

- *Given* a Case of the Billing record type owned by the `Billing` queue,
  *When* I open its record id directly in Lightning desktop,
  *Then* access is denied at the record, not merely hidden — I am not the owner, not a
  `Billing` queue member, and no sharing rule names `Billing_Team` or the Billing type.
- *Given* the same Billing case,
  *When* I search for it and when I open every Case list view available to me,
  *Then* no row is shown for it in any of them.
- *Given* my `PSG_Tier1_Prod` assignment,
  *When* the assignment is inspected,
  *Then* it grants the Billing record type neither as default nor as visible, and grants no
  `View All` or `Modify All` on Case.
- *Given* a Support case I do not own,
  *When* I open it,
  *Then* I can work it — proving the refusal above is record-scoped and has not broken the
  access this persona does need.

**Complexity:** S · **Fit tier:** Standard · **NFR class:** security · **Training impact:**
none · **MoSCoW:** Must

**Recommended agents:** `access-path-explainer`, `permission-set-architect`
· **Recommended skills:** `admin/sharing-and-visibility`, `admin/permission-set-architecture`

**Dependencies:** REQ-010, REQ-020, REQ-028, REQ-029.

**Notes:** assumption **A15** governs this story — the persona is set up without the
granting permission set and nothing else is assumed to be blocking the path, because Q82 is
deferred. The tester records *what they actually saw* (the refusal text or the empty list),
so a pass is evidence rather than an inference. The fourth criterion exists because a deny
case that passes for the wrong reason — a tester whose access is broken generally — is the
failure mode A15 was written against.

#### US-CASE-006 — Tier 2 engineer works an escalated Support case they do not own

**As a** Tier 2 support engineer on the `Acme Support Tier 2` profile holding
`PSG_Tier2_Prod`,
**I want** to open and edit any Support case whoever owns it, and to pick my work from a
list,
**So that** an escalation reaches an engineer who can act on it immediately instead of
waiting for a manual share.

**Acceptance Criteria:**

- *Given* a Support case owned by the `Tier_1_General` queue,
  *When* I open it,
  *Then* I can edit it — the `Support_Cases_To_Tier_2` criteria rule shares every Support
  case to the `Support_Tier_2` group at Edit, including records owned by others.
- *Given* I am starting my shift,
  *When* I open the `Tier_2_Queue` list view,
  *Then* it lists the cases waiting in `Tier_2_Engineering` and is the surface I work from.
- *Given* a Case of the Billing record type,
  *When* I open its record id directly,
  *Then* access is denied — the sharing rule filters on `RecordTypeId equals Support` and
  nothing extends Billing cases to this group.
- *Given* a Support case owned by the Automated Process identity at intake,
  *When* I open it before any assignment has landed,
  *Then* I can still edit it, because the rule includes records owned by all users.

**Complexity:** M · **Fit tier:** Config · **NFR class:** security · **Training impact:**
none · **MoSCoW:** Must

**Recommended agents:** `access-path-explainer`, `audit-router` · **Recommended skills:**
`admin/sharing-and-visibility`, `admin/list-views-and-compact-layouts`

**Dependencies:** REQ-019, REQ-023, REQ-029, REQ-048.

**Notes:** criterion 3 is this persona's deny case. Criterion 4 is the one worth running
first: intake creates cases under the integration identity, so a rule that did not include
records owned by all would be useless for the first minute of every case's life.

### Epic C — The clock, the escalation and the completion signal

#### US-CASE-007 — Tier 1 agent sees a first-response clock on the right calendar

**As a** Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`,
**I want** a new case to arrive with its SLA clock already running against the calendar its
account's region implies,
**So that** a Premier customer in London is measured on London hours rather than on New York
hours and we do not report a breach that never happened.

**Acceptance Criteria:**

- *Given* an account whose contracted tier is Premier,
  *When* a case is created against it,
  *Then* the first-response target is 4 business hours, on the `First_Response_Premier`
  process.
- *Given* an account on the standard tier,
  *When* a case is created against it,
  *Then* the first-response target is 1 business day, on the `First_Response_Standard`
  process.
- *Given* a case created at 17:00 London time on a Friday,
  *When* the clock is read on Saturday and again on Monday morning,
  *Then* it has not ticked over the weekend and the remaining time is unchanged.
- *Given* a case created on a date the calendar lists as a holiday,
  *When* the clock is read the next working morning,
  *Then* the holiday did not consume any of the target.
- *Given* a case created against no account at all,
  *When* it saves,
  *Then* it saves — the stamp falls back rather than blocking intake.

**Complexity:** L · **Fit tier:** Config · **NFR class:** reliability · **Training impact:**
email-blast · **MoSCoW:** Must

**Recommended agents:** `entitlement-and-milestone-designer`,
`business-hours-and-holidays-configurator` · **Recommended skills:**
`admin/entitlements-and-milestones`, `admin/business-hours-and-holidays`

**Dependencies:** REQ-038, REQ-040, REQ-041, REQ-045, REQ-008; **deploy prerequisite P1** —
`enableEntitlements` is owned by no step in this plan and three M4 steps depend on it, so
none of these criteria can be run until it is switched on.

**Notes:** **UNVERIFIED — both processes pin `US Support`.** Finding F-40 (HIGH) at the M4
gate records that the M4 goal promises a Premier EMEA clock on the EMEA calendar while both
`entitlementProcess` files name `US Support` business hours. The gate accepted that for this
phase. So criterion 3 as written proves the *pause* behaviour, not the *regional* behaviour,
and the tester must record which calendar the clock actually used. The three calendars that
exist are `US Support` (default, America/New_York), `EMEA Support` (Europe/London) and
`Severity 1 24x7`. The 14 seeded holidays and their owner are themselves UNCONFIRMED (G4
decision 5), so criterion 4 is run against whatever the calendar holds on the day.

#### US-CASE-008 — Tier 2 engineer receives a case that went untouched for 8 business hours

**As a** Tier 2 support engineer on the `Acme Support Tier 2` profile holding
`PSG_Tier2_Prod`,
**I want** an untouched support case to arrive in my queue with a handover notice of its
own,
**So that** nothing sits unworked for a day and the handover is visible to a human rather
than inferred from a changed owner field.

**Acceptance Criteria:**

- *Given* an open Support case created 8 business hours ago and not touched since,
  *When* the escalation rule is active and evaluates it,
  *Then* it is reassigned to `Tier_2_Engineering` and the Tier 2 handover notice is sent —
  a notice distinct from the customer acknowledgement.
- *Given* an open case flagged `Severity 1`,
  *When* 8 elapsed hours pass across a weekend,
  *Then* it escalates anyway, because that entry runs on no calendar and observes no
  holidays.
- *Given* a case that was closed inside the window,
  *When* the rule evaluates,
  *Then* no escalation fires and no reassignment is made — closed cases are excluded by an
  explicit criterion, not by assumption.
- *Given* the rule as this build ships it,
  *When* a tester looks for an escalation at all,
  *Then* none occurs, because the rule is deliberately inactive and activation is a separate
  deploy inside an agreed comparison window.

**Complexity:** L · **Fit tier:** Config · **NFR class:** reliability · **Training impact:**
enablement-session · **MoSCoW:** Must

**Recommended agents:** `audit-router`, `entitlement-and-milestone-designer`
· **Recommended skills:** `admin/escalation-rules`, `admin/business-hours-and-holidays`

**Dependencies:** REQ-043, REQ-023, REQ-033; **deploy prerequisite P2** — both the
`Tier_2_Engineering` and `Billing` queues need non-routing mailboxes
(`tier2-queue@acme.example`, `billing-queue@acme.example`) *before* activation, or the
handover notice reaches nobody (G4 decision 1, finding F-44); **deploy prerequisite P3** —
activation itself, per `artefacts/M4-S04/escalation-activation-runbook.md`.

**Notes:** criterion 4 is not a defect and is not padding. Q47 chose deploy-inactive-then-
activate precisely to avoid a wave of instant escalations on cutover, so "nothing escalated"
is the correct result on the deployed build and the first three criteria are **Blocked, not
Failed**, until activation. That distinction is Q97's whole point and the triager decides it.

#### US-CASE-009 — Tier 1 agent's first reply stops the first-response clock

**As a** Tier 1 support agent on the `Acme Support Tier 1` profile holding `PSG_Tier1_Prod`,
**I want** the First Response milestone to close when I actually start work on a case,
**So that** our SLA reporting measures response rather than measuring whether someone
remembered to close a milestone by hand.

**Acceptance Criteria:**

- *Given* an open case with a running First Response milestone and Status `New`,
  *When* I move Status off `New`,
  *Then* the milestone's completion date is stamped and the clock stops.
- *Given* a case whose Status is already off `New`,
  *When* I edit any other field,
  *Then* no second completion is stamped and the existing completion date is unchanged.
- *Given* a case with no entitlement attached and therefore no running milestone,
  *When* I move Status off `New`,
  *Then* the edit saves and nothing errors.
- *Given* 200 cases updated at once,
  *When* Status moves off `New` on all of them,
  *Then* every one completes without a limit error.

**Complexity:** M · **Fit tier:** Custom · **NFR class:** performance, reliability
· **Training impact:** enablement-session · **MoSCoW:** Must

**Recommended agents:** `apex-builder`, `test-class-generator` · **Recommended skills:**
`admin/entitlements-and-milestones`, `apex/case-trigger-patterns`

**Dependencies:** REQ-042, REQ-044; **deploy prerequisite P1** (`enableEntitlements`) and
**P5** — an active SlaProcess carrying a First Response milestone must exist in the target
org before the M4-S05 test class runs, and that test runs with `SeeAllData=true`.

**Notes:** **Completion-proxy line — carry this verbatim into the UAT script.** Q50's own
answer named *the first outbound EmailMessage* as the completion signal. This delivery
implements a narrower proxy: the Case leaving Status `New` (`decisions.md` D-M4S05-02,
REQ-044, accepted at the M4 gate as decision 7). So criterion 1 proves the proxy, **not**
Q50's requirement. A case where the agent replies to the customer without moving Status off
`New` will show an un-stopped clock and that is the shipped behaviour, not a defect. An
EmailMessage-triggered completion is a named backlog item.

### Epic D — The working surfaces and the monitoring report (Q31, Q91)

#### US-CASE-010 — Billing specialist works from the Billing queue list view

**As a** Billing specialist on the `Acme Billing` profile holding `PSG_Billing_Prod`,
**I want** one list that shows the finance cases waiting to be picked up,
**So that** two people can cover the queue without asking each other what is outstanding.

**Acceptance Criteria:**

- *Given* I hold `PSG_Billing_Prod`,
  *When* I open the `Billing_Queue` list view on Case,
  *Then* it lists the open cases owned by the `Billing` queue and is the surface I pick work
  from — Billing pulls, it is not pushed to.
- *Given* a Support case is open in another queue,
  *When* I look at that same list view,
  *Then* no row is shown for it, and opening its record id is denied.
- *Given* I take a case from the list,
  *When* ownership moves from the queue to me,
  *Then* it leaves the queue list view, so the list shows what is genuinely unclaimed.

**Complexity:** S · **Fit tier:** Standard · **NFR class:** — · **Training impact:**
email-blast · **MoSCoW:** Must

**Recommended agents:** `audit-router`, `permission-set-architect` · **Recommended skills:**
`admin/list-views-and-compact-layouts`, `admin/queues-and-public-groups`

**Dependencies:** REQ-049, REQ-048; the `Billing` queue and `Billing_Team` group (M2-S04).

**Notes:** criterion 2 is the deny case — the same denial US-CASE-005 proves from the other
side: Private OWD with no sharing rule reaching across the record types.

#### US-CASE-011 — Tier 2 lead reviews escalated open cases weekly

**As a** Tier 2 support engineer acting as the Tier 2 lead, on the `Acme Support Tier 2`
profile holding `PSG_Tier2_Prod`,
**I want** a saved report I can open every week without rebuilding it,
**So that** we can confirm next month that the escalation path is still firing, rather than
discovering months later that it silently stopped.

**Acceptance Criteria:**

- *Given* I hold `PSG_Tier2_Prod`,
  *When* I open `Escalated_Open_Cases` in the `Support_Operations` folder,
  *Then* it runs and returns open Cases opened in the last 30 days.
- *Given* the report as this build ships it,
  *When* I compare its rows against the cases the escalation engine actually flagged,
  *Then* it **over-reports** — the Escalated criterion is absent from the file and its own
  description says so.
- *Given* a Tier 1 support agent,
  *When* they open the same report folder,
  *Then* folder access governs what they see, and Billing cases remain unreachable to them
  through a report exactly as they are through a list view.

**Complexity:** S · **Fit tier:** Standard · **NFR class:** — · **Training impact:**
email-blast · **MoSCoW:** Should

**Recommended agents:** `audit-router`, `object-designer` · **Recommended skills:**
`admin/reports-and-dashboards`, `admin/sharing-and-visibility`

**Dependencies:** REQ-051; the post-deploy runbook step in `decisions.md` D-M5S01-02.

**Notes:** **UNVERIFIED — the Escalated column code.** D-M5S01-02 records that report column
codes are report-type specific and are not derivable from field API names; five candidates
for `Case.IsEscalated` were rejected by the org and no skill in the library carries the
sixth. So the report ships filtering on open plus last-30-days only. Criterion 2 asserts the
shipped behaviour honestly rather than asserting the intended one and failing. The remedy is
a post-deploy runbook step owned by the Tier 2 lead — add the filter in the report builder,
retrieve, and commit the harvested code.

---

## Requirements Traceability Matrix

`REQ-001` to `REQ-051` already exist in this build's `traceability.md` and are reused
unchanged — `admin/requirements-traceability-matrix` § ID Conventions makes `REQ-XXX`
immutable and never reused. `REQ-052` onward are minted here for the testing-and-environment
requirements the Q77–Q97 group contributes, continuing from the highest id already on file
(`REQ-051`). Cardinality is 1 requirement : N stories, never a requirement split across
rows.

`uat_test_id` is deliberately empty in every row: `agents/build-doc-keeper` assigns the
canonical `ac_id`s and `TC-` ids at M5-S04 when it compiles `acceptance-criteria.md` and
`uat-test-cases.yaml`. This step does not mint a competing id space.

| req_id | source | story_id | acceptance_criteria_ids | uat_test_id | priority | status |
|---|---|---|---|---|---|---|
| REQ-005 | Q19 | US-CASE-001, US-CASE-002, US-CASE-003 | AC-1 in each | — | Must | In UAT |
| REQ-010 | Q13 | US-CASE-005 | AC-1, AC-2, AC-3 | — | Must | In UAT |
| REQ-013 | Q24 | US-CASE-004 | AC-1, AC-2 | — | Must | In UAT |
| REQ-019 | Q13 | US-CASE-006 | AC-1, AC-4 | — | Must | In UAT |
| REQ-020 | Q13 | US-CASE-005 | AC-1, AC-3 | — | Must | In UAT |
| REQ-023 | Q13 | US-CASE-006, US-CASE-008 | US-CASE-006 AC-2; US-CASE-008 AC-1 | — | Must | In UAT |
| REQ-024 | Q1 | US-CASE-002 | AC-1, AC-2 | — | Must | In UAT |
| REQ-028 | Q7 | US-CASE-005 | AC-3 | — | Must | In UAT |
| REQ-029 | Q13 | US-CASE-005, US-CASE-006 | US-CASE-005 AC-4; US-CASE-006 AC-1, AC-3 | — | Must | In UAT |
| REQ-030 | Q5 | US-CASE-004 | AC-3 | — | Must | In UAT |
| REQ-031 | Q5 | US-CASE-001, US-CASE-004 | US-CASE-001 AC-4; US-CASE-004 AC-4 | — | Must | In UAT |
| REQ-032 | Q22 | US-CASE-001, US-CASE-003 | AC-2 in each | — | Must | In UAT |
| REQ-033 | Q63 | US-CASE-008 | AC-1 | — | Must | In UAT |
| REQ-034 | Q17 | US-CASE-001, US-CASE-002 | AC-1 in each | — | Must | In UAT |
| REQ-035 | Q66 | US-CASE-003 | AC-1, AC-3 | — | Must | In UAT |
| REQ-036 | Q25 | US-CASE-001, US-CASE-002, US-CASE-003, US-CASE-004 | AC-1 in each | — | Must | In UAT |
| REQ-037 | Q28 | US-CASE-001, US-CASE-003 | AC-2 in each | — | Must | In UAT |
| REQ-038 | Q39 | US-CASE-007 | AC-3, AC-4 | — | Must | In UAT |
| REQ-040 | Q38 | US-CASE-007 | AC-1 | — | Must | In UAT |
| REQ-041 | Q38 | US-CASE-007 | AC-2 | — | Must | In UAT |
| REQ-042 | Q53 | US-CASE-009 | AC-1, AC-2 | — | Must | In UAT |
| REQ-043 | Q45 | US-CASE-008 | AC-1, AC-2, AC-3, AC-4 | — | Must | In UAT |
| REQ-044 | Q50 | US-CASE-009 | AC-1 (proxy only — see the story's notes) | — | Must | In UAT |
| REQ-045 | Q48 | US-CASE-007 | AC-1, AC-2, AC-5 | — | Must | In UAT |
| REQ-048 | Q31 | US-CASE-006, US-CASE-010 | US-CASE-006 AC-2; US-CASE-010 AC-1 | — | Must | In UAT |
| REQ-049 | Q31 | US-CASE-010 | AC-1, AC-3 | — | Must | In UAT |
| REQ-050 | A7 | US-CASE-001 | AC-1 | — | Should | In UAT |
| REQ-051 | Q91 | US-CASE-011 | AC-1, AC-2 | — | Should | In UAT |
| REQ-052 | Q77 | every story in this backlog | the `As a` stem of each | — | Must | In UAT |
| REQ-053 | Q84 | US-CASE-001, US-CASE-002, US-CASE-003, US-CASE-004 | AC-1 in each | — | Must | In UAT |
| REQ-054 | Q80 | US-CASE-001, US-CASE-005, US-CASE-006, US-CASE-010 | the deny criterion named in each story's notes | — | Must | In UAT |
| REQ-055 | Q78 | US-CASE-001, US-CASE-002, US-CASE-003 | AC-2 in US-CASE-001 and US-CASE-003 | — | Must | In UAT |
| REQ-056 | Q96 | — (UAT programme control) | Background, shared | — | Must | Gap — see Process Observations |
| REQ-057 | Q97 | — (UAT programme control) | — | — | Must | Gap — see Process Observations |
| REQ-058 | Q94 | — (blocked on M5-S02) | — | — | Should | Gap — see Process Observations |

**Backward check.** Every story above appears in at least one row; no orphan stories.
**Coverage check.** 32 of 35 requirements in this matrix map to at least one story. The
three that do not are named explicitly below rather than left as empty cells.

**Requirements deliberately not restated here.** `REQ-001` to `REQ-004`, `REQ-006` to
`REQ-009`, `REQ-011`, `REQ-012`, `REQ-014` to `REQ-018`, `REQ-021`, `REQ-022`, `REQ-025` to
`REQ-027`, `REQ-039`, `REQ-046` and `REQ-047` are build-configuration requirements already
traced to their own steps in `traceability.md` and proven by those steps' checkers. This
matrix covers what the *sandbox proof* has to demonstrate, not what the build had to
contain; M5-S04's compiled matrix joins the two.

---

## MoSCoW capacity check

| Priority | Stories | Count |
|---|---|---|
| Must | US-CASE-001 … US-CASE-010 (excluding US-CASE-011) | 9 |
| Should | US-CASE-011 | 1 |
| Could | — | 0 |
| Won't (this phase) | — | 0 |

One story moved between the algorithmic and final priority: **US-CASE-011** scored Must
algorithmically (Q91 makes the report a named requirement) and is delivered as Should,
because D-M5S01-02 leaves the report over-reporting until a post-deploy runbook step
harvests the Escalated column code. A Must that cannot pass its own second criterion is a
Must in name only. No caller-supplied `priority_overrides` were applied.

**The 60% rule could not be evaluated.** `release_capacity_points` was not supplied, so
`admin/moscow-prioritization-for-sf-backlog`'s check — Must-have points ≤ 60% of capacity —
has no denominator. What can be said without it: 9 of 11 stories are Must, which is 82% of
the *backlog by count*, and that is the shape the rule exists to flag. It is defensible here
only because this backlog is the acceptance surface for a build that already exists rather
than a sprint commitment — every Must is proving something already written to disk. If this
were forward work, the descope candidates by lowest value-per-effort would be US-CASE-011
(Should already), then US-CASE-008 (blocked on activation anyway), then US-CASE-007's
holiday criterion.

---

## Process Observations

### What was healthy

- **Every persona resolves to a file.** All three tester personas map to a Profile and a
  Permission Set Group this build actually wrote (`artefacts/M2-S03/profiles/`,
  `artefacts/M2-S02/permissionsetgroups/`). No persona in this backlog was inferred, which
  is the failure `admin/user-story-writing-for-salesforce` gotcha 2 and LLM anti-pattern 1
  both describe. Observed while reconciling `personas_supplied` against the M2 artefacts.
- **Every `Then` names a concrete observable.** The two validation-rule criteria quote the
  `errorMessage` string byte-for-byte from
  `artefacts/M3-S01/objects/Case/validationRules/`, so the failure a tester sees and the
  failure the story names are one fact rather than two descriptions that can drift.
- **The deny cases were already designed, not retrofitted.** `case-visibility-model.md`
  opens with a single sentence explaining why a Tier 1 agent cannot open a Billing case and
  names the three files that make it true. Writing US-CASE-005 was transcription, not
  design.
- **The build is honest about its own gaps in the artefacts themselves.** The escalation
  rule's `active=false`, the report's own `<description>`, and the assignment rule's comment
  about the catch-all entry all state the shipped behaviour where a reader in Setup will
  see it. That is why three stories here could assert what the build *does* rather than what
  it was meant to do.

### What was concerning

- **Three stories cannot be run at all until an org prerequisite is met.** US-CASE-007 and
  US-CASE-009 need `enableEntitlements`, which G4 decision 2 records as owned by **no step
  in this plan**. US-CASE-008 needs the escalation rule activated and both queue mailboxes
  created first. A UAT script compiled from this backlog will have three stories whose
  result is Blocked on day one unless the prerequisites are worked first. Observed while
  writing `dependencies[]` against the G4 gate notes.
- **Q24 remains half-built after four steps.** D-M1S02-03 recorded it at M1-S02, O-M3S04-01
  recorded it again at M3-S04 with the routing consequence made concrete, and this backlog
  records it a third time as a training obligation. Roughly 20 cases a day depend on a human
  remembering a checkbox. Three recordings of the same gap is the signal that it needs a
  decision, not another recording.
- **F-40 is not closed and this backlog inherits it.** Both entitlement processes pin
  `US Support` business hours while the M4 goal promises a Premier EMEA clock. US-CASE-007's
  criterion 3 therefore proves the weekend pause but not the regional calendar, and says so.
  A tester who does not read the note will record a pass that does not mean what it looks
  like it means.
- **Ten of eleven stories trip the checker's 250-word body WARN, and the overflow is not
  story.** `check_invest.py` counts everything between one story heading and the next, so a
  story's `Complexity` / `Fit tier` / `Recommended agents` / `Recommended skills` /
  `Dependencies` / `Notes` block is counted as body. Measured per story, the stem plus the
  acceptance criteria alone run 143–235 words and every one is *under* the threshold; the
  handoff block adds 73–193. The stories are not too large to demo — the ones that overflow
  most (US-CASE-007 at 193 handoff words, US-CASE-009 at 169, US-CASE-004 at 155) are the
  three carrying the F-40, completion-proxy and Q24 notes the M4 gate required be written
  down. Trimming those notes to clear a heuristic WARN would delete the content the gate
  asked for, so they stand. The declared acceptance test passes at exit 0 because it does
  not pass `--strict`; a future run that adds `--strict` would fail on these, and the fix
  then is `--max-words`, not shorter notes.
- **The sandbox is unnamed.** `admin/user-story-writing-for-salesforce` gotcha 14 requires a
  story to name the sandbox it will be proven in and what must exist there first. No story
  here can, because Q75 is deferred and M5-S02 is `blocked` on four sandbox-strategy inputs.
  Preconditions are named; the environment is not.

### What was ambiguous

- **Three requirements in the matrix have no story, deliberately.** REQ-056 (Q96, PSG
  recalculation gate), REQ-057 (Q97, Fail-versus-Blocked triage) and REQ-058 (Q94,
  environment owner and refresh approver) are controls on how UAT is *run*, not behaviours a
  persona can demo. Writing them as stories would have produced exactly the undemoable
  stories LLM anti-pattern 5 warns about. REQ-056 and REQ-057 are carried in the shared
  Background instead; REQ-058 has nowhere to go while M5-S02 is blocked. A human should
  confirm that `agents/build-doc-keeper` picks all three up in the M5-S04 UAT pack rather
  than assuming this backlog carried them.
- **`REQ-052` onward were minted here.** This step assigned seven new requirement ids
  continuing from `REQ-051`, the highest already on file. If `agents/build-doc-keeper` mints
  its own ids at M5-S04 from the same clarification group, the two spaces will collide. The
  gap is that no writer owns the `REQ-` sequence for this build.
- **Whether the email channel should be one story or two.** The M5 manual acceptance test
  asks that each of the three channels has its own story. This backlog gives email two
  (US-CASE-001, US-CASE-002), split by data variation, because Q77 gives Billing its own
  named tester and a single story cannot carry two personas without the drift gotcha 3
  describes. A reviewer who reads "three channels, three stories" literally should confirm
  the split is acceptable before M5-S04 compiles it.
- **Fit tiers are library-only readings.** No `target_org_alias` was supplied, so no license
  probe and no closest-existing-object search ran. Every `Fit tier` above is MEDIUM
  confidence by the skill's own rule, and `Custom` on US-CASE-009 reflects that this build
  wrote Apex for it, not that no declarative route exists.

### Suggested follow-up agents

- `agents/build-doc-keeper` (`/keep-build-docs`) — M5-S04 is the next step and compiles this
  backlog's criteria into `acceptance-criteria.md` and `uat-test-cases.yaml`, which is where
  the `ac_id` and `TC-` ids this matrix left empty get assigned.
- `agents/access-path-explainer` (`/why-cant-user`) — because US-CASE-005 and US-CASE-006
  both turn on a record-level refusal, and a tester who sees the refusal but cannot say
  which layer produced it has evidence of an outcome rather than of a design.
- `agents/sandbox-strategy-designer` (`/design-sandbox-strategy`) — because the four inputs
  blocking M5-S02 are the same four that leave every story here without a named sandbox.

These are recommendations. Nothing above was invoked.

---

## Citations

| Type | Id / path | Used for |
|---|---|---|
| skill | `skills/admin/user-story-writing-for-salesforce/SKILL.md` | INVEST checklist, the As-A/I-Want/So-That stem, S/M/L/XL sizing, the split techniques, the handoff field rules |
| skill | `skills/admin/user-story-writing-for-salesforce/templates/story-shape.md` | the canonical markdown story shape and the INVEST self-check |
| skill | `skills/admin/user-story-writing-for-salesforce/references/gotchas.md` | gotcha 2 (missing persona), 8 (sad path), 10 (implicit trigger), 11 (`Then` with no concrete state), 12 (volume), 14 (no named sandbox) |
| skill | `skills/admin/user-story-writing-for-salesforce/references/llm-anti-patterns.md` | anti-pattern 1 (invented personas), 2 (implementation steps as AC), 3 ("the system shall"), 5 (undemoable stories), 7 (sizing by hours) |
| skill | `skills/admin/acceptance-criteria-given-when-then/SKILL.md` | the Given/When/Then anatomy, the negative-path pairing rule, the permission-precondition Background pattern, the requirement-id convention, the bulk-path scenario rule |
| skill | `skills/admin/uat-and-acceptance-criteria/SKILL.md` | the pre-UAT environment questions (sandbox type, deliverability, named tester per persona, restriction criteria), the Fail-versus-Blocked defect distinction, the UAT script column set M5-S04 will fill |
| standard | `standards/build-orchestration.md` § 4 | the borrowed-roster-agent rule: declare only outputs the owning agent's Output Contract names |
| agent | `agents/story-drafter/AGENT.md` | the nine-step plan, the routing table behind every `Recommended agents` line, and the seven-section Output Contract this document follows |
| build artefact | `artefacts/M1-S01/objects/Case/Case.object-meta.xml`, `standardValueSets/CaseOrigin.standardValueSet-meta.xml` | Private OWD; the three Origin values every channel criterion names |
| build artefact | `artefacts/M1-S02/layouts/` | `showRunAssignmentRulesCheckbox` on both layouts (US-CASE-004) |
| build artefact | `artefacts/M2-S02/`, `artefacts/M2-S03/profiles/` | the three PSGs and three profiles every persona anchor resolves to |
| build artefact | `artefacts/M2-S04/queues/`, `groups/` | the `Tier_1_General`, `Tier_2_Engineering` and `Billing` queues and their groups |
| build artefact | `artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml`, `case-visibility-model.md` | the single criteria-based rule and the deny-case reasoning behind US-CASE-005 and US-CASE-006 |
| build artefact | `artefacts/M3-S01/objects/Case/validationRules/` | the two `errorMessage` strings quoted verbatim in US-CASE-001 and US-CASE-004 |
| build artefact | `artefacts/M3-S04/assignmentRules/Case.assignmentRules-meta.xml`, `autoResponseRules/Case.autoResponseRules-meta.xml`, `owner-writer-map.md` | the three rule entries incl. the catch-all, the `support-noreply@acme.example` sender, and the ~20-cases-a-day consequence in US-CASE-004 |
| build artefact | `artefacts/M4-S01/settings/BusinessHours.settings-meta.xml` | the three calendars and the seeded holidays US-CASE-007 reads |
| build artefact | `artefacts/M4-S02/entitlementProcesses/` | the 4-business-hour and 1-business-day targets, and the `US Support` pin behind the F-40 note |
| build artefact | `artefacts/M4-S04/escalationRules/Case.escalationRules-meta.xml`, `escalation-activation-runbook.md` | `active=false`, the Severity 1 `businessHoursSource None` entry, the closed-case exclusion |
| build artefact | `artefacts/M5-S01/objects/Case/listViews/`, `reports/Support_Operations/` | the three queue list views and the escalation monitoring report |
| build record | `plan.json` `human_gates[milestone:M4].notes` | deploy prerequisites P1–P5 and the completion-proxy acceptance (decisions 1, 2, 7, 9) |
| build record | `decisions.md` D-M1S02-03, O-M3S04-01, D-M4S05-02, D-M5S01-02 | the Q24 training line, the completion proxy, and the report's missing Escalated criterion |
| build record | `CLARIFICATIONS.md` Q24, Q50, Q68, Q72, Q74–Q78, Q80–Q84, Q94, Q96, Q97 | the discovery artefact this backlog was parsed from |
| build record | `plan.json` `assumptions[A15]`, `assumptions[A23]` | the deny-case single-cause assumption and the screen-plus-record evidence rule |
