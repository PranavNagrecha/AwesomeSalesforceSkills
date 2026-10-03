# Gotchas — Slack Salesforce Integration Setup

Non-obvious behaviors that stall or weaken a Slack and Salesforce rollout. "Slack Integrations guide" means Slack Integrations, Spring '26 (slack_apps.pdf). "Slack Help: Connect" means the Slack Help Center article Connect Salesforce and Slack (slack.com/help/articles/30754346665747), fetched 2026-10-03.

## Gotcha 1: The Handshake Needs Roles in Two Systems, Not Three People

**What happens:** The connection sits in a pending state for days, or a team insists on three separate administrators when one person holds the needed roles.

**When it occurs:** Step 1 (request) is done in Slack under Manage Salesforce Organizations. Step 2 (approve) needs a Salesforce System Admin in Setup > Platform Tools > Slack > Manage Slack Connection. Step 3 (activate) can be done by "Owners and people with the Salesforce Admin system role in Slack"; a plain workspace admin without that system role cannot activate. An earlier version of this skill said a single administrator can never complete all three steps; the article ties the steps to roles, not to separate people.

**How to avoid:** Identify the Slack Owner (or Salesforce Admin system role holder) and the Salesforce System Admin before starting, and run the steps in one session.

**Source:** Slack Help: Connect (Steps 1 to 3 and "Who can use this feature?").

---

## Gotcha 2: Government Cloud Orgs Cannot Connect, and the Apps Are Not FedRAMP or HIPAA Certified

**What happens:** A public sector project discovers at the approval step, or in an audit, that the integration is not allowed.

**When it occurs:** "You can't connect Slack to Government Cloud Salesforce orgs." The Slack Integrations guide adds: "Salesforce for Slack apps and their integrations aren't supported in Government Cloud. Don't turn on the feature in Government Cloud or Government Cloud Plus orgs." It also states that Salesforce for Slack "isn't certified with the Federal Risk and Authorization Management Program (FedRAMP) or the Health Insurance Portability and Accountability Act of 1996 (HIPAA)" and "can't be used within Blackjack".

**How to avoid:** Run a compliance gate before any setup. Propose alternatives (a custom Slack app, middleware, or email notifications) for those orgs.

**Source:** Slack Help: Connect (Keep in mind); Slack Integrations guide, Enable Salesforce for Slack Integrations (Note) and Salesforce Apps for Slack Limitations (Blackjack Not Supported).

---

## Gotcha 3: Every Slack User Needs the Connect Salesforce With Slack Permission

**What happens:** The workspace owner cannot add the apps, or some users see errors after the connection is live.

**When it occurs:** "Unless otherwise specified, each Slack user, including the Slack workspace owner that adds apps in Slack, must be assigned a permission set on the Salesforce license that has the Connect Salesforce with Slack system permission. Some licenses don't support Slack integration. If the user license doesn't support the permission, an error displays when you try to assign the permission set to the user." Apps add their own permissions, such as Slack Sales User for Sales Cloud for Slack and Slack Service User plus Run Flows for Service Cloud for Slack.

**How to avoid:** Create one permission set with the system permission, assign it before installation, and check license support for every user population (for example community licenses).

**Source:** Slack Integrations guide, Enable Salesforce for Slack Integrations (User Permissions table and step 4 Important note).

---

## Gotcha 4: Record Link Previews Follow the Configured Option, Not Each Viewer's Field Access

**What happens:** A user posts an Opportunity link and the channel sees the amount and stage, including members who cannot see those fields in Salesforce.

**When it occurs:** Admins choose how unfurled links appear. The options "Data Viewable by Slack Default Render User" and "Data Viewable by User Sharing the Link" display record data in the channel according to that user's permissions, using the URL Unfurling Slack Record Layout for the object or the compact layout if none is assigned. The preview-button options open a window "with the viewer's permissions" and display no data in the channel. For Sales Cloud for Slack, "Show record name" includes the record name and key fields "even to users who don't have access in Salesforce". An earlier version of this skill tied previews to the page layout of the Platform Integration User; the guide describes Slack Record Layouts and these options instead.

**How to avoid:** Use Preview Button Only (or Name, Type, and Preview Button) for sensitive objects. If a "data viewable" option is required, assign a URL Unfurling Slack Record Layout with only safe fields. Use Show object type only for Sales Cloud for Slack where record names are sensitive.

**Source:** Slack Integrations guide, Unfurling Slack Record Layouts with Data Sharing Options; Create a New URL Unfurling Slack Record Layout; Set Record Detail Security for Your Salesforce Apps.

---

## Gotcha 5: The Org Limit Is "Up to 20 Additional" on Paid Plans

**What happens:** An enterprise tries to connect every sandbox to one workspace and runs out of connections.

**When it occurs:** "On the Pro, Business+, and Enterprise plans, repeat the steps to connect up to 20 additional Salesforce orgs and Slack." The connection feature itself is "Available on all plans", so an earlier version of this skill's claim that a Free plan cannot connect at all is not supported by the article. UNVERIFIED (2026-10-03): whether "20 additional" means 21 orgs in total, and how many orgs a Free plan can connect, are not stated.

**How to avoid:** Connect production and the sandboxes that need Slack features first, and keep a register of connections per workspace.

**Source:** Slack Help: Connect (Configure a connection; Who can use this feature?).

---

## Gotcha 6: Org Connection Is Not User Access

**What happens:** After the connection is active, users report that Salesforce search and records do not work in Slack.

**When it occurs:** With automatic account mapping (Email or SAML NameID), members with mapped accounts get the Salesforce app automatically. With manual mapping, members are prompted to sign in to Salesforce. For the Salesforce for Slack apps, each user adds the app to their sidebar and connects their Salesforce account ("I agree to allow Slack to access my Salesforce account"). Users with the Unified Employee license "can only be mapped automatically."

**How to avoid:** Prefer automatic mapping, turn it on where Unified Employee licenses exist, and include the personal connection step in user onboarding.

**Source:** Slack Help: Connect (Step 1 note, Manually map member accounts, Keep in mind); Slack Integrations guide, Add Apps in Your Personal Slack Sidebar.

---

## Gotcha 7: IP Restrictions and Org URL Changes Break the Connection Quietly

**What happens:** Slack features stop working after a network hardening project or a My Domain change.

**When it occurs:** "Features that rely on a connection between Slack and Salesforce may not work as expected when Salesforce IP restrictions are enabled." "If you change your Salesforce org URL, you'll have to update your connection to Slack."

**How to avoid:** Review IP restriction plans with the Slack owner, and add "update the Slack connection" to the My Domain change runbook.

**Source:** Slack Help: Connect (Keep in mind).

---

## Gotcha 8: The Slack-Built Salesforce App Is Legacy

**What happens:** A team follows an old guide, installs the Slack package from AppExchange, and cannot complete setup.

**When it occurs:** The Slack Help article Configure Salesforce for use with Slack says its instructions apply "only to the Slack-built Salesforce app which no longer supports new installations" and recommends the Salesforce-built integrations. An earlier version of this skill cited that article as a setup source.

**How to avoid:** Use the Salesforce-built integrations and the connection steps above for new work.

**Source:** Slack Help Center, Configure Salesforce for use with Slack (slack.com/help/articles/360044038514), fetched 2026-10-03.

---

## Gotcha 9: Large Records Lose Fields in Slack Modals

**What happens:** Users editing a record in Slack cannot find some fields.

**When it occurs:** Records shown with the legacy dynamic layout "are subject to Slack's block limit, which is 100 blocks in a modal. If a record is too large to be displayed or edited in a Slack modal, some fields aren't shown." Notes, Tasks, Events, and Swarm creation are not supported in Slack Record Layouts.

**How to avoid:** Create a Slack Record Layout per object with only the fields users need in Slack.

**Source:** Slack Integrations guide, Salesforce Apps for Slack Limitations (Compact Layout for Record Views; Object-Level Support for Slack Record Layouts).
