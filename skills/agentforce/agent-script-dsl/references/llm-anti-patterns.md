# LLM Anti-Patterns — Agent Script DSL

Common mistakes AI coding assistants make when generating or advising on Agent Script DSL.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using GenAiPlannerBundle Syntax Against API v63 or Lower

**What the LLM generates:** A complete `.agent` file or Metadata API manifest referencing `GenAiPlannerBundle` for a project with `apiVersion: 63.0` or lower:

```yaml
spec:
  plannerBundle: MyAgent_PlannerBundle  # Wrong for API v63
```

**Why it happens:** LLMs trained on Spring '26+ documentation default to GenAiPlannerBundle syntax without checking the target API version. The distinction between GenAiPlanner (v60–v63) and GenAiPlannerBundle (v64+) is a version-gated API change that is easy to miss.

**Correct pattern:**

```yaml
# For API v64+ (Spring '26+) — use GenAiPlannerBundle
spec:
  plannerBundle: MyAgent_PlannerBundle

# For API v60–v63 — use GenAiPlanner
spec:
  planner: MyAgent_Planner
```

**Detection hint:** Check the `apiVersion` in `sfdx-project.json`. If it is 63.0 or lower, any reference to `GenAiPlannerBundle` is wrong and will fail at deploy time.

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
