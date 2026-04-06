---
name: einstein-next-best-action
description: "Guide practitioners through building Einstein Next Best Action strategies using Flow Builder, configuring Recommendation records, and surfacing recommendations via the Actions & Recommendations Lightning component. Trigger keywords: next best action, NBA strategy, surface recommendations. NOT for Einstein Prediction Builder model training, Einstein Bots conversation design, or Agentforce agent topic routing."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Scalability
triggers:
  - "How do I build an NBA strategy to surface contextual recommendations on a record page?"
  - "My Actions & Recommendations component is not displaying any recommendations to users"
  - "I need to migrate from Strategy Builder to Flow Builder for next best action strategies"
tags:
  - einstein-next-best-action
  - recommendations
  - flow-builder
  - actions-and-recommendations
  - nba-strategy
inputs:
  - "Business rules defining which recommendations apply to which records or segments"
  - "Recommendation sObject records with Name, Description, ActionReference, AcceptanceLabel, and RejectionLabel"
  - "Target Lightning record page or app page where recommendations should appear"
outputs:
  - "Flow-based NBA strategy that returns List<Recommendation> via an output variable"
  - "Configured Actions & Recommendations Lightning component on the target page"
  - "Recommendation sObject records with linked acceptance actions (Flows or quick actions)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Einstein Next Best Action

Einstein Next Best Action (NBA) surfaces contextual, actionable recommendations to users directly within Lightning record pages. This skill activates when a practitioner needs to design, build, or troubleshoot NBA strategies, Recommendation records, or the Actions & Recommendations component.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has the "Einstein Next Best Action" permission set license assigned to relevant users, and that the Recommendation standard object is accessible.
- The most common wrong assumption is that Strategy Builder is still the tool for authoring strategies. Since Spring '24, Strategy Builder is deprecated and all NBA strategies must be built as Autolaunched Flows that output `List<Recommendation>`.
- The Actions & Recommendations component displays a maximum of 25 recommendations per invocation. Flow interview limits and Recommendation record volume can both constrain throughput.

---

## Core Concepts

### Recommendation sObject

The Recommendation standard object is the data backbone of NBA. Each record stores a Name, Description, ActionReference (the API name of the Flow or quick action to execute on acceptance), AcceptanceLabel, RejectionLabel, and an optional ExpirationDate. Recommendations are not tied to a specific record type by default — your strategy Flow handles filtering and relevance logic. Creating clean, well-named Recommendation records with clear AcceptanceLabel text ("Enroll in Loyalty Program") is critical because that label is what users see on the component button.

### NBA Strategy as a Flow

Since Spring '24, NBA strategies are Autolaunched Flows (not the legacy Strategy Builder). The Flow must define an output variable of type `List<Recommendation>` (collection variable, sObject type = Recommendation). Inside the Flow, you query or construct Recommendation records, apply filtering and sorting logic using Decision and Assignment elements, and assign the final filtered list to the output variable. The Actions & Recommendations component invokes this Flow at page load and when manually refreshed.

### Actions & Recommendations Component

This is the standard Lightning Web Component that renders recommendations on a page. You configure it in Lightning App Builder by selecting which strategy Flow to invoke. When a user clicks the acceptance button, the platform executes the Flow or quick action referenced in the Recommendation's ActionReference field. Rejection dismisses the recommendation for that user/session. The component supports up to 25 visible recommendations at a time.

---

## Common Patterns

### Flow-Based Strategy with Record-Context Filtering

**When to use:** You want to show different recommendations based on the current record's field values (e.g., Account industry, Case priority, Opportunity stage).

**How it works:**
1. Create Recommendation records for each possible action (e.g., "Upsell Premium Plan", "Schedule Renewal Call").
2. Build an Autolaunched Flow. Add a Record Variable input of the relevant sObject type (e.g., Account).
3. Use a Get Records element to retrieve all active Recommendation records.
4. Add Decision elements to filter recommendations based on the input record's fields.
5. Assign the filtered recommendations to the output `List<Recommendation>` variable.
6. Place the Actions & Recommendations component on the record page and select this Flow as the strategy.

**Why not the alternative:** Hardcoding recommendation logic in Apex bypasses the declarative management and versioning that Flow provides, and makes it harder for admins to modify business rules without developer involvement.

### Expiration-Based Recommendation Lifecycle

**When to use:** Recommendations are time-sensitive (seasonal promotions, limited-time offers, compliance deadlines).

**How it works:**
1. Set the ExpirationDate field on each Recommendation record to the date it should stop appearing.
2. In your strategy Flow, add a Decision element that filters out recommendations where ExpirationDate is before TODAY.
3. Optionally, create a Scheduled Flow that deactivates or archives expired Recommendation records on a nightly basis.

**Why not the alternative:** Relying solely on manual deactivation of Recommendation records leads to stale recommendations appearing to users, eroding trust in the system.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Simple static recommendations (fewer than 10) | Flow with Get Records + Decision elements | Low maintenance, easy for admins to modify |
| Dynamic recommendations based on complex scoring | Flow calling an Invocable Apex action for scoring, returning sorted list | Keeps scoring logic testable in Apex while Flow handles orchestration |
| Time-limited promotional recommendations | ExpirationDate field + Flow filter + Scheduled Flow cleanup | Automatic lifecycle management without manual intervention |
| Recommendations differ by user profile or role | Flow Decision branches checking $User.ProfileId or custom permission | Declarative segmentation without custom code |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites** — Confirm the Einstein Next Best Action permission set license is assigned, the Recommendation object is accessible, and the target Lightning page exists in Lightning App Builder.
2. **Define Recommendation records** — Create Recommendation sObject records for each action. Populate Name, Description, ActionReference (API name of the acceptance Flow or quick action), AcceptanceLabel, RejectionLabel, and optionally ExpirationDate.
3. **Build the strategy Flow** — Create an Autolaunched Flow. Define a collection output variable of type Recommendation. Add Get Records to pull Recommendation records, Decision elements for filtering, and Assignment elements to build the output list.
4. **Wire acceptance actions** — Ensure every ActionReference on a Recommendation record points to a valid, active Flow or quick action. Test each acceptance action independently before connecting it to the recommendation.
5. **Place the component** — In Lightning App Builder, drag the Actions & Recommendations component onto the target record page. Configure it to use the strategy Flow. Activate the page.
6. **Test end-to-end** — Open a record that matches your strategy's criteria. Verify that the correct recommendations appear, acceptance triggers the correct action, and rejection dismisses the recommendation.
7. **Review and iterate** — Check that no more than 25 recommendations are returned per invocation, expired recommendations are filtered out, and acceptance labels are clear and actionable for end users.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Einstein Next Best Action permission set license is assigned to target users
- [ ] All Recommendation records have valid ActionReference values pointing to active Flows or quick actions
- [ ] Strategy Flow defines an output variable of type `List<Recommendation>` (collection, sObject = Recommendation)
- [ ] Strategy Flow filtering logic excludes expired recommendations (ExpirationDate < TODAY)
- [ ] Actions & Recommendations component is placed on the correct Lightning page and configured with the strategy Flow
- [ ] Acceptance actions execute correctly when the user clicks the acceptance button
- [ ] No more than 25 recommendations are returned per strategy invocation
- [ ] AcceptanceLabel and RejectionLabel text is clear and user-friendly

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Strategy Builder is deprecated** — Since Spring '24, Strategy Builder is fully deprecated. Any references to Strategy Builder in documentation or existing implementations must be migrated to Flow Builder. New orgs may not have Strategy Builder available at all.
2. **ActionReference must match an active Flow or quick action API name exactly** — If the referenced Flow is deactivated or the API name has a typo, the acceptance button will silently fail or throw an unhandled error. There is no compile-time validation between the Recommendation record and the referenced action.
3. **25-recommendation display cap** — The Actions & Recommendations component renders a maximum of 25 recommendations. If your strategy Flow returns more, the extras are silently dropped. You must implement priority sorting in the Flow to ensure the most important recommendations appear first.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| NBA strategy Flow | Autolaunched Flow returning `List<Recommendation>` that encodes business rules for which recommendations to surface |
| Recommendation records | Standard sObject records defining each actionable recommendation with labels, descriptions, and acceptance action references |
| Lightning page configuration | Updated Lightning record page with the Actions & Recommendations component wired to the strategy Flow |

---

## Related Skills

- einstein-prediction-builder — Use alongside NBA when you want AI-scored predictions to influence recommendation priority or filtering
- prompt-builder-templates — Use when recommendation descriptions or labels need dynamic, AI-generated content
- einstein-trust-layer — Relevant when NBA strategies incorporate generative AI outputs that need toxicity or PII guardrails
