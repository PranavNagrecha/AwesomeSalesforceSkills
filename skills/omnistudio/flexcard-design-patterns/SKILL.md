---
name: flexcard-design-patterns
description: "Use when designing, building, or reviewing OmniStudio FlexCards — including data source selection, card states, actions, conditional visibility, flyout configuration, and child card iteration. Triggers: 'FlexCard', 'card template', 'flyout', 'card action', 'card state', 'data source', 'child card', 'conditional visibility'. NOT for OmniScript design, standalone LWC development, or Apex controller architecture outside the FlexCard context."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Performance
triggers:
  - "how do I show different content on a FlexCard based on a field value"
  - "FlexCard is loading slowly with multiple data sources"
  - "how to launch an OmniScript from a FlexCard action button"
  - "FlexCard flyout not displaying child card data correctly"
  - "how do I iterate over related records in a FlexCard"
  - "FlexCard card state not switching after save action completes"
  - "how to deploy FlexCards between Salesforce environments"
tags:
  - omnistudio
  - flexcard
  - data-sources
  - card-actions
  - conditional-visibility
  - flyout
inputs:
  - "record context: which object the FlexCard surfaces (e.g. Account, Case)"
  - "data requirements: which fields and related data the card must display"
  - "action requirements: what the user needs to trigger from the card"
  - "org OmniStudio version (standard vs. managed package)"
outputs:
  - "FlexCard design recommendation covering data sources, states, actions, and templates"
  - "conditional visibility and card state configuration guidance"
  - "deployment approach for versioned FlexCard promotion"
  - "performance review findings for data source consolidation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# FlexCard Design Patterns

Use this skill when building or reviewing OmniStudio FlexCards. It covers data source selection and consolidation, card state design, action configuration, conditional visibility, flyout and child card patterns, and controlled deployment through versioned FlexCards. Activate when a practitioner asks how to display record data on a FlexCard, configure card behavior, or promote FlexCards across environments.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which Salesforce object is the card anchored to, and what data must it display?
- Is the org on the standard (Salesforce Industries) OmniStudio package or the managed package? Some metadata and deployment behaviors differ.
- How many data sources are proposed? More than two data sources per card is a performance risk — check whether an Integration Procedure can consolidate them.
- What actions must the card expose — navigation, OmniScript launch, Apex, DataRaptor, or custom LWC?
- Are any related lists or child record sets required (child card iteration)?
- What deployment mechanism is in use — change sets, SFDX, or the OmniStudio migration tool?

---

## Core Concepts

### Data Sources

A FlexCard data source is the mechanism that retrieves data for rendering the card. The five supported types are:

1. **SOQL** — Direct SOQL query executed at card load time. Use for simple single-object data needs. Limited to fields accessible to the running user via FLS.
2. **Apex** — An `@AuraEnabled` Apex method. Use when data requires logic that SOQL cannot express, or when multiple objects must be combined in Apex with a clear return contract.
3. **DataRaptor** — An OmniStudio DataRaptor Extract. Use when the data shape is already modeled in a DataRaptor and reuse is valuable. Adds a DataRaptor dependency to the card.
4. **Integration Procedure (IP)** — An OmniStudio Integration Procedure. The preferred choice when data requires aggregating multiple queries, calling external systems, or applying transformation logic. Consolidating queries into one IP call is the primary performance lever for FlexCards.
5. **Streaming** — A Platform Event or Change Data Capture channel. Use when the card must update in real time without user-initiated refresh.

Each data source maps to a named node in the card's data model. Card template elements and conditional logic reference these node paths.

### Card States

FlexCards have three built-in states:

- **Default** — The state rendered on initial card load. Contains the primary display template.
- **Saved** — An optional state shown after a save action completes successfully. Use to give the user confirmation feedback without a page reload.
- **Error** — An optional state shown when a data source or action returns a failure. If not configured, the card silently renders nothing on error, which is the most common production support issue.

Each state has its own template, so a card can show a spinner, a success message, or an inline error notice depending on the outcome. State transitions are driven by action outcomes — not by data values; conditional visibility handles show/hide based on data.

### Actions

FlexCard actions are interactive triggers that a user can invoke from the card surface. Supported action types:

- **Navigation** — Route to a record page, app page, or external URL.
- **OmniScript Launch** — Open an OmniScript in a modal or new tab. The card passes context data as input variables to the OmniScript.
- **Apex** — Call an `@AuraEnabled` Apex method directly. Use sparingly; prefer Integration Procedures for testability.
- **DataRaptor** — Execute a DataRaptor Turbo Action to save or update records without an OmniScript.
- **Custom LWC** — Invoke a handler method on a custom Lightning Web Component embedded in the card.

Actions are bound to card template elements (buttons, icons, menu items). Each action can define a `success` and `error` follow-on behavior such as a state transition, a refresh, or navigation.

### Conditional Visibility and Templates

Conditional visibility controls whether a card element (a field, a block, a button, or an entire section) renders. Conditions evaluate against the card's data model at render time using path-based expressions.

Common patterns:
- Show an escalate button only when `{Record.Status}` equals `Open`.
- Hide a section when `{DataSource.relatedCount}` is zero.
- Display a warning banner when `{Record.SLABreached__c}` is `true`.

Templates define the layout and content of each card state. OmniStudio provides a WYSIWYG Card Designer. The template compiles to a reusable LWC component — the FlexCard is not interpreted at runtime, it is compiled. This means template changes require a save and activation before they take effect.

### Child FlexCards and Flyouts

**Child FlexCards** are nested card components used to iterate over related data. A parent card with a child card can render a list of related records — for example, iterating over `{Record.OpenCases}` to render one card per case. Each child card is an independent FlexCard that receives the iterated record as its context.

**Flyouts** are modal-like overlays triggered by an action. A flyout renders a child FlexCard in a popup panel. Use flyouts to show related detail without navigating away from the parent context.

### Versioning and Deployment

FlexCards support versioning. A new version of a FlexCard can be authored and activated while the previous version remains in production. Version control is managed through the card's version number in its metadata name (e.g., `AccountSummaryCard_v2`).

FlexCards compile to LWC components at activation time. Deployment across environments follows standard SFDX or change set rules for LWC metadata. The OmniStudio Migration Tool is the recommended approach for moving FlexCards between orgs because it handles the full dependency graph: data sources, child cards, referenced Integration Procedures and DataRaptors.

---

## Common Patterns

### Pattern 1: Integration Procedure as Single Data Source

**When to use:** The card must display data from more than one Salesforce object, or requires aggregated or transformed data.

**How it works:**
1. Build an Integration Procedure that queries all required objects and shapes the output into a single response map.
2. In the FlexCard, add one Integration Procedure data source pointing to that IP.
3. Map the IP output nodes to card template elements using path references such as `{IntegrationProcedure.AccountName}`.

**Why not the alternative:** Using two or three SOQL data sources on the same card fires multiple parallel queries at card load. For cards on high-traffic pages (e.g., Account 360), this compounds into measurable render delay and governor limit exposure. One IP call with caching is faster and easier to test.

### Pattern 2: Error State with Explicit Failure Handling

**When to use:** Any FlexCard that calls an Integration Procedure or Apex data source in a production context.

**How it works:**
1. In Card Designer, open the **Error** state.
2. Add a visible error message element bound to the failure node from the data source (e.g., `{IntegrationProcedure.errorMessage}`).
3. Optionally add a retry action.
4. Test by forcing the IP to return a `failureResponse` in the debugger.

**Why not the alternative:** If the Error state is left empty, the card renders blank when a data source fails. Users assume the page is broken and raise P1 support tickets. An explicit error state surfaces the failure and empowers the user to take action.

### Pattern 3: OmniScript Launch from Card Action

**When to use:** A card user needs to trigger a guided process (e.g., update case details, initiate a service order) without leaving the current page context.

**How it works:**
1. Add a button element to the Default state template.
2. Set the button action type to **OmniScript Launch**.
3. Configure the OmniScript Type, SubType, and Language to match the target OmniScript's identity.
4. Map card data nodes to OmniScript input variables — for example, pass `{Record.Id}` as the `recordId` input.
5. Set the action's **Close behavior** to refresh the card on completion so updated data is reflected.

**Why not the alternative:** Navigating to a standalone OmniScript URL loses the record context and requires the user to navigate back. The launch action keeps the user in place and passes the full card data context to the OmniScript.

### Pattern 4: Child Card Iteration for Related Lists

**When to use:** The card must render a dynamic list of related records (e.g., open activities, related contacts, recent cases) as individual styled cards.

**How it works:**
1. Create a standalone FlexCard for the child record type (e.g., `CaseLineItemCard`). Configure it to accept the record data as its input context.
2. In the parent FlexCard, add a **Child Card** element.
3. Set the child card's data source to the collection node (e.g., `{IntegrationProcedure.relatedCases}`).
4. The parent iterates the collection and renders one instance of the child card per record.

**Why not the alternative:** Embedding a flat table in the parent card template does not scale visually and cannot support per-row actions without complex conditional logic. Child cards encapsulate display and action logic per record.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single object, simple field display | SOQL data source | Minimal overhead, no IP required |
| Data from 2+ objects or requires transformation | Integration Procedure data source | Single network call, cacheable, testable |
| Real-time data (e.g. stock price, live status) | Streaming data source | Push update without user refresh |
| Card must confirm success after save | Saved state with success message element | Built-in state transition, no custom logic needed |
| Card must show error details on failure | Error state with failure node binding | Surfaces actionable error to user |
| Related list of records with per-row actions | Child FlexCard with iteration | Encapsulates row logic, scalable to variable list sizes |
| Navigate to record from card | Navigation action | Standard routing, respects app context |
| Trigger guided process from card | OmniScript Launch action | Keeps user in context, passes data to script |
| Deploy FlexCard with all dependencies | OmniStudio Migration Tool | Handles child cards, IPs, DataRaptors as a unit |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking FlexCard work complete:

- [ ] Every data source is justified — SOQL only for single-object reads, IP for multi-source or transformed data
- [ ] The Error state is configured and bound to a meaningful failure message node
- [ ] All actions have a defined success behavior (state transition, refresh, or navigation)
- [ ] Conditional visibility conditions reference valid data model paths (test with actual data)
- [ ] Child FlexCard data source paths are tested with empty collections (zero records must not break layout)
- [ ] FlexCard is activated after any template change (compiled LWC is not updated until activation)
- [ ] Deployment uses the OmniStudio Migration Tool or SFDX with the full dependency graph captured
- [ ] Card is tested in the target Lightning App Page or Experience Cloud page context, not just the designer preview

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Error state is opt-in — blank card on failure is the default** — If the Error state template is empty, a failed data source causes the FlexCard to render nothing. There is no console error visible to the user. Always configure the Error state explicitly and bind it to the failure response node.

2. **Template changes require activation — the designer preview does not reflect compilation** — The Card Designer preview renders within the designer context. The compiled LWC component used on a Lightning App Page or Experience Cloud site is only updated when the FlexCard is saved and activated. Deploying an inactive version or forgetting to activate after edits is a common cause of "the change isn't showing up" support issues.

3. **Nested child FlexCards multiply data source calls** — Each child card instance runs its own data source query when it renders. A parent card iterating over 20 related records with a child card that has a SOQL data source fires 20 separate queries. Always push child data retrieval into the parent IP and pass the data down as a collection to avoid governor limit and performance issues.

4. **Action limits per card state** — FlexCards support up to 10 actions per card state. This is rarely a problem in practice, but cards designed with many contextual menu items (e.g., different actions per record status) can hit this ceiling. Consolidate actions using conditional visibility on individual action elements rather than duplicating the action list per status.

5. **OmniStudio managed package vs. standard deployment differences** — In orgs using the managed OmniStudio package (common in ISV and partner implementations), FlexCard metadata lives under the `OmniInteractionConfig` namespace. SFDX source format, file paths, and deployment commands differ from standard orgs. Confirm the package mode before building a deployment pipeline.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FlexCard design recommendation | Data source selection, state configuration, and action mapping for the target card |
| Conditional visibility specification | Element-level show/hide rules with data path references |
| Deployment checklist | Dependency list (IP, DataRaptors, child cards) and migration tool instructions |

---

## Related Skills

- integration-procedures — Build the Integration Procedure data source that consolidates multiple queries for a FlexCard; error handling contract between IP and card
- omnistudio-security — FLS enforcement on SOQL data sources, Apex sharing rules for card-facing methods, guest user exposure on Experience Cloud FlexCards
