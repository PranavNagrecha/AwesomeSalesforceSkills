# Gotchas — Case Management Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Auto-Response Rules Do Not Fire Independently of Assignment Rules

**What happens:** The auto-response rule never sends an acknowledgment email to the customer, even though the rule is active and the template is valid.

**When it occurs:** The auto-response rule fires ONLY when the active case assignment rule also fires for that case. If the assignment rule is inactive, if no rule entry criteria match the incoming case, or if the case was created via an API or Data Loader integration that did not include the `Sforce-Auto-Assign: true` REST header or the SOAP `AssignmentRuleHeader` element, the assignment rule does not fire — and therefore the auto-response rule does not fire either.

**How to avoid:** Before debugging the auto-response rule itself, always verify that the case assignment rule is active, has at least one matching entry (or a catch-all), and that the creation method triggers assignment rule evaluation. Check Case history for "Rule Assignment" entries to confirm the assignment rule ran. If creating cases via API, confirm the integration is passing the correct header.

---

## Gotcha 2: Escalation Rule Reactivation Triggers Bulk Immediate Escalations

**What happens:** When a deactivated escalation rule is reactivated, the escalation engine immediately evaluates all open cases against the rule. Cases that have been open longer than the escalation threshold since the rule was deactivated will escalate at once — generating a surge of re-assignment actions, emails, and queue changes in a single engine pass.

**When it occurs:** Any time an escalation rule is deactivated for maintenance or troubleshooting and then reactivated. The longer the rule was inactive and the more open cases exist in the org, the larger the wave. In orgs with thousands of open cases and multi-hour SLA thresholds, hundreds of simultaneous escalations can occur.

**How to avoid:** Never reactivate an escalation rule in production without first testing in a sandbox with representative case volume. Before reactivation, consider temporarily closing or bulk-updating the cases that would immediately escalate. Communicate to the support team that a volume surge may follow reactivation.

---

## Gotcha 3: Email-to-Case Thread ID Misconfiguration Creates Duplicate Cases

**What happens:** Customer replies to a case email notification create new, separate cases instead of threading as Email Message records on the original case.

**When it occurs:** The Email-to-Case thread ID is a token embedded in outgoing case emails that Salesforce uses to match replies to the parent case. If the routing address is incorrectly configured, the mail server strips custom headers, the reply-to address is not set to the routing address, or a third-party email system modifies the message body before forwarding, the thread token is missing or invalid. Salesforce cannot match the reply and creates a new case.

**How to avoid:** Test thread handling end-to-end before go-live: create a case via email, reply from the Salesforce case (not manually), and confirm the customer-facing reply-to address includes the Salesforce routing address. Have the customer (or a test email account) reply and verify the reply appears as an Email Message on the original case. Enable the "Thread ID in Email Subject" option as a fallback if the mail server strips body tokens.

---

## Gotcha 4: The Web-to-Case Overflow Signal Exists, But It Stops After Five Emails

**What happens:** Web-to-Case enforces a 24-hour submission limit. Requests above it are not discarded — they land in a pending request queue that Web-to-Case and Web-to-Lead **share**, capped at 50,000 combined requests. Only when that queue is full are further requests rejected and not queued at all. The submitter sees the HTML form's success page regardless, and no case is created.

There **is** a native signal, and teams routinely build monitoring as though there weren't: when the pending limit is reached and requests start being rejected, Salesforce emails the administrator about the **first five rejected submissions**. That is the whole notification. A four-hour outage that drops 40,000 requests produces exactly five emails, all in the first few seconds — so the useful design question is not "how do we detect this at all" but "is the address receiving those five emails monitored, and do we have a second signal for the remaining 39,995?"

**When it occurs:** High-volume campaigns, product launches, or outage events that drive spike submission volume. Because the pending queue is shared, a Web-to-Lead spike from a marketing campaign can exhaust the queue and take Web-to-Case down with it — a coupling that is invisible from the Service Cloud side.

**How to avoid:** Route the administrator notification address to a monitored support mailbox or ticket queue, not an individual's inbox. Monitor the pending request count in Setup, and account for Web-to-Lead volume in the same budget. Salesforce Customer Support can raise the pending request limit. For sustained high volume, supplement with On-Demand Email-to-Case, or replace the built-in endpoint with an Experience Cloud form or a custom integration that creates cases through the **REST or SOAP API**. (SOSL is a search language and cannot create records of any kind — it is not an alternative intake path.)

---

## Gotcha 5: Escalation Rule Business Hours Omission Runs Clock 24/7

**What happens:** Cases escalate outside of business hours — on weekends, evenings, and holidays — because the escalation threshold is measured in calendar time, not business time.

**When it occurs:** When creating an escalation rule entry, the business hours field is optional and defaults to none. Without a business hours record attached, Salesforce measures escalation time in elapsed wall-clock hours from case creation or last modification. A case opened on Friday at 5 PM escalates after the threshold hours even if the support team does not work weekends.

**How to avoid:** Always create a business hours record in Setup → Business Hours before configuring escalation rules. Attach the correct business hours record to every escalation rule entry that should respect work schedules. Verify the attachment is saved — the field is easy to overlook in the rule entry form.

---

## Gotcha 6: Same Subject and Body in Email-to-Case Creates Infinite Loop

**What happens:** An infinite loop of case creation occurs: an auto-response email to a customer triggers the Email-to-Case routing address again, creating a new case, which sends another auto-response, which creates another case — indefinitely.

**When it occurs:** If the "from" address or "reply-to" address on an auto-response email is set to (or accidentally matches) the Email-to-Case routing address, Salesforce receives the outgoing auto-response as a new inbound email and creates a new case. This is most common when the routing address is set up as both a send-from and receive-at address, or when a mail server misconfiguration bounces outgoing auto-responses back to the routing address.

**How to avoid:** Set the auto-response "from" address to a non-routed email address (e.g., noreply@company.com). Never use the Email-to-Case routing address as the sender for auto-response emails. In Salesforce Setup, the Email-to-Case routing address should only be used for inbound routing. Test by inspecting the "from" and "reply-to" headers on the outgoing auto-response email before go-live.
