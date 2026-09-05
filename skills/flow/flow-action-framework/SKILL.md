---
name: flow-action-framework
description: "Use when designing or troubleshooting Salesforce Flow actions in Flow Builder: standard and core actions, the Apex action element for @InvocableMethod classes, how list-shaped inputs and outputs map at the Flow–Apex boundary, subflows, and choosing between declarative actions versus custom Apex versus packaged invocables. Triggers: 'Flow Apex action', 'add Apex to Flow', 'InvocableMethod in Flow', 'Flow action palette', 'map Flow variables to Apex invocable inputs'. NOT for authoring or testing the Apex @InvocableMethod body — use apex/invocable-methods. More triggers: 'actionType enum', 'flowTransactionModel', 'dataTypeMappings T__ U__', 'storeOutputAutomatically', 'faultConnector on an action', 'timeoutConnector', 'InvocableActionExtension', 'apexPluginCalls legacy Apex action', 'action catalogue describe /actions/custom/apex'. NOT for registering an OpenAPI spec or HTTP Callout action — use flow/flow-external-services. NOT for writing the @InvocableMethod body — use apex/invocable-methods."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
  - Performance
triggers:
  - "how do I call Apex from a Flow and wire the input and output variables"
  - "my Flow Apex action does not show my invocable class in the palette"
  - "why does my Flow pass a collection into an Apex action and only some rows come back"
  - "should I use a subflow or an Apex action for this automation step"
  - "what is the difference between a standard Flow action and a custom Apex action"
  - "how do I bulkify an Apex action that Flow calls in record-triggered context"
  - "choose between an Apex action an External Service and a subflow"
  - "add a fault path to an Apex action in a flow"
  - "bind a generic sObject apex action to a concrete object in a flow"
  - "reorder or group the inputs on an apex action in flow builder"
  - "deploy a flow whose email alert action is missing in the target org"
  - "flow action still points at a class after the invocable annotation was removed"
  - "write a flow test that asserts what an action returned"
  - "set the transaction model on a flow action that calls out"
  - "convert a legacy apex plug-in action to an invocable method"
  - "which action types can a screen flow use"
tags:
  - flow-action-framework
  - flow-builder
  - apex-action
  - invocablemethod
  - invocablevariable
  - subflow
  - core-actions
  - flow-orchestration
inputs:
  - "Flow type (screen, autolaunched, record-triggered) and whether the path runs in bulk"
  - "Whether the step is declarative-only, needs callouts, or needs Apex or a subflow"
  - "Apex class API name and whether @InvocableMethod exists and is visible to Flow"
  - "Input/output variable types in Flow versus wrapper properties on the Apex side"
outputs:
  - "Decision guidance for which action category fits the step"
  - "Flow Builder wiring pattern for Apex actions and variable mapping"
  - "Checklist for list-shaped contracts and fault handling at the action boundary"
  - "Pointers to Apex invocable design (invocable-methods) or External Services when scope shifts"
dependencies:
  - apex/invocable-methods
version: 2.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Flow Action Framework

This skill activates when work centers on **Flow Builder actions** — the reusable steps in the toolbox and canvas — not on unrelated automation such as Process Builder migration or pure Apex services with no Flow surface. It explains how Salesforce groups work into action categories, how an **Apex action** element binds to an `@InvocableMethod`, why inputs and outputs are **list-shaped** at the platform boundary even when the builder feels single-record, and when a **subflow** or **standard action** is the better orchestration choice. Use it to route design questions, debug missing actions in the palette, and validate that variable mapping matches the invocable contract before runtime failures appear in production interviews.

The "wrong category" choice is the most common design failure this skill catches. An admin who builds a 12-element Flow + 3 Apex actions for something that could have been a single standard action has created maintenance debt; a team that drops to Apex for logic a subflow would have handled has bypassed the reusability win that the subflow provides.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which Flow runtime is in play:** Screen flows, autolaunched flows, and record-triggered flows differ in user context, bulk behavior, and whether certain actions or callouts are allowed in the same transaction as triggering DML. Misclassification here is a common source of "works in test, fails in production."
- **Whether the step must stay declarative:** If the requirement is only field updates, decisions, or platform messaging, a standard action or subflow often beats custom Apex. Apex belongs when the platform does not expose the operation declaratively or when you intentionally centralize logic behind a stable invocable contract.
- **Apex visibility and packaging:** An Apex action appears only when the class is compiled, the method is `public` or `global` and `static`, annotated with `@InvocableMethod`, and the running user can see the class. Managed-namespace classes expose only what the publisher designed. If the action is missing from the palette, verify visibility, API version, and packaging before rewriting Flow logic.
- **List contract at the boundary:** Flow passes a list of input rows into the invocable and expects a list of results aligned to that bulk shape. Treating the action as strictly single-record in design often breaks when record-triggered Flow batches many IDs through one interview.
- **Namespace considerations:** Managed-package consumers see only the actions the package exposes; locked packages sometimes hide actions that unlocked packages don't.

---

## Questions to Ask Before Configuring

Ask these before adding any action element. Each one maps to a failure documented in
`references/gotchas.md`, and skipping it produces a flow that deploys cleanly and breaks
somewhere the canvas does not show.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which action *family* is this — Apex, a standard core action, External Service, HTTP Callout, a subflow, quick action, or email?" | `actionType` is `Required` and decides packaging, limits, fault behaviour and transaction semantics; the canvas renders all of them the same (gotcha: *`actionName` is unique only within an `actionType`*) | The one row in the taxonomy table below that governs everything else, and the `actionType` value to write |
| "Who runs this flow — an end user, or the admin who built it?" | Describe *and* invoke for an Apex action "respect the profile access for the Apex class. If you don't have access, an error is issued" (`api_rest.txt` L13780) | The permission-set line item, and the user the release-gate describe call gets run as |
| "Does the invocable take a generic `sObject`, or a concrete one?" | A generic surface cannot be bound without `dataTypeMappings`, and its `typeName` needs the `T__` / `U__` prefix (gotcha: *the flow half of a generic contract*) | The two `<dataTypeMappings>` blocks, or a decision to type the Apex concretely instead |
| "When this action fails, what should the interview do — and is 'fail' the same as 'never answered'?" | `faultConnector` and `timeoutConnector` are different fields catching different events (gotcha: *An async action's timeout does not travel down the fault connector*) | The fault target, and whether `timeoutPathUsage` needs enabling |
| "Does this action call out, and does anything before it write records?" | The screen-flow-only callout gate decides whether the platform commits and starts a new transaction; outside a screen flow, `flowTransactionModel` is the only lever (`apexdev.txt` L26872-26880) | A deliberate `Automatic` / `CurrentTransaction` / `NewTransaction` value with a recorded reason |
| "Will this action's output be read once, or branched on several times?" | `storeOutputAutomatically` changes how every downstream reference is written; the default is `false` (gotcha: *`storeOutputAutomatically` and explicit outputs*) | One reference style used consistently, rather than half the flow referencing `{!Action_Name.field}` and half a variable |
| "What else has to ship with this flow for the action to resolve in the target org?" | Apex actions, email alerts, Post to Chatter, Quick Action, Send Email and Submit for Approval do not pull their referenced components into a package (`api_rest.txt` L13787-13800) | The manifest, built from the action inventory rather than from the flow (`references/metadata-examples.md` § 4) |

What a proper configuration adds over just dragging the action onto the canvas: the flow
names an action that provably exists in the target org for the *running user*, binds its
generic types explicitly, distinguishes a failure from a timeout, declares its transaction
model rather than inheriting a default, and ships with the components it depends on.

## Core Concepts

### Action categories in Flow Builder

Flow Builder surfaces several families of actions. **Standard and core actions** cover platform capabilities such as record create or update, decisions, assignments, loops, and many productized operations (subject to edition and permissions). **Subflows** package reusable Flow definitions behind an action-shaped boundary with defined input and output variables. **Apex actions** bind to one `@InvocableMethod` on a class and map Flow variables to annotated request and response shapes. **External integrations** can appear as generated actions from External Services or related integration features when registered — those paths are detailed in the External Services skill. **Platform Events** appear as publish/subscribe actions. Understanding which family you are in determines limits, fault behavior, and how variables are typed.

| Family | When to reach for it | Gov-limit behavior |
|---|---|---|
| Standard / core action | Declarative operation Salesforce already provides (Create Record, Send Email, Submit for Approval, etc.) | Lowest overhead |
| Subflow | Same declarative sequence reused in 2+ parent flows | Shares parent transaction |
| Apex action (@InvocableMethod) | Logic not declaratively expressible; reusable logic from both Flow and Apex | Apex governor semantics apply |
| External Service action | Typed REST operations registered via OpenAPI schema | Callout limits apply |
| Platform Event publish | Decouple the save transaction from downstream work | Publish-limit counts against org cap |

### The `actionType` taxonomy, as the platform actually enumerates it

Every action call is a `FlowActionCall` element whose `actionType` is one value from the
`InvocableActionType` enumeration (`api_meta.txt` L68465-68466, enum at L68551 onward).
The value is what decides the rulebook, so it is the first thing to fix. These are the
general-purpose values from that enumeration, quoted:

| `actionType` | The guide's own words | Metadata that has to travel with it |
|---|---|---|
| `apex` | "Invokes an Apex method that has the @invocableMethod annotation" (L68604) | `ApexClass` + Apex class access; optionally `InvocableActionExtension` |
| `flow` | "Invokes an autolaunched flow. This action type isn't available for flows with a `processType` of `Flow` or `AutolaunchedFlow`. To invoke an autolaunched flow from one of those types, use `FlowSubflow`" (L68749-68753) | The child `Flow`, active |
| `externalService` | "Invokes an External Service operation that makes an HTTP request to an external system made available by an External Service schema registered through Setup" (L68739-68742), API 46.0+ | `ExternalServiceRegistration` + `NamedCredential` |
| `externalConnector` | "Executes a process or method exposed via a connector to an external system" (L68736-68738), API 63.0+ | The connector definition |
| `emailAlert` | "Sends an email by referencing a workflow email alert" (L68729) | `WorkflowAlert` **and** its `EmailTemplate`, both added by hand |
| `emailSimple` | "Sends an email by using flow resources. This action isn't available for flows with a `processType` of `Workflow`" (L68731-68733) | Nothing beyond the flow's own resources |
| `quickAction` | "Invokes a Quick Action" (L68848) | The `QuickAction`, added by hand |
| `submit` | "Submits a record for approval" (L68928) | The `ApprovalProcess`, added by hand |
| `chatterPost` | "Posts to Chatter" (L68655) | Nothing; parameters are `text` and `subjectNameOrId` (L73249-73269 sample) |
| `lwcComponent` | "Triggers the LWC component that targets the `lightning__FlowAction` target in the XML configuration file and that's referenced by `actionName`" (L68830-68832), API 63.0+ | The `LightningComponentBundle`; screen flows only |
| `component` | "Invokes the Aura component that implements the `lightning:availableForFlowActions` interface" (L68659-68660), API 43.0+ | The `AuraDefinitionBundle` |
| `rpa` | "Performs a set of actions in a defined scope outside the flow, such as… an RPA robot" (L68862-68864), API 63.0+ | The RPA configuration |
| `sendNotification` / `customNotificationAction` | "Sends an available notification type" (L68875); "Sends a custom notification" (L68710) | The `CustomNotificationType` |

The rest of the enumeration is product-specific — Quip, Slack, Knowledge, Data Cloud,
Order Management, B2B/D2C Commerce, Omnichannel Inventory, Education Cloud, CMS,
Agentforce. Two consequences worth naming: the palette an admin sees is a *feature-licence*
view of that list, so "the action isn't there" is often an entitlement answer rather than a
visibility one; and Slack actions (`slackPostMessage`, `slackCreateChannel`,
`slackSendMessageToLaunchFlow`, and the rest, API 54.0+) belong to `flow/flow-for-slack`,
which owns their parameter contracts.

**Two things named "an action" that are not `FlowActionCall`:**

- A **subflow** is a `<subflows>` element (`FlowSubflow`), with `flowName`,
  `inputAssignments`, `outputAssignments`, `storeOutputAutomatically` and `connector` —
  and no `faultConnector`, no `flowTransactionModel`, no `dataTypeMappings`
  (`api_meta.txt` L72625-72658). Design of the child contract is
  `flow/subflows-and-reusability`.
- A **legacy Apex action** is an `<apexPluginCalls>` element (`FlowApexPluginCall`), keyed
  on `apexClass` rather than `actionName`/`actionType` (`api_meta.txt` L69680-69702). It
  comes from a class implementing `Process.Plugin`, which "doesn't support Blob,
  Collection, and sObject, data types, and it doesn't support bulk operations"
  (`apexdev.txt` L27262-27263).

### The four fields that make an action call behave

| Field | Required? | What it decides |
|---|---|---|
| `actionName` | Yes — "Must be unique across actions with the same `actionType`" (L68462-68463) | *Which* action. For `apex`, the class name (one `@InvocableMethod` per class, `apexdev.txt` L5422) |
| `actionType` | Yes (L68465-68466) | The rulebook: limits, packaging, palette, transaction |
| `flowTransactionModel` | Yes, API 51.0+ (L68479-68480) | `Automatic` / `CurrentTransaction` / `NewTransaction` (L68481-68486) |
| `faultConnector` | No (L68476-68477) | Where an error goes. Absent by default — and `timeoutConnector` (L68532-68534) is a *different* field for async timeouts |

`dataTypeMappings` binds generic-`sObject` parameters to a concrete object, with a `T__`
prefix on input variable names and `U__` on outputs (`api_meta.txt` L70192-L70203, API
48.0+). `storeOutputAutomatically` decides the reference style for outputs and defaults to
`false` (L68523-68529). Full worked XML for all of these is in
`references/metadata-examples.md` § 1.

### Action versioning and what a signature change does to a saved flow

The action element stores a *name*, not a version, and the platform resolves it at run
time. That produces three distinct versioning behaviours worth keeping straight:

- **Apex actions have no version pin at all.** `nameSegment` and `versionSegment` were
  "available in API version 58.0 to 61.0" and are "deprecated in API version 62.0 and
  later" (`api_meta.txt` L68495-68501, L68542-68546). What remains is the class name.
- **Removing the annotation is a runtime failure, not a deploy failure.** "If you add an
  Apex action to a flow, and then remove the Invocable Method annotation from the Apex
  class, a runtime error in the flow occurs" (`api_rest.txt` L13781-13782). Deploy
  validation will not catch it; the checker in this skill's `scripts/` will.
- **Calling a flow resolves to the active version, and who is calling changes the answer.**
  "When a flow user invokes an autolaunched flow, the active flow version runs. If there's
  no active version, the latest version runs. When a flow admin invokes a flow, the latest
  version always runs" (`api_rest.txt` L13783-13784). An admin testing an action-called
  flow is not testing what users get.
- **Once published in a managed package, the signature is permanent:** "after you add an
  invocable method you can't remove it from later versions of the package"
  (`apexdev.txt` L5460-5461), and only `global` invocable methods appear in Flow Builder
  in a subscriber org (L5463-5464).

### Action catalogue governance

The action list an admin scrolls is a shared namespace, and three `@InvocableMethod`
modifiers own how a new action lands in it: `label` — "appears as the action name in Flow
Builder. The default is the method name, though we recommend that you provide a label";
`description` — "The default is Null"; `category` — "If no category is provided (by
default), actions appear under **Uncategorized**" (`apexdev.txt` L5404-5409). An org that
never sets `category` gets one flat Uncategorized bucket. `InvocableActionExtension`
(API 65.0+) then governs the *inside* of the action's property panel — parameter order,
collapsible groups, picklists for text inputs, a custom header, and partial custom property
editors (`api_meta.txt` L81893-82005). See `references/metadata-examples.md` § 2.

The org-side inventory is the REST action catalogue: `/services/data/vXX.X/actions`
returns `standard` and `custom` roots, and `custom` fans out into `quickAction`, `apex`,
`emailAlert`, `flow`, `sendNotification` and more (`api_rest.txt` L13561-13562,
L13836-13841). Describing one action there answers as the *calling user*, which is what
makes it a release gate rather than a curiosity (L13780).

### Apex action element and the invocable surface

The Flow element that calls Apex is the "Action" element filtered by the class and method advertised to Flow. The Flow author picks the action, sets input values or collections, and maps outputs to Flow variables or record fields. The Apex side must follow the invocable rules enforced by the compiler: a single list-typed input parameter for the method signature used by Flow, and a void or list return for outputs, with bulk-safe semantics. Field-level discoverability for Flow authors comes from `@InvocableVariable` metadata on wrapper types. This skill stays on the Flow side of that boundary; deep DTO design belongs in `invocable-methods`.

### Bulk interviews and variable typing

Record-triggered and bulk autolaunched paths can supply collections where a novice design assumed scalars. Collection variables, SObject collection variables, and formulas that evaluate per item all interact with how much work a single Apex action invocation performs. Choosing **Loop → Apex** versus **single Apex with a collection input** affects governor use and failure granularity. Standard actions that operate on `$Record` may still run in a bulk context behind the scenes; Apex actions make that bulk shape explicit in the method contract.

### Permissions surface of Apex actions

The Flow's running user must have access to:
- The Apex class (profile / permission set grants).
- Any object the Apex performs DML on (CRUD + FLS; `with sharing` inherits from the user).
- Any external credential used by the Apex (Named Credentials + permission-set assignment).

A common deploy-time surprise: the action works in sandbox (admin-run) but fails in production when an end user invokes it because the user's profile lacks Apex class access. Audit this BEFORE deploying.

---

## Common Patterns

### Pattern 1: Single Apex action with collection input (preferred for bulk)

**When to use:** Multiple records or rows need the same transformation in one transaction and the Apex method is already list-oriented.

**Structure:**
```text
Record-triggered Flow:
  [Assignment: collect IDs into a Text Collection variable]
  [Apex Action: MyBulkProcessor — input = <collection>]
    └── Success → continue
    └── Fault   → log + notify
```

**Why not the alternative:** Calling Apex inside a loop on a large collection multiplies CPU and DML overhead and obscures partial failure behavior.

### Pattern 2: Subflow as the stable action boundary

**When to use:** The same sequence of declarative steps is reused across many parent flows, or you want versioning and testing isolated behind input/output variables.

**Structure:** Parent flow invokes `Run Subflow` with input variables. See `flow/subflows-and-reusability` for the full contract-design guidance.

**Why not the alternative:** Copy-pasting blocks of elements across flows drifts over time; a subflow gives one canonical implementation without jumping to Apex.

### Pattern 3: Standard action first, Apex only for the gap

**When to use:** The operation is mostly declarative but one step needs unsupported logic.

**Structure:** Implement the narrow Apex invocable for the gap only; keep surrounding steps as standard actions for readability and lower maintenance. Apex action should do ONE thing (compute, transform, or call-out); wider Apex belongs in a trigger handler, not a Flow action.

**Why not the alternative:** Replacing large declarative regions with Apex raises testing burden and hides self-documenting Flow structure from admins.

### Pattern 4: Packaged invocables with versioned contracts

**When to use:** Cross-org or unlocked-package distribution of a reusable invocable.

**Structure:** Ship the invocable in a namespace; document the `@InvocableVariable` contract as the public API; avoid breaking changes to the wrapper types between versions.

**Why not the alternative:** Copying the same Apex into each consumer org produces drift; one shared package centralizes.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Platform supports the operation declaratively | Standard / core action | Fewer moving parts, easier admin review, no Apex deployment |
| Reuse across many flows with same inputs/outputs | Subflow | Encapsulation and change control without code |
| Logic not available declaratively, or shared with non-Flow callers via Apex | Apex action (`@InvocableMethod`) | Full language power behind a typed invocable contract |
| Typed REST operations from OpenAPI + Named Credential | External Service action (see `flow-external-services`) | Spec-driven fields and validation in Flow Builder |
| Need to teach Flow authors how to write the Apex method body | `invocable-methods` (Apex domain) | Compiler rules, wrappers, tests, and bulk safety live there |
| Action must run asynchronously (fire-and-forget) | Platform Event publish OR `@future`-wrapped invocable | Decouples from save transaction |
| Cross-org distribution of an invocable | Packaged namespace with stable wrapper types (Pattern 4) | Prevents drift across consumer orgs |

---

## Recommended Workflow

1. **Answer the seven questions above** and record the answers in
   `templates/flow-action-framework-template.md`. The one that changes everything else is
   the first: which `actionType` this is. Fix it before anything is dragged onto a canvas.
2. **Fix the action family against the taxonomy table**, not against what the palette
   happens to show. If the answer is "call another flow" from a screen or autolaunched
   flow, it is a `<subflows>` element and not `actionType flow` — hand the contract design
   to `flow/subflows-and-reusability`. If it is an OpenAPI or HTTP callout, hand it to
   `flow/flow-http-callout-action` / `flow/flow-external-services`. If it is Slack, hand it
   to `flow/flow-for-slack`.
3. **Write the action call as XML first**, from `references/metadata-examples.md` § 1, and
   set all four decisive fields explicitly: `actionName`, `actionType`,
   `flowTransactionModel`, `faultConnector`. Add `dataTypeMappings` if the invocable takes
   a generic `sObject`, and `timeoutConnector` + `timeoutPathUsage` if the action is
   asynchronous. Route every fault to one logging element rather than to per-action paths.
4. **Decide the output reference style once.** `storeOutputAutomatically` `true` gives
   `{!Action_Name.field}` with no declared variables; `false` needs `outputParameters` plus
   variables. Do not mix the two on one element.
5. **Lay out the property panel if the action is Apex and has more than three inputs** —
   `references/metadata-examples.md` § 2. Remember `Order` is all-or-nothing across the
   action's parameters.
6. **Build the manifest from the action inventory, not from the flow**
   (`references/metadata-examples.md` § 4). Apex actions, email alerts, Post to Chatter,
   Quick Action, Send Email and Submit for Approval do not pull their dependencies in.
7. **Run the checker over flows and Apex together** — it is the only step that resolves an
   `actionName` against the classes in the same tree:
   `python3 skills/flow/flow-action-framework/scripts/check_flow_action_framework.py --manifest-dir force-app/main/default`
8. **Deploy in the order in `references/metadata-examples.md` § 5, then describe the action
   as a representative end user** — `GET /services/data/vXX.X/actions/custom/apex/<name>`.
   That describe honours Apex class access, so it is the one check that reproduces the
   "works for the admin, 403s for the user" failure before an interview finds it. Pin the
   outcome with the `FlowTest` in § 3, remembering it can only assert at `Start` and
   `Finish`.

## Review Checklist

- [ ] Correct action category chosen (standard vs subflow vs Apex vs integration action).
- [ ] Apex action inputs and outputs match list-oriented invocable contract; no accidental per-row Apex in a tight loop without justification.
- [ ] Running user profile or permission set grants access to the Apex class and any queried objects.
- [ ] Fault connector or structured error outputs defined; no silent interview failures.
- [ ] Bulk scenarios tested for the same Flow path that will run in production.
- [ ] Apex invocable documented: inputs, outputs, permissions, governor notes.
- [ ] If packaged: wrapper types have stable contracts with explicit version strategy.

---

## Salesforce-Specific Gotchas

1. **Missing Apex action in palette** — Usually visibility, API version, `global` vs `public` in managed packages, or the class failing compilation. Flow will not list invalid invocables. The compiler rules are exact: "The invocable method must be static and public or global, and its class must be an outer class" and "Only one method in a class can have the InvocableMethod annotation" (`apexdev.txt` L5421-5422) — an inner class never appears no matter how the annotation is written.
2. **List size and output alignment** — Invocable methods operate on batches; Flow expects the bulk semantics documented for invocable methods. Mismatched assumptions show up as partial updates or "wrong row" symptoms.
3. **Callouts and DML in the same invocable** — Callout constraints still apply inside Apex invoked from Flow; mixing DML and callouts without proper ordering causes `System.CalloutException` in the interview.
4. **Per-row Apex in a Loop** — Apex action invoked inside a Flow Loop fires once per iteration. For 200 records, that's 200 Apex invocations sharing the same transaction budget. Aggregate into a collection first, then invoke once.
5. **Running user Apex class access** — Profile / permission-set must grant the Apex class: "If a flow invokes Apex, the running user must have the corresponding Apex class security set in their user profile or permission set" (`apexdev.txt` L5172-5173), and "Describe and invoke for an Apex action respect the profile access for the Apex class" (`api_rest.txt` L13780). The common "action works in sandbox but fails in prod" cause is missing class access for end users.
6. **Invocable input type mismatch** — Flow's Text vs Apex's String behave the same; Flow's Number vs Apex's Decimal don't always. Test with edge values (large numbers, decimals) before deploying. UNVERIFIED (2026-09-05): no Flow-to-Apex type-coercion table appears in `api_meta.txt` or `apexdev.txt`; the only documented conversion table is "Process.Plugin Data Type Conversions" (`apexdev.txt` L27300), which covers the *legacy* interface, not `@InvocableMethod`; a flow's `numberValue` is documented only as "a double value" (`api_meta.txt` L70484-70485). Treat this as a testing instruction, not a documented behaviour.
7. **Managed-package invocable names are namespaced** — `mypackage__DoWork` shows up differently in Flow Builder than an unmanaged `DoWork`. Rename-refactor the Flow if the namespace changes. UNVERIFIED (2026-09-05): the `namespace__Name` shape of a packaged action's `actionName` is not stated in `api_meta.txt`, `apexdev.txt` or `api_rest.txt`; what *is* grounded is that only `global` invocable methods appear in Flow Builder in a subscriber org (`apexdev.txt` L5463-5464) and that a published invocable method can never be removed from a later package version (L5460-5461). Confirm the exact name with `GET /services/data/vXX.X/actions/custom/apex` in the subscriber org.
8. **Standard action availability varies by entitlement** — the grounded form is "Some actions require special access", said of both the custom and standard catalogues (`api_rest.txt` L13763, L13918), and the enumeration itself is full of product-gated families (Data Cloud, Order Management, B2B Commerce, Education Cloud, Omnichannel Inventory). Verify every standard action against the target org's own `/actions/standard` describe rather than against a feature list. UNVERIFIED (2026-09-05): no per-edition availability table for Flow actions exists in the extracted guides, and no "launch a Batch job" value appears anywhere in `InvocableActionType` (`api_meta.txt` L68551-69010) — the earlier wording of this gotcha named one.
9. **Apex action does NOT get a fault connector by default** — must be added explicitly. Missing fault connector = unhandled exception bubbles to user.
10. **Invocable's `@InvocableVariable(required=true)` is enforced at runtime, not design time** — Flow Builder won't prevent you from leaving a required input unmapped; the failure happens at runtime. UNVERIFIED (2026-09-05): `required` is documented as a modifier (`apexdev.txt` L5275, L5559) but neither guide states *when* it is enforced. Do not rely on the builder to catch an unmapped required input; the `Order` / `ProvidedValuesList` attributes in an `InvocableActionExtension` are the documented way to make the panel guide the admin instead.
11. **`flowTransactionModel` is `Required` on every action call**, including a Chatter post — three fields on `FlowActionCall` carry that marking and this is the one people omit.
12. **`actionName` is unique only within an `actionType`** — the pair addresses the action, so repointing by editing the name alone can silently target something else.
13. **`actionType flow` is illegal from a screen or autolaunched flow** — those must use a `<subflows>` element, which the enum entry for `flow` says in its own sentence.
14. **A fault connector does not catch an async action timeout** — `timeoutConnector` is a separate field, switched on by `timeoutPathUsage`.
15. **Three of the four common action families do not package their dependencies** — email alerts, Chatter posts, quick actions, Send Email, Submit for Approval and Apex actions all need their referenced components added by hand.
16. **A `FlowTest` can assert only at `Start` and `Finish`** — there is no test point at the action element, and no mocking, so the test really invokes the action.
17. **A legacy `<apexPluginCalls>` element is a different type** — it keys on `apexClass`, has no transaction model, and cannot be added in Flow Builder's auto-layout canvas.
18. **`Order` in an `InvocableActionExtension` is all-or-nothing** — ordering some parameters and not others produces undefined layout.

---

## Proactive Triggers

Surface these WITHOUT being asked:

- **Apex action called inside a Flow Loop** → Flag as High. Refactor to collection-input pattern.
- **Apex action with no fault connector** → Flag as High. Unhandled exception risk.
- **Standard action available but Apex action used** → Flag as Medium. Unnecessary code; prefer declarative.
- **Subflow candidate (same sequence in 2+ flows) left inlined** → Flag as Medium. Duplication debt.
- **Managed-package Apex action used without documented contract** → Flag as Medium. Upgrade risk; pin package version.
- **End-user profile missing Apex class access for required action** → Flag as Critical. Prod-launch blocker.
- **Invocable wrapper type changing between versions** → Flag as High. Breaking change for consumers.
- **External Service action not using Named Credentials** → Flag as Critical. Credentials in cleartext.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Action decision table | Markdown or design-doc table mapping each step to standard, subflow, Apex, or integration action |
| Flow variable map | Document listing Apex action input/output names next to Flow variable API names and types |
| Test matrix | Bulk and single-record cases with expected Apex invocations and fault paths |
| Permissions audit | Running-user access requirements across profile / PS / PSG |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing the actual XML — a deployable four-action flow, the `InvocableActionExtension`, a `FlowTest`, `package.xml`, the deploy order, and the REST describe call that verifies the action catalogue |
| `references/gotchas.md` | An action behaves differently from what the canvas suggests: a missing required field, a timeout that skips the fault path, a package that installs without its email template, a FlowTest with nowhere to assert |
| `references/examples.md` | You want the reasoning worked through — the bulk-collection refactor, the subflow extraction, and the shell pass that inventories an org's action families from retrieved source |
| `references/llm-anti-patterns.md` | Reviewing generated flow XML or action advice before it ships |
| `references/well-architected.md` | Justifying an action-family choice in a design review, and for the grounded source list with the claim each source supports |
| `templates/flow-action-framework-template.md` | Running the seven questions with a requester, before any XML exists |
| `scripts/check_flow_action_framework.py` | Validating a manifest directory — fault connectors, `actionName` resolution against the tree's Apex, generic-type binding, loop placement, transaction model |

## Related Skills

- `apex/invocable-methods` — Apex-side `@InvocableMethod` and `@InvocableVariable` design, tests, and bulk safety.
- `flow/flow-external-services` — HTTP callout and External Services actions from Flow.
- `flow/subflows-and-reusability` — Parent/child flow composition and variable contracts.
- `flow/auto-launched-flow-patterns` — Autolaunched entry, bulk collection patterns, and API invocation context.
- `flow/fault-handling` — fault-routing at the action boundary.
- `flow/flow-bulkification` — when the action must stay inside bulk safety math.
- `flow/flow-http-callout-action` — when the action is Flow Builder's HTTP Callout rather than a registered External Service.
- `flow/flow-for-slack` — when the action is one of the `slack*` values in the enumeration; that skill owns their parameter contracts.
- `lwc/custom-property-editor-for-flow` — when `configurationEditor` or an `InvocableActionExtension` `CpeName` points at an LWC you have to build.
- `flow/flow-custom-property-editors` — when the open question is whether a custom property editor is warranted at all.
- `flow/flow-testing` — when the `FlowTest` in `references/metadata-examples.md` § 3 is the starting point rather than the whole test plan.
- `flow/flow-transactional-boundaries` — when `flowTransactionModel` is the decision rather than a field to fill in.
- `flow/flow-deployment-and-packaging` — when the action inventory turns into a release plan across orgs.
