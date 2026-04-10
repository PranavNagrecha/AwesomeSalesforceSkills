# Gotchas — Marketing Automation Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: MCAE Lifecycle Report Stages Are Not CRM Fields

**What happens:** Stakeholders review the MCAE Lifecycle Report in B2B Marketing Analytics and assume the stage values (Visitor, Prospect, MQL, SQL, Opportunity, Customer, Won) are written to a field on the Salesforce Lead or Opportunity record. They request CRM reports and dashboards filtered by "current lifecycle stage" and are told the data does not exist.

**When it occurs:** When requirements assume that the Lifecycle Report's stage metrics automatically populate a CRM field without an explicit automation rule or completion action to do so. The MCAE Lifecycle Report is computed from MCAE activity data and CRM object records at report run time; it does not persistently write a stage value to a field.

**How to avoid:** Requirements must explicitly call out a `Lifecycle_Stage__c` custom picklist field on Lead and Contact (and potentially Opportunity) that MCAE automation rules and Engagement Studio completion actions update at each stage transition. Each transition — Prospect → MQL, MQL → SQL, SQL → Opportunity — must have a corresponding automation action that writes the new stage value to this field. This field is what enables CRM-side lifecycle reporting.

---

## Gotcha 2: Score Decay Does Not Trigger Automation Rules or De-MQL Processes

**What happens:** A prospect crosses the MQL threshold (Score >= 100, Grade >= B), is assigned to Sales, and the rep does not follow up. Over 60 days, score decay reduces the prospect's score to 70. The prospect is no longer above the MQL threshold, but the `Is_MQL__c` checkbox, the `MQL_Date__c` stamp, and the Sales queue assignment all remain unchanged. The prospect sits in the Sales queue indefinitely with a stale MQL flag and a score that no longer qualifies.

**When it occurs:** When requirements specify score decay rules but do not include a corresponding "de-MQL" or recycle automation to handle prospects whose score falls below the threshold post-decay. MCAE's score decay silently reduces scores without re-evaluating automation rules or firing completion actions.

**How to avoid:** Requirements must include a separate recycle automation specification: an MCAE Automation Rule (or scheduled CRM Flow) that evaluates prospects currently flagged as MQL whose current score has dropped below the threshold, and triggers a recycle action: resets `Is_MQL__c = false`, sets `Lifecycle_Stage__c = "Prospect"`, adds the prospect to a re-nurture list, and notifies the assigned rep. This rule must be listed explicitly in requirements alongside the MQL handoff rule — it is not automatic.

---

## Gotcha 3: MCAE Score and Grade Sync Is One-Way From MCAE to CRM

**What happens:** A Salesforce admin builds a Flow that writes a manually adjusted score to the `Score` field on the Lead record (e.g., to promote a VIP contact to MQL status). The next time MCAE syncs (typically every few minutes), MCAE overwrites the CRM `Score` field value with the MCAE-maintained score, silently discarding the manual adjustment. The VIP contact reverts to a non-MQL status.

**When it occurs:** When requirements do not explicitly prohibit CRM-side writes to MCAE-synced fields (`Score`, `Grade`, `Pardot_Score__c`, or whatever field names are mapped in the MCAE connector). Any CRM automation — Flow, Process Builder, Apex trigger — that writes to these fields will be overwritten by MCAE on the next sync.

**How to avoid:** Requirements must identify the MCAE-synced fields on Lead and Contact and explicitly flag them as read-only from the CRM side. If manual MQL promotion is a business requirement, the requirements document must specify that manual overrides are performed in the MCAE UI (on the MCAE prospect record), not by editing the CRM field — because MCAE-side manual overrides are respected and prevent automatic re-scoring. CRM-side field protection (field-level security or a validation rule blocking non-system writes) is a recommended safeguard to document in requirements.

---

## Gotcha 4: MCAE Automation Rules Are Retroactive on Activation

**What happens:** The implementation team finishes configuring the MQL Automation Rule and activates it. Within minutes, hundreds of existing prospects who have accumulated score above the threshold over months of previous campaigns are simultaneously assigned to the Sales queue, creating CRM tasks and flooding reps with hundreds of alerts at once.

**When it occurs:** When requirements do not address the retroactive behavior of MCAE Automation Rules. When an Automation Rule is activated, MCAE evaluates all existing prospects in the database against the rule criteria immediately — not just future prospects going forward. A threshold-based rule on an org with thousands of existing prospects causes a mass assignment event on activation.

**How to avoid:** Requirements must include a launch strategy for the MQL Automation Rule that accounts for the existing prospect population. Options to specify: (a) add a "Date Created after [launch date]" criterion to the initial rule to restrict it to new prospects during the rollout period; (b) run the rule in a controlled segment (test list) before full database activation; (c) schedule a "clean sweep" with Sales to process existing above-threshold prospects manually before the rule goes live. The chosen approach must be documented in requirements so the implementation team and Sales are aligned on the activation plan.

---

## Gotcha 5: MC Next Scoring Models and MCAE Scoring Are Not Interchangeable

**What happens:** An org begins a migration from MCAE to Marketing Cloud Next. Requirements are written using MCAE scoring terminology (Automation Rules, Profiles, decay rules) but the implementation is on MC Next's Scoring Model framework. The implementation team finds that MC Next Scoring Models do not have the same configuration structure — there are no "Automation Rules" in MC Next, Profiles are not the grading mechanism, and decay is configured differently using the Scoring Model's recency weighting. The requirements document cannot be implemented as written.

**When it occurs:** When requirements writers assume MCAE and MC Next have the same scoring architecture because both are "Salesforce marketing platforms." They are architecturally different: MCAE scoring operates on the MCAE prospect record; MC Next Scoring Models operate on Data Cloud Individual profiles using engagement event streams.

**How to avoid:** Requirements must be written for the specific platform. If the org is using MC Next, requirements must describe MC Next Scoring Model configuration: engagement event streams in scope, scoring dimensions and weights in the Data Cloud scoring framework, recency weighting settings, the Individual profile field that surfaces the output score, and the CRM connector mapping that brings the score into Salesforce Lead/Contact fields. Do not reuse MCAE-specific terminology (Automation Rules, Profiles, decay scoring admin UI) in MC Next requirements.
