# Examples — Slack Salesforce Integration Setup

## Example 1: Three-Party Handshake for First-Time Org Connection

**Context:** A company wants to connect their Salesforce Production org to their Slack workspace to enable record sharing and Salesforce search within Slack.

**Problem:** The IT team tried to complete the entire setup with one admin who had both Slack Workspace Admin and Salesforce System Admin roles. The setup stalled because the Salesforce approval step was not visible after the Slack admin initiated, leading to repeated failed attempts.

**Solution:**

Complete the handshake in three distinct phases with the correct role at each step:

1. **Slack Workspace Admin** logs into Slack → Apps → App Directory → search "Salesforce for Slack" → Install to workspace.
2. **Salesforce System Admin** logs into Salesforce → Setup → Platform Tools → Apps → Salesforce for Slack → Manage Slack Connection → Approve the pending connection.
3. **Slack Workspace Admin** (or Workspace Owner) returns to Slack → App Home tab of Salesforce for Slack app → Complete the connection activation.
4. Each individual user then connects their personal Salesforce account from the Salesforce app in Slack.

**Why it works:** The platform enforces role separation across these steps. Step 2 requires Salesforce System Admin — a different role from the Slack admin who initiated in step 1. Coordinating all three parties in a 15-minute call prevents the multi-day back-and-forth that common ad-hoc setups encounter.

---

## Example 2: Governing Record Preview Data Exposure

**Context:** A financial services firm connected Salesforce to Slack for their sales team. A compliance audit discovered that deal terms and compensation data (stored in custom Opportunity fields) were visible in Slack channel previews to all channel members, including junior staff who lack field-level security access to those fields in Salesforce.

**Problem:** Record previews render based on the Salesforce page layout visible to the Platform Integration User, not the individual Slack user's Salesforce field-level security settings.

**Solution:**

1. Identify all custom Opportunity fields containing sensitive data (Compensation, Legal Terms, Discount Approval).
2. Remove these fields from the Opportunity page layout assigned to the Platform Integration User used by the Salesforce for Slack app.
3. Create a restricted page layout with only non-sensitive fields for Slack preview purposes.
4. Assign this restricted layout to the Platform Integration User's profile.
5. Document a channel governance policy: Opportunity records with deal value > $X should only be shared in designated private Slack channels with restricted membership.

**Why it works:** The preview card renders the page layout visible to the Platform Integration User. Restricting the layout for that user limits what appears in previews regardless of which Slack user shared the URL.

---

## Anti-Pattern: Attempting Government Cloud Connection

**What practitioners do:** A client with a Salesforce Government Cloud org requests Salesforce for Slack setup.

**What goes wrong:** Government Cloud orgs cannot be connected to Slack workspaces — this is an absolute platform restriction. Attempts to initiate the connection fail at the Salesforce approval step with no available workaround.

**Correct approach:** Inform the client of the hard restriction. Propose alternative integration patterns: custom Slack app built using Slack SDK, MuleSoft-based integration, or native Salesforce notifications via email. There is no configuration workaround for Government Cloud Slack connection.
