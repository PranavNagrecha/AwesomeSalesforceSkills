# Gotchas: Agent Actions

Non-obvious platform behaviours behind the action-design rules in `SKILL.md`. Each entry cites the official source it rests on.

## Gotcha 1: Generic names and boilerplate descriptions hurt selection

**What happens:** The agent picks the wrong action, or none, because two actions read alike or a name like `handleRequest` says nothing.

**When it occurs:** Actions are named after code (`runProcess`, `execute`) or share the same opening verb and stock phrases.

**How to avoid:** Write one to three sentences as an instruction to the LLM: the goal, the use cases, and the records the action reads or changes. Vary related verbs (Get, Find, Identify, Retrieve) across similar actions and delete phrases repeated across actions ("Provides the ability to...").

**Source:** Generative AI guide (Spring '26), Best Practices for Agent Action Instructions: "the more relevant detail you include in your instructions, the easier it is for the LLM to differentiate between actions" and "LLMs work best when you use unique or varied language."

---

## Gotcha 2: Prompt-template actions are generation tools with narrow inputs and outputs

**What happens:** A team builds a record update on a prompt-template action. It cannot take the inputs it needs and returns only text.

**When it occurs:** Generation and side effects are blurred into one action.

**How to avoid:** Use prompt-template actions to generate text. Use Flow or Apex actions for writes. If a template needs an sObject input, wrap it in a flow and create the custom action from the flow.

**Source:** Generative AI guide, Considerations for Custom Actions: custom actions that reference a custom prompt template support record information object inputs and text outputs only; sObject input types are partially supported, and the guide recommends wrapping the template in a flow.

---

## Gotcha 3: Confirmation is an action setting, and it changes the conversation

**What happens:** A write runs the moment the agent decides to call it. Or, once confirmation is on, the team is surprised by the extra turn and the extra cost.

**When it occurs:** Actions that create, update or send are configured without the confirmation setting, or with it but no plan for a "no".

**How to avoid:** Turn on "Require user confirmation" (`isConfirmationRequired` in `GenAiFunction`) for actions that change records or send messages. Write the input instructions so the agent reads the values back. Decide what the agent says when the user declines.

**Source:** Generative AI guide, Create a Custom Action for Agents ("When an action makes a change to a record, you can require an agent to ask the user to confirm the change"); Agent Actions and Large Language Model Use (confirmation adds messages and LLM calls); Metadata API reference, GenAiFunction `isConfirmationRequired`.

---

## Gotcha 4: Raw exceptions are weak agent contracts

**What happens:** A DML exception or a stack trace reaches the conversation, or the whole batch of inputs fails because one input was bad.

**When it occurs:** The invocable throws for business-rule failures.

**How to avoid:** Return a result object per input with a success flag, a user-safe message and a machine-readable code. Log the technical detail separately.

**Source:** Apex Developer Guide (API 67.0), InvocableMethod Annotation: "To handle exceptions within an invocable method, wrap the results in an Apex object that reports failures. The execution of the invocable method must run and return the same number of results as inputs received even if errors occur."

---

## Gotcha 5: More than 15 actions in one subagent degrades performance

**What happens:** Selection quality drops as a subagent accumulates overlapping tools.

**When it occurs:** Every new request becomes a new action in the same subagent.

**How to avoid:** Keep each subagent at 15 actions or fewer. Split by job to be done, and remember an action can be added to several subagents instead of being copied. The earlier figure in this skill, 20 actions per agent, was a local heuristic; the documented guidance is per topic.

**Source:** Generative AI guide, Agents Limits: "For best performance, we recommend assigning no more than 15 actions to a topic"; Agent Action Assignments: "An action can be added to multiple topics."

---

## Gotcha 6: An action is invisible until it is assigned to a subagent

**What happens:** A custom action is created and tested in isolation, then never fires in conversation.

**When it occurs:** The action exists in the library but no topic includes it.

**How to avoid:** Assign the action to the subagent that owns the job, then test it in a preview conversation with utterances you expect to trigger it.

**Source:** Generative AI guide, Agent Action Assignments: "An agent uses only the actions that are assigned to it. To assign an action to an agent, an action must be added to a topic"; Create a Custom Action for Agents: "Your action must be assigned to an agent to test it."

---

## Gotcha 7: Business rules written as instructions are followed only most of the time

**What happens:** An instruction such as "never refund orders older than 30 days" holds in testing and fails in production.

**When it occurs:** Deterministic or sensitive rules live in action or topic instructions.

**How to avoid:** Enforce the rule in the reference action (the Apex class or flow) and let the instruction only explain it. The example in `references/metadata-examples.md` validates the callback time in code for this reason.

**Source:** Generative AI guide, Best Practices for Writing Topic Instructions ("Build sensitive or deterministic business rules into the logic of an action itself") and Troubleshooting Agents ("LLMs are nondeterministic").

---

## Gotcha 8: Input settings decide what the agent asks for and what it may skip

**What happens:** The agent runs an action without a value the business needs, or asks the user for something it should have found itself.

**When it occurs:** "Require input" and "Collect data from user" are left at defaults.

**How to avoid:** Set "Require input" on every value the action cannot run without; all other inputs are treated as optional. Set "Collect data from user" only on values the user must supply. An input that is required by the reference action is required on the agent action and cannot be changed there.

**Source:** Generative AI guide, Create a Custom Action for Agents (settings table: Collect data from user, Require input, Filter from copilot action, Show in conversation).

---

## Gotcha 9: Every action needs at least one usable output

**What happens:** The agent's reply after an action is unrelated to what the action returned.

**When it occurs:** All outputs are filtered out or none is marked for the planner.

**How to avoid:** Keep at least one output in use and mark it for the planner (`copilotAction:isUsedByPlanner`). Mark only the outputs the agent may repeat as "Show in conversation".

**Source:** Generative AI guide, Create a Custom Action for Agents ("At least one output must be used with the agent action"; "At least one output must be available"); Metadata API reference, GenAiFunction output folder ("At least one output property must have this value as true or else the planner returns random responses").

---

## Gotcha 10: The running identity decides what an action can touch

**What happens:** An action works for an admin in preview and fails, or returns too much, for the real agent.

**When it occurs:** Nobody checks which user the action runs as and what that user can see.

**How to avoid:** For service agents, the agent user determines what the agent can access and do, so grant that user exactly the objects, fields and Apex classes its actions need. Access to a custom action follows its reference action: a flow-based action obeys the permissions, field-level security and sharing the flow runs with. UNVERIFIED (2026-10-03): which user an Agentforce (Default) employee agent's custom Apex action runs as; the guide says that agent performs tasks "on behalf of the users".

**Source:** Generative AI guide, Create an Agent from a Type ("The agent user determines what your agent can access and do") and Trust and Agents, Permissions and Access; Agentforce Developer Guide, Agent Script Blocks (access block: "An agent runs in the context of a user").

---

## Gotcha 11: Editing a standard action's reference flow or template has limits

**What happens:** A team adds an input to the flow behind a standard action and the standard action never passes it.

**When it occurs:** The underlying flow or prompt template of a standard agent action is customized.

**How to avoid:** Edit the reference flow or template for behaviour changes only. When inputs or outputs change, create a custom agent action that calls the edited reference and replace the standard action with it.

**Source:** Generative AI guide, Editing Standard Agent Action Reference Actions: "if you add or remove inputs or outputs from the reference action, you must create a custom agent action to replace the standard agent action."

---

## Gotcha 12: Custom actions cannot control their output format or read page context

**What happens:** A team builds an action expecting it to render a table, or to know which record page the user is on.

**When it occurs:** Expectations carry over from standard actions or from Lightning components.

**How to avoid:** Return plain values and pass the record identifier as an input. Use custom Lightning types when a custom UI is genuinely required.

**Source:** Generative AI guide, Considerations for Custom Actions ("you can't specify how the output appears in an agent conversation") and Considerations for Agent Conversations ("Page context isn't supported for custom agent actions"); Agentforce Developer Guide, Enhance the Agent UI with Custom LWCs and Lightning Types.

---

## Gotcha 13: Adding an action to a live agent means deactivating it or versioning

**What happens:** A hotfix action is added to a live agent and every open conversation drops.

**When it occurs:** Changes are made directly on the active agent.

**How to avoid:** Make action changes on a new agent version, test it, then activate it. If you deactivate instead, plan for interrupted sessions; users are not notified.

**Source:** Generative AI guide, Activate or Deactivate Your Agent ("To make changes to an agent, such as adding or removing topics or actions, deactivate it" and "Deactivating an agent interrupts any ongoing user conversations. Users aren't notified").
