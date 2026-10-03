# Metadata Examples: Agentforce Agent Creation

This file shows the deployable pieces of standing up and promoting an agent: org readiness as a settings file, the agent manifest for API 67.0 and earlier, string replacement for the agent user, and the command sequence that deploys, activates and smoke-tests the agent.

API version note. The Agentforce Developer Guide says agent metadata is updated in API 68.0 (new types `AiAgentDefinition` and `AiAgentDefinitionVersion`), and both orgs must be on 68.0 to use them. Summer '26 is API 67.0, so this file uses the 67.0-and-earlier types: `Bot`, `BotVersion`, `GenAiPlannerBundle`, `AiAuthoringBundle`, `GenAiPlugin`, `GenAiFunction`.

## Example 1: Org readiness as code

Generative AI must be on before Agents appears in Setup. The setting is deployable.

**File path:** `force-app/main/default/settings/EinsteinGpt.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EinsteinGptSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableEinsteinGptPlatform>true</enableEinsteinGptPlatform>
</EinsteinGptSettings>
```

`enableEinsteinGptPlatform` "indicates whether to turn on generative AI features across Salesforce" (Metadata API reference, EinsteinGptSettings, API 61.0 and later). Do not copy the reference's own sample file: its closing tags do not match its opening tags (`<enableEinsteinGptPlatform>true</reRunAttributeBasedRules>`), so it does not parse. Turning on Agentforce itself is a separate Setup toggle; UNVERIFIED (2026-10-03): no settings field for that toggle was found in the Metadata API reference.

## Example 2: Manifest for one agent version (API 67.0 and earlier)

**File path:** `manifest/agent-NGA_Service_Agent-v2.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- BotVersion, not Bot, selects one version of the agent. -->
    <types>
        <members>NGA_Service_Agent.v2</members>
        <name>BotVersion</name>
    </types>
    <types>
        <members>NGA_Service_Agent_v2</members>
        <name>GenAiPlannerBundle</name>
    </types>
    <types>
        <members>NGA_Service_Agent_2</members>
        <name>AiAuthoringBundle</name>
    </types>
    <types>
        <members>Order_Support</members>
        <name>GenAiPlugin</name>
    </types>
    <types>
        <members>Look_Up_Order_Status</members>
        <name>GenAiFunction</name>
    </types>
    <!-- Name the Apex, flows and templates the agent uses. Wildcards here can pull
         excessive data and lead to very long deployments or timeouts. -->
    <types>
        <members>OrderStatusLookupAction</members>
        <name>ApexClass</name>
    </types>
    <version>66.0</version>
</Package>
```

The member forms come from the Agentforce Developer Guide sample "Manifest Defining a Single Agent Version (v67 and Earlier)", which also uses version 66.0. Three rules from that page decide whether the deploy works:

- Before deploying a single version with `BotVersion`, the full agent must already exist in the target org. The first deployment uses the all-agents form (`Bot` with `*`, or the agent name) so every required component is created.
- When you saved more versions than you committed, the `AiAuthoringBundle` version number differs from the `BotVersion` and `GenAiPlannerBundle` version. Read the `target` in the bundle's `bundle-meta.xml` to find the matching pair.
- Name each `ApexClass`, `Flow` and `GenAiPromptTemplate` instead of using `*`.

`Order_Support`, `Look_Up_Order_Status` and `OrderStatusLookupAction` are the subagent, action and class from `agentforce/agentforce-tool-use-patterns`; substitute your own.

## Example 3: Replace the agent username per target org

Retrieved agent metadata carries the source org's agent username. Agents run in the context of a user, and usernames differ between orgs.

**File path:** `sfdx-project.json` (excerpt: the `replacements` array is the relevant part)

```json
{
  "packageDirectories": [{ "path": "force-app", "default": true }],
  "name": "service-agent",
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "66.0",
  "replacements": [
    {
      "glob": "force-app/main/default/bots/**/*-meta.xml",
      "stringToReplace": "serviceagent.sandbox@example.com",
      "replaceWithEnv": "TARGET_AGENT_USER"
    },
    {
      "glob": "force-app/main/default/aiAuthoringBundles/**/*.agent",
      "stringToReplace": "serviceagent.sandbox@example.com",
      "replaceWithEnv": "TARGET_AGENT_USER"
    }
  ]
}
```

The structure follows the Agentforce Developer Guide "Example: Configure String Replacement for Agent Username". String replacement works only for a draft agent. A committed agent cannot be edited, so to change its user you create a new version and set the user there. If you deploy without replacement, you must set the agent user manually before the agent can run.

## Example 4: Deploy, activate and smoke-test

```bash
# 1. Org readiness and the action layer first. Publishing an agent does not deploy Apex or flows.
sf project deploy start --source-dir force-app/main/default/settings --target-org prod
sf project deploy start --source-dir force-app/main/default/classes --target-org prod

# 2. The agent itself, with the production agent user substituted.
TARGET_AGENT_USER="serviceagent@example.com" \
  sf project deploy start --manifest manifest/agent-NGA_Service_Agent-v2.xml --target-org prod

# 3. Activate the exact version. --version is the number from "vX".
sf agent activate --api-name NGA_Service_Agent --version 2 --target-org prod

# 4. Smoke-test against the active version.
sf agent test run --api-name NGA_Service_Agent_Smoke --target-org prod --wait 10 --result-format json --output-dir results
```

Activation is its own step. Only one version can be active, and activating a committed version deactivates the version that was active. A smoke test belongs after activation because some tests need an active agent.

## Example 5: The same settings in Agent Script (authoring bundles)

For agents built with Agent Script, the identity and logging settings live in the `.agent` file inside `aiAuthoringBundles/<api-name>/`. Excerpt:

```text
config:
    developer_name: "NGA_Service_Agent"
    agent_label: "Service Agent"
    description: "Answers order questions and escalates billing disputes to a service rep."
    agent_type: "AgentforceServiceAgent"
    enable_enhanced_event_logs: True

access:
    default_agent_user: "serviceagent@example.com"
```

`developer_name` is at most 80 characters, starts with a letter, uses letters, digits and underscores, cannot end with an underscore or contain two in a row, and must be unique in the org. `default_agent_user` is required for Agentforce Service agents (Agentforce Developer Guide, Agent Script Blocks).

## Verification

- `sf org open agent --api-name NGA_Service_Agent --target-org prod` opens the agent; the active version is v2 and the agent user is the production user.
- The Enhanced Chat v2 or Messaging channel shows the agent as its routing target. The agent must be active before a channel can route to it.
- The smoke test JSON shows every case with a `metricScore`; an exit code of 1 means execution errors, not failed assertions.
