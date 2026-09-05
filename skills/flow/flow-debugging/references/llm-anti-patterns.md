# LLM Anti-Patterns — Flow Debugging

Common mistakes AI coding assistants make when generating or advising on diagnosing Flow issues.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting debug logs for Flow troubleshooting as the first step

**What the LLM generates:**

```
"Enable debug logs for the running user to trace the Flow execution."
```

**Why it happens:** LLMs default to Apex-style debugging. For Flow, the built-in Debug mode in Flow Builder and the Flow interview log are the primary tools — they show the exact path, variable values, and fault details without requiring debug log parsing.

**Correct pattern:**

1. Open the Flow in Flow Builder
2. Click Debug, set input variables, and run
3. Review the debug output panel for each element's path and variable values
4. For production issues, check Setup > Flows > View Flow Interviews for paused or failed interviews

Use Apex debug logs only when the issue involves Apex invocable actions called by the Flow.

**Detection hint:** Advice to "enable debug logs" as the primary debugging approach for a Flow issue.

---

## Anti-Pattern 2: Not checking entry conditions when a record-triggered flow does not fire

**What the LLM generates:**

```
"The flow might not be active. Go to Setup > Flows and activate it."
```

**Why it happens:** LLMs check the most obvious cause (inactive flow) but skip the more common cause: entry conditions that do not match the record being saved.

**Correct pattern:**

Debugging checklist for "flow not firing":
1. Is the flow active? (Check Setup > Flows)
2. Do the entry conditions match? (Check field values vs. conditions)
3. Is the trigger type correct? (Create vs. Update vs. Create or Update)
4. Does the "When to Run" setting match? (Every time vs. Only when changed to meet conditions)
5. Is there another flow or process on the same object that might be interfering?

**Detection hint:** Debugging advice for "flow not firing" that only checks activation status without mentioning entry conditions.

---

## Anti-Pattern 3: Recommending adding Screen elements for debugging in production

**What the LLM generates:**

```
"Add a Screen element before the Update Records element to display
the variable values so you can see what the flow is doing."
```

**Why it happens:** LLMs suggest adding visible debug output because it is intuitive. This approach is inappropriate for record-triggered flows (which have no UI), and adding temporary screens to production screen flows is risky.

**Correct pattern:**

- Use Flow Builder's Debug mode with test inputs
- Use the Flow Test framework to create repeatable assertions
- For record-triggered flows, check Paused and Failed Flow Interviews in Setup
- For temporary production debugging, create an Error_Log__c record with variable values

**Detection hint:** Advice to add Screen elements for debugging purposes in non-screen flow types.

---

## Anti-Pattern 4: Not considering the running user's permissions when debugging access issues

**What the LLM generates:**

```
"The flow works in my sandbox. It must be a deployment issue."
```

**Why it happens:** LLMs test against admin-level access and do not consider that the running user in production may lack field-level security, object permissions, or record access that the flow requires.

**Correct pattern:**

Debug with the correct user context:
1. In Flow Builder Debug, use "Run flow as another user" to test with a non-admin profile
2. Check that the running user has CRUD on all objects the flow accesses
3. Check FLS on all fields the flow reads or writes
4. For record-triggered flows, the running user is the user who saved the record
5. For scheduled flows, the running user is the flow creator or the context user

**Detection hint:** Debugging advice that does not mention checking the running user's profile, permission sets, or sharing rules.

---

## Anti-Pattern 5: Confusing flow versions when diagnosing production issues

**What the LLM generates:**

```
"Open the flow and check the logic in the current version."
```

**Why it happens:** LLMs reference "the flow" as a single artifact. In Salesforce, flows have multiple versions. The active version in production may differ from the latest version in the builder.

**Correct pattern:**

1. Go to Setup > Flows
2. Identify which version number is currently active
3. Open that specific version to review the logic
4. Check if a recent activation changed the version
5. Compare the active version with the previous version if the issue started after a deployment

**Detection hint:** Debugging instructions that do not specify checking the active version number.

---

## Anti-Pattern 6: Not using Flow Tests for repeatable regression verification

**What the LLM generates:**

```
"Manually test the flow by creating a record and checking the result."
```

**Why it happens:** LLMs suggest manual testing because it is the simplest approach. Flow Tests (Setup > Flow Tests) provide automated, repeatable assertions that catch regressions across deployments.

**Correct pattern:**

1. Create a Flow Test for each critical path (happy path, fault path, edge cases)
2. Define test inputs and expected assertions
3. Run Flow Tests after every deployment
4. Include Flow Tests in your CI/CD pipeline where possible

```
Flow Test: "Closed Won Opportunity creates Task"
  Input: Opportunity with StageName = "Closed Won"
  Assert: Task created with correct Subject and WhatId
```

**Detection hint:** Debugging or testing advice that relies entirely on manual record creation without mentioning Flow Tests.

---

## Anti-Pattern 7: Setting the Workflow log category to ERROR "to find the error"

**What the LLM generates:**

```
"Create a debug level with Workflow set to ERROR so the log only contains
the failures, then reproduce the issue."
```

**Why it happens:** The level name matches the word in the user's problem statement, and
filtering noise out of a log is normally good advice. The model has no model of which
event fires at which level.

**Correct pattern:**

`FLOW_ELEMENT_FAULT` — the event emitted when a fault connector catches a failure — logs at
**Workflow / WARNING and above** (`apexdev.txt` L38792). Levels are cumulative upward only
(L38389–L38403), so `ERROR` excludes `WARN` and therefore excludes every caught fault. The
better the flow's fault handling, the emptier the log at `ERROR`.

Set `Workflow` to `FINER` and everything else to `NONE`:

```json
{ "DebugLevel": { "Workflow": "FINER", "ApexCode": "NONE", "Database": "NONE",
                  "System": "NONE", "Callout": "NONE", "Visualforce": "NONE",
                  "ApexProfiling": "NONE", "Validation": "INFO" } }
```

`FINER` is also the floor for `FLOW_VALUE_ASSIGNMENT`, `FLOW_RULE_DETAIL`,
`FLOW_LOOP_DETAIL` and every `*_LIMIT_USAGE` event, so nothing below it is worth choosing.

**Detection hint:** any generated `DebugLevel` where `Workflow` is `ERROR`, `WARN` or
`INFO`, or where `ApexCode` is left at `DEBUG`/`FINEST` alongside a flow investigation.

---

## Anti-Pattern 8: Querying `FlowInterviewLog` for a record-triggered flow, then reporting "no evidence the flow ran"

**What the LLM generates:**

```
"Query FlowInterviewLog for the failed interview. Note that Flow Interview
Log entries are purged after 7 days."
```

**Why it happens:** The object name contains "FlowInterview" and "Log", which reads as the
general-purpose flow log. The seven-day figure is real but belongs to a different object.

**Correct pattern:**

`FlowInterviewLog` "represents the logs of a **screen flow** interview"
(`object_reference.txt` L140059–L140060). A record-triggered, autolaunched or scheduled flow
never writes a row. Zero rows is the documented outcome, not a finding.

For any non-screen flow, query `FlowInterview` — "represents a flow interview. A flow
interview is a running instance of a flow" (L139861), with no flow-type qualifier:

```soql
SELECT Id, InterviewLabel, CurrentElement, InterviewStatus, Error, Guid, CreatedDate
FROM FlowInterview
WHERE InterviewStatus IN ('Error', 'Paused', 'VersionPaused')
ORDER BY CreatedDate DESC
```

`Error` — "the error message that explains why the flow interview failed" — is available in
API version 62.0 and later (L139912–L139913). The seven days belongs to `ApexLog` rows whose
`Location` is `Monitoring` (L31308–L31311); no retention period for `FlowInterviewLog` is
stated in the Object Reference at all.

**Detection hint:** `FROM FlowInterviewLog` in advice about a record-triggered flow, or any
statement of a Flow Interview Log retention period.

---

## Anti-Pattern 9: Inventing `FlowExecutionErrorEvent` field names

**What the LLM generates:**

```apex
trigger FlowErrors on FlowExecutionErrorEvent (after insert) {
    for (FlowExecutionErrorEvent e : Trigger.new) {
        insert new Error_Log__c(
            Element__c = e.ElementApiName,
            Flow__c    = e.FlowApiName,
            Record__c  = e.ContextRecordId,
            Version__c = e.FlowVersionNumber
        );
    }
}
```

**Why it happens:** The event name is plausible, the field names follow the platform's usual
conventions, and the shape of a platform-event trigger is well represented in training data.
Nothing about the output signals that the field list was reconstructed rather than looked up.

**Correct pattern:**

`FlowExecutionErrorEvent` appears **nowhere** in `object_reference.txt`, `api_meta.txt`,
`apexdev.txt` or `api_rest.txt`. Neither its existence nor a single field name can be
confirmed from the Object Reference. Never emit a field list for it. Describe it first:

```bash
sf sobject describe --sobject FlowExecutionErrorEvent --target-org my-sandbox
```

If the describe returns, serialize the whole event rather than naming fields, so the code
cannot fail to compile on a field that does not exist:

```apex
for (SObject evt : Trigger.new) {
    logs.add(new Application_Log__c(
        Source__c = 'FlowExecutionErrorEvent',
        Message__c = JSON.serialize(evt)
    ));
}
```

The design of the alerting path this feeds belongs to `flow/flow-error-monitoring`.

**Detection hint:** any named field on `FlowExecutionErrorEvent` — `ErrorId`,
`ElementApiName`, `FlowVersionNumber`, `InterviewGuid`, `ContextRecordId`, `UserId` — stated
without a describe. The same test applies to any platform event an assistant names
confidently but cannot cite.
