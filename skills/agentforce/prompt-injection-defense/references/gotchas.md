# Gotchas: Prompt Injection Defense

Non-obvious behaviours that let an injection succeed, or let a red-team pass that should fail. Each gotcha names its source. "GenAI Guide" means Quickstart Your Einstein Generative AI Solution, Spring '26 (generative_ai.pdf). "Apex Guide" means the Apex Developer Guide, Version 67.0. "Metadata API" means the Metadata API Developer Guide, Version 67.0.

## Gotcha 1: Subagent Instructions Are Not Enforcement

**What happens:** A refund rule lives only in the subagent instructions ("only refund delivered orders"), and a role-play jailbreak gets the refund issued.

**When it occurs:** "Instructions are nondeterministic and rely on an LLM for interpretation. They don't replace the need for coded business rules." The guide's own example: "instead of adding the instruction 'Don't refund an order unless it was within 30 business days,' create a flow-based agent action that assesses the criteria for issuing a refund."

**How to avoid:** Put every sensitive or deterministic rule inside the action: re-query the facts under the running user and refuse in code. Keep the instruction only to reduce how often the model tries. The skill checker flags instructions that carry numeric business rules (`PI-TOPIC-01`).

**Source:** GenAI Guide, Best Practices for Writing Topic Instructions.

---

## Gotcha 2: A Custom Action Runs With the Access of the Apex Class or Flow Behind It

**What happens:** A low-privilege channel user talks the agent into an action that reads or changes records the user could never open.

**When it occurs:** "Access to a custom action depends on the Apex class, flow, or prompt template the action references. For example, if a custom action is built using a flow, the custom action adheres to the permissions, field-level security, and sharing settings configured in the flow." An Apex class declared `without sharing`, or queries with `WITH SYSTEM_MODE`, bypass the user's sharing or permissions. In API 67.0 and later, database operations default to user mode "unless system mode is explicitly specified."

**How to avoid:** Declare `with sharing` on action classes, keep queries and DML in user mode, and justify any system-mode exception in writing. The checker flags `without sharing`, `WITH SYSTEM_MODE`, and `AccessLevel.SYSTEM_MODE` in invocable classes (`PI-SYS-01`).

**Source:** GenAI Guide, What are Agents? (Permissions and Access). Apex Guide, Use the with sharing, without sharing, and inherited sharing Keywords (Implementation in Apex Triggers; Best Practices; Versioned Behavior Changes).

---

## Gotcha 3: The Model Trusts Values It Was Asked to Supply

**What happens:** An action takes a Boolean such as `statusIsDelivered` from the model, and the attacker simply asserts it.

**When it occurs:** Any action input that encodes a fact the server could look up. Prompt injection is "a method used to control or manipulate the model's output by giving it certain prompts," and model-filled inputs are model output. UNVERIFIED (2026-10-03): no fetched source catalogues this pattern; it follows from the glossary definition and Gotcha 1.

**How to avoid:** Accept identifiers from the model, never verdicts. Re-query status, eligibility, and ownership in the action. The checker flags Boolean request variables named like verdicts (`PI-TRUST-01`).

**Source:** GenAI Guide, Einstein Generative AI Glossary of Terms (Prompt injection); Best Practices for Writing Topic Instructions.

---

## Gotcha 4: Masking Is Off for Agents, So Nothing Scrubs What the Model Repeats

**What happens:** A crafted record persuades the agent to repeat an internal email address, and nothing masks it on the way to the customer.

**When it occurs:** "Data masking through the Einstein Trust Layer is disabled to improve the performance and accuracy of agents." Masking elsewhere is a pre-prompt replacement with demasking of the response, not an output filter. Secure data retrieval still limits grounding to what the running user can access.

**How to avoid:** Remove the data from the prompt instead of hoping to mask it: narrow grounding projections, keep internal-only fields out of agent-facing queries, and add a leakage case to the suite for every sensitive field.

**Source:** GenAI Guide, Agentforce Agents (Einstein Trust Layer section); Einstein Trust Layer: Designed for Trust (Data Masking for the LLM; Data Demasking).

---

## Gotcha 5: English-Only Suites Miss Multilingual Payloads

**What happens:** Injection passes the English suite but succeeds in Spanish or French.

**When it occurs:** Multi-lingual deployments. Trust Layer toxicity detection and masking have region and language support tables, and the guide warns that region-specific language "presents difficulties in effectively identifying harmful or inappropriate content." When adding languages to an agent, the guide says to "consider the regions and languages where the Einstein Trust Layer detects and masks sensitive data."

**How to avoid:** Include at least two non-English versions of each adversarial prompt, plus one mixed-language prompt. The checker warns when a suite has no non-English utterance (`PI-SUITE-02`).

**Source:** GenAI Guide, Einstein Trust Layer Region and Language Support (Toxicity Detection); agent Language Settings step.

---

## Gotcha 6: A Suite That Is Not Versioned With the Agent Tests the Wrong Thing

**What happens:** The suite passes, but it ran against an older agent version, or nobody re-ran it after a topic edit.

**When it occurs:** AiEvaluationDefinition `subjectVersion` is "The agent version to test. If not provided, the latest active version is used by default." To edit a topic, the guide's steps begin "If your agent is active, deactivate it," so edits create new behaviour that the old results do not cover.

**How to avoid:** Keep the suite as an AiEvaluationDefinition in source control beside the agent, set `subjectVersion` explicitly for release tests, and re-run on every topic or action change.

**Source:** Metadata API, AiEvaluationDefinition (subjectVersion, testCase, expectation). GenAI Guide, Create a Custom Topic and Edit a Standard Topic (deactivate step).

---

## Gotcha 7: More Instructions Make a Weaker Subagent

**What happens:** Each incident adds a sentence, and after a few months 100-line instructions contradict each other and slow every turn.

**When it occurs:** "Start with minimal instructions, and iterate as needed." "Contradicting instructions can cause errors and degrade performance." "The LLM doesn't use the visual order of instructions in the Topic Configuration tab to make decisions." And "an agent tends to strictly follow strong language like 'always' and 'never.'"

**How to avoid:** Collapse patterns into a few hard rules, each naming the action that verifies the fact. Use "never" only where you mean it. Move everything else into the suite. The checker warns when a topic carries more than 15 instructions (`PI-TOPIC-02`, a review heuristic).

**Source:** GenAI Guide, Best Practices for Writing Topic Instructions.

---

## Gotcha 8: There Is No Toxicity or Injection Threshold to Tune

**What happens:** A team plans to "raise the Trust Layer threshold" to stop jailbreaks and finds no such setting.

**When it occurs:** Toxicity scores are logged to Data Cloud for review, and the guide notes that `isToxicityDetected = false` "doesn't necessarily mean there isn't toxicity." EinsteinAISettings lists `enableAITrustPromptInjectionDetection` and `enableAITrustInputToxicityDetection` as "Reserved for internal use." UNVERIFIED (2026-10-03): the earlier gotcha about calibrating a toxicity threshold described a setting that no fetched source documents.

**How to avoid:** Treat Trust Layer scoring as monitoring. Put the controls you can change (action logic, access mode, grounding scope, instructions) under test instead.

**Source:** GenAI Guide, Review Toxicity Scores. Metadata API, EinsteinAISettings.
