# LLM Anti-Patterns — Slack Salesforce Integration Setup

## Anti-Pattern 1: Claiming a Single Admin Can Complete the Three-Party Handshake

**What the LLM generates:** "Your Salesforce admin can complete the Slack connection setup in Setup > Slack > Manage Slack Connection."

**Why it happens:** LLMs are unaware of the role-separated three-party handshake requirement. They model Salesforce Setup as the complete entry point.

**Correct pattern:** The connection requires three distinct steps across two systems. Step 1 (Slack app installation) and Step 3 (activation) require Slack Workspace Owner/Admin. Step 2 (Salesforce approval) requires Salesforce System Admin. A single person can complete all steps only if they hold both roles AND both Workspace Owner and System Admin — which must be verified before assuming it's possible.

**Detection hint:** Instructions that say "your Salesforce admin can connect to Slack" without mentioning Slack Workspace admin approval are incomplete.

---

## Anti-Pattern 2: Claiming Record Previews Respect Field-Level Security

**What the LLM generates:** "Record previews in Slack only show fields the Slack user has access to in Salesforce based on their field-level security settings."

**Why it happens:** LLMs infer that Salesforce security model applies universally. They model Salesforce FLS as enforced at all points, including external app previews.

**Correct pattern:** Record preview cards render based on the page layout visible to the Platform Integration User — NOT the Slack user's FLS. All channel members see the same preview regardless of their individual Salesforce permissions. Governance must be applied at the Platform Integration User page layout level.

**Detection hint:** Any claim that Slack record previews "respect" or "enforce" individual user field-level security is incorrect.

---

## Anti-Pattern 3: Proposing Government Cloud Slack Connection as Configurable

**What the LLM generates:** "Government Cloud orgs can be connected to Slack with special configuration or through Salesforce Support."

**Why it happens:** LLMs often present restrictions as configurable with enough effort or escalation. Government Cloud's Slack restriction is absolute.

**Correct pattern:** Government Cloud orgs cannot connect to Slack workspaces. There is no configuration workaround and no Salesforce Support exception. Propose alternative integration patterns: custom Slack app via Slack SDK, MuleSoft-mediated integration.

**Detection hint:** Any suggestion that Government Cloud Slack connection can be unlocked via configuration or Support request is incorrect.

---

## Anti-Pattern 4: Ignoring the 20-Org Workspace Limit

**What the LLM generates:** Architecture recommendations that connect all Salesforce environments (production, full sandbox, partial sandbox, developer orgs) to a single Slack workspace without mentioning limits.

**Why it happens:** LLMs do not model per-workspace org connection limits and assume connections are unlimited.

**Correct pattern:** Each Slack workspace supports a maximum of 20 connected Salesforce orgs. Large organizations must prioritize which orgs to connect and may need multiple workspaces if the limit is exceeded.

**Detection hint:** Architecture designs that connect many Salesforce environments to a single Slack workspace without counting the connections may exceed the 20-org limit.

---

## Anti-Pattern 5: Omitting Individual User Account Connection Requirement

**What the LLM generates:** "Once the org is connected, all Salesforce users can access Salesforce records and data in Slack immediately."

**Why it happens:** LLMs model org connection as establishing universal user access, not as a prerequisite for individual user authorization.

**Correct pattern:** Org connection grants workspace-level app installation. Each individual user must separately connect their personal Salesforce account from the Salesforce app in Slack (Home tab → Connect). Without this step, users cannot see personalized Salesforce data, search Salesforce records, or receive personalized notifications.

**Detection hint:** Any post-connection onboarding guide that does not include the individual user personal account connection step is incomplete.
