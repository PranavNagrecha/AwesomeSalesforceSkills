# Gotchas — Email-to-Case Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Routing Address Verification is a Hard Blocker

**What happens:** After creating a routing address and configuring the mail server forwarding rule, inbound emails arrive at the Salesforce-generated address but no cases are created. The mail server logs show successful delivery; Salesforce shows nothing.

**When it occurs:** Any time a routing address has not been verified. Salesforce will not process inbound email for an unverified routing address even if delivery is confirmed at the network level. The verification requirement is enforced silently — there is no error in the UI or in the email headers to indicate the cause.

**How to avoid:** After creating a routing address, always click "Send Verification Email" immediately. Open the Salesforce-generated inbox (which requires the forwarding rule to be active first), click the verification link, and confirm the status shows "Verified" in the routing address record before testing case creation. Document the verification date in the org runbook.

---

## Gotcha 2: The On-Demand Size Limit Is a 35 MB Total, and MIME Encoding Eats a Third of It

**What happens:** An inbound email is silently dropped and no case is created. The support team was told the limit is 25 MB, the customer's attachment was 24 MB, and everyone concludes Email-to-Case is broken. In fact Salesforce enforces the limit on the *total* redirected message — body + attachments + HTML — at 35 MB, and MIME transfer encoding inflates the payload by up to 33% between the sender's outbox and the routing address. A 27 MB set of attachments can arrive as 36 MB and be rejected. There is no in-Salesforce error record for the rejection.

**When it occurs:** On-Demand mode, at the routing address, before any Apex or assignment logic runs. Standard Email-to-Case receives at the company's own mail server, so its first size gate is whatever that server is configured to allow.

**How to avoid:** Publish the honest figure — 35 MB total message, roughly 25 MB of usable attachment payload — rather than a per-attachment cap, because Salesforce does not document one. If large attachments are a genuine business requirement, put a Salesforce Files or portal upload link in the auto-response template rather than switching modes. Beware of stale numbers: 25 MB was the org-wide total before Winter '21 and 10 MB before Summer '14, so any source quoting those as current is out of date.

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
