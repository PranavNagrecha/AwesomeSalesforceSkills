---
name: agent-console-requirements
description: "Use when gathering and documenting requirements for a Lightning Service Console deployment: agent workspace layout, page template selection, utility bar composition, macro requirements, case handling workflows, split-view navigation design, and licensing requirements. Triggers: service console requirements, agent workspace design, console page layout, utility bar planning, console licensing. NOT for console configuration steps or click-by-click setup (use admin/case-management), NOT for Omni-Channel routing model design (use architect/service-cloud-architecture), NOT for CTI telephony integration details."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Scalability
triggers:
  - "what do I need to design an agent console for our support team"
  - "how should I lay out case pages in the Lightning Service Console"
  - "what licensing does the Service Console require and which permission sets are needed"
  - "design the utility bar and macro requirements for our contact center agents"
  - "what page template should I use for cases in the console"
tags:
  - service-console
  - agent-workspace
  - lightning-console
  - case-management
  - macros
  - utility-bar
  - service-cloud
inputs:
  - Agent workflow description — how agents find, open, and work cases from creation to resolution
  - Case handling process — number of case types, typical objects open simultaneously, average handle time
  - Support tier structure — tier-1 generalists vs tier-2 specialists and whether same console app serves all
  - Macro and automation requirements — repetitive actions agents perform on every case
  - Channel mix — phone, email, chat, messaging, so CTI softphone and Omni-Channel widget needs can be confirmed
  - Licensing inventory — how many Service Cloud User licenses and whether Omni-Channel add-ons are purchased
outputs:
  - Agent console requirements document covering workspace layout, page templates, utility bar spec, and macro catalog
  - Permission set and license matrix confirming which agents need which console access
  - Page template selection rationale (Pinned Header vs standard) per case record type
  - Utility bar component list with justification for each component
  - Macro inventory with trigger actions and steps mapped to repetitive agent workflows
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Agent Console Requirements

Use this skill when gathering and documenting requirements for a Lightning Service Console implementation. It activates when a practitioner needs to translate contact center agent workflows into concrete console workspace decisions — covering page template selection, utility bar composition, macro catalog, split-view navigation rules, and the licensing and permission-set prerequisites that gate console access. It produces a structured requirements artifact that drives the subsequent admin configuration work.

---

## Before Starting

Gather this context before working on anything in this domain:

- **What Salesforce edition and licenses does the org have?** Service Console requires a Service Cloud User license (or Service Cloud Einstein). The console Lightning App itself is a standard app but agents without the correct license cannot access it. Open CTI requires an additional telephony license and an approved CTI adapter. Omni-Channel requires the Service Cloud license and a Routing Configuration. Macro automation requires the Macros permission.
- **What is the most common wrong assumption?** Practitioners assume the Lightning Service Console is simply a Lightning App with a different theme. It is architecturally distinct: it uses split-view list navigation (where clicking a record opens it as a subtab rather than navigating away), a persistent utility bar, and the Pinned Header page template that changes how the page renders compared to standard Lightning pages. Designing console pages using standard Lightning App logic produces a disjointed agent experience.
- **What platform limits and constraints apply?** The console supports a maximum of 10 open primary tabs and 10 subtabs per primary tab. Utility bar components load on console app startup and consume memory for the full agent session — overloaded utility bars slow the console. Macros execute sequentially and cannot exceed the standard Apex governor limits triggered by each macro action. Split-view list panels show up to 200 records; filtering is critical for high-volume case queues.

---

## Core Concepts

### Lightning Service Console App and Split-View Navigation

The Lightning Service Console is a Lightning App type built specifically for high-throughput agent work. Unlike a standard Lightning App where clicking a record navigates the full page, the console uses a split-view workspace:

- The left panel (split-view list) shows a queue or list view. Agents click records without losing their current context.
- Records open as primary tabs at the top of the workspace. Related records (such as the Account associated with a Case) open as subtabs within the primary tab.
- Multiple primary tabs can be open simultaneously. Agents switch between cases without losing context on any of them.

This split-view model is what drives most of the requirements-gathering questions: which objects should open as primary tabs vs subtabs, what goes in the split-view list panel, and how many simultaneous tabs the agent population needs. The split-view navigation is not optional — it is the defining behavioral characteristic that separates console apps from standard apps.

### Page Templates: Pinned Header vs Standard

Console case pages use the **Pinned Header** page layout template, not the standard layout used in non-console Lightning apps. The Pinned Header template:

- Fixes a header region (the Highlights Panel component) at the top of the page that remains visible when the agent scrolls down through case details.
- Supports a taller canvas height to accommodate dense information layouts — case details, related lists, Knowledge sidebar, and Chatter all visible simultaneously.
- Requires explicit placement of the **Highlights Panel** component in the pinned header region. Pages not configured with this template produce a scrolling layout that hides key case identifiers when agents work in the lower sections.

For knowledge-intensive workflows the **Knowledge Accordion** component is placed in the right sidebar of the Pinned Header template to surface article suggestions without leaving the case page. Standard Lightning page layouts do not have this sidebar region.

### Utility Bar Components

The utility bar is a persistent footer bar visible across all console tabs. It provides single-click access to tools agents use across every case, independent of which case tab is active. Core utility bar components for agent console deployments:

- **Omni-Channel:** Required if Omni-Channel routing is in use. Shows agent presence status and incoming work notifications. Cannot be omitted if Omni-Channel is licensed and active.
- **History:** Shows recently viewed records. Allows agents to return to a case they accidentally closed.
- **Macros:** Provides access to the macro runner. Agents invoke macros from here rather than navigating a menu on each case.
- **Open CTI Softphone:** Required if a CTI telephony integration is deployed. Renders the phone softphone panel in the utility bar. This component is only visible if an Open CTI adapter is configured.
- **Notes:** Optional. Allows quick note-taking across cases without opening a Notes record.

Each utility bar item is a separate Lightning component that initializes at console startup. Overloading the utility bar degrades startup performance. Requirements gathering should produce a prioritized list — not every possible component.

### Macro Requirements and the Macro Automation Layer

Macros execute predefined sequences of actions on a case record with a single click. They are the primary productivity mechanism for repetitive console work — sending a standard email reply, updating a case status, adding a case comment, and logging a call note in one action instead of four separate manual steps.

Requirements for macros:

- Each macro is defined as an ordered list of instructions (Update Field, Quick Action, Send Email, Submit for Approval).
- Macros require the **Run Macros** permission on the agent profile or permission set.
- Bulk macros can execute across multiple selected records in the split-view list. Bulk macro execution requires the **Manage Macros** permission.
- Macros can be shared with all agents, shared with groups, or kept private. Sharing rules matter for large teams where different support tiers need different macro sets.

Requirements gathering should inventory the top 10-15 repetitive agent actions and map each to a candidate macro. This prevents agents from rebuilding this list ad hoc after go-live.

---

## Common Patterns

### Pattern: Tiered Console App — Single App for Multiple Support Tiers

**When to use:** Organizations where Tier-1 generalists and Tier-2 specialists both use the Service Console but need different page layouts, different utility bar contents, or different split-view list filters.

**How it works:**
1. Create a single Lightning Console App shared by all tiers.
2. Use record types on the Case object to differentiate Tier-1 and Tier-2 case types. Assign different page layouts per record type — Tier-1 pages use a simplified layout; Tier-2 pages surface technical fields.
3. Assign page layout overrides using Lightning App Builder per-profile or per-permission-set (using the "Assign to users by profile" option in App Builder). Tier-1 agents see a simplified console page; Tier-2 agents see the full layout.
4. Use separate list views in the split-view panel filtered by record type or queue, so each tier sees only their relevant cases.

**Why not the alternative:** Creating two separate console apps (one per tier) doubles admin overhead for every future layout change. A single app with profile-driven layout assignments is simpler and supports agents who move between tiers.

### Pattern: Case-Centric Primary Tab with Account/Contact Subtabs

**When to use:** Any console deployment where agents work cases and need to reference or update the associated Account or Contact during case resolution.

**How it works:**
1. Configure the Case object as a primary tab object in the console app settings.
2. Add Account and Contact as subtab objects under Case, so opening a Case automatically opens the linked Account and Contact as subtabs.
3. On the Case Pinned Header page, add the Highlights Panel in the pinned header region and the Knowledge Accordion in the right sidebar.
4. Confirm that the Account and Contact subtab pages also use the Pinned Header template with appropriate highlights panel configuration.

**Why not the alternative:** Without subtab configuration, agents navigate away from the case to view the account, losing their case context. In high-volume environments with 50+ cases per agent per day, that navigation overhead adds up to hours of wasted time per week.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Case page layout for any Service Console | Pinned Header page template with Highlights Panel | Standard template scrolls the case header off-screen; Pinned Header keeps case ID, status, and priority always visible |
| Telephony integration is in scope | Open CTI Softphone utility bar component | Required to render the softphone in the console; cannot be replaced with a standalone tab |
| Omni-Channel routing is licensed | Omni-Channel widget in utility bar | Agents cannot change presence status or accept work without it visible |
| Multiple support tiers need different layouts | Single console app with profile-driven page layout assignments | Fewer apps to maintain; profile-based layout assignments in App Builder support this natively |
| Agents perform 5+ repeated actions per case | Macro catalog of 10-15 macros | Each macro saves multiple manual steps; macro investment pays back within the first week of go-live |
| High case volume list panel (200+ cases in queue) | Filtered list views per queue or tier in split-view | Default views with 200+ unfiltered records cause agents to miss priority cases |
| Knowledge-heavy resolution workflows | Knowledge Accordion component in console right sidebar | Surfaces article suggestions in context without leaving the case; agents do not need to switch tabs |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner gathering agent console requirements:

1. **Confirm licensing and permissions baseline** — Verify that every agent who needs console access holds a Service Cloud User (or Service Cloud Einstein) license. Identify which agents need the Run Macros permission and which need the Manage Macros permission. Confirm whether Open CTI or Omni-Channel add-ons are purchased. Document the license and permission-set matrix before any layout work begins.

2. **Map agent workflows to console workspace needs** — Interview or shadow agents through a typical case from queue pickup to resolution. Document: which objects they open, what they look up (Account, Contact, related cases), how many cases they have open at once, and what actions they perform on every case. This produces the primary tab / subtab object list and the macro candidate inventory.

3. **Define page template and layout per case record type** — For each case record type, specify the Pinned Header template, the components that belong in the pinned header region (Highlights Panel), the right sidebar (Knowledge Accordion if relevant), and the main canvas. Capture the required fields in the Highlights Panel for each record type. Confirm whether Knowledge search is needed in-context.

4. **Specify the utility bar** — Prioritize utility bar components from the shortlist (Omni-Channel, History, Macros, Open CTI Softphone, Notes). Confirm which components are required vs nice-to-have. Cap the utility bar at 6-8 items to protect console startup performance. Document any custom utility bar LWC components that need to be built.

5. **Catalog macro requirements** — List the top 10-15 repetitive agent actions identified in step 2. For each macro, define: name, trigger scenario, ordered list of steps (Update Field / Send Email / Quick Action), applicable case record types, sharing scope (all agents vs specific profiles). Identify bulk macro candidates.

6. **Design split-view list panel** — For each agent tier, define the default list view to display in the split-view panel (which queue, which fields, which sort order). Confirm filter criteria that prevent high-volume queues from overflowing the 200-record display limit.

7. **Document and validate requirements** — Compile the console requirements document (workspace layout, page templates per record type, utility bar spec, macro catalog, split-view list design, license/permission matrix). Walk through the document with the lead admin who will build the configuration. Confirm each requirement is feasible and maps to a specific console configuration or Lightning App Builder step.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every agent who needs console access has a confirmed Service Cloud User license
- [ ] Omni-Channel widget included in utility bar if Omni-Channel routing is licensed and active
- [ ] Open CTI Softphone component included in utility bar if a CTI telephony integration is deployed
- [ ] All case page layouts use the Pinned Header template with Highlights Panel in the pinned header region
- [ ] Knowledge Accordion placed in the right sidebar for knowledge-intensive case resolution workflows
- [ ] Utility bar capped at 6-8 components to protect console startup performance
- [ ] Primary tab and subtab objects defined (Case as primary; Account, Contact as subtabs)
- [ ] Split-view list view filters defined per tier or queue to prevent 200-record overflow
- [ ] Macro catalog documented with at least 10 candidates covering the most frequent repetitive actions
- [ ] Run Macros and Manage Macros permission assignments mapped to the correct permission sets
- [ ] Console requirements document reviewed by the lead admin before build begins

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Pinned Header template is not selected by default in Lightning App Builder** — When an admin creates a new console case page, App Builder defaults to the standard page template. The Pinned Header template must be explicitly selected from the template picker when creating the page. Deploying a console case page without Pinned Header produces a scrolling layout where the Highlights Panel disappears as agents scroll down — they lose case context on every scroll.

2. **Open CTI Softphone only renders if an Active CTI configuration exists in the org** — Adding the Open CTI Softphone to the utility bar produces a blank grey panel if no CTI configuration is active. Agents see a broken component with no error message. Requirements must confirm that the telephony vendor's CTI adapter is installed and a Call Center definition is configured before including this component.

3. **Macros require a specific permission, not just the profile** — Agents with full Case Edit access cannot run macros unless they also have the **Run Macros** user permission, which is not included in any standard profile. It must be added via a permission set. This is a post-go-live support ticket waiting to happen if missed in requirements.

4. **Split-view list panel maximum of 200 records is silent** — If a queue contains more than 200 cases, the split-view panel silently shows only the first 200 matching the current list view sort. There is no warning to the agent that cases are being hidden. High-volume queues must be partitioned into filtered list views (by priority, by sub-queue, by creation date window) so agents are never working an incomplete view.

5. **Console subtab objects must be explicitly configured or records open in a new primary tab** — Account, Contact, and other related records do not open as subtabs automatically. Each object must be added to the console app's Subtab Objects configuration. Without this, clicking the Account link from a Case opens a new primary tab, consuming one of the 10 available slots and confusing agents who lose their case context.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Console requirements document | Full workspace specification: page templates per case record type, utility bar component list with justification, split-view list view definitions per agent tier, macro catalog with step-by-step definitions |
| License and permission matrix | Table mapping each agent role to required Salesforce license, console app permission set, Run Macros permission, and optional CTI or Omni-Channel permissions |
| Macro catalog | Inventory of 10-15 macro candidates with name, trigger scenario, ordered action steps, applicable record types, and sharing scope |
| Page template selection rationale | Per-record-type documentation of template choice, Highlights Panel fields, sidebar components, and layout regions with justification |

---

## Related Skills

- architect/service-cloud-architecture — Use when the broader Service Cloud architecture (channel strategy, routing model, knowledge design) needs to be designed before or alongside the console requirements
- admin/case-management — Use after requirements are gathered to drive the click-by-click console configuration (Lightning App Builder, utility bar setup, macro creation)
- apex/opportunity-trigger-patterns — Not typically related, but reference if custom Apex is proposed to replace macros — macros should be preferred for sequential UI actions on a single record
- architect/multi-channel-service-architecture — Use when the console requirements include multi-channel routing and agent capacity modeling beyond the console workspace itself

---

## Official Sources Used

- Lightning Service Console Overview — https://help.salesforce.com/s/articleView?id=sf.console2_overview.htm
- Set Up Lightning Service Console — https://help.salesforce.com/s/articleView?id=sf.console2_lex_app_setup_overview.htm
- Customize Lightning Service Console Pages — https://help.salesforce.com/s/articleView?id=sf.console2_lex_pages.htm
- Macros in Service Cloud — https://help.salesforce.com/s/articleView?id=sf.macros_overview.htm
- Utility Bar in Lightning Apps — https://help.salesforce.com/s/articleView?id=sf.console2_utilities.htm
- Open CTI Adapter — https://help.salesforce.com/s/articleView?id=sf.cloud_cti_api_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
