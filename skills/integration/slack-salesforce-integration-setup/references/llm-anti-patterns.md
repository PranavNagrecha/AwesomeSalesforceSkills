# LLM Anti-Patterns — Slack Salesforce Integration Setup

Common mistakes AI assistants make when advising on connecting Salesforce and Slack. Facts cite the Slack Help Center article Connect Salesforce and Slack and the Slack Integrations guide, Spring '26, both read 2026-10-03.

## Anti-Pattern 1: Describing the connection as a Salesforce-only task, or as three different people

**What the LLM generates:** "Your Salesforce admin can complete the Slack connection in Setup > Slack > Manage Slack Connection." Or the opposite: "A single administrator can never complete the handshake."

**Why it happens:** The model sees only the Salesforce Setup page, or over-reads the role split.

**Correct pattern:** The connection is requested in Slack (Manage Salesforce Organizations), approved in Salesforce Setup by a Salesforce System Admin, and activated in Slack by an Owner or a person with the Salesforce Admin system role. One person who holds both the Slack role and Salesforce System Admin can do all three.

**Detection hint:** Instructions that omit the Slack request or activation step, or that require three separate people.

---

## Anti-Pattern 2: Claiming record previews follow each viewer's field-level security

**What the LLM generates:** "Record previews in Slack only show fields each channel member can see in Salesforce."

**Why it happens:** The model assumes the Salesforce sharing model applies at every surface.

**Correct pattern:** Admins choose the unfurling option. "Data Viewable by Slack Default Render User" and "Data Viewable by User Sharing the Link" show data in the channel according to that one user's permissions, using the URL Unfurling Slack Record Layout or the compact layout. Only the preview-button options open the record with the viewer's permissions. For Sales Cloud for Slack, "Show record name" shows the name and key fields even to users without access.

**Detection hint:** Any claim that Slack previews enforce each channel member's FLS without naming the configured unfurling option.

---

## Anti-Pattern 3: Proposing a Government Cloud connection as configurable

**What the LLM generates:** "Government Cloud orgs can be connected to Slack with special configuration or a Support case."

**Why it happens:** Models present restrictions as negotiable.

**Correct pattern:** "You can't connect Slack to Government Cloud Salesforce orgs," and Salesforce for Slack apps are not supported in Government Cloud or Government Cloud Plus. They are also not FedRAMP or HIPAA certified. Propose a custom integration instead.

**Detection hint:** Any suggestion that Government Cloud connection can be unlocked.

---

## Anti-Pattern 4: Ignoring the connection allowance, or misstating it

**What the LLM generates:** A design that connects every sandbox to one workspace, or a claim that Free plans cannot connect at all.

**Why it happens:** The model either ignores the limit or repeats an outdated rule.

**Correct pattern:** "On the Pro, Business+, and Enterprise plans, repeat the steps to connect up to 20 additional Salesforce orgs." The connection feature is listed as available on all plans. Prioritize which orgs to connect.

**Detection hint:** A connection list longer than the plan allows, or advice that rules out Free plans without a source.

---

## Anti-Pattern 5: Omitting user mapping and personal account connection

**What the LLM generates:** "Once the org is connected, all Salesforce users can use Salesforce in Slack."

**Why it happens:** The model treats the org connection as user authorization.

**Correct pattern:** Configure account mapping (Email or SAML NameID, automatic where possible; Unified Employee license users can only be mapped automatically), and have users add the app to their sidebar and connect their Salesforce account.

**Detection hint:** A rollout plan with no mapping decision and no user connection step.

---

## Anti-Pattern 6: Forgetting the per-user permission

**What the LLM generates:** Setup steps that end at installation, with no Salesforce permission work for end users.

**Why it happens:** The permission requirement sits in an Important note inside the setup steps.

**Correct pattern:** Each Slack user, including the workspace owner who adds apps, needs a permission set with the Connect Salesforce with Slack system permission on a license that supports it; apps add permissions such as Slack Sales User. Assign them before installation.

**Detection hint:** A setup guide that never mentions the Connect Salesforce with Slack permission.

---

## Anti-Pattern 7: Installing the legacy Slack-built Salesforce app

**What the LLM generates:** "Install the Slack package from AppExchange and run the Slack Setup assistant."

**Why it happens:** The legacy Slack Help article still exists and ranks well.

**Correct pattern:** That article says the Slack-built Salesforce app "no longer supports new installations". Use the Salesforce-built integrations (Slack Apps Setup in Salesforce) and the org connection steps.

**Detection hint:** Instructions that reference the Slack AppExchange package or the Slack Setup assistant for a new installation.
