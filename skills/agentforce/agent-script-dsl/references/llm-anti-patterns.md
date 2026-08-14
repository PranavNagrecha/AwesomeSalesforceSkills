# LLM Anti-Patterns — Agent Script DSL

Common mistakes AI coding assistants make when generating or advising on Agent Script DSL.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using GenAiPlannerBundle Syntax Against API v63 or Lower

**What the LLM generates:** A complete `.agent` file or Metadata API manifest referencing `GenAiPlannerBundle` for a project with `sourceApiVersion` 63.0 or lower:

```yaml
spec:
  plannerBundle: MyAgent_PlannerBundle  # Wrong for API v63
```

**Why it happens:** LLMs default to GenAiPlannerBundle syntax without checking the project's API version. They also routinely misdate the cutover — the docs say "GenAiPlanner components are available in API version 60.0 to 63.0. GenAiPlannerBundle replaces GenAiPlanner in API version 64.0 and later," and v64.0 is **Summer '25**, not Spring '26 (v66.0). An assistant that repeats the Spring '26 figure will tell a team on a Winter '26 org that they need to wait for an upgrade they already have.

**Correct pattern:**

```yaml
# Project sourceApiVersion 64.0+ (Summer '25 onward) — use GenAiPlannerBundle
spec:
  plannerBundle: MyAgent_PlannerBundle

# Project sourceApiVersion 60.0–63.0 — use GenAiPlanner
spec:
  planner: MyAgent_Planner
```

**Detection hint:** Check `sourceApiVersion` in `sfdx-project.json` — the *project* pin decides, not the org's release banner. If it is 63.0 or lower, any reference to `GenAiPlannerBundle` is wrong and will fail at deploy time. Any statement that GenAiPlannerBundle "requires Spring '26" is also wrong.

---

## Anti-Pattern 2: Advising That Agent Activation Can Be Automated via Metadata API

**What the LLM generates:** Instructions telling the user to set an `isActive: true` field in BotVersion XML or a similar activation attribute to automate the Active state during deployment:

```xml
<!-- Wrong: there is no deployable activation field -->
<BotVersion>
    <isActive>true</isActive>
</BotVersion>
```

**Why it happens:** LLMs reason by analogy from other Salesforce metadata types (e.g., Flow activation, which does have a deployable status field). Agent activation state is intentionally excluded from deployable metadata to prevent accidental activation in production. LLMs are not always aware of this constraint.

**Correct pattern:**

Activation is always a manual UI step. After deploying agent metadata, navigate to Setup > Agentforce Agents (or Agentforce Builder) and click Activate. Document this as a required post-deploy manual gate in the deployment runbook. No metadata attribute can substitute for this step.

**Detection hint:** Any suggestion involving an `isActive`, `status`, or `activeVersion` attribute inside BotVersion or GenAiPlannerBundle XML intended to automate activation is incorrect.

---

## Anti-Pattern 3: Treating GenAiPlugin as Equivalent to a Flow or Trigger

**What the LLM generates:** Guidance that treats GenAiPlugin as executable logic — e.g., advising the user to add conditions, branching, or fallback behavior inside the GenAiPlugin XML:

```xml
<!-- Wrong: GenAiPlugin is a declarative topic definition, not executable logic -->
<GenAiPlugin>
    <conditions>
        <condition>...</condition>
    </conditions>
</GenAiPlugin>
```

**Why it happens:** LLMs conflate the GenAiPlugin metadata type with invocable Apex, Flow, or bot dialog state machines, all of which contain executable logic. GenAiPlugin is purely declarative — it defines the topic label, description, and action references. All executable logic lives in the Apex InvocableMethod implementations referenced by GenAiFunction records.

**Correct pattern:**

GenAiPlugin defines what the agent can do (a topic and its actions). Executable logic belongs in the Apex `@InvocableMethod` implementations or Flow actions invoked by GenAiFunction records. Keep GenAiPlugin files as declarative metadata: label, description, and action references only.

**Detection hint:** Any suggestion to add logic, conditionals, or branching inside GenAiPlugin or GenAiPlanner XML is incorrect. Executable logic belongs in GenAiFunction-referenced implementations.

---

## Anti-Pattern 4: Recommending a Finite State Machine Model for Agentforce Routing

**What the LLM generates:** Recommendations to define explicit routing rules, dialog transitions, or state machine logic in Agentforce agent configuration — analogous to how legacy Einstein Bots use dialog nodes and transitions:

```
// Wrong: Agentforce does not use FSM routing
if utterance contains "reservation":
    route to Reservations topic
else:
    route to General topic
```

**Why it happens:** Legacy Einstein Bot documentation and examples prominently feature dialog flow state machines. LLMs trained on this content extrapolate the FSM model to Agentforce, which uses a fundamentally different LLM-driven routing mechanism.

**Correct pattern:**

Agentforce routing is driven entirely by the language model. The LLM planner classifies each user utterance against the natural-language descriptions of all available topics and selects the best match. The correct way to influence routing is to write clear, specific, non-overlapping topic descriptions in the `.agent` file's `spec.topics[*].description` field — not to define explicit routing rules. The planner instructions (`spec.plannerInstructions`) can add routing constraints in natural language, but no explicit routing logic exists in the metadata.

**Detection hint:** Any suggestion to add routing conditions, transition rules, or dialog node logic to an Agentforce agent's metadata is a misapplication of Einstein Bot FSM concepts.

---

## Anti-Pattern 5: Generating a `.agent` File Without Checking LSP Diagnostics

**What the LLM generates:** A complete `.agent` YAML file with a note like "deploy this with `sf project deploy start`" — skipping the LSP validation step entirely. The file may be structurally plausible but contain field naming errors, missing required fields, or incorrect indentation that only the LSP or deploy validation would catch.

**Why it happens:** LLMs generate plausible YAML based on training data patterns. The `.agent` DSL schema is not universally well-represented in LLM training data, and subtle errors (wrong key names, missing required nested fields) are common. LLMs do not have access to the LSP schema validator at generation time.

**Correct pattern:**

Always include a validation step before recommending deploy:

1. Open the generated `.agent` file in VS Code with the Salesforce Agentforce extension active.
2. Verify zero LSP diagnostic errors or warnings before proceeding to deploy.
3. If LSP is unavailable, validate the YAML structure against the published Agentforce Agent DSL JSON Schema (available in the `@salesforce/plugin-agent` npm package).

```bash
# Optional: validate before deploy using sf agent validate (if available)
sf agent validate --spec force-app/main/default/agents/MyAgent.agent-meta.xml
```

**Detection hint:** Any AI-generated `.agent` file that skips a "validate before deploy" instruction is incomplete. Add an explicit "run LSP check or sf agent validate" step before every deploy recommendation.

---

## Anti-Pattern 6: Conflating `sf agent test run` with Apex Unit Tests

**What the LLM generates:** Instructions to include `sf agent test run` results in Apex test coverage reporting, or advice that `sf agent test run` validates Apex code coverage:

```bash
# Wrong interpretation: treating agent tests as Apex coverage tests
sf agent test run --coverage-reporters text
```

**Why it happens:** The Salesforce CLI has `sf apex run test` for Apex unit tests and `sf agent test run` for agent behavioral tests. LLMs conflate these because both are "test run" commands in the same CLI namespace, and both have `--wait` and status reporting flags.

**Correct pattern:**

`sf agent test run` executes `AiEvaluationDefinition` metadata records (`.aiTest` files) against a live deployed agent. It tests LLM routing behavior and action invocation assertions — it does not measure Apex code coverage and its results are not included in the Apex test coverage report required for production deployments. Run both `sf apex run test` (for code coverage) and `sf agent test run` (for behavioral correctness) as separate CI steps.

**Detection hint:** Any suggestion to combine `sf agent test run` results with Apex test coverage reporting, or to use it in place of `sf apex run test` for deployment code coverage gates, is incorrect.

---

## Anti-Pattern 7: Putting Deterministic Business Rules in `|` Prompt Instructions

**What the LLM generates:** Agent Script that hands a rule which must run identically every time — an entitlement check, a compliance gate, variable math, a hard branch — to a `|` prompt instruction rather than a `->` logic instruction:

```
# Wrong: a compliance gate delegated to the LLM
reasoning:
  | If the customer is not a premium member, do not offer a refund.
```

**Why it happens:** Agent Script's hybrid-reasoning model deliberately supports both natural-language (`|`) and deterministic (`->`) instructions, and natural-language phrasing is the path of least resistance for an LLM generating an agent. The distinction is easy to overlook because both forms read fluently. But per the docs, prompt instructions are "natural language sent to the LLM. The LLM interprets these instructions and decides how to respond," whereas logic instructions "run deterministically every time."

**Correct pattern:**

Behavior that must be guaranteed belongs in a `->` logic instruction with explicit conditionals; only conversational nuance belongs in a `|` prompt instruction:

```
# Right: the gate is deterministic, the messaging is conversational
reasoning:
  -> if @variables.is_premium_member != True:
       | Politely explain that refunds require a premium membership.
```

**Detection hint:** Any compliance, entitlement, security, or numeric rule expressed only as a `|` prompt instruction is suspect. Guarantee-required logic should appear as a `->` logic instruction, typically with `if` / `else` and `@variables` comparisons.

---

## Anti-Pattern 8: Treating the April 2026 Topic → Subagent Rename as a Behavioral Change

**What the LLM generates:** Advice that a `subagent` block behaves differently from an older `topic`, or a migration plan that assigns functional meaning to swapping the vocabulary — for example, claiming routing semantics changed when metadata moved from GenAiPlugin-per-topic to `subagent` blocks.

**Why it happens:** LLMs see two different terms in documentation of different vintages and infer a functional distinction. Salesforce's own docs are explicit that there is none: "Beginning in April 2026, agent topics are now called subagents. There are no changes to functionality."

**Correct pattern:**

Treat "topic" (older `.agent`/GenAiPlugin metadata) and "subagent" (newer Agent Script) as the same concept. The routing-quality principle is unchanged: the LLM classifies utterances against natural-language descriptions, so description quality — not the label of the block — is what drives correct routing.

**Detection hint:** Any claim that converting a topic to a subagent alters routing, testing, or deployment behavior is incorrect; the rename is terminology only.

---

## Anti-Pattern 9: "Modernizing" API Identifiers to the Subagent Vocabulary

**What the LLM generates:** Having learned that topics are now subagents, the assistant helpfully renames the API surface to match — in a manifest, a retrieve command, or an `.aiTest` file:

```xml
<!-- Wrong: there is no GenAiSubagent type and no subagent_sequence_match expectation -->
<types>
    <members>MyAgent_Reservations</members>
    <name>GenAiSubagent</name>
</types>
...
<expectation>
    <name>subagent_sequence_match</name>
</expectation>
```

**Why it happens:** The April 2026 rename reached the developer guide and the Builder UI but not the API. An assistant reconciling the two vocabularies assumes the metadata layer simply lags in the docs and "corrects" it. It does not lag — it never renamed. `GenAiPlugin` is still documented as "Represents an agent topic, which is a category of actions related to a particular job to be done by AI agents," and the word *subagent* does not appear on that page at all. `AiEvaluationDefinition` still uses `topic_sequence_match`.

**Correct pattern:**

Keep the API vocabulary exactly as the API defines it, and let the prose use whichever term the audience knows:

```xml
<types>
    <members>MyAgent_Reservations</members>
    <name>GenAiPlugin</name>
</types>
...
<expectation>
    <name>topic_sequence_match</name>
    <expectedValue>Reservations</expectedValue>
</expectation>
```

**Detection hint:** Any identifier containing "subagent" in a `package.xml`, an `sf project retrieve/deploy` `--metadata` flag, or an `AiEvaluationDefinition` expectation name is fabricated. Valid expectation names include `topic_sequence_match`, `action_sequence_match`, `bot_response_rating`, `output_latency_milliseconds`, `string_comparison`, and `numeric_comparison`.
