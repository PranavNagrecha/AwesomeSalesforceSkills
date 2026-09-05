---
name: email-deliverability-strategy
description: "Use when configuring or troubleshooting email deliverability for Marketing Cloud or Salesforce orgs: sender authentication (SPF, DKIM, DMARC), private sending domain setup, dedicated IP warm-up, list hygiene practices, and sender reputation monitoring. NOT for building a Marketing Cloud email — use admin/email-studio-administration. NOT for unsubscribe and consent — use admin/consent-management-marketing. Also covers the Salesforce Core deliverability surface: EmailAdministrationSettings, EmailAuthorizationSettings, EmailDomainKey (DKIM), EmailRelay, EmailDomainFilter, OrgWideEmailAddress verification, bounce management, and the 5,000-a-day outbound email cap."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "emails are landing in spam instead of the inbox"
  - "how do I set up SPF and DKIM for Marketing Cloud"
  - "dedicated IP warm-up plan for a new sending domain"
  - "DMARC policy required by Google and Yahoo for bulk senders"
  - "our sender reputation dropped and bounce rates are climbing"
  - "how to suppress hard bounces and inactive subscribers automatically"
  - "difference between inbox placement rate and delivery rate"
  - "is there a way to throttle outbound emails so we don't trigger spam filters"
  - "throttle email sending rate to avoid spam filters"
  - "salesforce sending too many emails too fast deliverability"
  - "email deliverability isn't working"
  - "why is my org-wide email address not sending"
  - "set up DKIM keys in Salesforce Setup"
  - "rotate a DKIM key without breaking outbound email"
  - "route Salesforce email through our own SMTP relay"
  - "hit the 5000 email per day limit in a flow"
  - "EmailBouncedDate is empty even though emails are bouncing"
  - "deploy EmailAdministrationSettings but the file name is wrong"
  - "emails send from sfcustomeremail.com instead of our domain"
tags:
  - email-deliverability
  - spf
  - dkim
  - dmarc
  - sender-reputation
  - list-hygiene
  - dedicated-ip
  - marketing-cloud
inputs:
  - "Sending domain (private vs shared Marketing Cloud sending domain)"
  - "Current daily send volume and target volume"
  - "Whether a dedicated IP is in use or planned"
  - "Bounce and unsubscribe rates from recent sends"
  - "Current DNS records for the sending domain (or access to DNS admin)"
  - "Retrieved EmailAdministration.settings / EmailAuthorization.settings from the target org"
  - "EmailDomainKey, EmailRelay, EmailDomainFilter and OrgWideEmailAddress query results"
outputs:
  - "DNS record specifications for SPF, DKIM, and DMARC"
  - "Dedicated IP warm-up schedule with daily volume ramp"
  - "List hygiene suppression policy and implementation steps"
  - "Sender reputation monitoring checklist"
  - "Decision table: private domain vs shared domain vs dedicated IP"
  - "Deployable EmailAdministrationSettings / EmailAuthorizationSettings XML plus package.xml"
  - "DKIM key inventory with rotation dates, and the SOQL that regenerates it"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Email Deliverability Strategy

This skill activates when a practitioner needs to configure sender authentication records, plan a dedicated IP warm-up, establish list hygiene policies, or diagnose why emails are landing in spam. It does NOT cover email template design, dynamic content, Journey Builder flows, or Salesforce Core transactional email limits.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org uses a **private sending domain** (only your organization sends from it) or Marketing Cloud's **shared sending domain** (shared IP pool with other tenants). This distinction drives nearly every downstream decision.
- Ask for the current and target daily send volume. Volume determines whether a dedicated IP is justified (generally >100,000 emails/day) and shapes the warm-up schedule.
- Check if SPF, DKIM, and DMARC records already exist on the sending domain. Duplicate or conflicting SPF records are the most common misconfiguration.
- Know the current hard bounce rate. A rate above 2% is a signal that list hygiene needs immediate attention before any deliverability improvement work will hold. UNVERIFIED (2026-09-05): the 2% threshold is industry practice; no Salesforce guide states a bounce-rate number.
- Determine which of the **two layers** the request lives in, because they share vocabulary and nothing else:

| Layer | What it controls | Where it is configured | Grounded in this repo? |
|---|---|---|---|
| **Salesforce Core** | Bounce management, SPF compliance, TLS, Compliance BCC, DKIM keys, SMTP relay, org-wide From addresses, the 5,000-a-day cap | `EmailAdministrationSettings`, `EmailAuthorizationSettings`, and four sObjects | Yes — Metadata API guide, Object Reference, Apex guides. See `references/metadata-examples.md`. |
| **Marketing Cloud** | Private/shared sending domains, dedicated IPs and warm-up, subscriber suppression, seed-list inbox placement | Marketing Cloud Setup only | No — no Metadata API or Object Reference surface exists. Claims rest on Marketing Cloud Help and are marked UNVERIFIED where numeric. |

  Sending domain reputation is a Marketing Cloud concern; whether the platform will hand the message to a mail server at all is a Core concern. A "deliverability" ticket that is really "the Flow ran and nobody got the email" is Core, every time.

---

## Questions to Ask Before Configuring

Ask these before touching DNS or Setup; the answers decide which of the two layers the work belongs in, and an LLM that skips them produces a DNS plan for a problem that was an unverified org-wide address.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which sends are failing — a Marketing Cloud campaign, or an email alert / Flow / Apex send from the Core org?" | Splits the two layers before any work starts. Core failures have a metadata surface and a checker; Marketing Cloud failures do not. | The layer, and therefore whether `references/metadata-examples.md` or `references/examples.md` is the runbook |
| "Is the mail *not arriving*, or arriving in spam?" | Not arriving is a send-side failure (unverified domain, unverified org-wide address, daily cap, relay with no active filter). Arriving in spam is a reputation problem. | Splits Gotchas 10 / 12 / 13 from the SPF-DKIM-DMARC track |
| "Which domains does this org send from, and does each have an active DKIM key with a rotation date?" | Nothing on the platform expires a DKIM key or warns you it is stale; `TxtRecordsPublishState` can read `Publishing failed` indefinitely (Gotcha 9) | The `deliverability/dkim-keys.json` inventory the checker enforces |
| "Has anyone touched `enableSubstituteFromAddress` or an org-wide address to stop send failures?" | `true` silently rewrites the From address to `@…sfcustomeremail.com`, throwing away every reputation signal (Gotcha 10) | Whether the org is quietly sending as Salesforce rather than as the brand |
| "What is the org's daily external send volume, counting email alerts and Flow Send Email actions?" | For orgs created Spring '19 and later those count against the same 5,000 external addresses per day as Apex (Gotcha 13, apexdev.txt L19959-19966) | Whether a throttle is a real fix or a redistribution of the same budget |
| "Do we relay through corporate SMTP, and is bounce management on?" | A relay with no active `EmailDomainFilter` is inert with no error (Gotcha 12); with bounce handling off the Contact/Lead bounce fields stay empty forever (Gotcha 11) | The relay/filter load order and whether bounce reporting is even possible |
| "Who owns DNS, and what is the change lead time?" | DKIM activation must wait for CNAMEs to resolve; DMARC tightening must wait for aggregate reports | A sequenced plan instead of a same-day activation that fails every signature |

What a proper configuration adds over just publishing the records: sends that fail are visible as bounces rather than as silence, the From address on every message is a domain you own and sign for, DKIM keys have a named owner and a rotation date, and the deployable half of the configuration is in source control and linted before it reaches an org.

---

## Core Concepts

### Authentication Trifecta: SPF, DKIM, and DMARC

Email authentication uses three complementary DNS-based standards. All three must be in place before deliverability can be fully controlled.

**SPF (Sender Policy Framework)** is a TXT record on the sending domain that lists the IP addresses and mail transfer agents authorized to send on behalf of that domain. Marketing Cloud provides a specific `include:` statement (e.g., `include:_spf.exacttarget.com` — UNVERIFIED (2026-09-05): the literal is from Marketing Cloud Setup, not from any guide in this repo's corpus; always read the real value from Setup > Private Domains) that must be added to the domain's SPF record. There must be exactly one SPF TXT record per domain; multiple SPF records are invalid per RFC 7208 and cause evaluation failures. The total number of DNS lookups from `include:` directives must not exceed 10.

**DKIM (DomainKeys Identified Mail)** attaches a cryptographic signature to each outbound email. Marketing Cloud generates a DKIM key pair per private sending domain; the public key is published as a CNAME record in DNS pointing to Marketing Cloud's key servers. CNAME-based DKIM (rather than a raw TXT public key) lets Salesforce rotate keys without a DNS change. Salesforce Core works the same way and *is* documented: `EmailDomainKey` exposes `Selector` / `AlternateSelector`, and Salesforce publishes `TxtRecordName` / `AlternateTxtRecordName` for you to CNAME to, with `AlternatePublicKey` existing so Salesforce can "auto-rotate domain keys" (object_reference.txt L103529-103545, L103693-103698).

**DMARC (Domain-based Message Authentication, Reporting, and Conformance)** is a TXT record at `_dmarc.<yourdomain.com>` that tells receiving mail servers what to do when SPF or DKIM fails: `p=none` (monitor only), `p=quarantine` (send to spam), or `p=reject` (block). Since February 2024 Google and Yahoo require a minimum DMARC policy of `p=none` for any sender sending more than 5,000 messages per day to Gmail or Yahoo addresses. UNVERIFIED (2026-09-05): receiver policy set by Google and Yahoo; no Salesforce guide states it, and the threshold and date are theirs to change. The record must also include `rua=` (aggregate report destination) so receiving servers can report alignment failures back. DMARC also enforces **alignment**: the domain in the `From:` header must match (or be a subdomain of) the SPF or DKIM signing domain.

### Private Sending Domain vs Shared Sending Domain

A **private sending domain** is a subdomain dedicated exclusively to your organization (e.g., `send.yourbrand.com`). All SPF, DKIM, and DMARC records are scoped to this subdomain. Reputation is isolated: your bounce history, spam complaint rate, and engagement metrics apply only to your sends.

A **shared sending domain** means Marketing Cloud's shared IP pools are used. Multiple tenants send from the same IP addresses, so one tenant's poor sending practices can damage the shared reputation. Shared domains are acceptable for low-volume, high-quality lists but should not be used for large-scale campaigns where reputation control matters.

### Dedicated IP Warm-Up

ISPs track sending reputation per IP address. A brand-new dedicated IP has no history, so ISPs throttle or block it until it establishes a positive track record. Warm-up is the process of gradually increasing send volume over 4–8 weeks while maintaining excellent engagement signals.

Warm-up principle: start with 50,000–100,000 emails per day using the **highest-quality, most-engaged segments** (subscribers who opened or clicked within the last 90 days). Double volume every 2–3 days as long as bounce and complaint rates remain within acceptable limits (hard bounce < 0.5%, spam complaint rate < 0.1%). Send to less-engaged segments only after the IP has handled volume from engaged subscribers without throttling.

Skipping warm-up or rushing it causes ISPs to assign a poor initial reputation that is difficult and slow to recover.

### List Hygiene

List hygiene is the single most influential lever for long-term sender reputation. Sending to invalid, inactive, or disengaged addresses drives up bounce rates and spam complaint rates, both of which degrade sender reputation.

Key hygiene rules:
- **Hard bounces** (permanent failures: invalid address, domain does not exist) must be suppressed after the first occurrence. Marketing Cloud does this automatically by moving hard-bounced addresses to the All Subscribers suppression list.
- **Soft bounces** (temporary failures: mailbox full, server unavailable) are suppressed automatically by Marketing Cloud after 3 consecutive soft bounce events for the same address.
- **Inactive subscribers** (no open or click in 6–12 months) should be moved to a sunset flow and eventually suppressed. Continuing to send to a large inactive segment is the most common cause of gradual reputation decay.
- **Spam complainers** (subscribers who mark email as junk) are automatically suppressed via the Feedback Loop (FBL) integration with major ISPs. Confirm FBL registration is active in the Marketing Cloud account.

### The Salesforce Core Surface

Six controls, four of which have no Metadata API type. `references/metadata-examples.md` has the deployable shapes, field-by-field notes, and every guide citation.

| Control | Surface | Deploys? | The failure it prevents |
|---|---|---|---|
| `EmailAdministrationSettings` | `settings/EmailAdministration.settings-meta.xml`, API 47.0+ | Yes | Bounce management off, SPF compliance flipped off, Compliance BCC enabled with no address, TLS unrestricted |
| `EmailAuthorizationSettings` | `settings/EmailAuthorization.settings-meta.xml`, API 66.0+ | Yes | Sending as `@…sfcustomeremail.com` from an unverified domain |
| `EmailDomainKey` | sObject, API 28.0+ | No — API / Data Loader / Setup | Unsigned or unverifiable DKIM; stale keys nobody owns |
| `EmailRelay` + `EmailDomainFilter` | sObjects, API 43.0+ | No | A relay that is configured and inert |
| `OrgWideEmailAddress` | sObject; `IsVerified` API 58.0+ | No | Alerts and Apex sends that produce no email and no error |
| Deliverability **Access Level** | Setup page only | **No** | A sandbox mailing real customers, or production silently sending nothing |

Two consequences that shape every plan. First, only two of the six are deployable, so a "deliverability change" is a mixed release: metadata for the settings, Data Loader or API for the sObjects, and a manual Setup step for Access Level — see `references/metadata-examples.md` § 7 for the required order. Second, the Access Level control that decides whether the org sends at all has no metadata element and cannot be diffed between orgs; when a send silently produces nothing, check it before anything else, and expect Apex to surface it as `System.NoAccessException: The organization is not permitted to send email.` (apexrefguide.txt L225158).

### Outbound Volume Is a Shared Org Budget

Each licensed org sends single emails to a maximum of 5,000 external email addresses per day, measured on GMT (apexdev.txt L19959-19961). What counts depends on org age: for orgs created before Spring '19 the cap applies only to Apex and Salesforce APIs except REST; for orgs created in Spring '19 and later it also covers "email alerts, simple email actions, Send Email actions in flows, and REST API" (apexdev.txt L19961-19964). Mass email and list email carry their own separate 5,000-a-day external cap (apexdev.txt L19976-19978).

Three consequences that surprise teams mid-incident: duplicates are counted individually, not deduplicated; internal recipients addressed by `setTargetObjectId` do not count while the same people addressed by `setToAddresses` do (apexdev.txt L19971-19975); and exceeding the cap notifies you by email and a debug-log entry rather than throwing at the point of send. `Messaging.reserveSingleEmailCapacity(n)` converts that into a fail-fast `System.HandledException` before the transaction commits (apexrefguide.txt L225161-225184).

### Inbox Placement Rate vs Delivery Rate

These are frequently conflated but measure different things:
- **Delivery Rate**: the percentage of sent messages accepted by the receiving mail server. A message is "delivered" even if it goes to the spam folder.
- **Inbox Placement Rate (IPR)**: the percentage of delivered messages that land in the inbox (as opposed to spam/junk). IPR is the metric that actually matters to recipients and campaign performance.

Tools like Return Path (Validity), 250ok, and GlockApps perform seed-list testing to measure IPR across ISPs. Delivery rate alone is insufficient for diagnosing deliverability problems.

---

## Common Patterns

### Pattern 1: New Private Sending Domain Setup

**When to use:** The organization is moving from the Marketing Cloud shared domain to a dedicated private sending domain, or setting up Marketing Cloud sending for the first time with a custom domain.

**How it works:**
1. Choose a subdomain dedicated exclusively to sending (e.g., `em.yourbrand.com`). Do not use the same domain as your website or corporate email to avoid DMARC policy conflicts.
2. In Marketing Cloud Setup > Private Domains, add the domain and retrieve the required CNAME records for DKIM.
3. Publish the DKIM CNAME records in DNS.
4. Construct and publish a single SPF TXT record that includes Marketing Cloud's SPF include directive plus any other authorized senders (corporate mail servers, etc.). Keep total DNS lookup count under 10.
5. Publish a DMARC TXT record at `_dmarc.em.yourbrand.com` starting at `p=none` with `rua=` set to an address that receives aggregate reports.
6. Validate all records using MXToolbox or a similar DNS check tool before sending.
7. If using a dedicated IP, execute the warm-up plan before sending large campaigns.

**Why not the alternative:** Using the shared Marketing Cloud domain avoids DNS setup but sacrifices reputation isolation and makes DMARC alignment more complex. For any brand where email is a primary channel, a private domain is required.

### Pattern 2: Dedicated IP Warm-Up Plan

**When to use:** A new dedicated IP has been provisioned, or the existing IP has been dormant for more than 30 days and ISP reputation has decayed.

**How it works:**
1. Identify the highest-engagement subscriber segment (opened/clicked within 90 days).
2. Week 1: Send 50,000–100,000/day to this segment only. Monitor bounce rates and complaint rates daily.
3. Week 2: Double the daily volume if rates are within limits. Expand to subscribers active within 180 days.
4. Weeks 3–4: Continue doubling every 2–3 days, including moderately engaged segments.
5. Weeks 5–8: Expand to full list. By week 8, the IP should be able to handle full production volume.
6. Never warm up using batch sends to cold or purchased lists. That will establish a bad reputation from day one.

**Why not the alternative:** Sending full volume immediately from a new IP triggers ISP rate limiting and bulk folder routing. The reputation damage can take months to repair.

### Pattern 3: Ongoing List Hygiene Policy

**When to use:** Establishing a standing hygiene process for any Marketing Cloud account to maintain sender reputation over time.

**How it works:**
1. Confirm Marketing Cloud's automatic suppression of hard bounces and triple soft bounces is active (it is by default; do not override it).
2. Build a re-engagement journey for subscribers with no open or click in 6 months. Send 1–2 re-engagement emails. Suppress non-responders.
3. Review the suppression list monthly. Confirm that known complainers from FBL are being added automatically.
4. Audit list growth vs suppression growth quarterly. If suppression is outpacing acquisition, diagnose the source (bad sign-up form, purchased list, etc.).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Send volume < 20,000/day, new program | Shared domain, no dedicated IP | Dedicated IP takes weeks to warm up; shared IP is already established |
| Send volume > 100,000/day, established brand | Private domain + dedicated IP | Reputation isolation; avoids shared IP neighbor effects |
| DMARC p=none is failing DMARC alignment | Verify From domain matches SPF/DKIM signing domain | DMARC requires identifier alignment; mismatch causes p=none reports to flag failures |
| Hard bounce rate > 2% | Pause campaigns, scrub list first | Sending further with high bounce rate accelerates reputation damage |
| IP reputation suddenly degraded | Check spam trap hits and complaint rate via Sender Score or Talos | ISP blacklisting is almost always caused by spam traps or high complaint rates |
| Emails delivered but IPR is low | Run seed-list inbox placement test; review engagement segment targeting | High delivery + low IPR = ISP is accepting but routing to spam; engagement signals must improve |
| Google/Yahoo recipients bulk sending > 5000/day | DMARC p=none minimum, one-click unsubscribe header required | Google/Yahoo 2024 mandate; non-compliance causes bulk folder routing or blocking |

---

## Recommended Workflow

1. **Split the layers, then read the matching runbook.** Answer the Questions above. Core work (nothing arrives, an alert produced no email, a relay, a DKIM key, a settings deploy) goes to `references/metadata-examples.md`; Marketing Cloud reputation work (arriving in spam, warm-up, list hygiene, inbox placement) goes to `references/examples.md`. Do not start in DNS.

2. **Get the org's real state into source before changing anything.** Retrieve `EmailAdministration.settings` and `EmailAuthorization.settings` with the manifest in `references/metadata-examples.md` § 7 — never hand-write them, because the guide's own prose misspells the filename (`references/gotchas.md` Gotcha 7). Run the queries in § 3, § 5 and § 6 to capture the DKIM inventory, unverified org-wide addresses, and current bounce volume, and save them as `deliverability/dkim-keys.json` and `deliverability/email-policy.json`.

3. **Lint before you deploy.** `python3 skills/admin/email-deliverability-strategy/scripts/check_email_deliverability_strategy.py --manifest-dir force-app/main/default` — it rejects undocumented settings elements, the two documented field dependencies, `enableComplianceBcc` with no recorded address, bounce handling off in an org that sends externally, and any sending domain without one published, rotation-dated, active DKIM key. Add `--strict` in CI. Fix every ERROR before `sf project deploy validate`.

4. **Sequence DKIM and DNS against the guide's order, not Setup's.** Insert keys inactive, read back `TxtRecordName` and `AlternateTxtRecordName`, publish both CNAMEs, confirm `TxtRecordsPublishState` reads `Published` and `dig` resolves, and only then set `IsActive = true` (`references/metadata-examples.md` § 3; Gotcha 9). Publish SPF in the same window and DMARC at `p=none` with a monitored `rua=`.

5. **Deploy in the order the surfaces force.** DKIM keys → verified org-wide addresses → the two settings files → relay then domain filter (never the reverse; Gotcha 12) → the manual Deliverability Access Level in every sandbox that must not send. Run the seven verification checks in `references/metadata-examples.md` § 8; check 6 in particular catches bounce handling that was never on.

6. **Then, and only then, do the reputation work.** With Core sending correctly, run the Marketing Cloud track: warm-up schedule, list hygiene policy, and seed-list inbox placement testing (Common Patterns 2 and 3 above; worked versions in `references/examples.md` Examples 2 and 3). Tightening DMARC to `p=quarantine` belongs here, after 30+ days of clean aggregate reports — not in step 4.

7. **Leave the operational hooks behind.** Record DKIM rotation dates and owners in `dkim-keys.json`, wire the checker into CI, book the DMARC report review cadence, and re-read `references/llm-anti-patterns.md` before handing generated DNS or XML to anyone.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] SPF TXT record is present, has exactly one record, and includes the Marketing Cloud include directive
- [ ] DKIM CNAME records are published and validated via MXToolbox DKIM lookup
- [ ] DMARC TXT record is at `_dmarc.<sending-domain>`, policy is at least `p=none`, `rua=` is set
- [ ] DMARC identifier alignment verified: From domain matches SPF or DKIM signing domain
- [ ] If dedicated IP: warm-up plan documented and week 1 volume is within 50,000–100,000/day from engaged segments only
- [ ] Hard bounce automatic suppression confirmed active in Marketing Cloud account
- [ ] Re-engagement journey or sunset policy exists for subscribers inactive > 6 months
- [ ] Sender reputation monitored via at least one tool (Sender Score, Talos, or Barracuda)
- [ ] Google/Yahoo compliance checked: DMARC in place, one-click unsubscribe header present, spam complaint rate < 0.3%
- [ ] `python3 skills/admin/email-deliverability-strategy/scripts/check_email_deliverability_strategy.py --manifest-dir <project>` exits 0
- [ ] `EmailAdministration.settings` is retrieved (not hand-written) and `enableHandleBouncedEmails` is `true` in any org that sends externally
- [ ] `enableComplianceBcc` is either `false` or paired with an address confirmed in Setup > Compliance BCC Email
- [ ] `EmailAuthorizationSettings.enableSubstituteFromAddress` is `false`, or its use is documented with an end date
- [ ] Every sending domain has exactly one active `EmailDomainKey` with `TxtRecordsPublishState = 'Published'`, `KeySize = 2048`, an `AlternateSelector`, and a recorded `nextRotationDue`
- [ ] `SELECT Address, IsVerified FROM OrgWideEmailAddress WHERE IsVerified = false` returns no address referenced by a live alert or Apex send
- [ ] If a relay exists, at least one `EmailDomainFilter` with `IsActive = true` points at it
- [ ] Daily external send volume is counted against the 5,000-address cap **including** email alerts and Flow Send Email actions

---

## Salesforce-Specific Gotchas

The three summarised here are the ones that most often send a diagnosis down the wrong path. `references/gotchas.md` carries all thirteen with the guide citations, split into the Marketing Cloud layer (1-6) and the Salesforce Core layer (7-13: the misspelled settings filename, the `enableEmailSpfCompliance` default, DKIM activation ordering, From-address substitution, the Contact/Lead bounce-field asymmetry, inert relays, and what actually counts against the 5,000-a-day cap).

1. **Duplicate SPF records break authentication silently** — RFC 7208 requires exactly one SPF TXT record per domain. If a previous team added a generic SPF record and a Salesforce admin adds a second one for Marketing Cloud, SPF evaluation fails with a `PermError`. The failure is silent from the sender's perspective but appears in DMARC aggregate reports as authentication failures. Always merge all authorized senders into a single SPF TXT record.
2. **DMARC alignment failure when From domain differs from signing domain** — Marketing Cloud uses a subdomain for sending (e.g., `em.yourbrand.com`) but marketers often set the From header to the corporate domain (`yourbrand.com`). If the DMARC record exists at `yourbrand.com` and the DKIM signing domain is `em.yourbrand.com`, relaxed alignment (the default) will pass. But strict alignment (`aspf=s` or `adkim=s`) will fail. The default relaxed mode passes if the org domain matches — verify the DMARC alignment mode before tightening policy.
3. **Sandbox email deliverability setting does not affect Marketing Cloud** — Salesforce Core sandbox orgs have an email deliverability setting (`System Email Only`, `All Email`) that controls whether the sandbox sends external email. This setting is entirely separate from Marketing Cloud deliverability configuration. Disabling external email in the Core sandbox does not prevent Marketing Cloud from sending, and vice versa.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DNS Record Specification | The exact SPF, DKIM CNAME, and DMARC TXT records to publish, including Marketing Cloud-specific include directives |
| Warm-Up Schedule | Week-by-week volume ramp table by engagement segment, with pass/fail criteria per day |
| List Hygiene Policy Document | Suppression rules, re-engagement journey threshold, inactive sunset criteria |
| Sender Reputation Monitoring Checklist | Tools, monitoring cadence, alert thresholds, and escalation path |
| `EmailAdministration.settings` / `EmailAuthorization.settings` | Deployable org email settings plus the package.xml that retrieves and deploys them |
| `deliverability/dkim-keys.json` | DKIM inventory: domain, selector, alternate selector, key size, publish state, rotation due date, owner |
| `deliverability/email-policy.json` | Sending domains, whether the org sends externally, and the Compliance BCC address — the inputs the checker cross-references |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing, retrieving or reviewing any Salesforce Core artifact: the settings XML, DKIM keys, relay and domain filter, org-wide addresses, bounce SOQL, package.xml, deploy order, verification |
| `references/gotchas.md` | Thirteen platform behaviours that cause production incidents — 1-6 Marketing Cloud / internet standards, 7-13 Salesforce Core with guide citations |
| `references/examples.md` | The Marketing Cloud reputation layer: private-domain setup, dedicated IP warm-up, re-engagement and sunset, and a worked Core diagnosis |
| `references/well-architected.md` | Weighing shared vs dedicated IP, `p=none` vs `p=reject`, and subdomain vs corporate domain — and for the full source list |
| `references/llm-anti-patterns.md` | Reviewing DNS records, settings XML or a warm-up plan an assistant generated, before it reaches an org |

---

## Related Skills

- **admin/email-templates-and-alerts** — Use for template design, merge field configuration, and notification trigger logic. This skill (email-deliverability-strategy) handles whether the email reaches the inbox; email-templates-and-alerts handles what is inside it.
- **admin/email-to-case-configuration** — Use when the goal is routing inbound customer email to Cases, not outbound deliverability. Owns `enableHtmlEmail`, which is an Email-to-Case rendering setting despite living in `EmailAdministrationSettings` alongside the outbound flags.
- **admin/email-service-inbound** — Use for `EmailServicesFunction` and inbound message processing, including the separate inbound daily limit (user licenses × 1,000, capped at 1,000,000 — apexdev.txt L19951-19953) and inbound sender authentication via `isAuthenticationRequired`.
- **devops/sandbox-data-isolation-gotchas** — Contains notes on sandbox-level email deliverability settings (Core org layer) and how they interact with production email routing.
