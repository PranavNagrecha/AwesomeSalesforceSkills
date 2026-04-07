---
name: marketing-cloud-engagement-setup
description: "Use this skill when configuring Marketing Cloud Engagement (formerly ExactTarget): business units, user roles, sender profiles, delivery profiles, send classifications, and account-level settings. NOT for MCAE/Pardot or Marketing Cloud Account Engagement configuration."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "how do I set up business units in Marketing Cloud Engagement"
  - "configure sender profile and delivery profile in Marketing Cloud"
  - "Marketing Cloud user roles and permissions setup for Enterprise account"
  - "send classification commercial vs transactional Marketing Cloud"
  - "dedicated IP assignment and sender reputation across business units"
  - "reply mail management configuration for Marketing Cloud BU"
  - "new business unit provisioning Enterprise 2.0 Marketing Cloud"
tags:
  - marketing-cloud-engagement
  - business-units
  - sender-profiles
  - delivery-profiles
  - send-classifications
  - enterprise-2-account
  - user-roles
inputs:
  - "Marketing Cloud Engagement account type (Enterprise 2.0 vs standalone)"
  - "List of required business units with brand, locale, and sending domain"
  - "Desired user role assignments per BU"
  - "From-name and from-address requirements per brand or BU"
  - "Physical mailing address for CAN-SPAM compliance"
  - "Whether dedicated or shared IP is provisioned"
outputs:
  - "Configured Business Units with correct subscriber key space and reply mail settings"
  - "Sender Profiles covering all required from-name/from-address combinations"
  - "Delivery Profiles linked to physical address and IP assignment"
  - "Send Classifications pairing sender profile + delivery profile + unsubscribe profile"
  - "Role assignments for each BU user aligned to least-privilege"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Marketing Cloud Engagement Setup

This skill activates when a practitioner needs to configure Marketing Cloud Engagement infrastructure: creating and managing Business Units in an Enterprise 2.0 account, assigning user roles, and establishing the sender profile / delivery profile / send classification chain that governs all email sends. It does NOT cover MCAE (Pardot/Account Engagement) configuration, SMS setup via MobileConnect, or Journey Builder orchestration logic.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the account model: Enterprise 2.0 (multiple BUs under one parent) vs. standalone. Almost all mid-market and enterprise MC accounts use Enterprise 2.0, but the provisioning and inheritance rules differ from older account models.
- Identify which Salesforce support tier applies. New Business Unit provisioning requires opening a support ticket with Salesforce; it cannot be done from within the Setup UI alone.
- Obtain the physical mailing address that will appear on all commercial emails — CAN-SPAM requires a valid postal address in every commercial message. This address lives on the Delivery Profile, not the email template.
- Confirm whether a dedicated IP or shared IP is in use. With Enterprise 2.0, a dedicated IP is shared across all Business Units in the account — there is one sender reputation, not one per BU.
- Determine whether emails will be commercial (opt-in/opt-out governed) or transactional (order confirmations, password resets — bypasses commercial unsubscribes). This drives Send Classification selection.

---

## Core Concepts

### Enterprise 2.0 Account Model and Business Units

Marketing Cloud Engagement uses an Enterprise 2.0 (ENT 2.0) account structure. A single parent account contains one or more Business Units (BUs). Each BU maintains its own:

- Subscriber list (the "All Subscribers" list is per-BU, not shared across BUs)
- User accounts and role assignments
- Email templates, content blocks, and data extensions
- Sender profiles, delivery profiles, and send classifications
- Reply Mail Management configuration

This isolation is intentional — it supports multi-brand or multi-region operations where teams must not access each other's contacts or content. However, because each BU has its own subscriber key space, a contact present in BU A and BU B is treated as two independent subscriber records.

New BUs are provisioned by Salesforce Support in response to a case. Admins cannot self-provision additional BUs from the Setup menu.

### Sender Profiles, Delivery Profiles, and Send Classifications

These three objects form a required chain for any email send:

**Sender Profile** — controls the visible From Name and From Email Address that subscribers see in their inbox. Each BU can have multiple Sender Profiles (e.g., one per brand or product line). A Sender Profile can also specify a Reply-To address different from the From address.

**Delivery Profile** — controls the physical mailing address that appears in the email footer (CAN-SPAM compliance), the IP address or IP pool used for delivery, and the header/footer content wrapper. With a dedicated IP, the Delivery Profile references that IP. Because a dedicated IP is shared across all BUs in the Enterprise account, changes to IP warm-up status or reputation affect all BUs simultaneously.

**Send Classification** — links a Sender Profile and a Delivery Profile together and designates the send type as either **Commercial** or **Transactional**. Commercial sends respect subscriber opt-out (unsubscribe) status; Transactional sends bypass the commercial unsubscribe list, which means they can be sent to subscribers who have globally opted out. Misclassifying a commercial message as Transactional is a CAN-SPAM violation.

### User Roles and the Role Hierarchy

Marketing Cloud Engagement has a fixed set of standard roles. Custom roles can be created and are scoped to a specific BU — a custom role created in BU A is not automatically available in BU B.

Standard roles (from most to least privileged):
1. **Marketing Cloud Administrator** — full account and cross-BU access including Setup
2. **Administrator** — full access within a single BU, cannot manage account-level settings
3. **Content Creator** — create and edit content and emails; cannot manage users or send live campaigns independently
4. **Analyst** — view reports and tracking data; no content modification
5. **Data Manager** — manage data extensions, imports, and exports; cannot send

A user's role is assigned per BU. The same user can have Administrator in BU A and Content Creator in BU B. The Marketing Cloud Administrator role is assigned at the account (parent) level and grants access to all BUs.

---

## Common Patterns

### Pattern: Multi-Brand Enterprise Setup with BU-per-Brand Isolation

**When to use:** A company operates multiple distinct brands (e.g., retail + financial services) under one MC account and needs strict content and subscriber isolation between brands.

**How it works:**
1. Request BU provisioning via Salesforce Support case — one BU per brand.
2. Create a Sender Profile in each BU with the brand-specific from-name and from-address.
3. Create a Delivery Profile in each BU referencing the shared dedicated IP and the brand's physical mailing address.
4. Create Send Classifications per BU: one Commercial, one Transactional if transactional sends are needed.
5. Assign users to only their relevant BU with the minimum required role.
6. Configure Reply Mail Management per BU so unsubscribe replies and bounce handling are routed correctly.

**Why not the alternative:** Creating a single BU with segmented data extensions instead of separate BUs allows cross-team visibility into subscriber data and templates, creating brand contamination risk and increasing the blast radius of misconfigurations.

### Pattern: Transactional Send Classification for Order Confirmations

**When to use:** The product team needs to send order confirmation or password-reset emails that must reach subscribers regardless of their opt-out status.

**How it works:**
1. Create a dedicated Sender Profile for the transactional from-address (e.g., `noreply@orders.brand.com`).
2. Create or reuse a Delivery Profile with the correct physical address.
3. Create a Send Classification: set Type to **Transactional**, link the transactional Sender Profile and Delivery Profile.
4. When building the triggered send or journey, select this Send Classification explicitly.
5. Document in an internal runbook which email categories are approved for Transactional classification.

**Why not the alternative:** Using the default Commercial send classification for order emails means subscribers who have unsubscribed will not receive the email, creating customer service failures and potential contractual issues. But incorrectly using Transactional for promotional content violates CAN-SPAM and can result in deliverability penalties.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New brand or region needs email sending | Provision a new BU via Support case | Maintains subscriber and content isolation; avoids cross-brand data visibility |
| User needs to manage content but not users or sends | Assign Content Creator role | Least-privilege; prevents accidental live sends or user changes |
| Email is an order confirmation or password reset | Create a Transactional Send Classification | These messages must bypass commercial unsubscribe; using Commercial risks non-delivery |
| Multiple brands share one dedicated IP | Coordinate IP warming as a single entity | Dedicated IP reputation is unified across all BUs; one BU's poor-quality send affects all brands |
| Admin needs access to all BUs | Assign Marketing Cloud Administrator role at parent account level | BU-level Administrator role does not grant cross-BU or account-level Setup access |
| BU needs to handle replies and bounces | Configure Reply Mail Management at BU level | RMM is not inherited from parent; each BU's reply routing is independent |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm account model and existing BU inventory.** Log in to Marketing Cloud and navigate to Setup > Business Units. Confirm the account is Enterprise 2.0. List existing BUs and check whether new ones are needed. If new BUs are needed, open a Salesforce Support case with the BU name, primary locale, sending domain, and brand contact.

2. **Configure Sender Profiles.** In each BU, navigate to Email Studio > Admin > Sender Profiles. Create a Sender Profile for each distinct from-name/from-address pair the BU will use. Verify that the sending domain is authenticated (SPF, DKIM) in the account's Authenticated Domains list.

3. **Configure Delivery Profiles.** In each BU, navigate to Email Studio > Admin > Delivery Profiles. Create or update a Delivery Profile specifying the physical mailing address (street, city, state, ZIP, country) for CAN-SPAM footer compliance and the IP address or IP pool. Reference the dedicated IP if one is provisioned.

4. **Create Send Classifications.** In each BU, navigate to Email Studio > Admin > Send Classifications. Create at minimum one Commercial Send Classification and one Transactional Send Classification if transactional sends are required. Each Send Classification must reference a Sender Profile, a Delivery Profile, and an Unsubscribe Profile. Set the Type field to Commercial or Transactional explicitly.

5. **Assign user roles.** In Setup > Users, add or invite users and assign them to the appropriate BU with the correct role. Use the principle of least privilege. For users who span BUs, assign them independently in each BU. Reserve Marketing Cloud Administrator for accounts that genuinely need cross-BU Setup access.

6. **Configure Reply Mail Management.** In each BU, navigate to Setup > Reply Mail Management. Configure the reply address, auto-reply rule (auto-unsub, leave inbox, or forward), and the Salesforce forwarding address. Test by sending a test email and replying to confirm routing.

7. **Validate end-to-end with a test send.** Send a test email from each BU using the configured Send Classification. Confirm the From Name, From Address, physical footer address, and unsubscribe link render correctly. Check bounce and reply handling via Reply Mail Management logs.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All required Business Units provisioned and confirmed active in Setup > Business Units
- [ ] Each BU has at least one Sender Profile with an authenticated sending domain (SPF/DKIM)
- [ ] Each BU has a Delivery Profile with a valid physical mailing address for CAN-SPAM compliance
- [ ] Each BU has a Commercial Send Classification; Transactional Send Classification exists if needed
- [ ] User roles are assigned per-BU at the least-privilege level required for each user's function
- [ ] Reply Mail Management is configured and tested in every active BU
- [ ] Dedicated IP warm-up schedule is documented and coordinated across all BUs sharing the IP
- [ ] Transactional Send Classifications are used only for legally transactional message types

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **All Subscribers list is per-BU, not account-wide** — Each BU has its own All Subscribers list. A contact who unsubscribes in BU A remains subscribed in BU B. This is intentional for brand isolation but frequently surprises admins who assume account-level unsubscribes propagate everywhere. CAN-SPAM compliance requires honoring unsubscribes within each BU independently.

2. **Dedicated IP reputation is shared across all BUs** — When a dedicated IP is provisioned for an Enterprise 2.0 account, that single IP (or IP pool) is used by all BUs. A BU with poor list hygiene or high spam complaint rates will degrade deliverability for every other BU on the account. This is not visible in per-BU reporting; you must check account-level IP reputation data.

3. **New BU provisioning requires a Salesforce Support case** — Admins frequently expect to create BUs from the Setup UI. The option does not exist. New BUs can only be provisioned by Salesforce Support. This adds lead time (typically 1–3 business days) that is routinely missed in project plans.

4. **Transactional Send Classification bypasses ALL commercial unsubscribes** — Once a send is classified as Transactional, it will reach subscribers who are on the global unsubscribe list. Using Transactional for any promotional, marketing, or opt-in-required content is a CAN-SPAM violation and can trigger account suspension by Salesforce deliverability operations.

5. **Custom roles are scoped to the BU where they are created** — A custom role created in BU A does not appear in BU B. Admins who build a permission set-like custom role for one team must recreate it in every BU where it is needed. There is no account-level role inheritance for custom roles.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured Business Units | Active BUs in Setup with correct name, locale, and brand assignment |
| Sender Profiles | Named profiles per BU defining From Name and From Address |
| Delivery Profiles | Per-BU profiles containing physical mailing address and IP assignment |
| Send Classifications | Per-BU commercial and transactional classifications linking sender + delivery + unsubscribe profiles |
| User role assignments | Per-BU role assignments documented in a role matrix |
| Reply Mail Management config | Configured bounce/reply routing per BU |

---

## Related Skills

- admin/email-deliverability-setup — covers SPF, DKIM, and DMARC authentication for sending domains used in Sender Profiles
- admin/salesforce-connect-setup — relevant when MC Engagement is integrated with Sales Cloud via Marketing Cloud Connect
