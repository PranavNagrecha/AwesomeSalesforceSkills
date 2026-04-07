# Examples — Partner Data Access Patterns

## Example 1: Regional Partner Manager Sees All Sub-Partner Deals

**Context:** A manufacturing company has a regional partner account (ACME Distribution — West) with five field sales reps and one regional manager. All six are Partner Community users. Reps create Opportunities as part of deal registration. The regional manager must see and report on all deals in their region.

**Problem:** Without guidance, a practitioner might create sharing rules to expose Opportunities from each rep to the manager. This is unnecessary, creates rule clutter, and can trigger performance issues during sharing recalculations.

**Solution:**

No sharing rule is needed. The auto-generated partner role hierarchy provides this access natively.

Steps to configure:
1. Enable each field rep as a partner user on ACME Distribution — West. Salesforce auto-assigns them to the **User** tier of this account's role hierarchy.
2. Enable the regional manager as a partner user on the same account. Salesforce auto-assigns them to the **Manager** tier.
3. Set Opportunity External OWD to **Private** (Setup > Sharing Settings > Opportunity > External Access = Private).
4. Verify "Grant Access Using Hierarchies" is enabled on Opportunity (this is the default and controls whether hierarchy drives visibility).
5. Log in as the regional manager using the User Switcher (Setup > Users > Login). Confirm they can see all Opportunity records owned by the five reps.

Configuration reference (no code needed):
```
Opportunity External OWD: Private
Grant Access Using Hierarchies: Enabled
Partner user tiers:
  - Field Reps → User tier (ACME Distribution — West)
  - Regional Manager → Manager tier (ACME Distribution — West)
```

**Why it works:** The Manager tier inherits visibility over records owned by users in the User tier within the same account's hierarchy branch. No sharing rule is required because hierarchy access flows upward automatically. The Executive tier (if provisioned) would see both Manager- and User-owned records.

---

## Example 2: Selective Cross-Account Sharing for Co-Sell Opportunities

**Context:** A technology vendor has two independent partner accounts — Global SI (a global system integrator) and Regional VAR. For specific deals tagged as "Co-Sell", Global SI needs to see Opportunities owned by Regional VAR users, and vice versa.

**Problem:** There is no natural hierarchy relationship between two different partner accounts. Role hierarchy is scoped per account — Global SI's Executive tier has no visibility into Regional VAR's records.

**Solution:**

Use a criteria-based sharing rule to expose co-sell Opportunities across accounts.

Configuration steps:
1. Create a custom Opportunity field: `Type__c` (picklist) with value "Co-Sell".
2. Create a Public Group containing the partner roles for Global SI (Setup > Public Groups > New > add "Global SI — Partner User", "Global SI — Partner Manager", "Global SI — Partner Executive" roles).
3. Repeat for Regional VAR.
4. Navigate to Setup > Sharing Settings > Opportunity > Sharing Rules > New Criteria-Based Rule:
   - Share Opportunities where `Type__c = Co-Sell`
   - Share with: Regional VAR Public Group
   - Access level: Read Only
5. Create a mirror rule sharing Co-Sell Opportunities with the Global SI Public Group.
6. Validate: log in as a Regional VAR User tier user and confirm they can see Co-Sell Opportunities owned by Global SI users. Confirm they cannot see non-Co-Sell Opportunities from Global SI.

```
Sharing Rule: Co-Sell Cross-Account (Opportunity)
  Criteria: Type__c = "Co-Sell"
  Share with: [Public Group: Regional VAR Partners]
  Access: Read Only

Sharing Rule: Co-Sell Cross-Account (Opportunity)
  Criteria: Type__c = "Co-Sell"
  Share with: [Public Group: Global SI Partners]
  Access: Read Only
```

**Why it works:** Criteria-based sharing rules apply based on field values rather than ownership, making them the correct mechanism for cross-account structural sharing. Scoping to the Co-Sell field ensures competing partners do not see each other's private pipeline. Public Groups make future management easier — adding a new user to a partner account automatically inherits the sharing via group membership.

---

## Anti-Pattern: Using Public External OWD to Solve Partner Visibility

**What practitioners do:** Set the Opportunity External OWD to Public Read/Write because "all partners need to see all deals" — it is simpler than designing sharing rules.

**What goes wrong:** All partner users across every partner account can see every Opportunity in the org. Competing partners see each other's pricing, deal status, and customer names. This is a data breach scenario for multi-partner orgs. Reversing it later requires a full sharing model redesign and may trigger large sharing recalculation jobs.

**Correct approach:** Keep Opportunity External OWD at Private. Use the auto-generated role hierarchy for within-account visibility and criteria-based sharing rules for controlled cross-account access. Limit manual sharing to genuine one-off exceptions.
