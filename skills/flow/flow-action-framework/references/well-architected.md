# Well-Architected Notes — Flow Action Framework

## Relevant Pillars

- **Security** — Apex actions run in the running user’s context unless documented otherwise for the specific pattern; class access, CRUD, and FLS still matter. UNVERIFIED (2026-09-05): "runs in the running user's context" is not a phrase either guide applies to invocable Apex — Apex sharing is governed by the class's `with sharing` / `without sharing` / `inherited sharing` declaration, and the flow-level control is `Flow.runInMode` (`api_meta.txt` L68374-68390), not a property of the action. What *is* grounded is the access gate: "If a flow invokes Apex, the running user must have the corresponding Apex class security set in their user profile or permission set" (`apexdev.txt` L5172-5173). Prefer least-privilege permission sets and explicit sharing design on the Apex side (`invocable-methods`).

- **Performance** — Choosing looped Apex versus one bulk invocable changes CPU and DML consumption dramatically in record-triggered automation. Standard actions often optimize common data operations compared with naive Apex.

- **Scalability** — List-shaped invocable contracts align with bulkified Flow interviews; designs that ignore batch size do not scale with data volume.

- **Reliability** — Fault connectors, structured error results, and clear subflow contracts reduce silent failures and improve operability.

- **Operational Excellence** — Action choice (standard vs subflow vs Apex) directly impacts who can maintain the automation (admins vs developers) and how changes are reviewed in CI.

## Architectural Tradeoffs

Subflows improve **Operational Excellence** and **Reliability** through encapsulation but add indirection when debugging a long interview. Apex actions maximize flexibility for **Performance**-sensitive or complex logic at the cost of **Operational Excellence** (code reviews, tests). Standard actions optimize for admin readability and platform-supported semantics until they hit a capability ceiling. External Service actions trade spec maintenance for typed integration—see `flow-external-services` when the boundary is HTTP, not Apex.

## Anti-Patterns

1. **Apex as default** — Using custom invocables for operations with first-class Flow actions increases cost and security review surface without benefit.

2. **Hidden bulk** — Assuming screen-style single-record behavior for paths that can run bulk; causes intermittent governor and data correctness issues.

3. **Leaky subflow contracts** — Exposing ten rarely used optional outputs instead of a small stable contract makes parent flows brittle.

## Official Sources Used

Summer '26 / v62 PDF extractions read directly for this revision, with the claim each one
supports:

- **Metadata API Developer Guide — `FlowActionCall` field table** (`api_meta.txt`
  L68455-68549): `actionName` / `actionType` / `flowTransactionModel` are the three
  `Required` fields; `faultConnector` vs `timeoutConnector`; `storeOutputAutomatically`
  defaults to `false`; `dataTypeMappings`; `nameSegment` / `versionSegment` deprecated in
  API 62.0; `isWaitUntilCompleted` / `offset` / `timeoutPathUsage`.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Metadata API Developer Guide — `InvocableActionType` enumeration** (`api_meta.txt`
  L68551-69010): the action-family taxonomy in `SKILL.md` — `apex`, `chatterPost`,
  `component`, `emailAlert`, `emailSimple`, `externalService`, `flow`, `lwcComponent`,
  `quickAction`, `submit`, `rpa`, and the vertical blocks. Also the constraint that `flow`
  is unavailable from a `processType` of `Flow` or `AutolaunchedFlow` (L68749-68753).
- **Metadata API Developer Guide — `FlowSubflow`, `FlowDataTypeMapping`,
  `FlowApexPluginCall`, `FlowTest`** (`api_meta.txt` L72625-72685, L70177-L70203,
  L69680-69702, L73959-74100, L74140-74203): the subflow field set (no `faultConnector`);
  the `T__` / `U__` prefix rule; the legacy Apex plug-in element; FlowTest's `Start` /
  `Finish`-only test points and `WithAssertion` `testType`.
- **Metadata API Developer Guide — `InvocableActionExtension`** (`api_meta.txt`
  L81893-82160): API 65.0+, the four `targetType` values, the standard `key` list
  (`CpeName`, `ConfiguredBy`, `ControllingField`, `CustomHeaderLwcName`, `GroupName`,
  `Order`, `ProvidedValueList`), and the `__c` custom-key rule in API 67.0+.
- **Metadata API Developer Guide — `ExternalServiceRegistration`** (`api_meta.txt`
  L64002-64110): `registrationProviderType` `SchemaInferred` is "the API specification…
  provided during the HTTP Callout configuration process" — the grounding for treating an
  HTTP Callout action as a registration plus a Named Credential, not its own type.
- **Apex Developer Guide — `InvocableMethod` annotation and its considerations**
  (`apexdev.txt` L5169-5470): `label` defaults to the method name, `category` defaults to
  Uncategorized, `configurationEditor` registers a CPE; "Only one method in a class can
  have the InvocableMethod annotation" (which is why `actionName` is a class name); "Only
  global invocable methods appear in Flow Builder… in the subscriber org".
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Developer Guide — "Making Callouts to External Systems from Invocable Actions"**
  (`apexdev.txt` L26877-26895): the three-condition, screen-flow-only gate that decides
  whether the platform commits and starts a new transaction — the reason
  `flowTransactionModel` is the lever outside screen flows.
- **Apex Developer Guide — "Extend Invocable Action Configuration in Flow Builder"**
  (`apexdev.txt` L26888-27253): the `.invocableactionextension-meta.xml` suffix and
  `invocableactionextensions` directory, the all-or-nothing `Order` rule, the 500-value
  picklist cap, and the `apex://` dynamic-picklist URI.
- **Apex Developer Guide — "Passing Data to a Flow Using the `Process.Plugin` Interface"**
  (`apexdev.txt` L27257-27330): legacy Apex actions are free-form-only in Flow Builder, do
  not support Blob / Collection / sObject types or bulk, and are callable only from flows.
- **REST API Developer Guide — Invocable Actions resources** (`api_rest.txt`
  L13600-14080): `/actions`, `/actions/custom`, `/actions/standard` as the action
  catalogue; describe respects Apex class profile access; removing `@InvocableMethod`
  from a class already wired into a flow is a *runtime* error; `emailAlert` consumes the
  workflow email allocation; and the six action families whose referenced components are
  not auto-packaged.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- **Lightning Web Components Developer Guide — flow local actions** (`lwc_guide.txt`
  L8805-8875, pages `use-flow-local-actions`, `use-flow-js-actions`,
  `use-flow-cancel-async-request`): `lightning__FlowAction` target, screen-flow-only
  because a browser context is required, the 120-second default timeout, and the fault
  connector / `$Flow.FaultMessage` behaviour on `reject()`.

Reference material kept from the previous revision (URLs only; not re-read for this
revision):

- Flow Reference (Help) — action inventory, Flow element reference, and runtime behavior for Flow features: https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- Flow Builder (Help) — authoring and element palette concepts: https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Apex Developer Guide — `@InvocableMethod` annotation (method shape, visibility, Flow exposure rules): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm
- Apex Developer Guide — `@InvocableVariable` annotation (Flow-visible field metadata on wrapper types): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableVariable.htm
- Apex Developer Guide — callouts from invocable actions (transaction rules when Flow invokes Apex that calls out): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_forcecom_flow_invocable_action_callout.htm
- Metadata API Developer Guide — metadata shape for deployments that include Flow and Apex: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — quality framing for automation boundaries and operability: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
