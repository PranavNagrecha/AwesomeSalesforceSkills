# Gotchas: Agent Security Review

Each entry names the official source it rests on. Gotchas 1 to 3 are carried from the earlier version and now carry sources; Gotcha 4 corrects a claim the earlier `SKILL.md` made about Trust Layer masking.

## Gotcha 1: The agent user has View All, or is a cloned admin

**What happens:** The agent sees records across owners that the business never meant it to see, and summarizes them to whoever asks.

**When it occurs:** An integration user or an admin is cloned as the agent user, or a broad permission set is assigned "to make the demo work".

**How to avoid:** Create a dedicated agent user with the license permission set plus one narrow data-access permission set (see `references/metadata-examples.md`). Query effective access, including the profile-owned permission set, at every review.

**Source:** Generative AI guide (Spring '26), Create an Agent from a Type: "The agent user determines what your agent can access and do"; Agentforce Developer Guide, Use Metadata to Move an Agent to a New Org: "Ensure the agent user has sufficient permissions to carry out the agent's tasks", for example view permission on each custom field it reads.

---

## Gotcha 2: Nobody can answer "what did the agent see and say?" after the fact

**What happens:** A subject-access request or an incident review needs the prompts and responses for a session, and the data is gone or was never kept.

**When it occurs:** The team relies on Agent Builder event logs, or never turned on audit data collection.

**How to avoid:** Decide retention per data class before go-live. Turn on Einstein generative AI data collection and storage if prompts and responses must be kept, and document how to delete them. Builder event logs keep data for 7 days, and without enhanced event logs the conversation text is replaced with "Sensitive data not available".

**Source:** Generative AI guide, Enable Enhanced Event Logs ("Event logs store information for 7 days"); Einstein Audit and Feedback Data (audit data includes the hydrated prompt, retrieved data and LLM response; it is stored in the default Data Cloud data space; it can be deleted by removing the data lake objects; streams refresh every hour). UNVERIFIED (2026-10-03): retention periods for the Data Cloud audit objects.

---

## Gotcha 3: Event Monitoring is licensed but not collected

**What happens:** An anomaly in an action (mass reads, unexpected exports) is invisible to the security team.

**When it occurs:** Event Monitoring is not licensed, or `EventLogFile` data is never retrieved into the SIEM.

**How to avoid:** Where the entitlement exists, retrieve `EventLogFile` data (for example the `ApexExecution` event type) on a schedule and add the agent user to standing alert rules.

**Source:** Object Reference (Summer '26), EventLogFile (event types such as ApexExecution). UNVERIFIED (2026-10-03): which agent-specific events, if any, appear in EventLogFile.

---

## Gotcha 4: Trust Layer data masking does not protect agent prompts

**What happens:** A review signs off on regulated fields in grounding because "the Trust Layer masks PII". It does not, for agents.

**When it occurs:** Masking settings are reviewed for prompt templates and assumed to cover agents.

**How to avoid:** Keep regulated fields out of the agent user's field permissions and out of every grounding selector. Treat zero-data retention as the provider-side control, not as masking.

**Correction:** the earlier `SKILL.md` workflow said to "redact/mask confidential and regulated fields at the Trust Layer". The Generative AI guide states the opposite for agents.

**Source:** Generative AI guide, Trust and Agents: "Data masking through the Einstein Trust Layer is disabled to improve the performance and accuracy of agents. All data accessed by agents, including personally identifiable information (PII), is protected in transit and isn't stored or used for training purposes by external LLM providers."

---

## Gotcha 5: The API version of each action class changes its default access mode

**What happens:** Two action classes with identical code enforce different access. One respects the agent user's field-level security; the other runs in system mode.

**When it occurs:** Action classes are saved at different API versions and omit an explicit access mode or sharing keyword.

**How to avoid:** Record each action class's API version in the review. Require an explicit sharing keyword and `WITH USER_MODE` or `AccessLevel.USER_MODE` regardless of version, so the code does not depend on the default.

**Source:** Apex Developer Guide (API 67.0), Apex Versioned Behavior Changes, Version 67.0: "Apex runs in user context by default ... In API version 66.0 and earlier, system mode is the default" and "classes without an explicit sharing declaration are run in the current user context."

---

## Gotcha 6: Standard actions carry broad data access into external agents

**What happens:** A standard action added to a customer-facing subagent can reach more data than the use case needs.

**When it occurs:** Standard actions are attached to the Escalation topic or other external subagents because they are convenient.

**How to avoid:** For external agents, prefer custom actions with an explicit, reviewable field list. Never attach standard actions to the Escalation topic.

**Source:** Generative AI guide, Agent Topic: Escalation, Guidelines and Considerations: "Avoid associating standard actions with the Escalation topic. Standard actions have broad data access not intended for external use cases. Define custom actions instead."

---

## Gotcha 7: A sensitive subagent with no rule expression is open to unverified users

**What happens:** An unauthenticated visitor reaches account-management actions by phrasing a request well.

**When it occurs:** Customer verification exists as a subagent, but the subagents that act on customer records are not locked behind its result.

**How to avoid:** Gate every subagent that reads or changes a customer's own records with a rule expression on a verification variable. Pass verified identifiers to actions through attribute mappings from the verification action's output, not from user input.

**Source:** Metadata API Developer Guide (API 67.0), GenAiPlannerBundle: rule expressions "conditionally lock or unlock topics and actions based on defined security criteria"; attribute mappings "propagate sensitive data safely without relying on untrusted user input" (sample: `Verified_User` on `isVerified`).

---

## Gotcha 8: Retriever access follows Data Cloud permissions, not CRM sharing

**What happens:** A retriever returns knowledge or file chunks that the CRM sharing model would have hidden.

**When it occurs:** The review checks CRM sharing for the agent user and stops there.

**How to avoid:** Review the Data Cloud permission sets and data space that govern each retriever the agent uses, as a separate line in the review. Scope data libraries (for example by Knowledge data category) when content must be restricted.

**Source:** Generative AI guide, Ground with Retrieval Augmented Generation: "Access to retrievers and their data is controlled by the Data Cloud permission sets"; Agentforce Developer Guide, Knowledge Library Example (data category rules "restrict what the knowledge library is allowed to search").

---

## Gotcha 9: Context variables and private conversation data reach places reviewers do not look

**What happens:** Session data such as an end-user ID lands in every prompt, or customer inputs are logged when policy says they must not be.

**When it occurs:** Context variables are set to be included in the prompt without review, or `logPrivateConversationData` is left on.

**How to avoid:** List every context variable with `includeInPrompt` set to true and justify it. Decide `logPrivateConversationData` deliberately and record the decision.

**Source:** Metadata API reference, Bot: `ConversationContextVariable.includeInPrompt` ("whether the variable is injected into the prompt sent to the Agentforce model") and `logPrivateConversationData` ("whether to log customer inputs as part of conversation data").

---

## Gotcha 10: Moving an agent between orgs carries the source org's agent username

**What happens:** A deployment lands with the wrong agent user, or a release engineer "fixes" it by assigning an admin so the agent runs.

**When it occurs:** Agent metadata is retrieved from a sandbox and deployed to production.

**How to avoid:** Replace the agent username at deploy time with string replacement, pointing at the production least-privilege user. After deploy, confirm the agent user before activation. A committed agent cannot be edited, so a wrong user means a new version.

**Source:** Agentforce Developer Guide, Use Metadata to Move an Agent to a New Org ("Your retrieved metadata contains the agent username(s) from the source org"; "You can't edit a committed agent") and Example: Configure String Replacement for Agent Username.

---

## Gotcha 11: Who can open an employee agent is a permission, and it drifts

**What happens:** An employee agent built for one team becomes available to everyone through a broad permission set.

**When it occurs:** Agent access is granted through convenience permission sets, and nobody reviews it.

**How to avoid:** Grant employee-agent access through a dedicated permission set (`agentAccesses`) assigned by group, and query `SetupEntityAccess` rows with type `BotDefinition` at each review.

**Source:** Metadata API reference, PermissionSet `agentAccesses` (API 63.0 and later: "which agents are visible to users assigned to this permission set"); Object Reference, SetupEntityAccess (`BotDefinition` for agents, API 64.0 and later).
