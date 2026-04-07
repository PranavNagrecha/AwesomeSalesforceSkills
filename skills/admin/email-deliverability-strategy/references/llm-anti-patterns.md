# LLM Anti-Patterns — Email Deliverability Strategy

Common mistakes AI coding assistants make when generating or advising on Email Deliverability Strategy.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Publishing Two Separate SPF TXT Records

**What the LLM generates:** Two separate TXT records for the same domain:
```
em.domain.com  TXT  "v=spf1 include:_spf.google.com ~all"
em.domain.com  TXT  "v=spf1 include:_spf.exacttarget.com ~all"
```

**Why it happens:** LLMs are trained on documentation for individual systems (Google Workspace, Marketing Cloud) in isolation. When composing a combined setup, they model each system's documentation independently and output one record per system without recognizing the RFC 7208 constraint that there must be exactly one SPF TXT record per domain.

**Correct pattern:**
```
em.domain.com  TXT  "v=spf1 include:_spf.google.com include:_spf.exacttarget.com ~all"
```

**Detection hint:** If the output contains two or more TXT record lines for the same domain where both begin with `v=spf1`, flag it as invalid.

---

## Anti-Pattern 2: Recommending DMARC p=reject as the Starting Policy

**What the LLM generates:**
```
_dmarc.em.domain.com  TXT  "v=DMARC1; p=reject; rua=mailto:dmarc@domain.com"
```
With advice like: "Set p=reject to get maximum protection immediately."

**Why it happens:** LLMs optimize for the security-maximizing answer. DMARC `p=reject` is described as the strongest policy in training data, so LLMs recommend it directly without accounting for the operational prerequisite of reviewing aggregate reports to confirm all legitimate send paths pass authentication.

**Correct pattern:**
```
_dmarc.em.domain.com  TXT  "v=DMARC1; p=none; rua=mailto:dmarc@domain.com; ruf=mailto:dmarc-failures@domain.com; fo=1"
```
Start at `p=none`, review aggregate reports for a minimum of 30 days, then advance to `p=quarantine`, and only then to `p=reject` once 95%+ of legitimate sends show DMARC pass.

**Detection hint:** If the output recommends `p=reject` without mentioning aggregate report review or a staged rollout, flag it.

---

## Anti-Pattern 3: Treating Delivery Rate as the Primary Deliverability KPI

**What the LLM generates:** Reports or dashboards that show "delivery rate: 99.8%" and conclude deliverability is healthy, without mentioning inbox placement rate.

**Why it happens:** Delivery rate is the metric most prominently surfaced in Marketing Cloud send reports and is what most training data about email marketing KPIs discusses. Inbox Placement Rate (IPR) requires separate seed-list tooling that is less commonly documented and less often present in training corpora.

**Correct pattern:**
```
Deliverability health requires two distinct metrics:
1. Delivery Rate — percentage of emails accepted by receiving mail server (99.8% is typical and expected)
2. Inbox Placement Rate (IPR) — percentage of delivered emails landing in inbox vs spam/junk
   - Measure using seed-list tools: Validity (Return Path), 250ok, GlockApps
   - Target: >90% for Gmail, >85% for Outlook
   - A 99.8% delivery rate combined with a 60% IPR means 40% of sends go to spam
```

**Detection hint:** If the output only references delivery rate or bounce rate and does not mention IPR or inbox placement, the deliverability assessment is incomplete.

---

## Anti-Pattern 4: Assuming Marketing Cloud Warm-Up Is Done After One Week

**What the LLM generates:** A warm-up plan that runs for 5–7 days before concluding "the IP is now warmed up and ready for full volume."

**Why it happens:** LLMs often compress timelines when generating structured plans. Warm-up is described in training data as a gradual ramp, but the specifics of ISP throttling windows and the 4–8 week standard are less consistently represented than the general concept.

**Correct pattern:**
```
Dedicated IP warm-up timeline:
- Week 1: 50,000–100,000/day, engaged-only segment (90-day opens/clicks)
- Week 2: 150,000–200,000/day, 180-day segment
- Week 3: 300,000/day, 12-month segment
- Week 4+: Scale to full list
- Total duration: 4–8 weeks depending on list size and ISP response
- Pause if: hard bounce > 0.5%, spam complaint > 0.1%, Sender Score drops below 80
```

**Detection hint:** If the warm-up plan shows full production volume by day 7, flag the timeline as too compressed for standard ISP warm-up expectations.

---

## Anti-Pattern 5: Recommending a Purchased or Rented Email List as a Growth Strategy

**What the LLM generates:** "To quickly build your list for the campaign launch, you could supplement with a targeted purchased list from a reputable data broker."

**Why it happens:** List purchasing appears in general marketing training data as a common (if controversial) acquisition tactic. LLMs may generate it as a neutral option without knowledge of the specific consequences for email deliverability infrastructure: spam trap hits, immediate IP blacklisting, and the destruction of a newly warmed dedicated IP.

**Correct pattern:**
```
Do not send to purchased, rented, or appended lists using a primary production sending IP.
Consequences:
- Purchased lists contain spam traps maintained by Spamhaus, SURBL, and major ISPs
- A single campaign to a trap-seeded list can result in IP blacklisting within 24 hours
- Recovery from a Spamhaus SBL listing typically requires weeks and a formal delisting request
- The warm-up investment is destroyed

If re-permission outreach to cold contacts is required:
- Use a separate, non-production IP or Marketing Cloud shared IP
- Send a single re-permission email; suppress all non-responders immediately
- Never include cold contacts in warm-up segments
```

**Detection hint:** If the output suggests purchasing, renting, or appending email lists, flag it as a deliverability risk regardless of the marketing context.

---

## Anti-Pattern 6: Skipping the One-Click Unsubscribe Header for Custom Templates

**What the LLM generates:** A custom HTML email template with a footer unsubscribe link (`<a href="%%unsub_center_prefix%%...">Unsubscribe</a>`) but without the `List-Unsubscribe` and `List-Unsubscribe-Post` HTTP headers.

**Why it happens:** The `List-Unsubscribe-Post` header requirement was added in February 2024. LLMs trained on data before that date, or trained primarily on Marketing Cloud documentation rather than the Google/Yahoo sender guidelines, generate compliant-looking templates that are missing this header.

**Correct pattern:**
```
For Marketing Cloud standard templates:
- Use the built-in SafeUnsubscribe or Unsubscribe Footer content area
- Marketing Cloud inserts List-Unsubscribe and List-Unsubscribe-Post headers automatically

For custom templates or custom From configurations:
- Verify headers are present by sending a test to a Gmail address
- Inspect the raw message source for:
    List-Unsubscribe: <https://click.em.yourdomain.com/unsub/...>, <mailto:unsub@em.yourdomain.com>
    List-Unsubscribe-Post: List-Unsubscribe=One-Click
- If headers are absent, report the gap — they cannot be added via template HTML alone
```

**Detection hint:** If a custom template is generated without mention of `List-Unsubscribe-Post` headers, and the send volume exceeds 5,000/day to Gmail or Yahoo recipients, flag it as non-compliant with the 2024 Google/Yahoo requirements.
