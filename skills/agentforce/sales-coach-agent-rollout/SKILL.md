---
name: sales-coach-agent-rollout
description: "Use when an admin or RevOps team is rolling out the out-of-the-box Sales Coach agent (the Agentforce template that role-plays opportunity-stage conversations with reps for Discovery, Needs Analysis, Qualification, Proposal/Pricing, and Negotiation/Review). Covers prerequisites (Agentforce SKU, Einstein Generative AI activation, Opportunity stage hygiene, knowledge grounding), stage-by-stage prompt configuration, customizing role-play scenarios with org-specific objections and value props, privacy posture for what gets captured in LLM context vs persisted, console-vs-portal embedding choices, and a measurement plan tying coached opportunities to win-rate signal. Triggers: 'roll out sales coach agent', 'set up Agentforce sales coach for our reps', 'sales coach not engaging reps on early-stage opps', 'customize sales coach role-play scenarios for our industry', 'how do we measure sales coach effectiveness', 'sales coach feedback contradicts our methodology'. NOT for rolling out an HR or employee self-service agent instead — use agentforce/employee-hr-service-agent-rollout. NOT for building a bespoke agent from scratch rather than configuring a shipped template — use agentforce/agentforce-agent-creation."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - sales-coach-agent-rollout
  - agentforce
  - sales-coach
  - opportunity-stages
  - role-play
  - rep-enablement
triggers:
  - "we just bought Agentforce — how do we roll out the Sales Coach template"
  - "sales coach isn't engaging reps on Discovery-stage opportunities"
  - "customize sales coach role-play scenarios for our industry and ICP"
  - "what does sales coach actually log — privacy review for legal"
  - "should sales coach live in the sales console or in a separate tab"
  - "how do we tell if sales coach is making reps better — measurement plan"
  - "sales coach is giving advice that contradicts our sales methodology"
  - "sales coach won't trigger because our opportunity stages are renamed"
  - "rep adoption of sales coach is below 10% — what now"
inputs:
  - "Edition / SKU: which Agentforce tier the org is on (Foundations vs Sales / Service / Premier add-ons)"
  - "Sales methodology in use (MEDDIC, BANT, Challenger, etc.) and whether it's documented in a knowledge source"
  - "Opportunity stage list (standard vs renamed/custom) and current stage hygiene"
  - "Where reps work today: classic console, Lightning sales console, partner portal, mobile"
  - "Privacy/compliance posture: regulated industry, EU residency requirements, LLM-data-retention policy"
outputs:
  - "Rollout plan: prerequisites checklist, stage-prompt configuration, knowledge grounding sources, rep cohort plan"
  - "Stage-by-stage prompt activation map (which coached behaviors fire on which Opportunity stage)"
  - "Customized role-play scenario examples grounded in org-specific objections and value props"
  - "Privacy memo: what's sent to the LLM, what's logged where, retention defaults, opt-out path"
  - "Measurement plan with leading indicators (engagement frequency) and lagging indicators (win-rate delta, ramp time)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-08
---

# Sales Coach Agent Rollout

Activate this skill when an admin, enablement lead, or RevOps team is rolling out the **Sales Coach** agent — the Agentforce out-of-the-box template that role-plays opportunity-stage conversations with sellers and gives stage-appropriate feedback. The skill is about *deployment, configuration, and adoption* of the template, not about building a bespoke coaching agent from scratch.

Note on naming: depending on doc vintage and licensing pack, this template is referenced as **Sales Coach**, **Agentforce Sales Coach**, or **Einstein Sales Coach**. Treat the names as interchangeable for this skill — the underlying template is the same.

---

## Before Starting

Gather this context before configuring anything:

- **Confirm the SKU and entitlement.** Sales Coach is part of the Agentforce add-on (typically Agentforce for Sales). Verify in Setup → Company Information → Used Licenses, and confirm Einstein Generative AI is activated (Setup → Einstein → Einstein Setup). Without the SKU you can see the template in Agent Builder but cannot publish.
- **Inventory Opportunity stage hygiene.** Sales Coach prompts are keyed to *standard* opportunity-stage semantics — Discovery, Needs Analysis, Qualification, Proposal/Price Quote, Negotiation/Review. If the org has renamed stages (`Stage 1`, `Stage 2`, `Closed-MaybeNotReally`), the template's stage triggers will not match by label. Either align internal stages back to the standard names or plan to remap stage triggers in Agent Builder.
- **Identify the methodology source of truth.** If the org runs MEDDIC, Challenger, BANT, etc., locate where it lives — a Knowledge article, a SharePoint deck, a Notion page. Sales Coach uses retrieval-augmented grounding via the Data Cloud / Einstein knowledge layer; if your methodology is not in a grounded knowledge source, the coach will default to generic best practices that may contradict your playbook.
- **Review compliance posture.** Sales Coach sends Opportunity context (account name, stage, amount, products, notes) plus the rep's typed input to the LLM. For regulated verticals (financial services, healthcare, government) and EU-residency tenants, the Einstein Trust Layer applies, but you still need a documented data-flow diagram for legal review before publishing.
- **Pick a pilot cohort.** Sales Coach effectiveness is measured by behavior change in pipeline reps — that requires 8–12 weeks of usage. Picking a cohort up front (e.g., one segment, one region, one quota tier) gates the measurement plan.

---

## Core Concepts

### Concept 1 — What Sales Coach actually is

Sales Coach is a packaged Agentforce *agent template* — a pre-defined agent with topics, actions, and instructions tuned to opportunity-stage selling. It does three things, layered:

1. **Role-plays a buyer.** A rep asks for practice on a specific stage; the coach plays the buyer side of the conversation, reacting to the rep's pitch with realistic objections, push-back, and follow-up questions.
2. **Critiques the rep's approach.** After or during the role-play, the coach evaluates the rep's responses against the configured methodology — did they discover pain, qualify budget, handle the objection, surface a value prop?
3. **References Opportunity context.** When invoked from an Opportunity record, the coach reads the record (stage, amount, contacts, products) and tailors the role-play to that deal — buyer persona implied by Account Industry, objections likely for the product, etc.

What it is *not*: a real-time call coach (that is a separate Einstein Conversation Insights product), a deal-review summarizer (that's Sales Cloud Einstein Opportunity Insights), or an autonomous deal-progressor. It only acts when a rep starts a conversation with it.

### Concept 2 — Stage configuration: which prompts activate on which stage

Sales Coach ships with five stage personas mapped to the standard Opportunity stages. The mapping is enforced via topic instructions inside the agent — not via a hard-coded SOQL filter — which means stage names *labels* matter.

| Standard stage | Coached behaviors |
|---|---|
| Prospecting / Qualification | Cold-outreach role-play, BANT/MEDDIC qualification questioning, ICP fit-checking |
| Discovery | Open-question framing, pain identification, decision-criteria extraction |
| Needs Analysis | Stakeholder mapping, technical-fit probing, evaluation-process clarification |
| Proposal / Price Quote | Value-prop articulation, pricing objection rehearsal, ROI framing |
| Negotiation / Review | Concession strategy, mutual close plan, redline / legal handoff |

Two patterns matter for activation:

- **Stage-name match.** The shipped prompts reference stage names verbatim. If your `OpportunityStage` picklist values are `Discovery` and `Needs Analysis` you're fine; if they're `Stage 2 — Discover` and `Stage 3 — Validate`, the coach won't auto-suggest the right role-play scenario when invoked from a record. Fix: either rename stages back to standard, or edit the agent topic instructions in Agent Builder to reference your local stage names.
- **Open vs closed opportunities.** Sales Coach is intended for *open* pipeline. The shipped agent topics filter to `IsClosed = false` so a Closed-Won opportunity won't trigger Negotiation role-play. If your team uses a "post-mortem" stage on closed opps, that flow is *not* what Sales Coach does — point reps to a different debrief tool.

### Concept 3 — Customizing role-play scenarios

The shipped role-play prompts are deliberately generic. A rollout that stops at "default + publish" produces a coach that sounds like a B-school case study — directionally right, never actually relevant. Three customization points matter:

1. **Industry and persona seeds.** In Agent Builder, the topic instructions for each stage allow free-text additions like "When playing the buyer persona, default to a {Industry} {Title} archetype with {top 3 priorities}." Inject your ICP segments here. This is the highest-leverage customization — it transforms generic coaching into "you're now selling to a CISO at a 5,000-employee health system."
2. **Objection library.** The coach generates objections from the LLM's general knowledge, augmented by grounded knowledge sources. If your sellers face specific objections (`"why your platform vs incumbent X"`, `"the data residency question"`, `"ROI for the SMB tier is hard to justify"`), put them in a Knowledge article tagged for Agent grounding. The coach will then surface them during role-play.
3. **Value-prop and proof-point grounding.** Same mechanism — a Knowledge article enumerating your three top value props, key proof points, and competitive battle cards is *the* substrate for the coach's critique behavior. Without it, "did the rep handle the value prop well?" defaults to LLM generality.

The general rule: every customization belongs in *grounded data* (knowledge articles, Data Cloud objects), not in *agent instructions*. Agent instructions describe behavior; data describes the world. Don't stuff your battle cards into the agent's system prompt — they'll go stale and you can't version them.

### Concept 4 — Measurement: leading and lagging indicators

A Sales Coach rollout without a measurement plan is theater. Two layers:

- **Leading indicators (week 1–4).** Engagement frequency per rep, average session length, stages-coached distribution, follow-up question depth. All retrievable from Agentforce usage analytics in Setup → Einstein → Agentforce Analytics. These tell you if reps are *using* the coach.
- **Lagging indicators (week 8–24).** Win-rate delta between coached and uncoached opportunities (within the same segment), stage-velocity delta on coached opps, ramp-time delta for new hires given coach access vs not. These require a custom field or a flag (`Coach_Sessions_On_This_Opp__c`) plus a dashboard joining Opportunity outcome to coach engagement.

Common analytical mistake: comparing coached-opp win rate to global win rate. Reps who choose to use the coach are not random — they self-select for engagement and effort, biasing upward. Always compare *within* a segment (region, quota tier, product) and ideally use a randomized opt-in cohort.

---

## Recommended Workflow

1. **Verify prerequisites.** Confirm Agentforce SKU, Einstein Generative AI activation, Trust Layer settings, and Opportunity stage hygiene. Run the bundled `scripts/check_sales_coach_agent_rollout.py` against retrieved metadata to detect: missing agent definition, opportunity-stage drift from standard, absent grounded knowledge sources tagged for Sales Coach.
2. **Ground the methodology.** Locate or author the canonical methodology document (MEDDIC, BANT, Challenger, custom). Publish as a Knowledge article with the data-classification + Agent-accessible flag set. Without this, customization is shallow.
3. **Customize stage prompts in Agent Builder.** Open the Sales Coach template, walk each of the five stage topics, and inject ICP seeds, industry archetypes, and references to grounded knowledge. Do *not* paste battle cards directly into instructions — reference grounded sources.
4. **Configure the embed surface.** Decide between (a) embedding in the Lightning sales console as a utility item / Einstein panel, (b) embedding on the Opportunity record page as a component, or (c) launching a separate `/agentforce` portal. Console embedding has the highest engagement; portal isolates legal exposure if you're nervous. Pick one for the pilot — don't do all three.
5. **Run a privacy review.** Document what data flows to the LLM (Opportunity fields read by the agent's actions, rep's typed input), what is logged (Agentforce session logs in Setup → Einstein), and retention defaults. Get sign-off from legal/compliance before publishing to production. For EU tenants confirm Einstein Trust Layer EU data-residency settings are honored.
6. **Pilot with the chosen cohort.** Publish to a subset of users via permission set. Communicate the *purpose* (practice tool, not a deal-tracking tool, no manager surveillance), the *measurement plan*, and the feedback loop (where reps report bad coaching). Run 4 weeks before expanding.
7. **Re-measure and iterate.** At week 4, re-run the checker, pull engagement analytics, and gather rep feedback. Tune objection library and ICP seeds based on what reps say felt off. At week 8–12, evaluate lagging indicators and decide expand / hold / sunset.

---

## Related Skills

- `agentforce/agent-actions` — designing custom Agentforce actions if shipped Sales Coach actions need extension (see also templates/agentforce/AgentActionSkeleton.cls)
- `agentforce/prompt-builder-templates` — Prompt Builder mechanics for any custom prompt templates referenced by the agent
- `agentforce/einstein-trust-layer` — Trust Layer masking, data-residency, and audit-log configuration that applies to all Agentforce agents
- `admin/opportunity-management` — keeping standard stage names so packaged agents and reports work as designed
- `admin/knowledge-base-administration` — authoring, Data Categories, and publishing workflow for the Knowledge articles the agent grounds on (methodology, battle cards, objection libraries)
- `admin/ai-adoption-change-management` — broader adoption and measurement framework for any Agentforce agent rollout
