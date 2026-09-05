---
name: email-to-case-configuration
description: "Configuring Salesforce Email-to-Case: Standard vs On-Demand mode selection, routing address setup, email threading via Lightning tokens, auto-response rules, attachment limits, and per-address case field defaults. Trigger keywords: email-to-case, routing address, on-demand email-to-case, email threading, case from email, email agent, routing address setup, Case.settings-meta.xml, EmailToCaseRoutingAddress, emailServicesAddress, isVerified, caseOrigin, enableThreadTokenInBody, useEmailHeadersForThreading, overEmailLimitAction, unauthorizedSenderAction, enableE2CAttachmentAsFile, saveEmailHeaders, EmailMessage.EmailRoutingAddressId, auto-response loop. NOT for the wider case layer (queues, escalation rules, case teams, entitlements) - use admin/case-management-setup. NOT for routing case work items to agents after creation - use admin/omni-channel-routing-setup. NOT for the email templates or letterheads themselves - use admin/email-templates-and-alerts."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "customer reply to a case email is creating a new case instead of threading into the original"
  - "replies create a new case instead of threading"
  - "email to case stopped creating cases"
  - "should I use On-Demand Email-to-Case or Standard Email-to-Case and what is the difference"
  - "how do I set up a routing address so inbound support emails create cases automatically"
  - "customer emailed support but no case was created and there was no bounce"
  - "which Case field does the Email-to-Case routing address populate so assignment rules can read it"
  - "auto-response is looping and creating hundreds of duplicate cases"
  - "deploy Email-to-Case routing addresses with Case.settings-meta.xml"
  - "EmailMessage.ThreadIdentifier is blank on every Email-to-Case message"
  - "cases from two different support mailboxes are all landing with the same owner"
  - "should Email-to-Case attachments be saved as Files or as Attachments"
  - "one of our support channels disappeared from Setup after a settings deploy"
tags:
  - email-to-case
  - routing-address
  - on-demand-email-to-case
  - email-threading
  - service-cloud
  - case-creation
  - auto-response-rules
  - case-settings
  - routing-address-verification
  - email-message
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Email-to-Case Configuration

This skill activates when an admin needs to configure or troubleshoot Salesforce Email-to-Case: enabling the feature, choosing between Standard and On-Demand mode, creating and verifying routing addresses, ensuring customer reply emails thread into the originating case rather than creating duplicates, and setting per-address case defaults and auto-response behavior.

---

## Before Starting

Gather this context before working on Email-to-Case configuration:

- **Which Email-to-Case mode is appropriate?** On-Demand is the default choice for most orgs. It uses Salesforce-hosted Apex Email Services and requires no locally installed agent. Standard Email-to-Case requires a downloadable Java agent running on a server inside the company firewall; it keeps email traffic internal but adds operational overhead. Choose Standard only if security policy or data residency rules prohibit email routing through Salesforce infrastructure.
- **What are the attachment size limits?** On-Demand Email-to-Case accepts an inbound message of up to **35 MB in total** (body + attachments + HTML). Because MIME transfer encoding inflates a message by up to 33% in transit, the **effective attachment ceiling is approximately 25 MB**. Messages over the total limit are rejected at the routing address. There is **no separate per-attachment cap** — 10 MB and 25 MB are the *former* org-wide totals (pre-Summer '14 and pre-Winter '21 respectively), not current per-attachment rules.
- **Is email threading the top priority?** Threading is the single most commonly misconfigured behavior. Salesforce puts a thread token in the body and/or subject of outgoing case email — which settings control that depends on whether the org uses Lightning Threading, and the two switch pairs are mutually exclusive (see Core Concepts). When a customer replies, Salesforce reads the token to locate the parent case and adds the reply as an EmailMessage. If the token is stripped by a mail server or a security gateway, `useEmailHeadersForThreading` is the only thing standing between the org and a new case per reply.
- **Are auto-response rules needed?** Auto-response rules only fire when the active case assignment rule fires. Confirm an assignment rule is active and will match the cases created by Email-to-Case before configuring auto-response rules.

---

## Questions to Ask Before Configuring

Ask these before opening Setup. Each one has a gotcha behind it, and an agent that skips them
produces a settings file that deploys cleanly and silently drops customer mail.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which public addresses do customers actually write to, and does the same mailbox forward to more than one place?" | Each address is one `routingAddresses` element; a mailbox that forwards twice duplicates every case, and two elements sharing an `emailAddress` have no deterministic configuration | The channel list, one forwarding rule each, checked by the duplicate-address ERROR in the checker |
| "Which queue owns each channel's cases?" | `caseOwner` on a routing address writes the org-level `defaultCaseOwner`, so a second address setting it overwrites the first (gotchas #6) | Ownership expressed as `caseOrigin` per address plus assignment rule entries, not `caseOwner` |
| "Is the `Case.Origin` picklist value for each channel already active in the org?" | `caseOrigin` is the only per-address value an assignment rule can read; a value that is not in the picklist stamps something nobody can filter on | The picklist additions that must deploy before or with the settings file |
| "Is this org on Lightning Threading or legacy threading?" | Two mutually exclusive pairs of token switches exist and the wrong pair is inert (gotchas #8) | The one pair to set, plus `useEmailHeadersForThreading` as the gateway fallback |
| "What should happen to mail we refuse — bounce it or drop it?" | `unauthorizedSenderAction` and `overEmailLimitAction` both accept `Discard`, which leaves no Case, no EmailMessage and no bounce (gotchas #9) | A deliberate `Bounce` / `Requeue` choice instead of an invisible failure mode |
| "Who sends the acknowledgement, and does that address forward back to us?" | Any auto-response sender that reaches a routing address is an unbounded case-creation loop; so is a vacation responder on the forwarding mailbox | A no-reply sender, plus the mail-server rule audit the checker cannot see |
| "Does anyone need email headers for a future security investigation?" | `saveEmailHeaders` captures envelope data at processing time and cannot be backfilled (gotchas #12) | Headers on from day one, and `EmailMessage.Headers` inside the org's retention scope |

What a proper configuration adds over just switching Email-to-Case on: every channel is a reviewable
element in `settings/Case.settings-meta.xml` rather than an unowned Setup checkbox, ownership is
decided once in the assignment rule instead of racing through a shared org-level field, refused mail
leaves a trace, and the reply loop is caught by a script before it is caught by the send limit.

---

## Core Concepts

### Standard vs On-Demand Email-to-Case

Email-to-Case has two operating modes with distinct infrastructure requirements:

**Standard Email-to-Case** uses a locally installed Java agent. The agent polls the company mail server, converts inbound emails to cases, and pushes them to Salesforce via the API. Email traffic travels from the customer to the company mail server and remains inside the corporate network — it never routes through Salesforce infrastructure before case creation. This matters for orgs with strict data residency or email content classification requirements. The agent requires a server to run on, must be kept online, and consumes Salesforce API calls for every email processed.

**On-Demand Email-to-Case** uses Salesforce-hosted Apex Email Services. Salesforce generates a unique routing address in the format `[unique-id]@[instance].salesforce.com`. The company configures its mail server to forward inbound email from the public support address (e.g., `support@company.com`) to this Salesforce address. Email content, including attachments, travels through Salesforce's email infrastructure before the case is created. No local agent is required. This is the recommended mode for the majority of orgs.

Size behaviour differs by mode because the enforcement point differs. On-Demand enforces Salesforce's inbound message limit at the routing address: 35 MB total per message, with an effective attachment ceiling of roughly 25 MB once MIME encoding overhead is applied. Standard Email-to-Case receives mail at the company's own mail server, so the first size gate is whatever that server enforces; the agent then creates the case through the API. Do not quote a per-attachment cap for either mode — Salesforce documents a total-message limit, not a per-attachment one.

### Email Threading: Two Switch Pairs and a Header Fallback

An outgoing case email carries a thread token in the body, the subject, or both. Which elements
control that depends on the org's threading mode, and the Metadata API guide is explicit that the two
pairs are mutually exclusive:

| Element | Applies to | Effect |
|---|---|---|
| `enableThreadTokenInBody` / `enableThreadTokenInSubject` | orgs **using** Lightning Threading | appends the token when an agent sends from the Lightning email composer |
| `enableThreadIDInBody` / `enableThreadIDInSubject` | orgs **not** using Lightning Threading | inserts the Thread ID in the body / subject line |
| `useEmailHeadersForThreading` | either | matches a reply from incoming email metadata when token-based threading finds nothing |

Setting the pair that does not apply to the org changes nothing at all. `useEmailHeadersForThreading`
is the second chance when a mail gateway has stripped the token, and is the one switch worth turning
on in every org. Do not verify threading on `EmailMessage.ThreadIdentifier`: the Object Reference
states that field "is not used by On-Demand Email-to-Case". Verify on `EmailMessage.ParentId` —
query in `references/metadata-examples.md`.

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

Two fields are read-only and never come from your source file: `emailServicesAddress` (the
Salesforce-generated address the mailbox forwards *to*) and `isVerified`. A freshly deployed routing
address therefore always lands unverified, and Salesforce accepts no mail at it until someone clicks
the verification link in the org.

**What the address stamps on the Case, and what it does not.** `caseOrigin` sets `Case.Origin`,
`casePriority` sets `Case.Priority`, and `caseOwner` + `caseOwnerType` reach `Case.OwnerId` — but by
writing the single org-level `defaultCaseOwner`, so only one address can use them meaningfully.
There is **no routing-address field on Case at all**; the address is recorded one object over as
`EmailMessage.EmailRoutingAddressId`. That makes `Case.Origin` the only per-channel hand-off an
assignment rule can read, which is the rule design shown in `references/metadata-examples.md`.

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
| Inbound email rejected in On-Demand mode for size | Check the message total (body + attachments + HTML) against 35 MB, allowing ~33% MIME inflation; direct large files to a Files/portal upload link in the auto-response | Salesforce enforces a 35 MB total inbound message limit at the routing address, giving an effective attachment ceiling of ~25 MB |
| Auto-response email not sent on case creation | Confirm an active assignment rule exists and matches the case | Auto-response only fires when assignment rule fires |
| Cases created via Email-to-Case land with default case owner, not a queue | Add a catch-all entry to the assignment rule pointing to the correct queue | Assignment rule must be active and matching for cases to route to queues |
| Routing address verification email never arrives | Check spam filters, mail server logs, and that the forwarding rule is active | Salesforce sends the verification to the Salesforce-generated address; mail server must be forwarding |

---

## Recommended Workflow

1. **Read the org before writing anything.** `sf project retrieve start --metadata "Settings:Case" "AssignmentRules:Case" "AutoResponseRules:Case"`. `routingAddresses` is a full-replacement list, so every later edit must start from what the org actually has (`references/gotchas.md` #7).
2. **Answer the seven questions above** and fill in `templates/email-to-case-configuration-template.md`: channels, the `caseOrigin` value each stamps, the owning queue, the acknowledgement sender, the threading mode. Confirm the mode choice — On-Demand unless data residency policy forbids it.
3. **Shape the metadata** from `references/metadata-examples.md`: the `emailToCase` block with one `routingAddresses` element per channel, the matching `Case.assignmentRules` entries keyed on `Case.Origin`, and the `package.xml` naming `Settings:Case` explicitly (the wildcard does not work for an individual setting).
4. **Run the checker** — `python3 scripts/check_email_to_case_configuration.py --manifest-dir <dir> --verbose`. Clear every ERROR (duplicate `emailAddress`, `caseOwner` without `caseOwnerType`, more than one address setting `caseOwner`, auto-response sender equal to a routing address). Justify or fix each WARN.
5. **Deploy, then finish the setup that metadata cannot do**: copy each `emailServicesAddress` out of Setup, create one forwarding rule per channel, disable any auto-reply on the forwarding mailbox, send the verification email, and confirm each address reads Verified. The checklist is in `references/metadata-examples.md`.
6. **Run the three tests** from `references/metadata-examples.md`: the threading round-trip through the *production* mail gateway asserted on `EmailMessage.ParentId`, the routing-address/origin query, and the loop test (one email per address, case count must stop at one).
7. **Hand over.** Record the public address to `emailServicesAddress` mapping, the verification dates, and the threading mode in the org runbook — the org will not hand `emailServicesAddress` back if an address is ever deleted. Work through the Review Checklist below.

---

## Review Checklist

Run through these before marking Email-to-Case configuration complete:

- [ ] Email-to-Case feature is enabled in Setup and mode (On-Demand vs Standard) is documented and justified
- [ ] Each routing address has the external email address, default Case Origin/Status/Priority, and a verified Salesforce-hosted target address (On-Demand) or agent configuration (Standard)
- [ ] Mail server forwarding rules are active and tested: inbound email to each support address reaches Salesforce and creates a case
- [ ] Email threading tested end-to-end: customer reply to a case email adds an Email Message to the original case and does not create a new case
- [ ] Active case assignment rule exists with at least one entry matching Email-to-Case–created cases; catch-all entry routes remaining cases to a queue rather than default owner
- [ ] If auto-response rules are configured: assignment rule fires for the same case creation events; auto-response rule entry has a valid email template and a sender address that is not the routing address (to prevent email loops)
- [ ] Attachment size limits communicated to support team: On-Demand accepts up to 35 MB total inbound message size, i.e. roughly 25 MB of attachments after MIME encoding overhead; there is no per-attachment cap
- [ ] `settings/Case.settings-meta.xml` was retrieved from the target org before editing, and the routing-address count in the file to be deployed is not lower than the count in the org
- [ ] At most one routing address sets `caseOwner`, and it sets `caseOwnerType` alongside it; per-channel ownership is expressed as `caseOrigin` plus assignment rule entries
- [ ] Every `caseOrigin` value used by a routing address exists and is active in the `Case.Origin` picklist
- [ ] Only the threading switch pair matching the org's threading mode is set; `useEmailHeadersForThreading` is on
- [ ] `unauthorizedSenderAction` and `overEmailLimitAction` are a deliberate choice, and `Discard` is used only where someone has signed off on losing the message
- [ ] `saveEmailHeaders` is true on every routing address
- [ ] Threading verified on `EmailMessage.ParentId`, not on `ThreadIdentifier` (blank for On-Demand Email-to-Case by design)
- [ ] `python3 scripts/check_email_to_case_configuration.py --manifest-dir <dir> --verbose` reports zero ERRORs and every WARN is justified

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **The On-Demand size limit is per-message, not per-attachment — and the number you remember is probably a retired one** — Salesforce rejects an inbound On-Demand message once the total (body + attachments + HTML) exceeds 35 MB. MIME transfer encoding inflates the payload by up to 33%, so the practical attachment budget is about 25 MB. 25 MB was the org-wide total before Winter '21 and 10 MB was the total before Summer '14; both numbers survive in older blog posts and in model memory as fictitious *per-attachment* caps. Quote 35 MB total / ~25 MB effective, and never promise a per-attachment threshold.
2. **Routing address verification is required before inbound email is accepted** — Until the routing address is verified (by clicking the link in the Salesforce-sent verification email), Salesforce will not accept inbound email at that address. Forwarding can be configured on the mail server before verification, but emails will bounce or be dropped until verification completes.
3. **Auto-response rule loops when From address equals routing address** — If the auto-response rule is configured to send from the same email address that the routing address is configured to receive at (e.g., both are `support@company.com`), the auto-response email will arrive back at Salesforce and create another case, which triggers another auto-response, creating an infinite loop. Always use a different From address or a no-reply address for auto-response rules.
4. **Lightning thread token stripping by security gateways** — Corporate email security gateways (e.g., Proofpoint, Mimecast) sometimes strip or modify the reference string in the email body or subject line as part of link-rewriting or content inspection. This silently breaks threading. Test the full round-trip through the production mail gateway before go-live, not just against a direct SMTP relay.
5. **Standard Email-to-Case agent consumes API calls** — The local agent converts each email to a case via the Salesforce API. High-volume inbound mail can exhaust the org's daily API call limit. Monitor API usage after go-live if using Standard mode in a high-volume environment.
6. **`caseOwner` is an org-level field wearing a per-address costume** — the Metadata API guide states that setting it on a routing address writes `CaseSettings.defaultCaseOwner`. Give a second address its own owner and the first one's is overwritten, with no deploy warning. Route on `Case.Origin` instead.
7. **Deploying a partial settings file deletes the channels it omits** — `routingAddresses` is a full-replacement list, and `emailServicesAddress` is read-only, so a deleted address cannot be restored to its old Salesforce-generated value. Always retrieve first.
8. **`Discard` is genuinely silent** — both `unauthorizedSenderAction` and `overEmailLimitAction` accept it, and a discarded message produces no Case, no EmailMessage and no bounce. Nobody can prove the customer wrote in.

Deeper treatment, with the platform behaviour behind each, in `references/gotchas.md` (13 entries).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `settings/Case.settings-meta.xml` | The `emailToCase` block: mode, threading and failure-action switches, and one `routingAddresses` element per channel; deployable as `Settings:Case` |
| Email-to-Case routing address | Configured routing address record with external email, Salesforce target address, and case defaults; verification confirmed |
| Address map | Public address → `emailServicesAddress` → `caseOrigin` → owning queue, with verification dates, for the org runbook |
| Mail server forwarding rule | Forward rule on company mail server routing inbound mail from the support address to the Salesforce-generated address |
| Threading test record | Test case and Email Message records demonstrating that a customer reply threads correctly into the parent case |
| Assignment rule update | Active case assignment rule with entries that match Email-to-Case–created cases and route them to the correct queue |
| Auto-response rule (if applicable) | Active auto-response rule entry with email template; From address is not the routing address |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing `Case.settings-meta.xml`, the routing-address-to-assignment-rule hand-off, the forwarding and verification checklist, or the threading / routing / loop verification queries |
| `references/gotchas.md` | Mail is being dropped, threading broke, a channel vanished after a deploy, or ownership is wrong on one channel |
| `references/examples.md` | Working end-to-end setups: one mailbox, multiple channels, and how to catch the auto-response loop in the first five minutes |
| `references/llm-anti-patterns.md` | Reviewing AI-generated Email-to-Case guidance, especially any quoted attachment size number |
| `references/well-architected.md` | Justifying On-Demand vs Standard, single vs multiple addresses, or auto-response vs Flow, and for the source list |

---

## Related Skills

- admin/case-management-setup — the wider case layer (queues, escalation, entitlements, Web-to-Case); this skill closes that skill's open "routing-address to queue mapping" question via `Case.Origin`
- admin/assignment-rules — the `Case.assignmentRules` and `Case.autoResponseRules` files themselves: criteria grammar, entry order, and the `senderEmail` this skill must never let equal a routing address
- admin/email-templates-and-alerts — org-wide email addresses and the Classic templates an auto-response entry points at
- admin/queues-and-public-groups — `references/queue-behaviour-matrix.md`, the `email` / `doesSendEmailToMembers` pair that stacks with `notifyOwnerOnNewCaseEmail`
- admin/business-hours-and-holidays — the SLA clock that starts when an inbound email creates the case
- admin/email-service-inbound — a **different feature**: Apex Email Services with `Messaging.InboundEmailHandler`, for inbound mail that must run custom code. On-Demand Email-to-Case is Salesforce's own hosted email service and needs no handler; write one only when case creation is not what you want
- admin/case-feed-send-email-action — the outbound half: the Send Email quick action agents reply from, and its own file limits
- admin/email-deliverability-strategy — SPF, DKIM and DMARC on the domain that forwards into the routing address
- admin/omni-channel-routing-setup — pushing the created case to an available agent; `routingFlow` and `fallbackQueue` on a routing address are the entry point
- admin/permission-set-architecture — the grants that `isPermsetControlled` requires before it stops locking everyone out
