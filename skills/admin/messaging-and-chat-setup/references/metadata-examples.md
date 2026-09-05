# Metadata Examples — Messaging and Chat Setup

Deployable shapes for the five metadata types a Messaging for In-App and Web (MIAW) deployment owns: `MessagingChannel`, `EmbeddedServiceConfig`, `BrandingSet`, `CorsWhitelistOrigin`, `CspTrustedSite`. Every element name, enum value and "Required" marking below is from the Metadata API Developer Guide (v62 PDF, `api_meta.pdf`); line numbers cite the extracted text so each claim can be re-checked.

The Omni-Channel side — `ServiceChannel`, `ServicePresenceStatus`, `PresenceUserConfig`, `QueueRoutingConfig`, `Queue` — is **not** repeated here. Deploy it from `admin/omni-channel-routing-setup` first; this package only points at the queue and flow that produced.

## Where the files live and the deploy order

| Order | Type | package.xml `<name>` | File (Metadata API format) | Why this position |
|---|---|---|---|---|
| 1 | Queue + routing config | `Queue`, `QueueRoutingConfig` | see `admin/omni-channel-routing-setup` | `MessagingChannel.sessionHandlerQueue` is **Required** and must resolve (api_meta:87506) |
| 2 | Omni-Channel flow (optional) | `Flow` | `flows/Route_Chat_By_Language.flow` | `sessionHandlerFlow` must resolve (api_meta:87498) |
| 3 | Branding set | `BrandingSet` | `brandingSets/Support_Chat_Brand.brandingSet` | `EmbeddedServiceConfig.branding` names it (api_meta:56836) |
| 4 | Experience site / website | `Network`, `ExperienceBundle` | see `admin/experience-cloud-site-setup` | `EmbeddedServiceConfig.site` is **Required** (api_meta:56912) |
| 5 | Messaging channel | `MessagingChannel` | `messagingChannels/Support_Portal_Chat.messagingChannel` | `embeddedServiceMessagingChannel/messagingChannel` is **Required** and points here (api_meta:57173) |
| 6 | Embedded Service deployment | `EmbeddedServiceConfig` | `EmbeddedServiceConfig/Support_Portal_Web.EmbeddedServiceConfig` | Binds channel + site + branding + pre-chat form |
| 7 | CORS origin | `CorsWhitelistOrigin` | `corswhitelistorigins/Support_Portal.corswhitelistorigin` | Browser-side; no dependency on the above |
| 8 | CSP trusted site | `CspTrustedSite` | `cspTrustedSites/Support_Portal.cspTrustedSite` | Browser-side; no dependency on the above |

Folders and suffixes come from each type's "File Suffix and Directory Location" section: `messagingChannel` / `messagingChannels` (api_meta:87385), `.EmbeddedServiceConfig` / `EmbeddedServiceConfig` (api_meta:56807), `brandingSet` / `brandingSets` (api_meta:30579), `.corswhitelistorigin` / `corswhitelistorigins` (api_meta:39351), `.cspTrustedSite` / `cspTrustedSites` (api_meta:39432). In `sf` source format each file gains a `-meta.xml` tail; retrieve once into an empty project and copy the paths the CLI writes rather than guessing the source-format casing.

## 1. Messaging channel — enhanced web chat, flow routing with a fallback queue

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MessagingChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Support Portal Chat</masterLabel>
    <description>Enhanced web chat for support.example.com</description>
    <messagingChannelType>EmbeddedMessaging</messagingChannelType>

    <sessionHandlerType>Flow</sessionHandlerType>
    <sessionHandlerFlow>Route_Chat_By_Language</sessionHandlerFlow>
    <sessionHandlerQueue>Support_Fallback</sessionHandlerQueue>

    <embeddedConfig>
        <authMode>UnAuth</authMode>
        <anonymousUserJwtExpirationTime>1440</anonymousUserJwtExpirationTime>
        <isAttachmentUploadEnabled>true</isAttachmentUploadEnabled>
        <isSaveTranscriptEnabled>false</isSaveTranscriptEnabled>
        <isEstimatedWaitTimeEnabled>true</isEstimatedWaitTimeEnabled>
    </embeddedConfig>

    <automatedResponses>
        <autoResponseContentType>TextResponse</autoResponseContentType>
        <language>en_US</language>
        <response>Thanks for reaching out. An agent will be with you shortly.</response>
        <type>InitialResponse</type>
    </automatedResponses>
    <automatedResponses>
        <autoResponseContentType>TextResponse</autoResponseContentType>
        <language>en_US</language>
        <response>Are you still there? This chat closes if we do not hear from you.</response>
        <type>EndUserInactiveResponse</type>
        <responseTimeoutInMins>10</responseTimeoutInMins>
    </automatedResponses>
    <automatedResponses>
        <autoResponseContentType>TextResponse</autoResponseContentType>
        <language>en_US</language>
        <response>Thanks for chatting with us today.</response>
        <type>AgentEndEngagementResponse</type>
    </automatedResponses>

    <standardParameters>
        <parameterType>Email</parameterType>
        <actionParameterMappings>
            <actionParameterName>Route_Chat_By_Language</actionParameterName>
        </actionParameterMappings>
    </standardParameters>
    <standardParameters>
        <parameterType>Subject</parameterType>
        <actionParameterMappings>
            <actionParameterName>Route_Chat_By_Language</actionParameterName>
        </actionParameterMappings>
    </standardParameters>

    <customParameters>
        <name>PreferredLanguage</name>
        <masterLabel>Preferred Language</masterLabel>
        <externalParameterName>preferredLanguage</externalParameterName>
        <parameterDataType>Picklist</parameterDataType>
        <maxLength>10</maxLength>
        <actionParameterMappings>
            <actionParameterName>Route_Chat_By_Language</actionParameterName>
        </actionParameterMappings>
    </customParameters>
</MessagingChannel>
```

How to read it:

- Four fields are marked **Required**: `masterLabel` (api_meta:87450), `messagingChannelType` (api_meta:87452), `sessionHandlerQueue` (api_meta:87506) and `sessionHandlerType` (api_meta:87513). A deploy missing any of them fails on the field, not on the widget.
- `messagingChannelType` values: `AppleMessagesForBusiness`, `Custom` (Bring Your Own Channel, 61.0+), `EmbeddedMessaging`, `Facebook`, `Line`, `PstnVoice`, `Text`, `SipVoice`, `Voice`, `WhatsApp`, `WhatsAppVoice` (api_meta:87456–87469). `EmbeddedMessaging` is captioned "Enhanced Chat" (api_meta:87460) — that is the MIAW value. The same field description then says third-party channels such as WhatsApp and Facebook Messenger "don't use this metadata type" (api_meta:87470); see gotchas #6.
- `sessionHandlerType` is `AgentforceServiceAgent`, `Flow`, `Queue` or `User` (api_meta:87513–87518). `User` pairs with `sessionHandlerUser` (62.0+) to route to a named person instead of a pool.
- `sessionHandlerQueue` does two jobs: it is the routing target when `sessionHandlerType` is `Queue`, and it is "the fallback queue used if a message can't be routed using the selected flow" when `sessionHandlerFlow` is set (api_meta:87506–87508). There is no separate fallback field to forget.
- Inside `embeddedConfig`, `authMode` is **Required** — `Auth` or `UnAuth` (api_meta:87556–87559). `isEstimatedWaitTimeEnabled` (api_meta:87547), `isAttachmentUploadEnabled` (api_meta:87582) and `isSaveTranscriptEnabled` (api_meta:87588) all default to `false`; omit them and the customer gets no wait time, no file upload and no transcript download.
- `automatedResponses/type` is **Required** (api_meta:87706). `AgentEndEngagementResponse`, `AgentEngagedResponse` and `InitialResponse` are long-standing; `CustomResponse`, `DoubleOptInPrompt`, `EndUserIdleResponse`, `EndUserInactiveResponse`, `HelpResponse`, `OptInConfirmation`, `OptInPrompt`, `OptOutConfirmation` are 65.0+ (api_meta:87707–87719).
- `responseTimeoutInMins` accepts 5 to 60 (api_meta:87700–87701).
- `autoResponseContentType` is `TextResponse` (supply `response` and `language`) or `MessageDefinition` (supply `messageDefinitionName`, a messaging component) (api_meta:87668–87672).
- `standardParameters/parameterType` is **Required** and limited to `Email`, `FirstName`, `LastName`, `Subject` (api_meta:87824–87829). Everything else the pre-chat form collects has to be a `customParameters` entry.
- `customParameters` requires `name`, `masterLabel`, `externalParameterName` and `parameterDataType`; `parameterDataType` draws from the Flow data types `Apex`, `Boolean`, `Currency`, `Date`, `DateTime`, `Multipicklist`, `Number`, `Picklist`, `SObject`, `String`, `Time` (api_meta:87761–87775).
- `actionParameterName` is documented as "the name of the flow that the custom or standard parameters are mapped to" (api_meta:87792) — the flow API name, not a flow variable name.
- The guide's own two sample channels are at api_meta:87908 (a channel with auto-responses and opt-in/opt-out keywords) and api_meta:88021 (the minimal queue-routed channel). The first is introduced as "routes to a flow with a fallback queue" but its body sets `sessionHandlerType` to `Queue` with no `sessionHandlerFlow` — the prose and the XML disagree, so copy the field semantics from the field table above, not from that sample's routing lines.

## 2. Embedded Service deployment — web, referencing the site, channel and branding

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EmbeddedServiceConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Support Portal Web</masterLabel>
    <site>Support_Portal</site>
    <deploymentType>Web</deploymentType>
    <deploymentFeature>EmbeddedMessaging</deploymentFeature>
    <branding>Support_Chat_Brand</branding>
    <areGuestUsersAllowed>true</areGuestUsersAllowed>
    <shouldHideAuthDialog>false</shouldHideAuthDialog>
    <isTermsAndConditionsEnabled>true</isTermsAndConditionsEnabled>
    <isTermsAndConditionsRequired>true</isTermsAndConditionsRequired>

    <embeddedServiceMessagingChannel>
        <isEnabled>true</isEnabled>
        <messagingChannel>Support_Portal_Chat</messagingChannel>
        <businessHours>Support_Hours_PT</businessHours>
        <shouldShowTypingIndicators>true</shouldShowTypingIndicators>
        <shouldShowReadReceipts>true</shouldShowReadReceipts>
        <shouldShowDeliveryReceipts>true</shouldShowDeliveryReceipts>
        <shouldShowEmojiSelection>true</shouldShowEmojiSelection>
        <shouldStartNewLineOnEnter>false</shouldStartNewLineOnEnter>
    </embeddedServiceMessagingChannel>

    <embeddedServiceForms>
        <isActive>true</isActive>
        <displayContext>Session</displayContext>
        <embeddedServiceFormFields>
            <displayOrder>0</displayOrder>
            <formField>_FirstName</formField>
            <messagingChannelParameterType>Standard</messagingChannelParameterType>
            <formFieldType>Text</formFieldType>
            <isHidden>false</isHidden>
            <isRequired>true</isRequired>
        </embeddedServiceFormFields>
        <embeddedServiceFormFields>
            <displayOrder>1</displayOrder>
            <formField>_Email</formField>
            <messagingChannelParameterType>Standard</messagingChannelParameterType>
            <formFieldType>Email</formFieldType>
            <isHidden>false</isHidden>
            <isRequired>true</isRequired>
        </embeddedServiceFormFields>
        <embeddedServiceFormFields>
            <displayOrder>2</displayOrder>
            <formField>PreferredLanguage</formField>
            <messagingChannelParameterType>Custom</messagingChannelParameterType>
            <formFieldType>ChoiceList</formFieldType>
            <isHidden>false</isHidden>
            <isRequired>true</isRequired>
            <choiceList>Language</choiceList>
        </embeddedServiceFormFields>
    </embeddedServiceForms>
</EmbeddedServiceConfig>
```

How to read it:

- `masterLabel` (api_meta:56904) and `site` (api_meta:56912) are the two **Required** top-level fields. `site` is "the name of the Experience site or website connected to this Embedded Service deployment" — a MIAW deployment cannot exist without one, which is why `admin/experience-cloud-site-setup` runs before this file.
- `deploymentFeature` values are `EmbeddedMessaging`, `Flows`, `FieldService`, `LiveAgent`, `None` (api_meta:56842–56849). `EmbeddedMessaging` is MIAW; `LiveAgent` is the legacy chat value.
- `deploymentType` values are `Mobile` ("For future use"), `Web` and `API` (api_meta:56852–56857). The guide's own sample uses `Mobile` (api_meta:57291) — use `Web` for a website.
- `branding` (52.0+) names a `BrandingSet` (api_meta:56836), not an `EmbeddedServiceBranding`. See §3.
- `isTermsAndConditionsEnabled` and `isTermsAndConditionsRequired` (59.0+) are supported only when `deploymentFeature` is `EmbeddedMessaging` or `LiveAgent`, and both default to `false` (api_meta:56884–56903).
- `embeddedServiceMessagingChannel` is a 62.0+ subtype (api_meta:57152). Inside it, `isEnabled`, `messagingChannel`, `shouldShowDeliveryReceipts`, `shouldShowEmojiSelection`, `shouldShowReadReceipts`, `shouldShowTypingIndicators` and `shouldStartNewLineOnEnter` are **all marked Required** (api_meta:57170–57191) — this block is all-or-nothing, so a partial edit fails the deploy. `businessHours` on the same block associates a Business Hours record with this specific deployment (api_meta:57166); design it with `admin/business-hours-and-holidays`.
- `embeddedServiceForms` is `EmbeddedServiceForm` (62.0+, api_meta:57056): `displayContext` is **Required** and is `Session` (form shown every session), `Conversation` (every conversation) or `None` — the guide explicitly says of `None`, "Don't select this option" (api_meta:57061–57066). `isActive` defaults to `false` (api_meta:57068), so a pre-chat form deployed without it collects nothing.
- `EmbeddedServiceFormField` (62.0+, api_meta:57073) requires `formField`, `messagingChannelParameterType` and `formFieldType`. `messagingChannelParameterType` is `Standard` or `Custom` and must match what `formField` points at; the standard parameter names are `FirstName`, `LastName`, `Email`, `Subject` (api_meta:57081–57100), while the guide's sample writes them underscore-prefixed as `_FirstName` and `_LastName` (api_meta:57312, 57335). Retrieve a hand-built form before choosing between the two spellings.
- `formFieldType` is `Text`, `Email`, `Phone`, `Number`, `Checkbox`, `Choicelist` in the field table (api_meta:57110–57118) and `ChoiceList` in the sample (api_meta:57352). Copy the casing your org's retrieve emits.
- Two shape rules that are easy to violate: when `isHidden` is `true`, `displayOrder` must be `-1` and `isRequired` must be `false`; and `isHidden` can only be `true` for a `Custom` parameter (api_meta:57120–57138). `choiceList` likewise attaches only to a `Custom` parameter (api_meta:57140–57146).

## 3. Branding set — MIAW branding does not use EmbeddedServiceBranding

```xml
<?xml version="1.0" encoding="UTF-8"?>
<BrandingSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Support Chat Brand</masterLabel>
    <description>Colours for the support.example.com chat window</description>
    <brandingSetProperty>
        <propertyName>ACCENT_COLOR_1</propertyName>
        <propertyValue>#0B5CAB</propertyValue>
    </brandingSetProperty>
</BrandingSet>
```

- `masterLabel` is the only **Required** field (api_meta:30598); `brandingSetProperty` repeats a `propertyName` (required, api_meta:30608) / `propertyValue` pair.
- `EmbeddedServiceBranding` — the type carrying `primaryColor`, `navBarColor`, `font`, `height`, `width` — "works only with the legacy chat products. For Messaging for In-app and Web, use the BrandingSet object" (api_meta:56699). Deploying it against a MIAW deployment is the most common wasted change in this domain.
- Branding property names are case-sensitive and all capitals (api_meta:30620). **UNVERIFIED (2026-09-05): the specific BrandingSet property names the MIAW chat window reads are not enumerated in api_meta.pdf — the documented property list is scoped to Lightning Experience themes and Experience Builder. Retrieve a branding set edited in Setup and copy the property names it emits rather than inventing them.**

## 4. CORS origin and CSP trusted site — one pair per host

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CorsWhitelistOrigin xmlns="http://soap.sforce.com/2006/04/metadata">
    <developerName>Support_Portal</developerName>
    <urlPattern>https://*.example.com</urlPattern>
</CorsWhitelistOrigin>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CspTrustedSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Hosts the embedded messaging widget</description>
    <endpointUrl>https://support.example.com</endpointUrl>
    <context>All</context>
    <isActive>true</isActive>
    <isApplicableToConnectSrc>true</isApplicableToConnectSrc>
    <isApplicableToFrameSrc>true</isApplicableToFrameSrc>
    <isApplicableToImgSrc>true</isApplicableToImgSrc>
    <isApplicableToStyleSrc>true</isApplicableToStyleSrc>
    <isApplicableToFontSrc>true</isApplicableToFontSrc>
    <isApplicableToMediaSrc>false</isApplicableToMediaSrc>
    <canAccessCamera>false</canAccessCamera>
    <canAccessMicrophone>false</canAccessMicrophone>
</CspTrustedSite>
```

How to read it:

- `CorsWhitelistOrigin.urlPattern` "must include the HTTPS protocol and a domain name, and can include a port. The wildcard character (*) is supported and must be in front of a second-level domain name. For example, `https://*.example.com` adds all subdomains of example.com to the allowlist" (api_meta:39362–39368). So CORS *does* take wildcards — but only in that position; `https://support.*.com` is invalid.
- An IP address and a domain that resolve to the same address are different origins and need separate entries (api_meta:39374–39378).
- A request from an origin that is not allowlisted gets HTTP **404** (api_meta:39413), not a CORS-labelled status. DevTools shows a 404 against the org endpoint, which is why this is routinely misdiagnosed as a wrong URL.
- `CspTrustedSite.endpointUrl` (api_meta:39501) and `isActive` (api_meta:39523, default `true`) are **Required**. `endpointUrl` must be well-formed: `malformed^url.example.com` and `https://{subdomain}.example.com` fail the syntax check, and malformed entries saved before February 2025 are silently excluded from the generated CSP header (api_meta:39511–39520).
- Every `isApplicableTo*Src` field defaults to `false`, and from API version 59.0 "for each trusted URL, at least one CSPTrustedSite starting with isApplicable or canAccess must be set to true" (api_meta:39562–39564, restated at api_meta:39608). A trusted site deployed with no directives is a no-op that still appears in Setup.
- `context` is `All`, `Communities` (Experience Builder sites only), `FieldServiceMobileExtension`, `LEX`, `LightningOut` (reserved) or `VisualForce` (api_meta:39470–39492). A widget on an Experience Cloud site needs `Communities` or `All`.
- Keep the generated CSP header under 12 KB; customers report issues approaching 16 KB (api_meta:39443). That, not admin patience, is the real ceiling on "one trusted site per staging subdomain".

## 5. Omni-Channel handoff (pointer, not a copy)

`MessagingChannel` names a queue and optionally a flow; everything about how that queue picks an agent lives next door. Deploy from `admin/omni-channel-routing-setup` and read that package for:

- `ServiceChannel` for messaging work, including `capacityModel` — `STATUS_BASED` (capacity held until the work is completed or reassigned) or `TAB_BASED` (released when the console tab closes), API 65.0+ (api_meta:107793–107802).
- `PresenceUserConfig` capacity, `ServicePresenceStatus`, `QueueRoutingConfig`.
- The org-level gates `OmniChannelSettings.enableOmniChannel` (api_meta:123158) and `enableOmniStatusCapModel` (api_meta:123168), deployed as `<members>OmniChannel</members><name>Settings</name>` (api_meta:123180–123190).

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types><members>*</members><name>MessagingChannel</name></types>
    <types><members>Support_Portal_Web</members><name>EmbeddedServiceConfig</name></types>
    <types><members>Support_Chat_Brand</members><name>BrandingSet</name></types>
    <types><members>*</members><name>CorsWhitelistOrigin</name></types>
    <types><members>*</members><name>CspTrustedSite</name></types>
    <version>62.0</version>
</Package>
```

`MessagingChannel` (api_meta:88041), `CorsWhitelistOrigin` (api_meta:39417) and `CspTrustedSite` (api_meta:39617) support the `*` wildcard. **`EmbeddedServiceConfig` does not** — "This metadata type doesn't support the wildcard character * (asterisk) in the package.xml manifest file" (api_meta:57363) — so every deployment must be named explicitly. `EmbeddedServiceBranding` is likewise wildcard-free (api_meta:56790).

## Retrieve and deploy

```bash
# Retrieve what the org already has, so you edit real shapes rather than guessed ones
sf project retrieve start --manifest manifest/package.xml --target-org SANDBOX

# Validate before deploying (nothing is committed to the org)
sf project deploy validate --manifest manifest/package.xml --target-org SANDBOX

# Deploy
sf project deploy start --manifest manifest/package.xml --target-org SANDBOX

# Local gate on the retrieved tree
python3 scripts/check_messaging_and_chat_setup.py --manifest-dir force-app/main/default
```

## Verify after deploy

Setup checks:

- Setup > Messaging > Messaging Channels lists the channel with the routing target you deployed. The type requires the "Configure Messaging" and "View Setup and Configuration" permissions to be enabled for Messaging in the org (api_meta:87393) — a deploy that fails on access, not shape, points here.
- Setup > Embedded Service Deployments shows the deployment bound to that channel and to the site named in `site`.
- Setup > CORS and Setup > Trusted URLs each list the widget host, and the CSP entry shows at least one directive ticked.

SOQL, run after a test conversation:

```sql
-- Did the session land on the enhanced channel, and did it route?
SELECT Id, Name, Status, Origin, ChannelType, ChannelName, AgentType,
       OwnerId, StartTime, AcceptTime, EndTime, EndedByType,
       AgentMessageCount, EndUserMessageCount, EndUserContactId
FROM MessagingSession
ORDER BY StartTime DESC
LIMIT 20

-- Is the conversation attached to a person, or anonymous?
SELECT Id, MessageType, ContactId, AccountId, LeadId, IsFullyOptedIn, Language
FROM MessagingEndUser
WHERE MessageType = 'EmbeddedMessaging'
ORDER BY CreatedDate DESC
LIMIT 20

-- Where are sessions ending up over a week?
SELECT COUNT(Id), Status
FROM MessagingSession
WHERE StartTime = LAST_N_DAYS:7
GROUP BY Status
```

Field grounding (Object Reference, `object_reference.pdf`): `MessagingSession.Status` is a restricted picklist of `New` (standard channels only), `Active`, `Consent` (enhanced only), `Waiting`, `Paused` (enhanced only), `Inactive` (enhanced only), `Ended`, `Error` (enhanced only) (object_reference:182297–182320). `ChannelType` includes `EmbeddedMessaging` from API 55.0 (object_reference:182033–182055). `AgentType` is `Agent`, `Bot`, `BotToAgent`, `System` (object_reference:181978–181995). `Origin` includes `AgentInitiated`, `ConversationClose`, `ConversationControlLost`, `Help`, `InboundInitiated`, `OptIn`, `OptOut`, `TriggeredOutbound` (object_reference:182234–182250). `MessagingEndUser.MessageType` uses `EmbeddedMessaging` for MIAW (object_reference:181746).

A healthy first test produces one `MessagingSession` with `ChannelType = 'EmbeddedMessaging'` moving `Waiting → Active → Ended`, and one `MessagingEndUser` with `MessageType = 'EmbeddedMessaging'`. A session parked at `Waiting` with a null `OwnerId` is a routing problem, not a widget problem — go to `admin/omni-channel-routing-setup`. A session at `Error` is an enhanced-channel-only status and belongs with the channel or flow, not the queue.

## The snippet the website needs

The Embedded Service Deployment page in Setup generates the JavaScript the host page loads. **UNVERIFIED (2026-09-05): the exact bootstrap snippet, its script URL and its initialisation function are not documented in api_meta.pdf, object_reference.pdf or the Apex guides consulted for this skill; copy it from the deployment record in Setup rather than from any reconstruction.** What *is* grounded is the constraint it runs under: the host origin must be a `CorsWhitelistOrigin` (otherwise the org answers 404, api_meta:39413) and a `CspTrustedSite` with at least one directive true (api_meta:39562).
