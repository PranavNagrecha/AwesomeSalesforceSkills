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

**How to tell, from the org, that this happened:** the symptom is calls that exist in Amazon Connect
and never become routable Salesforce work. Three queries separate the failure modes. Field names and
value sets are from the Object Reference `VoiceCall` section (object_reference.txt L306734–307520).

```sql
-- 1. Did any VoiceCall rows land at all? If zero, the AWS-to-Salesforce handoff never fired.
--    VendorType is always 'ContactCenter' for Salesforce Voice (object_reference.txt L307500-307509),
--    which also excludes Sales Dialer rows in a mixed org.
SELECT COUNT(Id) FROM VoiceCall
WHERE VendorType = 'ContactCenter' AND CreatedDate = LAST_N_DAYS:1

-- 2. Rows exist but are orphaned from the contact center: the CallCenter link is wrong.
SELECT Id, Name, CallCenterId, QueueName, CallDisposition, CallStartDateTime
FROM VoiceCall
WHERE VendorType = 'ContactCenter' AND CallCenterId = NULL
  AND CreatedDate = LAST_N_DAYS:1

-- 3. Rows are linked and queued but never accepted: routing reached Omni-Channel and stalled there
--    (no eligible agent, or the presence status has no channels). CallDisposition stays 'new'
--    until an agent accepts, at which point it becomes 'in-progress'
--    (object_reference.txt L306823-306841).
SELECT Id, Name, QueueName, CallDisposition, CallQueuedDateTime, DisconnectReason
FROM VoiceCall
WHERE VendorType = 'ContactCenter'
  AND CallQueuedDateTime != NULL AND CallAcceptDateTime = NULL
  AND CreatedDate = LAST_N_DAYS:1
ORDER BY CallQueuedDateTime DESC

-- 4. Are Salesforce agents mapped to vendor agents at all? An empty result here is the signature
--    of a hand-built Amazon Connect instance: transfers and availability checks have nothing
--    to resolve against. Access requires Salesforce Voice Contact Center Admin / Supervisor /
--    Manage Call Centers (object_reference.txt L56475-56477).
SELECT Id, DeveloperName, CallCenterId, ExternalId, ReferenceRecordId
FROM CallCenterRoutingMap
LIMIT 50
```

| Query result | What it means | Where to fix it |
|---|---|---|
| 1 returns 0 | No handoff from the vendor system into Salesforce | Contact center provisioning / vendor link (`ConversationVendorInfo`) |
| 1 > 0, 2 returns rows | Calls arrive but are not tied to the contact center record | `CallCenter` record and `VoiceCall.CallCenterId` population |
| 2 empty, 3 returns rows | Salesforce received and queued the work; Omni-Channel could not place it | `ServiceChannel`, `ServicePresenceStatus` channels, `PresenceUserConfig.capacity` |
| 4 empty in a transfer-using org | Agents and queues were never mapped to vendor identities | `CallCenterRoutingMap` (see `references/metadata-examples.md` §5) |

Run 1 through 4 in order and stop at the first one that answers; running them out of order produces a
plausible-looking diagnosis of the wrong layer.
