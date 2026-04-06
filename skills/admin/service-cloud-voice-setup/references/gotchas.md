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
