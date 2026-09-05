# Examples — Email Deliverability Strategy

Examples 1-3 are the **Marketing Cloud reputation layer**. Marketing Cloud has no Metadata API or Object Reference surface, so the vendor literals (`include:` hosts, DKIM CNAME targets) and the numeric thresholds in them cannot be checked against this repo's extracted guides; each carries an UNVERIFIED marker. Example 4 is the **Salesforce Core layer** and every claim in it cites a guide line. Deployable Core artifacts live in `metadata-examples.md`.

## Example 1: Setting Up Authentication for a New Private Sending Domain

**Context:** A retail brand is launching a Marketing Cloud account for the first time. They have chosen `em.retailbrand.com` as their private sending domain. Their DNS is managed in Cloudflare. Marketing Cloud has generated DKIM keys and provided a list of required DNS records.

**Problem:** Without SPF, DKIM, and DMARC in place, outbound emails fail authentication checks at Gmail and Outlook. Starting in February 2024, Google and Yahoo require DMARC for all senders sending more than 5,000 messages per day. Without DMARC, bulk sends route to spam or are blocked outright.

**Solution:**

```text
# Step 1: SPF TXT record (single record for em.retailbrand.com)
em.retailbrand.com  TXT  "v=spf1 include:_spf.exacttarget.com ~all"   # include host: read from MC Setup

# Step 2: DKIM CNAME records (Marketing Cloud provides these values)
s1._domainkey.em.retailbrand.com  CNAME  s1.domainkey.<mc-tenant-id>.pub.sfmc.exacttarget.com
s2._domainkey.em.retailbrand.com  CNAME  s2.domainkey.<mc-tenant-id>.pub.sfmc.exacttarget.com

# Step 3: DMARC TXT record — start at p=none with aggregate reporting
_dmarc.em.retailbrand.com  TXT  "v=DMARC1; p=none; rua=mailto:dmarc-reports@retailbrand.com; ruf=mailto:dmarc-failures@retailbrand.com; fo=1"
```

UNVERIFIED (2026-09-05): the `include:_spf.exacttarget.com` value and both `*.pub.sfmc.exacttarget.com` CNAME targets are Marketing Cloud Setup output, not guide-documented; read the actual values from Setup > Private Domains for the account in hand rather than pasting these. The `_dmarc` record shape is RFC 7489.

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

UNVERIFIED (2026-09-05): every volume figure and threshold in this schedule (50k-75k week 1, 0.5% bounce, 0.1% complaint, Sender Score 80) is industry warm-up practice, not a Salesforce-documented limit. Confirm the current numbers with the account's Marketing Cloud deliverability contact before committing to a send calendar.

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

## Example 4: "The Flow Ran and Nobody Got the Email" (Salesforce Core)

**Context:** A Service Cloud org fires a case-acknowledgement email alert from a record-triggered Flow. The Flow interviews complete successfully with no fault paths taken, the debug log shows the Send Email element executing, and customers report receiving nothing. Two weeks earlier an admin "fixed" a wave of send errors in a sandbox and the change was promoted.

**Problem:** Every deliverability instinct points at DNS. None of it applies — nothing left the platform, or what left carried a Salesforce From address. Four Core controls can produce this exact symptom, and only one of them is visible in a Flow debug log.

**Solution — work the four in this order, cheapest first:**

```sql
-- 1. Is the org allowed to send at all?  (Deliverability Access Level, Setup only)
--    No SOQL exists. Setup > Email > Deliverability > Access level.
--    Apex confirms it: Messaging.reserveSingleEmailCapacity(1) throws
--    System.NoAccessException: The organization is not permitted to send email.
--    (apexrefguide.txt L225158)

-- 2. Is the alert's From identity verified?  IsVerified requires API 58.0+
SELECT Id, Address, DisplayName, Purpose, IsAllowAllProfiles, IsVerified
FROM OrgWideEmailAddress
WHERE IsVerified = false

-- 3. Did we blow the daily cap?  There is NO queryable counter for it -- the
--    org is notified by email and a debug-log entry, not an exception
--    (apexdev.txt L19964-19966). EmailMessage only holds sends that were
--    saved to Salesforce, so this is a floor on volume, never the count:
SELECT COUNT(Id) saved_outbound_today
FROM EmailMessage
WHERE Incoming = false AND CreatedDate = TODAY
--    Incoming = false means "sent" rather than "received"
--    (object_reference.txt L104280-104285). Email alerts and Flow Send Email
--    actions count against the same 5,000 external addresses/day in orgs
--    created Spring '19 or later (apexdev.txt L19961-19964).

-- 4. Is bounce handling on, so failures would even be recorded?
SELECT COUNT(Id) bounced_contacts FROM Contact WHERE IsEmailBounced = true
-- Zero in a mature org means enableHandleBouncedEmails is off, not that
-- nothing bounces (object_reference.txt L71679).
```

Then check the setting the sandbox "fix" most likely touched:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- settings/EmailAuthorization.settings-meta.xml — the state to look for -->
<EmailAuthorizationSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- true: sends go out as email@<orgId>.sfcustomeremail.com from any
         unverified domain — mail "delivered", brand reputation bypassed.
         false (the default): unverified domains cannot send at all.
         api_meta.txt L115074-115084, API 66.0+ -->
    <enableSubstituteFromAddress>false</enableSubstituteFromAddress>
</EmailAuthorizationSettings>
```

**Why it works:** Each step eliminates a control that produces silence rather than an error, and the order matches how cheap the check is against how often it is the cause. Access Level is the only one with no queryable surface, which is exactly why it is checked first — it is also the one a sandbox refresh resets. `enableSubstituteFromAddress` is the trap in this scenario: at `true` the customer *does* receive mail, from an address they do not recognise and did not allow-list, so "nobody got the email" and "delivery succeeded" are both true at once. None of the four are fixed by a DNS record, and running the checker (`--manifest-dir`) over the promoted settings would have caught steps 3 and 4 before the deploy.

---

## Anti-Pattern: Sending to a Purchased or Appended List

**What practitioners do:** To quickly grow a campaign list, a team purchases a 200,000-address list from a data broker or appends email addresses to existing CRM contacts using a third-party data provider.

**What goes wrong:** Purchased lists typically contain a high percentage of invalid addresses, spam traps (addresses maintained by blocklist operators specifically to catch bulk senders), and role accounts (`info@`, `admin@`) that are rarely monitored. A single campaign to a purchased list can generate enough spam complaints and spam trap hits to blacklist the sending IP within 24 hours. Recovery from a Spamhaus listing can take weeks and may require explaining the situation to a Salesforce deliverability specialist.

**Correct approach:** Build the list organically through permission-based acquisition (confirmed opt-in forms, lead magnets, event registration). If list growth is slow, invest in improving the sign-up flow and offer rather than purchasing addresses. If CRM contacts exist without email opt-in, use a re-permission campaign sent through a separate, non-production IP or shared domain, never through the primary dedicated IP.
