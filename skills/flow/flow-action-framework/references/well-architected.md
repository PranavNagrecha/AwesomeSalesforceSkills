# Well-Architected Notes — Flow Action Framework

## Relevant Pillars

- **Security** — Apex actions run in the running user’s context unless documented otherwise for the specific pattern; class access, CRUD, and FLS still matter. Prefer least-privilege permission sets and explicit sharing design on the Apex side (`invocable-methods`).

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

- Flow Reference (Help) — action inventory, Flow element reference, and runtime behavior for Flow features: https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- Flow Builder (Help) — authoring and element palette concepts: https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Apex Developer Guide — `@InvocableMethod` annotation (method shape, visibility, Flow exposure rules): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm
- Apex Developer Guide — `@InvocableVariable` annotation (Flow-visible field metadata on wrapper types): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableVariable.htm
- Apex Developer Guide — callouts from invocable actions (transaction rules when Flow invokes Apex that calls out): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_forcecom_flow_invocable_action_callout.htm
- Metadata API Developer Guide — metadata shape for deployments that include Flow and Apex: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — quality framing for automation boundaries and operability: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
