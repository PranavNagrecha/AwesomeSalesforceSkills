# Examples — Messaging and Chat Setup

## Example 1: Greenfield MIAW Deployment for a B2C Support Site

**Context:** A retail company is launching Service Cloud for the first time. They want a chat button on their support portal at `https://support.example.com`. Agents work in a single English-language queue with a capacity of four concurrent sessions each.

**Problem:** Without this skill's guidance, an admin might navigate to the legacy "Chat" setup area, configure a Live Agent Chat Button and deployment, embed the Snap-ins snippet, and deploy. The result looks functional in the sandbox but routes sessions to `LiveChatTranscript` records, not `MessagingSession` records. MIAW-native features (asynchronous session resumption, Einstein bot handoff, Omni-Channel Flow routing) are unavailable. The deployment type cannot be changed after creation.

**Solution:**

Step 1 — Enable Messaging for In-App and Web in Setup > Messaging Settings.

Step 2 — Create the Messaging Channel:
```
Setup > Messaging > Messaging Channels > New
  Channel Type:         Messaging for In-App and Web
  Name:                 Support Portal Chat
  Routing:              Queue — Support Tier 1
  Fallback Queue:       Support Fallback
  Off-Hours Message:    "We are currently offline. Our hours are Mon–Fri 9am–6pm PT."
```

Step 3 — Declare the pre-chat parameters on the Messaging Channel. Standard parameters are limited to `Email`, `FirstName`, `LastName` and `Subject`; anything else is a custom parameter. The *form* that renders them is built on the deployment in step 4, not here.

```
Messaging Channel standardParameters:  FirstName, LastName, Subject
Messaging Channel customParameters:    (none for this deployment)
```

Step 4 — Create the Embedded Service Deployment:
```
Setup > Embedded Service Deployments > New
  Type:                 Messaging for In-App and Web
  Name:                 Support Portal Deployment
  Messaging Channel:    Support Portal Chat
```

Step 4b — Build the pre-chat form on the Embedded Service Deployment, one form field per parameter declared in step 3, with `messagingChannelParameterType` set to `Standard` for each.

Step 5 — Register the domain in CORS **and** CSP. The CSP entry needs its directives set explicitly — they all default to false, so an entry with none of them ticked is inert:

```
CorsWhitelistOrigin urlPattern:  https://support.example.com
CspTrustedSite endpointUrl:      https://support.example.com
CspTrustedSite context:          All
CspTrustedSite directives on:    connect-src, frame-src, img-src, style-src, font-src
```

Step 6 — Copy the snippet from the deployment record and add to `<head>` of the portal pages.

**Why it works:** Using the MIAW channel type throughout ensures sessions land on `MessagingSession` records, agents see sessions in the Omni-Channel widget with correct capacity counting, and the asynchronous session model is available if agents need it.

---

## Example 2: Flow-Based Routing with Language Detection

**Context:** A software company supports English and Spanish customers from two separate Omni-Channel queues. A pre-chat field asks the customer to select their preferred language. Outside business hours, customers should receive an auto-response and the session should end rather than queue indefinitely.

**Problem:** A single queue on the Messaging Channel cannot branch on pre-chat field values. Without a routing Flow, all sessions go to the same queue regardless of language selection, requiring agents to manually transfer sessions.

**Solution:**

Step 1 — Create two Omni-Channel Queues: `Support EN` and `Support ES`.

Step 2 — Create an Omni-Channel Flow (Flow type: Omni-Channel):
```
Flow name: Route Chat by Language and Hours

Elements:
  1. Get Records — Query BusinessHours where IsDefault = true
  2. Decision — IsWithinBusinessHours?
       Yes branch → Decision: LanguageField == 'ES'?
                      Yes → Route To Queue: Support ES
                      No  → Route To Queue: Support EN
       No branch  → Send Message: "We are closed. Contact us during business hours."
                 → End Session
```

Step 3 — On the Messaging Channel, set the routing fields. In metadata these are three elements, and the queue is not optional — it is the flow's fallback:

```
sessionHandlerType:   Flow
sessionHandlerFlow:   Route_Chat_By_Language
sessionHandlerQueue:  Support_Fallback     <- Required; used when the flow cannot route
```

Step 4 — Wire the language answer through to the flow. A pre-chat answer only reaches the flow if the channel declares it as a parameter *and* maps it to the flow by name:

```xml
<customParameters>
    <name>PreferredLanguage</name>
    <masterLabel>Preferred Language</masterLabel>
    <externalParameterName>preferredLanguage</externalParameterName>
    <parameterDataType>Picklist</parameterDataType>
    <actionParameterMappings>
        <actionParameterName>Route_Chat_By_Language</actionParameterName>
    </actionParameterMappings>
</customParameters>
```

`actionParameterName` is the **flow's API name**, not a variable inside it. Omit the mapping and the parameter is collected, stored, and never seen by the routing logic — the flow falls through to its default branch and every session lands in one queue, which looks exactly like a broken decision element.

Step 5 — Test three paths, not one. Language `ES` in hours should reach Support ES; language `EN` in hours should reach Support EN; any language out of hours should get the auto-response. Then confirm with data:

```sql
SELECT Id, Status, Origin, ChannelType, OwnerId, StartTime, AcceptTime, EndedByType
FROM MessagingSession
WHERE ChannelType = 'EmbeddedMessaging'
  AND StartTime = TODAY
ORDER BY StartTime DESC
```

A row with `Status = 'Waiting'` and a null `OwnerId` after the test means the flow placed the session somewhere nobody can accept from — check the fallback queue's membership before touching the flow.

**Why it works:** Omni-Channel Flows have native access to session context (including pre-chat field values) and business hours records, making conditional routing reliable without custom Apex. The fallback queue ensures no session is permanently lost if the flow fails.

---

## Anti-Pattern: Using CORS Without CSP (or Vice Versa)

**What practitioners do:** The widget does not appear. The network tab shows a **404** against the Salesforce endpoint, so the admin concludes the URL in the snippet is wrong and starts editing the snippet. Later, having fixed the CORS entry, they add a CSP Trusted Site, see it listed in Setup, and stop.

**What goes wrong:** Two separate misreadings of the same symptom. First, a non-allowlisted origin does not produce a CORS-labelled error — Salesforce returns HTTP 404 — so the failure impersonates a bad URL. Second, a CSP Trusted Site grants nothing until a directive is set: every `isApplicableTo*Src` field defaults to false, so the record can be present, active, and completely inert. The admin has two green ticks in Setup and a widget that still will not load.

**Correct approach:** Register the pair, and set the CSP directives explicitly rather than accepting defaults:

```xml
<CspTrustedSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <endpointUrl>https://support.example.com</endpointUrl>
    <context>All</context>
    <isActive>true</isActive>
    <isApplicableToConnectSrc>true</isApplicableToConnectSrc>
    <isApplicableToFrameSrc>true</isApplicableToFrameSrc>
    <isApplicableToImgSrc>true</isApplicableToImgSrc>
    <isApplicableToStyleSrc>true</isApplicableToStyleSrc>
    <isApplicableToFontSrc>true</isApplicableToFontSrc>
</CspTrustedSite>
```

Two follow-on rules worth knowing before you scale this to five environments. A CORS `urlPattern` may use a wildcard, but only in front of a second-level domain — `https://*.example.com` covers every subdomain in one entry, while `https://support.*.com` is rejected. And the generated CSP header has a practical ceiling around 12 KB, so a per-subdomain entry per environment is not free.
