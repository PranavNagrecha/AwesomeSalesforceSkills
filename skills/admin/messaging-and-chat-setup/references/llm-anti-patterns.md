# LLM Anti-Patterns — Messaging and Chat Setup

Common mistakes AI coding assistants make when generating or advising on Messaging and Chat Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Live Agent or Snap-ins for New Chat Implementations

**What the LLM generates:** Step-by-step instructions to configure Live Agent Chat Buttons, create a Live Agent Deployment, and embed the Snap-ins JavaScript snippet. The response may reference `LiveChatTranscript`, Chat Buttons, and the `embedded_svc.settings` initialization object.

**Why it happens:** Live Agent was the dominant Salesforce chat product for many years and dominates pre-2023 training data. LLMs pattern-match "set up Salesforce chat" to the most frequently documented path, which is Live Agent. MIAW documentation is newer and less represented.

**Correct pattern:**
```
For new chat implementations, use Messaging for In-App and Web (MIAW):
  Setup > Messaging Settings > Enable Messaging for In-App and Web
  Setup > Messaging > Messaging Channels > New (type: Messaging for In-App and Web)
  Setup > Embedded Service Deployments > New (type: Messaging for In-App and Web)
Do NOT use Setup > Chat (Live Agent) for new deployments.
```

**Detection hint:** Any response that references `LiveChatTranscript`, `LiveChatButton`, `LiveAgent.showWhenOnline()`, `embedded_svc.init()`, or "Chat Deployment" (the legacy object) is using the wrong product for a new MIAW implementation.

---

## Anti-Pattern 2: Adding Only a CORS Trusted Site Without a Matching CSP Entry

**What the LLM generates:** Instructions to fix a widget loading failure by adding a CORS Trusted Site entry. The response stops there, treating CORS as the only trust mechanism needed.

**Why it happens:** CORS errors are visible and named in browser DevTools. CSP violations appear as a separate error type that is easy to overlook. LLMs trained on general web development content know CORS well but may not know that Salesforce Lightning enforces a separate CSP allow-list that also must be updated.

**Correct pattern:**
```
For every widget domain, add BOTH:
  1. Setup > CORS > New: https://your-domain.com
  2. Setup > CSP Trusted Sites > New: https://your-domain.com (Context: All)
These are independent allow-lists. Missing either one blocks the widget.
```

**Detection hint:** Any response that mentions CORS Trusted Sites without also mentioning CSP Trusted Sites (or vice versa) is incomplete for MIAW widget domain registration.

---

## Anti-Pattern 3: Assuming Pre-Chat Fields Auto-Link a Contact

**What the LLM generates:** Instructions to add Email as a pre-chat field on the Messaging Channel and a statement that "the session will automatically be linked to the matching Contact." The response implies no further automation is needed.

**Why it happens:** Salesforce Service Cloud does have some automatic contact matching in other contexts (e.g., email-to-case). LLMs over-generalize this behavior to MIAW pre-chat fields, which do not perform automatic Contact lookups.

**Correct pattern:**
```
Pre-chat fields collect data and store it on the MessagingSession record.
Automatic Contact linking does NOT happen.
To link a Contact, create an Omni-Channel Flow or Apex trigger on MessagingSession (after insert)
that queries Contact WHERE Email = :session.PreChatFormData__Email
and updates MessagingSession.ContactId.
```

**Detection hint:** Any response that claims pre-chat fields "automatically match" or "look up" a Contact without describing a Flow or trigger is incorrect.

---

## Anti-Pattern 4: Treating Status-Based Capacity as a Per-Channel Setting

**What the LLM generates:** Instructions to "enable Status-Based capacity for the Messaging channel" in the Embedded Service Deployment settings or on the Messaging Channel record. The response implies the setting is scoped to messaging only and will not affect voice or chat.

**Why it happens:** Per-channel configuration is a natural expectation. LLMs may infer that routing and capacity settings on the Messaging Channel record are fully isolated from other channels.

**Correct pattern:**
```
Status-Based capacity is an ORG-WIDE setting in Omni-Channel Settings.
Enabling it affects ALL Omni-Channel channels: messaging, voice, chat, email.
Before enabling:
  1. Audit all existing Presence Configurations.
  2. Set numeric capacity values for every channel type.
  3. Test in sandbox with realistic concurrent load across all channels.
```

**Detection hint:** Any response that says to enable Status-Based capacity "for messaging" or "on the Messaging Channel" without noting it is org-wide is misleading.

---

## Anti-Pattern 5: Routing MIAW Sessions via Apex Triggers Instead of Omni-Channel Flows

**What the LLM generates:** An Apex trigger on `MessagingSession` (before insert or after insert) that queries a queue and calls `System.enqueueJob()` or sets the `QueueId` field to implement conditional routing logic.

**Why it happens:** Apex triggers are a familiar pattern for Salesforce developers. LLMs default to code-first solutions when "routing logic" is mentioned, even when a declarative platform feature (Omni-Channel Flow) is purpose-built for the use case.

**Correct pattern:**
```
Use an Omni-Channel Flow (Flow Type: Omni-Channel) for conditional MIAW routing.
Omni-Channel Flows:
  - Run before session assignment (not after)
  - Have native access to pre-chat field values
  - Can call Route Work actions to assign to queues or agents
  - Support fault paths and fallback routing
Apex triggers on MessagingSession fire after the record is created,
which is too late to influence the initial routing assignment cleanly.
```

**Detection hint:** Any response that writes an Apex trigger on `MessagingSession` with routing logic should be challenged. Omni-Channel Flows are the platform-native routing mechanism and should be the first recommendation.

---

## Anti-Pattern 6: Skipping the Fallback Queue When Configuring Omni-Channel Flow Routing

**What the LLM generates:** A complete Omni-Channel Flow setup with routing branches — but no instruction to configure the fallback queue on the Messaging Channel record. The response treats the Flow as sufficient and does not address what happens when the Flow fails.

**Why it happens:** LLMs focus on the happy path. Error handling and fallback configuration are secondary concerns that get omitted when the primary task (routing logic) is described.

**Correct pattern:**
```
After configuring an Omni-Channel Flow on a Messaging Channel:
  1. Open the Messaging Channel record.
  2. In the Routing section, set Fallback Queue to a valid queue.
  This queue receives sessions when the Flow faults or produces no routing output.
  Without it, failed routing leaves the session stranded with no error surfaced.
```

**Detection hint:** Any response that configures Omni-Channel Flow routing without also confirming or setting the fallback queue on the Messaging Channel record is incomplete.
