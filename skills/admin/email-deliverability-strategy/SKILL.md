---
name: email-deliverability-strategy
description: "Use this skill when configuring or troubleshooting email deliverability for Marketing Cloud or Salesforce orgs: sender authentication (SPF, DKIM, DMARC), private sending domain setup, dedicated IP warm-up, list hygiene practices, and sender reputation monitoring. NOT for email template design, HTML/CSS email coding, or Journey Builder message configuration."
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
outputs:
  - "DNS record specifications for SPF, DKIM, and DMARC"
  - "Dedicated IP warm-up schedule with daily volume ramp"
  - "List hygiene suppression policy and implementation steps"
  - "Sender reputation monitoring checklist"
  - "Decision table: private domain vs shared domain vs dedicated IP"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Email Deliverability Strategy

This skill activates when a practitioner needs to configure sender authentication records, plan a dedicated IP warm-up, establish list hygiene policies, or diagnose why emails are landing in spam. It does NOT cover email template design, dynamic content, Journey Builder flows, or Salesforce Core transactional email limits.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org uses a **private sending domain** (only your organization sends from it) or Marketing Cloud's **shared sending domain** (shared IP pool with other tenants). This distinction drives nearly every downstream decision.
- Ask for the current and target daily send volume. Volume determines whether a dedicated IP is justified (generally >100,000 emails/day) and shapes the warm-up schedule.
- Check if SPF, DKIM, and DMARC records already exist on the sending domain. Duplicate or conflicting SPF records are the most common misconfiguration.
- Know the current hard bounce rate. A rate above 2% is a signal that list hygiene needs immediate attention before any deliverability improvement work will hold.

---

## Core Concepts

### Authentication Trifecta: SPF, DKIM, and DMARC

Email authentication uses three complementary DNS-based standards. All three must be in place before deliverability can be fully controlled.

**SPF (Sender Policy Framework)** is a TXT record on the sending domain that lists the IP addresses and mail transfer agents authorized to send on behalf of that domain. Marketing Cloud provides a specific `include:` statement (e.g., `include:_spf.exacttarget.com`) that must be added to the domain's SPF record. There must be exactly one SPF TXT record per domain; multiple SPF records are invalid per RFC 7208 and cause evaluation failures. The total number of DNS lookups from `include:` directives must not exceed 10.

**DKIM (DomainKeys Identified Mail)** attaches a cryptographic signature to each outbound email. Marketing Cloud generates a DKIM key pair per private sending domain; the public key is published as a CNAME record in DNS pointing to Marketing Cloud's key servers. CNAME-based DKIM (rather than a raw TXT public key) lets Salesforce rotate keys without a DNS change.

**DMARC (Domain-based Message Authentication, Reporting, and Conformance)** is a TXT record at `_dmarc.<yourdomain.com>` that tells receiving mail servers what to do when SPF or DKIM fails: `p=none` (monitor only), `p=quarantine` (send to spam), or `p=reject` (block). Since February 2024 Google and Yahoo require a minimum DMARC policy of `p=none` for any sender sending more than 5,000 messages per day to Gmail or Yahoo addresses. The record must also include `rua=` (aggregate report destination) so receiving servers can report alignment failures back. DMARC also enforces **alignment**: the domain in the `From:` header must match (or be a subdomain of) the SPF or DKIM signing domain.

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

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Assess current state**: Confirm sending domain type (private vs shared), current DNS records (SPF, DKIM, DMARC), daily send volume, and latest bounce/complaint rates. Use MXToolbox or similar to inspect live DNS records.
2. **Fix authentication gaps**: If any of SPF, DKIM, or DMARC are missing or misconfigured, resolve these first. All three must be present and aligned before any other deliverability work is meaningful. Start DMARC at `p=none` and advance to `p=quarantine` or `p=reject` only after reviewing aggregate reports for at least 30 days.
3. **Plan and execute dedicated IP warm-up** (if applicable): Segment the list by engagement recency. Build a week-by-week volume schedule starting at 50,000–100,000/day with the most-engaged subscribers. Do not skip or compress warm-up.
4. **Implement list hygiene policy**: Confirm automatic suppression rules are active. Build a re-engagement flow for inactive subscribers (6-month threshold). Document the suppression policy so it is enforced consistently.
5. **Monitor sender reputation**: Register with Sender Score (Validity/Return Path), check Talos (Cisco), and Barracuda Reputation using the sending IP(s). Set up monitoring alerts for reputation drops. Review DMARC aggregate reports weekly during the first 60 days.
6. **Validate inbox placement**: After authentication and hygiene steps are in place, run a seed-list inbox placement test to confirm IPR has improved across major ISPs (Gmail, Outlook, Yahoo, Apple Mail).
7. **Document and operationalize**: Record the DNS record specifications, warm-up schedule, hygiene thresholds, and monitoring checkpoints in the project context file. Schedule quarterly list hygiene audits.

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

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

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

---

## Related Skills

- **admin/email-templates-and-alerts** — Use for template design, merge field configuration, and notification trigger logic. This skill (email-deliverability-strategy) handles whether the email reaches the inbox; email-templates-and-alerts handles what is inside it.
- **admin/email-to-case-configuration** — Use when the goal is routing inbound customer email to Cases, not outbound deliverability.
- **devops/sandbox-data-isolation-gotchas** — Contains notes on sandbox-level email deliverability settings (Core org layer) and how they interact with production email routing.
