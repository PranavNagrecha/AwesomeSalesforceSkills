# Worked Example — Building a Case Intake Solution From Requirements Using Only the Skills

An acceptance test for the routing skill set: a realistic requirement set, worked from the questions the skills say to ask, through the ten-section configuration workbook, to the deployable artefacts and the tests, citing the skill file that supplied each decision. Where a skill had to be supplemented by judgement, the gap is listed at the end rather than papered over.

## 1. Requirements, captured as answers to the skills' questions

Requester: Acme Software, B2B support, moving from a shared mailbox to Service Cloud. Answers are recorded against the question that produced them (`SKILL.md` § Questions to Ask, and the same sections in `admin/assignment-rules`, `admin/queues-and-public-groups`, `admin/business-hours-and-holidays`, `admin/omni-channel-routing-setup`, `admin/email-templates-and-alerts`).

| Question asked | Answer |
|---|---|
| Which channels create cases, at what volume? | Email to `support@acme.example` (~400/day) and a website form (~60/day). No phone. Agents also create cases by hand for ~20/day. |
| Which mailbox addresses route in, and who owns them? | `support@` (general) and `billing@` (finance queries). IT owns the forwarding rules. |
| What must happen in the first minute? | Owner set, customer acknowledged, SLA clock started on the right calendar, priority set from the form. |
| Who works the pool, and how does that change? | Tier 1 (12 agents, EMEA and US, join and leave monthly), Tier 2 (4 engineers, stable), Billing (2 finance staff). |
| Queue or person? What if nothing matches? | Queues. Unmatched cases go to Tier 1 General. |
| Who is notified of a new record? | Tier 1 uses Omni-Channel push, so no queue email; Billing wants the queue address emailed. |
| Does anything else write `OwnerId`? | Not yet. Omni-Channel will, by design. |
| Should the customer get an acknowledgement? | Yes, from `support@acme.example`, for both channels, with the case number. |
| What is the SLA, and does it pause? | Premier accounts: first response in 4 business hours; standard: 1 business day. Escalate to Tier 2 if untouched for 8 business hours. Pauses on weekends and regional holidays. |
| Which regions work different hours? | EMEA (London, 08:00–18:00) and US (New York, 08:00–20:00). US is default. |
| How do we know a case's region at creation? | From the account's `Region__c`; unknown accounts default to US. |
| Any round-the-clock case type? | Severity 1 outages: 24/7 notification, no pause. |
| Who answers replies? | Tier 1, from `support@`. `billing@` replies come from `billing@`. |
| How will we know it works before customers do? | Sandbox test with real inbound email, a clock test, and a loop test. |

## 2. Decisions the skills forced

| Decision | Resolved by | Why |
|---|---|---|
| Assignment rules, not Flow, set the owner | `admin/assignment-rules` → `references/routing-selector.md` | Case is one of the two objects with a rule engine; Flow would re-implement the criteria table |
| Omni-Channel on Tier 1 only; Billing and Tier 2 are list-view queues | `admin/omni-channel-routing-setup` § Questions | Only Tier 1 needs availability-based push |
| Region calendar set by a before-save Flow, escalation entries on `Case` source | `admin/business-hours-and-holidays` Example 2, gotchas #3 and #4 | Anything after save runs the timer on the default calendar |
| Severity 1 entry uses `businessHoursSource` = `None` | `admin/business-hours-and-holidays` Decision Guidance | Entry-level choice, documented as an exception |
| Auto-response sender is `support@` (an org-wide address), never a routing address | `admin/email-to-case-configuration` gotchas; `admin/email-templates-and-alerts` → `references/metadata-and-sender-identity.md` | Sending from the routing address loops |
| Classic templates, deployed with the rules | `admin/email-templates-and-alerts` → `references/metadata-and-sender-identity.md` | Rules deployed by metadata reference Classic templates |
| Premier SLA as an entitlement process; Tier 2 escalation as an escalation rule | `admin/entitlements-and-milestones`; `admin/escalation-rules` | Milestones track the contractual promise; escalation re-routes untouched work |
| Queue membership by role and public group, no named users | `admin/queues-and-public-groups` → `references/queue-behaviour-matrix.md` | Monthly churn in Tier 1; usernames do not deploy between orgs |

## 3. Configuration workbook rows

Sections follow `admin/configuration-workbook-authoring` (ten canonical sections). Rows carry the executing agent and the skill files the row was written from.

### Section 1 — Objects + Fields

| row_id | target_value | recommended_agent | recommended_skills |
|---|---|---|---|
| CWB-OBJ-001 | `Account.Region__c` picklist (EMEA, US) if absent | object-designer | admin/case-management-setup |
| CWB-OBJ-002 | `Case.Severity__c` picklist (1–4); `Case.Priority` mapped from the web form | object-designer | admin/case-management-setup |
| CWB-OBJ-003 | Custom Setting `Round_Robin_Counter__c`: not in scope this release (Omni-Channel replaces round-robin) | — | admin/assignment-rules |

### Section 2 — Page Layouts + Lightning Pages

| row_id | target_value | recommended_agent | recommended_skills |
|---|---|---|---|
| CWB-LAY-001 | Case record page for the Service Console with Business Hours, Entitlement, and Severity visible | path-designer / object-designer | admin/record-types-and-page-layouts, architect/agent-console-requirements |

### Section 3 — Profiles + Permission Sets + PSGs

| row_id | target_value | recommended_agent | recommended_skills |
|---|---|---|---|
| CWB-PS-001 | PSG `Support_Agent`: Case CRUD, Email-to-Case reply, Omni-Channel presence (Tier 1 only) | permission-set-architect | admin/omni-channel-routing-setup, templates/admin/permission-set-patterns.md |
| CWB-PS-002 | Org-wide address `support@acme.example` restricted to the support profiles; `billing@` to finance | permission-set-architect | admin/email-templates-and-alerts → references/metadata-and-sender-identity.md |

### Section 4 — Sharing Settings

| row_id | target_value | recommended_agent | recommended_skills |
|---|---|---|---|
| CWB-SHR-001 | Queues with `doesIncludeBosses` = true so support managers see queue-owned cases | permission-set-architect | admin/queues-and-public-groups → references/queue-behaviour-matrix.md |

### Section 5 — Validation Rules

| row_id | target_value | recommended_agent | recommended_skills |
|---|---|---|---|
| CWB-VR-001 | Severity 1 requires a non-empty `Description` and an Account | audit-router | templates/admin/validation-rule-patterns.md |

### Section 6 — Automation

| row_id | target_value | recommended_agent | recommended_skills |
|---|---|---|---|
| CWB-AUT-001 | Case assignment rule `Support_Case_Routing`: Billing origin address → `Billing_Queue`; Severity 1 → `Tier_2_Support_Queue`; catch-all → `Tier_1_General` | assignment-and-auto-response-rules-designer | admin/assignment-rules → references/metadata-examples.md |
| CWB-AUT-002 | Case auto-response rule `Case_Acknowledgement`: Web and Email origins → `Support_Templates/Case_*_Acknowledgement`, sender `support@` | assignment-and-auto-response-rules-designer | admin/assignment-rules → references/metadata-examples.md; admin/case-management-setup § Assignment Rules and Auto-Response Dependency |
| CWB-AUT-003 | Before-save Flow `Case_Set_Calendar`: `BusinessHoursId` from `Account.Region__c`, fallback US | flow-builder | admin/business-hours-and-holidays Example 2; flow/record-triggered-flow-patterns |
| CWB-AUT-004 | Escalation rule `Support_SLA`: entry 1 Severity 1, source `None`, notify at 60 min; entry 2 all others, source `Case`, notify owner at 240 min, reassign to `Tier_2_Support_Queue` at 480 min | audit-router (case_escalation) | admin/escalation-rules; admin/assignment-rules → references/metadata-examples.md (escalation XML) |
| CWB-AUT-005 | Entitlement process `Premier_Support` with milestone First Response (240 business minutes) on the US calendar, EMEA override for EMEA accounts | entitlement-and-milestone-designer | admin/entitlements-and-milestones |
| CWB-AUT-006 | Business hours `US Support Hours` (default), `EMEA Support Hours`; holidays attached per region | business-hours-and-holidays-configurator | admin/business-hours-and-holidays Example 1 |
| CWB-AUT-007 | Omni-Channel: `Case_Channel`, presence statuses, `Tier_1_Agents` presence configuration (capacity 6), routing configuration `Case_Routing_Least_Active` (weight 2, push timeout 120 s) on `Tier_1_General` | omni-channel-routing-designer | admin/omni-channel-routing-setup → references/metadata-examples.md |

### Section 7 — List Views + Search

| row_id | target_value | recommended_agent | recommended_skills |
|---|---|---|---|
| CWB-LV-001 | One list view per queue (`Owner.Type = 'Queue'`), plus "My Open Cases" | audit-router | admin/queues-and-public-groups § SOQL for queue-owned records |

### Section 8 — Reports + Dashboards

| row_id | target_value | recommended_agent | recommended_skills |
|---|---|---|---|
| CWB-RPT-001 | Cases by queue and age; milestone violations; escalations by entry | audit-router | admin/reports-and-dashboards-fundamentals; admin/entitlements-and-milestones |

### Section 9 — Integrations

| row_id | target_value | recommended_agent | recommended_skills |
|---|---|---|---|
| CWB-INT-001 | On-Demand Email-to-Case routing addresses `support@`, `billing@` with verified forwarding and threading test | audit-router | admin/email-to-case-configuration § Routing Addresses, § Email Threading |
| CWB-INT-002 | Web-to-Case form with reCAPTCHA, `orgid`, `retURL`, Origin = Web, Priority mapped | audit-router | admin/case-management-setup § Web-to-Case; security/recaptcha-and-bot-prevention |

### Section 10 — Data + Migration

| row_id | target_value | recommended_agent | recommended_skills |
|---|---|---|---|
| CWB-DATA-001 | Historic mailbox cases: not migrated this release | — | — |
| CWB-DATA-002 | Deploy order: fields → groups → queues → templates → business hours → routing config → rules → Flow → entitlement process | changeset-builder | admin/assignment-rules → references/migration-and-sandbox.md |

## 4. Artefacts produced, with the file each was shaped from

| Artefact | Path | Shaped from |
|---|---|---|
| Public group | `groups/Support_Agents_EMEA.group-meta.xml` | queues → metadata-examples.md |
| Queues | `queues/Tier_1_General.queue-meta.xml`, `Tier_2_Support_Queue`, `Billing_Queue` | queues → metadata-examples.md |
| Email folder + 2 Classic templates | `email/Support_Templates-meta.xml`, `email/Support_Templates/Case_Web_Acknowledgement.email(+-meta.xml)`, `Case_Email_Acknowledgement` | email-templates → metadata-and-sender-identity.md |
| Business hours | `settings/BusinessHours.settings-meta.xml` | business-hours → examples.md Example 1 |
| Omni-Channel set | `serviceChannels/`, `servicePresenceStatuses/`, `presenceDeclineReasons/`, `presenceUserConfigs/`, `queueRoutingConfigs/` | omni-channel → metadata-examples.md |
| Assignment rule | `assignmentRules/Case.assignmentRules-meta.xml` | assignment-rules → metadata-examples.md |
| Auto-response rule | `autoResponseRules/Case.autoResponseRules-meta.xml` | assignment-rules → metadata-examples.md |
| Escalation rule | `escalationRules/Case.escalationRules-meta.xml` | assignment-rules → metadata-examples.md |
| Calendar Flow | `flows/Case_Set_Calendar.flow-meta.xml` | business-hours Example 2; templates/flow/RecordTriggered_Skeleton.flow-meta.xml |
| Entitlement process | built in Setup this release (see gap 2) | entitlements-and-milestones |
| package.xml | one manifest in the deploy order above | assignment-rules → migration-and-sandbox.md |

## 5. Tests before go-live

1. Checkers: `check_assignment_rules.py`, `check_business_hours_and_holidays.py`, `check_queues.py` on the deployed folder.
2. Channel matrix (assignment-rules → testing.md): one email to each routing address, one web form submission, one manual case with and without "Run assignment rules"; record actual owner against expected.
3. Loop test: confirm the auto-response sender is not a routing address, then send one email and check no second case is created (email-to-case-configuration gotchas).
4. Clock test (business-hours → examples.md Example 4): create an EMEA case Friday 17:30 London; escalation target must land Monday morning.
5. Omni test: an agent in `Tier_1_Agents` with the Case status selected receives a pushed case; one outside it does not.
6. Sandbox deliverability raised before any of the above (devops/sandbox-data-isolation-gotchas).

## 6. Gaps found while building (the point of the exercise)

Every row above was written from a skill file except these; each is a candidate for the next depth wave.

1. **Web-to-Case form.** `admin/case-management-setup` describes the pattern but has no HTML form example with the hidden fields (`orgid`, `retURL`, `origin`, `recordType`) the way `admin/lead-management-and-conversion` does for Web-to-Lead. Row CWB-INT-002 was written from the Lead example by analogy.
2. **Entitlement process metadata.** `admin/entitlements-and-milestones` explains processes, milestones, and calendars but has no deployable `EntitlementProcess` example, so row CWB-AUT-005 says "built in Setup". Unverified whether the org can deploy the process with its milestones by metadata; check the Metadata API guide before promising it.
3. **Support agent permission set.** No skill states the concrete permissions a Tier 1 agent needs for Email-to-Case reply and Omni-Channel presence; row CWB-PS-001 lists them from experience, not from a file. `templates/admin/permission-set-patterns.md` gives the shape, not the Service Cloud content.
4. **Case reports.** `admin/reports-and-dashboards-fundamentals` is generic; there is no "support operations dashboard" reference (queue age, milestone violations, escalations by entry). Row CWB-RPT-001 is a list of report names, not a design.
5. **Routing-address to queue mapping.** `admin/email-to-case-configuration` explains that a routing address pre-classifies a case, but the assignment rule criteria that read it (the case's origin address) are not shown; row CWB-AUT-001 assumes a criteria field exists for it and should be verified against the org.

Everything else in the build, including all rule, queue, calendar, Omni-Channel and template metadata, was produced directly from the cited files.
