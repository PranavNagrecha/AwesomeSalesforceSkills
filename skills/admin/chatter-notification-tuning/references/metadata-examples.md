# Metadata Examples — Chatter Notification Tuning

Notification volume is produced by four surfaces, and only two of them are metadata:

| Surface | Kind | How it moves |
|---|---|---|
| `ChatterSettings` (`Chatter.settings`) | metadata | `package.xml` → `<name>Settings</name>`, `<members>Chatter</members>` |
| `ChatterEmailsMDSettings` (`ChatterEmailsMD.settings`) | metadata | `package.xml` → `<name>Settings</name>`, `<members>ChatterEmailsMD</members>` |
| `CustomNotificationType` (`.notiftype`) | metadata | `package.xml` → `<name>CustomNotificationType</name>`, **no wildcard** (api_meta.txt L41932–41934) |
| Feed Tracking (`enableFeeds`, `trackFeedHistory`) | metadata | object + field files |
| `User.DefaultGroupNotificationFrequency`, `User.DigestFrequency`, `User.UserPreferencesDisable*Email` | **data** | Data Loader / SOQL / DML on the `User` sObject |
| `CollaborationGroupMember.NotificationFrequency` | **data** | Data Loader / DML |

Shapes for the metadata half are taken from the Metadata API Developer Guide (v62 PDF —
`ChatterEmailsMDSettings` api_meta.txt L112368–112445, `ChatterSettings` L112452–112648,
`CustomNotificationType` L41769–41934, `trackFeedHistory` L43668–43672, `enableFeeds` L42035–42039)
and extended to one worked tuning baseline. Field semantics for the data half come from the Object
Reference (`CollaborationGroupMember` object_reference.txt L67430–67540, `User` L295156–295207 and
L296124–296300, `FeedItem` L136330–136560, `EntitySubscription` L111051–111200).

Group *lifecycle* metadata — archiving, unlisted groups, creation permissions — belongs to
`admin/chatter-group-governance`; that skill owns the `Chatter.settings` elements this one does not
touch.

---

## 1. `ChatterEmailsMD.settings` — the email surface

`force-app/main/default/settings/ChatterEmailsMD.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ChatterEmailsMDSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableChatterDigestEmailsApiOnly>false</enableChatterDigestEmailsApiOnly>
    <enableChatterEmailAttachment>false</enableChatterEmailAttachment>
    <enableCollaborationEmail>true</enableCollaborationEmail>
    <enableDisplayAppDownloadBadges>false</enableDisplayAppDownloadBadges>
    <enableEmailReplyToChatter>true</enableEmailReplyToChatter>
    <enableEmailToChatter>false</enableEmailToChatter>
    <noQnOwnNotifyOnCaseCmt>false</noQnOwnNotifyOnCaseCmt>
    <noQnOwnNotifyOnRep>false</noQnOwnNotifyOnRep>
    <noQnSubNotifyOnBestR>false</noQnSubNotifyOnBestR>
    <noQnSubNotifyOnRep>false</noQnSubNotifyOnRep>
</ChatterEmailsMDSettings>
```

### How to read it

- **`enableCollaborationEmail`** (L112391–112392) is the only master switch this type has: "whether
  collaboration email notifications can be sent (`true`) or not (`false`)." Set it `false` and every
  per-user and per-group frequency below it is inert — which is a blunt instrument, not a tuning move.
  The checker raises `CNT-EMAIL-MASTER` when it is `false` while `enableChatter` is `true`, because
  that combination usually means someone reached for the master switch instead of the dials.
- **There is no default-digest-frequency element here, and no `emailOnAllPosts` /
  `emailOnFollowedPosts` / `emailOnAtMention` element either.** The ten elements above are the entire
  documented field table (L112383–112418). Everything per-event — mentions, likes, comments after
  a like, follower notifications — lives on the `User` record as `UserPreferencesDisable*Email`
  fields (section 4), not in this file. If an assistant hands you a `ChatterEmailsMD.settings` with an
  `emailOn*` element in it, the deploy fails; the checker's `CNT-SETTINGS-ELEMENT` catches it first.
- **`enableChatterDigestEmailsApiOnly`** (L112386–112387) — "whether Chatter digests can be sent via
  the API, rather than according to the regular schedule." A `true` here is the answer to "digests
  stopped arriving on Monday mornings"; the checker prints it as an INFO note for exactly that reason.
- **`enableEmailReplyToChatter`** (L112399–112400) and **`enableEmailToChatter`** (L112401–112402) are
  the two inbound halves: replying to a notification by email, and posting to a feed by email. Both
  add feed volume. `enableEmailToChatter = false` is a cheap way to close one automated-post channel
  that no Flow audit will ever find.
- **`enableDisplayAppDownloadBadges`** (L112395–112396) adds iOS/Android download badges to Chatter
  notifications. It changes nothing about volume; turn it off only for the cosmetic reason.
- The four `noQn*` elements are Chatter Questions notifications, and their polarity is inverted:
  `noQnOwnNotifyOnRep` "indicates whether a user is notified when a reply is posted on their question
  (`false`) or not (`true`)" (L112407–112408). `false` means notify. Read them twice.

### Not this type

`ChatterAnswersSettings` (api_meta.txt L112253 onward) carries `emailFollowersOnReply`,
`emailOwnerOnReply`, and similar `email*` names. It is the Chatter Answers *forum* feature and is
unrelated to Chatter notification tuning. Grepping the guide for "email" under "chatter" lands there
first; do not deploy it by mistake.

---

## 2. `Chatter.settings` — the two elements that move notification volume

`force-app/main/default/settings/Chatter.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ChatterSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableApprovalRequest>false</enableApprovalRequest>
    <enableChatter>true</enableChatter>
    <enableRichLinkPreviewsInFeed>true</enableRichLinkPreviewsInFeed>
</ChatterSettings>
```

### How to read it

- **`enableApprovalRequest`** (L112490–112496) is the highest-volume element in this file for most
  orgs: "When the value is `true`, users see approval requests as posts in Chatter feeds. Users can
  update their own Chatter feeds settings to opt out of receiving approval requests as Chatter posts.
  When the value is `false`, approval requests aren't posted to Chatter. The default value is
  `false`." An org with a busy approval process and this set to `true` is generating a feed post per
  submission — and the opt-out is per user, so nobody's inbox gets quiet without either the org flag
  or a per-user campaign.
- **`enableChatter`** (L112517–112519) is the on/off switch for the whole feature. It is in this file
  for completeness only; treat flipping it as a separate decision with its own change record, not as
  a noise fix.
- **`enableRichLinkPreviewsInFeed`** (L112582–112586) converts links into embedded video, image, and
  article previews. It does not change the number of posts, only their weight in the feed — relevant
  when the complaint is "the feed is unreadable" rather than "there are too many emails."
- **`allowSharingInChatterGroup` is Removed**: "The setting of this field has no effect on the org.
  Available in API version 47.0 only" (L112487–112489). Retrieved trees from old orgs still carry it;
  the checker raises `CNT-SETTINGS-REMOVED` so it gets dropped rather than debated.
- **Deploy only the elements you changed.** There is one settings file per settings component
  (L112459–112461) — you cannot scope it per profile, and a full-file deploy overwrites every element
  in it, including the group-lifecycle elements that `admin/chatter-group-governance` owns. Retrieve,
  diff, and deploy the whole file knowingly, or coordinate with whoever owns the other half.

---

## 3. `CustomNotificationType` — the migration target for transient alerts

`force-app/main/default/notificationtypes/Opportunity_Won_Internal.notiftype-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomNotificationType xmlns="http://soap.sforce.com/2006/04/metadata">
    <customNotifTypeName>Opportunity_Won_Internal</customNotifTypeName>
    <description>Owner alert when an Opportunity reaches Closed Won. Replaces the
        chatterPost action formerly in the Opportunity_Stage_Change flow.</description>
    <desktop>true</desktop>
    <masterLabel>Opportunity Won</masterLabel>
    <mobile>true</mobile>
</CustomNotificationType>
```

### How to read it

- The file suffix is `.notiftype` and the directory is `notificationtypes/` (L41779–41781);
  the type is available in API version 46.0 and later (L41785).
- **`desktop` and `mobile` are the only delivery channels**, and both are `Required`
  (L41802–41812). `slack` is "Reserved for future use." There is no "in-app" channel element — if a
  generated file has one, it will not deploy. Both `false` produces a notification type that delivers
  nowhere, which the checker flags as `CNT-NOTIFTYPE-CHANNEL`.
- `customNotifTypeName` maxes at 80 characters, `description` at 255 (L41797–41801).
- **No wildcard**: "This metadata type doesn't support the wildcard character `*` in the package.xml
  manifest file" (L41932–41934). List each notification type by name.
- The Flow-side counterpart is `actionType` `customNotificationAction` — "Sends a custom
  notification. This value is available in API version 46.0 and later" (L68710) — replacing
  `chatterPost`, "Posts to Chatter" (L68655).

---

## 4. Feed Tracking — the object and field half

`force-app/main/default/objects/Account/Account.object-meta.xml` (fragment)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableFeeds>true</enableFeeds>
</CustomObject>
```

`force-app/main/default/objects/Account/fields/Account_Status__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Account_Status__c</fullName>
    <label>Account Status</label>
    <type>Picklist</type>
    <trackFeedHistory>true</trackFeedHistory>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Prospect</fullName>
                <default>true</default>
                <label>Prospect</label>
            </value>
            <value>
                <fullName>Active</fullName>
                <default>false</default>
                <label>Active</label>
            </value>
            <value>
                <fullName>Churned</fullName>
                <default>false</default>
                <label>Churned</label>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

### How to read it

- **`trackFeedHistory` has a hard prerequisite**: "To set this field to `true`, the `enableFeeds`
  field on the associated CustomObject must also be `true`" (L43668–43672). Deploying the field
  without the object file in the same package is the most common failure here; the checker's
  `CNT-TRACK-NO-FEEDS` catches it before the deploy does.
- **System fields cannot be feed-tracked at all.** Only standard fields "to which you can add help
  text or enable history tracking or Chatter feed tracking" are supported — "Other standard fields
  aren't supported, including system fields (such as `CreatedById` or `LastModifiedDate`) and
  autonumber fields" (L2164–2167, repeated at L43210–43213). A "someone tracked `LastModifiedDate`"
  diagnosis is a dead end; look at qualitative picklists and owner fields instead.
- **Per record type**: `recordTypeTrackFeedHistory` (L42234–42241) enables feed tracking for one
  record type, with the same `enableFeeds` prerequisite. This is the surgical lever when one record
  type — an automated integration record type, say — is the noise source and the others are fine.
- A tracked change produces a `FeedItem` of `Type` `TrackedChange`, defined as "a change **or group
  of changes** to a tracked field" (object_reference.txt L136377–136378). Several tracked fields
  changed in one save do not necessarily produce several feed items — so field count is a proxy for
  noise, not a multiplier of it.

---

## 5. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Chatter</members>
        <members>ChatterEmailsMD</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Opportunity_Won_Internal</members>
        <name>CustomNotificationType</name>
    </types>
    <types>
        <members>Account</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Account.Account_Status__c</members>
        <name>CustomField</name>
    </types>
    <version>62.0</version>
</Package>
```

The `Settings` block follows the guide's own `ChatterSettings` manifest sample (L112629–112637),
which uses `<members>Chatter</members>` under `<name>Settings</name>`; `ChatterEmailsMD` is the
matching member name from its file-suffix note (L112377–112380). The wildcard `*` does **not** work
for an individual settings type — "the wildcard applies only when retrieving all settings, not for an
individual setting" (L112640–112648) — nor for `CustomNotificationType` (L41932–41934).

---

## 6. Retrieve and deploy

```bash
# Retrieve the current baseline before changing anything
sf project retrieve start \
    --metadata Settings:Chatter Settings:ChatterEmailsMD \
    --target-org prod-audit

# Lint what came back, before you edit it
python3 scripts/check_chatter_notification_tuning.py \
    --manifest-dir force-app/main/default

# Validate against production without committing the change
sf project deploy validate --manifest manifest/package.xml --target-org prod

# Deploy
sf project deploy start --manifest manifest/package.xml --target-org prod
```

---

## 7. The data half — the digest policy, and the DML that applies it

Frequencies are `User` and `CollaborationGroupMember` data, never metadata. Write the intent down
first so it is reviewable, then generate the DML from it.

`notification-policy.json`

```json
{
  "defaultGroupNotificationFrequency": "W",
  "justification": "Weekly keeps a heartbeat for project groups without a per-post inbox; broadcast groups override to D.",
  "groupOverrides": [
    {"groupName": "Announce-AllHands", "frequency": "D", "reason": "Broadcast group, IsBroadcast=true, low post rate"},
    {"groupName": "Project-Atlas", "frequency": "W", "reason": "Active project, weekly is enough"},
    {"groupName": "Topic-Watercooler", "frequency": "N", "reason": "Social group, opt-in reading only"}
  ]
}
```

Lint it against the real group population before any DML runs:

```bash
sf data query --result-format csv --target-org prod \
    --query "SELECT Id, Name, IsBroadcast, IsArchived FROM CollaborationGroup" > groups.csv

python3 scripts/check_chatter_notification_tuning.py \
    --manifest-dir force-app/main/default \
    --policy notification-policy.json \
    --group-inventory groups.csv
```

`CNT-POLICY-GROUP` fires when an override names a group that does not exist — the failure mode where
a rename made the whole override a no-op and nobody noticed. `CNT-FREQ-VALUE` fires on any value
outside `D` / `W` / `N` / `P`, which is the complete documented enum for
`CollaborationGroupMember.NotificationFrequency` (object_reference.txt L67510–67520). There is no
`L`, and no `Limited`.

### Member CSV for Data Loader

`members_update.csv` — update, not upsert; `Id` is the `CollaborationGroupMember` id.

```csv
Id,NotificationFrequency
0FBRM0000000001AAA,W
0FBRM0000000002AAA,W
0FBRM0000000003AAA,N
0FBRM0000000004AAA,D
```

```bash
python3 scripts/check_chatter_notification_tuning.py --member-csv members_update.csv
```

`NotificationFrequency` is "Required. The frequency at which Salesforce sends Chatter group email
digests to this member. **Can only be set by the member or users with the 'Modify All Data'
permission**" (object_reference.txt L67510–67513). Group ownership is not enough — see
`references/gotchas.md` gotcha 2.

### User CSV for the personal digest and per-event email

`users_update.csv` — the per-user half. Every one of these is a plain `User` field with
`Create, Filter, Update` properties, so ordinary Data Loader reaches them.

```csv
Id,DigestFrequency,DefaultGroupNotificationFrequency,UserPreferencesDisableAllFeedsEmail,UserPreferencesDisableLikeEmail,UserPreferencesDisCommentAfterLikeEmail
005RM000000001AAA,W,W,false,true,true
005RM000000002AAA,N,N,true,true,true
005RM000000003AAA,D,W,false,false,true
```

| Column | Meaning | Source |
|---|---|---|
| `DigestFrequency` | personal email digest: `D` / `W` / `N`, default `D` | object_reference.txt L295200–295207 |
| `DefaultGroupNotificationFrequency` | frequency inherited **when the user joins a group**: `P` / `D` / `W` / `N`, default `N` — but `D` for Professional, Enterprise, Unlimited and Developer orgs that existed before API version 22.0 | L295156–295172 |
| `UserPreferencesDisableAllFeedsEmail` | when `false`, the user receives email for all feed updates, subject to the individual types below | L296132–296140 |
| `UserPreferencesDisableLikeEmail` | when `false`, email on every like of the user's post or comment | L296220–296227 |
| `UserPreferencesDisCommentAfterLikeEmail` | when `false`, email on every comment on a post the user liked | L296271–296278 |

Note the double negative on every `UserPreferencesDisable*` field: `false` means the email is **on**.
The full documented set — bookmark, change-comment, endorsement, file-share-for-API, followers,
later-comment, like, mentions-in-post, mentions-in-comment, message, profile-post, share-post — is at
L296132–296300.

### DML alternative, when the change is conditional

```apex
// Move every member of the project groups to weekly, but leave anyone who
// deliberately chose Never alone. Requires Modify All Data.
Set<Id> projectGroupIds = new Map<Id, CollaborationGroup>([
    SELECT Id FROM CollaborationGroup
    WHERE Name LIKE 'Project-%' AND IsArchived = false
]).keySet();

List<CollaborationGroupMember> updates = new List<CollaborationGroupMember>();
for (CollaborationGroupMember m : [
    SELECT Id, NotificationFrequency
    FROM CollaborationGroupMember
    WHERE CollaborationGroupId IN :projectGroupIds
]) {
    if (m.NotificationFrequency != 'N' && m.NotificationFrequency != 'W') {
        m.NotificationFrequency = 'W';   // W = Weekly. Not 'Weekly', and there is no 'L'.
        updates.add(m);
    }
}
if (!updates.isEmpty()) {
    Database.update(updates, false);
}
```

---

## 8. Verification

Settings components have no queryable record, so verification splits by surface.

**Metadata surface — Setup.** Setup → Feature Settings → Chatter → Chatter Settings; confirm *Allow
Approvals* matches your `enableApprovalRequest` value (the guide gives that as the Setup label,
L112495–112496). Setup → Feature Settings → Chatter → Email Settings for the
`ChatterEmailsMDSettings` half. Then re-run the checker against a **re-retrieved** tree — a clean run
on the retrieved copy is the deploy's receipt:

```bash
sf project retrieve start --metadata Settings:Chatter Settings:ChatterEmailsMD --target-org prod
python3 scripts/check_chatter_notification_tuning.py --manifest-dir force-app/main/default
```

**Data surface — SOQL.** The distribution is the measurement, not a spot check:

```sql
-- Where the group digest population actually sits, after the load
SELECT NotificationFrequency, COUNT(Id) members
FROM CollaborationGroupMember
GROUP BY NotificationFrequency

-- Users still on the per-post default for groups they have yet to join
SELECT COUNT(Id)
FROM User
WHERE IsActive = true AND DefaultGroupNotificationFrequency = 'P'

-- Users with every feed email switched on (the double negative: false = on)
SELECT Id, Username, DigestFrequency
FROM User
WHERE IsActive = true AND UserPreferencesDisableAllFeedsEmail = false
ORDER BY Username
```

**Volume surface — FeedItem.** Direct `FeedItem` queries need the View All Data permission: "If
you're using API version 23.0 or later and have View All Data permission, you can directly query for
a FeedItem" (object_reference.txt L136505–136507). Run this as an admin, before the change and again
two weeks after:

```sql
SELECT Type, COUNT(Id) posts
FROM FeedItem
WHERE CreatedDate = LAST_N_DAYS:30
GROUP BY Type
ORDER BY COUNT(Id) DESC
```

`TrackedChange` dominating the result means the fix is Feed Tracking (section 4). `TextPost`
dominating with a small set of `CreatedById` values means the fix is the Flow and Apex inventory
(section 3, and the checker's `CNT-FLOW-CHATTERPOST` / `CNT-APEX-FEEDITEM` findings).
