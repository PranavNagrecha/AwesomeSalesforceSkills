---
name: business-rules-engine
description: "Use when designing, building, or troubleshooting OmniStudio Business Rules Engine (BRE) artifacts: Decision Tables, Decision Matrices (rule matrices), and Expression Sets used for eligibility determination, pricing, discounting, or any complex multi-attribute rule evaluation. Trigger keywords: 'business rules engine', 'BRE', 'decision table', 'rule matrix', 'eligibility determination', 'ExpressionSetService', 'expression set evaluate'. NOT for Flow decision elements or Flow-based branching logic (use flow/* skills). NOT for Calculation Procedures that do not involve multi-condition rule lookup (use omnistudio/calculation-procedures). Requires Industries Cloud license."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
tags:
  - business-rules-engine
  - decision-table
  - expression-sets
  - omnistudio
  - eligibility
  - industries-cloud
triggers:
  - how do I build eligibility determination rules in OmniStudio without writing code
  - decision table is not returning the right outcome for my input values
  - how do I call a Business Rules Engine expression set from an Integration Procedure or Apex
  - how do I version and activate BRE rules so old and new rule sets coexist
  - BRE rule matrix returns null or wrong value at runtime
inputs:
  - "Business rule requirements: conditions, operators, input attributes, and expected outcomes"
  - "Existing Decision Table or Expression Set metadata if reviewing or troubleshooting"
  - "Integration context: whether caller is an Integration Procedure, OmniScript, or Apex"
  - "Versioning requirements: effective dates, rollback plan, and parallel version strategy"
outputs:
  - "Decision Table column definition, condition rows, and activation plan"
  - "Expression Set structure with condition groups, operators, and output mappings"
  - "Review findings covering activation status, version gaps, and input-attribute mismatches"
  - "Runtime invocation pattern for Integration Procedure callout or Apex ExpressionSetService"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Business Rules Engine

Use this skill when designing or troubleshooting OmniStudio Business Rules Engine (BRE) artifacts — Decision Tables, Decision Matrices, and Expression Sets — for eligibility determination, product qualification, pricing, or any multi-attribute conditional logic that must be managed by business analysts without deployments. This skill is distinct from Calculation Procedures, which perform sequential math; BRE is for rule-based lookup and eligibility evaluation.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has an Industries Cloud license (Communications, Media, Energy, Financial Services, Health, or similar). BRE is not available in core Salesforce without this license.
- Identify which BRE artifact type is appropriate: Decision Table (row-based rule matching with explicit condition rows), Decision Matrix (column-based lookup table), or Expression Set (complex boolean condition group with AND/OR operators). These are not interchangeable.
- Confirm how the rule will be called at runtime: from an Integration Procedure (Action element of type BRE), from OmniScript (via Integration Procedure), or directly from Apex using `ExpressionSetService.evaluate()`. The invocation path determines input/output variable naming conventions.
- Clarify versioning requirements upfront. BRE artifacts support multiple versions; only one version can be active at a time per artifact. If the business needs parallel versioning (e.g., A/B or future-effective), understand that now.
- Verify API version: Decision Tables and Expression Sets were significantly expanded in API v55.0 (Summer '22) and further in v60.0+. Metadata type names differ from UI labels — always confirm the deployed metadata type name.

---

## Core Concepts

### Decision Tables

A Decision Table is a rule-based lookup artifact. It consists of a set of condition columns (input attributes) and output columns (outcomes). Each row defines one rule: when all condition columns for that row match the provided inputs, the output columns for that row are returned.

Decision Tables use an operator per condition column (Equals, Not Equals, In, Not In, Range, etc.). Rows are evaluated in priority order; the first matching row wins. If no rows match, the table returns null or a default output row if one is configured.

The underlying metadata type is `DecisionTable`, with rows stored as `DecisionTableRow` and column definitions in `DecisionTableColumn`. Decision Tables are versioned — each version is independent, and only one version can be active at a time. The platform metadata file extension is `.decisionTable-meta.xml`.

Decision Tables are best suited for discrete lookup scenarios: product eligibility matrices, discount tier lookups, geographic rate tables, and similar flat rule sets. They are not suited for complex nested boolean logic — use Expression Sets for that.

### Expression Sets

An Expression Set (`ExpressionSet` metadata type) defines a tree of condition groups and conditions evaluated with AND/OR operators. The result is a boolean or a computed output value depending on configuration. Expression Sets are used for eligibility scoring, approval threshold checks, and discount qualification where the logic is a combination of conditions rather than a simple row lookup.

Expression Sets support nested condition groups (a group can contain sub-groups), making it possible to express `(A AND B) OR (C AND NOT D)` logic that cannot be captured in a flat decision table. An Expression Set version (`ExpressionSetVersion`) must be activated before it can be called. Expression Sets can call Decision Tables internally as lookup sources.

The API invocation surface for Expression Sets is `ExpressionSetService.evaluate(expressionSetApiName, inputMap)` in Apex, or the REST endpoint `POST /connect/business-rules/expression-sets/{expressionSetApiName}/actions/evaluate`.

### Versioning and Activation

All BRE artifacts (Decision Tables and Expression Sets) use a versioning model:

- Each definition (e.g., `ProductEligibilityRules`) can have multiple versions numbered sequentially.
- Only one version can be in `Active` status at a time per definition.
- Activating a new version automatically deactivates the previously active version.
- Versions in `Draft` or `Inactive` status are never called at runtime — the platform always resolves to the single active version.
- BRE does not support date-effective version selection (unlike Calculation Matrices). To manage future-effective rules, coordinate activation timing manually or use a wrapper that routes to different rule sets by date.

Metadata deployment promotes the version definition but does not activate it automatically. Post-deployment activation must be performed via the BRE UI or via the Connect API PATCH endpoint.

### Runtime Execution

BRE rules are synchronous and execute within the current transaction context. Two primary invocation paths exist:

1. **Integration Procedure (IP) callout action** — Add an Action element of type `BusinessRules` or `DecisionTable` in the IP step palette. Pass input attributes as the action's input JSON. Map output JSON back to IP variables. This is the most common pattern for OmniScript-driven journeys.

2. **Apex invocation** — Use `BusinessRules.ExpressionSetService.evaluate(String expressionSetName, Map<String, Object> inputs)` for programmatic calls. The return type is `Map<String, Object>` containing the output attribute values. This path is used in trigger-based eligibility checks or batch reprocessing.

Regardless of invocation path, input attribute names are case-sensitive and must exactly match the column or condition attribute API names defined in the BRE artifact.

---

## Common Patterns

### Pattern 1: Product Eligibility Decision Table

**When to use:** When a product or service is available only when a set of conditions are simultaneously true — for example, a broadband product that requires a service area code, a credit tier, and an account type match.

**How it works:**
1. Define the Decision Table with one condition column per eligibility attribute (`ServiceArea`, `CreditTier`, `AccountType`) and one output column (`IsEligible` = true/false, or `EligibleProductCode`).
2. Add a row for each valid combination. Use `In` operator for multi-value columns instead of repeating rows.
3. Add a default row (all conditions blank) returning `IsEligible = false` to handle unmatched inputs without returning null.
4. Create version 1, populate rows, and activate the version.
5. In the Integration Procedure that drives the OmniScript journey, add a BusinessRules action element. Pass context attributes as inputs. Map the output `IsEligible` to an IP variable.
6. In the OmniScript, add a Condition Step reading the IP variable to branch the journey.

**Why not a Flow Decision element:** A Flow Decision requires a developer deployment for every rule change. A Decision Table lets a business analyst update rows via the BRE UI with no deployment.

### Pattern 2: Complex Eligibility with Expression Set Condition Groups

**When to use:** When eligibility depends on nested boolean logic — for example, an insurance quote is eligible if `(age >= 18 AND state IN ['CA','TX']) OR (age >= 21 AND hasExistingPolicy = true)`.

**How it works:**
1. Create an Expression Set definition for `QuoteEligibility`.
2. In version 1, create two condition groups at the top level joined by OR.
3. Group 1: add conditions `age >= 18` AND `state IN ['CA','TX']`.
4. Group 2: add conditions `age >= 21` AND `hasExistingPolicy = true`.
5. Set the Expression Set output to return a boolean result or an eligibility score.
6. Activate the version.
7. Call from Apex: `BusinessRules.ExpressionSetService.evaluate('QuoteEligibility', new Map<String, Object>{'age' => 25, 'state' => 'CA', 'hasExistingPolicy' => false})`.
8. Inspect the return map for the output attribute key.

**Why not a decision table:** A flat decision table cannot represent `(A AND B) OR (C AND D)` without exploding into a combinatorial row set. Expression Sets handle nested boolean logic cleanly.

### Pattern 3: Versioned Rule Rollout with Parallel Draft

**When to use:** When the business wants to author next-quarter rules while current rules remain live in production.

**How it works:**
1. Keep the current version active in production.
2. Create version 2 in Draft status. Authors can edit draft rows without affecting runtime.
3. Test version 2 using the BRE Test tab (provide sample inputs and verify expected outputs).
4. Deploy version 2 metadata to production (metadata deploy does not activate).
5. On the go-live date, activate version 2 via the BRE UI or via a Connect API PATCH call. The platform deactivates version 1 automatically.
6. Keep version 1 in Inactive status for rollback reference.

**Why not deploy-and-activate in one step:** Separating deploy from activation allows business sign-off in production data before go-live, reducing risk.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Flat rule lookup with discrete input combinations | Decision Table | Row-based evaluation is fast, auditable, and business-analyst-editable |
| Nested AND/OR eligibility logic | Expression Set with condition groups | Supports arbitrary boolean trees; Decision Tables cannot represent nested logic |
| Rules change frequently without IT involvement | BRE Decision Table or Expression Set | Business analysts manage rules in UI with no deployment required |
| Need to call rules from Apex trigger or batch job | Apex `ExpressionSetService.evaluate()` | Direct synchronous Apex call; no HTTP overhead |
| Need to call rules from OmniScript journey | Integration Procedure with BusinessRules action | IP manages input/output mapping and context variable passing |
| Future-effective rule version needed | Draft version + manual activation on go-live date | BRE does not support date-effective activation; activation is manual |
| Rule has > 500 rows | Consider splitting into multiple Decision Tables by a primary key | Large tables have no hard limit but degrade lookup performance; partition by a high-cardinality key |
| Rule returns wrong value after activation | Check input attribute name case sensitivity and verify only one version is Active | Most runtime mismatches are attribute name case or stale version activation |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on BRE design:

1. **Gather requirements** — Document input attributes (names, data types, valid values), expected outputs, operator requirements (range vs. equals vs. set membership), and frequency of rule changes. Confirm Industries license and org API version.
2. **Choose artifact type** — Use the Decision Guidance table to select Decision Table, Expression Set, or a combination. Document the choice and reasoning.
3. **Design the schema** — Define column names (these become the input attribute API names used at runtime), data types, operators, and output column names. Use snake_case or camelCase consistently — names are case-sensitive at runtime.
4. **Build and populate** — Create the artifact in the BRE designer or via metadata deploy. Add all rows/conditions. Add a default/fallback row for unmatched inputs if appropriate.
5. **Test in BRE UI** — Use the built-in Test tab to run sample inputs including boundary cases and confirm expected outputs before activating.
6. **Activate** — Activate the version via the BRE UI or Connect API. Verify only one version is Active. Do not activate in production without prior testing in a lower environment.
7. **Integrate and validate end-to-end** — Wire the BRE artifact into the Integration Procedure or Apex caller. Run end-to-end tests through the consuming OmniScript or process. Confirm attribute name alignment and output mapping.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Only one version of each BRE artifact is in Active status
- [ ] All input attribute names in the IP action or Apex call exactly match the column/condition API names in the BRE artifact (case-sensitive)
- [ ] A default or fallback row exists for Decision Tables to handle unmatched inputs without returning null
- [ ] BRE Test tab has been used with representative inputs including boundary values and confirmed expected outputs
- [ ] The artifact was tested in a non-production environment before production activation
- [ ] Output attribute names returned by the rule are correctly mapped to downstream IP variables or Apex variables
- [ ] Versioning strategy is documented: which version is active, what version 2+ contains, and rollback procedure
- [ ] Industries Cloud license confirmed on target org

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Attribute name case sensitivity causes silent null returns** — Decision Table column API names and Expression Set condition attribute names are case-sensitive. If the IP or Apex caller passes `creditTier` but the column is defined as `CreditTier`, the lookup receives null for that input and may match the wrong row or return no result. There is no runtime error — the mismatch is silent.

2. **Activating a new version in UI does not deploy it to other orgs** — BRE activations made through the UI are data-layer changes (record updates), not metadata changes. A metadata `retrieve/deploy` cycle captures version content but not the activation flag. Teams that rely solely on metadata deployment will find that versions arrive in production as Draft and must be activated post-deploy. Build a post-deployment activation step into the release process.

3. **No date-effective version selection in BRE Decision Tables** — Unlike Calculation Matrices, Decision Tables and Expression Sets do not support date-effective version ranges. There is one active version at any given time. If future-effective rules are required, you must manually activate on the go-live date or build a wrapper Integration Procedure that routes to different rule artifacts by date.

4. **Decision Table row evaluation stops at first match** — Rows are evaluated in priority order and execution stops when a match is found. If two rows could both match a given input (overlapping condition ranges or values), only the higher-priority row is returned. Overlapping rows that should have different outcomes is a common authoring error that is not flagged in the UI.

5. **Expression Set outputs are untyped `Object` in Apex return map** — `ExpressionSetService.evaluate()` returns `Map<String, Object>`. All output values are `Object` type and require explicit casting. Casting a numeric output to `String` or a boolean output to `Decimal` will throw a `TypeException` at runtime. Always cast defensively using `instanceof` or a try/catch.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Decision Table column definition | Input column names, data types, operators, and output column names — the schema used by both the BRE designer and the runtime caller |
| Expression Set structure | Condition groups, operator tree (AND/OR nesting), condition attribute names, and output definition |
| Versioning plan | Which version is active, what is in draft, effective date for planned activation, and rollback procedure |
| Integration Procedure wiring notes | Action element type, input attribute mapping, output variable mapping, and error handling strategy |
| BRE test case set | Sample inputs covering happy path, boundary values, and unmatched inputs with expected outputs |

---

## Related Skills

- **omnistudio/calculation-procedures** — Use when the task is sequential math (tiered pricing arithmetic, multi-step formula chains) rather than rule-based eligibility lookup. Calculation Procedures and BRE are complementary: a Calculation Procedure can call a Decision Table Lookup step internally.
- **omnistudio/integration-procedures** — Use when the BRE rule needs to be wired into a larger orchestration that reads Salesforce data, calls external systems, or drives an OmniScript journey.
- **omnistudio/omniscript-design-patterns** — Use when the BRE output drives branching or UI state in an OmniScript.
