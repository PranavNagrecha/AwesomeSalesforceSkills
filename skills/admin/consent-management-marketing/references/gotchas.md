# Gotchas — Consent Management Marketing

Non-obvious Salesforce Marketing Cloud behaviors that cause real production problems in this domain.

## Gotcha 1: Global Opt-Out on All Subscribers Silently Wins Over Publication List Opt-In

**What happens:** A subscriber who is globally opted out at the All Subscribers level (`HasOptedOutOfEmail = true`) continues to show as "Active" on individual publication lists. When a send targeted at that publication list is executed, the subscriber appears in the audience query, but MC silently suppresses delivery. There is no error; the subscriber just does not receive the email and the send log shows them as suppressed.

**When it occurs:** This is encountered most frequently when ops teams try to "fix" an opt-out complaint by re-importing the subscriber as Active into a publication list without clearing the global opt-out flag. The re-import succeeds at the list level but has no effect on delivery.

**How to avoid:** Always check the All Subscribers status before troubleshooting missing delivery. If `HasOptedOutOfEmail = true` at the All Subscribers level, the only valid resolution is to obtain explicit re-consent from the subscriber and then update the All Subscribers record — not just the publication list record. Never manually flip the global opt-out flag without documented re-consent.

---

## Gotcha 2: Privacy Center Erasure May Retain the Suppression Record

**What happens:** After processing a GDPR right-to-erasure request through Privacy Center, the subscriber's personal data is removed from Data Extensions and engagement records per the configured erasure scope. However, the All Subscribers record itself (including the email address and opt-out flag) may be retained as a suppression record, depending on Privacy Center configuration. This is intentional: MC keeps the address on a suppression list to prevent re-addition.

The gotcha is the inverse: if a team configures Privacy Center to perform a full delete including the All Subscribers record, the suppression signal is gone. If the email address is later re-synced from a CRM that was not updated with the opt-out, the subscriber will be re-added to All Subscribers as Active and commercial email will resume — potentially to someone who has legally invoked their right to erasure.

**When it occurs:** After GDPR erasure requests, especially in orgs where MC Connect is not configured to propagate erasure to the CRM. Also occurs after bulk data re-imports that do not check against a locally maintained suppression list.

**How to avoid:** Configure Privacy Center to retain the suppression record (address + opt-out status only) while erasing all other personal data. Maintain a parallel erasure log in the CRM so re-syncs do not re-add erased subscribers. Document the Privacy Center erasure scope in the data protection impact assessment.

---

## Gotcha 3: Send Classification Not Inherited by Journey Builder and Triggered Send Activities

**What happens:** The account-level default Send Classification is applied to User-Initiated Sends automatically. However, Journey Builder Email Activities and Triggered Send Definitions each have their own Send Classification field, which must be explicitly set. If a Journey or Triggered Send is created without setting the Send Classification, MC may apply a different classification (or no physical address) to that send, creating CAN-SPAM non-compliance for that specific touchpoint.

**When it occurs:** Most commonly when Journey Builder canvases are built by marketers who are not aware of the Send Classification requirement, or when a Triggered Send Definition is created via the API without including the `senderProfile` and `deliveryProfile` parameters.

**How to avoid:** Add a review step to Journey and Triggered Send deployment checklists: verify that the Send Classification on each email activity matches the approved commercial classification with the correct Delivery Profile. In API-created Triggered Sends, always pass `senderProfile` and `deliveryProfile` explicitly.

---

## Gotcha 4: Subscription Center Shows All Lists the Subscriber Is On, Including Internal/Operational Lists

**What happens:** The default MC Subscription Center displays every publication list that the subscriber currently has an `Active` status on. If internal operational lists (e.g., "Internal Test List," "QA Send List," "Data Migration Seed") were created as publication lists rather than suppression lists or private lists, subscribers who ended up on those lists (from testing, imports, or mistakes) will see those list names in their Subscription Center and may opt out of them, interfering with operational processes.

**When it occurs:** Orgs that use publication lists for internal send testing, seed lists, or QA without using the `Private` list attribute. Also common when data migration imports use publication lists as a staging mechanism.

**How to avoid:** Use the `Private` attribute on any publication list that should not be surfaced to subscribers. Reserve public publication lists for subscriber-facing content categories only. Audit publication list visibility before launching Subscription Center to subscribers.

---

## Gotcha 5: One-Click Unsubscribe List-Unsubscribe Header Is Separate From the Footer Link

**What happens:** Google and Yahoo's 2024 bulk sender requirements include two distinct unsubscribe mechanisms: (1) a `List-Unsubscribe` email header that inbox providers use to display a native "Unsubscribe" button in the inbox UI, and (2) a visible one-click unsubscribe link in the email body. Marketing Cloud's native `%%subscription_center_url%%` satisfies the body link requirement. However, the `List-Unsubscribe` header must be configured separately in the Delivery Profile or via a custom header in the Send Classification.

If only the footer link is configured and the `List-Unsubscribe` header is absent, bulk senders (>5,000 emails/day to Gmail/Yahoo) may see deliverability penalties and suppressed placement from those providers.

**When it occurs:** Orgs that set up MC before the 2024 requirements were published, or orgs that use custom Delivery Profiles created before the header was added as a configurable option.

**How to avoid:** In the Delivery Profile, verify that `List-Unsubscribe` header generation is enabled. Test by viewing raw message headers on a test send to a Gmail address. The header should read: `List-Unsubscribe: <https://YOUR_MC_UNSUB_URL>, <mailto:unsub@yourdomain.com>` and include `List-Unsubscribe-Post: List-Unsubscribe=One-Click`.
