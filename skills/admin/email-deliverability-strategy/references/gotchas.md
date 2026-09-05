# Gotchas — Email Deliverability Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Gotchas 1-6 are the **Marketing Cloud / internet-standard** layer: they rest on RFC 7208 / 6376 / 7489, on Google and Yahoo receiver policy, and on Marketing Cloud Help articles listed in `well-architected.md` § Official Sources Used. None of that is checkable against the Salesforce developer guides this repo extracts, so the vendor literals and numeric thresholds in them carry an UNVERIFIED marker. Gotchas 7-13 are the **Salesforce Core** layer and every claim in them cites a guide line.

## Gotcha 1: Multiple SPF TXT Records Cause Silent PermError

**What happens:** SPF authentication returns a `PermError` result, which most receiving servers treat as a soft failure or reject. Emails may pass DMARC alignment checks intermittently or fail consistently depending on the receiving server's policy for `PermError`. This does not generate a user-visible bounce; the failure appears only in DMARC aggregate reports.

**When it occurs:** When a Salesforce admin adds Marketing Cloud's SPF include (`include:_spf.exacttarget.com` — UNVERIFIED (2026-09-05): the include-host literal is from Marketing Cloud Setup, not from any guide in this repo's corpus; take the real value from Setup > Private Domains for the account in hand) as a new TXT record, without realizing a generic SPF record already exists for the domain from a previous mail provider or IT team. The result is two TXT records beginning with `v=spf1 ...`, which RFC 7208 explicitly forbids.

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

**What happens:** Marketing Cloud automatically suppresses hard-bounced addresses after the first bounce and soft-bounced addresses after three consecutive bounces. UNVERIFIED (2026-09-05): both suppression thresholds are Marketing Cloud Help behaviour; help.salesforce.com is not fetchable from this repo and Marketing Cloud has no Metadata API or Object Reference surface to check them against. Salesforce Core's equivalent is `enableHandleBouncedEmails` writing `EmailBouncedDate` on Contact and Lead — see Gotcha 11. However, the bounce event must occur and be processed before the suppression takes effect. If a list contains thousands of invalid addresses that have never been sent to before, the first campaign to that list will generate all those bounces simultaneously before any suppression is applied.

**When it occurs:** When importing a new list that has not been validated prior to import, or when importing an old list that was not cleaned since last use.

**How to avoid:** Validate email address syntax and domain existence before importing lists into Marketing Cloud. Consider an email verification service (ZeroBounce, NeverBounce, etc.) for any list over 10,000 addresses that is more than 3 months old. Treat the first send to any new imported list as a test send: use a sub-segment of 5,000–10,000 addresses first, check bounce rates, then proceed with the full list.

---

## Gotcha 5: Spam Complaint Rate Threshold Is Much Lower Than Most Teams Expect

**What happens:** Teams monitor bounce rates closely but overlook spam complaint rate until it causes IP blacklisting or ISP blocking. The acceptable spam complaint rate is far lower than typical marketing metrics suggest.

**When it occurs:** When teams interpret a 0.5% complaint rate as "low" based on other marketing KPI benchmarks (a 0.5% click rate would be considered very good). A 0.5% spam complaint rate is catastrophically high for email deliverability purposes.

**How to avoid:** Google's 2024 sending guidelines specify a maximum complaint rate of 0.3% (as measured in Google Postmaster Tools), with a recommended rate below 0.1%. UNVERIFIED (2026-09-05): these are Google receiver thresholds, not Salesforce limits; no Salesforce guide states a complaint-rate number, and the Google sender-guidelines page previously cited here has since moved. Re-read Google's current bulk-sender guidelines before quoting the figures to a client. Monitor spam complaint rate via Google Postmaster Tools (free, requires domain verification) and the FBL data available through Marketing Cloud. If complaint rate rises above 0.1%, immediately investigate which send triggered the spike, review the list segment, subject line, and content, and pause sends to the affected segment until the root cause is resolved.

---

## Gotcha 6: One-Click Unsubscribe Is a 2024 Requirement, Not a Best Practice

**What happens:** Prior to 2024, best practice was to include a visible unsubscribe link in the email footer that led to a preference center. Google and Yahoo's February 2024 requirements added a technical mandate: bulk senders must support the `List-Unsubscribe` and `List-Unsubscribe-Post` headers (RFC 8058) — UNVERIFIED (2026-09-05): receiver policy set by Google and Yahoo, not by Salesforce; the 5,000/day trigger volume and the enforcement date are theirs and change so recipients can unsubscribe with a single click directly from the Gmail or Yahoo interface without visiting a preference center. Emails sent without this header by bulk senders (>5,000/day) are flagged as non-compliant.

**When it occurs:** When using older Marketing Cloud email templates that predate the header requirement, or when custom sends bypass the standard Marketing Cloud unsubscribe mechanism.

**How to avoid:** Marketing Cloud's standard Unsubscribe Footer and SafeUnsubscribe center insert the required headers automatically. Confirm that any custom templates or custom From/Reply-To configurations also include the header. Test by sending a seed message to a Gmail account and inspecting the message source for the `List-Unsubscribe-Post` header.

---

## Gotcha 7: The Metadata API Guide Misspells the Settings Filename It Tells You to Create

**What happens:** A retrieve or deploy of the org's email administration settings fails to find the file, or an agent hand-writing the file names it `EmailAdminstration.settings` and the deploy reports an unknown component. The Metadata API Developer Guide's prose reads, verbatim (api_meta.txt L114855): `EmailAdministrationSettings values are stored in the EmailAdminstration.settings file in the settings directory.` — "Adminstration" is missing its second `i`.

**When it occurs:** Whenever the filename is taken from the type's own section rather than from the general `Settings` rule. It bites hardest when an AI assistant is asked to "create the email settings file from the guide", because that sentence is the most quotable line in the section.

**How to avoid:** Trust the general rule instead: "The filename uses the format *Setting feature*`.settings`. For example, the SecuritySettings file would be `Security.settings`" (api_meta.txt L108379-108383). The same guide's own package.xml sample for this type uses `<members>EmailAdministration</members>` (api_meta.txt L115029). The correct file is `settings/EmailAdministration.settings-meta.xml`. Never hand-write it — retrieve it first with the manifest in `references/metadata-examples.md` § 7 and edit what comes back.

---

## Gotcha 8: `enableEmailSpfCompliance` Already Defaults to True, and Sender ID Silently Depends On It

**What happens:** Two failures in opposite directions from the same field pair. Setting `enableEmailSenderIdCompliance` to `true` without also setting `enableEmailSpfCompliance` to `true` is rejected — the guide states the prerequisite outright: "To enable this preference, `enableEmailSpfCompliance` must be set to `true`" (api_meta.txt L114884-114887). And an admin who flips `enableEmailSpfCompliance` to `false` while debugging a relay problem is not "leaving it as it was" — that field is documented with "a default value of **true**" (api_meta.txt L114893-114895), the only enable-flag in the whole 19-field type whose default is on.

**When it occurs:** During a first deploy of `EmailAdministration.settings` written from scratch rather than retrieved, and during relay or third-party-sender troubleshooting where turning compliance checks off looks like a diagnostic step. The org-wide effect of the second case is invisible until a receiver starts rejecting mail weeks later.

**How to avoid:** Retrieve the settings before editing so the true baseline is in the diff. Treat `enableEmailSpfCompliance` as on unless there is a written reason. Read the guide's own caution before enabling Sender ID at all — it sits directly beside the field (api_meta.txt L114889-114891): "Evaluate the multiple standard email security protocols (SPF, DKIM, and DMARC) supported by Salesforce before you enable this setting." Sender ID is a largely abandoned Microsoft protocol; SPF plus DKIM plus DMARC is the modern set. While you are in the file, check that `enableSendThroughGmailPref` is absent — the guide documents it in a single word, `Deprecated.` (api_meta.txt L114964) — and that the live `enableSendViaGmailPref` (L114969) carries the intent instead.

---

## Gotcha 9: Activating a DKIM Key Before Its CNAMEs Resolve Breaks Every Signature

**What happens:** `EmailDomainKey.IsActive` is set to `true` as soon as the record is created, so Salesforce starts signing outbound mail with a key whose public half no receiver can look up. Every message then carries a DKIM signature that fails verification — which is strictly worse than sending unsigned mail, because a DKIM `fail` is an explicit negative signal to a DMARC evaluator where absence is merely neutral.

**When it occurs:** Any time DKIM keys are created through the API or Data Loader instead of clicked through Setup, because `IsActive` is `Create`-able (object_reference.txt L103595-103600) and an insert CSV with `IsActive,true` is the obvious thing to write. It also occurs when DNS propagation is assumed rather than checked.

**How to avoid:** Follow the four-step order the Object Reference prescribes (object_reference.txt L103679-103698), which puts activation last: insert `Domain`, `DomainMatch`, `Selector` and `AlternateSelector`; read back `TxtRecordName` and `AlternateTxtRecordName`; publish both CNAMEs (`<selector>._domainkey.<domain> IN CNAME txtRecordName`); *then* set `IsActive` to `true`. Gate step four on `TxtRecordsPublishState` reading `Published` — the other two documented values are `Publishing in progress` and `Publishing failed` (object_reference.txt L103665-103674) — and on `dig CNAME <selector>._domainkey.<domain>` resolving. Note also that `DomainMatch` decides scope: a `DomainOnly` key on the parent domain does not sign anything sent from a marketing subdomain (object_reference.txt L103573-103594).

---

## Gotcha 10: An Unverified Sending Domain Rewrites Your From Address to a Salesforce One

**What happens:** Outbound email leaves with a From address of `email@UniqueId.sfcustomeremail.com` instead of your domain, where `UniqueId` is the org ID or Experience Cloud site ID. Every reputation signal — SPF alignment, DKIM signing domain, DMARC policy, the recipient's own allow-list — attaches to `sfcustomeremail.com`, not to you. Replies go nowhere useful and the mail is far more likely to be filtered. The alternative behaviour is not better: with the setting off, affected sends simply do not go out.

**When it occurs:** When `EmailAuthorizationSettings.enableSubstituteFromAddress` is `true` and a sending domain has not completed domain-level verification (api_meta.txt L115074-115084, API 66.0 and later). The default is `false`, which "[means] Salesforce users and automations can send messages from Salesforce only when the email domain is verified" (api_meta.txt L115081-115082) — so an org that flips it to `true` to stop a wave of send failures has traded visible failures for invisible reputation damage.

**How to avoid:** Treat `enableSubstituteFromAddress: true` as a temporary bridge with an end date, never as a fix, and record the verification work it is standing in for. Verify the domain, then set it back to `false`. Check the related surface at the same time: `OrgWideEmailAddress.IsVerified` defaults to `false` and is only available in API version 58.0 and later (object_reference.txt L206797-206804), so `SELECT Address, IsVerified FROM OrgWideEmailAddress WHERE IsVerified = false` both audits your From identities and confirms the org is on a recent enough API version to have the field at all.

---

## Gotcha 11: Lead Has No `IsEmailBounced` Field, and Its Bounce Fields Are Not Createable

**What happens:** Two separate failures from the same asymmetry. A bounce dashboard that unions Contact and Lead on `IsEmailBounced` silently drops every bounced Lead, because that field exists on Contact and does not exist on Lead at all (object_reference.txt L71802-71809 vs L163384-163401). And a migration or backfill CSV carrying bounce history inserts cleanly on Contact and fails on Lead, because `Lead.EmailBouncedDate` is documented `Filter, Nillable, Sort, Update` — no `Create` (object_reference.txt L163384-163387) — while `Contact.EmailBouncedDate` is `Create, Filter, Nillable, Sort, Update` (L71663-71666).

**When it occurs:** When building the suppression-audit report that a hygiene programme depends on, and during any org merge or CRM migration that tries to preserve which addresses are known bad.

**How to avoid:** Query Leads on `EmailBouncedDate != NULL` and Contacts on `IsEmailBounced = true`; do not assume one field spans both. Expect them to disagree even on Contact: `IsEmailBounced` covers "a soft or hard bounce" (object_reference.txt L71808) while `EmailBouncedDate` is documented for a hard bounce (L71679), so a `true` flag with a null date is a soft bounce, not a data error. On Lead, set bounce fields with a post-insert update rather than in the insert. And read the note both objects carry (object_reference.txt L71682-71684, L163390-163392): "Email bounce functionality isn't triggered by record updates, including updates to this field" — blanking `EmailBouncedDate` through the Data Loader clears the flag without re-testing whether the address is still bad. All of these fields stay empty entirely unless `enableHandleBouncedEmails` is on.

---

## Gotcha 12: An Email Relay With No Active Domain Filter Does Nothing, Silently

**What happens:** An `EmailRelay` record exists, points at the right SMTP host, and has correct credentials — and Salesforce keeps sending everything through its own infrastructure as if the relay were not there. There is no error and no log entry saying the relay was skipped. The Object Reference states the requirement plainly: "An email relay must be associated with an active email domain filter to take effect" (object_reference.txt L105018).

**When it occurs:** During a relay rollout where the `EmailDomainFilter` step was missed, deferred, or loaded with `IsActive` left at its default. The ordering is also forced in the other direction — "You must create an email relay in Setup or through the EmailRelay object before you can use the EmailDomainFilter object" (object_reference.txt L103433) — so a single-pass load of both objects fails on the filter and leaves an orphaned, inert relay behind.

**How to avoid:** Load the relay first, capture its Id, then load at least one `EmailDomainFilter` with `IsActive = true` referencing it. Verify with `SELECT EmailRelayId, PriorityNumber, IsActive FROM EmailDomainFilter WHERE IsActive = true`. Watch two more traps in the same objects: `IsRequireAuth = true` forces `TlsSetting` to `RequiredVerify` (object_reference.txt L104935-104941), so an auth-enabled relay pointing at a host with a mismatched certificate common name terminates the session and delivers nothing; and `PriorityNumber` must be unique with "Processing [stopping] after the first matching filter is applied" (object_reference.txt L103476-103493), so a broad catch-all filter with a low priority number shadows every specific rule after it.

---

## Gotcha 13: The 5,000-a-Day Cap Counts Flow and Email Alerts Too — Rate Limiting Does Not Move the Budget

**What happens:** A team throttling outbound volume for deliverability reasons moves sends out of Apex and into Flow Send Email actions or email alerts, believing only Apex and API sends are metered. In an org created in Spring '19 or later they are metered identically, and the daily limit is reached at the same point as before. The Apex Developer Guide is explicit (apexdev.txt L19959-19966): each licensed org sends single emails to "a maximum of 5,000 external email addresses per day based on Greenwich Mean Time"; for pre-Spring '19 orgs the cap is enforced only for Apex and API except REST, but "For orgs created in Spring '19 and later, the daily limit is also enforced for email alerts, simple email actions, Send Email actions in flows, and REST API."

**When it occurs:** On the day a campaign, a bulk case-notification, or a migration-triggered wave of automation crosses the cap. The failure mode is quiet by design: "If one of the newly counted emails can't be sent because your org has reached the limit, we notify you by email and add an entry to the debug logs" — an email and a log line, not an exception at the point of send.

**How to avoid:** Count against the real budget before designing the throttle. Duplicates are not deduplicated: "if you have johndoe@example.com in your email 10 times that counts as 10 against the limit" (apexdev.txt L19976-19978). Mass email and list email carry their own 5,000-a-day external cap. For internal recipients, `setTargetObjectId` with a user's Id does **not** count while putting the same person's address in `setToAddresses` does (apexdev.txt L19971-19975) — a one-line change that can halve a notification job's consumption. When a transaction's recipient count is known up front, call `Messaging.reserveSingleEmailCapacity(n)` first: it fails fast with `System.HandledException: The daily limit for the org would be exceeded by this request.` instead of part-sending (apexrefguide.txt L225161-225184). And remember the per-transaction ceiling is separate: 10 `sendEmail` calls per transaction, each carrying at most 100 To, 25 Cc and 25 Bcc recipients (apexdev.txt L19575; apexrefguide.txt L225190).
