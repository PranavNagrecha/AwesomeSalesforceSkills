---
name: service-cloud-voice-setup
description: "Use this skill when setting up Service Cloud Voice with Amazon Connect — provisioning the contact center, configuring phone numbers, enabling real-time transcription, and configuring After Conversation Work Time. NOT for CTI adapter development, Open CTI customization, or custom Amazon Connect Lambda development outside the guided wizard."
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
dependencies:
  - omni-channel-routing
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Service Cloud Voice Setup

This skill covers the end-to-end admin setup of Service Cloud Voice using the Salesforce-guided wizard that provisions an Amazon Connect instance, configures Omni-Channel routing for voice, enables real-time transcription, and sets up After Conversation Work Time (ACW). Activate this skill when a team needs to go from a licensed org to agents handling calls in the Service Console.

---

## Before Starting

Gather this context before working on anything in this domain:

- Verify the org has the **Service Cloud Voice with Amazon Connect** add-on license. The setup wizard will not appear in Setup without it. Partners and ISVs provisioning on behalf of customers must confirm the license is active on the production org, not just a sandbox.
- Confirm **My Domain** (custom domain) is deployed to all users. The Amazon Connect softphone widget is loaded via a Lightning page that requires a custom domain. Without it, OAuth callbacks from Amazon Connect will fail.
- Confirm **Omni-Channel** is enabled under Setup > Omni-Channel Settings. Service Cloud Voice creates a Voice service channel inside Omni-Channel; if Omni-Channel is not enabled, the wizard will halt.
- The most common wrong assumption: practitioners assume Amazon Connect can be configured from the AWS console independently and then "connected" to Salesforce as a second step. The correct path is the Salesforce-guided wizard, which provisions the AWS-side infrastructure on the admin's behalf and handles OAuth integration. Manual AWS-first setup bypasses the required trust configuration.
- Key limits: one Amazon Connect instance per Salesforce production org (you cannot link two production orgs to the same instance); sandbox environments require a separate Amazon Connect instance; concurrent call capacity is governed by your Amazon Connect service limits in AWS, not Salesforce.

---

## Core Concepts

### The Guided Provisioning Wizard

Service Cloud Voice setup begins at **Setup > Service Cloud Voice > Contact Centers**. The wizard walks through four phases: (1) Contact Center naming and region selection, (2) Amazon Connect instance provisioning (or import of an existing instance), (3) phone number claiming, and (4) Omni-Channel service channel creation. Behind the scenes, Salesforce uses an OAuth 2.0 integration between your org and AWS to create IAM roles, configure the Amazon Connect instance, and install the required Amazon Connect contact flows. Admins do not need to log in to the AWS console for a greenfield provisioning. The wizard handles all trust and permission scaffolding.

If an existing Amazon Connect instance needs to be imported rather than created fresh, the admin must provide the instance ARN and have sufficient AWS IAM permissions to grant Salesforce access. The import path is more fragile — existing contact flows must be manually mapped to Salesforce's expected flow entry points.

### Phone Numbers and Contact Flows

During wizard completion, the admin claims one or more phone numbers from Amazon Connect's number inventory. Numbers can be Direct Inward Dial (DID) from available country pools. Each number is associated with a **contact flow** — a routing program in Amazon Connect that determines how an inbound call is handled before it reaches an agent. Salesforce installs a default "Inbound Flow" contact flow that routes calls to the Omni-Channel queue. Custom contact flows (IVR menus, business hours checks, callback deflection) must be built in the Amazon Connect console after the wizard completes, and then re-associated with the phone number in the Amazon Connect console, not in Salesforce Setup.

### Real-Time Transcription

Live transcription of voice calls requires enabling **Live Media Streaming** on the Amazon Connect instance in the AWS console, under **Data Storage > Live Media Streaming**. This is separate from post-call recordings. Once live media streaming is enabled in AWS, the admin must return to Salesforce Setup > Contact Centers and enable **Call Transcription** on the contact center record. Real-time transcription data flows to the VoiceCall record as transcript segments accessible to supervisors via the Service Console. Einstein Real-Time Agent Assist and Einstein Automated Summaries both depend on this stream being active. Without live media streaming enabled at the Amazon Connect level, enabling transcription in Salesforce will silently produce no transcript output.

### After Conversation Work Time (ACW)

After Conversation Work Time is a presence status period that holds an agent in a wrap-up state after a call ends, preventing new work from being routed to them. It is configured under **Setup > After Conversation Work Time**. The admin sets a maximum ACW duration (in seconds). When a call ends, the agent is placed in a reserved "After Conversation Work" presence status automatically; the agent can manually end ACW before the timer expires. ACW is per-contact-center and must be explicitly enabled on the contact center record. If ACW is not configured, calls close immediately and agents are re-queued for work with no wrap-up time.

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

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites** — Confirm the Voice add-on license is active, My Domain is deployed to all users, and Omni-Channel is enabled. Check that the provisioning admin has the "Manage Contact Centers" permission and the "Service Cloud Voice" permission set.
2. **Run the provisioning wizard** — Navigate to Setup > Service Cloud Voice > Contact Centers > New. Complete all wizard steps: contact center name, AWS region, instance creation (or import), phone number claiming. Do not exit the wizard mid-flow; partial completions leave orphaned AWS resources.
3. **Verify Omni-Channel integration** — Confirm the Voice service channel was created under Setup > Omni-Channel > Service Channels. Add the channel to the appropriate routing configuration and queue. Assign capacity weights appropriate for voice (calls are typically weighted at 1.0 with lower capacity settings than chat).
4. **Assign permission sets to agents and supervisors** — Assign "Service Cloud Voice" permission set to all agents who will handle calls. Assign "Service Cloud Voice Transcription" to supervisors if transcription is in scope.
5. **Enable real-time transcription (if required)** — Enable Live Media Streaming in the AWS Amazon Connect console, then enable Call Transcription on the Salesforce contact center record. Test with a live call to confirm transcript segments appear.
6. **Configure After Conversation Work Time** — In Setup > After Conversation Work Time, set a maximum ACW duration appropriate for the team's wrap-up process. Enable ACW on the contact center record. Test by completing a call and confirming the agent enters ACW presence status automatically.
7. **End-to-end test** — Place inbound test calls from an external phone, confirm routing to the queue, answer in the Service Console, verify VoiceCall record creation with call metadata and (if enabled) transcript. Confirm ACW timer triggers post-call.

---

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

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Live media streaming must be enabled in AWS before transcription works in Salesforce** — Enabling Call Transcription on the Salesforce contact center record without first enabling Live Media Streaming in the Amazon Connect AWS console produces no error and no transcript output. Calls route normally; only transcripts are silently missing. Always validate in AWS first.
2. **One Amazon Connect instance per Salesforce org** — Salesforce enforces a one-to-one relationship between a Salesforce org and an Amazon Connect instance. Attempting to link the same Amazon Connect instance to a sandbox and production org will fail. Sandboxes must provision their own Amazon Connect instances.
3. **Partial wizard runs leave orphaned AWS resources** — If the guided wizard is abandoned mid-flow (e.g., after the Amazon Connect instance is created but before phone number claiming), an Amazon Connect instance remains in AWS with no corresponding active contact center record in Salesforce. These orphaned instances consume AWS service limits. Always complete or roll back wizard runs fully.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Contact Center record | Salesforce record linking to the Amazon Connect instance; holds transcription and ACW settings |
| Voice service channel | Omni-Channel service channel of type Voice, used for queue and routing configuration |
| VoiceCall record | Created per call; stores call metadata, participant info, and transcript segments |
| After Conversation Work presence status | System presence status agents enter automatically after call completion |

---

## Related Skills

- omni-channel-routing — Configure routing rules, queue assignments, and capacity weights for voice alongside other channels
- sales-engagement-cadences — Service Cloud Voice integrates with Sales Engagement for outbound call cadences
