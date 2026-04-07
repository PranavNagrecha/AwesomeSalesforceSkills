# Examples — Consent Management Marketing

## Example 1: Configuring CAN-SPAM-Compliant Send Classification

**Context:** A new Marketing Cloud account has been provisioned. The team is ready to send commercial email but wants to confirm the CAN-SPAM requirements are enforced before go-live.

**Problem:** If a Send Classification is not linked to a Delivery Profile containing the physical mailing address, Marketing Cloud will either block the send or the email will be missing the required address. Teams that skip this step often discover the gap only after a compliance audit or after their first suppressed send.

**Solution:**

1. In Marketing Cloud, navigate to **Admin > Send Management > Send Classifications**.
2. Create or edit the Default Commercial Send Classification.
3. Link it to a **Delivery Profile** that includes:
   - Physical mailing address (required for CAN-SPAM)
   - Reply mail management settings
4. Set this Send Classification as the default for both **User-Initiated Sends** and **Triggered Sends**.
5. In every email template footer, include the personalization string `%%subscription_center_url%%` for the unsubscribe link, and `%%member_addr%%` + `%%member_city%%` etc. (or the static address from the Delivery Profile) for the physical address block.

Example footer snippet in an email template:
```
%%[
  /* Subscription Center and physical address are required for CAN-SPAM */
]%%
<p style="font-size:11px;">
  You are receiving this email because you subscribed to our list.<br>
  <a href="%%subscription_center_url%%">Manage your email preferences</a> |
  <a href="%%unsub_center_url%%">Unsubscribe</a><br>
  Company Name, 123 Main Street, City, State, ZIP
</p>
```

**Why it works:** MC's Send Classification system acts as the enforcement layer for CAN-SPAM. Attaching a Delivery Profile to the Send Classification ensures the physical address appears on every send routed through that classification, without requiring individual template authors to remember to include it.

---

## Example 2: Building a CloudPages Preference Center with Immediate Opt-Out

**Context:** A brand requires a fully branded email preference management page. The existing MC Subscription Center does not match the brand style guide. Additionally, the 2024 Google/Yahoo bulk sender requirements mandate one-click unsubscribe — no confirmation screens.

**Problem:** A naive Preference Center implementation might display a "Are you sure you want to unsubscribe?" page before processing the opt-out. This violates the one-click unsubscribe requirement and can result in deliverability penalties from major inbox providers.

**Solution:**

Build a CloudPage with AMPscript that processes the opt-out on the initial GET request, then shows a confirmation of the action already taken:

```ampscript
%%[
  /* Retrieve subscriber context */
  SET @emailAddr = AttributeValue("emailaddr")
  SET @subKey   = AttributeValue("_subscriberkey")

  /* Determine action from query string */
  SET @action = RequestParameter("action")

  IF @action == "unsub" THEN
    /* Process global unsubscribe immediately — no confirmation step */
    UpsertData(
      "All Subscribers",
      1, "EmailAddress", @emailAddr,
      "HasOptedOutOfEmail", "true"
    )
    /* Log unsubscribe event to consent DE */
    InsertData(
      "Consent_Tracking_DE",
      "EmailAddress", @emailAddr,
      "EventType", "GlobalUnsubscribe",
      "EventTimestamp", NOW(),
      "Source", "PreferenceCenter"
    )
    SET @message = "You have been unsubscribed."
  ELSEIF @action == "update" THEN
    /* Handle publication list preference updates */
    /* ... list-specific AMPscript logic ... */
    SET @message = "Your preferences have been updated."
  ELSE
    SET @message = ""
  ENDIF
]%%

<p>%%=v(@message)=%%</p>
```

Link to this page from the email footer using a URL that includes `action=unsub` and the encoded subscriber key:

```
<a href="https://YOUR_CLOUDPAGE_URL?action=unsub&subkey=%%_subscriberkey%%">Unsubscribe</a>
```

**Why it works:** The opt-out is processed the moment the link is clicked and the page loads, before any HTML is rendered to the subscriber. This satisfies one-click unsubscribe requirements. The consent event is written to a tracking DE for auditing.

---

## Example 3: Double Opt-In Flow for GDPR-Compliant Acquisition

**Context:** A company acquires new marketing subscribers via a web form for EU audiences. GDPR requires documented, timestamped consent before sending commercial email.

**Problem:** Adding form submitters directly to a send list without confirmation creates GDPR exposure. If challenged, there is no auditable proof that the subscriber actively confirmed their consent.

**Solution:**

**Step 1 — Capture pending consent on form submit:**
```ampscript
%%[
  SET @email     = RequestParameter("email")
  SET @token     = GUID()  /* unique confirmation token */
  SET @timestamp = NOW()

  /* Write to pending-confirmation DE */
  InsertData(
    "Pending_Opt_In_DE",
    "EmailAddress", @email,
    "ConfirmationToken", @token,
    "CapturedTimestamp", @timestamp,
    "Source", "WebForm_EU"
  )

  /* Trigger confirmation email send via triggered send */
  /* Pass token as attribute for use in confirmation link */
]%%
```

**Step 2 — Confirmation email contains a link to a CloudPage:**
```
Please confirm your subscription:
<a href="https://YOUR_CLOUDPAGE_URL?token=%%[AttributeValue("token")]%%">Confirm my subscription</a>
```

**Step 3 — Confirmation CloudPage processes the opt-in:**
```ampscript
%%[
  SET @token = RequestParameter("token")
  SET @row   = LookupRows("Pending_Opt_In_DE", "ConfirmationToken", @token)

  IF RowCount(@row) > 0 THEN
    SET @email     = Field(Row(@row, 1), "EmailAddress")
    SET @captured  = Field(Row(@row, 1), "CapturedTimestamp")

    /* Activate on target publication list */
    UpsertData("Target_Publication_List_DE",
      1, "EmailAddress", @email,
      "Status", "Active"
    )

    /* Write confirmed consent record */
    UpsertData("Consent_Tracking_DE",
      1, "EmailAddress", @email,
      "ConsentTimestamp", @captured,
      "ConfirmedTimestamp", NOW(),
      "CaptureSource", "WebForm_EU",
      "LawfulBasis", "Consent",
      "IsConfirmed", "true"
    )

    /* Remove from pending DE */
    DeleteDE("Pending_Opt_In_DE", 1, "ConfirmationToken", @token)
  ENDIF
]%%
```

**Why it works:** The double opt-in pattern creates two timestamped records: the initial capture event and the confirmation event. If a GDPR audit or erasure request is received, the consent record shows when, how, and from where consent was obtained. The subscriber is never sent a commercial email until the confirmation step is completed.

---

## Anti-Pattern: Assuming MC Unsubscribes Sync to Salesforce CRM Automatically

**What practitioners do:** A subscriber opts out via the MC Subscription Center. The practitioner checks the subscriber's status in MC All Subscribers and sees `HasOptedOutOfEmail = true`. They assume this has also updated the Salesforce Contact record and the issue is resolved.

**What goes wrong:** Without MC Connect (Marketing Cloud Connect) configured with opt-out sync enabled, the Salesforce Contact `HasOptedOutOfEmail` field remains `false`. Any email sent from Sales Cloud, Salesforce Inbox, or Pardot to that contact will still be delivered, violating the subscriber's opt-out request. In a CAN-SPAM or GDPR context, this is a regulatory violation.

**Correct approach:** After an MC opt-out occurs, verify whether MC Connect is installed and whether the `Synchronized Data Sources` configuration includes opt-out writeback. If not, build a scheduled job or automation that reads MC All Subscribers opt-outs and writes them back to the CRM using the Salesforce API or a scheduled data sync. Document the sync lag and ensure the SLA is within the 10-business-day CAN-SPAM window.
