---
name: sales-cloud-architecture
description: "Use when designing or reviewing a Sales Cloud solution architecture covering process automation strategy, integration points, data model decisions, and scalability planning. Triggers: 'design a Sales Cloud architecture for enterprise org', 'Sales Cloud data model and automation strategy', 'how to architect Sales Cloud for high-volume pipeline management'. NOT for individual feature configuration (use admin/opportunity-management or admin/lead-management), NOT for CPQ-specific decisions (use architect/cpq-vs-standard-products-decision), NOT for integration implementation details (use architect/sales-cloud-integration-patterns)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "design a Sales Cloud architecture for enterprise org"
  - "Sales Cloud data model and automation strategy"
  - "how to architect Sales Cloud for high-volume pipeline management"
  - "Sales Cloud scalability planning and governor limits"
  - "end-to-end Sales Cloud solution design review"
tags:
  - sales-cloud
  - architecture
  - data-model
  - process-automation
  - scalability
  - opportunity-management
  - lead-to-cash
  - territory-management
inputs:
  - "Number of sales users and expected record volumes"
  - "Current sales process stages and conversion rules"
  - "Integration landscape — ERP, marketing automation, CPQ, external systems"
  - "Territory and forecasting requirements"
  - "Reporting and analytics expectations"
  - "Multi-currency or multi-org constraints"
outputs:
  - "Sales Cloud architecture decision record"
  - "Data model diagram with object relationships and field strategy"
  - "Process automation map — which tool for which automation"
  - "Integration touchpoint inventory"
  - "Scalability assessment with volume projections and limit headroom"
  - "Review checklist for go-live readiness"
dependencies:
  - architect/sales-cloud-integration-patterns
  - architect/limits-and-scalability-planning
  - architect/well-architected-review
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Sales Cloud Architecture

Use this skill when you are designing, reviewing, or refactoring a Sales Cloud implementation that spans multiple functional areas — lead management, opportunity pipeline, territory assignment, forecasting, and downstream integrations. The focus is on holistic architecture: how the data model, automation layer, integration points, and scalability constraints fit together as a coherent system rather than isolated features.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Edition and license entitlements** — Sales Cloud features vary significantly between Professional, Enterprise, and Unlimited editions. Confirm which features (Territory Management, Forecasting, Einstein Activity Capture) are actually licensed before designing around them.
- **Record volume projections** — Get concrete numbers: leads per month, opportunities per quarter, activities per user per day. Architecture decisions that work at 50K records collapse at 5M.
- **Existing automation inventory** — Most Sales Cloud orgs already have a mix of Workflow Rules, Process Builder, Flows, and Apex triggers. You cannot design new automation without mapping what already fires on Opportunity, Lead, and Account objects.

---

## Core Concepts

### Lead-to-Cash Object Model

The Sales Cloud data model centers on a standard object chain: Lead -> Account + Contact + Opportunity -> Quote -> Order. Each transition represents a business event with architectural implications. Lead conversion creates or matches Account and Contact records and optionally creates an Opportunity, all within a single DML transaction. Architects must decide early whether to extend standard objects with custom fields or introduce custom objects for domain-specific entities (deal desks, approval matrices, sales plays). Over-customizing standard objects leads to page-load degradation and validation-rule sprawl; under-leveraging them leads to shadow data models that break reporting.

### Process Automation Strategy

Sales Cloud orgs face a critical automation decision matrix: Record-Triggered Flows vs. Apex triggers vs. Platform Events. Flow is the declarative-first choice for field updates, notifications, and simple branching. Apex triggers are required when you need complex cross-object logic, callouts during save, or bulkified operations exceeding Flow's per-element governor limits. Platform Events decouple processes that do not need to execute synchronously — such as ERP sync after Opportunity close or commission calculations. The architecture must define a single automation owner per object per event (before-save vs. after-save) to prevent order-of-execution conflicts.

### Integration Boundary Design

Sales Cloud rarely operates in isolation. The architecture must define clear integration boundaries: what data enters Salesforce (marketing-qualified leads, ERP pricing), what leaves (closed-won notifications, forecast snapshots), and what stays synchronized bidirectionally (account hierarchies, contact records). Each boundary requires a decision on pattern (real-time API, Change Data Capture, batch ETL) and a contract on field mapping, conflict resolution, and error handling. Designing these boundaries early prevents the common failure mode where integrations are bolted on after go-live with inconsistent assumptions about data ownership.

### Scalability and Limit Planning

Sales Cloud architectures must plan for governor limits at design time, not as a remediation exercise. Key limits include: 50K records per SOQL query, 150 DML statements per transaction, 6MB heap size, and the 2000-row limit on aggregate queries. Territory Management hierarchies, roll-up summary fields on Account, and Opportunity Team cascade-delete operations all amplify these limits. The architecture should document expected transaction profiles (e.g., "bulk lead conversion of 200 records triggers N queries and M DML") and validate they stay within 50% of governor ceilings to leave headroom for future growth.

---

## Common Patterns

### Layered Automation Ownership

**When to use:** Any org with more than three automations firing on Lead, Opportunity, or Account.

**How it works:** Assign a single "automation owner" per object per timing slot. For example, Opportunity before-save logic lives in a single Record-Triggered Flow that handles all field defaults and validations. After-save logic routes through a single dispatcher trigger that calls domain-layer Apex handlers. This prevents the order-of-execution ambiguity that occurs when multiple Process Builders and Flows compete on the same object.

**Why not the alternative:** Allowing multiple independent automations per object per event leads to nondeterministic execution order, redundant SOQL queries that hit governor limits, and field-update ping-pong where one automation overwrites another's changes.

### Integration Facade with Platform Events

**When to use:** When Sales Cloud must notify two or more external systems on record changes (e.g., Opportunity close triggers ERP order creation and commission calculation).

**How it works:** After-save logic publishes a single Platform Event (e.g., `SalesEvent__e`) with the relevant record data. Subscribers — either Apex triggers on the Platform Event or external CometD listeners — each handle their integration independently. This decouples the Sales Cloud transaction from downstream system availability.

**Why not the alternative:** Direct synchronous callouts from triggers couple the save transaction to external system latency and availability. If the ERP is slow, the user's Opportunity save hangs. If it is down, the save fails entirely unless you add complex retry logic inside the trigger itself.

### Territory-Aware Data Partitioning

**When to use:** Orgs with 1000+ sales reps and territory hierarchies deeper than three levels.

**How it works:** Use Enterprise Territory Management with rule-based assignment rather than manual assignment. Partition reporting and sharing using territory hierarchies instead of role hierarchies to keep sharing calculations performant. Store territory assignment snapshots in a custom object for historical reporting rather than querying live territory membership.

**Why not the alternative:** Manual territory assignment does not scale and becomes a full-time admin job. Using role hierarchy for territory-based sharing forces a 1:1 mapping between organizational structure and sales territories, which breaks when territories are realigned quarterly.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Simple field update on Opportunity stage change | Record-Triggered Flow (before-save) | No DML cost, fastest execution, declarative |
| Cross-object update touching 3+ objects on close | Apex trigger with domain-layer handler | Flow interview limits and bulkification concerns |
| Notification to ERP on closed-won | Platform Event + subscriber | Decouples CRM save from ERP latency |
| Lead assignment for < 500 leads/day | Assignment Rules with lead queues | Standard feature, no custom code |
| Lead assignment for > 5000 leads/day | Custom Apex with @future or Queueable | Assignment Rules hit performance limits at volume |
| Territory realignment twice per year | Enterprise Territory Management with rule-based assignment | Automated reassignment, audit trail, forecast-safe |
| Historical pipeline reporting | Opportunity snapshots via Reporting Snapshots or custom batch | Live queries against Opportunity history are too slow at volume |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Gather requirements and constraints** — Document the number of users, expected record volumes (leads/month, opportunities/quarter), edition, licensed features, and existing automation inventory. Use `Setup > Installed Packages` and `Setup > Process Automation > Flows` to enumerate what already exists.

2. **Map the data model** — Diagram the standard object chain (Lead, Account, Contact, Opportunity, Product, PricebookEntry, Quote, Order) and identify where custom objects or junction objects are needed. Validate that no more than 500 custom fields exist on any single object.

3. **Define automation ownership** — For each object with automation needs (typically Lead, Account, Contact, Opportunity), assign exactly one automation mechanism per timing slot (before-save Flow, after-save trigger, scheduled batch). Document the assignment in the architecture decision record.

4. **Design integration boundaries** — For each external system, document: direction (inbound/outbound/bidirectional), pattern (real-time API/CDC/batch), data ownership (system of record), field mapping, and error handling. Validate that synchronous integrations do not exceed callout limits (100 per transaction, 120-second timeout).

5. **Validate scalability** — For each critical transaction profile (lead conversion, opportunity close, bulk data load), estimate the governor limit consumption. Confirm all profiles stay below 50% of limits. Document the analysis in the scalability assessment artifact.

6. **Review against Well-Architected pillars** — Walk the architecture through Scalability (can it handle 10x current volume?), Reliability (what happens when an integration target is down?), Performance (are there N+1 query patterns?), and Operational Excellence (can admins modify automation without developer intervention?).

7. **Produce deliverables** — Generate the architecture decision record, data model diagram, automation map, integration inventory, and scalability assessment. Submit for stakeholder review.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Data model uses standard Sales Cloud objects where they exist; custom objects are justified
- [ ] Each object has at most one automation owner per timing slot (before-save, after-save)
- [ ] No synchronous callouts from Opportunity or Lead triggers without Platform Event decoupling
- [ ] Governor limit analysis exists for all critical transaction profiles with 50% headroom
- [ ] Territory Management approach is documented with assignment rules, not manual only
- [ ] Integration boundaries define system of record, field mapping, and error handling per system
- [ ] Forecasting configuration aligns with fiscal year and territory hierarchy
- [ ] Sharing model is validated — OWD settings, sharing rules, and territory sharing are coherent
- [ ] Historical reporting strategy does not rely on live queries against multi-million-row objects

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Lead conversion transaction scope** — Lead conversion creates/updates Account, Contact, and Opportunity in a single transaction. All triggers, Flows, and validations on all four objects fire within the same governor limit envelope. A seemingly safe trigger on Contact can push the Lead conversion transaction over limits when combined with Account and Opportunity automations.

2. **Opportunity Team cascade delete** — Deleting an Opportunity Team member cascades to remove their Opportunity Splits. If splits are required for commission reporting, accidental team-member removal can silently break downstream calculations. There is no undelete for splits.

3. **Forecast hierarchy recalculation** — Changing the forecast hierarchy (role hierarchy or territory hierarchy) triggers a background recalculation that can take hours for large orgs. During this window, forecast numbers are inconsistent. Architects must plan territory realignment for low-activity periods and communicate the inconsistency window.

4. **Roll-up summary field limits on Account** — Account supports a maximum of 25 roll-up summary fields. Architects who design KPI dashboards using roll-up summaries on Account often hit this limit, forcing a late-stage redesign to use batch Apex or reporting snapshots instead.

5. **Big Deal Alert vs. automation** — Big Deal Alerts are a legacy feature that sends emails based on Opportunity amount thresholds. They fire independently of Record-Triggered Flows and Apex triggers. Architects who do not inventory Big Deal Alerts often create duplicate notifications when building new automation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Architecture Decision Record | Documents key decisions (automation strategy, integration patterns, data model extensions) with rationale and tradeoffs |
| Data Model Diagram | Visual map of standard and custom objects with relationship types, field counts, and record volume estimates |
| Automation Map | Matrix showing each object, timing slot, automation mechanism, and owning team |
| Integration Inventory | Per-system table listing direction, pattern, SOR, field mapping, error strategy, and SLA |
| Scalability Assessment | Transaction profiles with governor limit consumption estimates and headroom percentages |

---

## Related Skills

- architect/sales-cloud-integration-patterns — Use when designing the specific integration implementation after architecture decisions are made
- architect/limits-and-scalability-planning — Use for detailed governor limit analysis beyond the Sales Cloud scope
- architect/cpq-vs-standard-products-decision — Use when the product/pricing model requires a CPQ vs. standard products decision
- architect/well-architected-review — Use for a formal Well-Architected review across all pillars
