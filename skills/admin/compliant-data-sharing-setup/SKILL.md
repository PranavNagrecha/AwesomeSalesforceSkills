---
name: compliant-data-sharing-setup
description: "Declarative setup of Compliant Data Sharing (CDS) in Financial Services Cloud: enabling CDS per-object in IndustriesSettings, configuring OWDs, creating CDS permissions, adding the Financial Deal Participants related list, and defining Participant Roles. Trigger keywords: ethical walls, compliant data sharing setup, FSC sharing model, isolate banking teams, participant roles. NOT for standard Salesforce sharing rules, OWD, or role hierarchy sharing. NOT for programmatic participant record DML (use fsc-compliant-sharing-api instead)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "how do I set up ethical walls between retail banking and wealth management in Salesforce FSC"
  - "managers can see their team's accounts in FSC but they should not be able to under CDS"
  - "how to enable Compliant Data Sharing for Financial Deal and Opportunity in Financial Services Cloud"
  - "what permissions do admins need to configure Compliant Data Sharing"
  - "Financial Deal Participants related list not showing on Account layout"
  - "how to disable Compliant Data Sharing and what needs to happen first"
tags:
  - fsc
  - compliant-data-sharing
  - ethical-walls
  - sharing-model
  - financial-services
  - participant-roles
  - deal-management
inputs:
  - FSC org with Financial Services Cloud installed
  - Confirmation of which CDS-supported objects require ethical-wall enforcement (Account, Opportunity, Interaction, Interaction Summary, Financial Deal)
  - Team or business-unit structure to model as Participant Roles
  - OWD baseline setting for each target object (must be Private or Public Read-Only before enabling CDS)
outputs:
  - Step-by-step CDS enablement checklist (OWDs, IndustriesSettings metadata, Deal Management, permissions, layouts)
  - Participant Role naming and access-level guidance for the target org
  - Guidance on disabling CDS safely without orphan role records
  - Review checklist for admin handoff
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Compliant Data Sharing Setup

This skill activates when an FSC administrator or architect needs to configure Compliant Data Sharing (CDS) declaratively — enabling ethical-wall enforcement on supported objects, setting the required organization-wide defaults, creating CDS-specific permission sets, adding the Financial Deal Participants related list to page layouts, and defining Participant Role records. It does NOT cover Apex participant record DML; use the `fsc-compliant-sharing-api` skill for that.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has Financial Services Cloud installed and is on API v50.0 or later. CDS participant objects were introduced at that version.
- Know which objects need ethical-wall enforcement. CDS is supported natively on Account, Opportunity, Interaction, Interaction Summary, and Financial Deal. Custom-object CDS requires Summer '22+ and an additional `enableCompliantDataSharingForCustomObjects` flag.
- Identify the current OWD for each target object. CDS requires Private or Public Read-Only. If any target object is currently Public Read/Write, plan an OWD change before enabling CDS — changing OWD in production triggers a sharing recalculation.
- Understand the team separation requirements (e.g., retail banking vs. wealth management). These map directly to Participant Roles, which define the access level (Read or Edit) each role grants.
- Determine whether Financial Deal records are in scope. Financial Deal requires Deal Management to be enabled as a prerequisite before CDS for that object can be turned on.

---

## Core Concepts

### What Compliant Data Sharing Does

CDS enforces ethical walls by disabling role-hierarchy-based sharing on its supported objects. In a standard Salesforce org, a manager automatically inherits visibility into every record their subordinates own. CDS switches off this inheritance for the objects it manages. After CDS is enabled, a record's owner's manager does NOT automatically see that record. Access must be granted explicitly by assigning the user a Participant Role on the specific record.

This is a fundamentally different access model from standard OWD + role hierarchy + sharing rules. CDS runs as a parallel mechanism: OWDs still set the floor (Private or Public Read-Only), standard sharing rules still apply to non-CDS objects, but for CDS-enabled objects the role hierarchy is bypassed and CDS is the only grant path above OWD.

### Supported Objects and IndustriesSettings Flags

CDS is enabled per-object via the `IndustriesSettings` metadata type. Each supported object has its own flag:

| Object | IndustriesSettings Field |
|---|---|
| Account | `enableCompliantDataSharingForAccount` |
| Opportunity | `enableCompliantDataSharingForOpportunity` |
| Interaction | `enableCompliantDataSharingForInteraction` |
| Interaction Summary | `enableCompliantDataSharingForInteractionSummary` |
| Financial Deal | `enableCompliantDataSharingForFinancialDeal` |

Enabling CDS for an object is irreversible via Setup UI alone — the Salesforce support team must be involved for deactivation in most cases, and all Participant Role records for that object must be deleted first (see Disabling CDS below).

### Participant Roles and the Access Grant Model

A Participant Role is a named record (stored in the `ParticipantRole` object) that defines:
1. A human-readable name (e.g., "Relationship Manager", "Deal Lead", "Co-Advisor")
2. The `AccessLevel` it grants: Read or Edit

When an admin or automation assigns a user to a record via a Participant Role, the CDS engine writes a share row (`RowCause = 'CompliantDataSharing'`) for that user on that record. The Participant Role record itself is the durable source of truth. If the share row is deleted directly, the CDS engine rewrites it on the next recalculation. To revoke access, the Participant Role assignment (the `AccountParticipant` or equivalent record) must be deleted.

### Permissions Required for CDS Administration

Two permission sets are required for CDS to function:

- **CDS Manager permission** — grants the "Configure CDS" system permission. Admins with this permission can enable CDS in IndustriesSettings, create and manage Participant Role records, and configure Financial Deal Participants layouts.
- **CDS User permission** — grants the "Use CDS" system permission. End users with this permission can be assigned as participants on records. A user without "Use CDS" cannot be added as a participant even by an admin.

Both permissions must be assigned before testing CDS access grants. A common setup mistake is granting "Configure CDS" to the admin and forgetting "Use CDS" for the business users who need to be participants.

### Deal Management Prerequisite for Financial Deal CDS

If Financial Deal records are in scope, Deal Management must be enabled before CDS can be turned on for Financial Deal. Deal Management is enabled in Setup under Financial Services > Financial Deal Settings. Without this step, the `enableCompliantDataSharingForFinancialDeal` flag has no effect and the Financial Deal Participants related list is not available.

---

## Common Patterns

### Pattern 1: OWD + CDS Enablement Sequence

**When to use:** Initial CDS rollout for an org that has never had CDS enabled. Most of the time the target objects are currently Public Read/Write or not Private, requiring an OWD change.

**How it works:**

1. Identify current OWDs via Setup > Sharing Settings. Note every object that needs to change.
2. Change OWDs for target objects to Private or Public Read-Only. Do this during a maintenance window — OWD changes trigger sharing recalculations in production.
3. Enable CDS per object by deploying (or editing via Setup) the `IndustriesSettings` metadata with the relevant flags set to `true`.
4. Verify via Setup > Sharing Settings that the object shows "Compliant Data Sharing" as the active sharing mechanism.
5. Add the Financial Deal Participants related list to relevant page layouts if Financial Deal CDS is enabled.
6. Create Participant Role records to match the org's access model.
7. Assign CDS Manager and CDS User permission sets to the appropriate users.

**Why not the alternative:** Attempting to enable CDS before setting OWDs to Private/Read-Only causes the platform to accept the IndustriesSettings change but produce no share rows for participant assignments — nothing appears to work and the error is silent.

### Pattern 2: Defining Participant Roles for Ethical Wall Isolation

**When to use:** Two or more business lines (e.g., retail banking and wealth management) must be prevented from seeing each other's client accounts even when the same org hierarchy is used.

**How it works:**

1. Create a Participant Role for each distinct access level per business line (e.g., "Retail RM - Edit", "Wealth Advisor - Edit", "Deal Lead - Read").
2. The Access Level on the Participant Role determines what the CDS engine writes into the share row — Read or Edit. Name roles descriptively so the business can audit participant lists without needing admin access.
3. Assign users to records using only the roles appropriate for their business line. Do not create cross-line Participant Role assignments unless cross-line access is intentional.
4. Verify that managers in Retail Banking cannot see Wealth Management accounts by testing with a user in each hierarchy branch.

**Why not the alternative:** Using a single generic Participant Role for all business lines does enforce the ethical wall at the role-hierarchy level but provides no audit trail of which business line was granted access to which record. Named roles enable meaningful compliance reporting.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Target object OWD is Public Read/Write | Change OWD to Private first, then enable CDS | CDS share rows are never written when OWD is Public Read/Write |
| Financial Deal CDS needed | Enable Deal Management before enabling CDS for Financial Deal | Deal Management is a hard prerequisite |
| Manager must see subordinate records | Create explicit Participant Role assignments for the manager | Role-hierarchy inheritance is disabled by CDS; there is no automatic path |
| Need to disable CDS | Delete all Participant Role assignments for the object, then contact Salesforce Support | Platform blocks CDS deactivation while active participant records exist |
| User cannot be added as participant | Check "Use CDS" permission assignment | Users missing this permission are rejected by the CDS engine silently |
| Custom object ethical walls | Enable `enableCompliantDataSharingForCustomObjects` + per-object flag on Summer '22+ | Both flags are required; per-object flag alone produces no share rows |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Verify prerequisites — confirm FSC is installed, API version is 50.0+, Deal Management is enabled if Financial Deal CDS is needed, and the org admin has the CDS Manager permission set assigned.
2. Set OWDs — for every CDS target object, confirm OWD is Private or Public Read-Only in Setup > Sharing Settings. If not, schedule an OWD change and sharing recalculation during a maintenance window.
3. Enable CDS per object — in Setup > Industries Settings (or by deploying `IndustriesSettings` metadata), set the `enableCompliantDataSharing` flag for each required object to `true`.
4. Configure layouts and roles — add the Financial Deal Participants related list to Account and Financial Deal page layouts where applicable; create Participant Role records representing each access tier in the org (e.g., "Relationship Manager - Edit", "Co-Advisor - Read").
5. Assign permissions and validate — assign CDS Manager to admins and CDS User to all business users who will be participants; test by assigning a Participant Role on a real record and verifying access is granted without role-hierarchy inheritance.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] OWD for each CDS-enabled object is Private or Public Read-Only
- [ ] Deal Management enabled (required if Financial Deal CDS is in scope)
- [ ] `enableCompliantDataSharing` IndustriesSettings flag set to `true` for every target object
- [ ] Financial Deal Participants related list added to relevant page layouts
- [ ] CDS Manager permission set assigned to all CDS administrators
- [ ] CDS User permission set assigned to every user who will be a participant on any record
- [ ] At least one Participant Role record created per distinct access tier
- [ ] Managers verified to NOT automatically see subordinate records under CDS
- [ ] Access grants verified via explicit Participant Role assignments only
- [ ] Disabling CDS path documented if required: all participant assignments deleted before support ticket

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Managers do not inherit subordinate records under CDS** — This is intentional and is the entire purpose of CDS. However, admins migrating from standard sharing frequently open a support ticket thinking CDS is broken. After enabling CDS, a manager must be explicitly assigned as a participant on every record they need to access. There is no automatic inheritance path, and no sharing rule can restore it for CDS-enabled objects.

2. **Disabling CDS requires deleting all participant role assignments first** — The platform blocks deactivation of CDS for any object that still has active `AccountParticipant`, `OpportunityParticipant`, or equivalent records. Attempting to disable without clearing participants results in an error. The cleanup must happen via data tools or Apex before a Salesforce Support ticket for deactivation can be processed.

3. **CDS and standard sharing rules are independent mechanisms** — Enabling a sharing rule on a CDS-enabled object does not interact with the CDS engine. Standard sharing rules continue to grant access via the normal `RowCause` values, while CDS manages `RowCause = 'CompliantDataSharing'` rows separately. This means a record can be accessible via both a sharing rule AND a CDS participant role simultaneously, which can create unintended cross-team visibility if sharing rules are not audited when CDS is introduced.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CDS enablement checklist | Step-by-step admin task list for enabling CDS on a target object |
| Participant Role design | Named role records with access levels mapped to business-line access model |
| Permission set assignment list | CDS Manager and CDS User assignments per user group |
| `check_compliant_data_sharing_setup.py` report | Static analysis of IndustriesSettings metadata and sharing settings for CDS configuration issues |

---

## Related Skills

- fsc-compliant-sharing-api — Use for programmatic participant record DML after CDS is enabled declaratively via this skill
- fsc-architecture-patterns — Use for broader FSC sharing architecture decisions including multi-object CDS rollout sequencing
