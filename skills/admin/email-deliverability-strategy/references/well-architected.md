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

**Deployable settings vs Setup-only controls**: Of the six Salesforce Core deliverability controls, only `EmailAdministrationSettings` and `EmailAuthorizationSettings` have a Metadata API type. DKIM keys, the SMTP relay and its domain filter, and org-wide addresses are sObjects loaded through the API; the Deliverability **Access Level** exists only as a Setup page. The tradeoff is unavoidable rather than chosen: any change that touches more than the settings files is a mixed release with a manual step, and the one control that decides whether an org sends at all cannot be diffed between orgs or asserted in CI. The mitigation is to make the non-deployable half explicit — the DKIM inventory and sending policy JSON files that `scripts/check_email_deliverability_strategy.py` reads exist precisely so that state which has no metadata home still has a reviewed, version-controlled home.

**Verified domain vs guaranteed delivery**: `EmailAuthorizationSettings.enableSubstituteFromAddress` frames a genuine choice. At `false` (the default) an unverified sending domain simply cannot send — loud, immediate, unmissable failure. At `true` the mail goes out with a substituted `@…sfcustomeremail.com` From address — delivery succeeds and the brand's authentication, alignment and reputation are all bypassed. The failure mode of `true` is strictly harder to detect than the failure mode of `false`, which is why `false` is the correct steady state and `true` is only ever a dated bridge while verification is completed.

## Anti-Patterns

1. **Publishing DMARC and never reading the reports** — DMARC aggregate reports are the primary signal for authentication health. Teams that publish `p=none` and treat deliverability as done miss ongoing authentication failures from third-party senders, misconfigured DKIM, and spoofing attempts. Reading aggregate reports is non-negotiable.

2. **Rushing dedicated IP warm-up to meet a campaign deadline** — A common pattern is provisioning a dedicated IP one week before a major campaign and attempting to send full volume immediately. This invariably triggers ISP throttling and bulk folder routing during the highest-stakes send of the year. Warm-up must be planned 6–8 weeks ahead of critical sends, not alongside them.

3. **Diagnosing a Core send failure as a DNS problem** — "nobody got the email" from an email alert or Flow is almost never SPF, DKIM or DMARC. It is the Deliverability Access Level, an unverified `OrgWideEmailAddress`, the 5,000-a-day cap, or a substituted From address. All four fail silently, none of them are visible in a Flow debug log, and all four are ruled out in minutes. Reaching for `dig` first spends hours on the layer that was working.

4. **Treating bounce rate as the only deliverability KPI** — Bounce rate measures server-level acceptance, not inbox placement. An organization can have a 0.1% bounce rate and a 40% inbox placement rate, meaning the majority of "delivered" emails are going to spam. Deliverability programs that optimize only for low bounce rates miss the metric that determines whether recipients actually see the content.

## Official Sources Used

- **Metadata API Developer Guide** — `EmailAdministrationSettings`, api_meta.txt L114848-115032 (the 19 documented fields, their defaults, the `enableEmailSpfCompliance` / `enableEmailSenderIdCompliance` and `enableHandleBouncedEmails` / `enableResendBouncedEmails` dependencies, the Compliance BCC and TLS Setup prerequisites, the `EmailAdminstration.settings` filename typo, and the sample definition the metadata example extends). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Metadata API Developer Guide** — `EmailAuthorizationSettings`, api_meta.txt L115053-115116, and `Settings`, L108356-108386 (the `enableSubstituteFromAddress` semantics behind the "verified domain vs guaranteed delivery" tradeoff above; the package.xml member-name rule and the no-wildcard-for-individual-settings rule used in metadata-examples.md § 7). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Object Reference for Salesforce and Lightning Platform** — `EmailDomainKey`, object_reference.txt L103512-103700 (the `DomainMatch`, `KeySize` and `TxtRecordsPublishState` picklists, the read-only `AlternatePublicKey` auto-rotation field, the `PrivateKey`-is-a-token note, and the four-step create-then-activate order that Gotcha 9 rests on). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Object Reference** — `EmailRelay` L104890-105025 and `EmailDomainFilter` L103422-103509 (the `TlsSetting` and `Port` restricted picklists, the `IsRequireAuth` → `RequiredVerify` coupling, the mutual create-order constraint, and "an email relay must be associated with an active email domain filter to take effect" — the whole of Gotcha 12). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Object Reference** — `OrgWideEmailAddress` L206751-206832, `Contact` L71663-71809, `Lead` L163384-163401, `Account` L13772-13786 (`IsVerified` and its API 58.0 floor; the Contact/Lead bounce-field asymmetry and the "not triggered by record updates" note behind Gotcha 11). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Apex Developer Guide** — Outbound Email limits, apexdev.txt L19959-19983, and inbound email-service limits L19946-19958 (the 5,000-external-addresses-a-day cap, what counts in orgs created Spring '19 and later, duplicate counting, `setTargetObjectId` vs `setToAddresses` — the "Outbound Volume Is a Shared Org Budget" concept and Gotcha 13). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Reference Guide** — `Messaging` class, apexrefguide.txt L225128-225190 (`reserveSingleEmailCapacity` / `reserveMassEmailCapacity` and their `System.HandledException` and `System.NoAccessException` messages, and the 10-sends / 100-25-25-recipients per-transaction ceiling). Extracted from the Summer '26 / v62 Apex Reference Guide PDF; no verified PDF URL is recorded for this guide in the repo's source list.
- **Salesforce Well-Architected** — Overview, used for the pillar framing above. https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

### Sources this repo could not verify

The Marketing Cloud layer (Gotchas 1-6, Examples 1-3, Patterns 1-3) rests on the sources below. help.salesforce.com is not fetchable from this repo and Marketing Cloud has no Metadata API or Object Reference surface, so no claim drawn from them is checkable here; each numeric threshold and vendor literal carries an UNVERIFIED marker at the point of use.

- Salesforce Help: Addressing Email Deliverability Issues with Marketing Cloud — https://help.salesforce.com/s/articleView?id=sf.mc_es_deliverability_issues.htm
- Salesforce Help: SPF and Authentication FAQs — https://help.salesforce.com/s/articleView?id=sf.mc_es_spf_faq.htm
- Salesforce Help: Marketing Cloud Deliverability Options — https://help.salesforce.com/s/articleView?id=sf.mc_es_deliverability_options.htm
- Salesforce Help: Email Sending Reputation — https://help.salesforce.com/s/articleView?id=sf.mc_es_sending_reputation.htm
- Google bulk sender guidelines (February 2024) — the previously cited support.google.com page has moved; re-locate the current guidelines before quoting the 5,000/day trigger or the 0.3% complaint threshold.
- Yahoo Sender Best Practices — https://senders.yahooinc.com/best-practices/
- RFC 7208 (SPF) — https://datatracker.ietf.org/doc/html/rfc7208
- RFC 6376 (DKIM) — https://datatracker.ietf.org/doc/html/rfc6376
- RFC 7489 (DMARC) — https://datatracker.ietf.org/doc/html/rfc7489
- RFC 8058 (One-Click Unsubscribe) — https://datatracker.ietf.org/doc/html/rfc8058
