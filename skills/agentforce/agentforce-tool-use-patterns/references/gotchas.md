# Gotchas: Agentforce Tool Use Patterns

Non-obvious platform behaviours that cause production problems. Three earlier entries were wrong or unsupported and are corrected in place: Gotcha 1 (label changes), Gotcha 3 (output descriptions) and Gotcha 11 (action category). Gotcha 2 was narrowed to what the Apex guide documents.

## Gotcha 1: Renaming the Apex label does not rename the agent action

**What happens:** A developer renames `@InvocableMethod(label=...)` to make the tool clearer to the LLM. Nothing changes in the agent. The agent action still shows the old label and the old instructions.

**When it occurs:** Refactoring the reference action after the agent action was created.

**How to avoid:** Treat the agent action as its own artefact. When you create a custom agent action, its label, API name and instructions are copied from the reference action; after that you edit them on the agent action. References between metadata use API names: `GenAiPlugin` lists `functionName` (the action API name) and `GenAiFunction` points at the class through `invocationTarget`. Edit the agent action's label and instructions in Agentforce Builder, or in the retrieved `GenAiFunction`, when the tool's meaning changes.

**Correction:** the earlier text said a label change "breaks" subagents that reference the action by label. The Metadata API reference shows references by API name, so the real failure is drift, not breakage.

**Source:** Generative AI guide (Spring '26), Create a Custom Action for Agents (label, API name and instructions are populated from the reference action); Metadata API reference, GenAiPlugin `functionName` and GenAiFunction `invocationTarget`.

---

## Gotcha 2: `callout=true` is documented for screen-flow transaction control

**What happens:** A team adds `callout=true` and expects it to change how the agent runs the action. Or a team omits it, and a screen flow that reuses the same invocable fails with uncommitted-work errors.

**When it occurs:** The same Apex invocable serves both an agent and a screen flow, and it makes an HTTP callout.

**How to avoid:** Set `callout=true` on any invocable that calls an external system. The documented effect is in screen flows: when the modifier is true, the action's Transaction Control lets the flow decide, and the transaction has uncommitted work, the flow commits, starts a new transaction and makes the call safely. UNVERIFIED (2026-10-03): no source documents a separate effect of the modifier when an agent invokes the action, and the earlier claim that omitting it raises "Callout from triggers are currently not supported" for agents is not supported by any source read.

**Source:** Apex Developer Guide (API 67.0), InvocableMethod Annotation (supported modifiers) and Making Callouts to External Systems from Invocable Actions.

---

## Gotcha 3: Output descriptions are instructions the planner reads

**What happens:** Authors leave output descriptions blank or write developer notes in them. The agent misreads results, or answers with irrelevant fields.

**When it occurs:** Teams assume only the method description and input descriptions reach the LLM.

**How to avoid:** Write each output description as an instruction: what the value is and what the agent should say or do with it. Mark the outputs the agent may show with "Show in conversation" (`copilotAction:isDisplayable`). Make sure at least one output is used by the planner (`copilotAction:isUsedByPlanner` set to `true`).

**Correction:** the earlier text said output descriptions "aren't part of the prompt". The Generative AI guide tells you to write instructions for outputs ("specify the result of the action and what an agent returns to the user"), and the Metadata API reference says that if no output property is used by the planner, "the planner returns random responses".

**Source:** Generative AI guide, Best Practices for Agent Action Instructions (Instructions for Inputs and Outputs); Metadata API reference, GenAiFunction output folder.

---

## Gotcha 4: External Service and API catalog changes break actions quietly

**What happens:** The external API changes its response shape, or an admin deactivates an API catalog operation. The agent gets nulls, a deserialization error, or a missing action.

**When it occurs:** Partner APIs without versioning, an OpenAPI spec that was not re-imported after a change, or catalog cleanup that ignored which actions use an operation.

**How to avoid:** Pin versioned endpoints. Re-import the spec when the vendor changes it. Before you deactivate or delete an API catalog registration, remove it from every agent action that uses it.

**Source:** Agentforce Developer Guide, Apex REST and AuraEnabled agent action Limits pages: "Before inactivating or deleting an ... API catalog registration, remove it from any agent action that's using it." UNVERIFIED (2026-10-03): the runtime symptom (null versus error) when a schema drifts.

---

## Gotcha 5: Retrieval with no results needs an explicit path

**What happens:** The agent answers a policy question with text no source contains.

**When it occurs:** Retrieval returns nothing useful and the subagent has no instruction for that case.

**How to avoid:** Return an explicit no-results marker from custom retrieval actions, and instruct the subagent what to say. Keep the platform groundedness check on for knowledge-heavy agents: by default, Agentforce checks the LLM's responses against source content, and the Agent Script `runtime` block exposes `groundedness` and `citation` switches. Troubleshoot wrong answers against the sources before changing instructions.

**Source:** Agentforce Developer Guide, Agent Script Blocks (runtime sub-block: `groundedness`, `citation`); Generative AI guide, Troubleshooting Agents ("verify the output of your action against the content of your sources"). UNVERIFIED (2026-10-03): how often an empty retrieval produces a fabricated answer.

---

## Gotcha 6: Overlapping action descriptions make selection unstable

**What happens:** For the same request the agent picks `Look_Up_Order` one time and `Search_Orders` the next.

**When it occurs:** Two actions share verbs and boilerplate and differ in one detail.

**How to avoid:** Vary the verbs (Get, Find, Identify, Retrieve) instead of starting every action with the same one. Remove phrases repeated across actions. Say what each action does, when to use it, and the objects it reads or changes; more relevant detail makes actions easier to tell apart.

**Source:** Generative AI guide, Best Practices for Agent Action Instructions ("LLMs work best when you use unique or varied language").

---

## Gotcha 7: Example values in descriptions get passed literally

**What happens:** A description says "for example A7842". The agent passes `A7842` when the user said "my last order".

**When it occurs:** Format examples sit in an input description without framing.

**How to avoid:** Frame examples as format only and say where the real value comes from ("from the user's message; ask if it is missing"). Validate the format in the action itself.

**Source:** UNVERIFIED (2026-10-03): no source documents literal copying of examples. The Generative AI guide notes that "examples don't generalize well" and recommends describing how the information is retrieved ("retrieve the ID from the user's input").

---

## Gotcha 8: A flow action that faults without a structured result leaves the agent guessing

**What happens:** The flow faults and the agent replies with a vague apology, or retries the same input.

**When it occurs:** The autolaunched flow has no fault path, or its fault message is not safe to show.

**How to avoid:** Give every agent-facing flow a fault path that sets a structured error output, and tell the subagent what to do when it is set. Troubleshoot the reference flow directly when the agent output is wrong.

**Source:** Generative AI guide, Agent Actions and Large Language Model Use (an action error triggers an extra generated message) and Troubleshooting Agents ("troubleshoot the reference action itself"). UNVERIFIED (2026-10-03): the exact message the agent shows for an unhandled flow fault.

---

## Gotcha 9: Long prompt-template inputs and retriever queries hit limits

**What happens:** A prompt-template action fed a 10,000-character `Case.Description` produces weak output, or a retriever query built from a long field is cut short.

**When it occurs:** Large field values go straight into a template or a retriever search.

**How to avoid:** Summarize long inputs first with a separate action, or ground through retrieval. Keep retriever search text short: in Prompt Builder the search text input is limited to 255 characters, globals and prompt inputs.

**Source:** Generative AI guide, Ground with Retrieval Augmented Generation (Retriever Settings, 255-character search text); Metadata API reference, GenAiPromptTemplateVersion `fileDroppingStrategy` (a strategy exists for exceeding context limits with attached files). UNVERIFIED (2026-10-03): the truncation behaviour for long record-field inputs.

---

## Gotcha 10: Managed-package actions bring package rules with them

**What happens:** A packaged action and an unpackaged action with the same local name coexist and the agent picks the wrong one. Or a team cannot remove an obsolete packaged invocable.

**When it occurs:** Partial migration to a managed package.

**How to avoid:** Never keep two actions with the same local name. Plan packaged invocables as permanent: after you add an invocable method to a package, you can't remove it from later versions. Only global invocable methods appear in Flow Builder in the subscriber org.

**Source:** Apex Developer Guide, InvocableMethod Considerations (Managed Packages). UNVERIFIED (2026-10-03): the selection behaviour when two actions share a local name.

---

## Gotcha 11: The Apex `category` modifier is a Flow Builder grouping, not an LLM signal

**What happens:** A team renames categories to "Customer Support" expecting better routing. Nothing changes.

**When it occurs:** `category` is treated as part of the prompt.

**How to avoid:** Put routing meaning in the action description and the subagent instructions. Use `category` only to organize actions in Flow Builder.

**Correction:** the earlier text said the category "affects what the LLM sees". The Apex Developer Guide defines `category` as "the action category in Flow Builder", and the Metadata API field list for `GenAiFunction` has no category field, so there is no documented path from the Apex category to the planner.

**Source:** Apex Developer Guide, InvocableMethod Annotation (Supported Modifiers); Metadata API reference, GenAiFunction fields.

---

## Gotcha 12: Custom actions that reference Apex or flows accept primitive types only

**What happens:** An action built on an invocable with a `List<String>` or an sObject parameter behaves inconsistently or cannot be configured as the team expected.

**When it occurs:** A Flow-oriented invocable that takes collections or records is reused as an agent tool.

**How to avoid:** Give agent-facing invocables primitive fields in a request class: one record ID, one order number, one date. For a prompt template that needs an sObject input, the guide recommends wrapping the template in a flow and creating the custom action from the flow.

**Source:** Generative AI guide, Considerations for Custom Actions: "Custom actions that reference an Apex class or flow support only primitive data types. Collections aren't supported" and "Custom actions can't accept a list and object as input." The checker flags collection-typed invocable variables (TU-004).

---

## Gotcha 13: Prompt-template tools cost LLM calls that Apex and flow tools do not

**What happens:** Moving a lookup into a prompt template raises consumption and latency with no quality gain.

**When it occurs:** Deterministic work is given a generative tool shape.

**How to avoid:** Use Apex, flows or standard invocable actions for deterministic work. Reserve prompt templates for generation. Expect extra generated messages when an action requires confirmation, needs more input, or errors.

**Source:** Generative AI guide, Agent Actions and Large Language Model Use: "Apex classes, flows, and standard invocable actions don't require an LLM call to execute, but prompt templates do."

---

## Gotcha 14: Schema text fields stop at 250 characters

**What happens:** A text output meant to carry a paragraph is cut off or rejected.

**When it occurs:** A `lightning__textType` property is used for long content.

**How to avoid:** Use `lightning__multilineTextType` or `lightning__richTextType` for long content, and keep `lightning__textType` for short values.

**Source:** Metadata API reference, GenAiFunction input and output folders: "The maximum text type length is 250 characters." The checker warns on larger `maxLength` values (TU-023).

---

## Gotcha 15: Invocable outputs must line up with inputs

**What happens:** An action that drops failed inputs returns results that no longer match the requests, and the agent attributes a result to the wrong record.

**When it occurs:** The invocable filters or throws for bad inputs.

**How to avoid:** Return one result per request, in the same order, with an error field for failures.

**Source:** Apex Developer Guide, InvocableMethod Annotation: the method "must run and return the same number of results as inputs received even if errors occur", and "the i-th Output entry must correspond to the i-th Input entry".

---

## Gotcha 16: Agents reached through Agent API stop waiting after 120 seconds

**What happens:** A long-running tool works in Builder preview but the client calling Agent API receives an HTTP 500.

**When it occurs:** A tool does slow external work inside the conversation turn and the agent is served through Agent API.

**How to avoid:** Keep tool work short. Hand slow work to asynchronous processing and return a reference the agent can report.

**Source:** Agentforce Developer Guide, Agent API Considerations: "The Agent API has a 120-second timeout. When a call times out, you receive an HTTP 500 response."
