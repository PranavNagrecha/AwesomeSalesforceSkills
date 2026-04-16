# Gotchas — Slack Salesforce Integration Setup

## Gotcha 1: Three-Party Handshake Cannot Be Completed Solo

**What happens:** A Salesforce System Admin who also has Slack Workspace Admin access attempts to complete the connection unilaterally. The Slack initiation step completes, but the Salesforce approval step requires a System Admin login in a different context, and the Slack activation step requires a Workspace Owner (not just admin). The process stalls.

**When it occurs:** Single-admin setups or orgs where Slack admin and Salesforce admin are the same person.

**How to avoid:** Plan the handshake as a coordinated event. Identify and schedule all three role holders before starting: Slack Workspace Owner/Admin (step 1 and 3), and Salesforce System Admin (step 2). A 15-minute call with all parties present resolves the setup.

---

## Gotcha 2: Record Previews Bypass Individual User Field-Level Security

**What happens:** A user pastes a Salesforce Opportunity URL in a Slack channel. All channel members see a rich preview card showing deal value, stage, and custom fields — including fields those channel members cannot see in Salesforce due to field-level security restrictions.

**When it occurs:** Whenever a Salesforce record URL is shared in any Slack channel where the Salesforce for Slack app is installed.

**How to avoid:** Review page layouts assigned to the Platform Integration User. Remove sensitive fields from those layouts. Implement channel-level governance policies for what types of Salesforce records can be shared in which Slack channels.

---

## Gotcha 3: Government Cloud Orgs Cannot Connect

**What happens:** Attempts to connect a Salesforce Government Cloud org to Slack fail at the approval step with no available workaround. The restriction is at the platform level.

**When it occurs:** Any public sector or regulated org using Salesforce Government Cloud.

**How to avoid:** Verify org type before promising Salesforce for Slack features to Government Cloud customers. Propose alternative integration patterns: custom Slack app via Slack SDK, MuleSoft-mediated integration, or email-based notifications.

---

## Gotcha 4: 20-Org Workspace Limit

**What happens:** An enterprise with 20+ Salesforce sandboxes, development orgs, and production instances hits the limit of 20 connected Salesforce orgs per Slack workspace. Additional connection attempts fail.

**When it occurs:** Large enterprises with many orgs that attempt to connect all environments (production + multiple sandboxes) to a single Slack workspace.

**How to avoid:** Plan org connection priorities upfront. Typically, connect production and major sandbox (UAT) orgs only. Reserve connections for high-priority environments. If needed, use multiple Slack workspaces to distribute connections.

---

## Gotcha 5: Individual User Connection Is Required After Org Connection

**What happens:** After the admin completes the org-level connection, users find they cannot search Salesforce records, see personalized data, or use Salesforce shortcuts in Slack. They report the integration is "not working."

**When it occurs:** After the three-party org connection handshake completes — the org connection grants workspace-level access but each user must separately authorize their personal Salesforce account.

**How to avoid:** After org connection, send a user onboarding communication instructing every user to open the Salesforce app in Slack and connect their personal Salesforce account. Include this step in user training materials.
