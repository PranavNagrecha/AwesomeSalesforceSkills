# LLM Anti-Patterns — Sales Cloud Architecture

Common mistakes AI coding assistants make when generating or advising on Sales Cloud Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Process Builder for New Automations

**What the LLM generates:** Architecture diagrams that include Process Builder as the automation tool for Opportunity stage-change logic or Lead assignment workflows.

**Why it happens:** LLM training data includes years of Salesforce documentation and blog posts from 2015-2022 when Process Builder was the recommended declarative tool. The model defaults to the pattern it has seen most frequently, even though Salesforce officially deprecated Process Builder in Spring '22 and recommends Record-Triggered Flows.

**Correct pattern:**

```text
WRONG:  "Use a Process Builder on Opportunity to update fields when Stage changes"
RIGHT:  "Use a Before-Save Record-Triggered Flow on Opportunity to update fields when Stage changes"
```

**Detection hint:** Search output for "Process Builder" — any new architecture recommendation should use Flow instead.

---

## Anti-Pattern 2: Ignoring Order of Execution in Automation Recommendations

**What the LLM generates:** Architecture recommendations that place a validation rule, a before-save Flow, and an Apex before-trigger on the same object without acknowledging their execution order or cumulative governor limit impact.

**Why it happens:** LLMs treat each automation as an independent unit and do not model the Salesforce order of execution where all automations on an object fire within a single transaction. The model lacks the concept of "transaction budget" that architects must manage.

**Correct pattern:**

```text
WRONG:  "Add a validation rule for Amount, a Flow for Stage defaults, and a trigger for discount calculation on Opportunity"
RIGHT:  "Opportunity before-save execution budget:
         1. Validation rules (system) — Amount > 0
         2. Before-save Flow (single) — Stage defaults + discount flagging
         3. Before-trigger (single dispatcher) — complex discount calculation
         Combined query estimate: 3 SOQL / Combined DML: 0 (before-save)"
```

**Detection hint:** If the recommendation places 3+ automations on one object without mentioning order of execution or governor limits, flag it.

---

## Anti-Pattern 3: Suggesting Direct Synchronous Callouts from Triggers

**What the LLM generates:** Apex trigger code that makes HTTP callouts directly inside the trigger execution context (e.g., calling an ERP API from an Opportunity after-update trigger).

**Why it happens:** LLMs generate patterns from general web-development training where synchronous API calls from event handlers are standard. The model does not internalize that Salesforce prohibits callouts from synchronous trigger context and that even @future callouts from triggers create tight coupling.

**Correct pattern:**

```text
WRONG:  "In the Opportunity after-update trigger, call the ERP API to create an order"
RIGHT:  "In the Opportunity after-update trigger, publish a SalesEvent__e Platform Event.
         A separate Platform Event trigger subscriber makes the ERP callout asynchronously.
         This decouples the save transaction from ERP availability."
```

**Detection hint:** Search for "callout" or "HTTP" within trigger context recommendations. Any callout in a trigger should use @future, Queueable, or Platform Events.

---

## Anti-Pattern 4: Treating Territory Management as Simple Field Assignment

**What the LLM generates:** Architecture that assigns territories by writing a Territory__c text field on Account or Opportunity, then using sharing rules based on that field value.

**Why it happens:** LLMs simplify Territory Management to a field-based filter because training data contains many blog posts showing custom territory fields. The model does not distinguish between custom field tagging and Enterprise Territory Management, which is a platform feature with its own data model (Territory2, UserTerritory2Association, ObjectTerritory2Association), forecast integration, and sharing engine.

**Correct pattern:**

```text
WRONG:  "Add a Territory__c picklist field to Account and use sharing rules to control access per territory"
RIGHT:  "Enable Enterprise Territory Management. Define territory types and models in Setup.
         Use rule-based assignment on Account (Billing Country, Industry, Annual Revenue).
         Territory sharing is managed by the platform — no custom sharing rules needed.
         Forecasts roll up through the territory hierarchy automatically."
```

**Detection hint:** If the architecture mentions a custom "Territory" field for access control without referencing Enterprise Territory Management, flag it as oversimplified.

---

## Anti-Pattern 5: Hallucinating Sales Cloud APIs or Objects

**What the LLM generates:** References to nonexistent objects like `SalesForecast__c`, `PipelineStage__c`, or APIs like `ForecastingService.recalculate()`. May also reference `OpportunityHistory` as a queryable object with full field access when it is actually limited to specific tracked fields.

**Why it happens:** LLMs interpolate object and API names from naming conventions rather than referencing the actual Salesforce Object Reference. "SalesForecast" sounds like a plausible standard object name. The model confuses standard objects with custom objects from specific customer implementations seen in training data.

**Correct pattern:**

```text
WRONG:  "Query SalesForecast__c to get the current quarter forecast"
RIGHT:  "Query ForecastingItem (API) or use the Forecasting REST API at
         /services/data/vXX.0/forecasting/quota to access forecast data.
         Standard objects: ForecastingQuota, ForecastingItem, ForecastingAdjustment."
```

**Detection hint:** Cross-reference any object or API name against the Salesforce Object Reference. If it is not in the standard object list and does not end with `__c` (custom) or `__e` (platform event), it is likely hallucinated.

---

## Anti-Pattern 6: Recommending Workflow Rules Alongside Flows

**What the LLM generates:** Architecture that mixes Workflow Rules and Record-Triggered Flows on the same object, often using Workflow Rules for email alerts and Flows for field updates.

**Why it happens:** Training data spans the full history of Salesforce automation tools. The model does not apply the current platform guidance that Workflow Rules should be migrated to Flows and should not coexist with Flows on the same object due to order-of-execution complexity.

**Correct pattern:**

```text
WRONG:  "Use a Workflow Rule for the close-date email alert and a Flow for the stage-change field update"
RIGHT:  "Consolidate all automation into the Record-Triggered Flow. Use a Send Email action
         within the Flow for the close-date alert. Migrate the existing Workflow Rule."
```

**Detection hint:** If the output mentions "Workflow Rule" for any new automation, flag it. New architectures should use Flows exclusively for declarative automation.

---

## Anti-Pattern 7: Underestimating Lead Conversion Complexity

**What the LLM generates:** Architecture diagrams that show lead conversion as a simple arrow from Lead to Opportunity without acknowledging the multi-object transaction, field mapping requirements, or Person Account variations.

**Why it happens:** LLMs treat lead conversion as a single-step operation because most documentation describes it at a high level. The model does not account for the fact that conversion is a compound DML operation touching up to four objects with complex field-mapping rules and governor-limit implications.

**Correct pattern:**

```text
WRONG:  "Leads are converted to Opportunities using the standard conversion process"
RIGHT:  "Lead conversion is a single-transaction operation that:
         1. Updates Lead (Status = Converted)
         2. Creates or matches Account (with field mapping from Lead)
         3. Creates or matches Contact (with field mapping from Lead)
         4. Optionally creates Opportunity
         All triggers on all four objects fire within one governor limit envelope.
         Person Account orgs follow a different path (Account only, no Contact).
         Custom field mappings must be configured in Setup > Lead > Fields > Map Lead Fields."
```

**Detection hint:** If lead conversion is described without mentioning multi-object transaction scope or field mapping configuration, the recommendation is incomplete.
