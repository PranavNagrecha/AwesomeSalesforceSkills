# Gotchas — Email-to-Case Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Routing Address Verification is a Hard Blocker

**What happens:** After creating a routing address and configuring the mail server forwarding rule, inbound emails arrive at the Salesforce-generated address but no cases are created. The mail server logs show successful delivery; Salesforce shows nothing.

**When it occurs:** Any time a routing address has not been verified. Salesforce will not process inbound email for an unverified routing address even if delivery is confirmed at the network level. The verification requirement is enforced silently — there is no error in the UI or in the email headers to indicate the cause.

**How to avoid:** After creating a routing address, always click "Send Verification Email" immediately. Open the Salesforce-generated inbox (which requires the forwarding rule to be active first), click the verification link, and confirm the status shows "Verified" in the routing address record before testing case creation. Document the verification date in the org runbook.

---

## Gotcha 2: On-Demand 10 MB Per-Attachment Limit Silently Rejects Emails

**What happens:** Inbound emails with individual attachments larger than 10 MB are rejected by On-Demand Email-to-Case. The sender typically receives a bounce or no case is created. There is no in-Salesforce error record. The 25 MB total email size limit is documented prominently, but the per-attachment cap specific to On-Demand mode is not prominently surfaced in the standard Email-to-Case setup UI.

**When it occurs:** On-Demand mode only. Standard Email-to-Case does not enforce a per-attachment cap (only the total 25 MB limit). Orgs that previously used Standard and migrate to On-Demand are especially vulnerable — attachments that worked under Standard will silently fail under On-Demand.

**How to avoid:** Communicate the 10 MB per-attachment limit to support teams and customers during rollout. If large attachment support is a business requirement, evaluate whether Standard Email-to-Case is appropriate despite its operational overhead, or implement an alternative workflow (e.g., a Salesforce Files link in the auto-response directing customers to upload via a portal).

---

## Gotcha 3: Auto-Response Email Loops When From Address Matches Routing Address

**What happens:** After configuring an auto-response rule, cases begin appearing in the org at an abnormal rate. Investigation reveals that each case creates an auto-response email, the customer's inbox receives it and bounces or forwards it, and the routing address receives the bounce/forward and creates another case.

**When it occurs:** When the auto-response rule entry's sender ("From") email address is the same as or forwards to the Email-to-Case routing address. The most common cause: the admin copies the support address (`support@company.com`) into the auto-response rule "From" field, and the company mail server has a blanket forwarding rule for all mail arriving at `support@company.com`.

**How to avoid:** Always use a dedicated no-reply address (e.g., `no-reply@company.com`) as the From address for auto-response rule entries. Confirm this address does not forward to any Email-to-Case routing address. Test auto-response by sending a single inbound email and monitoring the Case count for 5 minutes to confirm it does not grow.

---

## Gotcha 4: Security Gateway Token Stripping Breaks Threading Silently

**What happens:** Threading works in sandbox or direct SMTP tests but fails in production. Customer replies consistently create new cases instead of adding Email Messages to the original case. The Lightning thread token (the `[ref:...:ref]` suffix in the subject and the reference string in the body) is present in emails sent from Salesforce but absent in the replies received.

**When it occurs:** Corporate email security gateways (Proofpoint, Mimecast, Barracuda, Microsoft Defender for Office 365) perform link rewriting and content modification on inbound and outbound email. Some configurations strip or rewrite the thread token strings as part of safe-link processing or content normalization. Because sandbox tests often bypass the production gateway, the issue only surfaces in production.

**How to avoid:** Test the full round-trip through the production mail gateway before go-live. Send an email from Salesforce to an external inbox that goes through the production gateway. Reply to that email and confirm the reply threads correctly. If tokens are being stripped, work with the IT team to add Salesforce thread token patterns to the gateway's allowlist or exclusion rules. The thread token pattern (`ref:` followed by alphanumeric characters and `:ref`) is the signature to preserve.

---

## Gotcha 5: Standard Email-to-Case Agent API Call Consumption

**What happens:** In a high-volume environment using Standard Email-to-Case, the org's daily API call limit is exhausted before end of day. Other integrations and automations begin failing. Investigation reveals the Email-to-Case agent is responsible for a large share of the API consumption — each inbound email consumes one or more API calls.

**When it occurs:** Standard Email-to-Case only. The local agent uses the SOAP or REST API to create cases in Salesforce. Orgs receiving hundreds or thousands of emails per day may not account for this consumption when estimating daily API usage. On-Demand Email-to-Case does not use API calls — it uses Apex Email Services, which is outside the API call governor.

**How to avoid:** If the org expects high email volume, use On-Demand Email-to-Case. If Standard is required, estimate daily email volume and add it to the org's API call budget. Monitor API usage in Setup → Company Information → API Requests, Last 24 Hours.
