---
name: email-to-case-configuration
description: "Configuring Salesforce Email-to-Case: Standard vs On-Demand mode selection, routing address setup, email threading via Lightning tokens, auto-response rules, attachment limits, and per-address case field defaults. Use when setting up a new Email-to-Case channel, troubleshooting duplicate cases from customer replies, or choosing between On-Demand and Standard mode. Trigger keywords: email-to-case, routing address, on-demand email-to-case, email threading, case from email, email agent, routing address setup. NOT for email templates or letterheads (use email-templates-and-alerts). NOT for Omni-Channel routing of case work items after creation (use omni-channel-routing-setup). NOT for Web-to-Case or inbound-only chat channels."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "customer reply to a case email is creating a new case instead of threading into the original"
  - "should I use On-Demand Email-to-Case or Standard Email-to-Case and what is the difference"
  - "how do I set up a routing address so inbound support emails create cases automatically"
tags:
  - email-to-case
  - routing-address
  - on-demand-email-to-case
  - email-threading
  - service-cloud
  - case-creation
  - auto-response-rules
inputs:
  - "Service Cloud org with Cases enabled"
  - "Decision on Email-to-Case mode: On-Demand (recommended) or Standard (requires local agent)"
  - "Inbound email address(es) to map to cases (e.g., support@company.com)"
  - "Case field defaults per routing address: origin, status, priority, queue or owner"
  - "Whether auto-response emails are required on case creation"
outputs:
  - "Enabled Email-to-Case feature with On-Demand mode configured"
  - "One or more verified routing addresses mapped to inbound support mailboxes"
  - "Mail server forward rule directing inbound mail to Salesforce routing address"
  - "Email threading tested end-to-end (reply threads into parent case)"
  - "Auto-response rule firing correctly when assignment rule fires"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Email-to-Case Configuration

This skill activates when an admin needs to configure or troubleshoot Salesforce Email-to-Case: enabling the feature, choosing between Standard and On-Demand mode, creating and verifying routing addresses, ensuring customer reply emails thread into the originating case rather than creating duplicates, and setting per-address case defaults and auto-response behavior.

---

## Before Starting

Gather this context before working on Email-to-Case configuration:

- **Which Email-to-Case mode is appropriate?** On-Demand is the default choice for most orgs. It uses Salesforce-hosted Apex Email Services and requires no locally installed agent. Standard Email-to-Case requires a downloadable Java agent running on a server inside the company firewall; it keeps email traffic internal but adds operational overhead. Choose Standard only if security policy or data residency rules prohibit email routing through Salesforce infrastructure.
- **What are the attachment size limits?** Both modes support a maximum total inbound email size of 25 MB. However, On-Demand Email-to-Case caps individual attachments at 10 MB per attachment. Emails exceeding the total size limit are rejected. Standard Email-to-Case does not have the individual attachment cap.
- **Is email threading the top priority?** Threading is the single most commonly misconfigured behavior. Salesforce embeds a Lightning token (a unique thread ID) in the body and subject of every outgoing case email. When a customer replies, Salesforce reads this token to locate the parent case and adds the reply as an Email Message record. If the token is stripped by a mail server, a security gateway, or an incorrect routing address configuration, every reply creates a new case.
- **Are auto-response rules needed?** Auto-response rules only fire when the active case assignment rule fires. Confirm an assignment rule is active and will match the cases created by Email-to-Case before configuring auto-response rules.

---

## Core Concepts

### Standard vs On-Demand Email-to-Case

Email-to-Case has two operating modes with distinct infrastructure requirements:

**Standard Email-to-Case** uses a locally installed Java agent. The agent polls the company mail server, converts inbound emails to cases, and pushes them to Salesforce via the API. Email traffic travels from the customer to the company mail server and remains inside the corporate network — it never routes through Salesforce infrastructure before case creation. This matters for orgs with strict data residency or email content classification requirements. The agent requires a server to run on, must be kept online, and consumes Salesforce API calls for every email processed.

**On-Demand Email-to-Case** uses Salesforce-hosted Apex Email Services. Salesforce generates a unique routing address in the format `[unique-id]@[instance].salesforce.com`. The company configures its mail server to forward inbound email from the public support address (e.g., `support@company.com`) to this Salesforce address. Email content, including attachments, travels through Salesforce's email infrastructure before the case is created. No local agent is required. This is the recommended mode for the majority of orgs.

The individual attachment limit difference is important: On-Demand caps each attachment at 10 MB; Standard does not enforce this per-attachment cap, though both enforce the 25 MB total email size cap.

### Email Threading via Lightning Tokens

Every case email sent through Salesforce contains a hidden Lightning thread token. The token appears in two locations: embedded in the email body (usually as a reference string below the visible content) and in the email subject line (as a `[ref:...:ref]` suffix). Both locations serve as fallbacks.

When a customer replies, Salesforce's inbound processing inspects the reply for a matching token. If found, the reply is appended to the originating case as a new Email Message record. If not found, a new case is created. Threading failures occur when:

- The mail server or security gateway strips or modifies the reference string in the body or subject.
- The customer uses a mail client that strips quoted content (removing the body token) AND modifies the subject line (removing the subject token).
- The routing address is misconfigured and inbound mail is not matched to the correct Email-to-Case configuration.

Always test threading end-to-end before go-live: send an inbound email, confirm case creation, reply from the case in Salesforce, have the reply delivered to the customer's inbox, and reply back. The reply must add an Email Message to the original case, not create a new case.

### Routing Addresses

A routing address is a per-mailbox Email-to-Case configuration record. Each routing address defines:

- The external email address customers use (`emailAddress` — the address your mail server forwards from).
- The Salesforce-generated target address (On-Demand mode only) that the mail server forwards to.
- Default values applied to cases created via this address: Case Origin, Status, Priority, and optionally a queue or owner.
- Whether an auto-response is sent and which auto-response rule entries apply.

An org can have multiple routing addresses, one per inbound support channel (e.g., `support@`, `billing@`, `returns@`). Each address creates cases with its own defaults, allowing cases to be pre-classified by channel before assignment rules run.

### Auto-Response Rules and Assignment Rule Dependency

Auto-response rules send confirmation emails to customers when cases are created. They are not independent: an auto-response rule entry fires only when the active case assignment rule fires for the same case creation event. If no assignment rule is active, or if no rule entry matches the incoming case, the auto-response will not fire regardless of auto-response rule configuration.

This dependency is the most commonly misdiagnosed "auto-response not sending" issue.

---

## Common Patterns

### Pattern: On-Demand Email-to-Case with Verified Threading

**When to use:** Configuring Email-to-Case for the first time in an org with no local email agent requirement.

**How it works:**
1. Navigate to Setup → Email-to-Case. Click Edit and enable Email-to-Case. Select "Enable On-Demand Service" to activate On-Demand mode.
2. Save. Return to Email-to-Case settings. Under Routing Addresses, click New.
3. Enter the routing address name (for display), the email address customers use (e.g., `support@company.com`), and the default Case Origin, Status, and Priority for cases created from this address.
4. Save the routing address. Salesforce generates a Salesforce-hosted email address. Copy this address.
5. Configure the company mail server to forward inbound mail from `support@company.com` to the Salesforce-generated address.
6. Click "Send Verification Email" on the routing address to confirm Salesforce can receive at that address. Verify the address in the confirmation email.
7. Test threading: send an email to `support@company.com`, confirm a case is created in Salesforce, send a reply from the case, deliver it to an inbox, and reply back. The reply must append to the original case as an Email Message, not create a new case.

**Why not Standard Email-to-Case:** Standard requires a local agent, server maintenance, and consumes API calls per email. On-Demand is fully hosted and requires only a mail forwarding rule.

### Pattern: Multiple Routing Addresses for Channel-Based Case Classification

**When to use:** The org has multiple inbound support email addresses (e.g., billing, technical, returns) and needs cases created from each address to have different default fields or route to different queues.

**How it works:**
1. Create one routing address per inbound channel, each with appropriate default Case Origin, Status, and Priority.
2. In the case assignment rule, add rule entries that match on Case Origin (or a custom field set by the routing address) and route to the appropriate queue.
3. Each address generates its own Salesforce-hosted routing address (On-Demand). Configure a separate forwarding rule on the mail server for each address.
4. Test each channel independently to confirm cases arrive with correct defaults.

**Why not a single routing address with automation:** A single address cannot set per-channel defaults natively. Using multiple addresses keeps classification at the point of creation rather than requiring post-creation automation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New Email-to-Case setup with no local infrastructure requirement | On-Demand Email-to-Case | No agent to install or maintain; fully Salesforce-hosted |
| Org policy prohibits email content routing through external infrastructure | Standard Email-to-Case with local agent | Email stays inside corporate network before case creation |
| Customer replies create new cases instead of threading | Verify Lightning token in outgoing email body and subject; check mail server for token stripping | Threading depends on token surviving round-trip through customer's mail client and company gateway |
| Individual attachment larger than 10 MB fails in On-Demand mode | Switch to Standard Email-to-Case OR ask customers to send smaller attachments | On-Demand caps individual attachments at 10 MB; Standard does not |
| Auto-response email not sent on case creation | Confirm an active assignment rule exists and matches the case | Auto-response only fires when assignment rule fires |
| Cases created via Email-to-Case land with default case owner, not a queue | Add a catch-all entry to the assignment rule pointing to the correct queue | Assignment rule must be active and matching for cases to route to queues |
| Routing address verification email never arrives | Check spam filters, mail server logs, and that the forwarding rule is active | Salesforce sends the verification to the Salesforce-generated address; mail server must be forwarding |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Confirm the Email-to-Case mode requirement: On-Demand (default) unless data residency or firewall policy requires Standard. Document the decision and the rationale before proceeding.
2. Enable Email-to-Case in Setup. For On-Demand: enable the On-Demand Service option. For Standard: download and configure the local email agent before proceeding with routing address setup.
3. Create one routing address per inbound support mailbox. Set Case Origin, Status, Priority, and optional default owner or queue on each address. For On-Demand, copy the Salesforce-generated target address.
4. Configure the company mail server to forward inbound mail from each support address to the corresponding Salesforce-generated address. Verify each routing address using the built-in verification flow.
5. Confirm an active case assignment rule exists with at least one entry that will match cases created by Email-to-Case. If auto-response emails are required, configure the auto-response rule now and confirm it is active.
6. Test threading end-to-end: inbound email creates case, outgoing reply sent from Salesforce, customer reply returns and threads into the original case as an Email Message (not a new case).
7. Review the checklist below, run the checker script against retrieved metadata, and document the configuration for the org's runbook before marking complete.

---

## Review Checklist

Run through these before marking Email-to-Case configuration complete:

- [ ] Email-to-Case feature is enabled in Setup and mode (On-Demand vs Standard) is documented and justified
- [ ] Each routing address has the external email address, default Case Origin/Status/Priority, and a verified Salesforce-hosted target address (On-Demand) or agent configuration (Standard)
- [ ] Mail server forwarding rules are active and tested: inbound email to each support address reaches Salesforce and creates a case
- [ ] Email threading tested end-to-end: customer reply to a case email adds an Email Message to the original case and does not create a new case
- [ ] Active case assignment rule exists with at least one entry matching Email-to-Case–created cases; catch-all entry routes remaining cases to a queue rather than default owner
- [ ] If auto-response rules are configured: assignment rule fires for the same case creation events; auto-response rule entry has a valid email template and a sender address that is not the routing address (to prevent email loops)
- [ ] Attachment size limits communicated to support team: 25 MB total email, 10 MB per attachment (On-Demand only)
- [ ] Checker script output reviewed and any issues resolved

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **On-Demand attachment limit is per-attachment, not per-email** — On-Demand Email-to-Case rejects individual attachments larger than 10 MB even if the total email is under 25 MB. Standard Email-to-Case does not have this per-attachment cap. Teams migrating from Standard to On-Demand may encounter unexpected rejections for attachments that previously worked fine.
2. **Routing address verification is required before inbound email is accepted** — Until the routing address is verified (by clicking the link in the Salesforce-sent verification email), Salesforce will not accept inbound email at that address. Forwarding can be configured on the mail server before verification, but emails will bounce or be dropped until verification completes.
3. **Auto-response rule loops when From address equals routing address** — If the auto-response rule is configured to send from the same email address that the routing address is configured to receive at (e.g., both are `support@company.com`), the auto-response email will arrive back at Salesforce and create another case, which triggers another auto-response, creating an infinite loop. Always use a different From address or a no-reply address for auto-response rules.
4. **Lightning thread token stripping by security gateways** — Corporate email security gateways (e.g., Proofpoint, Mimecast) sometimes strip or modify the reference string in the email body or subject line as part of link-rewriting or content inspection. This silently breaks threading. Test the full round-trip through the production mail gateway before go-live, not just against a direct SMTP relay.
5. **Standard Email-to-Case agent consumes API calls** — The local agent converts each email to a case via the Salesforce API. High-volume inbound mail can exhaust the org's daily API call limit. Monitor API usage after go-live if using Standard mode in a high-volume environment.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Email-to-Case routing address | Configured routing address record with external email, Salesforce target address, and case defaults; verification confirmed |
| Mail server forwarding rule | Forward rule on company mail server routing inbound mail from the support address to the Salesforce-generated address |
| Threading test record | Test case and Email Message records demonstrating that a customer reply threads correctly into the parent case |
| Assignment rule update | Active case assignment rule with entries that match Email-to-Case–created cases and route them to the correct queue |
| Auto-response rule (if applicable) | Active auto-response rule entry with email template; From address is not the routing address |

---

## Related Skills

- case-management-setup — use when the broader case handling layer (queues, escalation rules, entitlements, Web-to-Case) also needs configuration alongside Email-to-Case
- email-templates-and-alerts — use when the focus is on authoring or managing the email templates used in auto-response rules or case email actions
- omni-channel-routing-setup — use when cases created by Email-to-Case need to be routed to agents via Omni-Channel after creation
- assignment-rules — use when the case assignment rule logic, criteria ordering, or API trigger behavior needs dedicated attention
