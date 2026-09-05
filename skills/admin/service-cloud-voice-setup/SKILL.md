---
name: service-cloud-voice-setup
description: "Use this skill when setting up Service Cloud Voice with Amazon Connect — provisioning the contact center, configuring phone numbers, enabling real-time transcription, and configuring After Conversation Work Time. Covers the deployable metadata behind it: CallCenter, ConversationVendorInfo (vendorType), CallCenterRoutingMap, the Voice ServiceChannel that carries ACW, ServicePresenceStatus, PresenceUserConfig, ServiceCloudVoice.settings, and the VoiceCall / VoiceCallRecording objects. Trigger keywords: Service Cloud Voice, Amazon Connect, contact center, softphone, call transcription, After Conversation Work, ACW, wrap-up time, VoiceCall, CallCenter metadata, vendorType, telephony provider. NOT for Omni-Channel routing setup — use admin/omni-channel-routing-setup. NOT for Open CTI softphone adapters — use apex/cti-adapter-development. NOT for Sales Dialer (Voice.settings) — that is a different product."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I set up Service Cloud Voice with Amazon Connect in my Salesforce org?"
  - "Agents can't receive calls in Omni-Channel — we just got the Voice add-on license"
  - "I need to enable real-time call transcription so supervisors can see live agent conversations"
  - "How do I configure After Conversation Work Time so agents have wrap-up time after calls?"
  - "The Service Cloud Voice provisioning wizard is failing during Amazon Connect setup"
  - "deploy a Service Cloud Voice contact center from sandbox to production"
  - "hasAfterConvoWorkTimer deploy fails on the voice service channel"
  - "agents are online in Omni-Channel but never get routed a voice call"
  - "vendorType is not a valid value deploying ConversationVendorInfo"
  - "softphone widget will not load after we enabled first-party cookies"
  - "where are Amazon Connect call recordings stored for Service Cloud Voice"
  - "turn on call recording for voice but nothing changed for agents"
  - "voice calls not routing to agents through omni-channel"
tags:
  - service-cloud-voice
  - amazon-connect
  - omni-channel
  - telephony
  - call-transcription
  - after-conversation-work
  - contact-center
inputs:
  - "Salesforce org with Service Cloud Voice add-on license assigned"
  - "Contact Center permission set assignments for admins and agents"
  - "Custom domain configured in the org (My Domain)"
  - "Omni-Channel enabled in the org"
  - "AWS account credentials if bringing an existing Amazon Connect instance (optional)"
outputs:
  - "Provisioned Amazon Connect contact center instance linked to Salesforce"
  - "Voice service channel in Omni-Channel routing configuration"
  - "Phone number(s) claimed and assigned to contact flows"
  - "Real-time transcription enabled (if required)"
  - "After Conversation Work Time presence status configured"
  - "Agents able to handle voice calls from the Service Console"
  - "Deployable manifest: CallCenter, ConversationVendorInfo, Voice ServiceChannel with ACW, ServicePresenceStatus, PresenceUserConfig, ServiceCloudVoice.settings"
  - "Verification SOQL over VoiceCall separating unrouted, unlinked, and unqueued calls"
dependencies:
  - admin/omni-channel-routing-setup
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Service Cloud Voice Setup

This skill covers the end-to-end admin setup of Service Cloud Voice using the Salesforce-guided wizard that provisions an Amazon Connect instance, configures Omni-Channel routing for voice, enables real-time transcription, and sets up After Conversation Work Time (ACW). Activate this skill when a team needs to go from a licensed org to agents handling calls in the Service Console.

---

## Before Starting

Gather this context before working on anything in this domain:

- Verify the org has the **Service Cloud Voice with Amazon Connect** add-on license. UNVERIFIED (2026-09-05): the exact licence names and the rule that the wizard is hidden without one come from help.salesforce.com, which cannot be fetched here. What *is* grounded is that the metadata behind a contact center is licence-gated: `ConversationVendorInfo` "requires an add-on license for Service Cloud Voice for Partner Telephony or Digital Engagement" (api_meta.txt L38646), and the adjacent `ConvIntelligenceSignalRule` names "Service Cloud Voice for Amazon Connect, Service Cloud Voice for Partner Telephony with Amazon Connect, Service Cloud Voice for Partner Telephony, or Digital Engagement" (api_meta.txt L39110-39112). Partners and ISVs provisioning on behalf of customers must confirm the license is active on the production org, not just a sandbox.
- Confirm **My Domain** (custom domain) is deployed to all users. The Amazon Connect softphone widget is loaded via a Lightning page that requires a custom domain. Without it, OAuth callbacks from Amazon Connect will fail.
- Confirm **Omni-Channel** is enabled under Setup > Omni-Channel Settings. This one is documented: `ServiceChannel`, `ServicePresenceStatus`, and `PresenceUserConfig` each carry the special access rule "This type is available only if Omni-Channel is enabled in your org" (api_meta.txt L107773, L107963, L96978), so without it none of the routing metadata can even be deployed.
- The most common wrong assumption: practitioners assume Amazon Connect can be configured from the AWS console independently and then "connected" to Salesforce as a second step. The correct path is the Salesforce-guided wizard, which provisions the AWS-side infrastructure on the admin's behalf and handles OAuth integration. Manual AWS-first setup bypasses the required trust configuration.
- Check `MyDomainSettings.isFirstPartyCookieUseRequired` **before** provisioning, not after the first failed call. It must be `false` for both Amazon Connect models (api_meta.txt L122293-122299), and orgs created in Summer '26 and later default it to `true`. See `references/gotchas.md` Gotcha 6.
- Know which product you are configuring. `ServiceCloudVoice.settings` is Service Cloud Voice; `Voice.settings` is Sales Dialer (api_meta.txt L128646-128647). Both write `VoiceCall` rows, so reports do not distinguish them — `VoiceCall.VendorType` does, and "for Salesforce Voice, this field is always set to `ContactCenter`" (object_reference.txt L307500-307509).
- Key limits: one Amazon Connect instance per Salesforce production org; sandbox environments require a separate Amazon Connect instance; concurrent call capacity is governed by your Amazon Connect service limits in AWS, not Salesforce. UNVERIFIED (2026-09-05): none of these three is stated in the Metadata API Developer Guide, the Object Reference, or the Salesforce App Limits cheat sheet (which contains no voice or contact-center entry at all). They are field practice from help.salesforce.com and AWS documentation. The documented Salesforce-side cap is 300 custom fields on `VoiceCall` (object_reference.txt L306739).

---

## Questions to Ask Before Configuring

Ask these before the wizard, not after the first test call. Each one maps to a failure in
`references/gotchas.md`; skipping them produces a contact center that provisions cleanly and routes
nothing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is this Amazon Connect, Partner Telephony, or Bring Your Own Channel for CCaaS?" | It fixes `ConversationVendorInfo.vendorType`, and the guide scopes almost every other field on that type to one model or the other (api_meta.txt L38708-39034) | The one legal `vendorType` value, and which of `connectorUrl` / `integrationClass` / `agentSSOSupported` are even in scope |
| "How many seconds of wrap-up, and may an agent extend it?" | ACW is a required field group on the Voice `ServiceChannel`, not a toggle — and every value is bounded — 10–3600 seconds, and 1–10 extensions | A deployable `hasAfterConvoWorkTimer` / `afterConvoMaxTime` pair, and whether the three extension fields are needed at all |
| "Do wrap-up times differ per team, or is one number right for everyone?" | Channel-level ACW is one setting for the org; per-user ACW on `PresenceUserConfig` is API 65.0+ and multiplies the records a release must keep consistent | A decision between one `ServiceChannel` field pair and N presence configurations, and the manifest's API version floor |
| "When was this org created, and has anyone hardened cookies?" | `isFirstPartyCookieUseRequired` defaults to `true` in newer orgs and is documented as incompatible with Amazon Connect | A `MyDomain.settings` change deployed *ahead* of the contact center, instead of a silent softphone failure |
| "Who owns the S3 bucket the call recordings land in, and what is its lifecycle policy?" | For Amazon Connect the audio is not in Salesforce at all (object_reference.txt L308341-308343) — a `VoiceCallRecording` row proves linkage, not retrievability | A named AWS owner and a retention policy inside the same change record as the Salesforce config |
| "Which presence statuses will agents actually pick, and does each one name the Voice channel?" | A status with no `channels` is silently converted to an Away status (api_meta.txt L107966-107970) | A status list where every routable status is verifiably routable, before agents are told to go live |
| "Are transcripts or Einstein features in scope, and who signed off on recording consent?" | Transcription depends on AWS-side configuration Salesforce does not validate, and `VoiceCallRecording.IsConsented` exists because consent is a per-recording fact | An explicit AWS prerequisite step in the runbook, and a consent position rather than a default |

What a proper configuration adds over just running the wizard: the routing path is deployable and
reviewable as source rather than clicked into one org, ACW and presence settings are internally
consistent so the deploy cannot half-succeed, and the AWS-side dependencies (cookies, recording
storage, media streaming) have named owners instead of being discovered during an incident.

---

## Core Concepts

### What a Contact Center Is, in Metadata

The wizard is a UI over ordinary deployable metadata. Knowing the shape is what lets you review a
setup, diff two orgs, or move one forward through environments.

| Component | Type | Its job | Guide line |
|---|---|---|---|
| The contact center record | `CallCenter` | The container. "Represents the Call Center definition used to integrate Salesforce with a third-party computer-telephony integration (CTI) system, a partner telephony system, or partner Contact Center as a Service (CCaaS) system." | api_meta.txt L31421-31424 |
| The vendor link | `ConversationVendorInfo` | Which telephony system, and what it supports. `vendorType` is the fork: `Amazon_Connect`, `BringYourOwnChannelPartner`, `BringYourOwnContactCenter`, `ServiceCloudVoicePartner` | api_meta.txt L39028-39034 |
| Agent/queue mapping | `CallCenterRoutingMap` | Maps a Salesforce user or queue to the vendor's user or queue; holds the Amazon Connect `quickConnect` ARN used for transfer availability | api_meta.txt L31685-31779 |
| The routing channel | `ServiceChannel` (`relatedEntityType` = `VoiceCall`) | Where Omni-Channel queues the call, and where After Conversation Work Time actually lives | api_meta.txt L107858, L107784-107841 |
| Agent eligibility | `ServicePresenceStatus` + `PresenceUserConfig` | Whether an online agent is routable, and how much they can hold | api_meta.txt L107966-107973, L96998-97001 |
| The feature switch | `ServiceCloudVoiceSettings` | `enableServiceCloudVoice` for Amazon Connect; `enableSCVExternalTelephony` for Partner Telephony | api_meta.txt L126885-126900 |
| The call record | `VoiceCall` (+ `VoiceCallRecording`) | Per-call metadata; `VendorType` is always `ContactCenter` for Salesforce Voice | object_reference.txt L306734, L307500-307509 |

`references/metadata-examples.md` carries deployable XML for each of these, a package.xml, the deploy
order, and the verification SOQL.

Note what this table refutes: Service Cloud Voice contact centers **are** `CallCenter` records. The
guide's own `CallCenterRoutingMap` sample carries an `arn:aws:connect:` agent ARN
(api_meta.txt L31774-31776), and `VoiceCall.CallCenterId` is a lookup to `CallCenter`
(object_reference.txt L306795-306809). What does *not* apply from the Open CTI era is the legacy
adapter workflow — the AppExchange package, the locally hosted adapter URL, and manual user
assignment to a call center; see `references/llm-anti-patterns.md` Anti-Pattern 5, which is correct
about the workflow and imprecise about the metadata type.

### The Guided Provisioning Wizard

Service Cloud Voice setup begins at **Setup > Service Cloud Voice > Contact Centers**. The wizard walks through four phases: (1) Contact Center naming and region selection, (2) Amazon Connect instance provisioning (or import of an existing instance), (3) phone number claiming, and (4) Omni-Channel service channel creation. Behind the scenes, Salesforce uses an OAuth 2.0 integration between your org and AWS to create IAM roles, configure the Amazon Connect instance, and install the required Amazon Connect contact flows. Admins do not need to log in to the AWS console for a greenfield provisioning. The wizard handles all trust and permission scaffolding.

If an existing Amazon Connect instance needs to be imported rather than created fresh, the admin must provide the instance ARN and have sufficient AWS IAM permissions to grant Salesforce access. The import path is more fragile — existing contact flows must be manually mapped to Salesforce's expected flow entry points.

UNVERIFIED (2026-09-05): the wizard's four phases, its AWS IAM and contact-flow behaviour, and the claim that no AWS console access is needed for greenfield provisioning are documented on help.salesforce.com and cannot be fetched here. The grounded trace of the same activity is in `ConversationVendorInfo`: `awsAccountKey` is "The 12-digit AWS subaccount ID that's automatically provisioned for you when Service Cloud Voice was turned on", `awsRootEmail` is "The email address used by Salesforce to create the root user for the provisioned AWS subaccount", and `awsTenantVersion` is "The version number of the SVCTenantStack AWS CloudFormation stack that's deployed… in AWS region 'us-east-1'" (api_meta.txt L38684-38706). Those three fields are the evidence that Salesforce provisions AWS infrastructure on the admin's behalf; the step-by-step screens are not.

### Phone Numbers and Contact Flows

During wizard completion, the admin claims one or more phone numbers from Amazon Connect's number inventory. Numbers can be Direct Inward Dial (DID) from available country pools. Each number is associated with a **contact flow** — a routing program in Amazon Connect that determines how an inbound call is handled before it reaches an agent. Salesforce installs a default "Inbound Flow" contact flow that routes calls to the Omni-Channel queue. Custom contact flows (IVR menus, business hours checks, callback deflection) must be built in the Amazon Connect console after the wizard completes, and then re-associated with the phone number in the Amazon Connect console, not in Salesforce Setup.

### Real-Time Transcription

Live transcription of voice calls requires enabling **Live Media Streaming** on the Amazon Connect instance in the AWS console, under **Data Storage > Live Media Streaming**. This is separate from post-call recordings. Once live media streaming is enabled in AWS, the admin must return to Salesforce Setup > Contact Centers and enable **Call Transcription** on the contact center record. Real-time transcription data flows to the VoiceCall record as transcript segments accessible to supervisors via the Service Console. UNVERIFIED (2026-09-05): the Live Media Streaming / Kinesis Video Streams prerequisite and the Salesforce-side Call Transcription toggle are help-only and AWS-only; neither appears in the Metadata API Developer Guide or the Object Reference. What is grounded on the Salesforce side is that `VoiceCall.TranscribedLanguage` is "automatically populated by the Conversation Intelligence platform" and must not be set by hand (object_reference.txt L307453-307459), and that phone-number masking, when enabled, redacts numbers in transcripts as well as recordings (api_meta.txt L126856-126865). Einstein Real-Time Agent Assist and Einstein Automated Summaries both depend on this stream being active. Without live media streaming enabled at the Amazon Connect level, enabling transcription in Salesforce will silently produce no transcript output.

### After Conversation Work Time (ACW)

After Conversation Work Time holds an agent in a wrap-up state after a call ends, preventing new work
from being routed to them. In metadata it is a **required field group on the Voice service channel**,
not a toggle on the contact center:

```xml
<ServiceChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Voice Calls</label>
    <relatedEntityType>VoiceCall</relatedEntityType>
    <hasAfterConvoWorkTimer>true</hasAfterConvoWorkTimer>   <!-- requires the next line -->
    <afterConvoMaxTime>120</afterConvoMaxTime>              <!-- 10-3600 seconds -->
    <hasAcwExtensionEnabled>true</hasAcwExtensionEnabled>   <!-- requires the next two lines -->
    <acwExtensionDuration>60</acwExtensionDuration>         <!-- 10-3600 seconds -->
    <maxExtensions>2</maxExtensions>                        <!-- 1-10 -->
</ServiceChannel>
```

All five are `ServiceChannel` fields, "Available only for service channels of type Messaging or
Voice", with Voice support from API 52.0 (api_meta.txt L107784-107792, L107825-107841, L107852-107856).
From API 65.0 the same timer can instead be set per user or profile on `PresenceUserConfig`
(api_meta.txt L96989-96993, L97037-97046). The Object Reference confirms the runtime behaviour from
the other end: a call reaching `CallDisposition` = `completed` means "the call has ended… If After
Conversation Work (ACW) is enabled, that work begins after the call completes"
(object_reference.txt L306831-306841).

UNVERIFIED (2026-09-05): the Setup navigation path "Setup > After Conversation Work Time" and the
claim that ACW is additionally toggled per contact-center record are help-only. No `CallCenter` or
`ConversationVendorInfo` field in the Metadata API Developer Guide corresponds to an ACW switch. If a
contact-center-level toggle exists in the UI, the deployable source of truth is still the
`ServiceChannel` field group above — configure and review it there. `references/gotchas.md` Gotcha 4
records the two-surface behaviour as observed; Gotcha 7 records what the guide says.

---

## Common Patterns

### Pattern: Greenfield Provisioning via Guided Wizard

**When to use:** New deployment with no existing Amazon Connect instance. The org has the Voice add-on, Omni-Channel is enabled, My Domain is deployed.

**How it works:**
1. Navigate to Setup > Service Cloud Voice > Contact Centers > New.
2. Follow the wizard: name the contact center, select AWS region closest to the agent population, let Salesforce create a new Amazon Connect instance.
3. Claim at least one phone number during the wizard. You can add numbers later from the contact center record.
4. After wizard completion, verify the Voice service channel appears under Setup > Omni-Channel > Service Channels.
5. Assign the Voice service channel to the appropriate Omni-Channel queue and routing configuration.
6. Add agents to the queue and assign them the "Service Cloud Voice" permission set.
7. Test by calling the claimed number from an external phone; the call should appear as a work item in the agent's Omni-Channel widget in the Service Console.

**Why not the alternative:** Attempting to manually create an Amazon Connect instance in the AWS console and link it afterward skips the automated IAM trust configuration and contact flow installation. This leaves the integration in a broken state where calls route to Amazon Connect but cannot be passed to Salesforce agents.

### Pattern: Enabling Real-Time Transcription on an Existing Contact Center

**When to use:** Voice is already live with basic call routing, but the team wants live transcription for supervisor monitoring or Einstein AI features.

**How it works:**
1. In the AWS console, open the Amazon Connect instance linked to the org.
2. Under Data Storage, enable Live Media Streaming with a Kinesis Video Stream. Select a retention period (minimum 0 hours is acceptable for transcription-only use cases).
3. Return to Salesforce Setup > Service Cloud Voice > Contact Centers, open the contact center record, and enable **Call Transcription**.
4. Assign the "Service Cloud Voice Transcription" permission set to supervisors who should see live transcript panels in the Service Console.
5. Test by placing a call and confirming the Transcript panel populates in the VoiceCall record in real time.

**Why not the alternative:** Enabling transcription in Salesforce Setup without first activating live media streaming in AWS produces no error — it simply silently produces no transcripts. The misconfiguration is hard to diagnose because the VoiceCall record is created and the call routes correctly; only the transcript segments are missing.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| No existing Amazon Connect account | Use guided wizard to provision a new instance | Wizard handles all AWS IAM trust, contact flows, and OAuth — zero manual AWS work required |
| Existing Amazon Connect instance in AWS | Import path in wizard, provide instance ARN | Preserves existing contact flows and numbers, but requires IAM permissions and manual flow mapping |
| Sandbox testing of voice setup | Provision a separate Amazon Connect instance for the sandbox | One Salesforce org per Amazon Connect instance; sharing with production is unsupported |
| Agents need wrap-up time after calls | Enable and configure After Conversation Work Time | ACW is the platform-native mechanism; custom presence rules are not needed |
| Supervisor live monitoring of transcripts | Enable live media streaming in AWS + transcription in Salesforce | Both must be active; Salesforce-only configuration produces no output |
| Custom IVR or business hours routing | Build contact flows in Amazon Connect console after wizard | Salesforce wizard does not expose contact flow editing; all flow logic lives in Amazon Connect |
| Telephony is not Amazon Connect | Set `vendorType` to `ServiceCloudVoicePartner` (or `BringYourOwnContactCenter` for CCaaS messaging) | The enum is restricted to four values; the connector, bridge and integration-class fields are scoped to these models only (api_meta.txt L38708-39034) |
| One wrap-up time for the whole org | ACW fields on the Voice `ServiceChannel` | One record to keep consistent, and it works on a v62 manifest (api_meta.txt L107784-107841) |
| Wrap-up time differs per team | ACW fields on `PresenceUserConfig`, assigned by profile or user | Per-team control, at the cost of API 65.0+ and N records per release (api_meta.txt L96989-96993, L97063-97072) |
| Promoting a contact center between orgs | Retrieve production, diff, re-point handler and fallback IDs | Those fields hold org-specific record IDs and carry "Don't change the value in this field" (api_meta.txt L31575-31619) |

---

## Recommended Workflow

1. **Establish the vendor model and read the questions.** Answer `## Questions to Ask Before
   Configuring` in full. The first answer alone — Amazon Connect vs Partner Telephony vs Bring Your
   Own Channel for CCaaS — decides `ConversationVendorInfo.vendorType` and which half of that type's
   fields are even legal (`references/metadata-examples.md` §2). Record it in
   `templates/service-cloud-voice-setup-template.md` before touching Setup.
2. **Clear the two prerequisites that fail silently.** Confirm Omni-Channel is on (without it none of
   `ServiceChannel`, `ServicePresenceStatus`, or `PresenceUserConfig` will deploy), and retrieve
   `Settings:MyDomain` to confirm `isFirstPartyCookieUseRequired` is `false`. Deploy that settings
   change first if it is not — see `references/gotchas.md` Gotcha 6.
3. **Provision, then retrieve — do not hand-author the contact center.** Run the guided setup, then
   pull the result into source so it is reviewable and promotable:
   `sf project retrieve start --metadata CallCenter ConversationVendorInfo ServiceChannel
   ServicePresenceStatus PresenceUserConfig CallCenterRoutingMap --metadata "Settings:ServiceCloudVoice"`.
   The `sections`/`items` names inside a live `CallCenter` are vendor-generated; copy them, never
   invent them.
4. **Author the routing layer as source.** Add or edit the Voice `ServiceChannel`
   (`relatedEntityType` = `VoiceCall`) with its complete ACW field group, a `ServicePresenceStatus`
   that names that channel, and a `PresenceUserConfig` with a real `capacity`. Use
   `references/metadata-examples.md` §4 for the shapes and the 10–3600 / 1–10 bounds.
5. **Lint before you deploy.** Run
   `python3 skills/admin/service-cloud-voice-setup/scripts/check_service_cloud_voice_setup.py
   --manifest-dir force-app/main/default`. It fails the build on an invalid `vendorType`, a half-set
   ACW group, `relatedEntity` in place of `relatedEntityType`, a missing Voice channel, a
   `PresenceUserConfig` without `capacity`, Sales Dialer fields in `ServiceCloudVoice.settings`, and
   `isFirstPartyCookieUseRequired` left true. Then
   `sf project deploy validate --manifest manifest/package.xml` in the deploy order in
   `references/metadata-examples.md` §7.
6. **Handle the AWS-side work as its own change record.** Live Media Streaming for transcription and
   the S3 bucket that holds Amazon Connect recordings are outside Salesforce and outside the
   validator's reach. Assign each an owner, capture the retention policy, and note the transcription
   prerequisite — the Salesforce toggle alone produces nothing (`references/gotchas.md` Gotchas 1
   and 11).
7. **Verify from the data, not the UI.** Place a test call, then run the four diagnostic queries at
   the end of `references/examples.md` in order. They separate "no handoff at all" from "arrived but
   unlinked" from "queued but never routed" from "agents never mapped to vendor identities" — the
   four failures that all present to a user as "the phone doesn't work".

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Voice add-on license is active and the Contact Centers menu appears in Setup
- [ ] Amazon Connect instance provisioned (or imported) and linked to the contact center record
- [ ] At least one phone number claimed and associated with the inbound contact flow
- [ ] Voice service channel exists in Omni-Channel and is assigned to a queue and routing config
- [ ] Agents and supervisors have correct Service Cloud Voice permission sets
- [ ] Real-time transcription tested end-to-end if enabled (live media streaming active in AWS)
- [ ] After Conversation Work Time configured and tested if wrap-up time is required
- [ ] No orphaned Amazon Connect instances in AWS from failed partial wizard runs
- [ ] `scripts/check_service_cloud_voice_setup.py --manifest-dir <source>` reports zero errors
- [ ] `MyDomain.settings` has `isFirstPartyCookieUseRequired` set to `false`
- [ ] A Voice `ServiceChannel` exists with `relatedEntityType` = `VoiceCall`, and its ACW field group is complete and inside 10–3600 / 1–10
- [ ] At least one `ServicePresenceStatus` names the Voice channel, and `PresenceUserConfig.capacity` is set
- [ ] `ServiceCloudVoice.settings` contains no Sales Dialer (`Voice.settings`) fields
- [ ] The S3 bucket holding Amazon Connect call recordings has a named owner and a documented retention policy
- [ ] The four diagnostic queries in `references/examples.md` were run after a live test call

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Live media streaming must be enabled in AWS before transcription works in Salesforce** — Enabling Call Transcription on the Salesforce contact center record without first enabling Live Media Streaming in the Amazon Connect AWS console produces no error and no transcript output. Calls route normally; only transcripts are silently missing. Always validate in AWS first.
2. **One Amazon Connect instance per Salesforce org** — Salesforce enforces a one-to-one relationship between a Salesforce org and an Amazon Connect instance. Attempting to link the same Amazon Connect instance to a sandbox and production org will fail. Sandboxes must provision their own Amazon Connect instances.
3. **Partial wizard runs leave orphaned AWS resources** — If the guided wizard is abandoned mid-flow (e.g., after the Amazon Connect instance is created but before phone number claiming), an Amazon Connect instance remains in AWS with no corresponding active contact center record in Salesforce. These orphaned instances consume AWS service limits. Always complete or roll back wizard runs fully.
4. **Deploying half an ACW field group fails the deploy** — `hasAfterConvoWorkTimer` without a max-time value, or `hasAcwExtensionEnabled` without both `acwExtensionDuration` and `maxExtensions`, is rejected rather than partially applied (api_meta.txt L107825-107841).
5. **A presence status with no channels is silently an Away status** — agents pick it, appear online, and are never routed a call (api_meta.txt L107966-107970).

`references/gotchas.md` carries all eleven with **What happens / When it occurs / How to avoid** and the guide line behind each.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Contact Center record | Salesforce record linking to the Amazon Connect instance; holds transcription and ACW settings |
| Voice service channel | Omni-Channel service channel of type Voice, used for queue and routing configuration |
| VoiceCall record | Created per call; stores call metadata, participant info, and transcript segments |
| After Conversation Work presence status | System presence status agents enter automatically after call completion |
| `ConversationVendorInfo` component | Names the telephony system and its `vendorType`; the first thing to check when a contact center behaves like the wrong product |
| Voice `ServiceChannel` component | `relatedEntityType` = `VoiceCall`, and the deployable home of the ACW field group |
| `ServicePresenceStatus` + `PresenceUserConfig` | Decide whether an online agent is routable and how much work they can hold |
| `CallCenterRoutingMap` records | Map Salesforce users and queues to vendor identities; required for transfer availability |
| `VoiceCallRecording` records | Link rows only — for Amazon Connect the audio itself lives in S3 on your AWS account |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing, reviewing, or promoting the deployable XML — CallCenter, ConversationVendorInfo, ServiceChannel with ACW, presence config, routing map, settings, package.xml, deploy order, verification SOQL |
| `references/gotchas.md` | Something provisioned cleanly and still does not work: silent transcription, cookies, ACW deploy failures, Away statuses, recordings that are not in Salesforce |
| `references/examples.md` | Walking a greenfield or transcription-enablement scenario end to end, or running the four-query diagnostic when calls are not reaching agents |
| `references/well-architected.md` | Choosing between the guided wizard and the import path, channel-level vs per-user ACW, always-on vs selective transcription — and for the source list behind every claim here |
| `references/llm-anti-patterns.md` | Reviewing AI-generated Service Cloud Voice guidance before acting on it |
| `templates/service-cloud-voice-setup-template.md` | Starting a build, to record the answers from `## Questions to Ask Before Configuring` |
| `scripts/check_service_cloud_voice_setup.py` | Before every deploy, with `--manifest-dir` pointed at the retrieved source |

---

## Related Skills

- `admin/omni-channel-routing-setup` — Queues, routing configurations, and capacity for the Voice service channel this skill creates; go there for the routing rules, come here for the channel and its ACW fields
- `admin/service-console-configuration` — Where the softphone and Omni-Channel widget live in the console app: utility bar items, workspace tabs, and the agent's screen layout
- `admin/messaging-and-chat-setup` — The Messaging service channel that shares the ACW field group and presence model with Voice; read it when voice and digital channels must share agent capacity
- `apex/cti-adapter-development` — The Open CTI path for non-Amazon telephony, and the `service_cloud_voice` interfaces (`PartnerSSO`, `RecordingMediaProvider`) a Partner Telephony integration class must implement
- `admin/sales-engagement-cadences` — Sales Engagement outbound calling, and the `disableSCVTaskCreationForHVS` setting that governs automatic task creation from voice calls
