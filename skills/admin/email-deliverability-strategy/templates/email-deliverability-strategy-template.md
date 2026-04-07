# Email Deliverability Strategy — Work Template

Use this template when setting up or auditing email deliverability for a Marketing Cloud or Salesforce org.

## Scope

**Skill:** `admin/email-deliverability-strategy`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding.

- **Sending domain type:** [ ] Private sending domain  [ ] Marketing Cloud shared domain
  - Domain name: `___________________________`
- **Current daily send volume:** _________________ emails/day
- **Target daily send volume:** _________________ emails/day
- **Dedicated IP in use or planned:** [ ] Yes  [ ] No  [ ] Planned — target date: ____________
- **Current hard bounce rate:** _______ % (flag if > 2%)
- **Current spam complaint rate:** _______ % (flag if > 0.1%)
- **DNS admin access confirmed:** [ ] Yes  [ ] No — owner: _______________________

---

## DNS Record Specification

Document the exact records to publish. Verify each with MXToolbox after publication.

### SPF TXT Record

```
<sending-domain>  TXT  "v=spf1 include:_spf.exacttarget.com [additional-includes] ~all"
```

Notes:
- Exactly ONE SPF TXT record per domain
- Total DNS lookups from all `include:` directives must be ≤ 10
- Replace `[additional-includes]` with any other authorized senders (e.g., `include:_spf.google.com`)

### DKIM CNAME Records

Retrieve these values from Marketing Cloud Setup > Private Domains > [your domain] > DNS Records.

```
s1._domainkey.<sending-domain>  CNAME  s1.domainkey.<mc-tenant-id>.pub.sfmc.exacttarget.com
s2._domainkey.<sending-domain>  CNAME  s2.domainkey.<mc-tenant-id>.pub.sfmc.exacttarget.com
```

### DMARC TXT Record

Start at `p=none`. Advance to `p=quarantine` after 30+ days of clean aggregate reports.

```
_dmarc.<sending-domain>  TXT  "v=DMARC1; p=none; rua=mailto:<report-address>; ruf=mailto:<failure-address>; fo=1"
```

- `rua=` — where aggregate (daily XML) reports are sent; use a monitored mailbox or a DMARC report aggregation service
- `ruf=` — where per-message failure reports are sent (optional but recommended during initial setup)
- `fo=1` — generate failure reports for any authentication failure (not just combined SPF+DKIM failure)

---

## Dedicated IP Warm-Up Schedule

Complete this section only if a dedicated IP is in use or being provisioned.

IP address being warmed: `___________________________`

| Week | Daily Volume Target | Subscriber Segment | Pass Criteria | Status |
|------|--------------------|--------------------|---------------|--------|
| 1 | 50,000–100,000 | Opened/clicked within 90 days | Hard bounce < 0.5%, complaint < 0.08% | [ ] |
| 2 | 150,000–200,000 | Opened/clicked within 180 days | Same thresholds | [ ] |
| 3 | 300,000 | Opened/clicked within 12 months | Same thresholds | [ ] |
| 4 | 400,000–500,000 | Full active list | Same thresholds | [ ] |
| 5–8 | Full production | Full active list | Maintain thresholds | [ ] |

**Pause criteria:** Stop sending and investigate if any of the following occur:
- Hard bounce rate > 0.5%
- Spam complaint rate > 0.1%
- Sender Score drops below 80
- ISP throttling messages appear in Marketing Cloud send logs

---

## List Hygiene Policy

| Hygiene Rule | Threshold | Method | Owner | Cadence |
|---|---|---|---|---|
| Hard bounce suppression | After 1st occurrence | Automatic (MC All Subscribers suppression) | Marketing Cloud admin | Automatic |
| Soft bounce suppression | After 3 consecutive | Automatic (MC built-in) | Marketing Cloud admin | Automatic |
| Inactive subscriber sunset | No open/click in 6 months | Re-engagement journey → suppression | Email strategist | Quarterly audit |
| Spam complainer suppression | On FBL report | Automatic (FBL integration) | Marketing Cloud admin | Automatic |
| New list validation | Before first import | Email verification service (optional) | Campaign manager | Per import |

**Re-engagement journey summary:**
- Touch 1: "We miss you" (Day 0) — include incentive
- Touch 2: "Last chance" (Day 7) — send to non-responders only
- Touch 3: "Should we say goodbye?" (Day 10) — explicit opt-out emphasis
- Suppression: Add all non-responders to sunset suppression list `inactive-sunset-YYYY-MM`

---

## Sender Reputation Monitoring

| Tool | URL | What It Measures | Check Cadence |
|---|---|---|---|
| Google Postmaster Tools | https://postmaster.google.com | Domain reputation, IP reputation, spam rate at Gmail | Weekly |
| Sender Score (Validity) | https://senderscore.org | IP reputation score (0–100); target > 80 | Weekly |
| Talos Reputation (Cisco) | https://talosintelligence.com/reputation | IP reputation; used by Cisco/IronPort-based mail servers | Weekly |
| Barracuda Reputation | https://www.barracudacentral.org/lookups | Barracuda blocklist; widely used by enterprise mail gateways | Monthly |
| MXToolbox Blacklist Check | https://mxtoolbox.com/blacklists.aspx | Checks sending IP against 100+ blocklists | After any reputation alert |

**Alert thresholds:**
- Google Postmaster spam rate > 0.1%: investigate immediately
- Sender Score < 80: review recent sends for complaint and bounce spikes
- Any blocklist hit: submit delisting request; pause sends to affected ISP if listed on Spamhaus SBL

---

## Inbox Placement Testing

Run a seed-list inbox placement test after completing authentication setup and after any warm-up milestone.

| ISP | Target IPR | Last Measured | Date | Tool Used |
|---|---|---|---|---|
| Gmail | > 90% | | | |
| Outlook / Hotmail | > 85% | | | |
| Yahoo Mail | > 85% | | | |
| Apple Mail (iCloud) | > 85% | | | |

**Note:** If IPR is above 85% but decreasing month-over-month, investigate whether inactive segments are growing or engagement rates are declining before a threshold breach.

---

## Review Checklist

Copy from SKILL.md and tick items as you complete them:

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

## Notes

Record any deviations from the standard pattern and the rationale:

-
-
