# Examples — Permission Set Architecture

## Example 1: Sales And Service Personas With Shared Platform Access

**Context:** An org has 11 custom profiles for Sales, Service, and RevOps users. Most differences are object permissions, app access, and a few approval capabilities.

**Problem:** Every new entitlement request requires profile edits, regression testing, and a comparison against multiple near-duplicate profiles.

**Solution:**

```text
Baseline profile: Standard Platform User

Permission Sets
- core-crm-access
- case-console-core
- opportunity-management
- quote-approver
- revenue-ops-tools

Permission Set Groups
- psg-sales-rep = core-crm-access + opportunity-management
- psg-service-agent = core-crm-access + case-console-core
- psg-revops = core-crm-access + opportunity-management + revenue-ops-tools
```

**Why it works:** The design separates baseline settings from feature capabilities. New access changes become permission-set or PSG changes instead of profile cloning.

---

## Example 2: Shared Bundle With One Restricted Persona

**Context:** Two support teams use the same console tools, but Tier 1 must not close premium cases or access refund approval objects.

**Problem:** Admins are about to clone the support bundle into two almost identical permission sets and maintain both forever.

**Solution:**

```text
PSG: psg-support-core
  includes:
  - case-console-core
  - knowledge-agent
  - entitlement-visibility
  - refund-approval

Muted PSG variant for Tier 1:
  - mute refund-approval object permission
  - mute close-premium-case custom permission
```

**Why it works:** The common bundle stays reusable while the restricted persona is handled through a narrow subtractive layer instead of wholesale duplication.

---

## Anti-Pattern: One Profile Per Job Title, Region, And Exception

**What practitioners do:** They create profiles such as `Sales_US`, `Sales_EMEA`, `Sales_Contractor`, and `Sales_Contractor_Limited`, then keep adding permissions directly to each.

**What goes wrong:** The org loses any reusable access model. Audits become profile-by-profile archaeology, permission drift accelerates, and emergency fixes create even more variants.

**Correct approach:** Keep profiles thin, move feature access into capability-based permission sets, and use PSGs plus tightly governed exceptions for recurring personas.
