---
name: agentforce-service-ai-setup
description: "Use this skill to verify prerequisites, license entitlements, and org readiness before enabling Einstein for Service AI features: Case Classification, Article Recommendations, Reply Recommendations, and Work Summaries. Trigger keywords: Einstein for Service setup, enable Case Classification, enable Article Recommendations, enable Reply Recommendations, enable Work Summaries, Einstein generative AI prerequisites, Data Cloud for Work Summaries. NOT for core Agentforce agent setup, Agent Builder topic design, Einstein Copilot configuration, ongoing optimization of already-running features, or Einstein Trust Layer configuration."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
  - Reliability
triggers:
  - "I want to enable Einstein for Service AI features — where do I start and what licenses do I need?"
  - "Case Classification is not available in Setup even though we have Service Cloud — what license or permission am I missing?"
  - "Work Summaries is greyed out or missing from Setup — what prerequisites do I need to enable generative AI features?"
  - "We are setting up Einstein for Service for the first time — what is the correct activation sequence and what can go wrong?"
  - "Article Recommendations or Reply Recommendations require a minimum number of cases or interactions — how do I verify we meet the data thresholds?"
tags:
  - einstein-for-service
  - case-classification
  - article-recommendations
  - reply-recommendations
  - work-summaries
  - service-cloud-einstein
  - einstein-generative-ai
  - data-cloud
  - prerequisites
  - setup
inputs:
  - Salesforce org with Service Cloud license and optionally Service Cloud Einstein or Einstein 1 Service edition
  - List of Einstein for Service features the customer intends to enable
  - Current case volume and closed case history available for model training
  - Whether Messaging or Voice channels are active (required for Work Summaries in some configurations)
  - Whether a Data Cloud entitlement is present
outputs:
  - Prerequisites checklist per feature (predictive AI vs. generative AI)
  - License gap analysis (what is needed vs. what is provisioned)
  - Recommended activation sequence with rationale
  - Data readiness assessment (case volume, Knowledge base, messaging history)
  - Go / No-Go determination for each Einstein for Service feature
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Agentforce Service AI Setup

This skill activates when a practitioner needs to determine org readiness, verify license entitlements, assess data prerequisites, and plan the activation sequence for Einstein for Service AI features: Case Classification, Article Recommendations, Reply Recommendations, and Work Summaries. It does NOT cover the ongoing optimization, accuracy tuning, or troubleshooting of already-running features (see `einstein-copilot-for-service`), Agent Builder configuration, Agentforce autonomous agent setup, or Einstein Trust Layer configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License tier:** Einstein for Service features split across two license tiers. Predictive AI features (Case Classification, Article Recommendations, Reply Recommendations) require Service Cloud Einstein or Einstein 1 Service. Generative AI features (Work Summaries, Service Replies) require an additional Einstein Generative AI entitlement or Einstein 1 Service edition — the base Service Cloud Einstein add-on does NOT include generative AI.
- **Data readiness for predictive AI:** Case Classification requires at minimum 1,000 closed cases with consistent (non-null) values in the fields to be classified for reliable model training. Salesforce's internal documentation states 400 as the floor but recommends 1,000+ for production-quality accuracy. Article Recommendations require an established case-to-article linking history. Reply Recommendations require several thousand historical messaging transcripts.
- **Channel and Data Cloud prerequisites for Work Summaries:** Work Summaries (After-Visit Summary) requires the Einstein Generative AI license plus, in many org configurations, an active Messaging or Voice channel and a Data Cloud entitlement. In orgs without Data Cloud, Work Summaries availability depends on org type and edition.
- **Permission set requirements:** Einstein for Service features are not automatically visible to all users after license provisioning. Dedicated permission sets (`Service Cloud Einstein`, `Einstein for Service`) must be explicitly assigned.

---

## Core Concepts

### Predictive AI Features vs. Generative AI Features

Einstein for Service features fall into two distinct categories with different license requirements, data prerequisites, and setup paths.

**Predictive AI features** — Case Classification and Article Recommendations — use machine learning models trained on your org's historical closed case data. They require Service Cloud Einstein or Einstein 1 Service. Model training is asynchronous (24–72 hours for initial training) and depends on data quality and volume. The minimum floor for Case Classification model training is 400 closed cases, but production-quality accuracy requires 1,000+ closed cases with consistent field population in the fields to be classified.

**Generative AI features** — Work Summaries (After-Visit Summary) and Service Replies — use large language models accessed through the Einstein Trust Layer. They require the Einstein Generative AI entitlement (included in Einstein 1 Service, or purchasable as an add-on to Service Cloud Einstein). No historical case data is required for training since these features use pre-trained LLMs grounded in the current conversation transcript or Knowledge articles, but channel and Data Cloud prerequisites apply for Work Summaries.

Understanding this split is critical before any enablement work. Orgs that discover mid-implementation that they lack the generative AI entitlement face a licensing procurement cycle that can delay go-live by weeks.

### Case Classification Data Requirements

Case Classification trains a machine learning model on closed cases in your org. The model predicts the correct value for picklist fields on the Case object (Case Type, Priority, Case Reason, and custom picklist fields). For the model to be useful:

- **Volume:** At least 400 closed cases (Salesforce floor), ideally 1,000+ for reliable predictions.
- **Completeness:** The fields to be classified must have non-null, consistent values in historical closed cases. If agents have been inconsistently filling in Case Type (e.g., 40% null rate), the model has insufficient training signal for that field and its predictions will be unreliable.
- **Distribution:** The training data should reflect realistic future case distribution. If your historical closed cases are unrepresentative of current case volume or case type mix, the model may perform worse than expected on production traffic.

Orgs that are net-new to Salesforce or have recently migrated may have very few closed cases, making Case Classification unsuitable until more case history accumulates.

### Work Summaries Channel and Data Cloud Dependencies

Work Summaries generates an AI-written summary of a service interaction (what the issue was, what was done, what the resolution was) from the conversation transcript. It is specifically designed for interactions that produce a transcript — Messaging sessions (SMS, WhatsApp, Facebook Messenger via Messaging for In-App and Web), Voice calls (Einstein Conversation Intelligence), and bot conversations.

In many org configurations, Work Summaries also requires a **Data Cloud entitlement** to ingest and store transcript data before the LLM summarization step can run. Without Data Cloud, Work Summaries may be unavailable or limited depending on org edition and feature packaging. Verifying Data Cloud entitlement is a prerequisite check that is frequently missed.

Work Summaries also goes through the Einstein Trust Layer, which applies data masking and grounding enforcement before the transcript is processed by the LLM. No customer data leaves Salesforce's infrastructure.

### License Verification Path

Before enabling any Einstein for Service feature, verify entitlements in Setup:

1. **Setup > Company Information > Feature Licenses** — look for `Service Cloud Einstein` or `Einstein 1 Service` seats
2. **Setup > Company Information > Permission Set Licenses** — look for `Einstein Generative AI` or `Einstein 1 Service` PSL for generative features
3. **Setup > Data Cloud** — verify Data Cloud entitlement if Work Summaries is in scope

Do not rely on what a license quote says — verify provisioned entitlements directly in Setup before beginning enablement work.

---

## Common Patterns

### Pattern 1: Full Einstein for Service Prerequisites Assessment

**When to use:** Before any Einstein for Service enablement project begins. Use this to produce a go/no-go determination per feature.

**How it works:**

1. Confirm org edition and license tier from Setup > Company Information > Feature Licenses. Record whether `Service Cloud Einstein` and/or `Einstein Generative AI` are present.
2. Run a Case report on closed cases in the last 18 months. Count total closed cases. For each field the customer wants to classify, calculate the null/blank rate. Document results.
3. Assess Knowledge base: Is Salesforce Knowledge enabled? How many published articles exist? Are agents currently linking articles to cases at resolution?
4. Assess messaging channels: Is Messaging (In-App and Web, or partner messaging) or Voice active? This determines Reply Recommendations and Work Summaries eligibility.
5. Check for Data Cloud: Setup > Data Cloud > check provisioning status. Note whether Data Cloud entitlement exists.
6. Produce a feature-by-feature readiness matrix (see Decision Guidance below).

**Why not skipping the assessment:** Customers regularly assume that purchasing Service Cloud Einstein unlocks all Einstein for Service features including generative AI. Discovering mid-project that Work Summaries requires a separate license — or that Case Classification cannot train because case volume is below threshold — resets timelines and erodes confidence.

### Pattern 2: Phased Activation Sequence

**When to use:** Org has passed the prerequisites assessment and is ready to activate features. Use this pattern to activate in the correct order to avoid dependency failures.

**How it works:**

1. Assign permission sets first: Assign `Service Cloud Einstein` and/or `Einstein for Service` permission sets to target agents and admins.
2. Enable Case Classification (Setup > Service > Einstein Classification Apps > Case Classification). Select only fields with >80% historical data completeness. Enable in Suggestion mode initially — not auto-populate — to allow the model to be reviewed before it acts autonomously.
3. Enable Article Recommendations (Setup > Service > Einstein Article Recommendations). Confirm Knowledge is active and articles are published.
4. Add UI components to Lightning record pages: Case Classification component and Einstein Article Recommendations component must be added manually via Lightning App Builder.
5. Wait for model training to complete before assessing feature quality (24–72 hours).
6. Enable Reply Recommendations only after the Training Data job has been explicitly run in Setup. Do NOT assume the feature activates automatically.
7. Enable Work Summaries and/or Service Replies only if Einstein Generative AI entitlement is confirmed and channel prerequisites are met.

**Why phased vs. all-at-once:** Enabling all features simultaneously makes it impossible to isolate which feature is producing problems during initial validation. Phased activation with validation gates between steps surfaces configuration issues before they compound.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org has fewer than 1,000 closed cases with consistent field values | Defer Case Classification; document case volume gap | Model can train at 400 but predictions will be unreliable; poor suggestions erode agent trust before adoption is established |
| Customer wants Work Summaries but only has Service Cloud Einstein add-on | Escalate license gap before any enablement work | Work Summaries requires Einstein Generative AI entitlement; this is a procurement item, not a configuration fix |
| Messaging or Voice channels are not yet active | Defer Reply Recommendations and Work Summaries | Both features require active channel transcripts; no channel = no transcript = no feature |
| Data Cloud entitlement is absent | Assess org edition carefully before promising Work Summaries | In many configurations Data Cloud is required; verify with Salesforce AE before committing |
| Knowledge base has fewer than 50 published articles | Defer Article Recommendations; build Knowledge content first | Recommendations are only as good as the article corpus; thin Knowledge = irrelevant recommendations |
| Org is net-new to Salesforce (no closed case history) | Enable predictive AI features in parallel with building case history | Set a milestone to revisit Case Classification activation at 1,000 closed cases |
| Org has sufficient license and data prerequisites | Follow phased activation sequence | Phased activation isolates issues and builds agent confidence feature-by-feature |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner executing Einstein for Service setup:

1. **Verify licenses:** Confirm provisioned entitlements in Setup > Company Information > Feature Licenses and Permission Set Licenses. Do not proceed until you have confirmed which features the license tier actually unlocks.
2. **Assess data readiness:** Run closed case reports to count volume and measure field completeness for all fields intended for Case Classification. Assess Knowledge article count and publication status. Assess Messaging/Voice channel status for generative AI features.
3. **Verify Data Cloud entitlement** if Work Summaries is in scope. If absent, flag as a licensing gap requiring procurement before generative AI features can be enabled.
4. **Produce a feature readiness matrix:** For each Einstein for Service feature in scope, document: license requirement met (Y/N), data threshold met (Y/N), channel prerequisite met (Y/N), go/no-go determination.
5. **Execute phased activation:** Assign permission sets, enable predictive features, add Lightning components, wait for model training, then enable generative features if prerequisites are confirmed.
6. **Validate each feature:** Confirm model training status in Setup before marking the feature live. For generative features, run a test interaction and verify the feature produces output.
7. **Document any deferred features:** For any feature where prerequisites are not met, record the gap and the condition that must be met before it can be activated.

---

## Review Checklist

Run through these before marking Einstein for Service setup work complete:

- [ ] Service Cloud Einstein or Einstein 1 Service license confirmed in Setup > Company Information > Feature Licenses
- [ ] Einstein Generative AI entitlement separately confirmed if Work Summaries or Service Replies are in scope
- [ ] Data Cloud entitlement verified if Work Summaries is in scope
- [ ] Closed case volume assessed: 1,000+ cases for reliable Case Classification (document actual count)
- [ ] Case field completeness assessed: each classified field has >80% non-null values in closed case history
- [ ] Salesforce Knowledge enabled and published articles exist (for Article Recommendations and Service Replies)
- [ ] Messaging or Voice channel active if Reply Recommendations or Work Summaries are in scope
- [ ] `Service Cloud Einstein` or `Einstein for Service` permission sets assigned to all target users
- [ ] Feature readiness matrix produced with go/no-go per feature
- [ ] Lightning components (Case Classification, Article Recommendations) added to Case record page via Lightning App Builder
- [ ] Case Classification enabled in Suggestion mode (not auto-populate) for initial validation
- [ ] Reply Recommendations Training Data job explicitly run before expecting suggestions
- [ ] Model training status confirmed as Active before go-live assessment

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Work Summaries requires Einstein Generative AI license — not just Service Cloud Einstein** — Service Cloud Einstein (the add-on) covers predictive AI features only. Work Summaries and Service Replies are generative AI features requiring a separate Einstein Generative AI entitlement or Einstein 1 Service edition. Customers who purchase only Service Cloud Einstein will find Work Summaries greyed out or absent from Setup. This is a licensing gap, not a configuration problem.

2. **Case Classification needs 1,000+ closed cases for reliable predictions, not just 400** — Salesforce documentation states 400 closed cases as the minimum for model training to run. However, 400 cases typically produces a model with poor precision that agents quickly lose trust in. The practical threshold for production-quality accuracy is 1,000+ closed cases with consistent field population in the fields being classified.

3. **Reply Recommendations require an explicit Training Data job before the feature activates** — Simply enabling Reply Recommendations in Setup does not activate the model. An admin must explicitly run the Training Data job from Setup > Service > Einstein Reply Recommendations before the model can be built. Skipping this step results in the feature being technically "enabled" but producing no suggestions — which is indistinguishable from a broken configuration without this knowledge.

4. **Data Cloud entitlement is required for Work Summaries in many configurations** — This prerequisite is frequently omitted from feature overview documentation and comes as a surprise during setup. In orgs without Data Cloud, Work Summaries may be unavailable depending on org edition and packaging. Always verify Data Cloud provisioning before promising Work Summaries availability to a customer.

5. **Lightning components must be manually added to record pages — enabling the feature is not enough** — Case Classification and Article Recommendations produce no visible output until their corresponding Lightning components are added to the Case record page or service console layout via Lightning App Builder. Enabling the feature in Setup without placing the components on the page layout is one of the most common causes of "it's enabled but nothing is showing up" support tickets.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Feature readiness matrix | Per-feature go/no-go determination with license, data, and channel prerequisites documented |
| License gap analysis | Record of which entitlements are present vs. required per feature |
| Case volume and field completeness report | Closed case count and per-field null rate for Case Classification readiness |
| Phased activation plan | Ordered sequence of activation steps with validation gates |
| Permission set assignment list | Confirmed list of users assigned Einstein for Service permission sets |
| Einstein for Service setup checklist | Completed checklist confirming all prerequisites met before go-live |

---

## Related Skills

- `einstein-copilot-for-service` — Use after initial setup for ongoing optimization, accuracy tuning, troubleshooting, and configuration of Einstein for Service features already running in production
- `einstein-trust-layer` — Configure data masking, grounding enforcement, and audit trails for generative AI features (Work Summaries, Service Replies) as part of the security review before go-live
- `agentforce-agent-creation` — Use when creating an autonomous Agentforce Service Agent via Agent Builder, which is a separate capability from the embedded Einstein for Service features covered by this skill
