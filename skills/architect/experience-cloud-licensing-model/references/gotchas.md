# Gotchas — Experience Cloud Licensing Model

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Login Credits Do Not Roll Over

**What happens:** Login-based license credits are consumed per daily unique login. Any credits not used within the monthly billing period expire — they do not carry forward. An org that purchases 1,000 login credits but consumes only 400 in a month permanently loses the remaining 600.

**When it occurs:** At portal launch when actual user adoption ramps slower than projected. Teams often purchase credits to cover peak projected usage from day one. During the ramp period (typically months 1–6), significant over-purchase occurs.

**How to avoid:** Start with a conservative login credit pool sized at confirmed baseline adoption and add credits as usage grows. Monitor login consumption with the `UserLogin` object or the License Management App. Avoid purchasing "headroom" upfront for login-based pools — unlike member seats, unused capacity generates no value.

---

## Gotcha 2: Customer Community Cannot Display Reports or Dashboards

**What happens:** Users with Customer Community licenses cannot view Salesforce Reports or Dashboards in an Experience Cloud site. This is a hard platform enforcement at the license level, not a profile or permission set configuration issue. No combination of permission sets or Experience Builder components will enable report visibility for a Customer Community user.

**When it occurs:** During UAT when a stakeholder or product owner expects to see a customer-facing dashboard (e.g., "order history report," "case trend chart"). The requirement was assumed to be a feature-flag problem, not a license constraint.

**How to avoid:** Confirm report and dashboard requirements explicitly during requirements gathering. If any external user must view a Salesforce Report or Dashboard, the minimum license tier is Customer Community Plus. Document this as a hard constraint in the design decision record. Note that charts built on SOQL queries within LWC components are not "reports" and can be displayed on any license tier — this is an alternative for custom visualizations that does not require a tier upgrade.

---

## Gotcha 3: License Tier Is Locked to Profile — Upgrade Requires Profile Migration

**What happens:** A user's Experience Cloud license type is determined by the profile assigned to them. Customer Community users are on a Customer Community profile; Partner Community users are on a Partner Community profile. Changing a user's license tier means changing their profile. If the same profile is shared across many users, all users are affected by any profile change. More commonly, a new profile is created for the new tier and individual users are migrated — which at scale (thousands of users) is a significant bulk data operation with potential for permission regressions.

**When it occurs:** Mid-project when a "small" requirements change introduces the need for reports, role-based sharing, or Opportunity access. The team assumed a profile setting could be changed; instead a full user migration is required.

**How to avoid:** Model the 12–18 month feature roadmap before selecting a license tier. If there is meaningful probability of needing reports, partner CRM objects, or per-account role hierarchy within the portal lifetime, start at the higher tier. The cost premium is typically less than the operational cost of a mid-project license migration. Document the upgrade conditions explicitly in the architecture decision record.

---

## Gotcha 4: External Apps License Requires Explicit Object Permission Configuration

**What happens:** Teams selecting External Apps license assume it automatically grants access to all objects because it is described as the "most flexible" tier. In practice, External Apps provides the maximum license ceiling for object access, but all actual object-level permissions (Read, Create, Edit, Delete), field-level security, and record access must still be explicitly configured on the user profile and permission sets.

**When it occurs:** After license assignment when users encounter "Insufficient Privileges" errors on objects that were expected to be accessible under External Apps.

**How to avoid:** Treat External Apps license selection as unlocking the capability ceiling, not as granting access. Build the profile/permission set configuration explicitly for each required object and field just as you would for any Salesforce user type. Do not skip the permission audit step.

---

## Gotcha 5: Sharing Sets Are Account-Lookup Based Only

**What happens:** Sharing Sets grant record access by matching a lookup field on the shared object to the portal user's Account (or a related Account via an account-to-account lookup chain). They cannot evaluate arbitrary criteria, formula fields, or multi-object relationships. Teams attempt to use Customer Community with Sharing Sets for records that need to be shared based on product category, region, or status — and discover that Sharing Sets cannot express these conditions.

**When it occurs:** When portal designers assume Sharing Sets are equivalent to sharing rules with simpler syntax. They are not — Sharing Sets are strictly account-lookup-based.

**How to avoid:** If the sharing requirement cannot be expressed as "share this record with all users whose Account matches the record's Account lookup field," Sharing Sets will not work. The minimum required tier is Customer Community Plus (enables criteria-based sharing rules) or Partner Community (enables role hierarchy). Map the sharing requirement to the available mechanism before committing to a license tier.
