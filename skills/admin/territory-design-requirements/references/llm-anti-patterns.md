# LLM Anti-Patterns — Territory Design Requirements

Common mistakes AI coding assistants make when generating or advising on territory design requirements for Salesforce ETM. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Date Fields as Assignment Rule Criteria

**What the LLM generates:** "Create an assignment rule for the Renewal Q2 territory: ContractRenewalDate__c >= '2025-04-01' AND ContractRenewalDate__c <= '2025-06-30'. This will automatically assign accounts with spring renewals to the Q2 territory."

**Why it happens:** LLMs generalize from other rule-based automation contexts (Flow, Process Builder, validation rules) where date fields are fully supported. ETM assignment rules have a narrower field type support list that is not prominent in most training data.

**Why the usual correction is also wrong:** the confident reply "date fields are not supported as
ETM assignment rule criteria" is itself UNVERIFIED (2026-09-05). `Territory2RuleItem` > `field` is
documented in the Metadata API Developer Guide only as "The standard or custom object field that the
rule item operates on," with no type restriction, and the `operation` enum carries `lessThan`,
`greaterThan`, `lessOrEqual` and `greaterOrEqual`. An assistant that asserts the restriction is
guessing in the opposite direction. State it as unverified, or configure it in a sandbox.

**Correct pattern:** the argument that does hold is about staleness, not field types.

```
Assignment rules run automatically when records are CREATED and EDITED
(Metadata API, Territory2Rule > active). They are not re-evaluated because
a date passed. A date-range predicate is therefore only as fresh as the last
record edit or the last manual rule run - and "Rules can't be run via
Metadata API" (Territory2Rule > Usage), so that run is a person's job.

Design instead for a value that CHANGES when the segmentation changes:

  Renewal_Quarter__c   picklist  Q1 | Q2 | Q3 | Q4
  populated by a record-triggered Flow on Contract_Renewal_Date__c

  rule item:  field = Account.Renewal_Quarter__c
              operation = equals
              value = Q2

Now the field edit is what re-triggers evaluation, which is the only
mechanism the platform actually offers.
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

**Why it happens:** LLMs optimize for coverage completeness and granularity. The operational consequence — 50 territories to maintain, assign, audit and forecast on for 15 people — is invisible in an answer that only counts coverage.

**Correct pattern:** note that the ratio itself is a heuristic. UNVERIFIED (2026-09-05): the "~3:1" figure is not stated in the Metadata API Developer Guide, the Object Reference or the Salesforce App Limits Cheat Sheet. An assistant should present it as a review trigger, not as a Salesforce rule, and should move to the two numbers that actually decide — accounts per leaf territory and users per leaf territory.

```
Heuristic (UNVERIFIED, field practice): ~3 territories per user.

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

50 state-level territories for 15 reps = 3.3 territories per user — acceptable
only if each state territory has enough account volume to justify a distinct
coverage area. The ratio never settles the question on its own: validate by
account count per proposed territory, and by users per territory, both of which
can be computed from the current org before any territory exists.
```

**Detection hint:** Territory proposals where territory count significantly exceeds team size (ratio > 10:1) or where all states/provinces are given individual territories without verifying team size and account distribution.

---

## Anti-Pattern 7: Getting the Territory Type Priority Direction Backwards

**What the LLM generates:** "Set the Named Account territory type to priority 1 and the Geographic type to priority 10. Lower numbers have higher priority, so named-account opportunities will be assigned to the strategic rep's territory."

**Why it happens:** Almost every other ordered thing in Salesforce runs lowest-first — assignment rule entry order, escalation rule order, matching rule precedence, `sortOrder` on picklist values. The model generalises that convention onto a field where Salesforce documented the opposite, and the output sounds equally authoritative in either direction because nothing in it reveals which way was assumed.

**Correct pattern:**

```
Metadata API Developer Guide, Territory2Type > priority
(identical text in the Object Reference, Territory2Type > Priority):

  "The account-assigned territory whose territory type priority is HIGHEST is
   then assigned to the opportunity. The priority field value on each territory
   type must be unique. Further, if there are multiple territories with the same
   territory type (and therefore the same priority) assigned to the account,
   NO territory is assigned to the opportunity."

Three rules, not one:
  1. Highest integer wins.  Named Account = 40, Overlay = 30, Geo = 20.
  2. Every type's integer is UNIQUE. Two types sharing 20 is invalid.
  3. Two territories of the SAME type on one account -> the opportunity gets
     no territory at all, and drops out of every territory forecast silently.

Space the integers by 10 so a type can be inserted later without renumbering.
```

**Detection hint:** any output containing "lower integer", "lower number", "1 is the highest priority", or a priority table where the type described as winning carries the smallest value. Also flag any priority table whose values are not distinct, and any hybrid design that never states how two territories of the same type on one account are prevented.

---

## Anti-Pattern 8: Enumerating Criteria Past the Ten-Rule-Item Ceiling

**What the LLM generates:** "Create the EMEA territory rule with these criteria: BillingCountry equals GB, OR BillingCountry equals IE, OR BillingCountry equals DE, OR BillingCountry equals FR, OR BillingCountry equals NL, OR BillingCountry equals SE, OR BillingCountry equals ES, OR BillingCountry equals IT, OR BillingCountry equals PL, OR BillingCountry equals PT, OR BillingCountry equals DK, OR BillingCountry equals FI."

**Why it happens:** One condition per value is the shape most rule-builder examples take, and the ceiling lives in a one-sentence Usage note rather than a field description, so it rarely surfaces in training data. The generated design is unbuildable but reads as thorough.

**Correct pattern:**

```
Metadata API, Territory2Rule > Usage: "A territory rule can have up to
10 rule items."  A hard ceiling on the rule, not a performance hint.

Collapse the enumeration into ONE item:

  field      Account.BillingCountry
  operation  includes
  value      GB;IE;DE;FR;NL;SE;ES;IT;PL;PT;DK;FI

Two further constraints from the same section, both silent when broken:

  - "The sort order of rule items is implicitly derived from the position of
    the rule items in the XML."  Reordering items renumbers a booleanFilter.
  - booleanFilter numbering "must start at 1 and must be contiguous", so
    deleting item 2 from "(1 AND 2) OR 3" invalidates the filter rather than
    shifting the remaining numbers down.

If more than ten genuinely distinct predicates are needed, the requirement is
a proxy field on Account (e.g. Territory_Segment__c), not a longer rule.
```

**Detection hint:** count the rule items in any generated rule — more than ten is unbuildable, and more than about five repeated `equals` conditions on one field should have been a single `includes`. Also flag any generated `booleanFilter` whose numbering does not start at 1, skips a number, or references more items than the rule contains.
