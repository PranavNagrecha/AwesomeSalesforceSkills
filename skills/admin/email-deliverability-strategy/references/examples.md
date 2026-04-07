# Examples — Email Deliverability Strategy

## Example 1: Setting Up Authentication for a New Private Sending Domain

**Context:** A retail brand is launching a Marketing Cloud account for the first time. They have chosen `em.retailbrand.com` as their private sending domain. Their DNS is managed in Cloudflare. Marketing Cloud has generated DKIM keys and provided a list of required DNS records.

**Problem:** Without SPF, DKIM, and DMARC in place, outbound emails fail authentication checks at Gmail and Outlook. Starting in February 2024, Google and Yahoo require DMARC for all senders sending more than 5,000 messages per day. Without DMARC, bulk sends route to spam or are blocked outright.

**Solution:**

```text
# Step 1: SPF TXT record (single record for em.retailbrand.com)
em.retailbrand.com  TXT  "v=spf1 include:_spf.exacttarget.com ~all"

# Step 2: DKIM CNAME records (Marketing Cloud provides these values)
s1._domainkey.em.retailbrand.com  CNAME  s1.domainkey.<mc-tenant-id>.pub.sfmc.exacttarget.com
s2._domainkey.em.retailbrand.com  CNAME  s2.domainkey.<mc-tenant-id>.pub.sfmc.exacttarget.com

# Step 3: DMARC TXT record — start at p=none with aggregate reporting
_dmarc.em.retailbrand.com  TXT  "v=DMARC1; p=none; rua=mailto:dmarc-reports@retailbrand.com; ruf=mailto:dmarc-failures@retailbrand.com; fo=1"
```

**Why it works:** The SPF record authorizes Marketing Cloud's sending IPs. The DKIM CNAMEs allow Marketing Cloud to sign all outbound email with a key bound to `em.retailbrand.com`. The DMARC record at `p=none` satisfies the Google/Yahoo mandate while enabling the team to review aggregate reports before advancing to `p=quarantine`. Advancing policy without reviewing reports first is the most common cause of legitimate email being blocked after a DMARC tightening.

---

## Example 2: Dedicated IP Warm-Up Schedule for a 500,000-Subscriber List

**Context:** A financial services firm has provisioned a dedicated IP for Marketing Cloud. They have 500,000 active subscribers and typically send 3 campaigns per week. The IP was just assigned; it has no sending history with any ISP.

**Problem:** Sending the full list immediately from a cold IP triggers ISP rate limiting and bulk folder placement. Gmail, Outlook, and Yahoo are suspicious of high-volume sends from IPs with no history.

**Solution:**

```text
Warm-Up Schedule — Dedicated IP

Week 1 (Days 1–7):
  - Daily volume: 50,000–75,000
  - Segment: Opened or clicked within last 90 days
  - Monitor: Hard bounce rate < 0.5%, spam complaint rate < 0.08%

Week 2 (Days 8–14):
  - Daily volume: 150,000–200,000
  - Segment: Opened or clicked within last 180 days
  - Monitor: Same thresholds; check Sender Score daily

Week 3 (Days 15–21):
  - Daily volume: 300,000
  - Segment: Opened or clicked within last 12 months
  - Monitor: Check Talos and Barracuda Reputation lookups

Week 4 (Days 22–28):
  - Daily volume: 400,000–500,000
  - Segment: Full active list (excludes hard-bounced and suppressed)
  - Monitor: Inbox placement rate via seed list test at end of week

Pause criteria (any of the following):
  - Hard bounce rate exceeds 0.5% on any send
  - Spam complaint rate exceeds 0.1%
  - Sender Score drops below 80
  - ISP throttling messages appear in MC send logs
```

**Why it works:** ISPs learn to trust an IP by observing consistent, engaged responses to email from that IP. Engagement-first sequencing sends the strongest possible signal (high open rates, low complaints) during the critical establishment window. If the warm-up triggers a pause criterion, diagnosing list quality before resuming is faster and less damaging than pushing through with a degraded reputation.

---

## Example 3: Re-Engagement Journey to Sunset Inactive Subscribers

**Context:** An e-commerce company has 800,000 subscribers. Roughly 300,000 have not opened or clicked any email in 12 months. Their inbox placement rate at Gmail has dropped from 92% to 67% over the past 6 months.

**Problem:** Continuing to send to 300,000 disengaged subscribers suppresses the engagement rate ISPs observe for the sending IP, causing spam folder routing for the entire list including active subscribers.

**Solution:**

```text
Re-Engagement Journey (3-touch):

Touch 1 — Day 0:
  Subject: "We miss you — here's 15% off"
  Segment: No open/click in 12 months
  Wait: 7 days

Touch 2 — Day 7 (send only to non-openers/non-clickers from Touch 1):
  Subject: "Last chance — your discount expires tomorrow"
  Wait: 3 days

Touch 3 — Day 10 (send only to non-responders from Touch 1 and 2):
  Subject: "Should we say goodbye?"
  Include explicit unsubscribe option in body copy

Suppression rule:
  - If subscriber did not open or click any of the 3 touches:
    Add to suppression list "12-month-inactive-sunset-YYYY-MM"
  - Do not delete the record; keep for compliance reporting
  - Re-add to active list only if subscriber re-opts-in via a new form submission
```

**Why it works:** Re-engagement gives the subscriber a genuine opportunity to re-engage before suppression. Sunsetting non-responders removes the deliverability drag of an unresponsive segment. The three-touch approach is proportionate — it avoids suppressing someone who simply missed the first email due to vacation or inbox filters.

---

## Anti-Pattern: Sending to a Purchased or Appended List

**What practitioners do:** To quickly grow a campaign list, a team purchases a 200,000-address list from a data broker or appends email addresses to existing CRM contacts using a third-party data provider.

**What goes wrong:** Purchased lists typically contain a high percentage of invalid addresses, spam traps (addresses maintained by blocklist operators specifically to catch bulk senders), and role accounts (`info@`, `admin@`) that are rarely monitored. A single campaign to a purchased list can generate enough spam complaints and spam trap hits to blacklist the sending IP within 24 hours. Recovery from a Spamhaus listing can take weeks and may require explaining the situation to a Salesforce deliverability specialist.

**Correct approach:** Build the list organically through permission-based acquisition (confirmed opt-in forms, lead magnets, event registration). If list growth is slow, invest in improving the sign-up flow and offer rather than purchasing addresses. If CRM contacts exist without email opt-in, use a re-permission campaign sent through a separate, non-production IP or shared domain, never through the primary dedicated IP.
