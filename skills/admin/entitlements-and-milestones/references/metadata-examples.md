# Metadata Examples — Entitlements and Milestones (Deployable)

Every element name, enum value and file location below comes from the Metadata API Developer Guide
(`EntitlementProcess` § api_meta.txt:59069, `EntitlementTemplate` § 59310, `MilestoneType` § 88319,
`EntitlementSettings` § 115601, `Workflow` § 139874, `Settings` § 108356) and the Object Reference
(`SlaProcess` § object_reference.txt:270637, `CaseMilestone` § 63342, `Entitlement` § 110176).
Line citations are `grep -n` line numbers into the v62 PDF text extracts.

This file closes the gap recorded in `admin/case-management-setup`
`references/worked-example-case-intake.md` § 6: *"no deployable `EntitlementProcess` example …
unverified whether the org can deploy the process with its milestones by metadata."*
**It can.** `EntitlementProcess` supports the `*` wildcard in `package.xml` (api_meta.txt:59306) and
carries its milestones and time triggers inline as `milestones` / `timeTriggers` child elements
(api_meta.txt:59132, 59196).

Design decisions — which tier, how many milestones, what the SLA should be — belong to
`agents/entitlement-and-milestone-designer/AGENT.md` and `architect/sla-design-and-escalation-matrix`.
This file is the shape you deploy and the checks you run afterwards.

Validate anything written here with:

```bash
python3 skills/admin/entitlements-and-milestones/scripts/check_entitlements_and_milestones.py \
  --manifest-dir force-app/main/default

# --strict also fails on WARN, for a tree that is meant to be the whole package
python3 skills/admin/entitlements-and-milestones/scripts/check_entitlements_and_milestones.py \
  --manifest-dir force-app/main/default --strict
```

Exit 1 means an ERROR. WARN and INFO print and exit 0 — including `W6`, which
fires when a process names `<businessHours>` and the tree holds no
`settings/BusinessHours.settings-meta.xml` at all. The name could not be
resolved against anything, so the calendar check was not made; run the checker
over the tree that carries the settings file (or the whole build) to turn W6
back into the real `W3` cross-check.

---

## Where the files live

| Component | package.xml type / member | DX path | Wildcard | Source |
|---|---|---|---|---|
| Milestone definition | `MilestoneType`, member `First Response` | `milestoneTypes/First Response.milestoneType-meta.xml` | `*` supported | api_meta.txt:88325, 88377 |
| Entitlement process (one file per **version**) | `EntitlementProcess`, member `premier_support_v1` | `entitlementProcesses/premier_support_v1.entitlementProcess-meta.xml` | `*` supported | api_meta.txt:59075–59084, 59306 |
| Entitlement template | `EntitlementTemplate`, member `Premier_Phone_Support` | `entitlementTemplates/Premier_Phone_Support.entitlementTemplate-meta.xml` | `*` supported | api_meta.txt:59318–59319, 59371 |
| Org switch (enable + versioning) | `Settings`, member `Entitlement` | `settings/Entitlement.settings-meta.xml` | `*` only when retrieving **all** settings | api_meta.txt:108368, 115607, 115726 |
| The alerts and field updates the actions name | `Workflow`, member `Case` | `workflows/Case.workflow-meta.xml` | `*` supported | api_meta.txt:139896–139898, 139884 |
| The calendars the process and milestones name | `Settings`, member `BusinessHours` | `settings/BusinessHours.settings-meta.xml` | see `admin/business-hours-and-holidays` | api_meta.txt:111271 |

Two file-naming rules that catch people out, both stated by the guide at api_meta.txt:59075–59084:

- **The process file name is not the display name.** It is `slaProcess.NameNorm` — the lowercase form
  of `name`, with `_v<n>` appended when entitlement versioning is on. The guide's own example: a
  process named `gold_support` produces `gold_support_v2.entitlementProcess`. A process you name
  "Premier Support" in the UI therefore does **not** retrieve as `Premier Support.entitlementProcess`.
  Create it, retrieve it, then edit the file that came back — do not guess the name.
- **One file per version, not per process.** "Each file contains one entitlement process or, if
  entitlement versioning is enabled, one version of an entitlement process" (api_meta.txt:59077).
  Versions of one process are tied together by an identical `versionMaster` value (api_meta.txt:59139).

<!-- UNVERIFIED (2026-09-04): the MilestoneType section (api_meta.txt:88325-88327) gives the directory
     and extension but does not state that the file's base name equals the milestone's Name field.
     The row above assumes it does, which matches how EntitlementTemplate is documented
     ("The file name matches the unique name of the entitlement template", api_meta.txt:59319).
     Retrieve MilestoneType from the target org before hand-writing these file names. -->

---

## 1. Milestone types — the definitions the process points at

A milestone must exist as a `MilestoneType` component before any process can reference it by
`milestoneName`. This is the step that makes an `EntitlementProcess` deploy rather than fail: the
process file carries the *timing*, the milestone type carries the *identity and recurrence*.

`milestoneTypes/First Response.milestoneType-meta.xml` — fires once per process run:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MilestoneType xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Time from case entry into the entitlement process to the first agent reply.</description>
    <recurrenceType>none</recurrenceType>
</MilestoneType>
```

`milestoneTypes/Resolution.milestoneType-meta.xml` — also once per process run:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MilestoneType xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Time from case entry into the entitlement process to a resolved case.</description>
    <recurrenceType>none</recurrenceType>
</MilestoneType>
```

`milestoneTypes/Case Update.milestoneType-meta.xml` — the "keep the customer informed every N hours"
commitment, chained so instance *n+1* opens only after instance *n* closes. The Premier process below
does not use it; a rolling-update tier in the same package would:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MilestoneType xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Rolling customer update while the case is open. Sequential: the next update window opens only after the previous update is logged.</description>
    <recurrenceType>recursChained</recurrenceType>
</MilestoneType>
```

**The three recurrence values, verbatim from api_meta.txt:88339–88345:**

| Value | Guide wording | Use it for |
|---|---|---|
| `none` | "no recurrence for the milestone. The milestone occurs only one time until the entitlement process exits" | First response, resolution |
| `recursIndependently` | "independent recurrence for the milestone" | A commitment per inbound event, where a missed one does not block the next |
| `recursChained` | "**sequential** recurrence for the milestone" | Rolling updates, where the next window must not open until this one closes |

The Setup UI labels these *No Recurrence*, *Recurs Independently* and *Recurs Chained*. This skill's
prose has historically said "Sequential" for `recursChained` and "Independent" for
`recursIndependently`; the API values above are what you write in XML.

---

## 2. The entitlement process — "Premier Support", version 1

`entitlementProcesses/premier_support_v1.entitlementProcess-meta.xml`.

Read it as: the process clock starts at `entryStartDateField`; the process ends when
`exitCriteriaFilterItems` is satisfied; each `milestones` entry names a `MilestoneType`, sets its
target with `minutesToComplete`, and hangs actions off `successActions` (on completion) and
`timeTriggers` (offsets from the target).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EntitlementProcess xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <description>Premier tier: 4h first response, 48h resolution. v1.</description>
    <SObjectType>Case</SObjectType>

    <!-- Process-level calendar. Every milestone inherits this unless it declares its own. -->
    <businessHours>Premier 24x7</businessHours>

    <!-- The clock starts when the case enters the process. SlaStartDate is one of the five
         documented values (api_meta.txt:59110-59117): SlaStartDate, CreatedDate, ClosedDate,
         LastModifiedDate, StopStartDate. -->
    <entryStartDateField>SlaStartDate</entryStartDateField>

    <!-- Exit criteria: the case leaves the process when Status = Closed. Leaving the process
         stops every milestone still running on it. -->
    <exitCriteriaFilterItems>
        <field>Case.Status</field>
        <operation>equals</operation>
        <value>Closed</value>
    </exitCriteriaFilterItems>

    <!-- Versioning. versionMaster must be identical across every version of this process. -->
    <versionMaster>premier_support</versionMaster>
    <versionNumber>1</versionNumber>
    <isVersionDefault>true</isVersionDefault>
    <versionNotes>Initial Premier tier process. Owner: Support Ops.</versionNotes>
    <name>premier_support</name>

    <!-- ================= Milestone 1: First Response ================= -->
    <milestones>
        <milestoneName>First Response</milestoneName>

        <!-- 240 minutes = 4 hours, counted from process entry because
             useCriteriaStartTime is false. -->
        <minutesToComplete>240</minutesToComplete>
        <useCriteriaStartTime>false</useCriteriaStartTime>

        <!-- WARNING trigger. timeLength is an offset from the TARGET, not a percentage.
             -60 Minutes fires at 180 minutes elapsed, i.e. one hour before breach.
             "Negative values indicate that the target completion date hasn't yet arrived
             and correspond to warning time triggers." (api_meta.txt:59213-59219) -->
        <timeTriggers>
            <timeLength>-60</timeLength>
            <workflowTimeTriggerUnit>Minutes</workflowTimeTriggerUnit>
            <actions>
                <name>Premier_First_Response_Warning</name>
                <type>Alert</type>
            </actions>
        </timeTriggers>

        <!-- VIOLATION trigger. Positive timeLength = after the target has passed.
             There is no documented "exactly at target" trigger, so a breach alert uses the
             smallest positive offset the unit allows. -->
        <timeTriggers>
            <timeLength>1</timeLength>
            <workflowTimeTriggerUnit>Minutes</workflowTimeTriggerUnit>
            <actions>
                <name>Premier_First_Response_Violation</name>
                <type>Alert</type>
            </actions>
            <actions>
                <name>Set_SLA_Breached_True</name>
                <type>FieldUpdate</type>
            </actions>
        </timeTriggers>

        <!-- SUCCESS actions fire when the milestone is completed (api_meta.txt:59194). -->
        <successActions>
            <name>Stamp_First_Response_Met</name>
            <type>FieldUpdate</type>
        </successActions>
    </milestones>

    <!-- ================= Milestone 2: Resolution ================= -->
    <milestones>
        <milestoneName>Resolution</milestoneName>

        <!-- 2880 minutes = 48 hours. -->
        <minutesToComplete>2880</minutesToComplete>

        <!-- Milestone-level calendar override. This one milestone counts on EMEA hours even
             though the process runs 24x7 (api_meta.txt:59162). -->
        <businessHours>EMEA Support Hours</businessHours>

        <!-- The milestone applies only to escalated cases, and because
             useCriteriaStartTime is true its clock starts when that criterion is first met,
             not when the case entered the process (api_meta.txt:59198-59201). -->
        <milestoneCriteriaFilterItems>
            <field>Case.IsEscalated</field>
            <operation>equals</operation>
            <value>true</value>
        </milestoneCriteriaFilterItems>
        <useCriteriaStartTime>true</useCriteriaStartTime>

        <timeTriggers>
            <timeLength>-240</timeLength>
            <workflowTimeTriggerUnit>Minutes</workflowTimeTriggerUnit>
            <actions>
                <name>Premier_Resolution_Warning</name>
                <type>Alert</type>
            </actions>
        </timeTriggers>
        <timeTriggers>
            <timeLength>1</timeLength>
            <workflowTimeTriggerUnit>Minutes</workflowTimeTriggerUnit>
            <actions>
                <name>Set_SLA_Breached_True</name>
                <type>FieldUpdate</type>
            </actions>
        </timeTriggers>
    </milestones>
</EntitlementProcess>
```

### How to read it

- **`timeTriggers` is the whole action model.** There is no `warningActions` element and no
  `violationActions` element in the `EntitlementProcessMilestoneItem` field table
  (api_meta.txt:59158–59202). A milestone has exactly `successActions` plus a list of
  `timeTriggers`; the sign of `timeLength` is what makes a trigger a warning or a violation.
- **Thresholds are offsets, not percentages.** `timeLength` is "the length of time between the time
  trigger activation and the milestone target completion date" (api_meta.txt:59213). A 75% warning on
  a 240-minute milestone is written `-60 Minutes`, and you recompute it by hand whenever
  `minutesToComplete` changes. Nothing scales it for you.
- **`workflowTimeTriggerUnit` accepts `Minutes`, `Hours`, `Days` only** (api_meta.txt:59220–59224).
  `minutesToComplete` is always minutes regardless of what the triggers use — a mismatch here is the
  single most common transcription bug in this file.
- **`actions` entries are `WorkflowActionReference`**: `name` plus a `type` from
  `Alert | FieldUpdate | FlowAction | OutboundMessage | Task` (api_meta.txt:139950–139968). The
  referenced component must exist in the org or in the same deploy.
- **`SObjectType` is `Case` or `Work Order`** (object_reference.txt:270729–270737). "An entitlement
  process runs only on records that match its type", so a Case process attached to an entitlement
  does nothing for that account's work orders.
- **Milestone criteria and process exit criteria are `FilterItem` lists**, with optional
  `criteriaBooleanFilter` / `exitCriteriaBooleanFilter` for filter logic, or a `*Formula` variant
  instead (api_meta.txt:59120–59128, 59167–59180).

---

## 3. The workflow actions the process names

`timeTriggers` and `successActions` only *reference* actions. Deploy them in the object's single
`Workflow` file — "one file per standard or custom object that has workflow" (api_meta.txt:139896).
The container root is `<Workflow>`; see `admin/workflow-field-update-patterns`
`references/metadata-examples.md` for the full container and `admin/approval-processes` for the same
file shared with an approval process.

`workflows/Case.workflow-meta.xml` (excerpt — the file also holds every other Case alert, field
update, task and rule, and a deploy replaces the whole file):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Workflow xmlns="http://soap.sforce.com/2006/04/metadata">
    <alerts>
        <fullName>Premier_First_Response_Warning</fullName>
        <description>Premier first response due in 1 hour</description>
        <protected>false</protected>
        <senderType>OrgWideEmailAddress</senderType>
        <senderAddress>support@acme.example</senderAddress>
        <template>unfiled$public/Premier_FirstResponse_Warning</template>
        <recipients>
            <type>owner</type>
        </recipients>
    </alerts>

    <alerts>
        <fullName>Premier_First_Response_Violation</fullName>
        <description>Premier first response SLA breached</description>
        <protected>false</protected>
        <senderType>OrgWideEmailAddress</senderType>
        <senderAddress>support@acme.example</senderAddress>
        <template>unfiled$public/Premier_FirstResponse_Violation</template>
        <recipients>
            <type>owner</type>
        </recipients>
        <recipients>
            <recipient>support.director@acme.example</recipient>
            <type>user</type>
        </recipients>
    </alerts>

    <alerts>
        <fullName>Premier_Resolution_Warning</fullName>
        <description>Premier resolution due in 4 hours</description>
        <protected>false</protected>
        <senderType>OrgWideEmailAddress</senderType>
        <senderAddress>support@acme.example</senderAddress>
        <template>unfiled$public/Premier_Resolution_Warning</template>
        <recipients>
            <type>owner</type>
        </recipients>
    </alerts>

    <fieldUpdates>
        <fullName>Set_SLA_Breached_True</fullName>
        <name>Set SLA Breached True</name>
        <description>Stamped by a milestone violation time trigger.</description>
        <field>SLA_Breached__c</field>
        <operation>Literal</operation>
        <literalValue>true</literalValue>
        <notifyAssignee>false</notifyAssignee>
        <protected>false</protected>
        <reevaluateOnChange>false</reevaluateOnChange>
    </fieldUpdates>

    <fieldUpdates>
        <fullName>Stamp_First_Response_Met</fullName>
        <name>Stamp First Response Met</name>
        <description>Stamped by the First Response success action.</description>
        <field>First_Response_Met__c</field>
        <operation>Formula</operation>
        <formula>NOW()</formula>
        <notifyAssignee>false</notifyAssignee>
        <protected>false</protected>
        <reevaluateOnChange>false</reevaluateOnChange>
    </fieldUpdates>
</Workflow>
```

`description`, `fullName`, `protected` and `template` are all **Required** on `WorkflowAlert`
(api_meta.txt:139975–140010); `field`, `fullName`, `name`, `notifyAssignee`, `operation` and
`protected` are **Required** on `WorkflowFieldUpdate` (api_meta.txt:140122–140175). A milestone action
that names a component missing any of these fails the whole deploy, not just the milestone.

Leave `reevaluateOnChange` at `false` on SLA stamps. Set to `true` it "reevaluates all workflow rules
on the associated object", and that cascade "can happen up to 5 times" (api_meta.txt:140176–140186) —
a breach flag is exactly the field you do not want re-triggering other automation.

---

## 4. The entitlement template

`entitlementTemplates/Premier_Phone_Support.entitlementTemplate-meta.xml`. The template is a set of
default terms; it points at the process by **name**, not by version file name
(api_meta.txt:59332–59337).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EntitlementTemplate xmlns="http://soap.sforce.com/2006/04/metadata">
    <businessHours>Premier 24x7</businessHours>
    <entitlementProcess>premier_support</entitlementProcess>
    <isPerIncident>true</isPerIncident>
    <casesPerEntitlement>50</casesPerEntitlement>
    <term>365</term>
    <type>Phone Support</type>
</EntitlementTemplate>
```

- `term` is "the number of days the entitlement is in effect" (api_meta.txt:59348) — days, not months.
- `casesPerEntitlement` is only meaningful with `isPerIncident` true; on the resulting `Entitlement`
  record `RemainingCases` "decreases in value by one each time a case is created with the entitlement"
  and "is only available if `IsPerIncident` is selected" (object_reference.txt:110345–110352).
  A per-incident entitlement that runs out stops applying the process to new cases.

---

## 5. The org switches

`settings/Entitlement.settings-meta.xml`. Deployed as `Settings` with member `Entitlement` — "the
component metadata type name without the 'Settings' suffix" (api_meta.txt:108368).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EntitlementSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableEntitlements>true</enableEntitlements>
    <enableEntitlementVersioning>true</enableEntitlementVersioning>
    <enableMilestoneFeedItem>false</enableMilestoneFeedItem>
    <enableMilestoneStoppedTime>true</enableMilestoneStoppedTime>
    <ignoreMilestoneBusinessHours>false</ignoreMilestoneBusinessHours>
    <entitlementLookupLimitedToActiveStatus>true</entitlementLookupLimitedToActiveStatus>
    <entitlementLookupLimitedToSameAccount>true</entitlementLookupLimitedToSameAccount>
    <entitlementLookupLimitedToSameAsset>false</entitlementLookupLimitedToSameAsset>
    <entitlementLookupLimitedToSameContact>false</entitlementLookupLimitedToSameContact>
    <assetLookupLimitedToActiveEntitlementsOnAccount>false</assetLookupLimitedToActiveEntitlementsOnAccount>
    <assetLookupLimitedToActiveEntitlementsOnContact>false</assetLookupLimitedToActiveEntitlementsOnContact>
    <assetLookupLimitedToSameAccount>false</assetLookupLimitedToSameAccount>
    <assetLookupLimitedToSameContact>false</assetLookupLimitedToSameContact>
</EntitlementSettings>
```

The four settings that change observable behaviour, per api_meta.txt:115615–115672:

| Setting | Effect |
|---|---|
| `enableEntitlements` | The master switch. Everything else in this file is inert while it is `false`. |
| `enableEntitlementVersioning` | Without it, `versionMaster` / `versionNumber` / `isVersionDefault` have nowhere to live — the guide marks all three "available … in organizations that have entitlement versioning enabled" (object_reference.txt:270688, 270752, 270775). Turn it on **before** you need a second version. |
| `enableMilestoneStoppedTime` | Shows *Stopped Time* and *Actual Elapsed Time* on the milestone. Without it, a case stopped mid-SLA reports elapsed time that nobody can reconcile. |
| `ignoreMilestoneBusinessHours` | `true` shows time remaining in **actual** hours rather than business hours. A reporting/display switch — it does not change when the triggers fire. |

<!-- UNVERIFIED (2026-09-04): the guide states the file is named "Entitlements.settings"
     (api_meta.txt:115607), while the general Settings rule (api_meta.txt:108374-108376) and the
     package.xml member rule (api_meta.txt:108368) both yield "Entitlement". The sibling skill
     admin/business-hours-and-holidays uses the DX-cased singular form for its own settings file,
     so the path above follows that convention. Retrieve Settings:Entitlement once and use whatever
     file name comes back. -->

---

## 6. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>MilestoneType</name>
    </types>
    <types>
        <members>*</members>
        <name>EntitlementProcess</name>
    </types>
    <types>
        <members>*</members>
        <name>EntitlementTemplate</name>
    </types>
    <types>
        <members>Case</members>
        <name>Workflow</name>
    </types>
    <types>
        <members>Entitlement</members>
        <members>BusinessHours</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

Wildcard status, verified type by type rather than assumed:

- `MilestoneType` — supported (api_meta.txt:88377), and the guide's own sample manifest shows
  `<members>* or a valid name of a milestone type</members>` (api_meta.txt:88360).
- `EntitlementProcess` — supported (api_meta.txt:59306). With versioning on, `*` retrieves **every
  version**, one file each.
- `EntitlementTemplate` — supported (api_meta.txt:59371).
- `Workflow` — supported; the guide shows `<members>*</members>` with `<name>Workflow</name>`
  (api_meta.txt:139884–139888).
- `Settings` — **not** per-setting. "The wildcard applies only when retrieving all settings, not for
  an individual setting" (api_meta.txt:115726–115729). Name each member.

---

## 7. Retrieve, deploy, and the versioning rule

Retrieve into a clean project first — you need the org's real file names before you can hand-edit:

```bash
sf project retrieve start \
  --metadata MilestoneType EntitlementProcess EntitlementTemplate \
  --metadata "Settings:Entitlement" \
  --metadata "Workflow:Case" \
  --target-org acme-sandbox
```

Validate against the target before you deploy, and run the tests the org requires:

```bash
sf project deploy validate \
  --source-dir force-app/main/default \
  --test-level RunLocalTests \
  --target-org acme-sandbox

sf project deploy start \
  --source-dir force-app/main/default \
  --target-org acme-sandbox
```

Deploy order matters within a single package: `MilestoneType` and the `Workflow` alerts/field updates
must resolve for the process's `milestoneName` and `actions/name` references to bind. Deploying them
in one package is the reliable way; the platform resolves intra-package references.

### Changing a process that is already active

**What the guide states, exactly.** `EntitlementProcess` files carry `versionMaster`, `versionNumber`
(int, "must be 1 or greater"), `versionNotes` and `isVersionDefault` ("indicates whether the
entitlement process is the default version"), all "available in API version 28.0 and later"
(api_meta.txt:59136–59152). One file holds one version (api_meta.txt:59077). Versions of the same
process share an identical `versionMaster` (api_meta.txt:59139–59142). On the record side,
`SlaProcess.NameNorm` is read-only and auto-generated per version as `process name + _v + x`
(object_reference.txt:270717–270727), and `SlaProcess` supports only
`describeSObjects(), query(), retrieve(), search(), describeLayout()` — **no `create()` or
`update()`** (object_reference.txt:270648).

So the safe change procedure is: deploy a **new file** with the next `versionNumber`, the same
`versionMaster`, and `isVersionDefault` moved to the new version.

`entitlementProcesses/premier_support_v2.entitlementProcess-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EntitlementProcess xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <description>Premier tier: 2h first response (contract change 2026-Q3). v2.</description>
    <SObjectType>Case</SObjectType>
    <businessHours>Premier 24x7</businessHours>
    <entryStartDateField>SlaStartDate</entryStartDateField>
    <exitCriteriaFilterItems>
        <field>Case.Status</field>
        <operation>equals</operation>
        <value>Closed</value>
    </exitCriteriaFilterItems>
    <versionMaster>premier_support</versionMaster>
    <versionNumber>2</versionNumber>
    <isVersionDefault>true</isVersionDefault>
    <versionNotes>First response cut from 240 to 120 minutes per 2026-Q3 contract.</versionNotes>
    <name>premier_support</name>
    <milestones>
        <milestoneName>First Response</milestoneName>
        <minutesToComplete>120</minutesToComplete>
        <useCriteriaStartTime>false</useCriteriaStartTime>
        <timeTriggers>
            <timeLength>-30</timeLength>
            <workflowTimeTriggerUnit>Minutes</workflowTimeTriggerUnit>
            <actions>
                <name>Premier_First_Response_Warning</name>
                <type>Alert</type>
            </actions>
        </timeTriggers>
        <timeTriggers>
            <timeLength>1</timeLength>
            <workflowTimeTriggerUnit>Minutes</workflowTimeTriggerUnit>
            <actions>
                <name>Set_SLA_Breached_True</name>
                <type>FieldUpdate</type>
            </actions>
        </timeTriggers>
        <successActions>
            <name>Stamp_First_Response_Met</name>
            <type>FieldUpdate</type>
        </successActions>
    </milestones>
</EntitlementProcess>
```

Note that `-60` became `-30`: the warning offset does not follow `minutesToComplete` down. Every
version bump is also a re-derivation of every `timeLength` in the file.

Ship the v1 file in the same deploy with one element changed:
`<isVersionDefault>false</isVersionDefault>`. The v1 listing in § 2 above still shows `true` because
that is how it was first deployed — if you copy both files verbatim into a package, the checker will
(correctly) fail it with `ERROR E2: versionMaster 'premier_support' has 2 files with
isVersionDefault true`. That is the check earning its keep, not a defect in the example.

<!-- UNVERIFIED (2026-09-04): the widely repeated rule "an active entitlement process cannot be
     edited, you must create a new version" is not stated in the Metadata API Developer Guide's
     EntitlementProcess section (api_meta.txt:59069-59308) nor in the Object Reference's SlaProcess
     section (object_reference.txt:270637-270790). What IS documented is the version model above and
     the absence of create()/update() on SlaProcess. Treat new-version-on-change as the procedure
     because it is the one the documented fields support, not because the guide forbids the edit. -->

---

## 8. Verification

### Is the process there, and which version is default?

```sql
SELECT Id, Name, NameNorm, VersionNumber, VersionMaster, IsVersionDefault,
       IsActive, SObjectType, BusinessHoursId, StartDateField
FROM SlaProcess
ORDER BY VersionMaster, VersionNumber
```

Exactly one row per `VersionMaster` should have `IsVersionDefault = true`
(object_reference.txt:270682–270693).

### Are entitlements actually live on accounts?

```sql
SELECT Id, Name, AccountId, SlaProcessId, StartDate, EndDate, Status,
       IsPerIncident, RemainingCases, BusinessHoursId
FROM Entitlement
WHERE Status = 'Active'
ORDER BY AccountId
```

`Status` is a picklist with properties `Filter, Nillable` only — **no `Create` and no `Update`**
(object_reference.txt:110364–110371). It is derived from `StartDate` / `EndDate`; you cannot force an
entitlement active by writing to it.

### Which milestones are breaching, by type?

```sql
SELECT MilestoneType.Name, COUNT(Id) breaches
FROM CaseMilestone
WHERE IsViolated = true AND CompletionDate = NULL
  AND TargetDate = LAST_N_DAYS:30
GROUP BY MilestoneType.Name
ORDER BY COUNT(Id) DESC
```

And the case-level list for the one that stands out:

```sql
SELECT CaseId, MilestoneType.Name, StartDate, TargetDate, CompletionDate,
       IsCompleted, IsViolated, TimeRemainingInMins, BusinessHoursId
FROM CaseMilestone
WHERE IsCompleted = false
  AND TargetDate = LAST_N_DAYS:7
ORDER BY TargetDate
```

`CaseMilestone.BusinessHoursId` on the row is the calendar that milestone instance actually used —
compare it against the process's `businessHours` to prove an override took effect rather than
assuming it did (object_reference.txt:63350–63356).

### Setup check

**Setup > Entitlement Processes** lists the process with the version you expect marked as the default
version, and opening a milestone shows the time triggers at the offsets in the XML — not percentages.
**Setup > Entitlement Settings** shows Entitlements enabled and, if you deployed v2 above, entitlement
versioning enabled.

---

## 9. Completing a milestone from Apex or Flow

Milestone *completion* is not automatic. `CaseMilestone` supports only
`describeLayout(), describeSObjects(), query(), retrieve(), update()` — no `create()`, no `delete()`
(object_reference.txt:63347–63348). Salesforce creates the rows when the case enters the process; your
automation's only lever is `update()`, and `CompletionDate` is one of exactly two updateable fields on
the object (`CompletionDate` and `StartDate`, object_reference.txt:63373–63380, 63403–63410).

The canonical shape — query the open milestone, stamp `CompletionDate`, update:

```apex
public with sharing class MilestoneCompletion {
    /** Completes the named milestone on the given cases. Bulk-safe: one query, one DML. */
    public static void complete(Set<Id> caseIds, String milestoneName) {
        List<CaseMilestone> open = [
            SELECT Id, CompletionDate
            FROM CaseMilestone
            WHERE CaseId IN :caseIds
              AND MilestoneType.Name = :milestoneName
              AND CompletionDate = NULL
            WITH USER_MODE
        ];
        if (open.isEmpty()) { return; }
        DateTime now = System.now();
        for (CaseMilestone cm : open) {
            cm.CompletionDate = now;
        }
        update as user open;
    }
}
```

Called from a record-triggered Flow, the same logic is an invocable wrapper — but the Flow cannot
create the `CaseMilestone` row either, so a Get Records that returns nothing means the case never
entered the process, not that the milestone is done.

<!-- UNVERIFIED (2026-09-04): the "MilestoneUtils" helper class that circulates in community posts
     does not appear anywhere in the Apex Developer Guide or the Apex Reference Guide extracts
     (grep -i "milestone" over apexdev.txt returns only the debug-log event rows at 39104-39117;
     apexrefguide.txt returns no CaseMilestone or MilestoneUtils hits). The class above is written
     from the CaseMilestone object's documented supported calls and updateable fields, not copied
     from a sample. -->

### When nothing is tracking, read the log, not the config

The Apex Developer Guide's debug-log event table (apexdev.txt:39104–39117) lists four events under the
**Workflow** category at **INFO and above** that are specific to this engine:

| Event | Logged with | What it tells you |
|---|---|---|
| `SLA_PROCESS_CASE` | Case ID | The engine looked at this case at all |
| `SLA_EVAL_MILESTONE` | Milestone ID | A specific milestone was evaluated |
| `SLA_NULL_START_DATE` | (none) | The case has no SLA start date — it never entered a process |
| `SLA_END` | number of cases, load time, processing time, number of case milestones to insert / update / delete, and new trigger | What the engine actually did |

Set a debug log on the case owner with Workflow = INFO, create a case through the failing intake
channel, and read for `SLA_NULL_START_DATE`. Its presence turns "milestones aren't working" into the
much narrower "this case never entered the process" — which is an entitlement-on-the-case problem, not
a milestone problem. Absence of all four events means the engine never ran.

---

## Related reading

- `admin/business-hours-and-holidays` — the calendars `businessHours` names, and the after-hours clock
  test; its `references/gotchas.md` § 5 is the process-vs-milestone-vs-Case calendar precedence rule.
- `admin/escalation-rules` — the other SLA clock, and its `references/metadata-examples.md` for the
  deploy-inactive cutover pattern this file's versioning section parallels.
- `admin/workflow-field-update-patterns` — the `Workflow` container in full.
- `admin/case-management-setup` — how a case gets an entitlement in the first place, per intake channel.
- `architect/sla-design-and-escalation-matrix` — what the numbers in `minutesToComplete` should be.
