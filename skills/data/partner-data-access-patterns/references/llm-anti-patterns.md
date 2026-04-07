# LLM Anti-Patterns — Partner Data Access Patterns

Common mistakes AI coding assistants make when generating or advising on partner data access patterns in Salesforce. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Designing Sharing Rules for Within-Account Manager Visibility

**What the LLM generates:** A set of sharing rules or Apex-based sharing that explicitly shares records from rep users to their manager within the same partner account — e.g., a sharing rule that shares all Opportunities owned by "Partner User tier" roles with "Partner Manager tier" roles.

**Why it happens:** LLMs trained on general Salesforce sharing content default to explicit rule-based sharing because it is the most commonly documented pattern. They do not distinguish between internal role hierarchy (which requires explicit rules for peer visibility) and the auto-generated partner role hierarchy (which provides upward visibility natively).

**Correct pattern:**

```
No sharing rule needed for within-account manager visibility.

Partner role hierarchy auto-generates:
  - Executive tier → sees Manager + User tier records (same account)
  - Manager tier → sees User tier records (same account)

Only add sharing rules when:
  - Cross-account visibility is required
  - An exception beyond hierarchy is needed (specific users, specific records)
```

**Detection hint:** If the output includes sharing rules where both the "owned by" and "share with" parties are roles within the same partner account's hierarchy, the rule is likely redundant. Search the output for patterns like `role = "Partner Manager"` and `share with = "Partner Executive"` on the same account.

---

## Anti-Pattern 2: Recommending Customer Community Plus for PRM Use Cases

**What the LLM generates:** A recommendation to use Customer Community Plus (CC+) licenses for a partner portal that includes Deal Registration, Lead management, or other PRM objects — often framed as a cost-saving measure.

**Why it happens:** LLMs conflate "Community Plus" with "full partner capabilities" because the "Plus" suffix implies feature richness. They are not reliably aware that PRM objects and 3-tier hierarchy are Partner Community license entitlements, not CC+ entitlements.

**Correct pattern:**

```
PRM object access (Deal Registration, Partner Funds, PRM-surfaced Leads/Opps):
  → Requires: Partner Community license
  → Customer Community Plus: NOT supported

3-tier role hierarchy (Executive / Manager / User):
  → Requires: Partner Community license
  → Customer Community Plus: 1 role per account only

Use Customer Community Plus only when:
  - No PRM objects are needed
  - Flat (non-hierarchical) partner access is sufficient
```

**Detection hint:** If the output recommends Customer Community Plus AND mentions Deal Registration, Lead routing, or partner hierarchy visibility, flag as incorrect. Search for "Community Plus" near "PRM", "Deal Registration", or "partner role hierarchy".

---

## Anti-Pattern 3: Ignoring Hierarchy Reconstruction on Account Ownership Change

**What the LLM generates:** Account ownership transfer runbooks or admin guidance that treats the Account `OwnerId` field as a routine administrative field, with no mention of the sharing recalculation impact on partner role hierarchies.

**Why it happens:** LLMs document account ownership changes in the context of internal users, where ownership change recalculation is well-understood. The additional layer — that partner account ownership drives hierarchy root for all partner users on that account — is a nuance that is not prominent in most documentation.

**Correct pattern:**

```
Before changing Account owner on a partner account:
1. Identify all partner users enabled on this account (query: WHERE AccountId = <id> AND IsPartner = true)
2. Estimate sharing recalculation scope (number of Opportunity/Lead records owned by these users)
3. Schedule ownership change during low-traffic window
4. Monitor Background Jobs in Setup for mass-reshare completion
5. Validate partner user access post-change with a test login
```

**Detection hint:** If the output includes Account ownership transfer steps for a partner org and does not mention sharing recalculation, hierarchy impact, or partner user access validation, the guidance is incomplete.

---

## Anti-Pattern 4: Treating Partner Role Hierarchy Like Internal Role Hierarchy

**What the LLM generates:** Advice to navigate to Setup > Roles to customize the partner role hierarchy — e.g., adding tiers, renaming the Executive/Manager/User roles, or nesting one partner hierarchy under another.

**Why it happens:** Internal role hierarchies in Salesforce are fully customizable via Setup > Roles. LLMs trained primarily on internal Salesforce administration conflate the two systems and suggest customization paths that do not exist for auto-generated partner hierarchies.

**Correct pattern:**

```
Partner role hierarchy:
  - AUTO-GENERATED when a user is enabled as Partner Community user
  - Fixed structure: Executive / Manager / User (3 tiers per account)
  - Cannot be renamed, extended, or restructured via Setup > Roles
  - Cannot merge hierarchies across accounts

For non-standard hierarchy requirements:
  - Use criteria-based sharing rules for cross-account access
  - Use public groups to model cross-account collaboration groups
  - Document the constraint clearly; do not attempt workarounds via internal role manipulation
```

**Detection hint:** If the output suggests navigating to Setup > Roles to edit or customize partner roles, or mentions "adding a fourth tier to the partner hierarchy", this is incorrect. Flag any instruction that treats partner roles as editable objects.

---

## Anti-Pattern 5: Assuming External OWD Inherits From Internal OWD

**What the LLM generates:** Sharing model guidance that sets the internal OWD to Private and assumes partner users are therefore also restricted — without explicitly setting the External OWD.

**Why it happens:** In older Salesforce configurations, External OWD did not exist as a separate field (it was added in later releases). LLMs trained on older documentation may not distinguish between internal and external OWD settings, or may assume they are always in sync.

**Correct pattern:**

```
Salesforce maintains SEPARATE OWD settings:
  - Internal OWD: controls baseline access for internal (employee) users
  - External OWD: controls baseline access for all external (community) users

Setting Internal OWD = Private does NOT automatically set External OWD = Private.

For every sensitive object in a partner org:
  1. Navigate to Setup > Sharing Settings > Default Sharing Settings table
  2. Verify BOTH "Default Internal Access" and "Default External Access" columns
  3. Set External OWD explicitly — do not rely on default inheritance
```

**Detection hint:** If the output includes sharing model setup instructions for a partner/community org and only mentions setting the OWD once (without distinguishing internal vs external), the guidance is incomplete. Search for both "Default Internal Access" and "Default External Access" — if only one is present, the other was likely omitted.

---

## Anti-Pattern 6: Manual Sharing Without Documentation or Review Process

**What the LLM generates:** Instructions to use the Share button on individual records to grant partner users access to specific Opportunities or Leads, with no mention of auditability, lifecycle management, or review cadence.

**Why it happens:** Manual sharing is the simplest one-click solution for "this user needs to see this record." LLMs default to the most direct answer without considering that manual shares are invisible in sharing rule lists, persist until explicitly removed, and accumulate silently over time.

**Correct pattern:**

```
Manual sharing is appropriate for:
  - Genuine one-off exceptions
  - Short-lived co-sell or handoff scenarios

Manual sharing requires:
  - A log entry (record ID, user/group granted, reason, expiry date)
  - A periodic review process (quarterly recommended)
  - A designated owner for each manual share

Do NOT use manual sharing:
  - As a substitute for proper sharing rule design
  - For structural, ongoing cross-account access (use criteria-based sharing rules instead)
```

**Detection hint:** If the output recommends manual sharing for more than one or two records, or for an ongoing business pattern (e.g., "all co-sell deals"), the correct mechanism is a sharing rule, not manual sharing. Flag any solution that scales manual sharing to a structural use case.
