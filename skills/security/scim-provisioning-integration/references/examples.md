# SCIM Provisioning — Examples

## Example 1: Okta → Salesforce With PSG Bundles

**Context:** Okta tenant has role-based groups (`sf-sales`, `sf-service`, `sf-admin`).

**Mapping:**
- `sf-sales` → Permission Set Group `Sales_Baseline` (PS: SalesCloudUser, ForecastsUser).
- `sf-service` → PSG `Service_Baseline` (PS: ServiceCloudUser, KnowledgeUser).
- `sf-admin` → PSG `Admin_Elevated` + PAM approval required.

**Why it works:** Role-to-PSG is stable; individual PS composition can evolve without renaming groups.

---

## Example 2: Freeze-First Deprovisioning

**Context:** Financial services org, same-day deprovisioning SLA.

**Runbook:**
1. HR fires "terminate" in Workday → IdP removes user from all SF groups.
2. IdP fires SCIM `PATCH active=false`.
3. Pre-hook: immediate `freeze-user` call (blocks new logins instantly).
4. Apex hook: revoke active OAuth tokens for the user.
5. Async job: reassign open cases/opps/queues per ownership policy.
6. Final: SCIM deactivation completes.

**Why it works:** No window where a terminated user can access data with a cached token.

---

## Anti-Pattern: Direct Profile Mapping

Mapping IdP groups to Salesforce Profiles directly. Profile changes are heavier than PS changes and often violate Salesforce design guidance. Use a default profile and layer entitlements via PS/PSG.
