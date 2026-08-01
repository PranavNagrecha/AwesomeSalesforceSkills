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

- Using the with sharing, without sharing, and inherited sharing Keywords — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm
- Enforcing Object and Field Permissions in Apex — WITH USER_MODE and AccessLevel.USER_MODE — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm
- PermissionSetAssignment object reference — querying effective access, including profile-owned permission sets — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_permissionsetassignment.htm
- EventLogFile object reference — ApexExecution, API and ContentTransfer event types — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm
- Agentforce Developer Guide — agent, topic and action configuration surface — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
