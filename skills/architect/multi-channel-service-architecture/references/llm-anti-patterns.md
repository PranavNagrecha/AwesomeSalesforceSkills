# LLM Anti-Patterns — Multi Channel Service Architecture

Common mistakes AI coding assistants make when generating or advising on Multi Channel Service Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Live Agent for New Implementations

**What the LLM generates:** Instructions to set up Live Agent chat buttons, `LiveChatTranscript` objects, and legacy snap-in code for new chat channel deployments.

**Why it happens:** Training data overwhelmingly contains Live Agent documentation and examples from before Spring '24. LLMs default to the most frequently seen pattern, which is the legacy approach.

**Correct pattern:**

```text
Use Messaging for In-App and Web (GA Spring '24) for all new chat implementations.
Configure an Embedded Service deployment with a Messaging channel.
The object model uses MessagingSession, MessagingEndUser, and MessagingChannel.
Live Agent (LiveChatTranscript, LiveChatButton) is legacy and should only
appear in migration plans, not new designs.
```

**Detection hint:** Any mention of `LiveChatTranscript`, `LiveChatButton`, `Live Agent` as a recommendation (not migration context) in new implementation guidance.

---

## Anti-Pattern 2: Treating All Channels as Equal Capacity

**What the LLM generates:** Omni-Channel configuration advice that assigns the same capacity weight (e.g., 10) to all Service Channels, or omits capacity weight configuration entirely.

**Why it happens:** LLMs generate generic Omni-Channel setup steps without accounting for the fact that different channels consume agent bandwidth differently. Phone calls are full-attention; chats allow concurrency.

**Correct pattern:**

```text
Assign capacity weights reflecting actual agent bandwidth consumption:
  - VoiceCall (phone): weight 100 (full agent capacity)
  - MessagingSession (chat): weight 25-33 (3-4 concurrent sessions)
  - Case from Email-to-Case: weight 10-15 (background work)
  - Case from Social: weight 20-25 (similar to chat)
  - MessagingSession (SMS): weight 20-25 (asynchronous, less urgent)

Agent total capacity: 100 units.
Tune weights based on observed average handle time per channel.
```

**Detection hint:** All Service Channels sharing identical capacity weight values, or capacity weight not mentioned in multi-channel Omni-Channel guidance.

---

## Anti-Pattern 3: Confusing Email-to-Case Variants

**What the LLM generates:** Instructions mixing on-demand Email-to-Case setup steps with org-wide Email-to-Case setup steps, or recommending org-wide as the default without explaining the tradeoff.

**Why it happens:** Both variants exist in documentation and LLMs merge them. On-demand is the simpler, more common approach but org-wide appears in older training data. LLMs do not distinguish which is appropriate for the user's context.

**Correct pattern:**

```text
Email-to-Case has two variants:

On-Demand Email-to-Case (recommended for most orgs):
  - No software to install
  - Emails forwarded to a Salesforce-generated routing address
  - 25 MB email size limit
  - Processes emails at a configurable rate

Org-Wide Email-to-Case:
  - Requires email relay through your mail server
  - Emails processed behind your firewall before reaching Salesforce
  - Use only when compliance requires email to pass through your infrastructure

Default to on-demand unless there is a specific compliance or infrastructure
requirement for org-wide.
```

**Detection hint:** Email-to-Case instructions that mention "download the Email-to-Case agent" (org-wide step) without explicitly stating this is the org-wide variant, or mixing routing addresses with relay configuration.

---

## Anti-Pattern 4: Referencing Social Studio as Current

**What the LLM generates:** Recommendations to use Social Studio for social media channel management, including Social Studio listen, engage, and publish features.

**Why it happens:** Social Studio was a prominent Salesforce product for years and is heavily represented in training data. LLMs do not know or reflect that Social Studio is retiring and being replaced by Social Customer Service for case-based social interactions.

**Correct pattern:**

```text
Social Studio is retiring. For social media service channels:
  - Use Social Customer Service to create Cases from social media posts
  - Social Customer Service integrates with Twitter/X and Facebook
  - Cases created from social posts route through Omni-Channel like any other case
  - For social listening and marketing, evaluate third-party tools or
    Salesforce Marketing Cloud Social (separate product)
```

**Detection hint:** Any mention of "Social Studio" as a current recommendation rather than a legacy/retiring product.

---

## Anti-Pattern 5: Designing Channel-Specific Queues Instead of Topic-Based Queues

**What the LLM generates:** Omni-Channel queue design with queues named "Phone Queue," "Chat Queue," "Email Queue" — one queue per channel rather than per business topic.

**Why it happens:** Channel-per-queue is an intuitive first design that LLMs generate because it mirrors how channels are discussed (separately). Training data often shows single-channel examples that get extrapolated into multi-channel designs.

**Correct pattern:**

```text
Design queues by business topic, not by channel:
  - Billing_Support (receives phone, chat, email, SMS billing cases)
  - Technical_Support (receives phone, chat, email technical cases)
  - Returns_Processing (receives email, chat returns cases)

Each queue is assigned to agents with the relevant skills.
Omni-Channel routes work from any channel to any available agent in
the appropriate topic queue, with capacity weights controlling how
many of each channel type the agent handles simultaneously.
```

**Detection hint:** Queue names containing channel identifiers (Phone, Chat, Email, Voice, Messaging) rather than business domain terms.

---

## Anti-Pattern 6: Omitting the Unified Case Timeline Requirement

**What the LLM generates:** Multi-channel architecture guidance that describes each channel's setup independently without addressing how all channel interactions converge on a single Case record for a unified customer view.

**Why it happens:** LLMs describe each channel as a standalone feature because that is how documentation is structured — each channel has its own help article. The cross-channel data model linking VoiceCall, MessagingSession, and Case is not prominent in training data.

**Correct pattern:**

```text
All channels must create or link to the Case object:
  - Email-to-Case: creates Case directly
  - Service Cloud Voice: creates VoiceCall linked to Case via RelatedRecordId
  - Messaging for In-App/Web: creates MessagingSession linked to Case
  - Social Customer Service: creates Case from social post
  - SMS Messaging: creates MessagingSession linked to Case

The Case Feed (Lightning) surfaces all related interactions as a
unified timeline. Verify that each channel's object has a lookup
or master-detail to Case, and that the Case Feed layout includes
components for all channel types.
```

**Detection hint:** Multi-channel design that describes channel setup without mentioning Case as the unifying object or "unified timeline" / "single customer view."
