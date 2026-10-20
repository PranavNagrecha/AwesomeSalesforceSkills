---
name: compliant-data-sharing-setup
description: "Declarative setup of Compliant Data Sharing (CDS) in Financial Services Cloud: enabling CDS per-object in IndustriesSettings, configuring OWDs, creating CDS permissions, adding the Financial Deal Participants related list, and defining Participant Roles. Trigger keywords: ethical walls, compliant data sharing setup, FSC sharing model, isolate banking teams, participant roles. NOT for participant record DML from Apex — use apex/fsc-compliant-sharing-api. NOT for the FSC sharing design decision — use architect/fsc-architecture-patterns."
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
  - OWD baseline setting for each target object (Private or Public Read-Only before enabling CDS is a Help-only prerequisite, UNVERIFIED 2026-10-20)
outputs:
  - Step-by-step CDS enablement checklist (OWDs, IndustriesSettings metadata, Deal Management, permissions, layouts)
  - Participant Role naming and access-level guidance for the target org
  - Guidance on disabling CDS safely without orphan role records
  - Review checklist for admin handoff
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Compliant Data Sharing Setup

This skill activates when an FSC administrator or architect needs to configure Compliant Data Sharing (CDS) declaratively — enabling ethical-wall enforcement on supported objects, setting the required organization-wide defaults, creating CDS-specific permission sets, adding the Financial Deal Participants related list to page layouts, and defining Participant Role records. It does NOT cover Apex participant record DML; use the `fsc-compliant-sharing-api` skill for that.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has Financial Services Cloud installed (the CDS scratch-org feature requires it, sfdx_dev 264 L7712-7719) and is on API v50.0 or later — ParticipantRole is available in API 50.0 and later (api_meta 264 L97091).
- Know which objects need ethical-wall enforcement. IndustriesSettings has CDS flags for Account, Opportunity, Interaction, Interaction Summary and custom objects (`enableCompliantDataSharingForCustomObjects`) — api_meta 264 L122543-122578 — and ParticipantRole `parentObject` also accepts FinancialDeal (API 52.0+), Budget, IndividualApplication, FundingAward, FundingOpportunity and Team (L97115-97153). UNVERIFIED (2026-10-20): the Summer '22 gate for custom objects.
- Identify the current OWD for each target object. CDS requires Private or Public Read-Only (UNVERIFIED (2026-10-20): Help-only prerequisite, no corpus line). If any target object is currently Public Read/Write, plan an OWD change before enabling CDS — updating organization-wide defaults runs a sharing recalculation (secguide 262 L2785-2786).
- Understand the team separation requirements (e.g., retail banking vs. wealth management). These map directly to Participant Roles, whose `defaultAccessLevel` is Edit, None or Read (api_meta 264 L97096-97103).
- Determine whether Financial Deal records are in scope. Deal Management is the IndustriesSettings flag `enableDealManagement` (api_meta 264 L122580-122582). UNVERIFIED (2026-10-20): that it gates CDS on Financial Deal.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which managers rely on the role hierarchy to see their team's records today? | CDS is designed to stop hierarchy inheritance (Gotcha 1; UNVERIFIED (2026-10-20): the bypass) | The explicit participant assignments to create before cut-over |
| What is the OWD of each target object, and when can it change? | The Private/Read-Only prerequisite (UNVERIFIED (2026-10-20)), and OWD changes run a recalculation (Gotcha 4) | A maintenance window and an order: OWD, recalculation, then CDS |
| Which sharing rules exist on the target objects? | Sharing rules grant access independently of CDS (Gotcha 3) | A keep/remove list per rule |
| Is Financial Deal in scope, and is `enableDealManagement` on? | Deal Management is its own IndustriesSettings flag (Gotcha 5) | The flag set before any Financial Deal participant roles |
| Which users hold the Use Compliant Data Sharing permission? | Participant groups contain only internal users with it (Core Concepts) | The permission assignment list per business line |
| What `defaultAccessLevel` does each participant role need? | Valid values are Edit, None and Read (Core Concepts) | A role catalogue that can be deployed as ParticipantRole metadata |
| Could CDS ever need to be turned off for an object? | Disabling is a cleanup project (Gotcha 2; UNVERIFIED (2026-10-20)) | A documented participant-cleanup path before go-live |

A proper configuration sets OWD, prunes sharing rules and deploys roles before the flags; "just doing it" flips the flags and leaves the old access paths open.

---

## Core Concepts

### What Compliant Data Sharing Does

UNVERIFIED (2026-10-20): this section's role-hierarchy claims — the corpus documents the CDS flags, ParticipantRole and participant groups but not the hierarchy bypass; the only hierarchy switch it names is `enableFinancialDealRoleHierarchy`, whether Financial Deal sharing follows the role hierarchy (api_meta 264 L122614-122616). CDS enforces ethical walls by disabling role-hierarchy-based sharing on its supported objects. In a standard Salesforce org, a manager automatically inherits visibility into every record their subordinates own. CDS switches off this inheritance for the objects it manages. After CDS is enabled, a record's owner's manager does NOT automatically see that record. Access must be granted explicitly by assigning the user a Participant Role on the specific record.

This is a fundamentally different access model from standard OWD + role hierarchy + sharing rules. CDS runs as a parallel mechanism: OWDs still set the floor (Private or Public Read-Only), and for CDS-enabled objects the role hierarchy is bypassed while sharing rules keep granting access alongside CDS (Gotcha 3).

### Supported Objects and IndustriesSettings Flags

CDS is enabled per-object via the `IndustriesSettings` metadata type. Each supported object has its own flag:

| Object | IndustriesSettings Field |
|---|---|
| Account | `enableCompliantDataSharingForAccount` |
| Opportunity | `enableCompliantDataSharingForOpportunity` |
| Interaction | `enableCompliantDataSharingForInteraction` |
| Interaction Summary | `enableCompliantDataSharingForInteractionSummary` |
| Custom objects | `enableCompliantDataSharingForCustomObjects` |

These five are the CDS flags in the IndustriesSettings field table (api_meta 264 L122543-122578), each defaulting to false. The table has no `enableCompliantDataSharingForFinancialDeal`; Financial Deal uses `enableDealManagement` (L122580-122582) and ParticipantRole `parentObject` FinancialDeal (L97142-97143).

UNVERIFIED (2026-10-20): that enabling CDS is irreversible in Setup, needs Salesforce Support to deactivate, and needs all participant records deleted first (Gotcha 2) — no corpus line.

### Participant Roles and the Access Grant Model

A Participant Role is `ParticipantRole` metadata (`.participantRole` files in `participantRoles`, API 50.0+, api_meta 264 L97087-97091) that defines:
1. `masterLabel` — the name (e.g., "Relationship Manager", "Deal Lead"), Required (L97110-97113)
2. `defaultAccessLevel` — Edit, None or Read, Required (L97096-97103)
3. `parentObject` — the object it applies to, Required (L97115-97118); plus `isActive` (L97105-97108)

When an admin or automation assigns a user to a record via a Participant Role, the CDS engine writes a share row for that user on that record. A `CompliantDataSharing` RowCause exists on share objects (object_reference 264 L56562); AccountShare's RowCause list does not name it (L17475-17504), and share rows with a non-Manual RowCause are read-only (L17340-17342). UNVERIFIED (2026-10-20): the RowCause on AccountShare, the rewrite on recalculation, and the `AccountParticipant` object name. To revoke access, delete the participant assignment, not the share row.

### Permissions Required for CDS Administration

The corpus names one CDS permission: **Use Compliant Data Sharing** — a Participant group holds only internal users who have it (object_reference 264 L155375-155379). UNVERIFIED (2026-10-20): a separate admin permission named "Configure CDS" and both permission-set names below.

- **CDS Manager permission** — grants the "Configure CDS" system permission. Admins with this permission can enable CDS in IndustriesSettings, create and manage Participant Role records, and configure Financial Deal Participants layouts.
- **CDS User permission** — grants the Use Compliant Data Sharing permission. End users with it can be assigned as participants on records; a user without it cannot be added as a participant even by an admin.

Both permissions must be assigned before testing CDS access grants. A common setup mistake is granting the admin permission and forgetting Use Compliant Data Sharing for the business users who need to be participants.

### Deal Management Prerequisite for Financial Deal CDS

If Financial Deal records are in scope, turn on Deal Management first — IndustriesSettings `enableDealManagement` (api_meta 264 L122580-122582) — and decide `enableFinancialDealRoleHierarchy`, which makes Financial Deal sharing follow the role hierarchy when true (L122614-122616). UNVERIFIED (2026-10-20): the Setup path and that the Financial Deal Participants related list needs Deal Management.

---

## Common Patterns

### Pattern 1: OWD + CDS Enablement Sequence

**When to use:** Initial CDS rollout for an org that has never had CDS enabled. Most of the time the target objects are currently Public Read/Write or not Private, requiring an OWD change.

**How it works:**

1. Identify current OWDs via Setup > Sharing Settings. Note every object that needs to change.
2. Change OWDs for target objects to Private or Public Read-Only (UNVERIFIED (2026-10-20): the prerequisite). Do this during a maintenance window — OWD changes trigger sharing recalculations in production.
3. Enable CDS per object by deploying (or editing via Setup) the `IndustriesSettings` metadata with the relevant flags set to `true`.
4. Verify via Setup > Sharing Settings that the object shows "Compliant Data Sharing" as the active sharing mechanism (UNVERIFIED (2026-10-20): this label).
5. Add the Financial Deal Participants related list to relevant page layouts if Financial Deal CDS is enabled.
6. Create Participant Role records to match the org's access model.
7. Assign the CDS admin permission set and Use Compliant Data Sharing to the appropriate users.

**Why not the alternative:** UNVERIFIED (2026-10-20): that enabling CDS before setting OWDs to Private/Read-Only is accepted but produces no share rows — no corpus line; the order still avoids a second recalculation.

### Pattern 2: Defining Participant Roles for Ethical Wall Isolation

**When to use:** Two or more business lines (e.g., retail banking and wealth management) must be prevented from seeing each other's client accounts even when the same org hierarchy is used.

**How it works:**

1. Create a Participant Role for each distinct access level per business line (e.g., "Retail RM - Edit", "Wealth Advisor - Edit", "Deal Lead - Read").
2. The `defaultAccessLevel` on the Participant Role — Edit, None or Read (api_meta 264 L97099-97103) — sets the default access granted. Name roles descriptively so the business can audit participant lists without needing admin access.
3. Assign users to records using only the roles appropriate for their business line. Do not create cross-line Participant Role assignments unless cross-line access is intentional.
4. Verify that managers in Retail Banking cannot see Wealth Management accounts by testing with a user in each hierarchy branch.

**Why not the alternative:** Using a single generic Participant Role for all business lines does enforce the ethical wall at the role-hierarchy level (UNVERIFIED (2026-10-20)) but provides no audit trail of which business line was granted access to which record. Named roles enable meaningful compliance reporting.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Target object OWD is Public Read/Write | Change OWD to Private first, then enable CDS | UNVERIFIED (2026-10-20): no share rows under Public Read/Write |
| Financial Deal CDS needed | Set `enableDealManagement` before Financial Deal participant roles | Deal Management is its own flag (api_meta 264 L122580) |
| Manager must see subordinate records | Create explicit Participant Role assignments for the manager | Role-hierarchy inheritance is disabled by CDS (UNVERIFIED (2026-10-20)); there is no automatic path |
| Need to disable CDS | Delete all Participant Role assignments for the object, then contact Salesforce Support | UNVERIFIED (2026-10-20): the deactivation block |
| User cannot be added as participant | Check the Use Compliant Data Sharing permission | Participant groups hold only users with it (object_reference 264 L155375-155379) |
| Custom object ethical walls | Enable `enableCompliantDataSharingForCustomObjects` (api_meta 264 L122557) | UNVERIFIED (2026-10-20): a second per-object flag and the Summer '22 gate |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Verify prerequisites — confirm FSC is installed, API version is 50.0+, `enableDealManagement` is true if Financial Deal is in scope, and the org admin has the CDS admin permission set assigned.
2. Set OWDs — for every CDS target object, confirm OWD is Private or Public Read-Only in Setup > Sharing Settings (UNVERIFIED (2026-10-20): the prerequisite). If not, schedule an OWD change and sharing recalculation during a maintenance window.
3. Enable CDS per object — in Setup > Industries Settings (or by deploying `IndustriesSettings` metadata), set the `enableCompliantDataSharingForX` flag for each required object to `true`; run `scripts/check_compliant_data_sharing_setup.py --manifest-dir` on the retrieved metadata.
4. Configure layouts and roles — add the Financial Deal Participants related list to Account and Financial Deal page layouts where applicable; create Participant Role records representing each access tier in the org (e.g., "Relationship Manager - Edit", "Co-Advisor - Read").
5. Assign permissions and validate — assign the admin permission set to admins and Use Compliant Data Sharing to all business users who will be participants; test by assigning a Participant Role on a real record and verifying access is granted without role-hierarchy inheritance.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] OWD for each CDS-enabled object is Private or Public Read-Only (UNVERIFIED (2026-10-20): Help-only prerequisite)
- [ ] `enableDealManagement` true (if Financial Deal is in scope)
- [ ] `enableCompliantDataSharingForX` IndustriesSettings flag set to `true` for every target object
- [ ] Financial Deal Participants related list added to relevant page layouts
- [ ] CDS admin permission set assigned to all CDS administrators
- [ ] Use Compliant Data Sharing assigned to every user who will be a participant on any record
- [ ] At least one Participant Role record created per distinct access tier
- [ ] Managers verified to NOT automatically see subordinate records under CDS
- [ ] Access grants verified via explicit Participant Role assignments only
- [ ] Disabling CDS path documented if required: all participant assignments deleted before support ticket (UNVERIFIED (2026-10-20): the deactivation sequence)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Managers do not inherit subordinate records under CDS** — UNVERIFIED (2026-10-20): the hierarchy bypass has no corpus line (see Core Concepts). This is intentional and is the entire purpose of CDS. However, admins migrating from standard sharing frequently open a support ticket thinking CDS is broken. After enabling CDS, a manager must be explicitly assigned as a participant on every record they need to access. There is no automatic inheritance path, and no sharing rule can restore it for CDS-enabled objects.

2. **Disabling CDS requires deleting all participant role assignments first** — UNVERIFIED (2026-10-20): the deactivation block and the `AccountParticipant`/`OpportunityParticipant` object names have no corpus line. The platform blocks deactivation of CDS for any object that still has participant records. Attempting to disable without clearing participants results in an error. The cleanup must happen via data tools or Apex before a Salesforce Support ticket for deactivation can be processed.

3. **CDS and standard sharing rules are independent mechanisms** — Enabling a sharing rule on a CDS-enabled object does not interact with the CDS engine. Standard sharing rules continue to grant access with RowCause `Rule` (object_reference 264 L17480), while CDS manages its own rows (UNVERIFIED (2026-10-20): the `CompliantDataSharing` RowCause on AccountShare). This means a record can be accessible via both a sharing rule AND a CDS participant role simultaneously, which can create unintended cross-team visibility if sharing rules are not audited when CDS is introduced.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CDS enablement checklist | Step-by-step admin task list for enabling CDS on a target object |
| Participant Role design | Named role records with access levels mapped to business-line access model |
| Permission set assignment list | Admin and Use Compliant Data Sharing assignments per user group |
| `check_compliant_data_sharing_setup.py` report | Static analysis of IndustriesSettings metadata and sharing settings for CDS configuration issues |

---

## Related Skills

- apex/fsc-compliant-sharing-api — Use for programmatic participant record DML after CDS is enabled declaratively via this skill
- architect/fsc-architecture-patterns — Use for broader FSC sharing architecture decisions including multi-object CDS rollout sequencing
