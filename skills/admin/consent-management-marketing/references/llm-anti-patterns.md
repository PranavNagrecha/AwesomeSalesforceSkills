# LLM Anti-Patterns — Consent Management Marketing

Common mistakes AI coding assistants make when generating or advising on Marketing Cloud consent management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating a Confirmation Screen Before Processing Unsubscribe

**What the LLM generates:** A CloudPages Preference Center that shows a "Are you sure you want to unsubscribe?" page and requires the subscriber to click a second button before the opt-out is actually processed.

**Why it happens:** Double-confirmation UX patterns are common in web application design and appear frequently in training data as "best practice." The LLM applies general web UX convention without knowing the 2024 Google/Yahoo one-click unsubscribe requirement.

**Correct pattern:**

```ampscript
%%[
/* Process opt-out immediately on page load — before rendering HTML */
SET @email = AttributeValue("emailaddr")
UpsertData("All Subscribers", 1, "EmailAddress", @email, "HasOptedOutOfEmail", "true")
/* Then render the confirmation of the already-completed action */
]%%
<p>You have been unsubscribed.</p>
```

**Detection hint:** If the generated CloudPage AMPscript processes the opt-out inside a form `POST` handler (requiring a second button click), or if there is an `IF @confirmed == "true"` gate before the unsubscribe call, the pattern is non-compliant with one-click requirements.

---

## Anti-Pattern 2: Advising to Use Publication List Opt-In to Re-Enable a Globally Opted-Out Subscriber

**What the LLM generates:** Guidance such as "to re-activate the subscriber, update their status to Active on the relevant publication list" — given to resolve a complaint that a subscriber is not receiving emails.

**Why it happens:** The LLM treats publication list status as the governing opt-in/opt-out control, analogous to a simple boolean field. It does not model the hierarchical relationship between All Subscribers global opt-out and publication list status.

**Correct pattern:**

```
To re-enable a subscriber who has globally opted out:
1. Obtain documented re-consent from the subscriber.
2. Update HasOptedOutOfEmail = false on the All Subscribers record.
3. Only then re-activate on the relevant publication lists.
Never update publication list status without first clearing the global opt-out.
```

**Detection hint:** If advice says "update publication list status to Active" as the complete solution for re-enabling delivery to a subscriber without mentioning the All Subscribers global opt-out check, the advice is incomplete and potentially creates compliance violations.

---

## Anti-Pattern 3: Assuming MC Unsubscribes Automatically Sync to Salesforce CRM

**What the LLM generates:** Statements like "when a subscriber opts out in Marketing Cloud, their Salesforce Contact record is automatically updated" or code that only checks `HasOptedOutOfEmail` in MC without verifying CRM sync.

**Why it happens:** LLMs conflate the Marketing Cloud and Salesforce CRM data models as a single unified system. The integration (MC Connect) is optional and must be explicitly configured. Without it, opt-out state is siloed.

**Correct pattern:**

```
MC unsubscribes are stored in All Subscribers (MC only).
To sync to Salesforce CRM:
- MC Connect must be installed and configured
- Synchronized Data Sources must include opt-out writeback
- Verify by checking Contact.HasOptedOutOfEmail AFTER an MC opt-out event

Without this configuration, CRM-based sends (Sales Engagement, Pardot, manual email)
will continue to reach opted-out subscribers.
```

**Detection hint:** If consent management advice describes MC opt-out as automatically reflected in Salesforce Contact or Lead records without mentioning MC Connect configuration, the advice is incomplete. Look for absence of the terms "MC Connect," "Synchronized Data Sources," or "writeback."

---

## Anti-Pattern 4: Storing Full Consent Records in a DE That Will Be Erased

**What the LLM generates:** A consent-tracking Data Extension design where all consent fields (email address, consent timestamp, source, lawful basis) are stored with the subscriber's email address as the primary key — and then erased together when a GDPR right-to-erasure request is processed through Privacy Center.

**Why it happens:** The LLM correctly understands that consent tracking requires a DE, but does not model the lifecycle tension between consent record retention (required to defend against future GDPR claims) and data erasure (required to comply with the right to erasure). It generates a single-table design that conflates personal data with consent evidence.

**Correct pattern:**

```
Split the consent model:
- Consent_Event_DE: stores a hashed subscriber identifier (not raw email),
  event timestamp, lawful basis, consent version, source.
  This table survives erasure and can be used to prove consent was obtained.

- Subscriber_Profile_DE: stores email address and personal data.
  This table is targeted by Privacy Center erasure.

On erasure, the email address is removed from Subscriber_Profile_DE.
The Consent_Event_DE retains the hashed record without PII.
```

**Detection hint:** If the generated consent DE uses the raw email address as the only key in a single table with no separation between PII and consent event metadata, the design is vulnerable to losing all consent evidence on erasure.

---

## Anti-Pattern 5: Omitting Physical Mailing Address From Custom Email Templates

**What the LLM generates:** A custom HTML email template or footer snippet that includes only the unsubscribe link (`%%subscription_center_url%%`) without the physical mailing address block required by CAN-SPAM.

**Why it happens:** The LLM focuses on the unsubscribe mechanism (the most commonly discussed CAN-SPAM requirement) and omits the physical address requirement. Training data includes many email templates that rely on a shared master template containing the address, so the LLM may not flag its absence in component templates.

**Correct pattern:**

```html
<p style="font-size:11px; color:#666;">
  <a href="%%subscription_center_url%%">Manage preferences</a> |
  <a href="%%unsub_center_url%%">Unsubscribe</a><br>
  %%[/* Physical address from Delivery Profile or static text */]%%
  Your Company Name &bull; 123 Main St, City, ST 12345
</p>
```

**Detection hint:** If a generated email template footer includes only the unsubscribe link without a physical mailing address (or a reference to a Delivery Profile that provides it), the template is CAN-SPAM non-compliant. Check for absence of street address, city, state, and ZIP code in the footer.

---

## Anti-Pattern 6: Recommending Double Opt-In as a CAN-SPAM Requirement

**What the LLM generates:** Guidance stating that double opt-in (confirmed opt-in) is required by CAN-SPAM law for email marketing compliance.

**Why it happens:** Double opt-in is a best practice frequently discussed alongside CAN-SPAM in the same context. LLMs conflate the two, treating a recommended practice as a legal requirement.

**Correct pattern:**

```
CAN-SPAM does NOT require double opt-in. CAN-SPAM requires:
- Accurate header information (From, Reply-To)
- No deceptive subject lines
- Identification as an advertisement (for commercial email)
- Physical mailing address
- Clear opt-out mechanism
- Opt-out honored within 10 business days

Double opt-in IS recommended for:
- GDPR compliance (auditable consent record)
- List hygiene (reduces invalid addresses)
- Deliverability (higher engagement rates from confirmed subscribers)
```

**Detection hint:** If generated guidance says double opt-in is "legally required" for US email marketing or "required by CAN-SPAM," the claim is incorrect. CAN-SPAM does not mandate confirmed opt-in; it mandates opt-out handling.
