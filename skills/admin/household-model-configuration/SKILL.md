---
name: household-model-configuration
description: "Use this skill when configuring the Financial Services Cloud (FSC) household data model — including Household record type setup, Primary Group assignment, ACR-based membership, rollup field inclusion, and batch rollup scheduling. NOT for NPSP household account configuration (use admin/npsp-household-accounts), non-FSC Account hierarchies, or standard Contact-Account relationships outside of FSC."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "FSC household rollup totals not updating after adding a financial account to a household member"
  - "How do I configure Primary Group assignment and household membership in Financial Services Cloud"
  - "AccountContactRelation setup with FinServ__PrimaryGroup__c and FinServ__IncludeInGroup__c not working"
  - "FSC household model versus NPSP household model — which fields and objects to use"
  - "Rollups picklist values missing for Cases or Insurance Policies in existing FSC org"
tags:
  - financial-services-cloud
  - fsc
  - household
  - account-contact-relation
  - rollups
  - person-accounts
  - primary-group
inputs:
  - Confirmation of whether the org is managed-package FSC (FinServ__ namespace) or Core FSC (no namespace, GA since Winter '23)
  - List of object types that need household rollups (Opportunities, Cases, Insurance Policies, Financial Accounts, etc.)
  - Whether the org was provisioned before or after Winter '23 (affects default Rollups__c picklist values)
  - Desired primary member and primary group assignment rules for existing household members
outputs:
  - Configured Household record type on the Account object with correct FSC fields
  - AccountContactRelation (ACR) records with FinServ__PrimaryGroup__c and FinServ__Primary__c correctly set
  - Rollups__c picklist values verified or added for all required object types
  - Scheduled batch job configuration for household rollups
  - Validation checklist confirming rollup behavior in sandbox
dependencies:
  - admin/financial-account-setup
  - admin/person-accounts
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Household Model Configuration

Use this skill when configuring or troubleshooting the FSC household data model — covering the Household Account record type, Person Account membership via AccountContactRelation, Primary Group designation, rollup field inclusion, and batch rollup scheduling. This skill is the canonical reference for understanding how FSC households differ architecturally from NPSP households and why mixing the two models causes silent data loss.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm FSC packaging model.** Managed-package FSC orgs use the `FinServ__` namespace (e.g., `FinServ__PrimaryGroup__c`). Core FSC orgs (GA since Winter '23) expose these as standard fields without the namespace. Every field reference, SOQL query, and Flow must use the correct form or it will fail silently.
- **Confirm org provisioning date.** Orgs provisioned before certain FSC releases do NOT automatically include all `Rollups__c` picklist values. Specifically, existing orgs must manually add values for Cases, Insurance Policies, and Opportunities. New orgs include a default set, but it may still be incomplete for custom object rollups.
- **Confirm NPSP is not installed.** FSC and NPSP use incompatible household models. If NPSP is present, the FSC rollup engine and ACR-based membership are not reliable. These two platforms should never coexist in a production org without explicit Salesforce guidance.
- **Confirm Person Accounts are enabled.** FSC households require household members to be Person Accounts. Individual (non-household) clients are Person Account records; the household itself is a standard Account with the Household record type.

---

## Core Concepts

### The Household Is a Standard Account Record

In FSC, a household is not a custom object. It is a standard `Account` record assigned the **Household** record type. This record type must be available on the Account object and associated with the correct FSC page layout and compact layout. The Household Account represents the financial unit — it holds the aggregated rollup data (total assets, liabilities, AUM, etc.) across all member Person Accounts.

Contrast this with NPSP: NPSP also places households on the Account object, but uses a direct `Contact.AccountId` lookup for membership and its own trigger-based rollup engine (NPSP Rollups). These two models are **architecturally incompatible**. FSC financial rollups (AUM, total assets, financial goals) are wired to FSC's ACR-based rollup engine and will not populate if a non-FSC membership model is active.

### Membership Is Managed via AccountContactRelation (ACR) with FSC Custom Fields

Household members — Person Account records — are linked to the Household Account via the `AccountContactRelation` (ACR) junction object. FSC adds three critical custom fields to ACR:

| Field | API Name | Purpose |
|---|---|---|
| Primary Group | `FinServ__PrimaryGroup__c` | Boolean. Marks which Household is this member's **primary** group. A single Person Account can belong to multiple households (e.g., a joint account holder), but only one can be their primary group. |
| Primary Member | `FinServ__Primary__c` | Boolean. Designates one member of the household as the primary contact for that household — used for display, record ownership, and some rollup defaults. |
| Include in Group | `FinServ__IncludeInGroup__c` | Boolean. Controls whether this member's financial accounts and related records are included in the household-level rollups. Setting this to false excludes the member's assets from the household's aggregated view. |

All three fields must be correctly set. A common mistake is creating ACR records without setting `FinServ__IncludeInGroup__c = true`, which causes financial accounts to not appear in household rollups even when the member relationship exists.

### Rollups: Real-Time Triggers and Scheduled Batch Jobs

FSC household rollups run through two mechanisms:

1. **Real-time rollups via triggers.** When a financial account is created, updated, or its role changes, FSC triggers recalculate the household balance synchronously. This covers the common case where a single advisor adds a new financial account to a household member.
2. **Scheduled batch rollup jobs.** For large data volumes, recalculations after bulk operations (data loads, mass updates), or periodic consistency checks, FSC provides a scheduled batch job (`FinServ.RollupBatchJob` in managed-package orgs). This should be scheduled to run nightly or as required by business SLA.

The `Rollups__c` picklist on the `Account` object controls **which object types** are included in household-level rollups. Each picklist value represents an object type (e.g., `Opportunity`, `Case`, `FinancialAccount`, `InsurancePolicy`). If the picklist value for an object type is missing, rollups for that type will not run — there is no error; data simply does not aggregate.

**Critical for existing orgs:** Orgs that existed before certain FSC release milestones may be missing `Rollups__c` picklist values for Cases, Insurance Policies, and Opportunities. These must be added manually via Setup > Object Manager > Account > Fields & Relationships > Rollups__c > Manage Values.

---

## Common Patterns

### Pattern: Set Up a Net-New Household

**When to use:** A new FSC org or a new client family needs a household structure created from scratch with multiple Person Account members.

**How it works:**
1. Create the Household Account record with the `Household` record type. Populate `Name`, `BillingAddress`, and any custom FSC fields required by the org's data model.
2. Create (or identify) the Person Account records for each household member. Each is a standard Account record with the `PersonAccount` record type and `IsPersonAccount = true`.
3. Create an `AccountContactRelation` record for each member, setting:
   - `AccountId` = the Household Account Id
   - `ContactId` = the Person Account's associated Contact Id (Person Account auto-creates a Contact; use `Account.PersonContactId`)
   - `FinServ__PrimaryGroup__c` = `true` for the member's primary household (typically `true` if this is their only or primary household)
   - `FinServ__Primary__c` = `true` for the designated primary household member; `false` for all others
   - `FinServ__IncludeInGroup__c` = `true` to include this member's assets in household rollups
4. Verify the Household Account's rollup fields are populated after the trigger fires (check `FinServ__TotalAssets__c`, `FinServ__TotalLiabilities__c`, or equivalent Core FSC fields).

**Why not the alternative:** Creating the household as a custom object or using the standard Account hierarchy (`ParentId`) bypasses the FSC rollup engine entirely. The ACR junction with FSC fields is what the rollup triggers listen to.

### Pattern: Add an Existing Client to a Second Household (Joint Account Scenario)

**When to use:** A Person Account (individual client) already has a primary household but is also a joint account holder in another household — common in wealth management for married couples with joint investment accounts.

**How it works:**
1. Create a second `AccountContactRelation` record linking the individual Person Account to the second Household Account.
2. Set `FinServ__PrimaryGroup__c = false` on the new ACR (the original household remains primary).
3. Set `FinServ__IncludeInGroup__c = true` only for the financial accounts that should roll up to the second household. If the individual's personal financial accounts should NOT appear in the joint household, set them to use the primary household only.
4. Validate: check the second household's rollup totals after the trigger fires.

**Why not the alternative:** Changing the existing `FinServ__PrimaryGroup__c` on the original ACR record to accommodate the new household would break the primary group designation and corrupt the individual's primary household rollups.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New FSC org, greenfield setup | Create Households as Account (Household record type), members as Person Accounts, link via ACR with all three FSC fields set | Standard FSC pattern; enables rollup engine and all FSC financial components |
| Org has NPSP installed | Do not mix FSC household model with NPSP model; engage Salesforce for migration path | The two rollup engines conflict; FSC financial aggregations will fail silently if NPSP household model is active |
| Rollup fields not populating for a member | Check `FinServ__IncludeInGroup__c` on the member's ACR record; also check `Rollups__c` picklist has the relevant object type value | Missing `IncludeInGroup__c = true` or missing picklist value are the two most common causes |
| Existing org missing rollup data for Cases or Insurance Policies | Verify `Rollups__c` picklist values exist for those object types; add manually if missing | Pre-release orgs may not have all values seeded by default |
| Large-scale data migration into FSC households | Use batch rollup job post-load rather than relying on trigger recalculation | Bulk data loads can exhaust trigger-based rollup capacity; batch job is designed for high-volume recalculation |
| Member should appear in household but assets excluded | Set `FinServ__IncludeInGroup__c = false` on that member's ACR; keep the ACR itself active | Supports scenarios like a minor child who is a household member but whose custodial account is tracked separately |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner configuring the FSC household model:

1. **Verify org prerequisites.** Confirm FSC packaging model (managed-package vs Core FSC), Person Accounts enabled, Household record type active on Account, and that NPSP is not installed. Note all field API names using the correct namespace form.
2. **Audit `Rollups__c` picklist values.** Navigate to Setup > Object Manager > Account > Fields & Relationships > Rollups__c > Values. Confirm values exist for every object type that should roll up to households (at minimum: FinancialAccount, Opportunity, Case, InsurancePolicy). Add any missing values manually.
3. **Create or verify Household Account records.** Each household must be an Account with the Household record type. Confirm required fields are populated and page layout includes FSC rollup display fields.
4. **Create or verify ACR membership records.** For each household member (Person Account), ensure an ACR record exists with `FinServ__PrimaryGroup__c`, `FinServ__Primary__c`, and `FinServ__IncludeInGroup__c` set correctly. Only one member per household should have `FinServ__Primary__c = true`. Only one household per individual should have `FinServ__PrimaryGroup__c = true`.
5. **Validate real-time rollups in sandbox.** Create a test financial account for a member and confirm the household's rollup fields update. Check `FinServ__TotalAssets__c` (or Core FSC equivalent) on the Household Account record.
6. **Configure and test the batch rollup job.** In a sandbox, run `FinServ.RollupBatchJob` (managed-package) or the equivalent Core FSC batch via the Apex Jobs UI. Confirm rollup totals match expected values after the batch completes. Schedule in production according to the business SLA (nightly recommended).
7. **Review checklist and document configuration.** Complete the review checklist below. Record namespace, picklist values added, and batch schedule in the work template for handoff.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] FSC packaging model confirmed (managed-package with `FinServ__` namespace vs Core FSC); all field references use the correct form
- [ ] `Rollups__c` picklist values verified for all required object types (FinancialAccount, Opportunity, Case, InsurancePolicy at minimum)
- [ ] All Household Account records use the Household record type and are standard Account records (not custom objects)
- [ ] All household members are Person Accounts; each linked via ACR with `FinServ__PrimaryGroup__c`, `FinServ__Primary__c`, and `FinServ__IncludeInGroup__c` correctly set
- [ ] No member has `FinServ__PrimaryGroup__c = true` on more than one ACR (one primary group per individual)
- [ ] No household has more than one ACR with `FinServ__Primary__c = true` (one primary member per household)
- [ ] Real-time rollup validated in sandbox: adding a financial account to a member updates the household's rollup totals
- [ ] Batch rollup job executed in sandbox and results match expected values
- [ ] Batch job scheduled in production (nightly recommended)
- [ ] NPSP not installed, or if present, FSC household model confirmed as the active model with Salesforce guidance

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Missing `Rollups__c` picklist values in pre-release orgs** — Orgs provisioned before certain FSC releases do not automatically receive all `Rollups__c` picklist values. If Cases, Insurance Policies, or Opportunities are missing from the picklist, rollup aggregation for those objects silently fails — no error is thrown, the rollup fields simply remain at zero or unchanged. Always audit the picklist before going live.
2. **`FinServ__IncludeInGroup__c` defaults to false in some org configurations** — When ACR records are created programmatically (via Apex, Data Loader, or Flow) without explicitly setting `FinServ__IncludeInGroup__c = true`, the field defaults to `false`. The member appears in the household relationship but their financial accounts are excluded from all rollups. This is the most common cause of "household rollup not working" tickets.
3. **Person Account `ContactId` on ACR must use `PersonContactId`, not `Id`** — ACR requires a Contact Id, not an Account Id. For Person Accounts, the underlying Contact is auto-created and its Id is exposed via `Account.PersonContactId`. Using the Person Account's `Account.Id` in the `ContactId` field of ACR will throw an error or silently fail. This is a frequent mistake in data migrations.
4. **FSC and NPSP household models are mutually exclusive** — The FSC rollup engine listens to ACR-based membership and the `Rollups__c` picklist. NPSP uses a direct `Contact.AccountId` lookup with its own rollup triggers. Installing both platforms in the same org causes rollup trigger conflicts, duplicate relationship records, and corrupted financial aggregations. There is no supported path to run both simultaneously.
5. **Batch rollup job does not cascade to sub-groups automatically** — If a Person Account belongs to multiple households (e.g., a joint account holder), the batch job recalculates rollups for all groups that include that member. However, if the `FinServ__IncludeInGroup__c` flag is toggled after the last batch run, the affected household rollup will not reflect the change until the next batch run or a manual trigger (e.g., saving the related financial account record).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured Household Account records | Standard Account records with the Household record type, populated FSC fields, and correct page layout |
| ACR membership records | AccountContactRelation records with `FinServ__PrimaryGroup__c`, `FinServ__Primary__c`, and `FinServ__IncludeInGroup__c` correctly set for each household member |
| `Rollups__c` picklist audit | List of verified or added picklist values for all required object types |
| Batch job schedule | Configured and tested scheduled batch rollup job with documented run frequency |
| Work template | Completed `household-model-configuration-template.md` recording org-specific configuration decisions |

---

## Related Skills

- `admin/financial-account-setup` — configure Financial Account records and roles that roll up to households; this skill handles the household container, that skill handles what goes inside it
- `admin/npsp-household-accounts` — NPSP-specific household model; architecturally incompatible with FSC; use only when FSC is not installed
- `admin/person-accounts` — enable and configure Person Accounts, which are required for FSC household membership
- `admin/fsc-data-model` — broader FSC data model overview including Groups, Relationships, and the full object graph
