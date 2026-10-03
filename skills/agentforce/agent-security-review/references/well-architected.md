# Well-Architected Notes — Agent Security Review

**Security:** the review answers one question per layer — which identity the action runs
as, which records that identity can reach (sharing keyword), which objects and fields it
can read or write (`WITH USER_MODE` / `AccessLevel.USER_MODE`), and what the grounding
selector puts into the prompt. Effective access is the union of profile, permission sets
and permission set groups, so the review must query it rather than read one permission
set.

**Operational Excellence:** the deliverable is a set of executable assertions stored
beside the agent metadata, not a document. Agent configuration drifts faster than a
review cadence, and only a re-runnable artefact survives the next action that ships.

## Official Sources Used

Read and checked on 2026-10-03 for this revision:

- Generative AI guide, Spring '26: Trust and Agents (Trust Layer data masking disabled for agents; permissions and access), Create an Agent from a Type (agent user), Enable Enhanced Event Logs (7-day retention), Einstein Audit and Feedback Data (data collected, storage, deletion, hourly refresh), Agent Topic: Escalation (avoid standard actions), Ground with Retrieval Augmented Generation (retriever access via Data Cloud permission sets): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf
- Metadata API Developer Guide, Summer '26 (API 67.0): GenAiPlannerBundle (rule expressions, attribute mappings, sample), Bot (`includeInPrompt`, `logPrivateConversationData`), PermissionSet (fields, `agentAccesses`, full-content deploy behaviour), GenAiFunction (`lightning:isPII`): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Apex Developer Guide, Summer '26 (API 67.0), Apex Versioned Behavior Changes (Version 67.0 user mode and sharing defaults): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Object Reference, Summer '26: PermissionSetAssignment, ObjectPermissions, FieldPermissions, SetupEntityAccess (`BotDefinition` from API 64.0), EventLogFile: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Agentforce Developer Guide, Use Metadata to Move an Agent to a New Org (agent username, committed agents, agent user permissions, do not edit retrieved agent metadata): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-deploy-metadata.html
- Agentforce Developer Guide, Example: Configure String Replacement for Agent Username: https://developer.salesforce.com/docs/ai/agentforce/guide/string-replace-example.html
- Agentforce Developer Guide, Agent Script Blocks (access block `default_agent_user`): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-blocks.html
- Agentforce Developer Guide, Knowledge Library Example (data category rules restrict what a library searches): https://developer.salesforce.com/docs/ai/agentforce/guide/adl-get-started-knowledge-library.html
- Agentforce Developer Guide, Trust Layer: https://developer.salesforce.com/docs/ai/agentforce/guide/trust.html

### Carried forward from earlier versions (not re-read on 2026-10-03)

These were not re-read for this revision. help.salesforce.com articles do not return their text to a fetch, so claims that rest only on a Help article are marked UNVERIFIED in the skill.

- Using the with sharing, without sharing, and inherited sharing Keywords — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm
- Enforcing Object and Field Permissions in Apex — WITH USER_MODE and AccessLevel.USER_MODE — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm
- PermissionSetAssignment object reference — querying effective access, including profile-owned permission sets — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_permissionsetassignment.htm
- EventLogFile object reference — ApexExecution, API and ContentTransfer event types — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm
- Agentforce Developer Guide — agent, topic and action configuration surface — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
