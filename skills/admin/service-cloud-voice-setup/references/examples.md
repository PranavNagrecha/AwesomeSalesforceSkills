# Examples — Service Cloud Voice Setup

## Example 1: Greenfield Contact Center Provisioning for a 50-Agent Support Team

**Context:** A mid-size software company is going live with Service Cloud for the first time. They have purchased the Service Cloud Voice with Amazon Connect add-on for 50 agents. Their Salesforce org already has My Domain deployed and Omni-Channel enabled for chat and email. They want phone support active within a week.

**Problem:** Without the guided wizard, admins might attempt to create an Amazon Connect instance manually in AWS, install a CTI adapter from AppExchange, and configure the AWS-Salesforce connection by hand. This bypasses the automated OAuth trust configuration and results in agents seeing a phone widget that cannot authenticate to Amazon Connect.

**Solution:**

Setup sequence (all steps in Salesforce Setup unless noted):

```
Prerequisites verified:
  - Voice add-on license: active
  - My Domain: deployed to all users
  - Omni-Channel: enabled

Step 1: Setup > Service Cloud Voice > Contact Centers > New
  - Contact Center Name: "ACME Support Voice"
  - AWS Region: us-east-1 (closest to agent population)
  - Choose: Create New Amazon Connect Instance
  - Instance alias: acme-support-voice (globally unique in AWS)

Step 2: Claim phone number
  - Country: United States
  - Type: DID (Direct Inward Dial)
  - Number: +1 (415) 555-XXXX (select from available inventory)

Step 3: Wizard completes — verify outputs:
  - Contact center record created in Salesforce
  - Amazon Connect instance visible in AWS console
  - Voice service channel "VoiceCall" appears in Omni-Channel

Step 4: Assign to queue
  - Setup > Omni-Channel > Queues > Support Queue
  - Add "VoiceCall" service channel with capacity weight 1

Step 5: Assign permission sets
  - Assign "Service Cloud Voice" permission set to 50 agents
```

**Why it works:** The guided wizard handles the AWS IAM trust role creation, installs the Salesforce-managed contact flows into Amazon Connect, and creates the OAuth integration between the org and Amazon Connect. Admins never need AWS console access for a greenfield provisioning — the Salesforce wizard executes all AWS API calls on their behalf.

---

## Example 2: Enabling Live Transcription for a Quality Assurance Team

**Context:** A financial services firm already has Service Cloud Voice live with 30 agents. The QA team wants to use Einstein Real-Time Agent Assist and supervisor monitoring panels. Real-time transcription has never been enabled.

**Problem:** An admin enables "Call Transcription" in the Salesforce contact center record but does not touch the AWS console. Calls continue to route normally, VoiceCall records are created, but the Transcript tab on the VoiceCall record is always empty. Supervisors open cases with Salesforce Support assuming a bug.

**Solution:**

```
Step 1 — AWS console (not Salesforce):
  Navigate to: Amazon Connect > Your Instance > Data Storage > Live Media Streaming
  Enable: Live Media Streaming
  Kinesis Video Stream prefix: salesforce-voice-transcription
  Retention period: 0 hours (transcription-only; no video storage needed)
  Save settings.

Step 2 — Salesforce Setup:
  Setup > Service Cloud Voice > Contact Centers > [Your Contact Center]
  Enable: Call Transcription toggle = ON
  Save.

Step 3 — Permission set:
  Assign "Service Cloud Voice Transcription" to supervisors
  who need the Transcript panel in the Service Console.

Step 4 — Validate:
  Place a test inbound call.
  Open the VoiceCall record during the active call.
  Confirm Transcript segments appear in near-real-time.
  Hang up and confirm the full transcript is persisted on the VoiceCall record.
```

**Why it works:** Amazon Connect streams live audio to Kinesis Video Streams when Live Media Streaming is enabled. Salesforce's transcription service consumes that stream and writes segments to the VoiceCall object. The Salesforce-side toggle alone does nothing without the upstream Kinesis stream being active.

---

## Anti-Pattern: Configuring Amazon Connect Directly Before Running the Salesforce Wizard

**What practitioners do:** An admin familiar with AWS logs into the AWS console, creates an Amazon Connect instance manually, configures phone numbers and contact flows in AWS, and then tries to "import" or "connect" this instance to Salesforce.

**What goes wrong:** The manually created Amazon Connect instance lacks the IAM trust role that Salesforce's wizard creates. The instance also does not have the Salesforce-managed contact flows installed (the flows that handle the handoff from Amazon Connect to Salesforce Omni-Channel). As a result, calls may reach Amazon Connect but never route to a Salesforce agent. The import path in the wizard requires the admin to have IAM admin permissions in AWS to grant Salesforce the required trust — a higher bar than greenfield provisioning.

**Correct approach:** Always start in Salesforce Setup > Service Cloud Voice > Contact Centers > New and let the wizard provision infrastructure. Only use the import path if there is an operational reason to reuse an existing Amazon Connect instance (e.g., existing customer phone numbers or contact flow investment), and ensure the importing admin has AWS IAM admin access to complete the trust grant.
