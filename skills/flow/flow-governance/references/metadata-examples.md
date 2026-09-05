# Metadata Examples — Flow Governance

Governance is not a wiki page. It is deployable metadata: the org-level switchboard that
decides what a flow may do (`Flow.settings`), the permission set that decides who may run
a restricted flow, the `FlowDefinition` that decides which version is live, the SOQL that
turns the portfolio into an inventory you can assert on, and a policy file the checker can
lint the manifest against.

Every element name, enum value and version floor below comes from the Metadata API
Developer Guide (`api_meta.txt`) or the Object Reference (`object_reference.txt`), cited by
`grep -n` line. Save-order positions come from the Apex Developer Guide
(`apexdev.txt` L15402–15478).

Shapes this file deliberately does not re-invent:

- `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` — the flow body itself. Nothing
  here contains a full flow; `flow/record-triggered-flow-patterns`
  `references/metadata-examples.md` already owns three of them.
- `templates/flow/FaultPath_Template.md` — what a fault path must do. The policy file
  below only *requires* fault paths; `flow/fault-handling` and its
  `scripts/check_flow_faults.py` decide whether a given one is correct.
- `flow/flow-element-naming-conventions` — the element-level convention table and its
  checker. The policy below governs the *flow's* API name, not its elements.

---

## 1. `Flow.settings` — the org-level governance switchboard

`FlowSettings` values live in `settings/Flow.settings`; there is exactly one settings file
per settings component (`api_meta.txt` L116824–116826). Available in API version 47.0 and
later (L116829). This is the highest-leverage governance artifact in the org, because six
of these booleans change what every flow in the portfolio is allowed to do.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <canDebugFlowAsAnotherUser>true</canDebugFlowAsAnotherUser>
    <doesEnforceApexCpuTimeLimit>true</doesEnforceApexCpuTimeLimit>
    <doesFormulaEnforceDataAccess>true</doesFormulaEnforceDataAccess>
    <enableFlowDeployAsActiveEnabled>true</enableFlowDeployAsActiveEnabled>
    <enableFlowFieldFilterEnabled>false</enableFlowFieldFilterEnabled>
    <enableFlowInterviewSharingEnabled>false</enableFlowInterviewSharingEnabled>
    <enableFlowPauseEnabled>true</enableFlowPauseEnabled>
    <enableFlowUseApexExceptionEmail>true</enableFlowUseApexExceptionEmail>
    <enableFlowViaRestUsesUserCtxt>true</enableFlowViaRestUsesUserCtxt>
    <enableLightningRuntimeEnabled>true</enableLightningRuntimeEnabled>
    <isFlowBlockAccessToSessionIDEnabled>true</isFlowBlockAccessToSessionIDEnabled>
    <isManageFlowRequiredForAutomationCharts>false</isManageFlowRequiredForAutomationCharts>
    <isTimeResumedInSameRunContext>true</isTimeResumedInSameRunContext>
</FlowSettings>
```

**How to read it — what each field governs, and what it costs you when it is wrong:**

| Field | Guide line | Documented behaviour | Governance meaning |
|---|---|---|---|
| `canDebugFlowAsAnotherUser` | L116834 | "Indicates whether a flow can be debugged as another user." API 50.0+. | `true` is how an admin reproduces a permission-shaped bug without borrowing a login. Leaving it `false` pushes support toward credential sharing. |
| `doesEnforceApexCpuTimeLimit` | L116849 | "Indicates whether Salesforce accurately measures the CPU time that flows and processes consume." API 51.0+. | `false` means your flows' CPU consumption is *under-*measured, so a portfolio that looks within limits in a sandbox can blow the limit once the release update lands. Governance wants this `true` in every org at once, not per-org. |
| `doesFormulaEnforceDataAccess` | L116855 | "Indicates whether formula resources and formula fields in a flow enforce record-level security." API 48.0+. | The difference between "a flow formula can read a field the running user can't see" and not. Set it once, org-wide; never leave it as an unreviewed default. |
| `enableFlowDeployAsActiveEnabled` | L116877 | "When the value is `false`, all processes and flows are deployed as inactive. When the value is `true`, deploying an active process or flow in a production org causes your Apex tests to run. If Apex tests don't launch your org's required percentage of active processes and autolaunched flows, the deployment is rolled back. The default value is `false` for production orgs and is `true` for non-production orgs." | The single field that decides whether "deploy" and "activate" are one event or two. See §4 and `gotchas.md`. |
| `enableFlowFieldFilterEnabled` | L116889 | By default (`false`) a Create/Update Records element that writes a field the running user can't edit **fails and executes the fault path**. When `true`, "the element sets only the fields that the running user can edit. No notification is sent when some fields aren't updated." | `true` converts a loud, fault-path-visible failure into a silent partial write. Govern it to `false` unless you have a written reason, because `flow/fault-handling` cannot catch what never raises. |
| `enableFlowInterviewSharingEnabled` | L116918 | By default (`true`) users can resume paused interviews shared with them, "either directly or via the role hierarchy." When `false`, "each paused interview can be resumed only by the interview owner or a flow admin who has view access to the interview." | This is a record-access decision wearing a Flow label. A paused interview can hold data the resumer never had access to; `FlowInterview` has both `FlowInterviewOwnerSharingRule` and `FlowInterviewShare` (`object_reference.txt` L140044–140049). |
| `enableFlowPauseEnabled` | L116935 | "Indicates whether screens can display the Pause button… By default, the value is `false`." | Turning it on creates a new operational object class: paused interviews that age, block version deletion (§4) and need an owner. Turn it on *with* the retirement query in §5, not before. |
| `enableFlowUseApexExceptionEmail` | L116961 | Error emails go either to "the user who last modified the process or flow (`false`)" or "the addresses set on the Apex Exception Email page in Setup (`true`)." | `false` is why flow failures reach a departed admin's inbox. This is the concrete fix for the "LastModifiedBy is not Owner" gotcha — route to a monitored address. |
| `enableFlowViaRestUsesUserCtxt` | L116968 | "Indicates whether a flow that runs via REST API uses the running user's profile and permission sets to determine the object permissions and field-level access of the flow." API 54.0+. | Integration-launched flows are the portfolio's blind spot. `false` means an API caller gets more access through a flow than through the API directly. |
| `enableLightningRuntimeEnabled` | L116982 | Flows launched from a URL or Setup use Lightning runtime (`true`) or Classic runtime (`false`). Default `true`. | Pin it explicitly so a screen flow does not render differently in one org of the release train. |
| `isFlowBlockAccessToSessionIDEnabled` | L117035 | When `true`, "flows that access the session ID variable receive a placeholder string instead of a valid session ID." Default `false`. | The default lets any flow author mint a usable session ID. Governance sets this `true` and treats an exception as a security review, not a config ticket. |
| `isManageFlowRequiredForAutomationCharts` | L117040 | When `true`, only users with Manage Flow see all Automation Home (Beta) charts; View Setup and Configuration users see only the Total Started Automations by Process Type chart. Default `false`. | Decides whether the portfolio dashboard is readable by the people you want reading it. Governance usually wants `false`. |
| `isTimeResumedInSameRunContext` | L117048 | "Indicates whether paused autolaunched flows always resume in the same context and retain the user access that they had before being paused." API 57.0+. | With `false`, a scheduled path can resume under different access than it paused with — the same flow, two answers. |

Two fields in the guide's own sample are deliberately **absent** above:
`isAccessToInvokedApexRequired` and `isFlowApexContextRetired` are "available in API
versions 47.0 to 58.0. The field is deprecated in API version 59.0 and later"
(L116988–117001, L117016–117024). Deploying them against a modern `package.xml` version is
governance debt, not governance. See `gotchas.md`.

The wildcard `*` "doesn't apply to metadata types for feature settings. The wildcard
applies only when retrieving all settings, not for an individual setting"
(L117094–117096) — so `Flow.settings` must be named explicitly in `package.xml`.

---

## 2. `PermissionSet` — who may run a restricted flow

Set `<isAdditionalPermissionRequiredToRun>true</isAdditionalPermissionRequiredToRun>` on
the flow (`api_meta.txt` L68162: "Override the default behavior and restrict access to
enabled profiles or permission sets… The default value is `false`") and access stops being
ambient. The Object Reference states the consequence on the interview itself: "If
**Override default behavior and restrict access to enabled profiles or permission sets** is
selected for an individual flow, access to that specific flow and its interviews is given
to users by profile or permission set" (`object_reference.txt` L139899–139903).

`PermissionSetFlowAccess` is the element that grants it — `enabled` and `flow`, both
Required, available in API version 47.0 and later (`api_meta.txt` L95053–95060).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Flow Runner - Revenue Operations</label>
    <description>Grants run access to the restricted Revenue Operations flows and the Apex actions they invoke. Owner: revenue-ops. Reviewed each release train.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <flowAccesses>
        <enabled>true</enabled>
        <flow>Opportunity_Screen_RenewalRiskReview</flow>
    </flowAccesses>
    <flowAccesses>
        <enabled>true</enabled>
        <flow>Opportunity_Autolaunched_RecalculateRenewalRisk</flow>
    </flowAccesses>
    <classAccesses>
        <apexClass>RenewalRiskInvocable</apexClass>
        <enabled>true</enabled>
    </classAccesses>
    <objectPermissions>
        <allowCreate>false</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Opportunity</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
</PermissionSet>
```

**How to read it:**

- Element order and shape follow the guide's own `PermissionSet` sample definition
  (`api_meta.txt` L95192–95233). Only documented elements appear: `label` (Required, limit
  80 characters, L94924), `description` (limit 255 characters, L94786),
  `hasActivationRequired` (L94820), `flowAccesses` (L94807, API 47.0+), `classAccesses`
  (L94772, API 23.0+), `objectPermissions` (L95064+).
- `classAccesses` is not decoration. `PermissionSetApexClassAccess` controls "which
  top-level Apex classes have methods that users assigned to this permission set can
  execute" (L94772–94774). A flow that calls an invocable Apex action and a permission set
  that grants the flow but not the class is the most common half-granted state in a Flow
  portfolio.
- There is deliberately **no `<userPermissions>` block**. The Manage Flow and Run Flows
  user permissions are real — the Object Reference names both in `FlowInterview`'s Special
  Access Rules: "To delete a flow interview, you must have the 'Manage Flow' user
  permission. All other calls require the 'Run Flows' user permission or the Flow User
  field enabled on the user detail page" (L139895–139899) — but their `<name>` values as
  they appear inside `userPermissions` are not enumerated in the Metadata API guide.
  **UNVERIFIED (2026-09-05): the exact `userPermissions/name` API strings for Manage Flow
  and Run Flows are not listed in `api_meta.txt`; retrieve an existing permission set and
  copy the literal rather than guessing.** Retrieval is the safe route anyway:
  `sf project retrieve start --metadata "PermissionSet:Flow_Runner_Revenue_Operations"`.

---

## 3. `FlowDefinition` — activation control, and why it is a trap

`FlowDefinition` "represents the flow definition's description and active flow version
number", is stored in the `flowDefinitions` directory with extension `.flowDefinition`,
and is available in API version 34.0 and later (`api_meta.txt` L73919–73936). It has
exactly four fields: `activeVersionNumber` (int, "the version number of the active flow"),
`apiVersion` ("Reserved for internal use"), `description`, and `masterLabel`
(L73938–73946).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <activeVersionNumber>12</activeVersionNumber>
    <description>Recalculates renewal risk. Owner: revenue-ops. Escalate: #rev-ops-oncall. v13 is drafted but not approved for activation.</description>
    <masterLabel>Opportunity Autolaunched RecalculateRenewalRisk</masterLabel>
</FlowDefinition>
```

**How to read it — and when not to ship it at all:**

- Setting `<activeVersionNumber>0</activeVersionNumber>` is the deactivation form of this
  file. That is the whole reason it survives in governance pipelines: it is the only
  metadata that says "this flow is off" as a versioned artifact.
- The guide's standing recommendation runs the other way: "In API version 44.0, we
  recommend upgrading your flows to flow metadata file names without version numbers and
  **discontinue using the FlowDefinition object to activate or deactivate a flow**. Then
  use the Flow object to activate or deactivate a flow" (L73925–73928).
- The precedence rule is the trap. "If you deploy with flow definitions, the active version
  numbers in the flow definitions **override the status fields in the flows**. For example,
  the active version number in the flow definition is version 3, and the latest version of
  the flow is version 4 with the status field as `Active`. After you deploy your flow, the
  active version is version 3" (L73929–73932, repeated at L73203–73206).
- So govern it as an either/or, and say which in the policy file (§6):
  `activation_control: flow_status` (delete `flowDefinitions/`, drive `<status>` on the
  Flow) or `activation_control: flow_definition` (a `.flowDefinition` per governed flow,
  and `<status>` on the Flow is documentation only). A repo with both is a repo where the
  reviewer's diff no longer tells you what will be live.
- The upgrade checklist for the `flow_status` route is explicit: "The flows directory
  doesn't include any unused flow versions… For each active flow, the `status` field is
  `Active`. Any flow without a `status` value is deployed or retrieved with a `status`
  value of `Draft`… The flowDefinitions directory is empty" (L73186–73190).

---

## 4. Deploying an active flow at all

Three sentences from the guide's Flow limitations set the whole activation gate
(`api_meta.txt` L68035–68042):

| Guide statement | Line | Governance consequence |
|---|---|---|
| "You can deploy changes to an active flow if in a non-production org… To deploy changes in a production org, you must enable the **Deploy processes and flows as active** preference." | L68038–68040 | Sandbox success proves nothing about production activation. The gate is `enableFlowDeployAsActiveEnabled` in §1. |
| "You can delete a flow version if it isn't active and doesn't have any paused interviews. If the flow version has paused interviews, wait for those interviews to resume and finish, or delete them." | L68041–68042 | Retirement (Pattern 3) has a hard precondition that only SOQL can tell you about. See §5. |
| "You can't use Metadata API to access a flow installed from a managed package unless the flow is a template." | L68035 | Managed-package flows are outside the manifest, so they are outside the checker. Inventory them from `FlowDefinitionView` instead (`InstalledPackageName`, `NamespacePrefix`, `ManageableState`). |

And when `enableFlowDeployAsActiveEnabled` is `true`, activation is a test event:
"deploying an active process or flow in a production org causes your Apex tests to run. If
Apex tests don't launch your org's required percentage of active processes and autolaunched
flows, the deployment is rolled back" (L116877–116886). The guide does not state the
percentage numerically. **UNVERIFIED (2026-09-05): the required percentage of active
processes and autolaunched flows is not given a number anywhere in `api_meta.txt` or
`apexdev.txt`; the 75% figure at `api_meta.txt` L2550 is Apex *code* coverage, which is a
different rule.** Write the requirement into the policy file as a boolean gate, not a
number you cannot cite.

---

## 5. The flow inventory — SOQL that answers the governance questions

`FlowDefinitionView` "represents the description of a flow definition", supports
`describeSObjects()` and `query()`, and is available in API version 46.0 and later
(`object_reference.txt` L139267–139273). This is the machine-readable Flow list view.

**(a) Active versions per object and save context — the duplication question.**

```sql
SELECT ApiName, Label, IsActive, IsOutOfDate, ActiveVersionId, VersionNumber,
       ProcessType, TriggerType, RecordTriggerType,
       TriggerObjectOrEventLabel, TriggerOrder, ApiVersion,
       InstalledPackageName, NamespacePrefix, ManageableState, LastModifiedBy
FROM FlowDefinitionView
WHERE IsActive = true
  AND TriggerType IN ('RecordBeforeSave', 'RecordAfterSave', 'RecordBeforeDelete')
ORDER BY TriggerObjectOrEventLabel, TriggerType, TriggerOrder NULLS LAST
```

Field grounding: `IsActive` "whether the latest version of the flow definition is the
active flow version" (L139383–139389, API 47.0+); `IsOutOfDate` "whether the active flow
version is the latest version of the flow definition" (L139391–139397, API 47.0+);
`TriggerOrder` "from 1 to 2,000… Available in API version 54.0 and later"
(L139763–139769); `TriggerType` enum including `RecordBeforeSave`, `RecordAfterSave`,
`RecordBeforeDelete`, `Scheduled`, `PlatformEvent` (L139772–139845); `ApiVersion`
"available in API version 59.0 and later" (L139292–139298); `InstalledPackageName`
(L139372–139378); `ManageableState` (L139437–139452); `LastModifiedBy` "name of the user
who last updated this flow definition" (L139482–139488).

Read it for three failure shapes:

1. **Two or more rows sharing `TriggerObjectOrEventLabel` + `TriggerType` where any
   `TriggerOrder` is null.** Unordered co-resident automation.
2. **Rows sharing object + `TriggerType` + the same non-null `TriggerOrder`.** A declared
   tie, which is not an order.
3. **`IsOutOfDate = true`.** The live version is not the latest saved version — someone
   built and never activated, or someone rolled back and never told the repo.

**(b) Version-level drift — API version and run mode.** `FlowVersionView` "represents the
version of a flow definition", API 46.0 and later (L144970–144978). Note the usage rule:
"A query must be filtered by `DurableId` or `FlowDefinitionViewId` to get results"
(L145295–145296) — you cannot sweep this object, you must drive it from (a).

```sql
SELECT DurableId, Label, VersionNumber, Status, ApiVersion, ApiVersionRuntime,
       ProcessType, RunInMode, Description, FlowDefinitionViewId
FROM FlowVersionView
WHERE FlowDefinitionViewId = '300xx0000000001'
ORDER BY VersionNumber DESC
```

`Status` enum: `Active`, `Draft`, `Obsolete`, `InvalidDraft`, `UnderReview`
(L145265–145273). `RunInMode`: `DefaultMode`, `SystemModeWithSharing` (L145251–145262).
`ApiVersion` is "the API version for the flow definition. Every flow version has an API
version specified at creation"; `ApiVersionRuntime` is "the API version for running the
flow. This value determines which versioned run-time behavior improvements are adopted by
the flow version. If not specified when the flow or flow version is created, the latest
available API version is used" (L144985–145008). Those are two different numbers and
governance cares about the second one.

**(c) Paused interviews — the retirement blocker.** `FlowInterview` "represents a flow
interview. A flow interview is a running instance of a flow", API 32.0 and later
(L139866–139869).

```sql
SELECT Id, Name, InterviewLabel, InterviewStatus, CurrentElement, PauseLabel,
       OwnerId, Owner.Name, FlowVersionViewId, WasPausedFromScreen, CreatedDate
FROM FlowInterview
WHERE InterviewStatus IN ('Paused', 'VersionPaused', 'Error')
ORDER BY CreatedDate
```

`InterviewStatus` enum: `Completed`, `Error`, `Paused`, `Running`, `VersionPaused`
("this flow version is paused. No more records are processed until the flow is resumed",
API 60.0+) — L139952–139972. `Error` carries the message ("the error message that explains
why the flow interview failed", API 62.0+, L139899–139906). `OwnerId`: "only this user or
an admin can resume the interview" (L140003–140006). Any row here whose
`FlowVersionViewId` points at a version you planned to delete is a blocked retirement per
§4.

**(d) What a paused interview is holding.** `FlowRecordRelation` "represents a relationship
between a record and a flow interview. When a flow interview is paused, Salesforce uses the
`$Flow.CurrentRecord` global variable in the flow to associate the interview with a record",
API 42.0 and later (`object_reference.txt` L143526–143529).

```sql
SELECT Id, ParentId, Parent.InterviewLabel, Parent.InterviewStatus, RelatedRecordId
FROM FlowRecordRelation
WHERE Parent.InterviewStatus IN ('Paused', 'VersionPaused')
```

This is the answer to "if I delete these interviews to unblock the retirement, whose record
loses its in-flight process?" — `ParentId` refers to `FlowInterview`, `RelatedRecordId` to
the business record (L143541–143570).

**(e) Flows below the policy's API floor.**

```sql
SELECT ApiName, Label, ApiVersion, TriggerObjectOrEventLabel, LastModifiedBy
FROM FlowDefinitionView
WHERE IsActive = true AND ApiVersion < 59
ORDER BY ApiVersion
```

The floor matters because `Flow.apiVersion` "defines the execution behavior of the flow"
(`api_meta.txt` L68075–68080) and `FlowVersionView.ApiVersionRuntime` "determines which
versioned run-time behavior improvements are adopted." Two flows on the same object at
different API versions can adopt different run-time behaviour in the same save.

---

## 6. `flow-governance-policy.yaml` — the standard, as a file the checker reads

Put this at the root of the source tree (or anywhere under `--manifest-dir`;
`scripts/check_flow_governance.py` discovers it by its `flow_governance_policy:` key). It
is not deployed to the org — it is the machine-readable form of the standard that §1–§5
are the enforcement surface for.

```yaml
flow_governance_policy:
  version: "1.0"
  owner: "platform-automation"
  reviewed: "2026-09-05"

  # Section 3: pick ONE. flow_status = drive <status> on the Flow, flowDefinitions/ empty.
  # flow_definition = a .flowDefinition per governed flow; <status> is documentation only.
  activation_control: flow_status

  naming:
    # <Object>_<TriggerType>_<PurposeVerbPhrase>
    pattern: "^[A-Z][A-Za-z0-9]*_(BeforeSave|AfterSave|BeforeDelete|Scheduled|Autolaunched|Screen|Orchestration|PlatformEvent)_[A-Z][A-Za-z0-9]*$"
    forbidden_substrings:
      - "New Flow"
      - "Copy"
      - "Test"
      - "Temp"
      - "Backup"
      - "Untitled"
      - "Final"

  versions:
    min_api_version: 59
    allowed_run_in_mode:
      - DefaultMode
      - SystemModeWithSharing
    allowed_status:
      - Draft
      - Active

  record_triggered:
    # More than one Active flow on the same object + triggerType must declare triggerOrder.
    require_trigger_order_when_co_resident: true
    # triggerOrder is an int 1..2000 (api_meta.txt L68438).
    trigger_order_min: 1
    trigger_order_max: 2000
    require_entry_criteria_for_after_save: true

  documentation:
    require_description: true
    min_description_chars: 60
    require_interview_label: true
    require_owner_in_description: true
    owner_marker: "Owner:"

  testing:
    require_flow_test_for_active: true
    # FlowTest supports record-triggered, autolaunched and Data Cloud-triggered flows
    # (api_meta.txt L73953-73955).
    testable_process_types:
      - AutoLaunchedFlow

  fault_paths:
    require_fault_connectors: true
    # This policy states the requirement; it does not judge the fault path.
    delegate_to: "flow/fault-handling scripts/check_flow_faults.py"

  review_gates:
    - "Named owner present in the flow description"
    - "Change reference recorded in the release ticket (admin/change-management-and-deployment)"
    - "FlowTest present and passing for every flow deployed Active"
    - "Rollback version identified, or activation_control documented as flow_definition"
    - "Retirement review run within the last 90 days (see references/metadata-examples.md section 5c)"
```

Run the checker over a retrieved source tree:

```bash
python3 skills/flow/flow-governance/scripts/check_flow_governance.py \
    --manifest-dir force-app/main/default
```

It lints the policy file itself first — an `activation_control` that is neither value, a
`naming.pattern` that is not a valid regex, a `runInMode` or `status` that is not a
documented enum, a `triggerOrder` bound outside 1–2,000, an empty `review_gates` — and
then lints every `*.flow-meta.xml`, `*.flowDefinition` and `settings/Flow.settings` in the
tree against it. Exit code 1 means at least one `ERROR`.

Two keys are deliberately advisory rather than blocking. `require_entry_criteria_for_after_save`
WARNs on an Active `RecordAfterSave` flow with no `<filters>` or `<filterFormula>` on
`<start>`, because some after-save flows legitimately run on every save.
`fault_paths.require_fault_connectors` produces a NOTE and nothing else: this checker
states the requirement and hands the judgement to `flow/fault-handling`
`scripts/check_flow_faults.py`, which reads the same `--manifest-dir`. `review_gates`
is never evaluated — it is the human half of the standard, and the checker's only
opinion is that leaving it empty is a claim of automation the tool does not provide.

---

## 7. `package.xml`

The wildcard does not work for an individual setting (`api_meta.txt` L117094–117096), so
`Flow` is named as a `Settings` member explicitly. `FlowDefinition` supports the wildcard
(L73948–73950) but is listed by name here because §3 governs which flows have one.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Flow</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Opportunity_Autolaunched_RecalculateRenewalRisk</members>
        <members>Opportunity_Screen_RenewalRiskReview</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Opportunity_Autolaunched_RecalculateRenewalRisk_HappyPath</members>
        <name>FlowTest</name>
    </types>
    <types>
        <members>Flow_Runner_Revenue_Operations</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

`FlowTest` components "have the suffix `.flowtest`, and Salesforce stores them in the
`flowtests` folder", available in API version 55.0 and later (`api_meta.txt`
L73957–73963). Add a `FlowDefinition` types block **only** if
`activation_control: flow_definition`.

---

## 8. Deploy order

| # | Step | Command | Why here |
|---|---|---|---|
| 1 | Baseline the inventory | run §5(a) and §5(c) against the target org | You cannot assert a retirement or a tie fix without the before state. |
| 2 | Settings first | `sf project deploy start --metadata "Settings:Flow" --target-org my-sandbox` | `enableFlowDeployAsActiveEnabled` decides whether step 4 activates or lands as Draft. Deploying it after the flows changes the meaning of the flow deploy. |
| 3 | Validate the flows | `sf project deploy start --manifest manifest/package.xml --dry-run --target-org my-sandbox` | The only place a bad `<object>`, a dangling `<targetReference>`, or a flow file name containing spaces surfaces before a user hits it — "spaces in a flow file name can lead to errors when you deploy the flow" (`api_meta.txt` L68036). |
| 4 | Flows + FlowTests | `sf project deploy start --manifest manifest/package.xml --target-org my-sandbox` | Deploy the tests with the flows, not after; in production with `enableFlowDeployAsActiveEnabled = true` the activation runs tests as part of this step (§4). |
| 5 | Permission set | `sf project deploy start --metadata "PermissionSet:Flow_Runner_Revenue_Operations" --target-org my-sandbox` | The flow must exist before `flowAccesses` can name it. |
| 6 | Retire, last | destructive changes for versions confirmed inactive and interview-free by §5(c) | Deleting a version with paused interviews fails (`api_meta.txt` L68041–68042). |
| 7 | Re-run the checker and §5 | `check_flow_governance.py --manifest-dir …` plus §5(a) | Prove the tie is gone rather than assuming the deploy fixed it. |

Retrieve the whole governed set back to see what actually landed, including the version
numbers Salesforce assigned:

```bash
sf project retrieve start --manifest manifest/package.xml --target-org my-sandbox
```

---

## 9. Verification

**Setup.** Setup > Process Automation > Flows. Confirm the version marked *Active* is the
version number you intended for each governed flow, and that the Flow Trigger Explorer
run-order numbers match the `<triggerOrder>` values you deployed. For paused interviews,
Setup > Process Automation > Paused Flow Interviews — the interview label you set is what
shows there and in the Paused Flow Interviews component on the user's Home tab
(`api_meta.txt` L68168–68172).

**SOQL — the one assertion a pipeline should make.** Re-run §5(a) and require that this
returns zero rows:

```sql
SELECT TriggerObjectOrEventLabel, TriggerType, COUNT(Id) flowCount
FROM FlowDefinitionView
WHERE IsActive = true
  AND TriggerType IN ('RecordBeforeSave', 'RecordAfterSave')
  AND TriggerOrder = null
GROUP BY TriggerObjectOrEventLabel, TriggerType
HAVING COUNT(Id) > 1
```

Any row is two or more live flows in the same save context on the same object with no
declared run order. That is the governance failure that produces "it worked yesterday"
bug reports, and it is the only one on this page that is invisible in Setup until you go
looking.

**Settings.** Retrieve `Flow.settings` back and diff it against §1. Feature settings do
not accept the wildcard, so a settings file that silently reverted is a diff nobody
notices unless it is in the manifest by name.

**Retirement.** Before any destructive change, §5(c) must return zero rows for the
`FlowVersionViewId` you are deleting. A non-empty §5(d) for those interviews is your list
of affected business records — decide about them before the deploy window, not during it.
