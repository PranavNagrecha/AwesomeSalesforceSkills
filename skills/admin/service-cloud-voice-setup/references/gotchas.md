# Gotchas — Service Cloud Voice Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Transcription Silently Produces No Output If Live Media Streaming Is Not Enabled in AWS

**What happens:** An admin enables Call Transcription on the Salesforce contact center record. Calls route correctly, VoiceCall records are created with call metadata, but the Transcript panel is always empty. No error message appears in Salesforce.

**When it occurs:** Any time Call Transcription is toggled on in Salesforce Setup without first enabling Live Media Streaming in the Amazon Connect instance's AWS console (Data Storage > Live Media Streaming). The Salesforce transcription service has no audio stream to consume, so it produces nothing, and Salesforce does not surface a configuration validation error.

**How to avoid:** Always configure AWS first. In the Amazon Connect console, navigate to the instance > Data Storage > Live Media Streaming, enable it, and attach a Kinesis Video Stream before enabling Call Transcription in Salesforce. After both are configured, place a live test call and confirm transcript segments appear on the VoiceCall record before marking the feature active.

---

## Gotcha 2: One Amazon Connect Instance Per Salesforce Org — Sandboxes Cannot Share Production's Instance

**What happens:** A team attempts to test Service Cloud Voice in a full-copy sandbox by pointing it at the same Amazon Connect instance used for production. The wizard either fails to complete or the sandbox contact center record appears orphaned with no working routing.

**When it occurs:** Amazon Connect enforces a one-to-one relationship with a Salesforce org's OAuth application. When production already holds the OAuth trust for an Amazon Connect instance, a sandbox cannot also claim it. Even if a sandbox can see the instance, routing events fire against the production org's event bus, not the sandbox's — which can corrupt production VoiceCall records during sandbox testing.

**How to avoid:** Provision a dedicated Amazon Connect instance for each Salesforce org (production, full-copy sandbox, partial sandbox). Use separate AWS sub-accounts or at minimum separate Amazon Connect instances per org. Document which instance ARN is associated with which Salesforce org. Budget for the Amazon Connect service costs of the sandbox instance.

---

## Gotcha 3: Partial Wizard Runs Leave Orphaned Amazon Connect Instances in AWS

**What happens:** An admin starts the provisioning wizard, gets through the Amazon Connect instance creation step, but abandons the wizard before completing phone number claiming (e.g., due to a browser refresh, permission error, or timeout). An Amazon Connect instance now exists in AWS but the Salesforce contact center record is in an incomplete or error state. Re-running the wizard creates a second Amazon Connect instance in AWS.

**When it occurs:** Any wizard abandonment after the AWS instance creation step. Common causes include: insufficient Salesforce permissions (the wizard proceeds past some checks before halting on others), AWS service limit hits during phone number claiming, and session timeouts on long wizard flows.

**How to avoid:** Before running the wizard, verify all prerequisites (license, My Domain, Omni-Channel, admin permission sets) to minimize mid-wizard failures. If a partial run occurs, log into the AWS console and delete the orphaned Amazon Connect instance before re-running the wizard. Check your Amazon Connect instance count limit in AWS (default is low for new accounts) — orphaned instances count against this limit.

---

## Gotcha 4: After Conversation Work Time Must Be Enabled on the Contact Center Record, Not Just Configured in Setup

**What happens:** An admin configures maximum ACW duration under Setup > After Conversation Work Time and assigns the duration. However, agents are never placed in ACW presence status after calls — they are immediately available for new work.

**When it occurs:** ACW has two configuration surfaces: the global Setup page where the duration is defined, and the individual contact center record where ACW must be explicitly toggled on. If the contact center record does not have ACW enabled, the global duration setting has no effect.

**How to avoid:** After configuring ACW duration in Setup, navigate to Setup > Service Cloud Voice > Contact Centers, open each contact center record, and explicitly enable "After Conversation Work Time" on that record. Test by completing a call and verifying the agent's Omni-Channel widget shows the "After Conversation Work" presence status with a countdown timer.

---

## Gotcha 5: Custom Domain (My Domain) Must Be Deployed to All Users Before Provisioning

**What happens:** The provisioning wizard completes, but agents opening the Service Console see a blank or broken phone widget. The softphone does not load and throws an OAuth redirect error in the browser console.

**When it occurs:** The Amazon Connect softphone widget is served from a Lightning page and loads via a URL tied to the org's My Domain. If My Domain is configured but not yet deployed to all users (Setup > My Domain > Deployment > Deploy to All Users), some agents retain the old instance URL format. The Amazon Connect OAuth callback URI is registered against the My Domain URL — a mismatch causes the OAuth flow to fail silently.

**How to avoid:** Confirm My Domain is fully deployed to all users before starting the provisioning wizard. Check Setup > My Domain and ensure the "Deploy to All Users" action has been completed (not just "Deploy to the organization"). This is a one-time action that cannot be reversed once completed, so perform it during a low-traffic window.

---

## Gotcha 6: My Domain's `isFirstPartyCookieUseRequired` Silently Breaks Amazon Connect — and Orgs Created After Summer '24 Default It On

**What happens:** The softphone widget fails to load or the agent is repeatedly signed out of the
contact center, with no configuration error anywhere in Setup. The Metadata API Developer Guide is
explicit about the cause: "Service Cloud Voice with Amazon Connect and Service Cloud Voice with
Partner Telephony from Amazon Connect aren't compatible with this setting. If you use those features,
set `isFirstPartyCookieUseRequired` to `false`" (api_meta.txt L122293–122299, `MyDomainSettings`).

**When it occurs:** Whenever `MyDomainSettings.isFirstPartyCookieUseRequired` is `true`. The same
field description states: "In Salesforce orgs created in Summer '24 and later, the default is `true`.
In all other orgs, the default is `false`." So a brand-new org fails by default and a long-lived org
does not — which is exactly the pattern that makes a team conclude "it worked in the old sandbox, so
Voice must be broken in the new one." A sandbox spun from a newer template inherits the newer default.

**How to avoid:** Read the flag before provisioning, not after the first failed call. Retrieve
`Settings:MyDomain`, confirm `<isFirstPartyCookieUseRequired>false</isFirstPartyCookieUseRequired>`,
and deploy the change ahead of the contact center. `enableCrossDomainPreviewCookies` is only
meaningful when the flag is `true` (api_meta.txt L122225–122229), so it is not a workaround.

---

## Gotcha 7: After Conversation Work Is a Service Channel Field Pair, and Setting Half of It Fails the Deploy

**What happens:** A deploy that sets `hasAfterConvoWorkTimer` to `true` on the Voice service channel
without also setting the maximum-time field is rejected. The `ServiceChannel` field table is
unambiguous: "If set to `true`, After Conversation Work (ACW) time can be configured for the channel.
If set to `true`, you must also set the `afterConvoWorkMaxTime` field" (api_meta.txt L107832–107841),
and the corresponding field states "You must set this field if `hasAfterConvoWorkTimer` is set to
`true`. Specify a value from 10 through 3600" (api_meta.txt L107784–107792).

**When it occurs:** Three variants, all from the same partial-set mistake. (1) Timer on, max time
missing. (2) `hasAcwExtensionEnabled` on without both `acwExtensionDuration` (10–3600) and
`maxExtensions` (1–10) — "Available only if `hasAfterConvoWorkTimer` is set to `true`. If set to
`true`, you must also set the `acwExtensionDuration` and `maxExtensions` fields"
(api_meta.txt L107825–107831, L107778–107783, L107852–107856). (3) The fields set on a channel whose type is neither
Voice nor Messaging: all four are "Available only for service channels of type Messaging or Voice."

**How to avoid:** Treat ACW as an atomic group of two (or five, with extensions) elements on the
`ServiceChannel` file, and keep every seconds value inside 10–3600. Note the guide's own field table
labels the max-time element `afterConvoMaxTime` while the `hasAfterConvoWorkTimer` description calls
it `afterConvoWorkMaxTime` (api_meta.txt L107784–107792 versus L107832–107841); `PresenceUserConfig`
uses `afterConvoWorkMaxTime` (api_meta.txt L96989–96993). UNVERIFIED (2026-09-05): the guide is
internally inconsistent on the `ServiceChannel` spelling, so retrieve the channel from the target org
and copy the element name that comes back rather than trusting either page.

---

## Gotcha 8: `Voice.settings` Is Sales Dialer — Editing It Changes Nothing in Service Cloud Voice

**What happens:** An admin asked to "turn on call recording for voice" finds
`enableVoiceCallRecording` in `settings/Voice.settings-meta.xml`, sets it to `true`, deploys cleanly,
and nothing changes for contact-center agents. The deploy succeeded because the field is real; it just
belongs to a different product.

**When it occurs:** Any time the two similarly named settings types are confused. `VoiceSettings`
"Represents an org's Sales Dialer settings, such as call recording, conferencing, and voicemail"
(api_meta.txt L128646–128647), and each of its fields ends with "To use this feature, enable Dialer in
Lightning Experience" (api_meta.txt L128686–128700). Service Cloud Voice lives in
`ServiceCloudVoiceSettings` / `ServiceCloudVoice.settings`, whose switch is `enableServiceCloudVoice`
(api_meta.txt L126897–126900). The confusion is compounded because both products write to the same
`VoiceCall` object, so reports still show rows.

**How to avoid:** Match the file name to the product before editing: `ServiceCloudVoice.settings` for
contact centers, `Voice.settings` for Sales Dialer. In a mixed org, separate the traffic in reports
with `VoiceCall.VendorType`, which "for Salesforce Voice … is always set to `ContactCenter`"
(object_reference.txt L307500–307509).

---

## Gotcha 9: The Contact Center sObject Has No `update()` — and Re-deploying Its Routing Fields Overwrites UI Configuration

**What happens:** A script tries to correct a contact center's name or version with a DML update and
gets an unsupported-operation error. Separately, a team round-trips the `CallCenter` file from sandbox
to production and finds voicemail routing pointing at the wrong flow afterwards.

**When it occurs:** The `CallCenter` object's supported calls are `create(), describeSObjects(),
getDeleted(), getUpdated(), query(), retrieve()` — no `update()`, no `delete()`
(object_reference.txt L56385). Changing a live contact center is a metadata deploy, not DML. And four
`ContactCenterChannel` subtype fields carry an explicit warning: `voiceMailHandler`,
`voiceMailFallbackQueue` (api_meta.txt L31603–31619) and, from API 65.0, `omniCallbackHandler`,
`omniCallbackFallbackQueue` (api_meta.txt L31575–31602) each say "Don't change the value in this
field. Instead, configure … routing in Lightning Experience." Those values are org-specific record
IDs, so a sandbox file carries sandbox IDs into production.

**How to avoid:** Retrieve the production `CallCenter` before every deploy and diff it, rather than
promoting the sandbox copy wholesale. Strip or re-point `contactCenterChannels` handler and fallback
elements to the production values. Remember `Name` and `InternalName` are capped at 80 characters
(object_reference.txt L56429–56448), so a long descriptive name fails at create time, not at design
time.

---

## Gotcha 10: A Presence Status With No Channels Becomes an "Away" Status, So the Agent Is Never Routed a Call

**What happens:** Agents show as online in the Omni-Channel widget, pick a status that looks
available, and receive no calls. Routing is configured correctly and the queue has work; the agents
simply are not eligible.

**When it occurs:** The `ServicePresenceStatus` `channels` field says: "Represents the service channels
assigned to the presence status. If no service channels are included, the presence status is
automatically marked as 'Away' (where `IsAway` is set to `true`.)" (api_meta.txt L107966–107970). A
hand-authored status file that omits the `channels` block, or one whose `channel` value does not match
the Voice `ServiceChannel`'s API name, is silently converted to an Away status. Nothing in the deploy
result says so.

**How to avoid:** Every routable status file must contain a `channels`/`channel` pair naming the Voice
service channel, and the deploy must place the `ServiceChannel` before the `ServicePresenceStatus`
that references it. Then check the presence configuration too: `PresenceUserConfig.capacity` is
Required (api_meta.txt L96998–97001), and `enableAutoAccept` is "Available only if `enableDecline` is
set to `false`" while `enableDecline` is available only if `enableAutoAccept` is `false`
(api_meta.txt L97004–97012) — setting both `true` is a contradiction the file will not resolve for you.

---

## Gotcha 11: Amazon Connect Call Recordings Are Not in Salesforce, So a `VoiceCallRecording` Row Proves Only Linkage

**What happens:** A compliance team confirms recordings exist by querying `VoiceCallRecording`, then
discovers during an audit that the audio itself is unreachable because the AWS-side bucket or its
lifecycle policy was changed by a different team.

**When it occurs:** The Object Reference is explicit: "Call recordings for Salesforce Voice with
Amazon Connect and for Salesforce Voice with Partner Telephony from Amazon Connect are stored in S3
buckets on your Amazon Web Services (AWS) account and can be accessed via AWS. Call recordings for
Sales Dialer are saved as files in Salesforce" (object_reference.txt L308341–308343). Only the Sales
Dialer path puts a `ContentDocument` in Salesforce via `MediaContentId`, which "counts toward your
org's file storage quota" (object_reference.txt L308398–308408). Retention for the Amazon Connect path
is an AWS bucket policy that Salesforce neither sets nor monitors.

**How to avoid:** Treat the retention SLA as an AWS artefact with a named owner, and make the S3
lifecycle policy part of the same change record as the Salesforce configuration. Two related access
facts belong in the same runbook: "As of Spring '20 and later, only your Salesforce org's internal
users can access this object" (object_reference.txt L308351), and on `VoiceCall`, "Only users with the
Modify All Data permission can delete call records" (object_reference.txt L306747) — so a
right-to-erasure request cannot be delegated to a support supervisor without over-granting.
