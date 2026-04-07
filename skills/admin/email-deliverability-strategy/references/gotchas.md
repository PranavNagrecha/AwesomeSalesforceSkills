# Gotchas — Email Deliverability Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Multiple SPF TXT Records Cause Silent PermError

**What happens:** SPF authentication returns a `PermError` result, which most receiving servers treat as a soft failure or reject. Emails may pass DMARC alignment checks intermittently or fail consistently depending on the receiving server's policy for `PermError`. This does not generate a user-visible bounce; the failure appears only in DMARC aggregate reports.

**When it occurs:** When a Salesforce admin adds Marketing Cloud's SPF include (`include:_spf.exacttarget.com`) as a new TXT record, without realizing a generic SPF record already exists for the domain from a previous mail provider or IT team. The result is two TXT records beginning with `v=spf1 ...`, which RFC 7208 explicitly forbids.

**How to avoid:** Before adding any SPF record, query existing TXT records for the sending domain using `dig TXT em.yourdomain.com` or MXToolbox. If an SPF record already exists, merge the new include directive into the existing record rather than creating a second record. The final record should be a single TXT value with all include directives and a trailing `-all` or `~all`.

---

## Gotcha 2: DMARC Aggregate Reports Require Monitoring — Not Just Publication

**What happens:** Teams publish a DMARC record at `p=none` to satisfy the Google/Yahoo mandate and then never read the aggregate reports. The `rua=` destination receives daily XML reports from Gmail, Yahoo, Outlook, and other receivers indicating which sources passed or failed SPF/DKIM alignment. Without reviewing these reports, authentication misconfigurations (e.g., third-party ESP not included in SPF, DKIM signing failure) go undetected for months.

**When it occurs:** After the initial DMARC TXT record is published and the team considers deliverability "set up." The reports arrive as email attachments in XML format and are not human-readable without a report parser.

**How to avoid:** Use a DMARC report aggregation service (Validity/Return Path, Postmark's DMARC Digests, or dmarcian) to parse and visualize aggregate reports. Set a calendar reminder to review reports at least weekly for the first 60 days after DMARC publication, and monthly thereafter. Before advancing DMARC policy from `p=none` to `p=quarantine`, verify that 95%+ of legitimate sends show DMARC pass in the reports.

---

## Gotcha 3: Warm-Up Applies Per IP, Not Per Domain

**What happens:** When an organization switches from a shared IP to a dedicated IP, they may assume that the sending reputation built on the shared IP transfers to the new dedicated IP. It does not. IP reputation is tracked per IP address by ISPs. The new dedicated IP starts with zero history and will be throttled regardless of how good the organization's sending practices were on the shared IP.

**When it occurs:** During a dedicated IP provisioning event — either when Marketing Cloud first sets up a dedicated IP for the account, or when the existing dedicated IP is changed or added to.

**How to avoid:** Plan the warm-up before the IP switch, not after the first failed send. Schedule 4–8 weeks of warm-up traffic on the new IP before routing production campaigns through it. If the timeline cannot accommodate a full warm-up, consider keeping the shared IP as the primary sending IP until the dedicated IP is established.

---

## Gotcha 4: Marketing Cloud Auto-Suppression Does Not Prevent All Harmful Sends Before the Bounce Occurs

**What happens:** Marketing Cloud automatically suppresses hard-bounced addresses after the first bounce and soft-bounced addresses after three consecutive bounces. However, the bounce event must occur and be processed before the suppression takes effect. If a list contains thousands of invalid addresses that have never been sent to before, the first campaign to that list will generate all those bounces simultaneously before any suppression is applied.

**When it occurs:** When importing a new list that has not been validated prior to import, or when importing an old list that was not cleaned since last use.

**How to avoid:** Validate email address syntax and domain existence before importing lists into Marketing Cloud. Consider an email verification service (ZeroBounce, NeverBounce, etc.) for any list over 10,000 addresses that is more than 3 months old. Treat the first send to any new imported list as a test send: use a sub-segment of 5,000–10,000 addresses first, check bounce rates, then proceed with the full list.

---

## Gotcha 5: Spam Complaint Rate Threshold Is Much Lower Than Most Teams Expect

**What happens:** Teams monitor bounce rates closely but overlook spam complaint rate until it causes IP blacklisting or ISP blocking. The acceptable spam complaint rate is far lower than typical marketing metrics suggest.

**When it occurs:** When teams interpret a 0.5% complaint rate as "low" based on other marketing KPI benchmarks (a 0.5% click rate would be considered very good). A 0.5% spam complaint rate is catastrophically high for email deliverability purposes.

**How to avoid:** Google's 2024 sending guidelines specify a maximum complaint rate of 0.3% (as measured in Google Postmaster Tools), with a recommended rate below 0.1%. Monitor spam complaint rate via Google Postmaster Tools (free, requires domain verification) and the FBL data available through Marketing Cloud. If complaint rate rises above 0.1%, immediately investigate which send triggered the spike, review the list segment, subject line, and content, and pause sends to the affected segment until the root cause is resolved.

---

## Gotcha 6: One-Click Unsubscribe Is a 2024 Requirement, Not a Best Practice

**What happens:** Prior to 2024, best practice was to include a visible unsubscribe link in the email footer that led to a preference center. Google and Yahoo's February 2024 requirements added a technical mandate: bulk senders must support the `List-Unsubscribe` and `List-Unsubscribe-Post` headers so recipients can unsubscribe with a single click directly from the Gmail or Yahoo interface without visiting a preference center. Emails sent without this header by bulk senders (>5,000/day) are flagged as non-compliant.

**When it occurs:** When using older Marketing Cloud email templates that predate the header requirement, or when custom sends bypass the standard Marketing Cloud unsubscribe mechanism.

**How to avoid:** Marketing Cloud's standard Unsubscribe Footer and SafeUnsubscribe center insert the required headers automatically. Confirm that any custom templates or custom From/Reply-To configurations also include the header. Test by sending a seed message to a Gmail account and inspecting the message source for the `List-Unsubscribe-Post` header.
