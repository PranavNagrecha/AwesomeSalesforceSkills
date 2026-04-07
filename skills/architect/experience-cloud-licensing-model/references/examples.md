# Examples — Experience Cloud Licensing Model

## Example 1: B2C Customer Portal — Customer Community License Selection

**Context:** A retail company is launching a self-service portal for 80,000 registered customers. The portal will allow customers to submit support cases, browse a knowledge base, track their order history (stored on a custom `Order__c` object linked to Account), and update their contact information. No reports or dashboards are required for end customers. Expected login pattern: roughly 5–8% of users log in on any given day.

**Problem:** The architect needs to select the correct license tier and billing variant. Without a structured decision framework, teams often default to Customer Community Plus "to be safe," paying for role-based sharing they do not need, or discover too late that they need criteria-based sharing rules that Customer Community cannot support.

**Analysis:**

Step 1 — CRM object check: The portal requires Cases, Knowledge, Contact, Account, and a custom object. No Leads, Opportunities, or Contracts. Customer Community is not eliminated.

Step 2 — Sharing model check: Order records need to be shared with the account holder. A Sharing Set configured on `Order__c.Account__c` maps the lookup to the portal user's Account — no roles needed. Customer Community is still viable.

Step 3 — Reports/dashboards check: End customers do not need reports. Customer Community is still viable.

Step 4 — Login economics: 80,000 users × 6% daily active = ~4,800 logins/day. Over 30 days that is approximately 144,000 login events. At login-based pricing, compare 144,000 credits/month against 80,000 member seats. At typical list pricing, login-based is significantly cheaper below the 25% DAU threshold. Recommended: **login-based Customer Community**.

**Solution summary:**

- License tier: Customer Community (login-based)
- Sharing: Sharing Set on `Order__c` with lookup to Account
- Upgrade trigger: if reporting requirements surface or if custom object sharing needs criteria-based rules, migrate to Customer Community Plus

**Why it works:** The Sharing Set handles all record visibility without roles. Login-based billing aligns cost to actual platform usage at low activity ratios.

---

## Example 2: B2B Channel Partner Portal — Partner Community License Selection

**Context:** A manufacturing company operates a network of 400 reseller partners across three tiers (Platinum, Gold, Silver). Each partner has between 3 and 15 portal users. Partners need to register deals (create Opportunities from a deal registration flow), view their own pipeline, track active Contracts, and receive MDF allocations. Partner managers need visibility into their team members' deals. A channel account manager at the manufacturer needs to see all activity for their assigned partner accounts.

**Problem:** The team initially proposed Customer Community Plus because it supports reports and the deal registration flow could theoretically be built on custom objects. However, this approach would require extensive custom Apex sharing to replicate the hierarchical visibility that Partner Community provides natively, and it cannot access standard Opportunity or Contract records.

**Analysis:**

Step 1 — CRM object check: Opportunities and Contracts are required. Customer Community and Customer Community Plus are both eliminated. Minimum tier: Partner Community.

Step 2 — Sharing model check: Per-account three-tier role hierarchy is needed for manager-level pipeline visibility. Partner Community's native role hierarchy (Partner Executive → Partner Manager → Partner User per Account) satisfies this without custom code.

Step 3 — Login economics: 400 partners × average 8 users = 3,200 users. Deal registration and pipeline review suggest near-daily login patterns for active users. At roughly 60% daily activity, member-based is more economical than login-based. Recommended: **member-based Partner Community**.

**Solution summary:**

- License tier: Partner Community (member-based)
- Sharing: per-account role hierarchy with PRM features enabled
- Deal registration: standard Opportunity creation with Partner Community deal registration flow
- Channel account manager access: internal Salesforce license with partner account ownership in the standard role hierarchy

**Why it works:** Partner Community provides native Opportunity and Contract access, the built-in per-account role hierarchy eliminates custom sharing Apex, and member-based billing is appropriate for high-frequency users.

---

## Anti-Pattern: Recommending Customer Community for All External Portals

**What practitioners do:** Default to Customer Community for every portal project because it is the cheapest and most commonly known tier, then attempt to work around its limitations (no roles, no reports) with custom Apex sharing classes and workaround dashboards in Lightning pages.

**What goes wrong:**
- Reports and dashboards cannot be embedded for Customer Community users regardless of configuration — this is a hard platform constraint, not a permission setting.
- Custom Apex sharing for complex visibility requirements adds maintenance debt and governor limit risk at scale.
- When the business later requests partner-facing Opportunity access, a full license migration is required for all affected user profiles.

**Correct approach:** Run the decision framework in SKILL.md Recommended Workflow steps 1–4 before committing to a tier. Identify the minimum tier that satisfies sharing model complexity, object access, and reporting requirements. Accept slightly higher per-user cost at the correct tier rather than engineering around license constraints.
