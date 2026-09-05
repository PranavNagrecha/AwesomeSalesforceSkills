# Metadata Examples — Custom Notification Types

Deployable metadata for the send path: the notification type itself, the
org-level delivery settings that ship beside it, the Flow action that fires
it, the Apex call that fires it, the manifest, and the post-deploy check.

Channel policy, consent, and how many types an org should have belong to
`admin/custom-notification-type-design`. This file is the wiring.

---

## Where the files live

| Metadata type | Suffix | Directory | Available since | What it holds |
|---|---|---|---|---|
| `CustomNotificationType` | `.notiftype` | `notificationtypes/` | API 46.0 | The type: `customNotifTypeName`, `masterLabel`, `description`, `desktop`, `mobile`, `slack`, `actionGroups` (Beta) |
| `NotificationTypeConfig` | `.config` | `notificationTypeConfig/` | API 48.0 | Org-level delivery settings: which channels and which connected apps are enabled per notification type |

Source: Metadata API Developer Guide, `CustomNotificationType` — "The file
suffix is `.notiftype` for the notification type definition. Notification
types are stored in the `notificationtypes` directory of the corresponding
package directory." (`api_meta.txt:41783-41784`); version at
`api_meta.txt:41791`. `NotificationTypeConfig` suffix and folder at
`api_meta.txt:92203`, version at `api_meta.txt:92207`.

In a DX tree that resolves to:

```text
force-app/main/default/
├── notificationtypes/
│   └── Case_Priority_High.notiftype-meta.xml
├── notificationTypeConfig/
│   └── NotificationTypeConfig.config-meta.xml
├── flows/
│   └── Case_Priority_High_Notification.flow-meta.xml
└── classes/
    └── CaseEscalationNotifier.cls
```

---

## 1. The notification type

The guide's own sample definition is four elements
(`api_meta.txt:41877-41882`). This is that sample extended with the two
optional fields the Fields table documents.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/notificationtypes/Case_Priority_High.notiftype-meta.xml -->
<CustomNotificationType xmlns="http://soap.sforce.com/2006/04/metadata">
    <customNotifTypeName>Case_Priority_High</customNotifTypeName>
    <masterLabel>Case escalated to High</masterLabel>
    <description>Fires when a Case Priority changes to High. Reaches the case owner (or queue members) and the on-call support manager group.</description>
    <desktop>true</desktop>
    <mobile>true</mobile>
</CustomNotificationType>
```

**How to read it:**

- `customNotifTypeName` is **required**, max 80 characters
  (`api_meta.txt:41799-41800`). It is the API name — the value Flow and Apex
  look the type up by. On the sObject side the same value is exposed as
  `CustomNotificationType.CustomNotifTypeName`, which is `idLookup` and
  `Unique`, and "isn't namespaced, so it can't be duplicated across installed
  packages" (`object_reference.txt:88306-88313`).
- `masterLabel` is **required** (`api_meta.txt:41808`) and is the string users
  see. Do not paste `customNotifTypeName` into it — see
  `references/gotchas.md` Gotcha 5.
- `description` is optional, max 255 characters, and is "displayed with the
  notification type name" (`api_meta.txt:41802-41803`) — it is read by
  admins in Setup, not by recipients.
- `desktop` and `mobile` are both **required** booleans
  (`api_meta.txt:41805-41806`, `api_meta.txt:41810-41811`). On the sObject the
  default for each is `false` (`object_reference.txt:88337-88338`,
  `object_reference.txt:88385-88386`), so a type deployed with both omitted or
  both `false` sends to nowhere. The checker flags this.
- `slack` is documented as "Reserved for future use"
  (`api_meta.txt:41813`) — the sObject field `IsSlack` says the same
  (`object_reference.txt:88347-88352`). Omit it. It is not the switch that
  puts a notification into Slack.
- `actionGroups` (Beta) adds tappable actions to mobile notifications
  (`api_meta.txt:41795-41796`). Its `CustomNotificationActionDefinition`
  requires `actionLabel`, `actionName`, and an `actionType` of either
  `NotificationApiAction` or `Share`, with `actionTarget` naming the Apex
  class that implements it (`api_meta.txt:41843-41864`). Beta — do not put it
  on a delivery path you cannot fall back from.

---

## 2. The delivery settings that ship beside the type

`CustomNotificationType` says the type *can* use desktop and mobile.
`NotificationTypeConfig` is the org-level record of which channels and which
connected apps are actually enabled for it. It is a separate metadata type in
a separate folder, so retrieving the `.notiftype` alone does not bring it.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/notificationTypeConfig/NotificationTypeConfig.config-meta.xml
     Shape follows the guide's sample definition at api_meta.txt:92280-92296. -->
<NotificationTypeConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <notificationTypeSettings>
        <notificationType>Case_Priority_High</notificationType>
        <notificationChannels>
            <desktopEnabled>true</desktopEnabled>
            <mobileEnabled>true</mobileEnabled>
        </notificationChannels>
        <appSettings>
            <connectedAppName>Salesforce_Mobile_App</connectedAppName>
            <enabled>true</enabled>
        </appSettings>
    </notificationTypeSettings>
</NotificationTypeConfig>
```

**How to read it:**

- `notificationType` is **required** and takes the *API name* of the type —
  for a custom type that is the `customNotifTypeName` above; a type installed
  with a managed package carries its namespace prefix
  (`api_meta.txt:92221-92225`).
- `notificationChannels` carries `desktopEnabled`, `mobileEnabled`, and
  `slackEnabled` (`api_meta.txt:92269-92274`) — the same three channels as
  the type, expressed as an org setting rather than a type capability.
- `appSettings.connectedAppName` is **required** and is the connected app's
  API name (`api_meta.txt:92248-92249`). The guide's instruction for finding
  the real value is explicit: "Retrieve `NotificationTypeConfig` to see the API
  names of the connected apps supported for a notification type"
  (`api_meta.txt:92250-92251`). Do not guess it — the placeholder above is a
  placeholder. UNVERIFIED (2026-09-04): `Salesforce_Mobile_App` is not a
  connected-app API name taken from any guide in this set; retrieve the file
  from the target org and substitute the real name before deploying.
- Connected-app settings do not always survive a cross-org deploy. If an
  Enhanced Connected App and a Connected App share a name, or the CA was
  migrated to an ECA, only the ECA is returned on retrieve, "the CA settings
  aren't applied when you deploy the retrieved settings to a new org", and
  those app settings "can't be changed via the Metadata API. To change these
  app settings, use the UI." (`api_meta.txt:92258-92262`).

---

## 3. Firing it from Flow

The Flow metadata type documents `customNotificationAction` as a valid
`actionCalls.actionType`, "Sends a custom notification. This value is
available in API version 46.0 and later." (`api_meta.txt:68710`).

The excerpt below is one `actionCalls` element in the shape the Flow sample
definition uses (`api_meta.txt:73211-73248`), wrapped in a `<Flow>` root so it
parses standalone.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- EXCERPT — one actionCalls element lifted out of
     force-app/main/default/flows/Case_Priority_High_Notification.flow-meta.xml.
     The surrounding <start>, <recordLookups>, <assignments> and <status>
     elements are omitted; this will not deploy on its own. -->
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <actionCalls>
        <name>Send_Escalation_Notification</name>
        <label>Send Escalation Notification</label>
        <locationX>380</locationX>
        <locationY>458</locationY>
        <actionName>customNotificationAction</actionName>
        <actionType>customNotificationAction</actionType>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>customNotifTypeId</name>
            <value>
                <elementReference>Get_Notification_Type.Id</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>recipientIds</name>
            <value>
                <elementReference>recipientIds</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>title</name>
            <value>
                <elementReference>notificationTitle</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>body</name>
            <value>
                <elementReference>notificationBody</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>targetId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputParameters>
        <nameSegment>customNotificationAction</nameSegment>
        <versionSegment>1</versionSegment>
    </actionCalls>
</Flow>
```

**How to read it:**

- `actionType` is the enum value; `actionName` and `nameSegment` repeat the
  standard action's name, which is the pattern the guide's own `chatterPost`
  sample uses (`api_meta.txt:73253-73254`, `api_meta.txt:73272`).
- UNVERIFIED (2026-09-04): the five `inputParameters/name` values —
  `customNotifTypeId`, `recipientIds`, `title`, `body`, `targetId` — are not
  listed in `api_meta.txt`; the Flow metadata type documents only the
  `actionType` enum value, and the per-action input schema lives in the
  Actions Developer Guide, which is not in this source set. **Harvest the real
  names**: build the action once in Flow Builder, then
  `sf project retrieve start -m "Flow:<YourFlowName>"` and read the
  `inputParameters` the org wrote. Do not hand-author these names blind.
- `customNotifTypeId` takes an **Id**, not a name. Get it at run time with a
  Get Records on `CustomNotificationType` filtered on `DeveloperName` (section
  5) and reference the result, as above. A pasted `0ML…` literal is an
  org-specific value — the checker flags it.
- `targetId` is what makes the notification open a record when tapped.

The declarative view of these same inputs — the Flow Builder labels and what
each one truncates to on screen — is in `flow/flow-email-and-notifications`.

---

## 4. Firing it from Apex

The full class, its bulk wrapper, and its async placement belong to
`apex/apex-custom-notifications-from-apex`. This is the ten lines that show
the call shape, adapted from the Apex Reference Guide example at
`apexrefguide.txt:166600-166635`.

```apex
// EXCERPT — see apex/apex-custom-notifications-from-apex for the class,
// the chunking wrapper, and the Queueable/Batchable placement.
CustomNotificationType t =
    [SELECT Id FROM CustomNotificationType
     WHERE DeveloperName = 'Case_Priority_High' WITH USER_MODE LIMIT 1];

Messaging.CustomNotification n = new Messaging.CustomNotification();
n.setNotificationTypeId(t.Id);      // Id, resolved by name — never a literal
n.setTitle('Case escalated');       // required; max 250 characters
n.setBody('Priority is now High.'); // required; max 750 characters
n.setTargetId(caseId);              // targetId OR targetPageRef — one is required
n.send(new Set<String>{ ownerId }); // max 500 values in the set
```

**How to read it:**

- The lookup is by `DeveloperName`, which is the sObject field holding "the
  API name of the notification type" (`object_reference.txt:88340-88345`).
  The guide's own example queries exactly this way, with `WITH USER_MODE`
  (`apexrefguide.txt:166604-166609`).
- `setTitle` max 250 characters, `setBody` max 750
  (`apexrefguide.txt:166830`, `apexrefguide.txt:166860`); both are documented
  as required to send (`apexrefguide.txt:166831`, `apexrefguide.txt:166861`).
- `setNotificationTypeId(String id)`, `setTitle(String)`, `setBody(String)`,
  `setSenderId(String)`, `setTargetId(String)`, `setTargetPageRef(String)`,
  and `send(Set<String>)` are the documented members
  (`apexrefguide.txt:166757-166762`, `166792-166797`, `166819-166824`,
  `166842-166847`, `166872-166877`, `166895-166900`, `166924-166929`). There
  is also a six-argument constructor
  `CustomNotification(typeId, sender, title, body, targetId, targetPageRef)`
  that sets everything at once (`apexrefguide.txt:166689-166690`).
- Sending requires the **Send Custom Notifications** user permission; without
  it "the `send()` method fails" (`apexrefguide.txt:166590-166594`). Grant it
  to the running user — for a record-triggered Flow in system context that is
  usually not an issue, but for an Apex path invoked by an end user it is.

---

## 5. Resolving recipients

`send()` takes `Set<String> users`, and the guide enumerates exactly which Id
kinds are valid (`apexrefguide.txt:166766-166781`):

| Id you put in the set | Who receives it | Precondition |
|---|---|---|
| `UserId` | that user | the user is active |
| `GroupId` | all active members of the group | — |
| `QueueId` | all active members of the queue | — |
| `AccountId` | all active members of that account's **Account Team** | account teams enabled for the org |
| `OpportunityId` | all active members of that opportunity's **Opportunity Team** | team selling enabled for the org |

"Values can be combined in a set, up to the maximum of 500 values."
(`apexrefguide.txt:166781`).

The two consequences that catch people:

- The cap counts **Ids in the set, not people reached**. One `QueueId` is one
  value even if the queue holds 4,000 members — so a queue-based fan-out never
  trips the 500 cap, while a hand-assembled `Set<String>` of 800 user Ids does.
- "if this user is active" (`apexrefguide.txt:166770`) is the whole contract
  for inactive recipients. An inactive user in the set is not an error; that
  recipient simply does not receive it.

To resolve the type Id declaratively, the equivalent of the Apex query is a
Get Records on the sObject (`object_reference.txt:88293-88294`, API 47.0+):

```sql
SELECT Id, DeveloperName, MasterLabel, Desktop, Mobile
FROM CustomNotificationType
WHERE DeveloperName = 'Case_Priority_High'
LIMIT 1
```

---

## 6. `targetId` versus `targetPageRef`

| | `setTargetId` / `targetId` | `setTargetPageRef` / `targetPageRef` |
|---|---|---|
| Takes | a record Id | a `pageReference` JSON string |
| Opens | that record | any navigable page (list view, tab, app page) |
| Use when | the notification is about one record | there is no single record — a summary, a batch result, a list |

The rule the guide states plainly: "You must specify a target for a
notification… Neither attribute is required, but if both are omitted, `send()`
throws an exception. If there's no natural target for a notification, set the
`targetID` to a dummy value, such as `000000000000000AAA`. A dummy value
prevents the exception, and also prevents automatic navigation."
(`apexrefguide.txt:166572-166575`). Both may be set at once, and "the client
app that receives the notification determines which target, if any, to use"
(`apexrefguide.txt:166576-166577`).

Prefer `targetId` when you have one. Before Winter '21 only `targetId` existed
and "most client applications expect to find a `targetID` in the notification
payload" — if a client app cannot handle a `targetPageRef`-only notification,
"set the `targetID` to a dummy value" (`apexrefguide.txt:166587-166589`).

---

## 7. package.xml

`CustomNotificationType` **does not support the wildcard** — "This metadata
type doesn't support the wildcard character `*` (asterisk) in the
`package.xml` manifest file." (`api_meta.txt:41892-41894`). Every type must be
named individually.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case_Priority_High</members>
        <members>Territory_Realigned</members>
        <name>CustomNotificationType</name>
    </types>
    <types>
        <members>NotificationTypeConfig</members>
        <name>NotificationTypeConfig</name>
    </types>
    <types>
        <members>Case_Priority_High_Notification</members>
        <name>Flow</name>
    </types>
    <types>
        <members>CaseEscalationNotifier</members>
        <name>ApexClass</name>
    </types>
    <version>62.0</version>
</Package>
```

`<members>` for `CustomNotificationType` is the `customNotifTypeName` /
`DeveloperName`, not the label.

---

## 8. Retrieve and deploy

```bash
# Pull an existing type — also the way to harvest a real Flow's
# customNotificationAction inputParameters (section 3) and the real
# connected-app API names for NotificationTypeConfig (section 2).
sf project retrieve start \
  -m "CustomNotificationType:Case_Priority_High" \
  -m "NotificationTypeConfig" \
  -m "Flow:Case_Priority_High_Notification" \
  -o my-sandbox

# Validate before you ship: check-only, nothing is committed to the org.
sf project deploy validate \
  -d force-app/main/default/notificationtypes \
  -d force-app/main/default/notificationTypeConfig \
  -o my-prod

# Deploy the type before the Flow or class that references it.
sf project deploy start \
  -x manifest/package.xml \
  -o my-prod
```

Order matters: a Flow whose `customNotifTypeId` resolves at run time will
deploy either way, but a Flow that runs before the type exists fails at
execution, not at deploy.

---

## 9. Verify after deploy

**Step 1 — the type landed with usable channels.** Run in the target org:

```sql
SELECT Id, DeveloperName, MasterLabel, Desktop, Mobile, NamespacePrefix
FROM CustomNotificationType
WHERE DeveloperName = 'Case_Priority_High'
```

Expect one row. `Desktop` or `Mobile` must be `true` — both default to
`false` (`object_reference.txt:88337-88338`, `88385-88386`), so a row with
both `false` deployed but delivers nothing. Record the returned `Id`: it is
org-specific and will differ from the sandbox value, which is why nothing
should hard-code it.

**Step 2 — the bell.** Fire the trigger condition with a test record, then, as
the recipient user, open the bell icon in the Lightning header. A bell entry
proves the type, the recipient resolution, and the send all worked. It does
**not** prove mobile push — desktop and mobile are independent channels, and
the org's hourly push allocation can be exhausted while in-app notifications
keep being created (`salesforce_app_limits_cheatsheet.txt:465-466`). For a
mobile claim, test on a real device.

**Step 3 — the click target.** Tap the bell entry as the recipient, not as an
admin. It must land on the target record. If it lands on "Insufficient
Privileges", the notification reached someone who cannot see what it is about
— see `references/gotchas.md` Gotcha 4.
