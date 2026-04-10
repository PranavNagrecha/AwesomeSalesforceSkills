---
name: marketing-automation-requirements
description: "Use this skill when gathering, documenting, or validating requirements for a Salesforce marketing automation program — covering MCAE (Account Engagement / Pardot) lifecycle stages, MQL/SQL threshold definitions, scoring model specifications (sources, weights, decay, ceiling), handoff notification design, CRM field updates on status change, and sales SLA. Trigger keywords: MQL criteria, marketing-to-sales handoff, lead lifecycle, scoring requirements, automation program requirements, Marketing Cloud Automation Studio scope. NOT for implementation of MCAE automation rules, MCAE scoring configuration, MC Automation Studio SQL activity authoring, or Einstein Lead Scoring setup — those are covered by dedicated implementation skills."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "We need to define what counts as an MQL before we build the automation in Account Engagement"
  - "Marketing and sales can't agree on when a prospect is ready to hand off — how do we document the criteria"
  - "How do we specify the scoring model requirements so the MCAE team knows what to build"
  - "What fields and SLA commitments does the handoff process need to cover before we go live"
  - "We're switching from Pardot to Marketing Cloud Next and need to re-document our scoring requirements"
  - "How do we document the lifecycle stages and stage-transition rules for our marketing automation program"
  - "The project team needs a requirements document before configuring Engagement Studio programs"
tags:
  - marketing-automation
  - mql
  - sql
  - mcae
  - pardot
  - account-engagement
  - lifecycle-stages
  - scoring-requirements
  - handoff-sla
  - requirements-gathering
  - marketing-cloud
inputs:
  - "Business definition of Ideal Customer Profile (ICP): target industries, company sizes, titles, geographies"
  - "Agreed or proposed MQL threshold: score alone, or score + grade combination"
  - "List of trackable behavioral signals: form fills, email clicks, page visits, content downloads, custom redirects"
  - "Current or planned marketing automation platform: MCAE (Pardot), Marketing Cloud Engagement, Marketing Cloud Next"
  - "Sales process framework in use: BANT, MEDDIC, or custom qualification steps"
  - "Existing CRM field inventory on Lead and Contact objects"
  - "Sales team response SLA expectations and escalation process"
outputs:
  - "Marketing automation scope document: platforms in scope, lifecycle stage map, and exclusions"
  - "Scoring model specification: behavioral sources, point weights per activity, score decay rules, ceiling score, grade profile criteria"
  - "MQL and SQL threshold definition: agreed criteria, score range or score+grade formula, sign-off record"
  - "Handoff mechanism specification: automation rule or program trigger, CRM field updates, notification method"
  - "Sales SLA document: max response time per MQL tier, recycle criteria, recycle field updates"
  - "CRM field requirements list: fields to create or modify on Lead/Contact for lifecycle tracking"
  - "Review checklist confirming all requirements sections are complete before handoff to implementation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Marketing Automation Requirements

This skill activates when a practitioner needs to gather, document, or validate the business requirements for a Salesforce marketing automation program before any platform configuration begins. It produces the requirements artifacts — scoring model spec, MQL/SQL threshold definitions, lifecycle stage map, handoff mechanism design, and sales SLA — that implementation skills (`mcae-lead-scoring-and-grading`, `mcae-pardot-setup`) depend on as inputs.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the platform scope.** MCAE (Account Engagement / Pardot) and Marketing Cloud Engagement (MCE) are distinct platforms with different scoring engines and automation models. MCAE uses a prospect-level behavioral score (integer) and a fit-based grade (A–F) configured via Profiles. Marketing Cloud Next uses configurable Scoring Models operating on Data Cloud engagement events. MCE Automation Studio handles batch SQL-driven processes; it does not share the rule-based program model of MCAE Engagement Studio. Requirements must specify which platform is in scope and explicitly exclude others.
- **Establish MQL alignment before touching any tooling.** The most frequent cause of failed marketing automation programs is that the MQL threshold was set unilaterally by marketing without sales input. Requirements gathering must produce a written, co-signed MQL definition before the implementation team begins configuration.
- **Map lifecycle stages to the platform's data model.** MCAE defines seven prospect lifecycle stages: Visitor → Prospect → MQL → SQL → Opportunity → Customer → Won. These map to CRM Opportunity stages at the SQL+ phases. Requirements must specify which stages are in scope, which CRM field updates each transition triggers, and which stages are tracked in MCAE vs. the CRM.
- **Determine scoring model complexity.** A simple model may use MCAE's default scoring rules (global point values per activity type). A complex model may use per-asset score overrides, multiple decay rules, separate fit Profiles for different ICP segments, and a ceiling score. Requirements must document the intended complexity so the implementation team can estimate configuration effort accurately.
- **Identify the handoff notification method.** When a prospect crosses the MQL threshold, MCAE can create a Salesforce task, send an alert email to the assigned rep, add the prospect to a CRM campaign, or update a prospect field. The requirements document must specify which notification mechanisms are required and what the rep is expected to do within the SLA window.

---

## Core Concepts

### Lifecycle Stages and Platform Mapping

MCAE defines a standard set of lifecycle stages used in the Lifecycle Report (accessible via B2B Marketing Analytics):

| Stage | Description | CRM Correlation |
|---|---|---|
| Visitor | Anonymous site visitor — no prospect record yet | No CRM record |
| Prospect | Known contact in MCAE database — below MQL threshold | Lead or Contact record exists |
| MQL | Crossed the agreed score (and optionally grade) threshold — flagged for sales | Lead `Is_MQL__c` stamped, rep notified |
| SQL | Rep has accepted and qualified the MQL against BANT/MEDDIC criteria | Lead status updated to "Accepted" or Contact linked to Opportunity |
| Opportunity | Active sales cycle underway | Salesforce Opportunity in open stage |
| Customer | Opportunity closed-won | Opportunity Stage = Closed Won |
| Won | Post-sale tracking within MCAE lifecycle report | Opportunity Stage = Closed Won, confirmed in MCAE |

Source: [Salesforce Help — Lifecycle Report Metrics](https://help.salesforce.com/s/articleView?id=sf.pardot_lifecycle_report.htm).

Requirements must define which stage transitions are automated (e.g., Prospect → MQL fires automatically when score threshold is crossed) and which require manual rep action (e.g., MQL → SQL requires rep to update Lead status).

### Scoring Model Specification

A compliant scoring model requirements document must specify six elements:

1. **Scoring sources** — the complete list of activities that generate score points: form fills, email link clicks, email opens, page views on tracked pages, content downloads, webinar registrations, custom redirect clicks, and any custom event integrations. Each source must be listed explicitly; "standard MCAE activities" is not a sufficient specification.
2. **Point weights per activity** — the numeric point value assigned to each scoring source. Weights must reflect relative intent signal strength: a demo request form fill (high intent) should outweigh a blog page view (low intent). Default MCAE weights (e.g., form fill = +50, email click = +5, page view = +1) are a starting point, but the requirements must confirm or override each value.
3. **Score decay rules** — time-based point reduction logic to ensure old engagement does not permanently inflate scores. A decay rule specifies: the inactivity period (e.g., 30 days with no tracked activity), the point reduction per cycle (e.g., −10 points), and whether multiple rules stack (e.g., −10 at 30 days AND −20 at 60 days). Without decay rules, prospects from old campaigns remain MQL-eligible indefinitely. Source: [Salesforce Help — MCAE Scoring and Grading](https://help.salesforce.com/s/articleView?id=sf.pardot_scoring_and_grading_about.htm).
4. **Ceiling score** — the maximum score a prospect can accumulate. MCAE does not enforce a hard ceiling by default, but requirements may specify a logical ceiling (e.g., 250 points) above which additional activity does not increase the score. This prevents a highly active competitor or researcher from permanently occupying the top of the MQL queue.
5. **Grade profile criteria** — for orgs using the score+grade MQL model, requirements must document the Profile criteria: which job titles, industries, company sizes, and geographies earn positive grade points, and which earn negative grade points. Each criterion must map to a specific Salesforce field value.
6. **Negative scoring** — activities that indicate disqualification (unsubscribe, hard bounce, opt-out) must be listed with their deduction values (e.g., Unsubscribe = −50, Hard Bounce = −75).

### MQL and SQL Threshold Definition

The MQL threshold is the quantitative boundary at which marketing certifies a prospect as ready for sales engagement. Requirements must document:

- **Threshold type:** Score alone (e.g., `Score >= 100`) or combined score+grade (e.g., `Score >= 100 AND Grade >= B`). Using score alone risks handing off high-engagement, low-fit prospects (competitors, students). Using score+grade requires the grade Profile to be accurate for this to function as intended.
- **Sign-off record:** The threshold must be agreed to in writing by both marketing and sales leadership — not set unilaterally. Include the names and dates of approvers in the requirements document.
- **SQL acceptance criteria:** When a rep receives an MQL, they evaluate it against a qualification framework. Requirements must document which framework is in use (BANT: Budget, Authority, Need, Timeline; or MEDDIC: Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion) and which criteria must be confirmed before the rep converts the lead to SQL.

### Marketing Cloud Next Scoring Models vs. MCAE Scoring

Marketing Cloud Next (MC Next) supports configurable Scoring Models that operate on Data Cloud engagement data, not on MCAE prospect activity. If the org uses MC Next, requirements must specify:

- Which Data Cloud engagement event streams feed the scoring model (email interactions, web engagement, mobile, commerce)
- The scoring model configuration: engagement dimensions, decay settings, and the output score field that maps to Data Cloud individual profiles
- How the MC Next score surfaces in CRM (via Data Cloud — CRM connector field mapping) and how it relates to, or replaces, MCAE prospect scoring

MC Next Scoring Models are distinct from MCAE Scoring. Requirements must be explicit about which system owns the authoritative score. Running both without a clear ownership rule causes conflicting scores on the same contact.

### MCE Automation Studio vs. MCAE Engagement Studio

These are two separate automation engines that are frequently confused in requirements documents:

- **MCAE Engagement Studio** — a rule-based, prospect-level program builder inside Account Engagement. Supports branching logic based on prospect field values, score/grade, list membership, and CRM data. Operates in near-real-time on individual prospects.
- **MCE Automation Studio** — a batch processing engine in Marketing Cloud Engagement. Activities are SQL queries, data extracts, imports, and script activities executed on a schedule. Automation Studio does not evaluate individual prospect engagement in real time; it processes data in bulk on a configured schedule. Source: [Salesforce Developer — Automation Studio Overview](https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/automation-studio-overview.html).

Requirements must state explicitly which automation engine is in scope. Conflating them leads to implementation specs that describe MCAE behavior using MCE terminology or vice versa, causing rework.

---

## Common Patterns

### Pattern 1: Score + Grade MQL with Lifecycle Stage Field Updates

**When to use:** B2B orgs with MCAE where both behavioral engagement and ICP fit must be confirmed before MQL handoff. This is the recommended baseline for most B2B use cases.

**How it works:**

1. Define MQL threshold: `Prospect Score >= 100 AND Prospect Grade >= B`.
2. Specify the MCAE Automation Rule that fires at this threshold and performs: (a) update `Prospect_Status` field to "MQL", (b) assign to Sales queue, (c) create CRM task on the Lead record with subject "New MQL — follow up within 24 hours", (d) send alert email to assigned rep.
3. Specify CRM field updates: `Is_MQL__c = true`, `MQL_Date__c = today`, `Lifecycle_Stage__c = "MQL"`.
4. Define the SLA: rep must accept or recycle within 1 business day. Recycled leads must have `Recycle_Reason__c` populated.
5. Document the SQL acceptance gate: rep confirms BANT and updates `Lifecycle_Stage__c = "SQL"`, `SQL_Date__c = today`.

**Why not score alone:** High-scoring, low-fit contacts (competitors researching your product, non-buyers in wrong geographies) generate noise in the Sales queue. The grade gate filters for ICP fit.

### Pattern 2: Score-Only MQL with Segmented Scoring Rules

**When to use:** Orgs with a single, broad ICP where firmographic fit is less variable, or orgs where MCAE Profiles are not yet configured and the team needs an initial MQL model to start collecting conversion data.

**How it works:**

1. Define MQL threshold: `Prospect Score >= 75` (lower threshold may be appropriate without a grade gate).
2. Specify per-asset score overrides for high-intent assets: demo request form = 75 points (enough to qualify on a single fill); pricing page view = 10 points (overrides the default 1-point page view).
3. Specify decay rules: −10 points after 30 days of inactivity, −20 points after 60 days.
4. Define ceiling: cap effective score at 150. If a prospect exceeds 150, no additional points are awarded until decay reduces the score below the ceiling.
5. Specify that a follow-up review is scheduled 90 days after go-live to assess MQL-to-SQL conversion rate and calibrate threshold.

**Why not implement grade profiles immediately:** If the org does not have reliable ICP field data (e.g., `Title`, `Industry` fields are sparsely populated), a grade Profile will produce inaccurate grades. Start with score-only and add grading once field data quality is confirmed.

### Pattern 3: MC Next Scoring Model Requirements for Data Cloud Orgs

**When to use:** Orgs using Marketing Cloud Next with Data Cloud as the engagement data backbone, replacing or supplementing MCAE with MC Next's configurable Scoring Models.

**How it works:**

1. Identify the engagement event streams in Data Cloud that will feed the scoring model: email engagement DMO, web engagement DMO, mobile push DMO.
2. Specify the scoring dimensions in the MC Next Scoring Model: which event types award points, what weights apply, and whether the model uses recency weighting (more recent events count more).
3. Specify the output: the computed score field on the Individual profile object in Data Cloud, and the cadence of score recalculation (near-real-time vs. scheduled batch).
4. Specify the CRM surface: how the MC Next score is mapped through the Data Cloud — Salesforce CRM connector to a Lead or Contact field, and how it is consumed by CRM-side routing (Flow, Assignment Rules).
5. Document the relationship between MC Next score and any residual MCAE score: if both systems are active, which score is authoritative for MQL evaluation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| MCAE is the primary MAP, B2B org with ICP fit variance | Score + Grade MQL (Pattern 1) | Dual-dimension filtering reduces false positives in Sales queue |
| MCAE active, ICP field data quality is poor or sparse | Score-only MQL with per-asset overrides (Pattern 2) until data quality improves | Grade model on bad data produces meaningless grades |
| MC Next + Data Cloud is the engagement platform | MC Next Scoring Model requirements (Pattern 3) | MCAE scoring concepts do not map to MC Next architecture |
| Org uses MCE Automation Studio for batch processes | Specify Automation Studio scope separately from Engagement Studio scope | These are different engines; conflating them creates incorrect requirements |
| Sales disputes MQL quality after go-live | Requirements doc must include a calibration review milestone at 60–90 days | Threshold calibration requires post-launch conversion data; build the review into the SLA |
| Multiple ICP segments with different fit criteria | Require separate grade Profiles per segment in requirements | One Profile cannot accurately represent multiple ICP segments with different fit signals |
| Org needs to track Marketing Lifecycle Metrics (B2B MA Analytics) | Include MCAE Lifecycle Stage field mapping in requirements | Lifecycle Report metrics require specific CRM field values mapped per stage |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Establish platform scope.** Confirm which marketing automation platforms are active in the org: MCAE, MCE, MC Next, or a combination. Document in the requirements scope section which platforms are in scope for this automation program and which are explicitly out of scope. Confirm that the implementation team will not conflate MCE Automation Studio with MCAE Engagement Studio.

2. **Map lifecycle stages and transitions.** Working from the MCAE standard lifecycle model (Visitor → Prospect → MQL → SQL → Opportunity → Customer → Won), confirm which stages are in scope, define the trigger for each stage transition (automated vs. manual rep action), and list the CRM field updates each transition must produce. Get explicit confirmation from both marketing and sales on the stage definitions.

3. **Define the scoring model specification.** For each scoring source (form fills, email clicks, page views, content downloads, webinar registrations, unsubscribes), document the agreed point weight. Confirm score decay rules (inactivity period and point reduction per cycle). Confirm the ceiling score. If the org uses MCAE grading, document the Profile criteria per ICP segment. Record any per-asset score overrides (e.g., pricing page view = 10 points instead of default 1).

4. **Agree on and document the MQL threshold.** Run a joint session with marketing and sales leadership. Document the threshold (score alone or score+grade), the names and dates of approvers, and the agreed SQL qualification framework (BANT or MEDDIC). This is the single most important output of the requirements process — do not proceed to implementation without this sign-off.

5. **Specify the handoff mechanism.** Document how the MQL is surfaced to the sales rep: which MCAE Automation Rule triggers (or which Engagement Studio program step fires), what CRM field updates occur (`Is_MQL__c`, `MQL_Date__c`, `Lifecycle_Stage__c`), what notification is sent (task creation, alert email, Slack notification via CRM Flow), and which queue or user the lead is assigned to.

6. **Define the sales SLA.** Document the maximum response time for each MQL tier (e.g., 1 business day for demo-request MQLs, 3 business days for content-download MQLs), the recycle trigger and recycle field requirements (`Recycle_Reason__c`, `Recycle_Date__c`), and the escalation process if a rep fails to act within the SLA window.

7. **Produce the requirements document and run the checklist.** Compile all decisions into the work template. Run the review checklist to confirm no section is incomplete. Hand off the completed requirements document to the implementation team as the input to `mcae-lead-scoring-and-grading` or the appropriate implementation skill.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Platform scope is documented: MCAE, MCE, and/or MC Next; which is in scope and which is excluded
- [ ] All seven MCAE lifecycle stages are reviewed; in-scope stages and their transition triggers are documented
- [ ] Scoring model specification covers all six elements: scoring sources, point weights, decay rules, ceiling score, grade profile criteria, negative scoring
- [ ] Score decay rules are specified with inactivity period, point reduction, and stacking behavior
- [ ] MQL threshold type is confirmed: score alone or score + grade
- [ ] MQL threshold value is agreed to and signed off by both marketing and sales leadership
- [ ] SQL qualification framework is named (BANT or MEDDIC) and criteria are listed
- [ ] Handoff mechanism is specified: automation trigger, CRM field updates, notification method, assignment target
- [ ] Sales SLA is documented: max response time per MQL tier, recycle criteria, escalation process
- [ ] CRM field requirements list is complete: all new or modified fields on Lead/Contact identified with API name and type
- [ ] Calibration review milestone is scheduled (60–90 days post-launch)
- [ ] MCE Automation Studio and MCAE Engagement Studio are not conflated anywhere in the document

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **MCAE lifecycle stage names do not auto-populate CRM fields** — The MCAE Lifecycle Report uses internally computed stage metrics; it does not write a "current lifecycle stage" value to the Salesforce Lead or Contact record automatically. If CRM-side reporting or Flow logic needs a lifecycle stage field, a separate custom picklist field (`Lifecycle_Stage__c`) must be created on Lead/Contact, and an MCAE automation rule or Engagement Studio completion action must update it at each stage transition. Requirements that assume the Lifecycle Report data is accessible in CRM reports will result in missing data.
2. **Score decay does not fire automation rules** — When MCAE's score decay silently reduces a prospect's score below the MQL threshold, no automation rule or completion action fires to remove the MQL flag or notify Sales. If requirements include a "de-MQL" process (returning a prospect to nurture when their score drops), this must be specified as a separate automation rule that evaluates score against the threshold on a scheduled basis, or a CRM-side scheduled Flow that checks `Score` on Lead records periodically.
3. **MCE Automation Studio is not real-time and does not evaluate individual engagement** — Automation Studio in Marketing Cloud Engagement runs batch processes on a schedule. It cannot evaluate a prospect's current score and route them to Sales when a threshold is crossed in real time. Requirements that describe real-time individual routing must reference MCAE Automation Rules or MCAE Engagement Studio, not MCE Automation Studio.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Platform scope document | Lists which marketing automation platforms are in scope, explicitly excludes others, and maps platform responsibilities |
| Lifecycle stage map | All lifecycle stages in scope with transition triggers, responsible system, and CRM field updates per transition |
| Scoring model specification | Complete scoring source list, point weights, decay rules, ceiling, grade Profile criteria, and negative scoring deductions |
| MQL threshold definition | Agreed threshold (score or score+grade), approver names and sign-off dates, effective date |
| SQL qualification framework | Named framework (BANT/MEDDIC) with confirmed criteria for SQL acceptance |
| Handoff mechanism spec | Automation rule or Engagement Studio step design, CRM field updates, notification method, assignment target |
| Sales SLA document | Max response time by MQL tier, recycle criteria, recycle field requirements, escalation process |
| CRM field requirements list | All Lead/Contact fields required: API name, type, owning system, and purpose |

---

## Related Skills

- `lead-scoring-requirements` — Use for Sales Cloud-only scoring requirements (no MCAE); this skill covers requirements when MCAE or MC Next is the scoring platform
- `mcae-lead-scoring-and-grading` — Implementation skill that consumes the outputs of this requirements skill; use after this skill's artifacts are complete and signed off
- `mcae-pardot-setup` — Prerequisite implementation skill for MCAE Business Unit provisioning and CRM connector setup before scoring configuration begins
- `mcae-engagement-studio` — Implementation skill for building the Engagement Studio programs specified in these requirements
