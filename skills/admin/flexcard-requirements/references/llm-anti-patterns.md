# LLM Anti-Patterns — FlexCard Requirements

Common mistakes AI coding assistants make when generating or advising on FlexCard requirements. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating FlexCard Requirements with Dashboard/Report Requirements

**What the LLM generates:** A "dashboard widget" specification listing data fields, chart types, and filter controls — using Lightning Dashboard or Tableau-style terminology instead of FlexCard-native concepts (data source types, action types, card state conditions).

**Why it happens:** LLMs associate "card" with standard Lightning dashboard components or generic web card widgets. FlexCard-specific structure (five data source types, five action types, card state templates compiled to LWC) is not the dominant "card" pattern in training data.

**Correct pattern:**
```
FlexCard requirements must specify:
- Data source type (SOQL / Apex / DataRaptor / Integration Procedure / Streaming)
- Action type for each user action (Navigation / OmniScript Launch / Apex / DataRaptor / Custom LWC)
- Card state template conditions (e.g., Status__c == 'Active' / Status__c == 'Cancelled')
```

**Detection hint:** Requirements output uses terms like "chart type," "filter control," "report source," or "widget" without FlexCard-specific data source and action type vocabulary.

---

## Anti-Pattern 2: Recommending SOQL for All Data Fields Without Assessing Aggregation Needs

**What the LLM generates:** A requirements document that specifies SOQL as the data source for all fields, including aggregated, computed, or external-API-sourced fields.

**Why it happens:** SOQL is the most familiar Salesforce data retrieval mechanism and LLMs default to it. They do not distinguish between fields that can be retrieved by direct SOQL and fields that require Integration Procedure orchestration or Apex computation.

**Correct pattern:**
```
Data source selection matrix:
- Direct Salesforce object fields → SOQL
- Simple remapped fields from a single object → DataRaptor
- Aggregated counts, multi-object joins, computed fields → Integration Procedure
- External API data → Integration Procedure with HTTP Action
- Real-time streaming data → Streaming data source
```

**Detection hint:** All data fields in requirements point to "SOQL" with no IP or Apex data sources, even for fields that are clearly aggregated or computed.

---

## Anti-Pattern 3: Omitting Card State Template Conditions

**What the LLM generates:** Requirements that describe "show different layout for different statuses" but don't enumerate the states, their condition expressions, or their layout differences.

**Why it happens:** LLMs treat conditional display as a straightforward UI concern and assume the developer will figure out the state template logic. They don't model that FlexCard state templates are compiled at activation time and require explicit condition expressions.

**Correct pattern:**
```
Card state templates must be enumerated with:
- State name
- Condition expression (e.g., {Status__c} == 'Active')
- Elements visible in this state
- Elements hidden or different from other states
Note: State templates compile to LWC at activation — all states must be defined before build.
```

**Detection hint:** Requirements mention "conditional layout" or "status-based view" without listing state names and condition expressions.

---

## Anti-Pattern 4: Omitting Build Dependency Order for Nested FlexCards

**What the LLM generates:** A requirements document that specifies a parent FlexCard embedding child FlexCards without noting that child cards must be activated before the parent card can be activated.

**Why it happens:** LLMs don't model Salesforce's component activation dependency model. They treat nested component requirements as standard component composition without noting the activation sequence constraint.

**Correct pattern:**
```
Build and activation dependency order:
1. Activate child FlexCard: ChildOrderLineCard
2. Activate Integration Procedure: GetOrderSummaryIP
3. Activate parent FlexCard: OrderSummaryCard (depends on 1 and 2)
```

**Detection hint:** Requirements include nested FlexCard references but have no build dependency sequence or activation order section.

---

## Anti-Pattern 5: Confusing Requirements Gathering (This Skill) with Implementation (Card Designer)

**What the LLM generates:** A requirements document that includes Card Designer configuration instructions, JSON condition syntax for direct entry in Card Designer, or developer instructions for wiring data bindings — blurring the line between BA requirements and developer implementation.

**Why it happens:** LLMs conflate the BA requirements phase with the developer implementation phase. When asked for FlexCard requirements, they jump to implementation details (how to configure in Card Designer) rather than producing stakeholder-readable requirements artifacts.

**Correct pattern:**
```
FlexCard requirements document (this skill) is a pre-build BA artifact:
- Written for stakeholder review and developer handoff
- Specifies WHAT is needed (data fields, actions, states) not HOW to configure it
- Does not include Card Designer JSON, element configuration steps, or developer instructions
Implementation (how to configure in Card Designer) belongs in omnistudio/flexcard-design-patterns skill.
```

**Detection hint:** Requirements document includes Card Designer configuration steps, element properties, or JSON condition syntax formatted as developer instructions rather than stakeholder-readable requirements.
