---
name: donor-lifecycle-requirements
description: "Requirements mapping for the full donor lifecycle in NPSP or Nonprofit Cloud: acquisition stage design, moves management for cultivation and solicitation, upgrade path design, lapsed donor re-engagement strategy, and segmentation for portfolio management. NOT for marketing automation execution, email campaign configuration, or recurring donation implementation."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
triggers:
  - "how do I map the donor lifecycle stages in NPSP or Nonprofit Cloud"
  - "designing moves management and donor portfolio strategy in Salesforce nonprofit"
  - "requirements for lapsed donor re-engagement and win-back strategy in NPSP"
  - "how do donors move from prospect to major gift in Salesforce NPSP"
  - "what Salesforce features support donor upgrade paths from annual to mid-level to major"
tags:
  - npsp
  - nonprofit-cloud
  - donor-management
  - moves-management
  - lifecycle
  - fundraising
inputs:
  - "NPSP or Nonprofit Cloud platform"
  - "Existing donor segments and portfolio definitions"
  - "Current solicitation cycle and cultivation stage definitions"
  - "Lapsed donor definition (LYBUNT, SYBUNT, multi-year lapsed criteria)"
outputs:
  - "Donor lifecycle stage map aligned to NPSP/NPC features"
  - "Moves Management configuration requirements"
  - "Lapsed donor segmentation and re-engagement workflow design"
  - "Donor upgrade path design"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Donor Lifecycle Requirements

This skill activates when you need to map the full donor lifecycle in NPSP or Nonprofit Cloud — from prospect acquisition through cultivation, upgrade, and lapsed re-engagement. It produces lifecycle stage maps, Moves Management configuration requirements, segmentation designs, and upgrade path workflows grounded in NPSP/NPC platform capabilities.

---

## Before Starting

Gather this context before working on anything in this domain:

- **NPSP vs NPC:** As of December 2025, NPSP is no longer offered in new production orgs. New nonprofits use Nonprofit Cloud (NPC). Legacy orgs remain on NPSP. The donor lifecycle features differ — confirm which platform before designing workflows.
- **Moves Management is NPSP-specific in its classic form:** NPSP Moves Management uses Opportunity Stages mapped to cultivation stages on a Contact or Opportunity. NPC uses a portfolio management approach. These are different design paradigms.
- **LYBUNT/SYBUNT are NPSP report concepts:** LYBUNT (Last Year But Unfortunately Not This Year) and SYBUNT (Some Year But Unfortunately Not This Year) are standard NPSP report labels for lapsed donors. These reports are built on Opportunity data in NPSP. NPC has Actionable Segmentation for donor classification.
- **Segmentation ≠ Marketing Automation:** Donor segmentation in this context means portfolio classification for relationship management — who goes in the Annual Fund, Mid-Level, or Major Gift portfolio. This is NOT campaign management or email marketing execution.

---

## Core Concepts

### NPSP Moves Management

NPSP Moves Management maps the donor cultivation lifecycle through **Opportunity Stage picklist values** and a Contact-level field tracking the donor's current cultivation stage. The lifecycle is:

Prospect → Identified → Cultivating → Solicited → Closed Won (or Lost)

Configuration components:
- Opportunity Stage picklist values aligned to cultivation stages
- Opportunity Sales Process restricting stages per Opportunity Record Type
- Path component on Opportunity layout showing stage progression
- Custom reports on Opportunity Stage changes for portfolio review

The "moves" in moves management are tracked as Opportunity Stage progressions, with associated Activity records documenting each cultivation touch (meeting, call, event attendance).

### NPC Donor Segmentation (Actionable Segmentation)

Nonprofit Cloud uses **Actionable Segmentation** to classify donors into portfolio tiers. This is NOT marketing automation segmentation — it is a CRM classification tool that:
- Assigns donors to portfolios (Annual Fund, Mid-Level, Major Gifts)
- Tracks portfolio assignments and assignment history
- Enables fundraiser-specific views filtered by portfolio

Actionable Segmentation creates Contact-level classification records that route donors to the appropriate fundraising strategy and portfolio manager.

### Lapsed Donor Re-engagement

NPSP provides three lapsed donor report types:
- **LYBUNT** — gave last year but not this year; highest priority for re-engagement
- **SYBUNT** — gave in a prior year but not in the most recent year
- **Multi-year lapsed** — no gift in 2+ years; lower priority, higher acquisition cost

These reports are built on Opportunity records (filtered by `npsp__LastOppDate__c` and `npsp__TotalGifts__c` rollup fields on Contact). The Enhanced Recurring Donation (ERD) `Status__c` field transitions to **Lapsed** automatically when a recurring donor misses a scheduled payment, providing an additional re-engagement trigger.

---

## Common Patterns

### Moves Management Stage Progression in NPSP

**When to use:** Designing the cultivation-to-solicitation lifecycle for major and mid-level donors in NPSP.

**How it works:**
1. Define Opportunity Stage values: Prospect Identified, In Cultivation, Proposal Pending, Solicitation Made, Closed Won, Closed Lost.
2. Create an Opportunity Record Type for Major Gift Solicitations with a restricted stage progression.
3. Add Opportunity Path component to the record detail view.
4. Create Engagement Plans for each cultivation stage to auto-generate tasks (thank-you call, site visit invite, proposal draft).
5. Build a Pipeline Report on Opportunity Stage grouped by fundraiser to enable weekly portfolio reviews.

**Why not only Contact activities:** Opportunities provide the financial projection (Amount field), close date, and stage progression that Activities alone cannot. Portfolio reviews need to see cultivation stage AND dollar value in a single pipeline view.

### LYBUNT Re-engagement Workflow

**When to use:** Annual lapsed donor re-engagement campaigns in NPSP.

**How it works:**
1. Run the NPSP LYBUNT report filtered to the re-engagement donor threshold (e.g., gave $500+ last year, no gift this year).
2. Export or mass-action to create Campaign Members on a re-engagement Campaign.
3. Configure an Engagement Plan on the Campaign to assign tasks: personalized outreach call → handwritten note → event invitation sequence.
4. Track re-engagement gifts via Opportunity linked to the Campaign.
5. Measure re-engagement rate: Campaign ROI report comparing re-engagement gift total to prior year giving.

**Why Engagement Plans over Flow:** NPSP Engagement Plans create task sequences without complex automation configuration and allow fundraisers to mark tasks complete at their pace. Flow can automate the entire process but removes fundraiser discretion in cultivation approaches.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Major gift cultivation tracking | NPSP Moves Management + Opportunity Stages | Stage progression tracks relationship investment over time |
| Annual fund lapsed re-engagement | LYBUNT report + Campaign + Engagement Plan | Built-in NPSP tooling for lapsed donor identification |
| Portfolio tier assignment | Actionable Segmentation (NPC) or custom Contact field (NPSP) | NPC has native segmentation; NPSP requires custom field |
| Recurring donor lapsed trigger | ERD Status = Lapsed + triggered task/alert | ERD auto-transitions to Lapsed on missed payment |
| Donor upgrade identification | Giving history analysis: consecutive giving + amount trend | NPSP rollup fields (TotalGifts, NumberOfGifts, LastOppAmount) |
| Marketing email execution | NOT this skill — use Marketing Cloud MCAE | Donor lifecycle ≠ marketing automation execution |

---

## Recommended Workflow

1. **Platform confirmation** — Confirm NPSP or NPC. The feature set for moves management and segmentation differs significantly between platforms.
2. **Lifecycle stage definition** — With fundraising staff, define the donor lifecycle stages from prospect through upgrade and retention. Map each stage to Salesforce features (Opportunity Stage, Contact lifecycle field, ERD Status).
3. **Segmentation design** — Define portfolio tiers (annual, mid-level, major) and the criteria for each (giving history thresholds, capacity indicators, relationship stage).
4. **Lapsed donor definition** — Confirm organizational definitions of LYBUNT, SYBUNT, and multi-year lapsed. Confirm NPSP rollup fields (`npsp__LastOppDate__c`) are calculating correctly.
5. **Engagement Plan design** — For each lifecycle stage, design the task sequence for cultivation touches and re-engagement outreach.
6. **Report design** — Design portfolio review reports, lapsed donor dashboards, and upgrade candidate reports before configuring automation.
7. **Review** — Confirm segmentation design is NOT conflated with marketing automation. Verify lapsed reports use correct NPSP date rollup fields. Confirm NPSP is legacy platform if org was created after December 2025.

---

## Review Checklist

- [ ] NPSP vs NPC platform confirmed
- [ ] Donor lifecycle stages mapped to Salesforce features (Opportunity Stage, ERD Status, etc.)
- [ ] Portfolio tier definitions and criteria documented
- [ ] Lapsed donor definitions (LYBUNT, SYBUNT) confirmed with fundraising team
- [ ] NPSP rollup fields (`npsp__LastOppDate__c`, `npsp__TotalGifts__c`) confirmed accurate
- [ ] Engagement Plans designed for cultivation stage task sequences
- [ ] NPC Actionable Segmentation NOT conflated with marketing automation

---

## Salesforce-Specific Gotchas

1. **NPSP is no longer offered in new production orgs** — As of December 2025, new nonprofits use Nonprofit Cloud (NPC). Designs referencing NPSP Engagement Plans, LYBUNT reports, or NPSP rollup fields need to confirm the org is a legacy NPSP org. New orgs will not have the NPSP package.
2. **NPC Actionable Segmentation is not marketing automation** — NPC Actionable Segmentation classifies donors for portfolio management. It does NOT send emails, manage campaign audiences, or connect to Marketing Cloud. Conflating segmentation with campaign execution leads to scope creep into marketing automation territory.
3. **ERD Status transitions to Lapsed automatically** — Enhanced Recurring Donation status transitions from Active to Lapsed automatically when a scheduled payment is missed. This is a platform behavior that fundraising teams often discover unexpectedly when donors call about their lapsed status.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Donor lifecycle stage map | Visual map of lifecycle stages from prospect to major donor, with Salesforce feature alignment |
| Segmentation design | Portfolio tier definitions, criteria, and assignment workflow |
| Lapsed donor re-engagement design | Identification criteria, workflow, and Engagement Plan task sequences |

---

## Related Skills

- `npsp-engagement-plans` — For implementation of Engagement Plans supporting the cultivation task sequences designed in this skill
- `recurring-donations-setup` — For ERD configuration relevant to recurring donor lifecycle and lapsed re-engagement
- `program-outcome-tracking-design` — For the program delivery side of nonprofit CRM alongside donor lifecycle
