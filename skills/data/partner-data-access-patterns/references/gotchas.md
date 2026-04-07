# Gotchas — Partner Data Access Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Partner Role Hierarchy Is Auto-Generated and Cannot Be Customized

**What happens:** When you enable a user as a Partner Community user, Salesforce automatically creates a 3-tier role hierarchy (Executive / Manager / User) scoped to the user's partner account. These tiers are fixed. You cannot add tiers, rename them, merge accounts into a shared hierarchy, or otherwise restructure the tree.

**When it occurs:** Any time a business requests "4-level partner hierarchy" or "sub-distributor under distributor" visibility models. The request sounds natural from a business standpoint but cannot be implemented by modifying the auto-generated roles.

**How to avoid:** Design cross-tier or cross-account visibility using sharing rules and public groups rather than attempting to modify the hierarchy structure. Clearly document this platform constraint early in discovery to set correct expectations. If a distributor needs to see sub-distributor records, this is a cross-account sharing rule scenario, not a hierarchy change.

---

## Gotcha 2: Customer Community Plus Gets Only One Role, Not Three

**What happens:** Customer Community Plus licenses create a single role per partner account — there is no Executive, Manager, or User tier. Practitioners who see "Community Plus" and assume they get the same 3-tier hierarchy as Partner Community licensees will design sharing models that silently fail. Managers assigned a CC+ license will not see sub-user records via hierarchy because there is no hierarchy depth.

**When it occurs:** When project requirements call for hierarchical partner visibility but the selected license is Customer Community Plus (e.g., for cost reasons). The license choice is often made independently of the data visibility design, creating a late-stage mismatch.

**How to avoid:** Confirm license type before designing the sharing model. If hierarchical manager visibility is a hard requirement, document that Partner Community license is required and include this in the license sizing conversation. Do not attempt to simulate hierarchy with sharing rules for CC+ — it adds complexity and maintenance overhead; the right fix is the correct license.

---

## Gotcha 3: Account Ownership Change Reconstructs the Hierarchy and Triggers Recalculation

**What happens:** The Salesforce Account record owner is the root of the partner role hierarchy for that account. If the Account owner changes — due to CSM reassignment, territory realignment, or org restructuring — Salesforce rebuilds the partner role hierarchy for that account. In orgs with large numbers of partner-owned records, this triggers a background sharing recalculation job that can run for hours and temporarily creates inconsistent data visibility.

**When it occurs:** Account ownership changes as part of routine Salesforce administration (e.g., a user leaves the company and their records are mass-reassigned). The impact on partner hierarchy is rarely documented in account ownership transfer runbooks.

**How to avoid:** Treat the Account owner field on partner accounts as a governed field, not a routine administrative field. Implement a validation rule or approval process before partner Account ownership changes. When a change is necessary, schedule it during low-traffic hours and monitor sharing recalculation queue (Setup > Background Jobs or Apex Jobs for mass-reshare triggers). Notify affected partner users of potential access delays.

---

## Gotcha 4: PRM Objects Are Inaccessible to Non-Partner Community Licenses

**What happens:** Deal Registration objects (`PartnerFundRequest`, `PartnerFundClaim`) and PRM-surfaced Leads and Opportunities are only exposed to Partner Community licensees. If a user holds a Customer Community or Customer Community Plus license, these objects either do not appear in their context or return access-denied errors — even if sharing rules are configured to expose them.

**When it occurs:** When a cost-optimization decision swaps Partner Community licenses to Customer Community Plus without auditing which objects were being accessed. Also common when a new object type (e.g., Market Development Funds) is added to the partner portal and the license type of existing users is not verified.

**How to avoid:** Before exposing any PRM object type to a user population, verify each user's license type. A SOQL query against the `User` object (`SELECT Id, Name, UserType, Profile.UserLicenseId FROM User WHERE IsPartner = true`) can identify all partner users and their license categories. Cross-reference against the PRM objects in scope.

---

## Gotcha 5: External OWD Is Set Independently of Internal OWD

**What happens:** Salesforce maintains separate OWD settings for internal users and external (community) users. The External OWD on an object controls baseline access for all community users, including partner users, independently of the internal OWD. Setting Internal OWD to Private does not make the External OWD Private — they are separate fields. An object can have Internal = Private and External = Public Read/Write, which would expose all records to partner users.

**When it occurs:** When an admin tightens internal OWD for a compliance reason and assumes the change also restricts partner access. Or when a new object is added and the external OWD is never explicitly configured (it defaults to the internal OWD value in most cases, but this should always be verified explicitly).

**How to avoid:** Always audit both OWD settings (Internal and External) for every in-scope object when designing or auditing a partner sharing model. Navigate to Setup > Sharing Settings > Object Defaults and verify the External column explicitly. Do not rely on inherited defaults — set External OWD explicitly for every sensitive object.
