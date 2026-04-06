# LLM Anti-Patterns — Service Cloud Voice Setup

Common mistakes AI coding assistants make when generating or advising on Service Cloud Voice Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Instructing Admins to Configure Amazon Connect Directly in AWS Before Using the Salesforce Wizard

**What the LLM generates:** Instructions to log into the AWS console, create an Amazon Connect instance, configure contact flows, create phone numbers, and then "add the Salesforce integration" as a final step using a CTI adapter.

**Why it happens:** LLMs conflate Service Cloud Voice with Open CTI (the older, more widely documented telephony integration model). Training data contains more Open CTI and generic Amazon Connect documentation than Service Cloud Voice wizard-specific content. The LLM reconstructs a plausible-sounding sequence from those fragments.

**Correct pattern:**

```
Correct sequence:
1. Verify prerequisites in Salesforce (license, My Domain, Omni-Channel).
2. Navigate to Salesforce Setup > Service Cloud Voice > Contact Centers > New.
3. Complete the guided wizard — it provisions AWS infrastructure on your behalf.
4. Only access the AWS console after wizard completion for advanced customization
   (custom contact flows, additional phone numbers, live media streaming).
```

**Detection hint:** Look for instructions to "create an Amazon Connect instance" or "install the CTI adapter" as early steps in a Service Cloud Voice setup guide. If the AWS console appears before Salesforce Setup in the instructions, the sequence is likely wrong.

---

## Anti-Pattern 2: Omitting the Live Media Streaming AWS Prerequisite When Advising on Transcription Setup

**What the LLM generates:** Instructions that say only "enable Call Transcription in Setup > Service Cloud Voice > Contact Centers" without mentioning the Amazon Connect Live Media Streaming configuration required in AWS.

**Why it happens:** The Salesforce help documentation for transcription is the primary source, and that doc focuses on the Salesforce-side toggle. LLMs do not consistently model the cross-system dependency between the Salesforce toggle and the AWS console prerequisite.

**Correct pattern:**

```
Correct transcription setup sequence:
Step 1 — AWS console:
  Amazon Connect > [Your Instance] > Data Storage > Live Media Streaming
  Enable: ON
  Kinesis Video Stream: create or select existing
  Retention: 0 hours minimum (for transcription-only)

Step 2 — Salesforce Setup:
  Service Cloud Voice > Contact Centers > [Your Contact Center]
  Call Transcription: Enable toggle

Step 3 — Permission set:
  Assign "Service Cloud Voice Transcription" to supervisors
```

**Detection hint:** Any transcription setup guidance that does not mention "Live Media Streaming," "Kinesis Video Streams," or the AWS console is incomplete. Flag responses that describe only the Salesforce Setup path.

---

## Anti-Pattern 3: Advising That ACW Is Configured Only in the Global Setup Page

**What the LLM generates:** Instructions to navigate to Setup > After Conversation Work Time, set the maximum duration, and declare configuration complete — without mentioning that ACW must also be enabled on the individual contact center record.

**Why it happens:** The global Setup page for ACW exists and is the first visible surface in documentation. LLMs often generate guidance based on the most visible or most-documented path and miss secondary configuration steps that are performed on a different object (the contact center record).

**Correct pattern:**

```
ACW configuration requires two steps:

1. Setup > After Conversation Work Time
   Set maximum ACW duration (seconds)
   Save.

2. Setup > Service Cloud Voice > Contact Centers > [Your Contact Center]
   After Conversation Work Time: Enable
   Save.

Both steps are required. The global duration setting has no effect
if ACW is not also enabled on the contact center record.
```

**Detection hint:** ACW guidance that references only "Setup > After Conversation Work Time" without a second step on the contact center record is incomplete. Look for the phrase "enable on the contact center record."

---

## Anti-Pattern 4: Claiming Sandboxes Can Reuse the Production Amazon Connect Instance

**What the LLM generates:** Advice that a full-copy sandbox can be connected to the same Amazon Connect instance as production for testing purposes, framed as a cost-saving measure.

**Why it happens:** LLMs trained on general Salesforce sandbox guidance know that sandboxes share many org configurations with production. They incorrectly extrapolate this to external integrations like Amazon Connect. The one-to-one constraint between Salesforce orgs and Amazon Connect instances is a less-documented platform behavior.

**Correct pattern:**

```
Each Salesforce org (production, full-copy sandbox, partial sandbox,
developer sandbox) must have its own dedicated Amazon Connect instance.

For sandbox environments:
- Provision a new Amazon Connect instance via the sandbox's
  Setup > Service Cloud Voice > Contact Centers > New wizard.
- Use a separate AWS account or separate Amazon Connect instance alias.
- Budget for Amazon Connect costs for each sandbox environment.
```

**Detection hint:** Any suggestion to "point the sandbox at the production Amazon Connect instance" or "reuse the existing instance for testing" should be flagged as incorrect.

---

## Anti-Pattern 5: Conflating Service Cloud Voice Setup with CTI Adapter Installation

**What the LLM generates:** Instructions to install an AppExchange CTI package, configure a Call Center definition file, and assign agents to the Call Center. This is the Open CTI path, not the Service Cloud Voice path.

**Why it happens:** Open CTI and Service Cloud Voice both enable telephony in Salesforce, and Open CTI has been available much longer. LLM training data contains substantially more Open CTI documentation and community content than Service Cloud Voice content. When asked about "setting up voice" or "configuring phone," the LLM defaults to the more familiar pattern.

**Correct pattern:**

```
Service Cloud Voice (Amazon Connect) setup:
- No AppExchange package installation required.
- No Call Center definition file (callcenter.xml) required.
- Setup is entirely within Setup > Service Cloud Voice > Contact Centers.
- The phone widget appears automatically in the Service Console
  after the provisioning wizard completes and agents have
  the "Service Cloud Voice" permission set.

Open CTI (third-party telephony) is the correct path only when
using a non-Amazon telephony provider.
```

**Detection hint:** Look for mentions of "Call Center definition file," "callcenter.xml," "CTI adapter," or "assign users to Call Center" in Service Cloud Voice setup guidance. These are Open CTI concepts and do not apply to Service Cloud Voice.

---

## Anti-Pattern 6: Recommending Custom AWS Lambda Functions for Basic IVR Routing

**What the LLM generates:** Instructions to write AWS Lambda functions in Node.js or Python to implement business hours checks, queue routing, or call deflection for Service Cloud Voice.

**Why it happens:** Amazon Connect documentation frequently references Lambda for data dip use cases (fetching CRM data from external systems). LLMs over-apply this pattern to basic routing scenarios that Amazon Connect contact flows can handle natively without Lambda.

**Correct pattern:**

```
For common IVR scenarios in Service Cloud Voice:
- Business hours routing: Use Amazon Connect's built-in
  "Check Hours of Operation" contact flow block.
- Queue-based routing: Use Omni-Channel queue configuration
  in Salesforce, not Lambda.
- Basic call deflection (press 1 for X): Use Amazon Connect
  contact flow "Get Customer Input" blocks.

Lambda is appropriate only when:
- Data must be fetched from a system Amazon Connect cannot
  natively reach (non-Salesforce systems).
- Custom authentication or token generation is required.
```

**Detection hint:** Lambda function code in Service Cloud Voice setup guidance for scenarios like business hours, simple menus, or queue routing indicates over-engineering. Flag and replace with native Amazon Connect flow block approaches.
