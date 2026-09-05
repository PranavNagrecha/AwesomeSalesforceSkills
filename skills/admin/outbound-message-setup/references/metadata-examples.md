# Metadata Examples — Outbound Message Setup

Deployable XML for the one metadata type an outbound message is made of: `Workflow`. There is no
standalone `OutboundMessage` type — a `WorkflowOutboundMessage` is an element inside the object's
`.workflow` file (api_meta.txt L139931), and the `WorkflowRule` that fires it is another element in the
same file (L139937). Shapes below are taken from the Metadata API Developer Guide (v62 PDF —
`Workflow` L139890–139948, `WorkflowActionReference` L139952–139966, `WorkflowOutboundMessage`
L140312–140371, `WorkflowRule` L140373–140436, `WorkflowTimeTrigger` L140524–140546, the guide's own
Declarative Metadata Sample Definition L140553–140736) and extended to one worked Account example.

Two things this file deliberately does not own:

- **The listener's response contract.** `notificationsResponse` is a single boolean `Ack`, and the
  `notifications` envelope carries up to 100 `Notification` elements per message — see
  [Understanding Outbound Messaging](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_understanding.htm)
  and [Building a Listener](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_wsdl.htm).
  The envelope table is in `SKILL.md` § The `notifications()` Envelope; the response body is in
  `templates/outbound-message-setup-template.md`.
- **The listener implementation.** `integration/outbound-messages-and-callbacks` covers parsing the
  envelope and using the session ID to call back.

## Where the files live

| Type | package.xml `<name>` | `<members>` syntax | Wildcard `*` | MDAPI source file | API |
|---|---|---|---|---|---|
| `Workflow` | `Workflow` | the object API name (`Account`, `My_Object__c`) | **Supported** (L140742–140744) | `workflows/Account.workflow` | 13.0+ (L139902) |
| `ApprovalProcess` | `ApprovalProcess` | `<Object>.<ProcessName>` | see the guide's `ApprovalProcess` section | `approvalProcesses/Account.Tier_Upgrade.approvalProcess` | 28.0+ (L23071) |

"Workflow files have the suffix `.workflow`. There's one file per standard or custom object that has
workflow. These files are stored in the `workflows` directory of the corresponding package"
(L139896–139898). In a Salesforce DX project the same file is `force-app/main/default/workflows/Account.workflow-meta.xml`.

**The single most important consequence:** the file is the object's *whole* workflow surface — alerts,
field updates, tasks, rules, outbound messages (L139908–139948). A deploy of a hand-written `Account.workflow`
that contains only your new outbound message removes the rest. Always retrieve first (§ 6).

---

## 1. The outbound message

`force-app/main/default/workflows/Account.workflow-meta.xml` — the `outboundMessages` element only.
The full file, with the rule wired to it, is § 3.

```xml
<outboundMessages>
    <fullName>Notify_ERP_Of_Tier_Change</fullName>
    <apiVersion>62.0</apiVersion>
    <description>Pushes the account tier change to the ERP account-master listener. Owner: Integration Platform team. Field list is contract-bound: adding a field requires the listener to regenerate its WSDL.</description>
    <endpointUrl>https://erp.example.com/sfdc/listener/account-master</endpointUrl>
    <fields>Id</fields>
    <fields>AccountNumber</fields>
    <fields>Name</fields>
    <fields>BillingCountry</fields>
    <fields>Customer_Tier__c</fields>
    <fields>LastModifiedDate</fields>
    <includeSessionId>false</includeSessionId>
    <integrationUser>erp.integration@example.com</integrationUser>
    <name>Notify ERP Of Tier Change</name>
    <protected>false</protected>
    <useDeadLetterQueue>true</useDeadLetterQueue>
</outboundMessages>
```

**How to read it**

- `fullName` is the developer name and the string every rule and approval action must match. It "can
  contain only underscores and alphanumeric characters. It must be unique, begin with a letter, not
  include spaces, not end with an underscore, and not contain two consecutive underscores"
  (L140348–140352). `name` is the separate human label, `Required`, API 16.0+ (L140361).
- `apiVersion` is `Required` and "automatically set to the current API version when the outbound message
  is created" (L140327–140328). Valid values are **8.0 and 18.0 or later** (L140329) — 17.0 is not a
  legal value. It "can only be modified by using Metadata API. It can't be modified using the Salesforce
  user interface" (L140332–140334), which is exactly why this file belongs in version control. Note the
  guide's own sample omits `apiVersion` entirely (L140624–140633); a retrieve fills it in with whatever
  the org assigned, so commit the value you intend rather than the value you inherited.
- `endpointUrl` is `Required` (L140344). The guide's sample uses `http://www.test.com` (L140626) — that
  is a placeholder, not a recommendation. `scripts/check_outbound_message_setup.py` fails any endpoint
  that is not `https`. The platform also constrains the port: "Salesforce restricts the outbound ports
  you can specify to one of the following: 80: This port only accepts HTTP connections. 443: This port
  only accepts HTTPS connections. 1024–66535 (inclusive): These ports accept HTTP or HTTPS connections"
  ([Defining Outbound Messaging](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_setting_up.htm)).
  So an HTTPS endpoint on port 8443 is legal and one on port 80 is not. The same page adds a certificate
  requirement that outlives the deploy: "the common name (CN) of the certificate must match the domain
  name for your endpoint's server, and the certificate must be issued by a Certificate Authority trusted
  by Java 2 Platform, Standard Edition (J2SE) 5.0 (JDK 1.5). If your certificate expires, message
  delivery fails."
- `fields` is "the named references to the fields to be sent" (L140346) and is *not* marked `Required`.
  A file with zero `<fields>` elements deploys. Include `Id` deliberately: it is the correlation key the
  listener needs, and nothing in the metadata guarantees it otherwise.
- `includeSessionId` is `Required` and is set "if you want the Salesforce session ID included in the
  outbound message. Useful if you intend to make API calls and you don't want to include a username and
  password" (L140354–140357). `false` unless the listener genuinely calls back — see gotcha 6.
- `integrationUser` is `Required`: "the named reference to the user under which this message is sent"
  (L140359). It is also the payload's access filter — "The chosen user controls data visibility for the
  message that is sent to the endpoint" — and the identity `SessionId` represents: it "represents the
  user defined in the previous step and not the user who triggered the workflow"
  ([Defining Outbound Messaging](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_setting_up.htm)).
  Use a dedicated integration user, not a departing admin, and do not give it the Send Outbound Messages
  permission if the listener writes back (gotcha 11).
- `protected` is `Required`; protected components "can't be linked to or referenced by components created
  in the installing organization" (L140363–140366). `false` for org-native config, `true` only inside a
  managed package.
- `useDeadLetterQueue` "is only available for organizations with dead letter queue permissions turned on.
  If set, this outbound message uses the dead letter queue if normal delivery fails" (L140368–140371). If
  your org does not have the permission, deploying `true` is not a fix — build reconciliation instead
  (gotcha 5).

---

## 2. The rule that fires it

```xml
<rules>
    <fullName>Account_Tier_Changed</fullName>
    <actions>
        <name>Notify_ERP_Of_Tier_Change</name>
        <type>OutboundMessage</type>
    </actions>
    <active>true</active>
    <criteriaItems>
        <field>Account.Customer_Tier__c</field>
        <operation>notEqual</operation>
        <value>Prospect</value>
    </criteriaItems>
    <description>Notifies the ERP account master whenever an account leaves Prospect tier.</description>
    <triggerType>onCreateOrTriggeringUpdate</triggerType>
</rules>
```

**How to read it**

- `<actions>` is a `WorkflowActionReference`: `name` is `Required` and is "the name of the workflow
  action"; `type` is `Required` and takes `Alert`, `FieldUpdate`, `FlowAction`, `OutboundMessage`, or
  `Task` (L139952–139966). `name` must equal the outbound message's `fullName` — **not** its `name`
  label. `Notify ERP Of Tier Change` here would fail the deploy.
- `criteriaItems` field references are object-qualified — the guide's sample uses
  `CustomObjectForWorkflow__c.Name` and `CustomObjectForWorkflow__c.CreatedById` (L140641, L140681).
  A bare `Customer_Tier__c` does not resolve.
- `operation` is a `FilterOperation`: `equals`, `notEqual`, `lessThan`, `greaterThan`, `lessOrEqual`,
  `greaterOrEqual`, `contains`, `notContain`, `startsWith`, `includes`, `excludes`, `within`
  (L43900–43913).
- "Either `criteriaItems` or `formula` must be set" (L140390–140393). For a change-detection rule, a
  `<formula>ISCHANGED(Customer_Tier__c)</formula>` with `<triggerType>onAllChanges</triggerType>` is the
  guide's own pattern (L140696–140701) — but note that `ISCHANGED` and `onCreateOnly` cannot both be
  satisfied, so pick the trigger type to match the criterion.
- `triggerType` takes `onAllChanges`, `onCreateOnly`, or `onCreateOrTriggeringUpdate` (L140420–140430).
  `onCreateOnly` means a later correction to the tier never reaches the ERP.
- `active` is `Required` (L140382). A rule deployed with `false` is silent, not broken.
- `booleanFilter` holds the advanced filter formula when you have more than one criterion — the guide's
  example is `1 AND 2 OR 3` (L140385–140387, sample L140639).

---

## 3. The complete file

`force-app/main/default/workflows/Account.workflow-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Workflow xmlns="http://soap.sforce.com/2006/04/metadata">
    <fieldUpdates>
        <fullName>Stamp_ERP_Sync_Timestamp</fullName>
        <description>Existing field update — retrieved, not authored. Deleting this element from the file deletes it from the org.</description>
        <field>ERP_Last_Notified__c</field>
        <formula>NOW()</formula>
        <name>Stamp ERP Sync Timestamp</name>
        <notifyAssignee>false</notifyAssignee>
        <operation>Formula</operation>
        <protected>false</protected>
    </fieldUpdates>
    <outboundMessages>
        <fullName>Notify_ERP_Of_Tier_Change</fullName>
        <apiVersion>62.0</apiVersion>
        <description>Pushes the account tier change to the ERP account-master listener.</description>
        <endpointUrl>https://erp.example.com/sfdc/listener/account-master</endpointUrl>
        <fields>Id</fields>
        <fields>AccountNumber</fields>
        <fields>Name</fields>
        <fields>BillingCountry</fields>
        <fields>Customer_Tier__c</fields>
        <fields>LastModifiedDate</fields>
        <includeSessionId>false</includeSessionId>
        <integrationUser>erp.integration@example.com</integrationUser>
        <name>Notify ERP Of Tier Change</name>
        <protected>false</protected>
        <useDeadLetterQueue>true</useDeadLetterQueue>
    </outboundMessages>
    <outboundMessages>
        <fullName>Notify_ERP_Of_Tier_Rejection</fullName>
        <apiVersion>62.0</apiVersion>
        <description>Fired only by the Tier Upgrade approval process on final rejection. No workflow rule references this message.</description>
        <endpointUrl>https://erp.example.com/sfdc/listener/tier-rejection</endpointUrl>
        <fields>Id</fields>
        <fields>AccountNumber</fields>
        <fields>Customer_Tier__c</fields>
        <includeSessionId>false</includeSessionId>
        <integrationUser>erp.integration@example.com</integrationUser>
        <name>Notify ERP Of Tier Rejection</name>
        <protected>false</protected>
        <useDeadLetterQueue>true</useDeadLetterQueue>
    </outboundMessages>
    <rules>
        <fullName>Account_Tier_Changed</fullName>
        <actions>
            <name>Notify_ERP_Of_Tier_Change</name>
            <type>OutboundMessage</type>
        </actions>
        <actions>
            <name>Stamp_ERP_Sync_Timestamp</name>
            <type>FieldUpdate</type>
        </actions>
        <active>true</active>
        <criteriaItems>
            <field>Account.Customer_Tier__c</field>
            <operation>notEqual</operation>
            <value>Prospect</value>
        </criteriaItems>
        <description>Notifies the ERP account master whenever an account leaves Prospect tier.</description>
        <triggerType>onCreateOrTriggeringUpdate</triggerType>
    </rules>
</Workflow>
```

**How to read it**

- Two `outboundMessages`, one `rules`. The second outbound message has no rule pointing at it and that is
  legal — it is referenced from the approval process in § 4. An outbound message is a declaration; the
  reference is separate.
- The `fieldUpdates` element is there to make the retrieve-first rule concrete. It was not authored for
  this change; it was retrieved. Omitting it from a deploy of this file removes it from the org.
- Element order inside `Workflow` follows the guide's sample (L140556–140737): `alerts`, `fieldUpdates`,
  `outboundMessages`, `rules`, `tasks`. Within each element, `fullName` first, then the rest
  alphabetically — this is the order a retrieve produces, and matching it keeps diffs readable.
- **Do not copy the guide's sample verbatim.** At L140666–140669 it contains
  `<fullName>Field_Update</name>` — an open tag closed with the wrong name. That block is not
  well-formed XML and will not parse. See gotcha 8.

---

## 4. The approval-process variant

Outbound messages are "workflow **and approval** actions" (L140313–140315). The `ApprovalProcess` file
references the message by the same `fullName`, using the same `name`/`type` pair as a workflow rule
(guide sample L23615–23641):

`force-app/main/default/approvalProcesses/Account.Tier_Upgrade.approvalProcess-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApprovalProcess xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <allowRecall>true</allowRecall>
    <enableMobileDeviceAccess>false</enableMobileDeviceAccess>
    <entryCriteria>
        <criteriaItems>
            <field>Account.Customer_Tier__c</field>
            <operation>equals</operation>
            <value>Strategic</value>
        </criteriaItems>
    </entryCriteria>
    <finalRejectionActions>
        <action>
            <name>Notify_ERP_Of_Tier_Rejection</name>
            <type>OutboundMessage</type>
        </action>
    </finalRejectionActions>
    <finalRejectionRecordLock>false</finalRejectionRecordLock>
    <label>Tier Upgrade</label>
    <recallActions>
        <action>
            <name>Notify_ERP_Of_Tier_Rejection</name>
            <type>OutboundMessage</type>
        </action>
    </recallActions>
    <recordEditability>AdminOnly</recordEditability>
    <showApprovalHistory>true</showApprovalHistory>
</ApprovalProcess>
```

**How to read it**

- `ApprovalProcess` components "have the suffix `.approvalProcess` and are stored in the
  `approvalProcesses` folder", available in API 28.0 and later (L23067–23071).
- `Notify_ERP_Of_Tier_Rejection` is **not** defined here. It is defined in `Account.workflow` (§ 3). A
  deploy of this `.approvalProcess` without the `Workflow` member in the same `package.xml` cannot
  resolve the action name.
- The guide notes that "the metadata doesn't include the order of active approval processes. Sometimes
  you have to reorder the approval processes in the destination org after deployment" (L23062–23063).
- For Knowledge article version (`_kav`) approval processes, the supported action types are Knowledge
  Action, Email Alert, Field Update, and Outbound Message (L23059–23061) — outbound messages are in
  scope there, most other action types are not.

---

## 5. package.xml

Deploying the approval process and the workflow together is the point — the approval action cannot
resolve without the workflow file.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account</members>
        <name>Workflow</name>
    </types>
    <types>
        <members>Account.Tier_Upgrade</members>
        <name>ApprovalProcess</name>
    </types>
    <version>62.0</version>
</Package>
```

`Workflow` "supports the wildcard character `*` (asterisk) in the package.xml manifest file"
(L140742–140744), and the guide gives the retrieve-everything form explicitly (L139884–139887):

```xml
<types>
    <members>*</members>
    <name>Workflow</name>
</types>
```

Use the wildcard to retrieve, name the objects explicitly to deploy. A wildcard deploy of workflow
metadata sends every object's whole workflow surface.

---

## 6. Retrieve and deploy

Retrieve before authoring — the file is the object's entire workflow surface:

```bash
# 1. Pull the current state of the object's workflow file
sf project retrieve start --metadata Workflow:Account --target-org my-sandbox

# 2. Diff before you edit, so you know what was already there
git diff -- force-app/main/default/workflows/Account.workflow-meta.xml

# 3. After editing, run the checker (see scripts/check_outbound_message_setup.py)
python3 skills/admin/outbound-message-setup/scripts/check_outbound_message_setup.py \
  --manifest-dir force-app/main/default

# 4. Validate-only deploy first — a bad action name fails here, not in production
sf project deploy start --manifest manifest/package.xml --target-org my-sandbox --dry-run

# 5. Deploy
sf project deploy start --manifest manifest/package.xml --target-org my-sandbox
```

To move the same configuration to production, repeat steps 4–5 against the production alias. The
`endpointUrl` almost always differs between sandbox and production — treat it as an environment
variable substituted at deploy time, not a value copied between orgs.

---

## 7. Verify after deploy

**A. Round-trip the metadata.** This is the only deterministic check, and it is how you discover what
the org actually assigned to `apiVersion`:

```bash
sf project retrieve start --metadata Workflow:Account --target-org my-sandbox
git diff -- force-app/main/default/workflows/Account.workflow-meta.xml
```

An empty diff means the org holds exactly what you committed. A diff on `<apiVersion>` means the org
overrode your value — reconcile it before the listener team regenerates a WSDL against the wrong version
(L140334–140337).

**B. Confirm in Setup.** The Metadata API guide gives the navigation: "To monitor the status of outbound
messages, from Setup, in the Quick Find box, enter `Outbound Messages`, and then select **Outbound
Messages**" (L140338–140340). The SOAP API guide's
[Viewing / Tracking Outbound Message Status](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_setting_up.htm)
says what is on the page:

| Where | What you can confirm |
|---|---|
| Outbound Messages list | "Select an existing outbound message to view details about it or view workflow rules **and approval processes** that use it" — this is the reverse index for gotcha 7, and the fastest way to prove an approval-only message is still wired |
| Click for WSDL | "The WSDL is bound to the outbound message and contains the instructions about how to reach the endpoint service and what data is sent to it" — regenerate and hand to the listener team after any field-list or `apiVersion` change |
| View Message Delivery Status | "The status of your outbound messages, including the total number of attempted deliveries", and the triggering workflow or approval action by its action ID |
| Retry / Del | Retry "change[s] the Next Attempt date to now"; Del "permanently remove[s] the outbound message from the queue" — Del is not a pause |

If these options are absent, "your org doesn't have outbound messaging enabled. Contact Salesforce to
enable outbound messaging for your org."

**C. There is no SOQL check.** UNVERIFIED (2026-09-05): a grep for `OutboundMessage` and
`Outbound Message` across the Object Reference returns only unrelated Messaging/Voice hits — no
queryable sObject exposes outbound message definitions or the pending queue. If your org needs
programmatic monitoring, the reachable surfaces are the Metadata API round-trip in (A) and the listener's
own receipt log; do not write a runbook step around a `SELECT` that has not been confirmed against your
org's Tooling API.
