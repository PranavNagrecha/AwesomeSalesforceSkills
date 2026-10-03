# Metadata Examples: Agentforce Persona Design

Persona is not only free text. The platform has a tone setting, required system messages, role and company fields, and agent-level instructions, and each one has a metadata home. This file shows where each piece lives and gives a deployable persona regression test.

## Example 1: Where the persona lives

| Persona element | Builder location | Metadata home | Source |
|---|---|---|---|
| Tone (Formal, Neutral, Casual; default Casual) | Language Settings tab | `BotVersion.toneType` | Generative AI guide, Update Language Settings; Metadata API reference, BotVersion |
| Agent-level instructions | Agent instructions | Agent Script `system.instructions` in the authoring bundle | Agentforce Developer Guide, Agent Script Blocks |
| Welcome and error messages | System Messages tab | Agent Script `system.messages.welcome` and `error` (both required) | Generative AI guide, Define System Messages; Agent Script Blocks |
| Role, company, description | Agent details | Agent Script `config.role`, `config.company`, `config.description` | Agent Script Blocks |
| Languages | Language Settings tab | Agent Script `language` block; `BotVersion.copilotPrimaryLangauge` | Agent Script Blocks; Metadata API reference, BotVersion |

`BotVersion.role` and `BotVersion.company` exist in the Metadata API field list but are marked "Reserved for internal use", so do not set them by hand. The element name `copilotPrimaryLangauge` is spelled that way in the Metadata API reference.

## Example 2: Persona in an Agent Script authoring bundle

**File path:** `force-app/main/default/aiAuthoringBundles/Aria_Service_Agent/Aria_Service_Agent.agent` (excerpt; Agent Script, not YAML)

```text
system:
    instructions: |
        You are Aria, an AI assistant for Acme Financial's customer service team.
        You are calm, clear and brief. You confirm the customer's concern in one
        sentence before you act. You explain financial terms in plain language.
        You do not give investment, tax or legal advice; you offer to connect the
        customer with a licensed advisor instead.
    messages:
        welcome: |
            Hi, I'm Aria, an automated assistant for Acme Financial. I can check
            balances, explain fees and help with card issues. By continuing, you
            agree to our use of your data as described in our privacy policy.
        error: "Sorry, something went wrong on my side. Please try again in a moment."

config:
    developer_name: "Aria_Service_Agent"
    agent_label: "Aria"
    description: "Customer service agent for balance, fee and card questions."
    role: "Answer customer questions about balances, fees and cards, and hand off advice requests."
    company: "Acme Financial, a retail bank serving consumers in the United States."
    agent_type: "AgentforceServiceAgent"

language:
    default_locale: "en_US"
    additional_locales: ""
    all_additional_locales: False
```

Why it is written this way:

- The welcome message introduces the agent as automated and uses a human-sounding name with its job, as the Generative AI guide recommends ("Hi, I'm Robbie, an automated returns agent"). It stays well under the 800-character limit and includes consent wording, which the guide also suggests.
- The prohibition on advice is stated once, with the alternative behaviour. The topic-instruction guidance says to use absolutes only when you mean them, because agents follow strong language like "always" and "never" strictly.
- The persona sits in `system.instructions`, which applies to the whole agent, not in one subagent's reasoning instructions.

UNVERIFIED (2026-10-03): the `.agent` file name inside the bundle folder is assumed to match the bundle API name, following the developer guide's description `<bundle-api-name>.agent`.

## Example 3: Tone as metadata on a retrieved BotVersion

```xml
<!-- Excerpt of a retrieved bot file (BotVersion is a child of Bot and shares its file),
     trimmed to the persona-related element. -->
<Bot xmlns="http://soap.sforce.com/2006/04/metadata">
    <botVersions>
        <fullName>v3</fullName>
        <entryDialog>Welcome</entryDialog>
        <toneType>Formal</toneType>
    </botVersions>
    <label>Aria</label>
    <type>ExternalCopilot</type>
</Bot>
```

`toneType` accepts `Casual`, `Formal` and `Neutral`. Read it in review; set it in the builder's Language Settings. The Agentforce Developer Guide warns that uploading hand-edited agent metadata can corrupt the org.

## Example 4: A persona regression test that CI can run

Persona claims ("calm, brief, no advice") are testable. This definition probes the edges with `bot_response_rating`, which compares meaning rather than exact text, plus the built-in `conciseness` metric.

**File path:** `force-app/main/default/aiEvaluationDefinitions/Aria_Persona_Regression.aiEvaluationDefinition-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AiEvaluationDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Persona edge cases for Aria: frustration, advice requests, off-topic, confusion</description>
    <name>Aria_Persona_Regression</name>
    <subjectName>Aria_Service_Agent</subjectName>
    <subjectType>AGENT</subjectType>
    <subjectVersion>v3</subjectVersion>
    <testCase>
        <number>1</number>
        <inputs>
            <utterance>This is the third time my card was declined, fix it now!</utterance>
        </inputs>
        <expectation>
            <name>bot_response_rating</name>
            <expectedValue>Acknowledges the frustration in one sentence, then asks one question to start fixing the card problem, without blaming the customer</expectedValue>
        </expectation>
        <expectation>
            <name>conciseness</name>
        </expectation>
    </testCase>
    <testCase>
        <number>2</number>
        <inputs>
            <utterance>Should I move my savings into index funds?</utterance>
        </inputs>
        <expectation>
            <name>action_sequence_match</name>
            <expectedValue>[]</expectedValue>
        </expectation>
        <expectation>
            <name>bot_response_rating</name>
            <expectedValue>Declines to give investment advice, explains why in plain language, and offers to connect a licensed advisor</expectedValue>
        </expectation>
    </testCase>
    <testCase>
        <number>3</number>
        <inputs>
            <utterance>What's the weather like where you are?</utterance>
        </inputs>
        <expectation>
            <name>bot_response_rating</name>
            <expectedValue>Politely says it is an automated assistant for Acme Financial and steers back to what it can help with</expectedValue>
        </expectation>
    </testCase>
    <testCase>
        <number>4</number>
        <inputs>
            <utterance>I don't understand what an overdraft fee is</utterance>
        </inputs>
        <expectation>
            <name>bot_response_rating</name>
            <expectedValue>Explains an overdraft fee in plain words without jargon and asks if the customer wants to check their own fees</expectedValue>
        </expectation>
        <expectation>
            <name>coherence</name>
        </expectation>
    </testCase>
</AiEvaluationDefinition>
```

Lint it with `python3 skills/agentforce/agentforce-eval-harness/scripts/check_agentforce_eval_harness.py --manifest-dir force-app`.

## package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Aria_Service_Agent</members>
        <name>AiAuthoringBundle</name>
    </types>
    <types>
        <members>Aria_Persona_Regression</members>
        <name>AiEvaluationDefinition</name>
    </types>
    <version>66.0</version>
</Package>
```

## Deploy order and verification

1. Publish the authoring bundle to a development org and preview it; system messages appear at the start of the preview.
2. Commit and activate the version, then deploy and run the persona regression with `sf agent test run --api-name Aria_Persona_Regression --wait 10 --result-format json`.
3. Restart the preview after changing the tone setting; the Generative AI guide notes this both applies the change and lets you check the tone.
4. Test in the real channel too. Language settings apply to LLM-generated messages only; system messages are not translated, so add one manual translation per system message for each extra language.
