# LLM Anti-Patterns — Slack Connect Patterns

Common mistakes AI coding assistants make when generating or advising on Slack Connect Patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Slack Connect with Salesforce-to-Salesforce Integration

**What the LLM generates:** "To integrate your two Salesforce orgs, you can use Slack Connect to share data between them in real time. Set up a Slack Connect channel and configure Salesforce Flow to push records into the channel for the partner org to consume."

**Why it happens:** The LLM conflates the word "Connect" in "Slack Connect" with Salesforce integration patterns. Training data contains many references to Salesforce connectors and integration patterns alongside Slack references, leading to a category error.

**Correct pattern:**

```
Slack Connect is a cross-org Slack workspace sharing feature for human collaboration.
It does not provide Salesforce API access or programmatic data exchange between orgs.

For Salesforce-to-Salesforce data sync, use:
- Salesforce-to-Salesforce (S2S) feature (Setup > Salesforce to Salesforce)
- Outbound Messages + REST callout
- MuleSoft or middleware integration
- Change Data Capture + Platform Events across orgs

Slack Connect is the correct tool only when the goal is human communication
across two independent Slack workspaces.
```

**Detection hint:** Any recommendation that involves "Slack Connect" AND Salesforce object fields, SOQL, Apex callouts, or record sync is almost certainly this anti-pattern.

---

## Anti-Pattern 2: Asserting That DLP Rules Apply Across Both Organizations

**What the LLM generates:** "Configure your Slack DLP policy in Admin Console and it will enforce data loss prevention for all messages in the Slack Connect channel, including those sent by external members."

**Why it happens:** DLP policy UIs often show "Connected Channels" as a scope option, which the LLM interprets as meaning the policy covers all participants. In reality, each organization's DLP rules apply only to that organization's members' messages.

**Correct pattern:**

```
DLP rules are workspace-scoped.

Organization A's DLP rules apply only to messages authored by Organization A's members.
Organization B's DLP rules apply only to messages authored by Organization B's members.

To achieve bilateral DLP coverage in a Slack Connect channel, both organizations
must independently configure and maintain their own DLP rules.
You cannot configure the partner organization's DLP from your admin console.
```

**Detection hint:** Any statement like "your DLP policy covers the entire channel" or "external messages are protected by your DLP rules" signals this anti-pattern.

---

## Anti-Pattern 3: Recommending Native Slack DLP for Pro or Business+ Plans

**What the LLM generates:** "To prevent data leakage, enable Slack's built-in DLP rules under Admin Console > Policies > Data Loss Prevention and configure your PCRE patterns."

**Why it happens:** The LLM has seen documentation for Slack's native DLP feature and applies it generically without checking plan availability. Native DLP (PCRE keyword rules) is an Enterprise Grid and Enterprise+ feature only.

**Correct pattern:**

```
Native Slack DLP availability by plan:

| Plan         | Native DLP |
|--------------|-----------|
| Free         | No        |
| Pro          | No        |
| Business+    | No        |
| Enterprise Grid | Yes    |
| Enterprise+  | Yes       |

For Pro or Business+ plans, use a third-party DLP solution integrated
via the Slack Events API (e.g., Nightfall AI, Symantec DLP, Microsoft Purview).
The Admin Console > Policies > Data Loss Prevention menu does not exist on these plans.
```

**Detection hint:** Any recommendation to use "Admin Console > Policies > DLP" without first confirming the plan is Enterprise Grid or Enterprise+ is this anti-pattern.

---

## Anti-Pattern 4: Assuming Message Deletion Is Bilateral

**What the LLM generates:** "If you set a 30-day retention policy, all messages older than 30 days will be permanently deleted from the Slack Connect channel for all participants."

**Why it happens:** In single-workspace Slack channels, retention policies do delete messages globally within that workspace. The LLM generalizes this behavior to Slack Connect channels without accounting for the split-ownership model.

**Correct pattern:**

```
In a Slack Connect channel, each organization retains its own members' messages
under its own retention policy. Deletion by one organization does not affect
the partner organization's copy.

Example:
- Org A sets a 30-day retention policy.
- After 30 days, Org A's members' messages are deleted from Org A's workspace.
- Org B still retains those same messages under Org B's policy (which may be 7 years).

Retention policy delete is NOT a bilateral compliance control in Slack Connect channels.
Both organizations must independently apply matching policies, and the asymmetry
must be documented and acknowledged by legal/compliance on both sides.
```

**Detection hint:** Any statement that retention policy deletion in a Slack Connect channel is "permanent" or "applies to all participants" is this anti-pattern.

---

## Anti-Pattern 5: Treating Slack Connect as Available for Free-Plan Workspaces

**What the LLM generates:** "You can set up a Slack Connect channel with your external partner even if they are on a Free Slack workspace — they just need to accept the invitation."

**Why it happens:** Slack's general documentation discusses Connect channels broadly, and the LLM does not always retrieve the paid-plan restriction. Free plan workspaces can receive some limited external invitations in specific contexts, creating ambiguity in the training data.

**Correct pattern:**

```
Both the inviting and the receiving workspace must be on a paid Slack plan
(Pro, Business+, Enterprise Grid, or Enterprise+) to participate in Slack Connect
channel sharing.

Free plan workspaces cannot initiate or accept Slack Connect channel connections.
The acceptance step in the receiving admin's console will fail for Free plan workspaces.

If the partner organization is on a Free plan, options are:
1. Ask the partner to upgrade to a paid plan.
2. Use an alternative collaboration medium (email, Microsoft Teams, etc.).
3. Add the partner as a paid Single-Channel Guest on your workspace (different model,
   consumes your seat count, not the same as Slack Connect).
```

**Detection hint:** Any recommendation that includes "Free plan" and "Slack Connect" in the same flow without noting the incompatibility is this anti-pattern.

---

## Anti-Pattern 6: Confusing Slack Connect with the Salesforce for Slack App

**What the LLM generates:** "Slack Connect is the feature that links your Salesforce org to your Slack workspace so your team can see Salesforce records and notifications in Slack channels."

**Why it happens:** Both "Slack Connect" and the "Salesforce for Slack" app involve Slack and cross-system connectivity. The LLM conflates them due to naming similarity and co-occurrence in Salesforce documentation.

**Correct pattern:**

```
These are two distinct features:

Slack Connect:
- A Slack platform feature for sharing channels between independent Slack workspaces.
- No Salesforce involvement. Purely a Slack-to-Slack cross-org collaboration feature.
- Governed by Slack admin settings on both sides.

Salesforce for Slack app:
- A Salesforce-developed integration that connects a Salesforce org to a Slack workspace.
- Enables record preview, notifications, and Salesforce actions from within Slack.
- Requires a three-party handshake: Slack admin + Salesforce admin + Slack admin.
- Covered in skill: integration/slack-salesforce-integration-setup

Use Slack Connect when: two organizations need to collaborate in a shared Slack channel.
Use Salesforce for Slack when: your internal team needs Salesforce records in Slack.
```

**Detection hint:** Any description of Slack Connect that mentions Salesforce orgs, record previews, Setup menu, or the Salesforce for Slack app is almost certainly this anti-pattern.
