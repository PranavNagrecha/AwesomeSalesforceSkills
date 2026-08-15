# Well-Architected — Decision Element

## Relevant Pillars

- **Reliability** — the failures in this domain are silent by construction. Null
  falls into the default, a superset outcome makes a later one dead code, a
  hardcoded Id stops matching after a sandbox refresh. None of them errors, so
  none of them surfaces until someone notices the wrong records in the wrong
  place.
- **Operational Excellence** — a named default outcome and a logged outcome
  identifier turn "why did this record go there" from an investigation into a
  query. The naming costs one field; the absence costs an afternoon each time.
- **Adaptable** — outcomes that differ only in a literal are data. Moving them
  into Custom Metadata converts a deploy-per-change into a data edit, which is
  the highest-leverage change available here and the one nobody reaches for
  first.

## Architectural Tradeoffs

- **Entry criteria vs a Decision:** entry criteria are cheaper — the interview
  never starts — and they do support `Is Changed`, on update-triggered flows
  under the "every time a record is updated" option. A Decision is required when
  the flow must also run on create, when the "only when updated to meet the
  condition requirements" trigger option is needed, or when the test belongs
  downstream. Prefer entry criteria where it fits; do not reach for a Decision on
  the mistaken belief that the operator is unavailable at the Start element.
- **One flat Decision vs nested Decisions:** a flat element with N outcomes is
  enumerable and reviewable; a tree of depth three has a default at every level
  and hides its uncovered combinations. Flat costs more outcome definitions and
  buys the ability to confirm coverage.
- **Formula resource vs inline conditions vs a pre-computed variable:** a formula
  reused across outcomes is evaluated at each reference, and inside a
  200-interview batch that arrives as CPU. An Assignment before the Decision
  computes once. Use the formula for cheap expressions, the variable for anything
  cross-object.
- **Branches vs Custom Metadata:** branches are visible on the canvas and require
  a deploy to change; a metadata-driven lookup is a data change with no deploy
  and moves the logic somewhere the canvas does not show. Prefer metadata once
  the outcomes enumerate values rather than express rules.
- **Decision-as-router vs Decision-with-inline-actions:** when each outcome
  triggers heavyweight work, splitting each into a subflow keeps the top-level
  flow readable as a routing table. It also multiplies the artifacts to version
  and deploy.

## Hygiene

- Every default outcome is named after the case it represents.
- Every nullable field referenced in a condition has an explicit null branch
  using `IsNull` with a boolean right-hand value.
- Outcomes are ordered most specific to widest, and each one answers "which
  record reaches this and not the one above it?"
- Every mixed AND/OR expression is parenthesised.
- Picklist comparisons use the API value, taken from the field's value set.
- No literal `005` or personal name anywhere in a condition.
- No Decision nested more than two deep.
- Expensive formulas are computed once into a variable before the Decision.

## Related

- `flow/recursion-and-re-entry-prevention` — the "changed and now equals X"
  pattern as a recursion guard, in depth.
- `flow/record-triggered-flow-patterns` — where entry criteria end and Decisions
  begin.
- `flow/flow-formula-and-expression-patterns` — formula cost and reuse.
- `flow/flow-element-naming-conventions` — naming outcomes so triage can read
  them.
- `flow/subflows-and-reusability` — extracting a decision domain.
- `admin/custom-metadata-driven-configuration` — moving a routing table out of
  branches.

## Official Sources Used

- Flow Operators in Decision, Wait, and Collection Filter Elements — text comparisons are case-insensitive for Text, Picklist, and Multi-Select Picklist values, except comparisons containing Salesforce Id values, which are case-sensitive; multi-select picklist operators treat the value as one string that happens to include semicolons; a set of operators is available only in Decision elements for evaluating `$Record` in a record-triggered flow — https://help.salesforce.com/s/articleView?id=platform.flow_ref_operators_condition.htm&type=5
- Define Conditions in a Decision or Wait Element — custom condition logic references conditions by number and supports parentheses, e.g. `1 AND (2 OR 3)` — https://help.salesforce.com/s/articleView?id=platform.flow_build_logic_conditions.htm&type=5
- How Entry Conditions Work in Record-Triggered Flows — https://help.salesforce.com/s/articleView?id=platform.automate_flow_build_working_with_conditions_record_triggered_flows.htm&type=5
- Decision Element — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_decision.htm&type=5
- Flow metadata type — `FlowDecision`, `FlowRule` (`name`, `conditionLogic`, `conditions`, `connector`, `label`), `FlowCondition` (`leftValueReference`, `operator`, `rightValue`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Per-Transaction Apex Governor Limits — the 10,000 ms synchronous CPU budget a batched flow's Decisions share — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Tips for Working with Picklist and Multi-Select Picklist Values — https://help.salesforce.com/s/articleView?id=sf.tips_for_using_picklist_formula_fields.htm&type=5
