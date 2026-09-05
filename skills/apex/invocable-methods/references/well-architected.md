# Well-Architected Notes — Invocable Methods

## Relevant Pillars

### Scalability

Invocable methods must remain bulk-safe even when the first Flow that uses them seems single-record.

Tag findings as Scalability when:
- queries or DML happen per input record
- the contract assumes one-request-at-a-time behavior
- wrapper shapes force multiple actions where one batch-safe action would do

### Operational Excellence

Well-designed invocable actions are understandable to Flow builders and easy to maintain.

Tag findings as Operational Excellence when:
- labels and descriptions are unclear
- the action contract is hard to evolve
- business logic is trapped inside the annotation class

### Reliability

Reliable actions expose predictable outcomes to their calling automations.

Tag findings as Reliability when:
- error behavior is ambiguous
- partial outcomes are needed but impossible to return
- invocable methods are hard to test or reuse

## Architectural Tradeoffs

- **Throwing exceptions vs returning structured results:** fail-fast simplicity versus richer orchestration behavior.
- **Simple parameter list vs wrapper DTOs:** fewer types initially versus long-term contract clarity.
- **Logic inline vs delegated to a service:** quicker start versus sustainable reuse.

## Anti-Patterns

1. **Single-record assumption in a list contract** — eventually fails at scale.
2. **Poor Flow-facing metadata** — builders cannot use the action confidently.
3. **Invocable class as business layer** — hard to reuse and evolve.

## Official Sources Used

- **Apex Developer Guide v67.0 (Summer '26) — "InvocableMethod Annotation", L5169–5474** — the
  whole contract this skill enforces: `public static` on an outer class (L5421), one annotated
  method per class (L5422), at most one input parameter (L5432), the permitted input and return
  types including generic `sObject` (L5433–5454), the six supported modifiers `label`,
  `description`, `callout`, `capabilityType`, `category`, `configurationEditor`, `iconName`
  (L5404–5417), the exception-handling rule (L5318–5319), and the size-and-order bulkification
  rule (L5456–5458). PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Developer Guide v67.0 — "InvocableVariable Annotation", L5488–5740** — the wrapper-field
  rules: which members may carry the annotation (L5718–5723), the permitted field data types
  (L5725–5729), case-sensitive name matching against the flow (L5731), `defaultValue` /
  `placeholderText` / `required` semantics including the `defaultValue`-with-`required` error
  (L5656–5693), managed-package visibility (L5732–5735), and the API 66.0 no-argument-constructor
  requirement (L5737–5739).
- **Apex Developer Guide v67.0 — "Making Callouts to External Systems from Invocable Actions",
  L26866–26880** — the three conditions under which a screen flow commits and starts a new
  transaction for a `callout=true` action, and the three under which it does not. This is the
  source for the gotcha that `callout=true` changes nothing in a record-triggered flow, and for
  the `System.CalloutException` message text at L8768–8769.
- **Apex Developer Guide v67.0 — "Execution Governors and Limits", L19540–19566** — the budget the
  action's bulk claim is measured against: 100 SOQL queries and 150 DML statements per synchronous
  transaction (L19544, L19554), 100 callouts with a 120-second cumulative timeout (L19563, L19565).
  These are the numbers the test class in `references/code-examples.md` §4 asserts against.
- **Metadata API Developer Guide v67.0 (Summer '26) — `FlowActionCall`, L68455–68540, and
  `FlowDataTypeMapping`, L70177–70203** — the flow-side half of the contract: `actionType` `apex`
  (L68604), `faultConnector` (L68479), the required `flowTransactionModel` with its
  `Automatic` / `CurrentTransaction` / `NewTransaction` values (L68479–68487), and the `T__` / `U__`
  data-type mappings that bind a generic-`sObject` action to a concrete type (L70192–70203).
  PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **REST API Developer Guide v67.0 (Summer '26) — "Invocable Actions Custom", L13610–13840** — the
  `/services/data/vXX.X/actions/custom/apex` resource used for verification, the primitive-only
  input restriction on the POST path (L13767–13779), the profile-access requirement (L13780), and
  the warning that removing the annotation from a class already wired into a flow produces a
  runtime error (L13781–13782).
- **Apex Reference Guide v67.0 (Summer '26) — `Invocable.Action` and `Invocable.Action.Result`,
  L160640–162600** — calling standard and custom actions from Apex: `createCustomAction` /
  `createStandardAction` (L160797–160913), `invoke()` returning `List<Invocable.Action.Result>`
  (L160993–160997), the `isSuccess()` / `getErrors()` / `getOutputParameters()` result surface
  (L162561–162573), and the explicit performance warning on `getDescribe()` (L160648–160652).
- **Salesforce Well-Architected** — the Scalability, Reliability and Operational Excellence framing
  used to tag findings in the sections above.
