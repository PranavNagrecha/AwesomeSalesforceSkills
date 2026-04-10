# Examples — Multi-BU Marketing Architecture

## Example 1: Global Retail Brand Sharing Suppression Lists Across Regional Child BUs

**Context:** A global retail company has one Marketing Cloud Enterprise 2.0 org with a Parent BU and six regional Child BUs (North America, EMEA, APAC, LATAM, Middle East, ANZ). Each region operates its own email program, but privacy regulations (GDPR in EMEA, CAN-SPAM in North America) require that an opt-out recorded in any region is honored globally before any subsequent send.

**Problem:** Without a centralized suppression mechanism, a subscriber who opts out of the EMEA BU's sends continues to receive emails from the North America BU. Each Child BU maintains its own unsubscribe list and there is no cross-BU enforcement.

**Solution:**

1. In the Parent BU, create a Data Extension called `Global_Suppression_Master` with columns: `EmailAddress`, `OptOutDate`, `OptOutBU`, `Reason`.
2. Create a folder in the Parent BU named `Shared Suppression` and move `Global_Suppression_Master` into it.
3. Configure the folder's Shared Data Extension Permissions to grant **Read** access to all six regional Child BUs.
4. In each Child BU, build a nightly Automation that uses a SQL Query Activity to append that BU's local unsubscribes to `Global_Suppression_Master` (via a cross-BU write-back mechanism using the Parent BU's Automation Studio or API).
5. Reference `Global_Suppression_Master` as a suppression list in every Child BU's email send activities and Journey Builder email steps.

**Why it works:** The Shared DE in the Parent BU acts as the single source of truth for suppression. Because it is accessible to all Child BUs, a send in any region checks the same list before delivery. Changes to folder permissions are Parent-BU-admin-controlled, preventing individual regions from accidentally breaking the suppression chain.

---

## Example 2: Multi-Brand Organization with Strict Data Segregation

**Context:** A financial services holding company owns two insurance brands — Brand A targeting consumers and Brand B targeting small businesses. Both brands share a single Marketing Cloud Enterprise 2.0 org for cost efficiency, but they have separate data ownership obligations: Brand A's customer data must not be accessible to Brand B's marketing team, and vice versa.

**Problem:** If both brands are operated within a single Child BU (or the Parent BU), a misconfigured user role or a shared folder could expose Brand A's subscriber records to Brand B's team. Platform-level enforcement is needed, not just access controls.

**Solution:**

1. Create two separate Child BUs: `BrandA-Consumer` and `BrandB-SMB`.
2. Provision Brand A's marketing team exclusively in `BrandA-Consumer`; provision Brand B's team exclusively in `BrandB-SMB`. No team member has access to both Child BUs.
3. Configure separate SAP, DKIM, and Reply Mail Management for each Child BU so that sending identities are fully distinct.
4. Do not configure any Shared DE permissions between `BrandA-Consumer` and `BrandB-SMB`. The Parent BU's shared folder, if used at all, is limited to content that legitimately spans both brands (e.g., company-wide legal footer content blocks).
5. Run all analytics and reporting scoped to each Child BU independently; do not export combined subscriber data across both BUs.

**Why it works:** BU-level scoping is a platform-enforced boundary. Data Extensions, automations, sends, and subscriber records in `BrandA-Consumer` are structurally inaccessible from `BrandB-SMB` without an explicit Shared DE configuration. The absence of shared permissions is the control.

---

## Anti-Pattern: Attempting Brand Separation Within a Single Child BU

**What practitioners do:** To avoid the overhead of provisioning separate Child BUs, teams try to separate two brands within one Child BU using folder permissions and Marketing Cloud role restrictions — e.g., giving Brand A's team access only to Brand A's DE folders and restricting Brand B's team to their own folders.

**What goes wrong:** Marketing Cloud's folder-level role restrictions within a BU are not consistently enforced across all tools. A user with the Marketing Cloud Administrator role at the Child BU level can see all DEs regardless of folder-level restrictions. Journey Builder and Automation Studio also provide data access pathways that folder restrictions do not cover. The result is a permission model that appears correct but has exploitable gaps.

**Correct approach:** Use separate Child BUs for each brand. Platform-enforced BU scoping provides the clean boundary that folder restrictions within a BU cannot reliably deliver.
