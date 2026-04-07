---
name: email-studio-administration
description: "Use when building, configuring, or troubleshooting email sends in Marketing Cloud Email Studio and Content Builder. Triggers: 'dynamic content', 'send classification', 'A/B test email', 'Content Builder template', 'triggered send', 'suppression list', 'Commercial vs Transactional'. NOT for MCAE (Pardot) email, SMS/push channel setup, or Journey Builder orchestration design."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "how do I set up dynamic content blocks that swap based on subscriber attributes"
  - "email send classification difference between Commercial and Transactional"
  - "A/B test winner selection is not firing on schedule"
  - "suppression list not excluding unsubscribed contacts from send"
  - "Content Builder template not showing correct footer on send"
  - "triggered send failing or emails not delivering"
  - "spam score too high flagged by Content Detective before approval"
tags:
  - email-studio
  - content-builder
  - dynamic-content
  - send-classification
  - ab-testing
  - triggered-sends
  - suppression-lists
  - marketing-cloud
inputs:
  - "Business unit context and subscriber data extension structure"
  - "Send type requirement: triggered, scheduled, or Journey Builder"
  - "Commercial vs Transactional classification intent"
  - "Subscriber attribute fields used for dynamic content rules"
  - "Suppression requirements (global, publication, or auto)"
outputs:
  - "Email build approach and Content Builder configuration guidance"
  - "Send Classification design with Commercial/Transactional rationale"
  - "Dynamic content rule structure for zero-version-proliferation sends"
  - "A/B test setup with winner criteria and split percentages"
  - "Pre-send validation checklist (Content Detective, inbox preview, approval)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Email Studio Administration

This skill activates when a practitioner is creating, configuring, or troubleshooting email builds and sends in Salesforce Marketing Cloud Email Studio and Content Builder. It covers email creation methods, dynamic content, send classifications, A/B testing, suppression lists, triggered vs scheduled sends, and pre-send validation. It does NOT cover MCAE (Pardot) email, SMS or push channel configuration, or the Journey Builder entry-source and decision-split design.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Business unit setup**: Which Marketing Cloud Business Unit owns this send? Send classifications, suppression lists, and SAP IP addresses are scoped to a business unit.
- **Data Extension or List structure**: Dynamic content rules and subscriber segmentation depend on which subscriber attributes or DE fields are populated and typed correctly.
- **Legal classification of the email**: Determine early whether the email is Commercial (marketing offer, newsletter) or Transactional (order confirmation, password reset). This drives which Send Classification to use and whether CAN-SPAM footer + global unsubscribe handling is required.
- **Most common wrong assumption**: Teams assume that building multiple email versions is required to support different subscriber segments — dynamic content blocks eliminate this need entirely.
- **Platform constraints**: Content Builder has no hard limit on the number of dynamic content blocks per email, but extremely complex rule trees (20+ conditions) slow template rendering in the preview pane and should be tested.

---

## Core Concepts

### Content Builder vs Classic Email Studio

Marketing Cloud offers two email creation environments. Classic Email Studio is the legacy tool. Content Builder is the current authoring environment and is used for all new email development.

Content Builder supports two build methods:
- **Drag-and-drop blocks**: Assembles emails from pre-built content blocks (text, image, button, HTML). Each block is independently editable. Block-level permissions can restrict who changes certain areas.
- **Raw HTML**: A single HTML code block allows full control over markup. Required for pixel-perfect rendering or legacy template migration.

Classic Email Studio remains accessible but Salesforce has directed all new development toward Content Builder. Classic templates cannot natively consume Content Builder dynamic blocks.

### Dynamic Content Blocks

A Dynamic Content block is a container inside a Content Builder email that evaluates rules at send time against subscriber data — attributes on the subscriber record or fields in a sendable Data Extension. Based on which rule matches first (rules evaluate top-to-bottom), the block displays one of the pre-defined content variations. If no rule matches, a default variation is shown.

Key behaviors:
- Rules evaluate at **send time**, not at build time. Subscriber data at the moment the email is processed determines which block renders.
- Only one variation per block renders per subscriber. The first matching rule wins.
- Dynamic content eliminates the need to maintain separate email versions per segment. One email definition serves all segments.
- Rule criteria support subscriber attribute comparisons (equals, contains, starts with, is not empty) and date-based rules.
- Dynamic content rules reference **Profile Attributes** or **Data Extension fields** — they cannot reference journey or send-time context variables directly.

### Send Classifications

A Send Classification is the configuration object that controls the legal and deliverability behavior of every email send. It bundles three components:

1. **Sender Profile**: Defines the From Name and From Address the subscriber sees.
2. **Delivery Profile**: Associates the physical mailing address (required by CAN-SPAM), the SAP (Sending Authentication Package) IP affinity, and the reply mail management settings.
3. **Unsubscribe Profile**: Determines whether an unsubscribe triggers a global unsubscribe (removes from all commercial sends) or only removes from the specific publication list.

**Commercial Send Classification**: Requires a CAN-SPAM-compliant footer (physical mailing address + unsubscribe link). Global unsubscribes from commercial sends are applied across the business unit. Required for marketing, promotional, or newsletter emails.

**Transactional Send Classification**: CAN-SPAM footer is not required. Unsubscribes from transactional sends do NOT trigger a global unsubscribe — they are recorded separately. Used only for genuine transactional messages (receipts, password resets, shipping notifications). Misusing Transactional to bypass unsubscribe requirements violates CAN-SPAM and can result in ISP blocklisting.

### A/B Testing

Email Studio A/B testing allows controlled comparison of two email variants on a portion of the audience before sending the winner to the remainder.

Supported test dimensions:
- **Subject line**: Test two subject lines; winner selected by open rate.
- **From name**: Test two sender identities; winner selected by open rate.
- **Content**: Test two distinct email bodies; winner selected by click rate or open rate.
- **Send time**: Test two delivery times; winner selected by open rate.

Test configuration:
- Define the test audience split (e.g., 10% receives version A, 10% receives version B, 80% is the holdout for the winner).
- Set the winner selection criteria (open rate, click rate, or manual).
- Set the evaluation window before winner determination (e.g., 4 hours, 24 hours).
- Winner send fires automatically at the end of the evaluation window if auto-send is enabled.

### Suppression Lists

Marketing Cloud enforces three suppression tiers on every send:

1. **Auto-Suppression (system-enforced)**: Addresses that have globally unsubscribed, hard-bounced, or been marked as spam complaints are automatically excluded. Cannot be overridden by a send.
2. **Publication List Suppression**: Contacts who have unsubscribed from a specific publication list are suppressed from sends using that list, but may still receive other commercial sends.
3. **Global Suppression List (GSL)**: A business unit-level or enterprise-level suppression list. Any address on the GSL is excluded from all sends regardless of send classification.

Suppression lists stack — an address excluded by any tier is excluded from the send.

---

## Common Patterns

### Pattern 1: Dynamic Content for Segmented Personalization

**When to use:** The business wants to show different offers, images, or copy to different subscriber segments (e.g., loyalty tier, geography, or preferred product category) without maintaining multiple email versions.

**How it works:**
1. In Content Builder, add a Dynamic Content block at the position where content should vary.
2. Create one content variation per segment condition (e.g., "LoyaltyTier equals Gold").
3. Order rules from most specific to least specific — the first matching rule wins.
4. Set a default variation for subscribers who match no rule.
5. Use test preview with a representative subscriber from each segment to confirm correct variation renders.

**Why not the alternative:** Building separate email records per segment multiplies your operational surface — every copy change requires updating N emails, approval workflows multiply, and reporting is fragmented across sends.

### Pattern 2: Commercial vs Transactional Classification Decision

**When to use:** Anytime a new send type is introduced or an existing send is reviewed for compliance posture.

**How it works:**
1. Ask: "Is the subscriber's primary motivation to receive this email commercial (marketing intent) or operational (they need this to complete a transaction)?"
2. If commercial: assign a Commercial Send Classification with a CAN-SPAM-compliant footer and publication list.
3. If transactional: assign a Transactional Send Classification, omit the unsubscribe footer, and confirm the email content qualifies (no promotional offers embedded).
4. Document the classification rationale in the send definition for future compliance review.

**Why not the alternative:** Mis-classifying marketing emails as Transactional to suppress the unsubscribe footer violates CAN-SPAM and can result in ISP complaints, ESP contract violations, and regulatory fines.

### Pattern 3: Pre-Send Validation Pipeline

**When to use:** Every email send before it goes to a live list, regardless of audience size.

**How it works:**
1. Run **Content Detective** from Email Studio — it scans for spam trigger words and phrases in subject line and body and reports a spam score.
2. Send a **test send** to a seed list that includes inboxes across major ISPs (Gmail, Outlook, Apple Mail) and internal approver addresses.
3. Use **Inbox Preview** (Litmus integration) to render the email across 40+ client/device combinations.
4. If an **approval workflow** is enabled for the business unit, submit the send definition for manager sign-off before activation.
5. Confirm dynamic content variations rendered correctly in the test send by seeding subscriber data for each rule condition.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One-time batch send to a static list on a fixed date | Scheduled send in Email Studio | Simplest path; full pre-send validation available |
| Email triggered by a real-time system event (e.g., purchase confirmation) | Triggered Send definition | Fires on API call or automation; decoupled from batch scheduling |
| Multi-step nurture sequence with waits and branching | Journey Builder with Email Studio content | Journey controls timing and branching; Email Studio owns content |
| Same email, multiple content variations by segment | Single email with Dynamic Content blocks | Zero version proliferation; segment logic in the block not in the send list |
| Testing subject line impact before full send | A/B test in Email Studio | Native winner selection by open rate; holdout send fires automatically |
| Marketing newsletter (commercial offer) | Commercial Send Classification | Requires CAN-SPAM footer; global unsubscribe enforced |
| Order confirmation or password reset | Transactional Send Classification | No unsubscribe footer required; unsubscribes recorded separately |
| Excluding former customers from all sends | Global Suppression List | Auto-applied to every send; cannot be bypassed by individual send configuration |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm legal classification** — Determine whether the email is Commercial or Transactional before building anything. Changing the classification after a send has gone out does not retroactively fix compliance exposure.
2. **Design the content structure** — Identify which sections need dynamic content blocks. Map the rule conditions to available subscriber attributes or Data Extension fields. Confirm default variations exist for every dynamic block.
3. **Build in Content Builder** — Use drag-and-drop blocks for standard layouts or raw HTML for pixel-perfect control. Attach the correct Send Classification. Define From Name, From Address, and Subject Line.
4. **Configure suppression** — Confirm the publication list and verify any Global Suppression List is active. For Triggered Sends, confirm auto-suppression is not being bypassed via API override.
5. **Pre-send validation** — Run Content Detective, send a test to the seed list, run Inbox Preview for cross-client rendering, and submit for approval if the workflow requires it.
6. **Schedule or activate** — For scheduled sends, set the send date and confirm the audience Data Extension is populated. For triggered sends, activate the Triggered Send Definition and test the API trigger end-to-end.
7. **Post-send review** — Check deliverability metrics (bounce rate, unsubscribe rate, spam complaint rate) within 24 hours. Bounce rates above 2% or complaint rates above 0.1% require immediate suppression list review.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Send Classification assigned and confirmed as Commercial or Transactional based on email content
- [ ] CAN-SPAM footer present and correct for Commercial sends; absent or minimal for Transactional
- [ ] Every Dynamic Content block has a valid default variation
- [ ] Dynamic content rules tested with subscriber data representative of each segment condition
- [ ] Content Detective run and spam score is acceptable (no red-flag trigger words in subject or body)
- [ ] Test send delivered to seed list and approved by email owner
- [ ] Inbox Preview completed for primary client/device targets
- [ ] Global Suppression List active and suppressed address count reviewed
- [ ] For A/B tests: winner criteria, evaluation window, and holdout percentage confirmed before activation
- [ ] For Triggered Sends: Triggered Send Definition is Active and API trigger tested end-to-end

---

## Salesforce-Specific Gotchas

1. **Transactional classification does not protect against CAN-SPAM if content is commercial** — ISPs and regulators evaluate the email content, not the classification field. A promotional email sent under a Transactional classification is still a commercial email under CAN-SPAM and CASL. The classification controls unsubscribe handling mechanics, not legal compliance.
2. **Dynamic content rules evaluate top-to-bottom and stop at first match** — If a "Gold" tier rule appears below a generic "has a loyalty number" rule, every loyalty subscriber will match the generic rule first. Always order rules from most specific to most general with a catch-all default at the bottom.
3. **A/B test winner does not auto-send if the evaluation window expires without sufficient data** — If the test audience is too small to achieve statistical separation within the window, the system may not declare a winner. Configure a fallback: either extend the window, lower the significance threshold, or select manual winner selection for small lists.
4. **Triggered Send Definitions must be Activated before they can fire** — A common support pattern is a Triggered Send that sits in "Building" status and silently drops all API-triggered messages. After building, the definition must be explicitly Activated from the UI.
5. **Suppression list changes are not retroactive to in-flight sends** — Adding an address to the Global Suppression List after a send job has started does not exclude it from that send job. For time-critical suppressions, pause the send job first, update the suppression list, then resume.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Send Classification design | Commercial vs Transactional recommendation with Sender Profile, Delivery Profile, and Unsubscribe Profile configuration |
| Dynamic content rule map | Ordered rule conditions mapped to subscriber attributes with default variation specified |
| A/B test configuration | Test dimension, split percentages, evaluation window, winner criteria, and holdout configuration |
| Pre-send validation checklist | Completed checklist covering Content Detective, seed send, Inbox Preview, and approval status |
| Suppression list review | Active suppression tiers confirmed with auto-suppression, publication-level, and global suppression verified |

---

## Related Skills

- admin/email-templates-and-alerts — Use when the email content requirement is a Salesforce Core notification (workflow email alert, Flow send email action), not a Marketing Cloud Email Studio send.
- admin/mcae-pardot-setup — Use when the marketing automation platform is Pardot/MCAE, not Marketing Cloud Engagement. Email Studio and MCAE are separate products with separate sending infrastructure.
- admin/flow-for-admins — Use when email triggering logic needs to originate from Salesforce Core automation (Flow, Process Builder) rather than Marketing Cloud Automation Studio or API.
