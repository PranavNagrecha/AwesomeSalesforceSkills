---
name: health-cloud-multi-cloud-strategy
description: "Use this skill when designing the license model, cloud topology, and org structure for a Salesforce Health Cloud implementation that involves more than one Salesforce cloud product (Experience Cloud patient portals, OmniStudio engagement flows, Marketing Cloud care campaigns, or Service Cloud case management). Trigger keywords: Health Cloud multi-cloud, patient portal licensing, Health Cloud Experience Cloud add-on, OmniStudio Health Cloud PSL, Marketing Cloud HIPAA BAA healthcare, multi-cloud healthcare org design. NOT for individual cloud configuration setup (e.g. configuring a single Health Cloud record page or a single Experience Cloud site), NOT for single-cloud Health Cloud implementations, and NOT for Health Cloud data model object definitions (see health-cloud-data-model skill)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Scalability
triggers:
  - "We are adding a patient-facing portal to our Health Cloud org — what licenses do we need?"
  - "Our healthcare client wants to use OmniStudio for guided care plans inside Health Cloud — how do permission sets and licenses work together?"
  - "We need Marketing Cloud for care program campaigns in Health Cloud — what are the HIPAA compliance requirements for connecting them?"
  - "How do Service Cloud and Health Cloud licenses relate — do we need separate Service Cloud licenses for our agents?"
  - "We are designing the overall cloud topology for a multi-cloud healthcare Salesforce implementation — where do we start?"
tags:
  - health-cloud
  - experience-cloud
  - service-cloud
  - multi-cloud
  - licensing
  - omni-studio
  - marketing-cloud
  - hipaa
  - architect
inputs:
  - List of intended user personas (internal care coordinators, patient portal users, marketing users)
  - Confirmed Salesforce edition (Enterprise or Unlimited — Health Cloud requires Enterprise minimum)
  - Use cases in scope (care coordination, patient self-service portal, care program campaigns, guided intake flows)
  - Whether Marketing Cloud is already licensed or planned
  - Whether a HIPAA Business Associate Agreement (BAA) is in place and with which clouds
outputs:
  - Multi-cloud license model recommendation with which SKUs are required vs. included
  - Permission set license (PSL) assignment matrix by persona
  - Org design recommendation (single org vs. hub-and-spoke)
  - Marketing Cloud integration decision with HIPAA BAA scope guidance
  - Architecture decision record (ADR) artifact documenting cloud topology rationale
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Health Cloud Multi-Cloud Strategy

This skill activates when an architect or practitioner needs to design the cross-cloud license model and org topology for a Salesforce Health Cloud implementation that spans multiple Salesforce products. It provides decision guidance on which clouds are bundled, which are separate add-ons, how permission sets must be assigned per persona, and what compliance obligations attach to each cloud connection.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Edition confirmation:** Health Cloud requires Salesforce Enterprise edition or higher. Verify the contracted edition before making any license bundling assumptions.
- **Persona inventory:** Collect a complete list of user types — internal care team members (nurses, case managers, care coordinators), patient portal users, marketing operations staff, and system administrators. Licensing and PSL assignments differ fundamentally between internal and external (portal) users.
- **HIPAA BAA scope:** Confirm which Salesforce clouds are covered under the org's HIPAA Business Associate Agreement. A BAA covering Health Cloud does NOT automatically extend to Marketing Cloud — Marketing Cloud requires its own separate HIPAA BAA.
- **Most common wrong assumption:** Practitioners frequently assume that a Health Cloud license includes Experience Cloud for patient portals. It does not. Experience Cloud for Health Cloud is a separate paid add-on SKU.
- **OmniStudio PSL requirement:** OmniStudio is bundled within Health Cloud licenses but the capability does not activate automatically. Each user who will use OmniStudio components must be assigned both the Health Cloud permission set license AND the OmniStudio User permission set license explicitly.
- **Service Cloud is implicit:** Unlike Experience Cloud, Service Cloud case management capabilities ARE implicitly included in every Health Cloud license and do not require a separate Service Cloud add-on purchase. Do not design a separate Service Cloud license line into the quote for internal care coordinators.

---

## Core Concepts

### Health Cloud Builds on Top of CRM — Service Cloud Is Included

Health Cloud is not a standalone product. It is a managed package and permission set layer delivered on top of a standard Salesforce CRM org (Sales Cloud + Service Cloud at the same edition level). Every Health Cloud license implicitly includes Service Cloud capabilities — case management, entitlements, omni-channel routing, and the full Case object — at no additional license cost for internal users. Care coordinators use Service Cloud Cases as the backbone of care coordination without needing a separate Service Cloud license.

Consequence: Do not add Service Cloud as a separate line item in architecture or licensing documentation for internal care team users. It creates confusion and may lead procurement to purchase redundant licenses.

### Experience Cloud for Health Cloud Is a Separate Paid Add-On

Patient-facing portals and caregiver portals built on Experience Cloud are NOT included in a standard Health Cloud license. They require the **Experience Cloud for Health Cloud** add-on SKU, which provisions:
- Customer Community Plus or Partner Community licenses for external portal users
- The Health Cloud-specific Experience Cloud components (patient portal templates, CareProgramEnrollee integration, PersonAccount-based site membership)
- Per-user permission set licenses for Experience Cloud Health Cloud users

Each external portal user must be assigned the **Health Cloud for Experience Cloud** permission set license. Failure to do this is the single most common licensing error in Health Cloud implementations.

### OmniStudio Bundled But Requires Explicit PSL Assignment

OmniStudio (FlexCards, OmniScripts, Integration Procedures, DataRaptors) is packaged within Health Cloud licenses — customers do not purchase OmniStudio separately when they have Health Cloud. However, activation requires three explicit permission set assignments for each internal user who needs OmniStudio:

1. **Health Cloud** permission set license
2. **Health Cloud Platform** permission set license (provides object-level access to Health Cloud data model objects)
3. **OmniStudio User** permission set license

If any of the three is missing, OmniStudio components will be visible in the metadata but will fail silently or throw permission errors at runtime for that user.

### Marketing Cloud Health Cloud Connect and the HIPAA BAA Gap

Marketing Cloud can be connected to Health Cloud to enable care program campaign management, appointment reminders, and patient re-engagement journeys via Marketing Cloud Health Cloud Connect (the managed integration package). However:

- Marketing Cloud operates as a **separate system** with its own data store — PHI sent into Marketing Cloud is governed by the Marketing Cloud HIPAA BAA, not the Health Cloud BAA.
- A separate HIPAA BAA must be executed with Salesforce specifically for Marketing Cloud before any PHI (patient demographics, care program enrollment status, appointment data) is sent from Health Cloud into Marketing Cloud.
- Until that BAA is in place, only de-identified or non-PHI data can flow from Health Cloud to Marketing Cloud.
- Marketing Cloud Connect syncs data via the Connected App framework and requires the Marketing Cloud Connector permission set in the Health Cloud org.

---

## Common Patterns

### Three-Tier Patient Portal Architecture

**When to use:** The implementation includes patient self-service (appointment scheduling, care plan viewing, secure messaging) alongside internal care coordinator workflows.

**How it works:**
- Tier 1 — Internal: Care coordinators and clinicians use the internal Health Cloud org with Service Cloud cases as care coordination records. OmniStudio OmniScripts drive guided intake and assessment flows.
- Tier 2 — Portal: Patients access an Experience Cloud site (licensed as Experience Cloud for Health Cloud add-on). The site uses PersonAccount for patient identity and CareProgramEnrollee records to display enrolled care programs. Data is read/written through the standard Health Cloud data model — no separate integration middleware is needed.
- Tier 3 — Campaign: Marketing Cloud Health Cloud Connect syncs care program enrollment and appointment status into Marketing Cloud for automated outreach journeys, governed under a Marketing Cloud HIPAA BAA.

**Why not the alternative:** Building the patient portal as a separate Salesforce org (a "portal org") introduces bidirectional sync complexity, duplicate identity management, and doubles the compliance surface. Single-org with Experience Cloud for Health Cloud is strongly preferred unless strict data residency requirements make a separate org necessary.

### Care Coordination Hub with OmniStudio Guided Flows

**When to use:** The care team requires standardized, multi-step intake assessments (SDOH screening, medication reconciliation) that must be auditable and configurable without code deployments.

**How it works:**
- OmniStudio OmniScripts replace custom Visualforce or LWC wizard flows for guided data collection.
- DataRaptors read and write to Health Cloud data model objects (EpisodeOfCare, CarePlan, ClinicalEncounter).
- Integration Procedures call external EHR systems (Epic, Cerner) via named credentials without custom Apex.
- FlexCards surface summarized patient context on the care coordinator's record page.

All of this runs within the standard Health Cloud org under the bundled OmniStudio entitlement — no separate OmniStudio license purchase required, but each user needs all three PSLs assigned (see Core Concepts).

**Why not the alternative:** Custom LWC-based wizards require code deployments for every assessment change, cannot be managed by non-developer care program staff, and lack the built-in audit trail that OmniScripts provide through the OmniProcess execution log.

### Single-Org vs. Hub-and-Spoke for Multi-Entity Health Systems

**When to use:** The health system has multiple hospitals, clinics, or business units that may need data isolation while sharing a Salesforce contract.

**How it works:**
- **Single org:** All entities share one Salesforce org. Data visibility is controlled via Health Cloud's Care Team sharing model, Sharing Sets for Experience Cloud users, and role hierarchy. Lowest cost, simplest administration.
- **Hub-and-spoke:** Each business unit gets its own Salesforce org (spoke). A central Platform Events or MuleSoft integration layer aggregates cross-entity patient records. Used only when regulatory requirements mandate data residency separation between entities (e.g., a behavioral health subsidiary with stricter 42 CFR Part 2 obligations).

**Why not the alternative:** Hub-and-spoke dramatically increases license cost, deployment complexity, and integration maintenance. Architects should exhaust single-org isolation patterns before recommending multiple orgs.

---

## Decision Guidance

| Use Case | Cloud / License Required | Included in Health Cloud? | Notes |
|---|---|---|---|
| Internal care coordinator case management | Service Cloud (Cases, Omni-Channel) | Yes — implicit | No separate purchase needed |
| Patient self-service portal | Experience Cloud for Health Cloud (add-on SKU) | No — separate add-on | Per-external-user PSL required |
| Guided care assessment flows (OmniScripts) | OmniStudio | Yes — bundled | Requires 3 PSL assignments per user |
| Appointment reminder and re-engagement campaigns | Marketing Cloud + Health Cloud Connect | No — separate product | Requires dedicated Marketing Cloud HIPAA BAA before PHI is sent |
| EHR integration (Epic, Cerner) | MuleSoft or named credential callouts | Not included | MuleSoft licensed separately; named credential callouts use Apex callout limits |
| Analytics on care program outcomes | CRM Analytics for Health Cloud | No — separate add-on | Health Cloud includes basic report builder; full CRM Analytics requires separate license |
| Caregiver portal (family member access) | Experience Cloud for Health Cloud (same add-on) | No | Caregiver access uses PersonAccount relationship records and sharing sets |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory all personas and their cloud touchpoints.** For every user type, document whether they are internal (care team) or external (patient, caregiver, marketing ops). Map each persona to the Salesforce cloud(s) they will interact with. This drives the license model.

2. **Confirm which clouds are in scope and which are purchased.** Use the decision guidance table above to identify which clouds are bundled (Service Cloud, OmniStudio) versus which require separate purchase (Experience Cloud for Health Cloud, Marketing Cloud, CRM Analytics). Cross-reference against the customer's signed order form.

3. **Design the permission set license (PSL) assignment matrix.** For every internal user role, determine whether they need Health Cloud PSL only, or also Health Cloud Platform and OmniStudio User PSLs. For external portal users, confirm Health Cloud for Experience Cloud PSL assignment. Document this matrix as a deliverable.

4. **Assess HIPAA BAA scope.** Confirm whether the existing HIPAA BAA covers Health Cloud only, or also Marketing Cloud. If Marketing Cloud campaigns will include PHI, initiate the Marketing Cloud HIPAA BAA process with the Salesforce account team before any Health Cloud data flows into Marketing Cloud environments.

5. **Choose org topology.** Evaluate single-org (preferred) versus hub-and-spoke based on data isolation requirements, regulatory obligations per business unit, and total cost of ownership. Document the decision rationale in an Architecture Decision Record.

6. **Validate the Experience Cloud site configuration.** If a patient portal is in scope, confirm that the Experience Cloud site uses PersonAccount (not standard Contact) for member identity, that Sharing Sets are configured to give patients access to their own CareProgramEnrollee and CarePlan records, and that the Experience Cloud for Health Cloud PSL is assigned to all portal user profiles.

7. **Review the complete license model with legal and compliance.** Before finalizing architecture, walk the HIPAA BAA scope and data flow diagram with the customer's legal and compliance team. Confirm that every cloud that will touch PHI is covered under the appropriate BAA.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All user personas are classified as internal or external and mapped to the correct Salesforce cloud
- [ ] Experience Cloud for Health Cloud add-on SKU is on the order form if a patient portal is in scope
- [ ] OmniStudio PSL assignment includes Health Cloud + Health Cloud Platform + OmniStudio User for all OmniStudio users
- [ ] Service Cloud is NOT listed as a separate line-item license for internal care coordinator users
- [ ] Marketing Cloud HIPAA BAA status is confirmed before any PHI flow from Health Cloud to Marketing Cloud is designed
- [ ] Org topology decision (single-org vs. hub-and-spoke) is documented with rationale
- [ ] Experience Cloud site uses PersonAccount (not Contact) for patient identity
- [ ] CareProgramEnrollee and CarePlan Sharing Sets are configured for portal user record access
- [ ] Architecture Decision Record (ADR) documenting the multi-cloud topology is produced

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Experience Cloud for Health Cloud PSL is not auto-assigned to portal profiles** — When an admin enables Experience Cloud for Health Cloud and creates the portal site, the Health Cloud for Experience Cloud permission set license is NOT automatically assigned to the portal user profile. Each portal user's profile must have this PSL explicitly assigned. Without it, Health Cloud components (Care Plan viewer, CareProgramEnrollee FlexCards) on the portal site throw "Insufficient Privileges" errors at runtime even though the site itself loads.

2. **PersonAccount is a one-way conversion in Health Cloud orgs** — Health Cloud implementations almost always require PersonAccount enabled for patient identity. Once PersonAccount is enabled in a Salesforce org, it cannot be disabled. If a customer's existing Service Cloud org has Contact records not linked to PersonAccount, a migration plan must be in place before Health Cloud is layered on. Retrofitting PersonAccount into a live org with existing Account-Contact relationships requires a full data migration and relationship remapping.

3. **OmniStudio components fail silently when Health Cloud Platform PSL is missing** — If a user has the Health Cloud PSL and the OmniStudio User PSL but is missing the Health Cloud Platform PSL, OmniScripts that read or write to Health Cloud-specific objects (EpisodeOfCare, CarePlan, ClinicalEncounter) will fail at the DataRaptor step with a generic "Record not found" or "FIELD_INTEGRITY_EXCEPTION" error rather than a clear permission error. This is the hardest PSL assignment bug to diagnose because the user can open the OmniScript UI successfully but the data operations silently fail.

4. **Marketing Cloud Health Cloud Connect requires the Connected App in both orgs** — When configuring Marketing Cloud Health Cloud Connect, the Marketing Cloud connector package must be installed in the Health Cloud org AND the corresponding Connected App credentials must be configured in Marketing Cloud's Setup. If the credentials are configured only on the Marketing Cloud side (a common partial-setup mistake), the sync appears to work but data does not flow, and the error surfaces only in Marketing Cloud's Synchronization Dashboard — not in Salesforce Setup logs.

5. **Sharing Sets for Experience Cloud portal users do not support all Health Cloud object relationships** — Sharing Sets (the mechanism that gives external portal users access to records they "own") work on direct lookup relationships from the portal user's PersonAccount. CarePlanTemplate and some ClinicalEncounter sub-objects are not reachable through Sharing Sets alone and require Apex sharing rules or OWD relaxation. Architects who design the portal access model assuming Sharing Sets cover all Health Cloud objects will discover the gaps in UAT, not design.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Multi-cloud license model | Table of all Salesforce clouds in scope, whether each is bundled or a separate SKU, and per-user license cost implications |
| PSL assignment matrix | Grid of every internal and external user persona against the permission set licenses they must receive, with rationale |
| Org topology ADR | Architecture Decision Record documenting single-org vs. hub-and-spoke decision with constraints, options considered, and chosen approach |
| HIPAA BAA scope diagram | Data flow diagram showing which clouds touch PHI and which BAAs must be in place for each flow |
| Experience Cloud site configuration checklist | Step-by-step verification list for PersonAccount enablement, Sharing Sets, and PSL assignment for the patient portal |

---

## Related Skills

- health-cloud-data-model — Use alongside this skill to understand the specific Health Cloud objects (CarePlan, EpisodeOfCare, CareProgramEnrollee) that the multi-cloud architecture must expose through the Experience Cloud portal and OmniStudio flows
- health-cloud-patient-setup — Use for individual patient record configuration once the multi-cloud org design decisions from this skill are finalized
- hipaa-compliance-architecture — Use for the full HIPAA technical safeguards architecture; this skill focuses on which clouds need BAAs, not on the full technical control set
- experience-cloud-setup — Use for the mechanics of building the Experience Cloud site once the licensing and persona decisions from this skill are documented
