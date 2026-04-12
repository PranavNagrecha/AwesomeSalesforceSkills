---
name: fundraising-process-mapping
description: "Use this skill when designing or documenting nonprofit fundraising lifecycle stages, donor pipeline workflows, cultivation-to-stewardship cycles, major gift solicitation sequences, or Salesforce Opportunity sales process configuration for NPSP or Nonprofit Cloud. Trigger keywords: fundraising lifecycle, donor pipeline, cultivation stage, solicitation workflow, major gift process, moves management, NPSP Opportunity stages, stewardship cycle, NPC fundraising stages. NOT for implementation of Engagement Plans, gift entry processing, payment integration, or recurring donation configuration."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "How do I design a donor cultivation workflow in Salesforce for our major gifts program?"
  - "What Opportunity stages does NPSP provide out of the box for tracking the fundraising lifecycle?"
  - "We are moving from NPSP to Nonprofit Cloud and need to remap our solicitation process stages"
  - "How should we model the moves management pipeline from prospect identification to stewardship?"
  - "Our gift officers need a standardized major gift workflow from cultivation through close and beyond"
tags:
  - nonprofit
  - NPSP
  - fundraising
  - moves-management
  - major-gifts
  - donor-pipeline
  - cultivation
  - stewardship
  - solicitation
  - NPC
inputs:
  - Confirmation of whether the org is on legacy NPSP or Nonprofit Cloud (NPC) — critical fork point
  - Existing fundraising program types in use (annual fund, major gifts, grants, in-kind, planned giving)
  - Gift officer and development team role structure (who owns which pipeline stages)
  - Any naming conventions, numeric thresholds, or probability targets already in use
  - Whether Moves Management is actively tracked (contacts, interactions, strategy per prospect)
outputs:
  - Documented stage map per fundraising program type (name, probability, entry criteria, exit criteria, owner)
  - Recommended Opportunity Record Type to Sales Process assignment for each program
  - Decision guidance on NPSP vs NPC stage configuration approach
  - Checklist of stage design decisions before any Salesforce configuration begins
  - Annotated lifecycle diagram narrative covering cultivation, solicitation, and stewardship phases
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Fundraising Process Mapping

This skill activates when a practitioner needs to design or document the fundraising lifecycle in Salesforce — mapping donor cultivation, solicitation, and stewardship phases to Opportunity stages and sales processes in either NPSP (legacy) or Nonprofit Cloud (NPC). It covers the NPSP four-process model, the NPC stage model divergence, Moves Management alignment, and the decision framework for stage design across fundraising program types. It does NOT cover how to configure Engagement Plans, process gift entries, integrate payment processors, or manage recurring donations.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the platform** — Determine whether the org is on legacy NPSP (the managed package, now end-of-life for new installs as of December 2025) or Nonprofit Cloud (NPC, the next-generation native Salesforce offering). The stage configuration approach, available objects, and feature availability differ materially between the two. If the org was created after December 2025 and does not have the `npsp` namespace in Setup > Installed Packages, it is on NPC or a blank org, not NPSP.
- **Identify program types** — NPSP ships four pre-configured Opportunity sales processes: Donation, Grant, In-Kind, and Major Gift. Each has a distinct stage picklist sequence. Confirm which program types the organization runs and whether all four are needed or only a subset.
- **Understand who owns each stage** — Solicitation and stewardship stages often have different responsible roles (prospect researcher, gift officer, stewardship coordinator). Mapping stage ownership prevents ambiguity about when a record moves and who is accountable.
- **Establish the probability model** — Salesforce displays a Probability % field on Opportunity that forecasts pipeline value. Nonprofits using pipeline reports depend on accurate probabilities per stage. Gather any existing probability targets before designing stages.

---

## Core Concepts

### NPSP Four Pre-Configured Sales Processes

NPSP ships four Opportunity sales processes, each mapped to a specific Opportunity Record Type. These processes define the stage picklist values available to gift officers:

1. **Donation** — Used for annual fund, direct mail, and general unrestricted gifts. Typical stages include Prospecting, Cultivation, Solicitation, Closed Won (e.g., "Pledged"), and Closed Lost. Stage names and probabilities are editable but the record type and process association must be preserved when customizing.
2. **Grant** — Used for institutional grants from foundations, government, or corporations. Stages reflect the grant calendar: Letter of Inquiry, Application, Under Review, Awarded, Closed Lost. A key behavioral difference is the Close Date aligns to the grant decision deadline, not a solicitation event.
3. **In-Kind** — Used for non-cash donations (goods, services, property). Stages are simpler: In Discussions, Accepted, Received, Declined. Valuation documentation is often tracked via a custom field rather than through stage.
4. **Major Gift** — Used for high-value individual donor solicitations managed through Moves Management. Stages typically follow the cultivation arc: Identification, Qualification, Cultivation, Solicitation, Verbal Commitment, Pledged (Closed Won), Stewardship. Probability values are set low in early stages and increase as the relationship develops.

The `Opportunity.StageName` field drives all stage-based automation, rollups, and pipeline reports. The values available to a user depend on the Sales Process associated with the Opportunity's Record Type.

### NPSP vs Nonprofit Cloud (NPC) Stage Model

NPSP and NPC are not interchangeable. As of December 2025, Salesforce no longer offers NPSP as a pre-configured package for new production orgs. New nonprofit orgs will be provisioned with Nonprofit Cloud (NPC) or a standard Sales Cloud org.

Key differences for fundraising process mapping:

- **NPSP** stores fundraising data on the standard `Opportunity` object, extended with the `npsp__` namespace fields. Sales processes and Record Types are standard Salesforce components configured in Setup.
- **NPC** introduces new objects in the Fundraising module (e.g., `GiftTransaction`, `GiftEntry`) alongside or instead of the NPSP Opportunity model. NPC does not use NPSP Engagement Plans — that feature does not exist in NPC in the same form.
- **Stage field names** may differ between NPSP and NPC. A stage value called "Pledged" in NPSP may not exist in an NPC-native stage set; practitioners must document existing values before attempting any lift-and-shift migration.

### Moves Management Alignment

Moves Management is the fundraising methodology that tracks discrete relationship-building interactions ("moves") between gift officers and major gift prospects. In Salesforce with NPSP, Moves Management is reflected through:

- Opportunity stage progression on the Major Gift sales process — each stage corresponds to a phase of the relationship (Qualification, Cultivation, Solicitation).
- Contact or Account Contact Roles linking the prospect to the Opportunity.
- Activities (Tasks and Events) logged against the Opportunity or Contact to record each move.
- NPSP Engagement Plans applied to drive consistent stewardship task sequences post-close.

Moves Management in Salesforce is a process design discipline, not a standalone feature. The quality of the lifecycle map directly determines the usefulness of pipeline reports and gift officer dashboards.

### Cultivation, Solicitation, and Stewardship Phases

Every major fundraising lifecycle — regardless of platform — moves through three broad phases:

1. **Cultivation** — Building the relationship and assessing capacity and interest before making an ask. Salesforce stages in this phase typically have low probability values (5%–25%). Moves in this phase include discovery calls, site visits, impact presentations, and event invitations.
2. **Solicitation** — Making the formal ask. A single stage (often called "Solicitation" or "Ask Made") with a probability that reflects confidence in the outcome (typically 50%–75% for major gifts). The Close Date should reflect the expected decision date.
3. **Stewardship** — Post-close recognition, reporting, and relationship maintenance for future giving. NPSP does not ship a post-close stage by default (Closed Won ends the active pipeline), but some organizations add a "Stewardship" stage for in-progress gift agreements or multi-year pledges still under active management.

---

## Common Patterns

### Four-Process Stage Map (NPSP Standard)

**When to use:** The org is on legacy NPSP, runs multiple fundraising program types, and needs a documented stage map before any configuration or pipeline reporting is built.

**How it works:**
1. List all four NPSP Record Types: Donation, Grant, In-Kind, Major Gift.
2. For each Record Type, retrieve the associated Sales Process and list its current stage values with probabilities.
3. For each stage, document: stage name, probability %, entry criteria (what event or decision moves the record into this stage), exit criteria (what triggers the move to the next stage), and responsible role.
4. Flag any stages that are missing entry/exit criteria — these are pipeline report accuracy risks.
5. Present the map to development leadership for sign-off before any Salesforce configuration work begins.

**Why not the alternative:** Skipping the documentation step and configuring stages directly in Setup leads to stage names that only one gift officer understands, missing probability values, and pipeline reports no one trusts.

### NPC Stage Audit Before Customization

**When to use:** The org is on Nonprofit Cloud (NPC) or is migrating from NPSP to NPC and needs to map existing NPSP stages to their NPC equivalents before going live.

**How it works:**
1. Export the current NPSP Opportunity stage picklist values and their Record Type assignments using the Salesforce Metadata API or Setup UI.
2. Document all active Opportunity records by stage and Record Type to identify which stages have live data.
3. Review the NPC fundraising object model and confirm which objects replace NPSP Opportunities for each program type.
4. Build a mapping table: NPSP stage → NPC stage equivalent (or "no equivalent — requires new design").
5. Identify automation, rollups, and reports that reference specific stage values by name — these must be updated as part of any NPC migration.

**Why not the alternative:** Assuming NPSP stage names carry over to NPC without validation leads to broken reports, failed automation, and lost historical data.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org is on legacy NPSP, needs stage review | Use the four-process NPSP standard stage map pattern | NPSP ships with these four processes; customization should be minimal and documented |
| New org created after December 2025 | Confirm NPC or standard Salesforce; do not assume NPSP is present | NPSP is no longer provisioned for new orgs as of Dec 2025 |
| Migrating from NPSP to NPC | Run the NPC stage audit before configuration | Stage names, objects, and features differ materially; direct lift-and-shift fails |
| Major gift program needs Moves Management tracking | Map stages to Major Gift sales process with explicit entry/exit criteria and Activities logging | Moves Management is a process discipline expressed through stages and activities |
| Org runs only one fundraising program type | Single sales process with a custom stage sequence | Four-process model adds unnecessary complexity for single-program orgs |
| Grant program stages need calendar alignment | Close Date = grant decision deadline; stage = current application status | Grant lifecycle is calendar-driven, not relationship-driven |
| Need stewardship tracking post-close | Add a post-close stage or use Engagement Plans for stewardship tasks | Closed Won ends pipeline visibility; multi-year pledges may need a stewardship stage |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm platform and installed packages** — Check Setup > Installed Packages for the `npsp` namespace. If absent and the org was created after December 2025, the org is NPC or standard Salesforce. Document the platform before any stage design work begins.
2. **Inventory existing Record Types and Sales Processes** — In Setup > Opportunity Record Types and Setup > Sales Processes, list all existing configurations. For NPSP orgs, confirm the four standard processes are present (Donation, Grant, In-Kind, Major Gift). For NPC orgs, confirm which objects and stage fields are in use.
3. **Map the fundraising lifecycle per program type** — For each active program type, produce a stage map with: stage name, probability %, entry criteria, exit criteria, and responsible role. Use the output template from this skill as the starting structure.
4. **Validate with development leadership** — Present the stage map to the chief development officer or equivalent before any Salesforce configuration. Stage names must reflect how gift officers actually talk about their pipeline, not generic Salesforce defaults.
5. **Document Moves Management alignment for major gifts** — For the Major Gift process, explicitly connect each stage to a phase of the Moves Management methodology (Identification, Qualification, Cultivation, Solicitation, Stewardship). This alignment drives gift officer dashboard design and pipeline forecasting.
6. **Identify automation dependencies** — List any Flows, Process Builder processes, or Apex triggers that fire on stage changes. These must be reviewed and updated if stage values are modified.
7. **Hand off to implementation** — Provide the completed stage map and automation dependency list to the configuration team. This skill's output ends at documented design; implementation of Engagement Plans, stage-change Flows, or rollup rules is handled by downstream skills.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Platform confirmed as NPSP or NPC (not assumed)
- [ ] All active Opportunity Record Types and Sales Processes inventoried
- [ ] Stage map produced for each active fundraising program type
- [ ] Each stage has documented probability %, entry criteria, and exit criteria
- [ ] Responsible role assigned to each stage
- [ ] Major Gift stages aligned to Moves Management phases (Identification → Qualification → Cultivation → Solicitation → Stewardship)
- [ ] Development leadership has reviewed and approved the stage map
- [ ] Automation dependencies on stage values identified and listed for the implementation team
- [ ] NPC/NPSP divergence flagged if org is post-December 2025 or migrating

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **NPSP No Longer Available for New Orgs (December 2025)** — Salesforce ended new NPSP provisioning in December 2025. Any engagement with a nonprofit org created after that date must confirm the actual platform before applying NPSP guidance. Recommending NPSP configuration steps in an NPC org will produce errors, confusion, or wasted setup work.
2. **NPC Does Not Have NPSP Engagement Plans** — The Engagement Plans feature (`npsp__Engagement_Plan_Template__c` and related objects) is specific to the NPSP managed package. It does not exist in Nonprofit Cloud (NPC). Practitioners designing stewardship cadences for NPC orgs must use Flow, Cadences (Sales Engagement), or other native automation — not Engagement Plans.
3. **Sales Process Stage Values Are Picklist-Restricted** — Changing a stage value name after Opportunities are in production does not update the existing records. Active pipeline records retain the old stage name, which may break reports and automation that reference the value by name. Stage renaming requires a data update job, not just a picklist edit.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Fundraising stage map | Per-program-type table of stage name, probability, entry criteria, exit criteria, and responsible role |
| NPSP/NPC platform confirmation note | Documented confirmation of which platform the org is on and what that means for stage configuration |
| Moves Management alignment matrix | Mapping of Major Gift stages to Moves Management phases (Identification, Qualification, Cultivation, Solicitation, Stewardship) |
| Automation dependency list | List of Flows, triggers, or rollups that reference specific stage values and will need updating if stages change |

---

## Related Skills

- `npsp-engagement-plans` — Use after stage design is complete to implement stewardship task automation on NPSP Opportunity Closed Won; Engagement Plans are an implementation tool, not a design tool
- `gift-entry-and-processing` — Use for NPSP and NPC gift entry mechanics, batch processing, and payment processing flows; separate from lifecycle stage design
- `fundraising-integration-patterns` — Use when the donor pipeline needs to connect to external CRMs, wealth screening tools, or peer-to-peer fundraising platforms
- `nonprofit-platform-architecture` — Use for overall NPSP vs NPC platform selection and data architecture decisions
