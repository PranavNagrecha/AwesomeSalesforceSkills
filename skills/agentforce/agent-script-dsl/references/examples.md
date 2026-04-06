# Examples — Agent Script DSL

## Example 1: Scaffolding and Deploying a New Agent from Source Control

**Context:** A team is building a new Agentforce Service Agent for a Spring '26 org and wants to manage all agent configuration in a Git repository for pull-request review and pipeline deployment.

**Problem:** Without source control, each agent configuration change requires manual UI work in Agentforce Builder in each environment, with no audit trail and no ability to roll back to a known-good state.

**Solution:**

```bash
# 1. Generate the agent scaffold in the DX project
sf agent generate agent \
  --name HospitalityServiceAgent \
  --target-org DevSandbox

# 2. Edit the generated .agent file in VS Code with Agentforce extension.
# Verify LSP reports no errors before continuing.

# 3. Deploy the full metadata bundle atomically
sf project deploy start \
  --metadata Bot:HospitalityServiceAgent \
  --metadata "BotVersion:HospitalityServiceAgent.v1" \
  --metadata "GenAiPlannerBundle:HospitalityServiceAgent" \
  --metadata "GenAiPlugin:HospitalityServiceAgent_Reservations" \
  --metadata "GenAiPlugin:HospitalityServiceAgent_GuestExperiences" \
  --target-org DevSandbox \
  --wait 10

# 4. After deploy, manually activate the agent in Setup > Agentforce Agents

# 5. Run agent tests
sf agent test run \
  --spec force-app/main/default/aiTests/HospitalityServiceAgentTest.aiTest-meta.xml \
  --target-org DevSandbox \
  --wait 10
```

**Why it works:** The `sf agent generate agent` command creates a structurally valid `.agent` file and the linked BotVersion/GenAiPlannerBundle stubs. Deploying all metadata types together in a single `sf project deploy start` call ensures the org reaches a consistent state atomically. The LSP check before deploy catches YAML schema errors locally before consuming deploy limits.

---

## Example 2: Retrieving an Agent Modified in the UI Back to Source Control

**Context:** A developer updated the agent's system instructions directly in Agentforce Builder during a debugging session. The source-controlled `.agent` file is now out of date.

**Problem:** If the team deploys from the stale source-controlled version, the planner instructions and topic descriptions updated in the Builder will be overwritten, silently reverting the agent to its previous behavior.

**Solution:**

```bash
# 1. Retrieve the full current agent state from the org
sf project retrieve start \
  --metadata Bot:HospitalityServiceAgent \
  --metadata "BotVersion:HospitalityServiceAgent.v1" \
  --metadata "GenAiPlannerBundle:HospitalityServiceAgent" \
  --metadata "GenAiPlugin:HospitalityServiceAgent_Reservations" \
  --metadata "GenAiPlugin:HospitalityServiceAgent_GuestExperiences" \
  --target-org DevSandbox

# 2. Review the diff
git diff force-app/main/default/

# 3. Commit the reconciled state before the next deploy
git add force-app/main/default/genAiPlugins/ \
        force-app/main/default/genAiPlannerBundles/ \
        force-app/main/default/bots/
git commit -m "chore: sync agent metadata from DevSandbox UI changes"
```

**Why it works:** Retrieving before committing makes the source-controlled version authoritative again. The `git diff` step surfaces any modifications made in the Builder that the team may not have reviewed — critical for catching accidental changes to `plannerInstructions` which are plain-text fields overwritten entirely on each retrieve.

---

## Example 3: Writing an .aiTest File for CI Pipeline Agent Testing

**Context:** A CI pipeline needs to verify that the agent routes to the correct topic and invokes the expected action for a set of canonical test utterances.

**Problem:** Without automated tests, pipeline promotion to staging or production has no signal about whether the agent's LLM routing behavior is correct after a metadata change.

**Solution:**

```xml
<!-- force-app/main/default/aiTests/HospitalityServiceAgentTest.aiTest-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<AiEvaluationDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>HospitalityServiceAgentTest</name>
    <subjectType>AGENT</subjectType>
    <subjectName>HospitalityServiceAgent</subjectName>
    <testCases>
        <testCase>
            <inputs>
                <utterance>I need to change my reservation for next Friday</utterance>
            </inputs>
            <expectedResults>
                <expectation>
                    <name>TopicClassification</name>
                    <expectedValue>Reservations</expectedValue>
                </expectation>
            </expectedResults>
        </testCase>
        <testCase>
            <inputs>
                <utterance>What activities are available at the resort this weekend?</utterance>
            </inputs>
            <expectedResults>
                <expectation>
                    <name>TopicClassification</name>
                    <expectedValue>GuestExperiences</expectedValue>
                </expectation>
            </expectedResults>
        </testCase>
    </testCases>
</AiEvaluationDefinition>
```

```bash
# Run in CI
sf agent test run \
  --spec force-app/main/default/aiTests/HospitalityServiceAgentTest.aiTest-meta.xml \
  --target-org StagingOrg \
  --wait 15
# Exit code 0 = all assertions passed; exit code 1 = failure or timeout
```

**Why it works:** `.aiTest` metadata records express topic classification and action invocation expectations as assertions the `sf agent test run` command evaluates against the live agent in the target org. The CLI exit code integrates cleanly with CI tools (GitHub Actions, Bitbucket Pipelines, Jenkins). This is the only scriptable mechanism for automated agent behavioral testing without a live UI session.

---

## Anti-Pattern: Deploying Only GenAiPlugin Without the BotVersion

**What practitioners do:** A developer edits a topic description in a GenAiPlugin XML file and deploys only that file to speed up iteration:

```bash
# Wrong: partial deploy
sf project deploy start \
  --metadata "GenAiPlugin:HospitalityServiceAgent_Reservations" \
  --target-org DevSandbox
```

**What goes wrong:** The deployed GenAiPlugin is now ahead of the BotVersion and GenAiPlannerBundle in the org. The next full bundle deploy (including BotVersion) may fail validation or silently overwrite the plugin change if the BotVersion being deployed still references the previous plugin version. In worst cases, the agent appears active but exhibits routing behavior inconsistent with any source-controlled version.

**Correct approach:** Always deploy the full metadata bundle atomically. Use a named manifest (`package.xml`) that lists all required metadata types together, and enforce this in the CI pipeline:

```xml
<!-- manifest/agent-bundle.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>HospitalityServiceAgent</members>
        <name>Bot</name>
    </types>
    <types>
        <members>HospitalityServiceAgent.v1</members>
        <name>BotVersion</name>
    </types>
    <types>
        <members>HospitalityServiceAgent</members>
        <name>GenAiPlannerBundle</name>
    </types>
    <types>
        <members>HospitalityServiceAgent_Reservations</members>
        <members>HospitalityServiceAgent_GuestExperiences</members>
        <name>GenAiPlugin</name>
    </types>
    <version>64.0</version>
</Package>
```

```bash
sf project deploy start --manifest manifest/agent-bundle.xml --target-org DevSandbox
```
