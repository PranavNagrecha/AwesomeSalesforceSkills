# Gotchas — NPSP vs. Nonprofit Cloud Decision

Non-obvious Salesforce platform behaviors and architectural facts that cause real problems in this decision domain.

## Gotcha 1: No In-Place Migration Path Exists

**What happens:** Organizations and advisors assume they can convert an existing NPSP org to Nonprofit Cloud using a Salesforce-provided migration tool, package upgrade, or configuration change. This assumption leads to wasted discovery time, incorrect budgeting, and eventual project restarts when the reality is discovered.

**When it occurs:** Any time a client asks "how do we upgrade to Nonprofit Cloud" or a consultant begins scoping a migration without first validating the architecture. AI assistants are particularly prone to hallucinating an upgrade procedure because "upgrade" is a common pattern for managed packages in Salesforce.

**How to avoid:** Always state explicitly at the outset: NPSP to NPC is a full org migration — provision a net-new org, rebuild configuration, migrate data. Never use the word "upgrade" when referring to this transition. Confirm the client understands this before any scoping begins.

---

## Gotcha 2: NPSP and NPC Use Incompatible Account Models

**What happens:** NPSP uses the Household Account model where individual Contacts are related to a Household Account (an Account record with Record Type = Household). Nonprofit Cloud uses Person Accounts by default, where each constituent is a single unified Account+Contact record. These two Account models are mutually exclusive at the org level — enabling Person Accounts in an NPSP org does not convert it to NPC, and an NPC org cannot run the NPSP Household model without serious data and trigger conflicts.

**When it occurs:** When a practitioner suggests adding Person Accounts to an NPSP org as a "first step" toward NPC, or when a data migration plan fails to account for the Contact-to-PersonAccount transformation required during migration.

**How to avoid:** Plan the data migration to explicitly transform each Household Account's constituent Contacts into Person Account records. This transformation affects relationship records, donation attribution, household roll-ups, and all downstream reports. It cannot be handled by a simple field mapping — it requires a structural data re-architecture pass.

---

## Gotcha 3: NPSP Is Feature-Frozen, Not End-of-Lifed

**What happens:** The phrase "NPSP is being sunset" circulates in the nonprofit Salesforce community, causing organizations to rush migration decisions without adequate preparation. The accurate statement is that NPSP is feature-frozen — no new capabilities will be developed — but Salesforce has not announced a hard end-of-life date as of April 2026. NPSP continues to receive critical security patches and bug fixes.

**When it occurs:** When community posts, AI-generated summaries, or informal advisor conversations inaccurately characterize NPSP's status. Organizations then make reactive migration decisions driven by fear rather than business requirements, often without sufficient implementation budget or change management capacity.

**How to avoid:** Use precise language. NPSP is feature-frozen with no new development since March 2023. It is not end-of-lifed. A decision to migrate should be driven by a feature gap or strategic need, not by an inaccurate EOL rumor. Always verify the current NPSP support status from Salesforce Help documentation before making a recommendation.

---

## Gotcha 4: The Program Management Module Does Not Map 1:1 to NPC Program Management

**What happens:** Organizations running the NPSP Program Management Module (PMM) assume that NPC's native Program Management is a direct replacement with equivalent functionality. In practice, NPC Program Management has architectural differences — different object names, different relationship models, and different reporting structures — that require careful feature-by-feature validation before migration.

**When it occurs:** During migration scoping when PMM is noted as "just another data migration." Teams discover mid-project that certain PMM capabilities (custom service delivery tracking patterns, complex enrollment workflows, community portal integrations) have no direct NPC equivalent and require custom development.

**How to avoid:** Treat PMM-to-NPC Program Management as a feature parity assessment, not a data mapping exercise. Produce a side-by-side feature comparison as part of the decision framework before committing to migration. Flag any PMM capabilities that require custom development in NPC so they are budgeted and scoped accurately.

---

## Gotcha 5: CRLP Rollup Definitions Do Not Transfer to NPC

**What happens:** NPSP's Customizable Rollup Summaries (CRLP) are managed package rollup definitions stored as NPSP custom metadata records. They power summary fields like Total Giving, Largest Gift, Last Gift Date, and Number of Gifts on Account and Contact records. These definitions do not exist in NPC, which uses its own native rollup framework (built on Salesforce rollup summary fields and custom aggregate flows). A migration that copies Opportunities and Accounts will arrive in NPC without any rollup values populated.

**When it occurs:** In post-migration UAT when the client reports that all their donor giving summary fields are blank or incorrect. CRLP was not rebuilt in NPC as part of the migration, and no one noticed because the data migration only covered object records, not rollup definitions.

**How to avoid:** Include a CRLP-to-NPC rollup rebuilding workstream explicitly in the migration project plan. Inventory all CRLP rollup definitions before migration begins. Plan to rebuild each using NPC's native mechanisms. Budget development time for this — it is not a configuration migration, it requires fresh setup.

---

## Gotcha 6: Recurring Donation Records Require Structural Transformation

**What happens:** NPSP Recurring Donations are custom objects in the NPSP managed package (`npe03__Recurring_Donation__c`). They generate installment Opportunity records on a schedule managed by NPSP triggers. NPC uses Gift Commitments and Gift Transactions as the native recurring giving model — different objects, different field names, different relationships to Person Accounts instead of Household Accounts. A simple data extract-load of Recurring Donation records into NPC will fail because the target objects are different.

**When it occurs:** When a data migration team treats Recurring Donations as a standard Opportunity migration and discovers mid-load that the target object structure does not match. Active recurring donors lose their giving history and schedule continuity.

**How to avoid:** Include Recurring Donation-to-Gift Commitment transformation in the migration data model design. Map each Recurring Donation to a Gift Commitment, each installment Opportunity to a Gift Transaction, and validate giving schedules and statuses are correctly carried over. Coordinate with the finance team to ensure historical giving totals are preserved in the new model.
