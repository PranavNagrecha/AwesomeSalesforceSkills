# Examples — Employee HR Service Agent Rollout

Concrete examples for each rollout area. Apply in the order shown — the integration patterns assume the visibility model is in place.

---

## Example 1 — Time-off balance lookup as a read-only Apex action

**Context:** The pilot includes "what's my PTO balance?" as one of the three target workflows. The HRIS is Workday, holding leave-balance as the source of truth. The agent must show only the requesting employee's balance and never another employee's.

**Action skeleton (read-only fetch from Workday, scoped to the running user):**

```apex
public with sharing class GetMyLeaveBalance {

    public class Input {
        @InvocableVariable(label='Leave Type' description='PTO, SICK, etc' required=false)
        public String leaveType;
    }

    public class Output {
        @InvocableVariable
        public Decimal balanceHours;
        @InvocableVariable
        public String asOfDate;
        @InvocableVariable
        public String leaveType;
    }

    @InvocableMethod(
        label='Get My Leave Balance'
        description='Returns the running user\'s leave balance from the HRIS. Never accepts an employee Id parameter.'
    )
    public static List<Output> run(List<Input> inputs) {
        // Bind to the running user — never accept an employee id from the agent.
        Id callerId = UserInfo.getUserId();
        String workdayWorkerId = [
            SELECT Workday_Worker_Id__c FROM User
            WHERE Id = :callerId LIMIT 1
        ].Workday_Worker_Id__c;

        // Named Credential carries the OAuth client credentials grant for Workday.
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Workday_HRIS/v1/workers/' + workdayWorkerId + '/timeOff/balances');
        req.setMethod('GET');
        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() != 200) {
            // Surface a generic message; never echo HRIS error bodies into the LLM prompt.
            throw new AuraHandledException('Leave balance temporarily unavailable.');
        }

        // Parse only the fields needed; do not pass the full payload to the agent.
        List<Output> outputs = new List<Output>();
        for (Object raw : (List<Object>) JSON.deserializeUntyped(res.getBody())) {
            Map<String, Object> row = (Map<String, Object>) raw;
            Output o = new Output();
            o.balanceHours = (Decimal) row.get('balanceHours');
            o.asOfDate     = (String) row.get('asOfDate');
            o.leaveType    = (String) row.get('leaveType');
            outputs.add(o);
        }
        return outputs;
    }
}
```

**Why it works:**
- The action accepts NO employee identifier from the agent. The caller is bound from `UserInfo.getUserId()`, so an instruction-injection attempt that says "get the leave balance for user X" cannot succeed.
- Named Credential `Workday_HRIS` carries the OAuth credential. No secret in code. Rotation is a credential-store change, not a redeploy.
- Only the relevant fields are returned to the agent — not the entire HRIS row, which often contains pay-rate metadata that the agent should never see.

---

## Example 2 — Benefits-explainer grounded on Salesforce Knowledge

**Context:** Employees ask questions like "what does our HSA contribution match look like?" or "how many sick days do I get if I'm part-time?". The answers live in HR policy documents authored by HR ops in Confluence. Pilot decision: import the policy KB into Salesforce Knowledge for grounding, rather than using external retrieval.

**Why Knowledge over external retrieval for this pilot:**
- Salesforce Knowledge integrates natively with Agentforce grounding.
- Article-level publishing controls (Data Categories, channel availability) align cleanly with employee-vs-public visibility.
- Salesforce Knowledge supports versioning + scheduled-publish, which matches HR's annual benefits-cycle update cadence.

**Setup checklist:**

```text
1. Create a "HR Policy" Data Category Group with categories:
   - Benefits
   - Time Off
   - Onboarding
   - Compensation (manager-only)
2. Import each Confluence policy as a Knowledge article. Tag with the Data Category.
3. In Agentforce Builder → Topic: "Benefits Explainer" → Grounding:
   - Source: Salesforce Knowledge
   - Filter: Data Category = HR Policy / Benefits
   - Article publish status: Published only
4. For Compensation category: Authorize only manager profiles to retrieve articles.
5. Run the bundled checker `check_employee_hr_service_agent_rollout.py` to
   confirm no HR knowledge article is exposed via a public Experience Cloud
   channel before going live.
```

**Why it works:**
- Knowledge Data Category visibility lines up with the manager-vs-employee split. The "Compensation" category is invisible to non-manager profiles, so even if the agent's grounding accidentally tried to retrieve it for an employee user, the Knowledge query would return zero rows.
- Versioning means an annual benefits change is a "publish new version" operation, not a retrain.
- Grounding data is retrieved at request time — the agent doesn't memorize policy text, so a policy correction propagates on the next conversation, not on the next agent rebuild.

---

## Example 3 — HRIS read-write back: leave-request submission with idempotency

**Context:** Pilot has graduated past read-only. The next workflow is "submit a leave request" — agent collects start date, end date, leave type, then submits to Workday. The hard part is not the Workday call; it's handling the case where the agent says "submitted" but Workday rejected it (overlap, insufficient balance, blackout window).

**Pattern:**

```apex
public with sharing class SubmitLeaveRequest {

    public class Input {
        @InvocableVariable(required=true) public Date startDate;
        @InvocableVariable(required=true) public Date endDate;
        @InvocableVariable(required=true) public String leaveType;
        // Idempotency key generated by the agent action layer, not by the LLM.
        @InvocableVariable(required=true) public String idempotencyKey;
    }

    public class Output {
        @InvocableVariable public String status;
        @InvocableVariable public String hrisRequestId;
        @InvocableVariable public String userMessage;
    }

    @InvocableMethod(label='Submit Leave Request')
    public static List<Output> run(List<Input> inputs) {
        Input in0 = inputs[0];
        // Look up an existing local Submission record by idempotency key
        // before issuing the callout — defensive against retries.
        List<Leave_Submission__c> existing = [
            SELECT Id, HRIS_Request_Id__c, Status__c
            FROM Leave_Submission__c
            WHERE Idempotency_Key__c = :in0.idempotencyKey
            LIMIT 1
        ];

        Output out = new Output();

        if (!existing.isEmpty()) {
            out.status         = existing[0].Status__c;
            out.hrisRequestId  = existing[0].HRIS_Request_Id__c;
            out.userMessage    = 'Your leave request was already submitted.';
            return new List<Output>{ out };
        }

        // Create local Submission as PENDING, callout, then update.
        Leave_Submission__c sub = new Leave_Submission__c(
            Idempotency_Key__c = in0.idempotencyKey,
            Status__c          = 'PENDING',
            Employee__c        = UserInfo.getUserId(),
            Start_Date__c      = in0.startDate,
            End_Date__c        = in0.endDate,
            Leave_Type__c      = in0.leaveType
        );
        insert sub;

        // ... call Workday, set sub.Status__c to ACCEPTED / REJECTED, update sub ...
        // On REJECT, return the user-friendly reason but do NOT echo the raw
        // Workday error body to the agent.
        return new List<Output>{ out };
    }
}
```

**Why it works:**
- The local `Leave_Submission__c` row is the agent's source of truth for "did I submit this already." Even if the agent action is retried due to a network timeout, the second call sees the existing row and returns the original outcome instead of double-submitting.
- The agent message on reject is curated text, not the raw HRIS error. HRIS errors leak field names and internal codes that an end employee should never see.
- The local row provides a reconciliation handle for HR ops if the HRIS submission later fails async (e.g., manager-approval rejected). HR can re-open the local row and the agent can re-deliver an updated message.

---

## Example 4 — Slack-first deployment with employee-self enforcement

**Context:** Pilot org is Slack-native (Slack Enterprise Grid, all employees in the workspace). Decision: Slack-first surface. The agent must respond only to the employee in DM and never expose another employee's data when @-mentioned in a channel.

**Configuration approach:**

```text
1. Agentforce Builder → Channels → Slack → Connect Workspace
   - Use the managed Agentforce for Slack app.
   - Authorize the workspace under an admin OAuth grant.
2. Channel scope: limit the agent to direct messages and ephemeral responses
   in #hr-help. Do NOT expose the agent in arbitrary channels.
3. Bind every agent action to UserInfo.getUserId() — derived from the
   Slack-to-Salesforce user mapping. Agent actions reject calls where the
   Slack user has no Salesforce user mapping.
4. Test the agent by:
   a. DM the bot from a regular employee account; confirm only that
      employee's data is shown.
   b. @-mention the bot in #general from a manager account; confirm the
      agent declines to answer (channel scope rejects that surface).
   c. DM from a contractor account with no Salesforce mapping; confirm
      the agent declines with a "your account isn't provisioned" message.
```

**Why it works:**
- The Slack-to-Salesforce user mapping is the trust boundary. The agent action can call `UserInfo.getUserId()` and trust the result because the channel layer mapped Slack identity to Salesforce identity. If that mapping is missing, the user is unauthenticated, and the action refuses.
- Restricting the agent to DM + a single named HR channel reduces the public-channel surface where a curious user could ask "show me everyone's PTO" hoping the agent forgets the visibility model.
- The pilot test list (regular employee, manager, contractor) covers the three personas the visibility model must distinguish. Skip the contractor case at your peril — many orgs allow contractor accounts in Slack but never authorize them for HR self-service.

---

## Example 5 — Measurement instrumentation from day 1

**Context:** Stakeholders will ask "is it working?" within two weeks of launch. Without instrumentation, the answer is anecdote. With instrumentation, the answer is a chart.

**Three metrics to instrument from day 1:**

| Metric | How to measure | Baseline source |
|---|---|---|
| **Deflection rate** | Count of agent sessions where the user did not subsequently file an HR case in the same week. Compare to historical HR-case-creation rate per active employee per week. | Pre-launch: 4 weeks of HR Case volume from `Case` records with `Origin = 'HR'` or RecordType. Post-launch: subtract sessions answered by agent. |
| **First response time (FRT)** | Median time from session start to first agent message. Agentforce session telemetry exposes this. | Compare to median time-to-first-response on HR cases (often 4–24 hours). Agent FRT should be seconds to single-digit seconds. |
| **CSAT / thumbs-up** | Per-session pulse: thumbs up/down + 1-question survey on session close. | Baseline: post-resolution CSAT on closed HR cases (often around 70–85% in mature orgs). |

**Acceptance bar for moving from pilot to GA:** deflection ≥ 30% on in-scope workflows, FRT < 30 seconds median, CSAT ≥ baseline of HR cases.

**Why this matters:** Pilot success is a contested narrative. A skeptical HR director will believe a chart that compares pre-launch case volume to post-launch case volume; they will not believe a vendor demo. Instrument before you launch.
