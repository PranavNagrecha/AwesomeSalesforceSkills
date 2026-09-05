# Metadata Examples — Service Cloud Voice Setup

Deployable shapes for the metadata a Service Cloud Voice contact center actually consists of. Element
names, enum values, ranges, and the base skeletons come from the Metadata API Developer Guide
(Summer '26 / v62 PDF) and the Object Reference; the worked examples extend the guide's own sample
definitions to a realistic Amazon Connect contact center. Line citations below are `grep -n` numbers
into the extracted guide text and are given so a reviewer can re-verify each element name.

Validate a retrieved manifest with:

```bash
python3 skills/admin/service-cloud-voice-setup/scripts/check_service_cloud_voice_setup.py \
  --manifest-dir force-app/main/default
```

> The Salesforce-guided provisioning UI creates most of this metadata for you. Author XML by hand only
> for the pieces the UI does not own — the Omni-Channel service channel, presence statuses, presence
> configuration, permission sets, and org settings. For the contact center itself, **retrieve first,
> edit, redeploy**: the `sections`/`items` names inside a live Service Cloud Voice `CallCenter` are
> vendor-generated. UNVERIFIED (2026-09-05): the Metadata API Developer Guide documents the
> `CallCenter` container shape (api_meta.txt L31421–31552) but publishes no Amazon Connect item-name
> list, so the item names in the example below are illustrative placeholders, not a documented contract.

---

## Where the files live

| Type | package.xml `<name>` | File in a DX project | Available since | Guide line |
|---|---|---|---|---|
| `CallCenter` | `CallCenter` | `callCenters/<Name>.callCenter-meta.xml` | API 27.0 | api_meta.txt L31431–31438 |
| `CallCenterRoutingMap` | `CallCenterRoutingMap` | `callCenterRoutingMaps/<Name>.callCenterRoutingMap-meta.xml` | API 52.0 | api_meta.txt L31702–31709 |
| `ConversationVendorInfo` | `ConversationVendorInfo` | `ConversationVendorInformation/<Name>.ConversationVendorInformation-meta.xml` | API 52.0 | api_meta.txt L38636–38643 |
| `ServiceChannel` | `ServiceChannel` | `serviceChannels/<Name>.serviceChannel-meta.xml` | API 44.0 | api_meta.txt L107764–107771 |
| `ServicePresenceStatus` | `ServicePresenceStatus` | `servicePresenceStatuses/<Name>.servicePresenceStatus-meta.xml` | API 44.0 | api_meta.txt L107950–107957 |
| `PresenceUserConfig` | `PresenceUserConfig` | `presenceUserConfigs/<Name>.presenceUserConfig-meta.xml` | API 44.0 | api_meta.txt L96968–96975 |
| `ServiceCloudVoiceSettings` | `Settings` (`<members>ServiceCloudVoice</members>`) | `settings/ServiceCloudVoice.settings-meta.xml` | API 52.0 | api_meta.txt L126808–126816 |
| `MyDomainSettings` | `Settings` (`<members>MyDomain</members>`) | `settings/MyDomain.settings-meta.xml` | API 47.0 | api_meta.txt L122094–122101 |

`ContactCenterChannel` is **not** a top-level type — it is a subtype serialised inside `CallCenter`
under `contactCenterChannels` (api_meta.txt L31553–31556). `ServiceChannel`,
`ServicePresenceStatus`, and `PresenceUserConfig` all carry the same special access rule: "This type
is available only if Omni-Channel is enabled in your org" (api_meta.txt L107773, L107963, L96978).

### How to read the examples

- **`fullName` is implicit.** All eight types extend `Metadata` and inherit `fullName`
  (api_meta.txt L31427, L38632, L96966). In a DX project the file name supplies it; do not add a
  `<fullName>` element to a source-format file.
- **`relatedEntityType`, not `relatedEntity`.** The `ServiceChannel` element that names the work
  object is `relatedEntityType` and it is Required (api_meta.txt L107858). Searching a manifest for
  `relatedEntity` misses it.
- **ACW lives on the channel, not on the contact center.** `hasAfterConvoWorkTimer` plus
  `afterConvoMaxTime` are `ServiceChannel` fields, "Available only for service channels of type
  Messaging or Voice" (api_meta.txt L107784–107792, L107832–107841). Since API 65.0 the same pair also exists on
  `PresenceUserConfig` as `hasAfterConvoWorkTimer` / `afterConvoWorkMaxTime`
  (api_meta.txt L96989–96993, L97037–97046).
- **Every ACW seconds value is 10–3600.** Both `afterConvoMaxTime` and `acwExtensionDuration` state
  "Specify a value from 10 through 3600" (api_meta.txt L107784–107788, L107778–107783).
  `maxExtensions` is 1 through 10 (api_meta.txt L107852–107856).
- **`vendorType` is a restricted enum.** Valid values are `Amazon_Connect`,
  `BringYourOwnChannelPartner`, `BringYourOwnContactCenter`, `ServiceCloudVoicePartner`
  (api_meta.txt L39028–39034). Anything else fails the deploy.
- **A presence status with no `channels` becomes an Away status.** "If no service channels are
  included, the presence status is automatically marked as 'Away'" (api_meta.txt L107966–107970) —
  so an agent assigned only that status can never be routed a call.

---

## 1. Org settings: turn Service Cloud Voice on

`settings/ServiceCloudVoice.settings-meta.xml` — every field below is from the
`ServiceCloudVoiceSettings` table at api_meta.txt L126818–126900.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ServiceCloudVoiceSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Service Cloud Voice with Amazon Connect. Default false. (L126897-126900) -->
    <enableServiceCloudVoice>true</enableServiceCloudVoice>
    <!-- Omni-Channel capacity is honoured by Voice AgentWork. Default false. API 54.0+ (L126841-126851) -->
    <enableOmniCapacityForSCV>true</enableOmniCapacityForSCV>
    <!-- Match inbound callers to end user records. Default false. API 53.0+ (L126837-126839) -->
    <enableEndUserForSCV>true</enableEndUserForSCV>
    <!-- Sync contact center queues, voice groups and users with Amazon Connect.
         Default false. API 55.0+ (L126825-126831) -->
    <enableAmazonQueueManagement>true</enableAmazonQueueManagement>
    <!-- Redact inbound/outbound numbers in Omni-Channel views, recordings and transcripts.
         Default false. API 61.0+ (L126856-126865) -->
    <enablePhoneNumberMaskingForSCV>false</enablePhoneNumberMaskingForSCV>
</ServiceCloudVoiceSettings>
```

Do **not** confuse this file with `settings/Voice.settings-meta.xml`. `VoiceSettings` is the *Sales
Dialer* settings type (api_meta.txt L128646, "Represents an org's Sales Dialer settings"), and its
`enableVoiceCallRecording` / `enableVoiceCallList` fields each say "To use this feature, enable Dialer
in Lightning Experience" (api_meta.txt L128675–128712). Setting them does nothing for Service Cloud
Voice.

`settings/MyDomain.settings-meta.xml` — the one My Domain field with a documented Service Cloud Voice
interaction:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MyDomainSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <myDomainName>acme</myDomainName>
    <!-- "Service Cloud Voice with Amazon Connect and Service Cloud Voice with Partner Telephony
         from Amazon Connect aren't compatible with this setting. If you use those features, set
         isFirstPartyCookieUseRequired to false." api_meta.txt L122293-122299.
         Note: orgs created in Summer '24 and later default this to TRUE. -->
    <isFirstPartyCookieUseRequired>false</isFirstPartyCookieUseRequired>
</MyDomainSettings>
```

---

## 2. `ConversationVendorInfo` — the vendor link

`ConversationVendorInformation/Service_Cloud_Voice.ConversationVendorInformation-meta.xml`. Shaped
from the guide's own sample (api_meta.txt L39040–39064), retargeted to Amazon Connect.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ConversationVendorInfo xmlns="http://soap.sforce.com/2006/04/metadata"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <!-- "For Service Cloud Voice with Amazon Connect, this field is always set to
         Service Cloud Voice." api_meta.txt L38863-38864 -->
    <masterLabel>Service Cloud Voice</masterLabel>
    <developerName>Service_Cloud_Voice</developerName>
    <!-- Enum: Amazon_Connect | BringYourOwnChannelPartner | BringYourOwnContactCenter
              | ServiceCloudVoicePartner   (api_meta.txt L39028-39034) -->
    <vendorType>Amazon_Connect</vendorType>
    <!-- Amazon-Connect-only fields (api_meta.txt L38684-38706, L38838-38845).
         These are populated by provisioning. Retrieve them; do not invent values. -->
    <awsAccountKey>123456789012</awsAccountKey>
    <awsRootEmail>aws-root+acme@example.com</awsRootEmail>
    <awsTenantVersion>2.0</awsTenantVersion>
    <isTaxCompliant>true</isTaxCompliant>
</ConversationVendorInfo>
```

The `Amazon_Connect` row is deliberately short. Most `ConversationVendorInfo` fields are scoped in the
guide to "Service Cloud Voice with Partner Telephony", "…from Amazon Connect", or "Bring Your Own
Channel for CCaaS" and **not** to plain Amazon Connect — `connectorUrl`, `bridgeComponent`,
`integrationClass`, `clientAuthMode`, `customLoginUrl`, `agentSSOSupported`, `namedCredential`,
`userSyncingSupported`, `queueManagementSupported`, `partnerPhoneNumbersSupported`
(api_meta.txt L38708–39010). For a partner-telephony contact center the same file grows those fields
and the pair must be internally consistent:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ConversationVendorInfo xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Acme Telephony</masterLabel>
    <developerName>Acme_Telephony</developerName>
    <vendorType>ServiceCloudVoicePartner</vendorType>
    <!-- Visualforce page or public URL hosting the connector (api_meta.txt L38759-38766) -->
    <connectorUrl>https://connector.acme.example.com</connectorUrl>
    <!-- Lightning component bridging telephony and other components (api_meta.txt L38724-38731) -->
    <bridgeComponent>acme:acmeTelephonyBridge</bridgeComponent>
    <!-- Apex class implementing the supported service_cloud_voice interfaces (api_meta.txt L38948-38955) -->
    <integrationClass>AcmeTelephonyIntegration</integrationClass>
    <!-- Enum: Custom | Mixed | SSO (api_meta.txt L38739-38755) -->
    <clientAuthMode>SSO</clientAuthMode>
    <!-- agentSSOSupported=true requires namedCredentialSupported=true AND the
         service_cloud_voice.PartnerSSO interface in the integration class
         (api_meta.txt L38660-38672) -->
    <agentSSOSupported>true</agentSSOSupported>
    <namedCredentialSupported>true</namedCredentialSupported>
    <namedCredential>Acme_Telephony_NC</namedCredential>
    <!-- universalCallRecordingAccessSupported=true requires the
         service_cloud_voice.RecordingMediaProvider interface (api_meta.txt L38963-38973) -->
    <universalCallRecordingAccessSupported>true</universalCallRecordingAccessSupported>
    <userSyncingSupported>true</userSyncingSupported>
    <queueManagementSupported>true</queueManagementSupported>
</ConversationVendorInfo>
```

Do not set `integrationClassName` (deprecated in API 53.0 — "Don't set this field. Instead, use
`integrationClass`", api_meta.txt L38957–38961) or `serverAuthMode` (deprecated in API 53.0, "Set this
value to `None`", api_meta.txt L38915–38925).

---

## 3. `CallCenter` — the contact center record

`callCenters/Acme_Support_Voice.callCenter-meta.xml`. The container shape (`sections` → `items` with
`label`/`name`/`value`, plus the four required top-level labels) is exactly the guide's sample
definition at api_meta.txt L31626–31682; the item names below are placeholders — retrieve the real
ones from a provisioned org.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CallCenter xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Required trio (api_meta.txt L31465-31481) -->
    <displayName>Acme Support Voice</displayName>
    <displayNameLabel>Display Name</displayNameLabel>
    <internalNameLabel>Internal Name</internalNameLabel>
    <!-- Optional: "A URL that points to an adapter" (api_meta.txt L31452-31456) -->
    <adapterUrl>https://acme.my.salesforce.com/apex/serviceCloudVoiceAdapter</adapterUrl>
    <sections>
        <label>General Information</label>
        <name>reqGeneralInfo</name>
        <items>
            <label>Description</label>
            <name>reqDescription</name>
            <value>Amazon Connect contact center for Acme support</value>
        </items>
        <items>
            <label>Telephony Provider</label>
            <name>reqVendorInfoApiName</name>
            <!-- Matches ConversationVendorInfo.developerName from section 2 -->
            <value>Service_Cloud_Voice</value>
        </items>
    </sections>
    <sections>
        <label>Dialing Options</label>
        <name>reqDialingOptions</name>
        <items>
            <label>Outside Prefix</label>
            <name>reqOutsidePrefix</name>
            <value>1</value>
        </items>
        <items>
            <label>International Prefix</label>
            <name>reqInternationalPrefix</name>
            <value>01</value>
        </items>
    </sections>
    <!-- Voicemail and callback routing. "Don't change the value in this field. Instead,
         configure voicemail routing in Lightning Experience." api_meta.txt L31603-31619.
         Retrieved values only — shown here so a reviewer recognises the shape. -->
    <contactCenterChannels>
        <channel>Acme_Voicemail_Channel</channel>
        <contactCenter>Acme_Support_Voice</contactCenter>
        <voiceMailHandler>Route_Voicemail_To_Queue</voiceMailHandler>
        <voiceMailFallbackQueue>Support_Queue</voiceMailFallbackQueue>
    </contactCenterChannels>
    <version>4</version>
</CallCenter>
```

`omniCallbackHandler` and `omniCallbackFallbackQueue` are the callback equivalents, added in API 65.0
and carrying the same "Don't change the value in this field" instruction (api_meta.txt L31575–31602).

The matching sObject is queryable but nearly immutable: `CallCenter` supports
`create(), describeSObjects(), getDeleted(), getUpdated(), query(), retrieve()` and **no `update()`
or `delete()`** (object_reference.txt L56385). Changing a live contact center is a metadata
deploy, not a DML update. `Name` and `InternalName` are capped at 80 characters
(object_reference.txt L56429–56448).

---

## 4. `ServiceChannel` — the Omni-Channel handoff, including ACW

`serviceChannels/Voice_Calls.serviceChannel-meta.xml`. This is the object that actually carries After
Conversation Work Time. Fields from api_meta.txt L107776–107905; skeleton from the guide's sample at
api_meta.txt L107911–107928.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ServiceChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Voice Calls</label>
    <!-- Required. Note the element is relatedEntityType (api_meta.txt L107858) -->
    <relatedEntityType>VoiceCall</relatedEntityType>
    <!-- Calls are synchronous: agents should not have to click Accept twice -->
    <hasAutoAcceptEnabled>true</hasAutoAcceptEnabled>
    <doesMinimizeWidgetOnAccept>true</doesMinimizeWidgetOnAccept>
    <!-- ACW. hasAfterConvoWorkTimer=true REQUIRES the max-time field.
         Voice channels: API 52.0+. Range 10-3600 seconds. (api_meta.txt L107784-107792, L107832-107841) -->
    <hasAfterConvoWorkTimer>true</hasAfterConvoWorkTimer>
    <afterConvoMaxTime>120</afterConvoMaxTime>
    <!-- Extension requires hasAfterConvoWorkTimer=true AND both of the next two fields.
         API 56.0+. acwExtensionDuration 10-3600; maxExtensions 1-10.
         (api_meta.txt L107825-107831, L107778-107783, L107852-107856) -->
    <hasAcwExtensionEnabled>true</hasAcwExtensionEnabled>
    <acwExtensionDuration>60</acwExtensionDuration>
    <maxExtensions>2</maxExtensions>
</ServiceChannel>
```

`capacityModel` (`STATUS_BASED` | `TAB_BASED`), `statusField`, and
`serviceChannelStatusFieldMappings` are API 65.0+ additions (api_meta.txt L107797–107810,
L107860–107876). Leave them off a v62 manifest.

Presence status and presence configuration — the two records that decide whether an agent can be
handed a call at all:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- servicePresenceStatuses/Available_for_Voice.servicePresenceStatus-meta.xml
     Skeleton: api_meta.txt L107978-107985 -->
<ServicePresenceStatus xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Available for Voice</label>
    <channels>
        <channel>Voice_Calls</channel>
    </channels>
</ServicePresenceStatus>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- presenceUserConfigs/Voice_Agents.presenceUserConfig-meta.xml
     Fields: api_meta.txt L96980-97060 -->
<PresenceUserConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Voice Agents</label>
    <!-- Required. Max work units an agent can hold at once (api_meta.txt L96998-97001) -->
    <capacity>5</capacity>
    <!-- enableAutoAccept is available only if enableDecline is false, and vice versa
         (api_meta.txt L97004-97012) -->
    <enableAutoAccept>true</enableAutoAccept>
    <enableDecline>false</enableDecline>
    <enableRequestSound>true</enableRequestSound>
    <enableDisconnectSound>true</enableDisconnectSound>
    <assignments>
        <profiles>
            <profile>Support Agent</profile>
        </profiles>
    </assignments>
</PresenceUserConfig>
```

---

## 5. `CallCenterRoutingMap` — mapping Salesforce agents and queues to Amazon Connect

Required when Omni-Channel needs to know an agent's availability in the vendor system for transfers.
The example is the guide's own, at api_meta.txt L31771–31783 — note it is already an Amazon Connect
agent ARN, which is the clearest published evidence that a Service Cloud Voice contact center is a
`CallCenter`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CallCenterRoutingMap xmlns="http://soap.sforce.com/2006/04/metadata">
    <callCenter>Acme_Support_Voice</callCenter>
    <!-- developerName = [SALESFORCE_USER_ID]_[CALL_CENTER] or
         [SALESFORCE_QUEUE_NAME]_[CALL_CENTER] (api_meta.txt L31726-31733) -->
    <developerName>User_005ABC00000FjYIIA0_04vZ6000000Cagl</developerName>
    <!-- Unique identifier for the external system's user or queue (api_meta.txt L31735-31740) -->
    <externalId>arn:aws:connect:us-east-1:123456789012:instance/4b1c9e10-0000-0000-0000-9f2ab7c1d3e4/agent/a69f7afe-5b04-4aa8-b5ee-108a84d0f504</externalId>
    <masterLabel>005ABC00000FjYIIA0</masterLabel>
    <referenceRecord>agent.one@acme.example.com</referenceRecord>
    <!-- Amazon Connect QuickConnectId ARN used to determine agent availability for
         Omni-Channel call transfers. API 56.0+ (api_meta.txt L31757-31761) -->
    <quickConnect>arn:aws:connect:us-east-1:123456789012:instance/4b1c9e10-0000-0000-0000-9f2ab7c1d3e4/transfer-destination/8c3f1a22-1111-2222-3333-5d6e7f809a0b</quickConnect>
</CallCenterRoutingMap>
```

Deploying this type requires "Contact Center Admin, Contact Center Admin (Partner Telephony), Contact
Center Supervisor, or Manage Call Centers permission" (api_meta.txt L31712–31714).

---

## 6. Permission set for contact-center agents

The Object Reference names the standard permission sets that gate voice data. For `VoiceCall`:
"Salesforce Voice Contact Center Rep or Salesforce Voice Contact Center Admin permission sets for
Salesforce Voice, or Agentforce Contact Center Admin (Salesforce Voice) permission set", and "Only
users with the Modify All Data permission can delete call records"
(object_reference.txt L306746–306750). For `CallCenterRoutingMap` records: "Salesforce Voice Contact
Center Admin, Salesforce Voice Contact Center Admin (Partner Telephony), Salesforce Voice Contact
Center Supervisor, or Manage Call Centers permission" (object_reference.txt L56475–56477).

Assign those standard sets first. Author a **custom** permission set only for the org-specific
additions on top:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- permissionsets/Voice_Agent_Add_Ons.permissionset-meta.xml
     Skeleton: api_meta.txt L95211-95260 -->
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Voice Agent Add-Ons</label>
    <description>Supplements the standard Salesforce Voice Contact Center Rep permission set.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <objectPermissions>
        <object>VoiceCall</object>
        <allowRead>true</allowRead>
        <allowCreate>true</allowCreate>
        <allowEdit>true</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>false</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
    <objectPermissions>
        <object>VoiceCallRecording</object>
        <allowRead>true</allowRead>
        <allowCreate>false</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>false</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
    <fieldPermissions>
        <field>VoiceCall.CallDisposition</field>
        <readable>true</readable>
        <editable>false</editable>
    </fieldPermissions>
    <fieldPermissions>
        <field>VoiceCall.CallResolution</field>
        <readable>true</readable>
        <!-- CallResolution is one of the few VoiceCall fields with Update
             (object_reference.txt L306944-306952) -->
        <editable>true</editable>
    </fieldPermissions>
</PermissionSet>
```

Two rules for this file:

1. **Do not guess `<userPermissions><name>` values.** UNVERIFIED (2026-09-05): the Metadata API
   Developer Guide documents only the shape of `PermissionSetUserPermission` — `enabled` and `name`,
   "Required. The name of the permission" (api_meta.txt L95170–95179) — and publishes no catalogue of
   permission API names, so no Voice-specific `name` value can be grounded from these sources. Retrieve
   a permission set that already has the permission and copy the exact string.
2. `PermissionSetServicePresenceStatusAccess` (`servicePresenceStatus` + `enabled`) is the element for
   granting a presence status, and it is API 64.0 and later (api_meta.txt L95181–95189). On a v62
   manifest, grant presence statuses through the Setup UI or a higher API version instead.

---

## 7. package.xml and deploy order

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>ServiceCloudVoice</members>
        <members>MyDomain</members>
        <name>Settings</name>
    </types>
    <types>
        <members>*</members>
        <name>ConversationVendorInfo</name>
    </types>
    <types>
        <members>Acme_Support_Voice</members>
        <name>CallCenter</name>
    </types>
    <types>
        <members>*</members>
        <name>ServiceChannel</name>
    </types>
    <types>
        <members>*</members>
        <name>ServicePresenceStatus</name>
    </types>
    <types>
        <members>*</members>
        <name>PresenceUserConfig</name>
    </types>
    <types>
        <members>*</members>
        <name>CallCenterRoutingMap</name>
    </types>
    <types>
        <members>Voice_Agent_Add_Ons</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

Wildcard support is explicit for `CallCenterRoutingMap`, `ConversationVendorInfo`, `ServiceChannel`,
and `ServicePresenceStatus` (api_meta.txt L31794–31796, L39085–39087, L107939–107941,
L108006–108008). It does **not** apply to feature settings: "The wildcard character `*` … doesn't
apply to metadata types for feature settings. The wildcard applies only when retrieving all settings,
not for an individual setting" (api_meta.txt L128761–128764) — which is why the `Settings` block
above names members explicitly.

Deploy order, and why:

| # | Deploy | Why it must come first |
|---|---|---|
| 1 | `Settings` (`ServiceCloudVoice`, `MyDomain`) | `enableServiceCloudVoice` gates the feature; `isFirstPartyCookieUseRequired` must already be `false` (api_meta.txt L122293–122299) |
| 2 | `ConversationVendorInfo` | `CallCenter` items and `ConversationChannelDefinition` reference it by `developerName` (api_meta.txt L113487–113493) |
| 3 | `CallCenter` | `CallCenterRoutingMap.callCenter` and `VoiceCall.CallCenterId` both point at it (api_meta.txt L31718–31724; object_reference.txt L306795–306809) |
| 4 | `ServiceChannel` | `ServicePresenceStatus.channels.channel` names it (api_meta.txt L107966–107973) |
| 5 | `ServicePresenceStatus`, then `PresenceUserConfig` | `presenceStatusOnDecline` / `presenceStatusOnPushTimeout` reference statuses (api_meta.txt L97056–97062) |
| 6 | `CallCenterRoutingMap` | Needs both the `CallCenter` and the real Salesforce user/queue to exist |
| 7 | `PermissionSet` | Object and field permissions need the objects enabled by step 1 |

```bash
# Retrieve what provisioning already created, so you edit rather than invent
sf project retrieve start \
  --metadata CallCenter ConversationVendorInfo ServiceChannel ServicePresenceStatus \
  --metadata PresenceUserConfig CallCenterRoutingMap \
  --metadata "Settings:ServiceCloudVoice" --metadata "Settings:MyDomain" \
  --target-org myOrg

# Lint the retrieved manifest before you touch it
python3 skills/admin/service-cloud-voice-setup/scripts/check_service_cloud_voice_setup.py \
  --manifest-dir force-app/main/default

# Validate without deploying
sf project deploy validate --manifest manifest/package.xml --target-org myOrg

# Deploy
sf project deploy start --manifest manifest/package.xml --target-org myOrg
```

---

## 8. Verification

**Setup check.** After deploy, confirm the channel and its ACW timer:
Setup → Omni-Channel → Service Channels → *Voice Calls* should show Related Entity Type `VoiceCall`
and an After Conversation Work Time of 120 seconds.

**SOQL — calls by disposition.** `CallDisposition` for Salesforce Voice takes `new`, `in-progress`,
and `completed`; "If After Conversation Work (ACW) is enabled, that work begins after the call
completes" (object_reference.txt L306823–306841).

```sql
SELECT CallDisposition, CallType, COUNT(Id) CallCount,
       AVG(CallDurationInSeconds) AvgSeconds
FROM VoiceCall
WHERE CreatedDate = LAST_N_DAYS:7
GROUP BY CallDisposition, CallType
ORDER BY COUNT(Id) DESC
```

**SOQL — unrouted calls.** A call that was queued but never accepted has `CallQueuedDateTime`
populated and `CallAcceptDateTime` null (object_reference.txt L306833–306841, L306786–306793). Both
are nillable and filterable, so this is a valid predicate:

```sql
SELECT Id, Name, CallType, QueueName, FromPhoneNumber,
       CallQueuedDateTime, CallEndDateTime, DisconnectReason
FROM VoiceCall
WHERE CallQueuedDateTime != NULL
  AND CallAcceptDateTime = NULL
  AND CreatedDate = LAST_N_DAYS:7
ORDER BY CallQueuedDateTime DESC
LIMIT 200
```

**SOQL — calls that never reached the contact center record.** If `CallCenterId` is null on Salesforce
Voice calls, the routing map or the contact center link is wrong. `VendorType` "for Salesforce Voice
… is always set to `ContactCenter`" (object_reference.txt L307500–307509), which makes it a reliable
filter to separate Service Cloud Voice traffic from Sales Dialer traffic in a mixed org:

```sql
SELECT Id, Name, VendorType, CallCenterId, QueueName, UserId, IsRecorded
FROM VoiceCall
WHERE VendorType = 'ContactCenter'
  AND CallCenterId = NULL
  AND CreatedDate = LAST_N_DAYS:30
LIMIT 200
```

**Recording check.** `VoiceCallRecording` is joined by `VoiceCallId` (Required,
object_reference.txt L308445–308460). For Amazon Connect the audio itself is not in Salesforce: "Call
recordings for Salesforce Voice with Amazon Connect … are stored in S3 buckets on your Amazon Web
Services (AWS) account and can be accessed via AWS" (object_reference.txt L308341–308343). A row here
proves metadata linkage, not that the file is retrievable.

```sql
SELECT Id, Name, VoiceCallId, DurationInSeconds, UploadDateTime, IsConsented
FROM VoiceCallRecording
WHERE UploadDateTime = LAST_N_DAYS:1
ORDER BY UploadDateTime DESC
LIMIT 50
```
