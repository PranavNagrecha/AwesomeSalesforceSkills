# Examples — Email-to-Case Configuration

## Example 1: On-Demand Email-to-Case Setup for a Single Support Mailbox

**Context:** A company uses `support@acme.com` as its customer-facing support address. Cases have been created manually; the admin now needs inbound emails to automatically create cases and have customer replies thread into the original case.

**Problem:** Without Email-to-Case configured, agents manually copy customer emails into cases. Customer replies create unrelated threads in the shared inbox instead of attaching to the existing case. No audit trail exists in Salesforce.

**Solution:**

```text
Setup → Email-to-Case → Edit
  [x] Enable Email-to-Case
  [x] Enable On-Demand Service
  Notify Case Owners on New Emails: [x]
  Save

Setup → Email-to-Case → Routing Addresses → New
  Routing Name: ACME Support
  Email Address: support@acme.com
  Case Origin: Email
  Case Priority: Normal
  Case Status: New
  Save

→ Copy Salesforce-generated address:
  case-[uniqueid]@[instance].salesforce.com

Mail server (e.g., Google Workspace or Exchange):
  Create forwarding rule:
  From: support@acme.com → Forward to: case-[uniqueid]@[instance].salesforce.com

Setup → Email-to-Case → Routing Addresses → ACME Support
  → Click "Send Verification Email"
  → Open verification email at the Salesforce-generated address → click Verify
```

**Why it works:** On-Demand uses Salesforce-hosted Apex Email Services to receive the forwarded email and create the case. The verification step confirms the forwarding route is active. Salesforce embeds a Lightning thread token in every outgoing case email so that customer replies route back to the originating case rather than creating new cases.

---

## Example 2: Multiple Routing Addresses for Channel-Based Case Classification

**Context:** An e-commerce company has three support inboxes: `support@store.com` (general), `billing@store.com` (billing), and `returns@store.com` (returns). Each should route to a different support queue with pre-populated Case Origin for reporting.

**Problem:** With a single routing address, all inbound emails create cases with the same defaults. Agents must manually re-classify cases after creation, and reporting by channel is unreliable.

**Solution:**

```text
Create three routing addresses:

Routing Address 1:
  Name: General Support
  Email: support@store.com
  Case Origin: Email - General
  Priority: Normal
  Status: New

Routing Address 2:
  Name: Billing
  Email: billing@store.com
  Case Origin: Email - Billing
  Priority: High
  Status: New

Routing Address 3:
  Name: Returns
  Email: returns@store.com
  Case Origin: Email - Returns
  Priority: Normal
  Status: New

Case Assignment Rule entries (evaluated in order):
  Entry 1: Case Origin = "Email - Billing"  → Queue: Billing Support
  Entry 2: Case Origin = "Email - Returns"  → Queue: Returns Team
  Entry 3: (catch-all, no criteria)         → Queue: General Support

Mail server: three separate forwarding rules, one per address.
```

**Why it works:** Each routing address stamps a distinct Case Origin on created cases. The assignment rule uses Case Origin to route to the correct queue. Pre-classification at creation eliminates post-creation manual triage and makes channel-based reporting reliable from day one.

---

## Anti-Pattern: Using the Routing Address as the Auto-Response From Address

**What practitioners do:** When configuring the auto-response rule, they set the "From" sender email to the same address as the Email-to-Case routing address (e.g., both are `support@acme.com`).

**What goes wrong:** Salesforce sends the auto-response to the customer. The customer's reply arrives back at `support@acme.com`, which forwards to the Salesforce routing address, which creates a new case, which triggers another auto-response, which the customer replies to again. This creates an email loop that rapidly generates hundreds of cases and outbound emails. In high-volume environments this can exhaust email send limits within minutes.

**Correct approach:** Set the auto-response rule "From" address to a no-reply address (e.g., `no-reply@acme.com`) that is not configured as an Email-to-Case routing address and that does not forward back to Salesforce. Add a clear instruction in the auto-response email body telling customers not to reply to the no-reply address and directing them to the correct support channel if they need to follow up.
