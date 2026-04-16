# Gotchas — Flow for Slack

## Gotcha 1: Actions Not Visible in Flow Builder Without Managed Package

**What happens:** A Flow builder searches for "Send Slack Message" or "Create Slack Channel" in Flow Builder's action search and finds nothing. There is no warning or error — the actions are simply absent.

**When it occurs:** When the Salesforce for Slack managed package has not been installed in the org, or when the package was uninstalled.

**How to avoid:** Before troubleshooting any Slack action visibility issue in Flow Builder, first verify the Salesforce for Slack managed package is installed: Setup > Installed Packages → look for "Salesforce for Slack." If not present, install from AppExchange.

---

## Gotcha 2: Permission Set Missing Causes Silent Runtime Fault

**What happens:** A Flow with a Send Slack Message action appears to succeed in Flow Builder testing but faults at runtime when triggered by a record change. The fault path fires with a cryptic error.

**When it occurs:** When the running user (or the process user for automated flows) lacks the Sales Cloud for Slack or Slack Service User permission set.

**How to avoid:** Assign the required permission set to all users who will trigger flows containing Slack actions. For scheduled or platform event-triggered flows, assign the permission set to the auto-process user or designated service user running the flow.

---

## Gotcha 3: Revoked OAuth Token Causes Actions to Disappear or Fail

**What happens:** After a Slack workspace admin revokes the Salesforce for Slack app's OAuth access, Slack actions disappear from Flow Builder and fail at runtime with a connection error. This can happen without the Salesforce admin being notified.

**When it occurs:** When a Slack workspace admin revokes OAuth access for the Salesforce for Slack app, or when the workspace OAuth token expires.

**How to avoid:** Monitor the connection status in Salesforce Setup > Slack > Manage Slack Connection. Set up monitoring alerts for flow fault emails that include Slack action errors. Re-establish the OAuth connection using the three-party handshake when this occurs.

---

## Gotcha 4: Channel Names Must Follow Slack Naming Rules

**What happens:** A Create Channel action fails at runtime with no clear error when the channel name contains spaces, uppercase letters, or special characters other than hyphens.

**When it occurs:** When channel names are derived from Salesforce record names (e.g., "Enterprise Deal: ACME Corp Q3") without transformation.

**How to avoid:** Always apply a formula transformation to channel names: LOWER(SUBSTITUTE(LEFT(recordName, 60), ' ', '-')). This produces a Slack-compatible name. Remove any special characters (periods, colons, slashes) before using the name in Create Channel.

---

## Gotcha 5: Slack Actions in Before-Save Context Cause Governor Limit Errors

**What happens:** A Flow triggers an unhandled "You have uncommitted work pending" error when a Slack action is placed in the before-save synchronous path.

**When it occurs:** When a Flow builder places Slack actions in the before-save execution path of a record-triggered Flow, not realizing that Slack actions are callouts requiring async context.

**How to avoid:** Always place Slack Core Actions in the after-save, asynchronous execution path. For record-triggered flows, use the "Run Asynchronously" option for all steps that include Slack actions.
