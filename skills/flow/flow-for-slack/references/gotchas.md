# Gotchas: Flow for Slack

Non-obvious platform behaviors that cause real production problems in this domain. Each gotcha names the source it rests on, or marks the claim UNVERIFIED.

## Gotcha 1: The Actions Depend on Several Setup Layers

**What happens:** A flow builder searches for "Send Slack Message" and finds nothing, or the action faults at runtime with a connection or permission error.

**When it occurs:** Salesforce for Slack Integrations isn't enabled in Slack Apps Setup, the Salesforce Slack app isn't installed in the workspace, the user hasn't connected their account, or the running user lacks the permissions.

**How to avoid:** Walk the layers in order: Slack Apps Setup (terms, apps, permissions), app installation from the Slack App Directory by a workspace owner or admin, user connection from the Slack sidebar, then permissions. UNVERIFIED (2026-10-03): an AppExchange "Salesforce for Slack" managed package is not part of the setup described in the Summer '26 Slack Integrations guide; check Salesforce Help before telling an admin to install one.

**Source:** Slack Integrations guide, Summer '26, "Enable Salesforce for Slack Integrations" and "Add Apps in Your Personal Slack Sidebar".

---

## Gotcha 2: The Permission Set Names Differ From the App Names

**What happens:** An admin looks for a "Sales Cloud for Slack" permission set and can't find it, or assigns a permission set that a user's license can't hold.

**When it occurs:** Granting access for flows that use the Sales Cloud for Slack or Service Cloud for Slack apps.

**How to avoid:** Assign Connect Salesforce with Slack (system permission) for most apps, Slack Sales User for Sales Cloud for Slack, and Connect Salesforce with Slack, Slack Service User, and Run Flows for Service Cloud for Slack. "If the user license doesn't support the permission, an error displays when you try to assign the permission set to the user."

**Source:** Slack Integrations guide, Summer '26, "Enable Salesforce for Slack Integrations" (User Permissions table and step 4).

---

## Gotcha 3: Send Message to Launch Flow Launches a Screen Flow

**What happens:** A team points Send Message to Launch Flow at an autolaunched flow, expecting the button to run background logic. The button needs a screen flow to launch.

**When it occurs:** Designs that treat the button as a remote trigger.

**How to avoid:** Build a screen flow for the recipient's task. If background work is needed, call a subflow or an autolaunched flow from that screen flow.

**Source:** Metadata API Developer Guide, InvocableActionType `slackSendMessageToLaunchFlow`: "includes a button that a recipient can use to launch a screen flow."

---

## Gotcha 4: The Target Screen Flow Needs the Slack Environment

**What happens:** The button appears in Slack, but the flow can't run there.

**When it occurs:** Screen flows saved with only the Default environment.

**How to avoid:** Save the screen flow with the Slack environment (`<environments>Slack</environments>` in metadata). The Slack value lets the flow run "in Slack and the default environment."

**Source:** Metadata API Developer Guide, Flow field `environments` (Default, Offline, Slack; API 55.0 and later).

---

## Gotcha 5: Channel Names Must Follow Slack's Rules

**What happens:** Create Slack Channel fails when the name comes straight from a record name such as "Enterprise Deal: ACME Corp Q3."

**When it occurs:** Channel names with capitals, spaces, colons, or more than 80 characters.

**How to avoid:** Normalize the name in a formula: lowercase, replace spaces with hyphens, drop other punctuation, and trim well below 80 characters. Underscores are allowed too.

**Source:** Slack API documentation, `conversations.create`: "Channel names may only contain lowercase letters, numbers, hyphens, and underscores, and must be 80 characters or less." UNVERIFIED (2026-10-03): that the Salesforce Create Slack Channel action applies exactly these rules is inferred, because the action creates the channel through Slack.

---

## Gotcha 6: "Show Record Name" Exposes Data to People Without Salesforce Access

**What happens:** Slack notifications show record names and key fields to channel members who have no access to those records in Salesforce.

**When it occurs:** Record Detail Setting set to Show Record Name and Object Type on the Enable Slack for Salesforce page (affects the Sales Cloud for Slack app).

**How to avoid:** Use Show Object Type Only where channels include people without record access, and keep sensitive fields out of messages built in flows.

**Source:** Slack Integrations guide, Summer '26, "Set Record Detail Security for Your Salesforce Apps" ("Show record name: Includes the record name and key fields, even to users who don't have access in Salesforce").

---

## Gotcha 7: Deleting a User Mapping Disconnects Every Slack App for That User

**What happens:** An admin deletes one user's Slack mapping to fix a single app. Flows that message that user or act as that user start failing for every Slack app.

**When it occurs:** Troubleshooting connections by deleting Slack User Mappings, or offboarding.

**How to avoid:** Treat mapping deletion as a full disconnect. Re-connect the user afterward, and use a fault path so the flows show the failure.

**Source:** Slack Integrations guide, Summer '26, "Disconnect Slack from Salesforce": "Disconnect a user's Salesforce account from Slack by deleting the user mapping. This action disconnects all Slack apps from the Salesforce account."

---

## Gotcha 8: Government Cloud Orgs Can't Use These Actions

**What happens:** A public-sector team designs Slack notifications for a Government Cloud org.

**When it occurs:** Government Cloud or Government Cloud Plus orgs.

**How to avoid:** Don't plan Flow-to-Slack automation there. Use email or in-app notifications instead.

**Source:** Slack Integrations guide, Summer '26: "Salesforce for Slack apps and their integrations aren't supported in Government Cloud."

---

## Gotcha 9: Slack Actions Without a Fault Path Fail Quietly for Users

**What happens:** A Slack action fails at runtime (app removed, permission revoked, channel archived). The flow fails or stops, and the only trace is a flow error email to an admin who may not read it.

**When it occurs:** Slack action elements with no fault connector.

**How to avoid:** Give every Slack action a `faultConnector` to a step that records `$Flow.FaultMessage` and alerts an owner. Store the app and workspace IDs in configuration so a reconnect doesn't require flow edits.

**Source:** Metadata API Developer Guide, FlowActionCall `faultConnector`. UNVERIFIED (2026-10-03): the exact error text for a removed Slack app or revoked token is not documented in the fetched sources.
