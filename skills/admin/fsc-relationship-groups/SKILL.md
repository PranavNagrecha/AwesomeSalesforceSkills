---
name: fsc-relationship-groups
description: "Use this skill when creating, configuring, or troubleshooting FSC Relationship Groups — including Household, Professional Group, and Trust group types; member role assignment via AccountContactRelation FSC fields; Primary Group designation; and group-level wealth aggregation rollups. NOT for standard account relationships, Contact-Account relationships outside FSC, NPSP household configuration, or Financial Account role setup (use admin/financial-account-setup)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "FSC relationship group wealth rollup total is wrong or shows incomplete assets for a household member"
  - "How do I add a person to a Household group versus a Professional Group or Trust in Financial Services Cloud"
  - "FinServ__PrimaryGroup__c field not set on AccountContactRelation and rollup data is missing"
  - "Client belongs to two FSC households but net worth only aggregates from one — why is the second group excluded"
  - "How to configure Trust record type as a relationship group in FSC for estate planning clients"
  - "FSC group member added but financial accounts are not rolling up to the group"
tags:
  - financial-services-cloud
  - fsc
  - relationship-groups
  - household
  - professional-group
  - trust
  - account-contact-relation
  - wealth-aggregation
  - primary-group
  - person-accounts
inputs:
  - Confirmation of FSC packaging model (managed-package with FinServ__ namespace vs Core FSC without namespace, GA since Winter '23)
  - Target group type required (Household, Professional Group, or Trust)
  - List of Person Account members and their intended roles in the group
  - Whether each member's financial accounts should roll up to this group
  - Whether this is a primary group for any given member (each member can have only one primary group)
outputs:
  - Correctly typed Relationship Group Account record (Household, Professional Group, or Trust record type)
  - AccountContactRelation records with FinServ__PrimaryGroup__c, FinServ__Primary__c, and FinServ__IncludeInGroup__c set correctly for every member
  - Validated wealth aggregation rollup fields on the group Account record
  - Decision guidance on Primary Group assignment and multi-group membership scenarios
  - Review checklist confirming group setup and rollup behavior in sandbox
dependencies:
  - admin/household-model-configuration
  - admin/financial-account-setup
  - admin/person-accounts
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSC Relationship Groups

Use this skill when configuring or troubleshooting FSC Relationship Groups — the mechanism by which Financial Services Cloud organizes Person Account clients into financial units (Households, Professional Groups, or Trusts) and aggregates wealth data across members. This skill covers the three group record types, member role fields on AccountContactRelation, the Primary Group constraint that governs rollup eligibility, and the silent failure modes that produce incomplete wealth aggregation.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm FSC packaging model.** Managed-package FSC orgs use the `FinServ__` namespace (e.g., `FinServ__PrimaryGroup__c`, `FinServ__IncludeInGroup__c`). Core FSC orgs (GA since Winter '23) expose these as standard fields without the namespace. Every field reference, SOQL query, Flow, and Apex class must use the correct form or fail silently.
- **Confirm which group type is needed.** FSC offers three Account record types for Relationship Groups: **Household** (family financial unit), **Professional Group** (business partners, partnership entities), and **Trust** (estate planning, revocable/irrevocable trusts). The correct record type determines page layout, available FSC components, and how the group is surfaced in FSC advisor workflows.
- **Confirm one-primary-group-per-member constraint.** Each Person Account can belong to multiple Relationship Groups, but only ONE of those groups may have `FinServ__PrimaryGroup__c = true` on the member's ACR. Rollup totals (total assets, net worth) aggregate exclusively from members whose `FinServ__PrimaryGroup__c = true` on that group's ACR records. A member added to a second group without designating it as primary silently contributes nothing to that second group's rollup.
- **Confirm Person Accounts are enabled.** Relationship Group members must be Person Accounts. The group itself is a standard Account record. This is the same prerequisite as the household model.

---

## Core Concepts

### Relationship Groups Are Standard Account Records with FSC Record Types

A Relationship Group is not a custom object. It is a standard Salesforce `Account` record assigned one of three FSC record types:

| Record Type | Use Case | Typical Members |
|---|---|---|
| Household | Family or cohabiting financial unit | Spouses, domestic partners, dependents |
| Professional Group | Business partnership or professional entity | Business partners, LLC members, shareholders |
| Trust | Estate planning legal entity | Trustees, beneficiaries, grantors |

Each record type has its own FSC page layout, FSC Lightning components, and rollup field behavior. The record type must be active on the Account object and assigned to the correct profile and page layout before groups of that type can be created. Assigning the wrong record type (e.g., using a Household record type for a trust client) causes the wrong FSC components to surface and may break estate-planning-specific data model assumptions.

### Membership Is Managed via AccountContactRelation with Three FSC Fields

Person Account clients are added to a Relationship Group via the `AccountContactRelation` (ACR) junction object. FSC adds three custom fields to ACR that control membership semantics and rollup inclusion:

| Field | API Name (managed) | Purpose |
|---|---|---|
| Primary Group | `FinServ__PrimaryGroup__c` | Boolean. Marks this group as the member's **primary** group. Only one ACR per Person Account may have this set to `true`. Rollups on the group aggregate assets exclusively from members with this set to `true`. |
| Primary Member | `FinServ__Primary__c` | Boolean. Designates the **primary contact** within this group — used for display, salutation, and advisor assignment defaults. Only one member per group should have this set to `true`. |
| Include in Group | `FinServ__IncludeInGroup__c` | Boolean. Controls whether this member's financial accounts and related records are included in group-level rollups. Defaults to `false` in many programmatic creation paths. |

All three fields are required for correct group behavior. Missing or incorrect values on any one field produces a subtly broken group that appears correctly configured but fails to aggregate wealth data.

### Primary Group Constraint and Its Effect on Wealth Aggregation

The most consequential constraint in FSC Relationship Groups is the **one-primary-group-per-member** rule. When a Person Account belongs to multiple groups:

- Group A has `FinServ__PrimaryGroup__c = true` on that member's ACR — the member's assets are included in Group A's rollup totals.
- Group B has `FinServ__PrimaryGroup__c = false` on that member's ACR — the member's assets are **not** included in Group B's rollup totals, even if `FinServ__IncludeInGroup__c = true`.

This is the source of the most common wealth aggregation complaint: a client is visibly listed as a member of two groups, but the second group shows no financial data for them. The platform does not throw an error — it simply does not aggregate from non-primary members. Practitioners must decide deliberately which group should be primary for each member, especially in joint account or trust beneficiary scenarios.

### Group-Level Rollups: What Aggregates and What Does Not

FSC group-level rollup fields (e.g., `FinServ__TotalAssets__c`, `FinServ__TotalLiabilities__c`, AUM) aggregate financial account data across all members of the group where `FinServ__PrimaryGroup__c = true` AND `FinServ__IncludeInGroup__c = true`. Rollups run via:

1. **Real-time triggers** — fire synchronously when a financial account is created, updated, or its owner changes.
2. **Scheduled batch job** — `FinServ.RollupBatchJob` (managed-package) recalculates all group rollups in bulk; essential after data migrations or bulk updates.

The `Rollups__c` picklist on the Account object controls which object types are included in rollup calculations. Missing picklist values for an object type cause silent exclusion of those records from rollup totals — no error is generated.

---

## Common Patterns

### Pattern: Create a New Household Relationship Group

**When to use:** A new FSC client family needs a Household group to aggregate financial accounts and wealth data across spouses or family members.

**How it works:**
1. Create the Household Account record using the `Household` record type. Populate `Name`, billing address, and any required FSC fields.
2. Identify the Person Account members (each is an Account with `IsPersonAccount = true`). Retrieve each member's `PersonContactId` — this is the Contact Id required by ACR, not the Account Id.
3. For each member, create an ACR record:
   - `AccountId` = Household Account Id
   - `ContactId` = Person Account's `PersonContactId`
   - `FinServ__PrimaryGroup__c` = `true` if this household is the member's primary group (typically `true` for a dedicated family household)
   - `FinServ__Primary__c` = `true` for the designated primary household member (only one per group)
   - `FinServ__IncludeInGroup__c` = `true` to include the member's financial accounts in rollups
4. Verify the Household Account rollup fields update after the trigger fires (check `FinServ__TotalAssets__c`, `FinServ__TotalLiabilities__c`, or equivalent Core FSC fields).

**Why not the alternative:** Using a standard Account hierarchy (`ParentId`) or a custom object to model a household bypasses the FSC rollup engine. The ACR junction with FSC fields is what rollup triggers and FSC Lightning components listen to.

### Pattern: Add a Client to a Trust Group Without Disrupting Their Primary Household

**When to use:** An existing FSC client is also a beneficiary or trustee of a Trust group. Their primary household should remain their primary group; the Trust is a secondary group for relationship and document tracking.

**How it works:**
1. Create (or identify) the Trust Account record with the `Trust` record type.
2. Create an ACR record linking the client Person Account to the Trust Account:
   - `FinServ__PrimaryGroup__c` = `false` (the client's household remains primary)
   - `FinServ__Primary__c` = `true` if this client is the primary contact for the trust (e.g., the trustee); `false` otherwise
   - `FinServ__IncludeInGroup__c` = `true` if the trust should display the client's financial accounts in its relationship view (note: assets will NOT roll up to trust totals because `FinServ__PrimaryGroup__c = false`)
3. Validate: confirm the client's household rollup totals are unchanged. Confirm the Trust group membership is visible in the client's household and person account relationship panels.
4. If trust-level asset aggregation is required (e.g., trust-owned accounts), link trust-owned Financial Account records directly to the Trust Account rather than relying on member rollups.

**Why not the alternative:** Setting `FinServ__PrimaryGroup__c = true` on the Trust ACR would transfer the client's primary group designation to the Trust and break household-level wealth aggregation for that client. This is the most common misconfiguration in multi-group scenarios.

### Pattern: Professional Group for Business Partners

**When to use:** Two or more clients co-own a business or partnership and need their business-related financial accounts grouped separately from their personal households.

**How it works:**
1. Create a Professional Group Account record with the `Professional Group` record type.
2. For each partner Person Account, create an ACR with:
   - `FinServ__PrimaryGroup__c` = `false` (each partner's personal household remains their primary group)
   - `FinServ__Primary__c` = `true` for the managing partner
   - `FinServ__IncludeInGroup__c` = `true` if partners' accounts should appear in the group's relationship view
3. Link business Financial Account records directly to the Professional Group Account using `FinancialAccount.PrimaryOwner` or the appropriate FSC relationship, so business assets aggregate at the group level independently of individual member rollup rules.

**Why not the alternative:** Attempting to merge business financial accounts into a personal Household group conflates personal and business wealth data, complicating regulatory reporting and advisor views.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New family client needs wealth aggregation | Create Household record type group; set `FinServ__PrimaryGroup__c = true` and `FinServ__IncludeInGroup__c = true` for all members | Standard FSC household pattern; enables all rollup and FSC component features |
| Client is a trust beneficiary, trust is secondary | Create Trust group; set `FinServ__PrimaryGroup__c = false` on trust ACR; household ACR remains primary | Preserves household wealth aggregation; trust is a relationship container, not a rollup contributor |
| Client belongs to two households (e.g., divorce, remarriage) | Set `FinServ__PrimaryGroup__c = true` on only one household ACR; use `false` for the secondary household | Only one primary group per member; secondary household will not aggregate assets but can track relationships |
| Business partners need group financial view | Use Professional Group record type; link business accounts directly to the group Account | Professional Group is designed for non-family financial units; keeps business and personal wealth separate |
| Estate planning clients with trustee and beneficiary roles | Use Trust record type; assign member roles explicitly via `FinServ__Primary__c` and ACR Roles field | Trust record type activates estate-planning FSC page layouts and components |
| Member added to group but rollup totals unchanged | Check `FinServ__PrimaryGroup__c` and `FinServ__IncludeInGroup__c` on the member's ACR; also verify `Rollups__c` picklist includes relevant object types | These two fields are the most common cause of silent rollup exclusion |
| Bulk data migration into FSC groups | Run `FinServ.RollupBatchJob` after load completes; do not rely on real-time triggers for bulk operations | Trigger-based rollups can be throttled or skipped during bulk DML; batch job is designed for high-volume recalculation |

---

## Recommended Workflow

Step-by-step instructions for configuring FSC Relationship Groups:

1. **Verify prerequisites.** Confirm FSC packaging model (managed-package vs Core FSC), Person Accounts enabled, and all three required Account record types (Household, Professional Group, Trust) active on the Account object with the correct page layouts and profiles.
2. **Determine the correct group type.** Based on the client scenario, select Household, Professional Group, or Trust. Confirm whether the group needs to serve as a primary group for any member (required for wealth aggregation rollups).
3. **Create the Relationship Group Account record.** Use the correct record type. Populate name, address, and any required FSC fields. Do not use a custom object or standard Account hierarchy (`ParentId`) as a substitute.
4. **Create ACR membership records for each member.** For each Person Account member, retrieve `PersonContactId` and create an ACR record. Set `FinServ__PrimaryGroup__c`, `FinServ__Primary__c`, and `FinServ__IncludeInGroup__c` deliberately based on the member's role. Ensure only one ACR per member has `FinServ__PrimaryGroup__c = true` across all their groups.
5. **Validate rollup fields in sandbox.** After ACR creation, check the group Account's rollup fields (`FinServ__TotalAssets__c`, `FinServ__TotalLiabilities__c`, etc.). If rollups do not update, audit ACR fields and the `Rollups__c` picklist for the relevant object types.
6. **Run batch rollup job if needed.** After bulk member or financial account creation, execute `FinServ.RollupBatchJob` (managed-package) or the equivalent Core FSC batch. Confirm group rollup totals match expected values.
7. **Review checklist and document.** Complete the review checklist. Record group types created, primary group designations, and any edge cases (multi-group members, trust beneficiary roles) in the work template for handoff.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] FSC packaging model confirmed; all field references use the correct namespace form (FinServ__ or Core FSC standard fields)
- [ ] Correct Account record type used for each group (Household, Professional Group, or Trust)
- [ ] All group members are Person Accounts; each linked via ACR with a valid `PersonContactId` (not Account Id)
- [ ] `FinServ__PrimaryGroup__c`, `FinServ__Primary__c`, and `FinServ__IncludeInGroup__c` explicitly set on every ACR — no field left at its default
- [ ] No Person Account has `FinServ__PrimaryGroup__c = true` on more than one ACR across all their groups
- [ ] No group has more than one ACR with `FinServ__Primary__c = true`
- [ ] `Rollups__c` picklist on Account object includes values for all required object types (FinancialAccount at minimum; Opportunity, Case, InsurancePolicy as needed)
- [ ] Rollup fields validated in sandbox after group and ACR creation
- [ ] Batch rollup job executed and verified if bulk data load was performed
- [ ] Multi-group members documented with deliberate primary group designation rationale

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Adding a member to a group does not automatically make it their primary group** — Creating an ACR record without explicitly setting `FinServ__PrimaryGroup__c = true` leaves the field `false`. The member appears in the group relationship panel but contributes zero financial data to group-level rollups. No error or warning is generated. This is the most common cause of "member is in the group but rollup shows zero assets."
2. **One primary group per member is a hard constraint — not enforced with a validation rule** — Salesforce does not enforce the one-primary-group rule with a platform validation. If a data migration or automation accidentally sets `FinServ__PrimaryGroup__c = true` on two ACR records for the same Person Account (different groups), the platform accepts both records. Rollup behavior becomes indeterminate — assets may double-count across groups or aggregate inconsistently. This must be caught via a pre-migration data audit or a custom validation rule.
3. **`FinServ__IncludeInGroup__c` defaults to false in programmatic ACR creation** — When ACR records are inserted via Apex, Data Loader, or Flow without explicitly setting `FinServ__IncludeInGroup__c = true`, the field defaults to `false`. The member is related to the group but their financial accounts are excluded from all rollup calculations. Always set this field explicitly — never rely on the default.
4. **Trust and Professional Group record types require separate activation** — In some FSC orgs, only the Household record type is active on Account by default. Professional Group and Trust record types may need to be manually activated and assigned to page layouts and profiles before they can be used. Attempting to create a group with an inactive record type fails with a generic record type error that does not explicitly name the missing activation step.
5. **Rollup totals do not update retroactively when Primary Group designation changes** — If a member's `FinServ__PrimaryGroup__c` is toggled (e.g., switching primary group from Household A to Household B), the rollup fields on both groups do not recalculate until the next trigger event (e.g., a related financial account is saved) or the next batch rollup job run. Between the field change and the next recalculation, both groups may show stale wealth totals.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Relationship Group Account records | Standard Account records with the correct FSC record type (Household, Professional Group, or Trust), populated FSC fields, and FSC page layout |
| ACR membership records | AccountContactRelation records per group member with FinServ__PrimaryGroup__c, FinServ__Primary__c, and FinServ__IncludeInGroup__c explicitly set |
| Primary Group assignment map | Documentation of which group is designated as primary for each multi-group member |
| Rollup validation results | Confirmed group-level wealth rollup field values in sandbox after group and ACR creation |
| Work template | Completed fsc-relationship-groups-template.md recording group types, member roles, and configuration decisions |

---

## Related Skills

- `admin/household-model-configuration` — deeper coverage of the FSC household data model, Rollups__c picklist configuration, and batch rollup scheduling; this skill focuses on group types and member roles
- `admin/financial-account-setup` — configure Financial Account records and roles that roll up to groups; this skill handles the group container, that skill handles what goes inside it
- `admin/person-accounts` — enable and configure Person Accounts, which are required as group members in FSC
- `admin/fsc-data-model` — broader FSC data model overview including the full object graph and FSC component architecture
