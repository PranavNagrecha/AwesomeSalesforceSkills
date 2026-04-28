# Examples — Flow Runtime Context And Sharing

Worked examples covering the canonical patterns. Every example includes the Flow XML snippet (the security-relevant fragment), the running-user persona, and the security implication.

---

## Example 1: User Context UI + System Context Subflow

**Context:** A Service Cloud Screen Flow lets agents log a Case-related touchpoint and silently increment a `Last_Touch_Datetime__c` field on the parent Account. Agents have read-only on the Account but full write on Cases. The parent Account is owned by Account Executives in another team and is shared via a sharing rule that grants the Service team `Read Only`.

**Problem:** If the entire Screen Flow runs as User Context, the Account update fails — agents lack edit access to the Account. If the entire flow runs as System Context Without Sharing, every Get Records on the screen bypasses sharing and may surface fields the agent shouldn't see.

**Solution:**

Top-level Screen Flow (User Context):

```xml
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <runInMode>DefaultMode</runInMode>
    <processType>Flow</processType>
    <!-- Screens, decisions, etc. — all in User Context -->
    <subflows>
        <name>Update_Account_Last_Touch</name>
        <flowName>Account_Last_Touch_Bump</flowName>
        <inputAssignments>
            <name>accountId</name>
            <value><elementReference>recordId.AccountId</elementReference></value>
        </inputAssignments>
        <inputAssignments>
            <name>touchDatetime</name>
            <value><elementReference>$Flow.CurrentDateTime</elementReference></value>
        </inputAssignments>
    </subflows>
</Flow>
```

Auto-launched Subflow `Account_Last_Touch_Bump` (System Context Without Sharing):

```xml
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <runInMode>SystemModeWithoutSharing</runInMode>
    <processType>AutoLaunchedFlow</processType>
    <description>
        Updates Account.Last_Touch_Datetime__c on behalf of Service users
        who hold Read-Only sharing on the Account. Justified as a system
        maintenance write — no user-controllable input flows into the
        update except a server-side timestamp. Audited via Account_Touch_Log__c.
    </description>
    <recordUpdates>
        <name>Update_Last_Touch</name>
        <inputReference>accountToUpdate</inputReference>
        <object>Account</object>
    </recordUpdates>
    <recordCreates>
        <name>Write_Audit_Row</name>
        <inputReference>auditRow</inputReference>
        <object>Account_Touch_Log__c</object>
    </recordCreates>
</Flow>
```

**Why it works:** The user only ever sees Account fields they're entitled to (Screen Flow stays in User Context). The privileged write happens in a tightly scoped subflow whose only inputs are an Account Id and a server-side timestamp — there is no path for the user to inject arbitrary field values. The audit log row records `$User.Id` of the original interactive user (passed as a subflow input) so security can trace every escalated write back to a real human.

---

## Example 2: Audit Query for Without-Sharing Flows

**Context:** Quarterly security review needs an inventory of every active flow running in System Context Without Sharing, plus every flow whose default behavior depends on the Spring '21 implicit default.

**Problem:** Flow XML is heterogeneous. Some flows have explicit `<runInMode>`; some rely on the API-version default; some use per-element overrides. A point-in-time audit must surface all three categories.

**Solution:**

```bash
#!/usr/bin/env bash
# audit-flow-run-modes.sh
# Emits CSV: flow_name,api_version,explicit_run_mode,override_count,classification

set -euo pipefail
ROOT="${1:-force-app/main/default/flows}"

echo "flow_name,api_version,explicit_run_mode,override_count,classification"

for f in "$ROOT"/*.flow-meta.xml; do
    name=$(basename "$f" .flow-meta.xml)
    api=$(grep -oP '(?<=<apiVersion>)[^<]+' "$f" || echo "MISSING")
    mode=$(grep -oP '(?<=<runInMode>)[^<]+' "$f" | head -1 || echo "")
    overrides=$(grep -c "<runInMode>SystemMode" "$f" || echo 0)

    # Classification:
    # P0 = explicit Without Sharing OR implicit Without Sharing under api>=52.0
    # P1 = with-sharing (review for justification)
    # P2 = User Context (default-safe)
    if [[ "$mode" == "SystemModeWithoutSharing" ]]; then
        classification="P0_EXPLICIT_WITHOUT_SHARING"
    elif [[ -z "$mode" && $(awk -v a="$api" 'BEGIN{print (a>=52.0)?1:0}') -eq 1 ]]; then
        classification="P0_IMPLICIT_WITHOUT_SHARING"
    elif [[ "$mode" == "SystemModeWithSharing" ]]; then
        classification="P1_WITH_SHARING"
    elif [[ "$mode" == "DefaultMode" || -z "$mode" ]]; then
        classification="P2_USER_CONTEXT"
    else
        classification="UNKNOWN"
    fi

    echo "$name,$api,${mode:-IMPLICIT},$overrides,$classification"
done
```

Run example output:

```
flow_name,api_version,explicit_run_mode,override_count,classification
Account_Last_Touch_Bump,62.0,SystemModeWithoutSharing,0,P0_EXPLICIT_WITHOUT_SHARING
Case_Triage_Screen,62.0,DefaultMode,1,P2_USER_CONTEXT
HR_Onboarding_Bulk_Insert,62.0,IMPLICIT,0,P0_IMPLICIT_WITHOUT_SHARING
Opportunity_Close_Date_Sync,52.0,SystemModeWithSharing,0,P1_WITH_SHARING
Legacy_Lead_Router,50.0,IMPLICIT,0,P2_USER_CONTEXT
```

**Why it works:** Every flow is classified deterministically from the XML alone — no org connection required. P0 findings get a Jira ticket; P1 findings get a justification request to the flow owner; P2 findings are filed away for the next quarter. The script is the canonical source for `agents/flow-analyzer/AGENT.md` audit-mode runs.

---

## Example 3: Per-Element Override on a Single Get Records

**Context:** A Screen Flow shows a Case-routing UI to a Tier-1 agent. The flow needs to look up the assigned Queue's owner email to display in a confirmation banner — but the agent isn't a member of that queue and can't query Group/User directly.

**Problem:** Setting the entire flow to System Context exposes every other Get Records to bypass sharing — for example, the Get Records on Contact that should respect sharing rules.

**Solution:**

Configure the flow as User Context overall, override only the queue lookup:

```xml
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <runInMode>DefaultMode</runInMode>
    <processType>Flow</processType>

    <recordLookups>
        <name>Get_Assigned_Queue</name>
        <description>
            Per-element override: SystemModeWithSharing required because
            Tier-1 agents are not Group members but need to see the queue
            owner's display name on the confirmation screen.
            Reads only DeveloperName + Email; no PII exposure.
        </description>
        <object>Group</object>
        <runInMode>SystemModeWithSharing</runInMode>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value><elementReference>queueId</elementReference></value>
        </filters>
        <queriedFields>DeveloperName</queriedFields>
        <queriedFields>Email</queriedFields>
    </recordLookups>

    <recordLookups>
        <name>Get_Contact_For_Display</name>
        <!-- No runInMode override - inherits DefaultMode (User Context) -->
        <object>Contact</object>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value><elementReference>contactId</elementReference></value>
        </filters>
        <queriedFields>Name</queriedFields>
        <queriedFields>Email</queriedFields>
    </recordLookups>
</Flow>
```

**Why it works:** Only the single Group lookup escalates. The Contact lookup stays in User Context, so if the agent doesn't have sharing on the Contact, the lookup correctly returns nothing — failing closed. The override is annotated inline in the element description, so audit scripts that read flow XML can extract the justification.

---

## Anti-Pattern: Setting an Entire Screen Flow to System Context Just to Make a Lookup Work

**What practitioners do:** A Screen Flow's Get Records on Account returns nothing because the running user lacks sharing. The "fix" is to flip the entire flow to System Context Without Sharing.

**What goes wrong:** Every other element in the flow now bypasses sharing. The Display Field that shows `Account.Annual_Revenue__c` reveals data the user shouldn't see. The Update Records that follows writes to fields the user shouldn't edit. FLS is bypassed, so even fields hidden from the user's profile appear on screen. The bug surfaces during a security audit six months later as "Tier-1 agents have de facto read access to all Accounts in the org."

**Correct approach:** Keep the flow in User Context. Add a per-element `runInMode=SystemModeWithSharing` (or `Without Sharing` if the use case truly requires it) on **only** the one Get Records that needs to escalate. Annotate inline. If the escalated read returns more than a single specific field, design a System Context Subflow (Pattern 1) that takes the record Id as input and returns only the minimum needed fields — never the full record.

---

## Anti-Pattern: Trusting `$Permission` to Branch a Scheduled Flow

**What practitioners do:** A scheduled flow checks `$Permission.Manage_Sensitive_Data` to decide whether to email a summary report. The author assumes "system runs everything, so $Permission will be true."

**What goes wrong:** Scheduled flows run as Automated Process. Automated Process has no profile, no permission set assignments, and `$Permission.X` evaluates to `false` for every X. The decision branch always takes the "false" path; the email is never sent. The bug is silent — no error, no fault email, just missing functionality.

**Correct approach:** Do not gate flow logic on `$Permission` in any flow whose running user is Automated Process (scheduled, PE-triggered, CDC-triggered). Use a Custom Metadata Type feature flag, or pass the gate value as a subflow input from a context where the running user is real.

---

## Anti-Pattern: Re-saving a Legacy Flow Without Re-Reviewing Run Mode

**What practitioners do:** A maintenance ticket asks for a small label change to a record-triggered flow created at API 50.0. The dev opens the flow in Flow Builder, fixes the label, clicks Save. Flow Builder bumps the API version to the current release. The flow originally ran in User Context (the API 50.0 default); it now runs in System Context Without Sharing (the API 62.0 default).

**What goes wrong:** The flow now bypasses sharing rules for every record-triggered execution. Records that previously failed visibility checks now succeed. Downstream automations that assumed a sharing-filtered set of records suddenly process the full org. Data leaks, performance regressions, and audit findings follow.

**Correct approach:** Before re-saving any pre-Spring-'21 flow, set `<runInMode>` explicitly to match the current behavior (`DefaultMode` would now mean Without Sharing — explicit is required). If the original behavior was sharing-enforced, set `<runInMode>SystemModeWithSharing</runInMode>` and document the choice. Add a CI check that fails the deployment if a flow's API version is bumped without a corresponding explicit `runInMode` set.

---

## Anti-Pattern: Assuming a Subflow Inherits the Parent's Run Mode

**What practitioners do:** A System Context Without Sharing parent flow calls a "shared utility" subflow. The author assumes the subflow runs in the parent's mode.

**What goes wrong:** Each flow's `runInMode` is independent. If the subflow is set to `DefaultMode` and is itself an auto-launched flow, it runs in System Context Without Sharing — coincidentally matching the parent. But if the subflow was authored as a Screen subflow or has `runInMode=SystemModeWithSharing`, it runs in its own mode regardless of the parent. The mismatch surfaces when the subflow's Get Records returns fewer records than the parent expected, or when the subflow's Update Records fails on records the parent could see but the subflow can't.

**Correct approach:** Set `<runInMode>` explicitly on every subflow. Treat each flow as a standalone security boundary. Document the contract in the subflow's description: "Expects to be called from a User Context parent; runs in System Context Without Sharing for the privileged write."
