# Well-Architected Notes — Email Deliverability Strategy

## Relevant Pillars

- **Security** — Authentication (SPF, DKIM, DMARC) is fundamentally a security control. It prevents domain spoofing and phishing on behalf of the sending domain. DMARC `p=reject` provides the strongest protection but requires thorough validation before enforcement to avoid blocking legitimate sends.
- **Reliability** — Deliverability depends on consistent infrastructure and process. An IP warm-up that is rushed, a list that is not kept clean, or a DMARC record with a broken `rua=` destination all create fragile configurations that degrade over time. Reliable email delivery requires ongoing maintenance, not one-time setup.
- **Operational Excellence** — Sender reputation monitoring, DMARC report review, and list hygiene audits are operational disciplines. Without defined processes, owners, and cadences, deliverability degrades silently until a campaign fails dramatically. Operationalizing these processes (quarterly audits, alert thresholds, escalation paths) is the difference between reactive firefighting and sustained performance.
- **Performance** — Inbox Placement Rate (IPR) is the performance metric that connects deliverability investment to business outcomes. High delivery rate with low IPR means the infrastructure is accepting emails but ISPs are routing them to spam — a performance failure invisible to server-side delivery logs. Measuring IPR through seed-list testing is required to know whether the sending program is actually performing.

## Architectural Tradeoffs

**Shared IP vs Dedicated IP**: Shared IPs require no warm-up and are appropriate for low-volume or new senders. Dedicated IPs provide reputation isolation but require a 4–8 week warm-up and ongoing volume to maintain the reputation (ISPs "forget" IPs that go quiet for >30 days). The break-even point is approximately 100,000 emails/day. Below that, the warm-up cost and maintenance risk of a dedicated IP typically outweigh the isolation benefit.

**DMARC p=none vs p=reject**: Starting at `p=none` is the correct approach. Jumping to `p=reject` before reviewing aggregate reports will block legitimate third-party sends (transactional email services, CRM tools, partner platforms) that are sending on behalf of the domain but are not yet included in SPF or signing with DKIM. The cost of a false positive at `p=reject` is undelivered legitimate email, which can be worse than the spoofing the policy was intended to prevent.

**Private sending subdomain vs corporate domain**: Using a subdomain for sending (e.g., `em.yourbrand.com`) isolates Marketing Cloud sending reputation from corporate mail infrastructure. If the sending program is compromised or generates spam trap hits, the subdomain's reputation can be isolated and recovered without affecting corporate mail or the parent domain's DMARC policy. This is the recommended pattern for any organization where email marketing and corporate mail coexist.

## Anti-Patterns

1. **Publishing DMARC and never reading the reports** — DMARC aggregate reports are the primary signal for authentication health. Teams that publish `p=none` and treat deliverability as done miss ongoing authentication failures from third-party senders, misconfigured DKIM, and spoofing attempts. Reading aggregate reports is non-negotiable.

2. **Rushing dedicated IP warm-up to meet a campaign deadline** — A common pattern is provisioning a dedicated IP one week before a major campaign and attempting to send full volume immediately. This invariably triggers ISP throttling and bulk folder routing during the highest-stakes send of the year. Warm-up must be planned 6–8 weeks ahead of critical sends, not alongside them.

3. **Treating bounce rate as the only deliverability KPI** — Bounce rate measures server-level acceptance, not inbox placement. An organization can have a 0.1% bounce rate and a 40% inbox placement rate, meaning the majority of "delivered" emails are going to spam. Deliverability programs that optimize only for low bounce rates miss the metric that determines whether recipients actually see the content.

## Official Sources Used

- Salesforce Help: Addressing Email Deliverability Issues with Marketing Cloud — https://help.salesforce.com/s/articleView?id=sf.mc_es_deliverability_issues.htm
- Salesforce Help: SPF and Authentication FAQs — https://help.salesforce.com/s/articleView?id=sf.mc_es_spf_faq.htm
- Salesforce Help: Marketing Cloud Deliverability Options — https://help.salesforce.com/s/articleView?id=sf.mc_es_deliverability_options.htm
- Salesforce Help: Email Sending Reputation — https://help.salesforce.com/s/articleView?id=sf.mc_es_sending_reputation.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Google Sender Guidelines (February 2024) — https://support.google.com/mail/answer/81126
- Yahoo Sender Best Practices — https://senders.yahooinc.com/best-practices/
- RFC 7208 (SPF) — https://datatracker.ietf.org/doc/html/rfc7208
- RFC 6376 (DKIM) — https://datatracker.ietf.org/doc/html/rfc6376
- RFC 7489 (DMARC) — https://datatracker.ietf.org/doc/html/rfc7489
