# LLM Anti-Patterns — Territory Design Requirements

Common mistakes AI coding assistants make when generating or advising on territory design requirements for Salesforce ETM. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Date Fields as Assignment Rule Criteria

**What the LLM generates:** "Create an assignment rule for the Renewal Q2 territory: ContractRenewalDate__c >= '2025-04-01' AND ContractRenewalDate__c <= '2025-06-30'. This will automatically assign accounts with spring renewals to the Q2 territory."

**Why it happens:** LLMs generalize from other rule-based automation contexts (Flow, Process Builder, validation rules) where date fields are fully supported. ETM assignment rules have a narrower field type support list that is not prominent in most training data.

**Correct pattern:**

```
Assignment rule criteria must use supported field types only:
  - Text
  - Picklist
  - Numeric (Number, Currency, Percent)
  - Checkbox

Date fields are NOT supported.

Workaround: Create a custom picklist field on Account — e.g., RenewalQuarter__c
with values: Q1, Q2, Q3, Q4. Populate via Flow or formula field.
Assignment rule: RenewalQuarter__c = 'Q2'
```

**Detection hint:** Any requirement mentioning a date field as territory assignment criteria — look for field names containing "Date," "Date__c," "CreatedDate," "CloseDate," or similar.

---

## Anti-Pattern 2: Treating Territory Hierarchy as a Mirror of Role Hierarchy

**What the LLM generates:** "Design the territory hierarchy to match your role hierarchy: SVP -> Regional VP -> Area Director -> Manager -> Rep. Create one territory for each role node. This ensures forecasting and access align with your org structure."

**Why it happens:** Role hierarchy and territory hierarchy both involve hierarchical structures that affect user visibility, and training examples often conflate them. The distinction — that they serve different purposes and should be designed independently — requires nuanced platform knowledge.

**Correct pattern:**

```
Territory hierarchy: designed around stable coverage areas (geographic regions,
account segments, verticals). Node names reflect coverage (e.g., "US West",
"Enterprise Segment"), not people or roles.

Role hierarchy: designed around management reporting and opportunity visibility.

These two hierarchies are independent in Salesforce ETM. Designing them to mirror
each other couples changes in org structure to territory realignment — a fragile
design that becomes expensive to maintain as the business scales.
```

**Detection hint:** Territory node names containing personal titles ("VP," "Director," "Manager"), person names, or territory structures that exactly match the number of management levels in the org chart.

---

## Anti-Pattern 3: Using ETM to Restrict Access Below Org-Wide Defaults

**What the LLM generates:** "To ensure reps only see accounts in their territory, assign each rep only to their territory and leave the Account OWD as Public Read/Write. Territory assignment controls which accounts they can see."

**Why it happens:** LLMs learn a simplified mental model that territory membership controls account visibility. The critical nuance — that ETM access is always additive and cannot override OWD — is not prominently documented in most introductory content, so it gets dropped.

**Correct pattern:**

```
ETM territory membership ADDS access. It cannot restrict below Account OWD.

If Account OWD = Public Read/Write:
  All users see all accounts regardless of territory membership.
  Territory membership provides no restriction.

If Account OWD = Private:
  Users see accounts they own or to which they have been granted access
  (including via territory membership).
  Territory membership ADDS visibility to assigned-territory accounts.

To restrict reps to only their territory accounts:
  1. Set Account OWD to Private (sharing-and-visibility skill)
  2. Then configure territory membership to grant reps access to their territory accounts

Requirements must verify the OWD setting before claiming territory-based restriction.
```

**Detection hint:** Requirements or guidance claiming that territory assignment controls visibility without mentioning OWD, or instructions to "leave OWD as-is" while expecting territory-based access restriction.

---

## Anti-Pattern 4: Proposing Hierarchies Deeper Than 6 Levels Without Justification

**What the LLM generates:** "Your territory hierarchy should be: Global -> Continent -> Country -> Region -> Sub-Region -> State -> City -> Rep. This gives maximum granularity for forecasting at every level."

**Why it happens:** LLMs tend to propose maximally complete structures when asked about hierarchy design, without considering maintenance overhead, forecast rollup readability, or the actual number of managers who will consume each rollup level.

**Correct pattern:**

```
Best practice hierarchy depth: 3-5 levels.

Each level should correspond to a real consumer of forecast data at that level
(a person who reviews forecasts at that rollup node). Adding hierarchy levels
beyond actual management needs:
  - Increases forecast rollup complexity
  - Creates "ghost" territories with no assigned users
  - Makes the model harder to maintain during realignments

Validate hierarchy depth against the actual number of management layers who
will consume territory-based forecasts. Remove intermediate levels that have
no forecast consumers.

Common valid shapes:
  3 levels: National -> Region -> Rep Territory
  4 levels: Global -> Country -> Region -> Rep Territory
  5 levels: Global -> Continent -> Country -> Region -> Rep Territory
```

**Detection hint:** Proposed hierarchies with 6 or more levels, or hierarchies where intermediate levels do not correspond to identifiable forecast consumers in the org's management structure.

---

## Anti-Pattern 5: Recommending Rule-Based Named Account Assignment for Frequently-Changing Lists

**What the LLM generates:** "For your named account list of 80 strategic accounts, create assignment rules: AccountName = 'Acme Corp' OR AccountName = 'Globex Corporation' OR ... for all 80 accounts. This will automatically assign them to the Named Account territory."

**Why it happens:** Rule-based assignment is the canonical ETM assignment mechanism, so LLMs default to it. The operational cost of maintaining large lists of exact-match text rules — especially when the list changes quarterly — is not surfaced in most ETM overview content.

**Correct pattern:**

```
Named account list management approaches by change frequency:

STABLE list (changes < once/year):
  Rule-based: Account Name exact-match rules or custom IsNamedAccount__c flag field
  Acceptable — low maintenance burden

CHANGING list (changes quarterly or more frequently):
  Manual account-to-territory assignment OR
  Custom field approach: IsNamedAccount__c = true (set via admin or Flow),
    then a single rule per named account territory: IsNamedAccount__c = true

Avoid: 80 individual AccountName exact-match rules in ETM assignment rule set.
Problems:
  - Each quarterly list change requires editing and saving individual rules
  - Text exact-match on Account Name is fragile (punctuation, spacing, legal name changes)
  - Triggers a full assignment rule rerun when rules are modified
  - Does not scale beyond ~20 named accounts without becoming unmanageable

Preferred for changing lists: IsNamedAccount__c checkbox field, managed by
sales ops via list view or Flow automation.
```

**Detection hint:** Assignment rule sets containing large numbers of individual Account Name text-match conditions, or any rule set with more than 10 criteria that could be reduced by using a proxy field.

---

## Anti-Pattern 6: Ignoring the User-to-Territory Ratio

**What the LLM generates:** "Create one territory per state in the US (50 territories) to give maximum flexibility. Reps can be assigned to multiple territories."

**Why it happens:** LLMs optimize for coverage completeness and granularity. The operational consequence — that 50 territories for 15 reps creates an administratively expensive ratio in the wrong direction — requires awareness of the 3:1 target and its rationale.

**Correct pattern:**

```
Target user-to-territory ratio: ~3:1 (territories per user).

Ratios above 10:1: too many territories relative to team size.
  - Admin overhead is high (many territories to maintain, assign, audit)
  - Forecast visibility is fragmented
  - Consider consolidating low-density territories

Ratios below 1:1: too few territories relative to team size.
  - Coverage accountability is unclear
  - Forecast granularity is too coarse
  - Consider splitting high-density territories

When designing territory count:
  Proposed territory count / Active user count ~= 3:1

50 state-level territories for 15 reps = 3.3:1 — acceptable only if each state
territory has sufficient account volume to justify a distinct coverage area.
Validate by checking account count per proposed territory, not just territory count.
```

**Detection hint:** Territory proposals where territory count significantly exceeds team size (ratio > 10:1) or where all states/provinces are given individual territories without verifying team size and account distribution.
