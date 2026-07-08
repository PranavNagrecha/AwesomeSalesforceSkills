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

## Gotcha 4: Web-to-Case 50,000 Pending Request Limit Is a Hard Drop

**What happens:** New Web-to-Case submissions are silently dropped once the pending request queue reaches 50,000 entries. The submitter sees a success message from the HTML form but no case is ever created. No error is logged in Salesforce and no alert is sent to admins by default.

**When it occurs:** High-volume campaigns, product launches, or outage events that drive spike submission volume can fill the queue quickly. The queue is drained as cases are processed, but a sustained spike can keep it full.

**How to avoid:** Monitor the pending Web-to-Case count in Setup → Web-to-Case regularly. Set up an operational alert (via external monitoring or a scheduled Flow/Apex job that checks the count via SOAP API) to notify admins when the count approaches the limit. For high-volume scenarios, consider On-Demand Email-to-Case as a supplement, or use Experience Cloud or a custom API-based form that creates cases via SOSL/REST rather than the built-in Web-to-Case endpoint.

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

---

## Gotcha 7: Activating a Rule Silently Deactivates the Rule Already Holding That Slot

**What happens:** An admin activates a newly built case assignment rule. Nothing warns them. The rule that had been routing production cases for two years is now inactive, and every case created from that moment forward is evaluated against the new rule's entries only. If the new rule has no catch-all entry, cases fall to the default case owner. Auto-responses tied to the old routing stop firing for anything the new rule does not match.

**When it occurs:** Every time. Assignment, auto-response, and escalation rules each expose exactly one active slot for cases. Salesforce states it directly for auto-response rules — "you can activate only one rule for leads and one rule for cases at a time" — and assignment and escalation rules behave the same way. Activating one deactivates the incumbent.

The three common triggers:

- An admin builds a "test" rule in production to try new criteria and activates it to see it work.
- A business unit asks for its own assignment rule for its own region or channel, and someone builds and activates a second rule believing both will coexist.
- A deployment activates a rule as part of a metadata push, displacing an incumbent nobody on the deploying team knew about.

**How to avoid:** Treat rule activation as a change-management event, not a Setup click.

- Inventory the active rule in each of the three slots before building anything. Record its name.
- Name rules with a version marker (`Case Assignment — 2026 Q3`) so the incumbent is identifiable and rollback is a single activation of the prior rule.
- Never model per-region or per-channel behavior as separate active rules. It is impossible. Model it as ordered **entries inside the one active rule**, specific-to-catch-all.
- Activate the replacement directly rather than deactivating the incumbent first. Deactivating first opens a window in which no rule is active, cases fall to the default case owner, and no auto-response sends.
- Rehearse the swap in a sandbox with representative case creation from every inbound channel, and confirm Case History shows a "Rule Assignment" entry for each.
