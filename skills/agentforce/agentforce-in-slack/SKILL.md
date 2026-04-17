---
name: agentforce-in-slack
description: "Use when configuring Slack-specific Agentforce capabilities AFTER the basic Slack deployment is complete: enabling Slack-native actions, managing public vs. private action scope, mapping Salesforce-to-Slack user identity, or troubleshooting Slack action failures. Triggers: 'add General Slack Actions topic to agent', 'configure canvas creation for Agentforce in Slack', 'Agentforce private action requires user identity mapping', 'Slack agent cannot send DMs after deployment', 'Agentforce Look Up User action not working in Slack', 'how to map Slack users to Salesforce identities for private actions'. NOT for core Agentforce setup, NOT for basic Slack OAuth installation or DM vs channel-mention mode — those are covered by agentforce/agent-channel-deployment."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - User Experience
  - Reliability
triggers:
  - "how to enable canvas creation for my Agentforce agent in Slack"
  - "General Slack Actions topic is missing from Agent Builder topic list"
  - "Agentforce private action fails because Slack user is not mapped to Salesforce"
  - "how to configure user identity mapping for private Agentforce actions in Slack"
  - "Agentforce agent in Slack cannot search message history or send DMs"
  - "troubleshoot canvas creation failure in Slack Agentforce deployment"
  - "how do public vs private Agentforce actions work in Slack"
tags:
  - agentforce
  - slack
  - slack-native-actions
  - general-slack-actions
  - slack-canvas
  - identity-mapping
  - private-actions
  - public-actions
  - agentforce-slack
inputs:
  - "Active Agentforce agent already connected to a Slack workspace (Slack deployment completed)"
  - "target Slack-native actions needed: Create Canvas, Search Message History, Send DM, Look Up User"
  - "Slack workspace plan type (Free vs. paid — required to validate canvas capability)"
  - "list of topics or actions that need private vs. public scope designation"
  - "Salesforce User IDs and Slack User IDs for identity mapping (private actions only)"
outputs:
  - "post-deployment configuration checklist to enable Slack-native actions"
  - "General Slack Actions topic setup steps"
  - "public vs. private action scope matrix with per-action recommendations"
  - "identity mapping setup instructions (self-service OAuth and admin bulk import paths)"
  - "canvas plan validation guidance and fallback design for Free workspaces"
  - "Trust Layer verification steps confirming private actions execute under correct Salesforce identity"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Agentforce In Slack

Use this skill when an Agentforce agent has already been deployed to Slack (the Slack deployment flow in Setup is complete and the agent responds to Slack messages) and the work now involves Slack-specific action capabilities, user identity management, or private vs. public action scope. This skill is the post-deployment configuration layer that unlocks Slack-native agent behaviors. It does NOT cover core Agentforce setup, agent creation, topic design, or the initial Slack OAuth installation flow — those are handled by `agentforce/agentforce-agent-creation`, `agentforce/agent-topic-design`, and `agentforce/agent-channel-deployment`.

The most important concept in this skill domain is that Agentforce connects to Slack via a **Salesforce-managed Slack app** — not a custom app created by the customer. This managed app holds the OAuth scopes, handles the session model, and routes traffic through the Einstein Trust Layer. All Slack-native actions operate through this managed app. Attempts to replicate Slack-native functionality with custom Apex invocable methods that call the Slack API directly bypass the Trust Layer, introduce token management overhead, and are an anti-pattern.

---

## Before Starting

Gather this context before working on anything in this domain:

- Has the Slack deployment been completed? Confirm in Setup > Agentforce > Slack Deployment that the workspace is connected and the agent is in Active state. This skill starts where agent-channel-deployment ends.
- Which Slack-native actions are needed? The four managed Slack-native actions are: Create Canvas, Search Message History, Send DM, and Look Up User. All four require the General Slack Actions topic.
- What is the Slack workspace plan? Canvas creation is not available on the Slack Free plan. Confirm the plan before designing canvas-based workflows.
- Are any actions user-specific (querying or modifying data the invoking user owns)? These require private action scope and Salesforce-to-Slack identity mapping.
- Have all Slack users completed identity mapping? For private actions, each Slack user must have their Slack User ID mapped to a Salesforce User ID. Unmapped users trigger hard authorization failures, not graceful degradation.

---

## Core Concepts

### The General Slack Actions Topic Is Not Auto-Added After Slack Deployment

Connecting an Agentforce agent to Slack through the Setup deployment flow does not automatically include Slack-native actions in the agent's action set. The General Slack Actions topic is a standard Salesforce-managed topic that must be explicitly added to the agent in Agent Builder. Until this topic is added, the agent has no ability to create canvases, send DMs, search message history, or look up Slack users — even though the Slack connection is active and the agent is responding to messages.

The General Slack Actions topic bundles all four Slack-native actions together. Adding the topic once unlocks all four. Removing the topic removes all four simultaneously.

### Public vs. Private Action Scope Controls Data Visibility

Every Agentforce action has a scope designation: public or private.

**Public actions** execute under the integration user's Salesforce credentials. All Slack users who trigger a public action see the same data because the action always runs as the same Salesforce identity. Public actions are appropriate for shared, non-sensitive data (for example, querying a shared FAQ knowledge base or returning org-wide announcements).

**Private actions** execute under the invoking Slack user's Salesforce identity. The agent's identity proxy layer resolves the Slack User ID to a Salesforce User ID at action invocation time and runs the action under that user's Salesforce permission set. Private actions are required for any query or mutation that is user-specific (for example, "my open cases", "my pipeline", "update my task"). Without private action scope, user-specific queries either return the integration user's data to everyone or must implement manual identity filtering — both outcomes are incorrect and violate Salesforce's record-level security model.

### Identity Mapping Is A Prerequisite For Private Actions

The Salesforce-to-Slack identity mapping is a per-user data record stored in the Salesforce org that links a Slack User ID to a Salesforce User ID. The identity proxy layer reads this record at private action invocation time to determine which Salesforce identity to use.

Identity mapping is created through two paths:

1. **User self-service OAuth**: the first time an unmapped user triggers a private action, the agent prompts them with a connection link. The user clicks the link, authenticates with Salesforce, and the mapping record is created automatically.
2. **Admin bulk provisioning**: an admin exports Salesforce User IDs and Slack User IDs, formats them as a CSV, and imports the CSV via the bulk mapping interface in Setup > Slack for Salesforce > User Mappings.

Identity mappings are stored as data records, not metadata. They are org-specific and do not survive sandbox refreshes or metadata deployments to production. Every production go-live must include an explicit step to re-provision identity mappings.

### Canvas Creation Requires A Paid Slack Plan

Slack canvases are a paid feature. The Create Canvas action is available in the General Slack Actions topic regardless of the workspace plan, so it will appear available in Agent Builder and the agent will attempt to use it. However, at runtime, canvas creation will fail in a Free workspace. The failure may not surface as a clear plan-restriction error in the Slack conversation. Always validate the workspace plan before building canvas-dependent workflows. Design fallback behavior (plain text responses) for workspaces that may be on or transition to the Free plan.

---

## Common Patterns

### Pattern 1: Enable General Slack Actions Topic

**When to use:** The Slack deployment is active but the agent has no Slack-native action capabilities (no canvas creation, no Send DM, no message history search, no Look Up User).

**How it works:**

1. In Setup, navigate to **Agentforce Agents** and click the relevant agent to open Agent Builder.
2. Click the **Topics** tab.
3. Click **Add Topic**.
4. Search for **General Slack Actions** in the topic picker. This is a standard Salesforce-managed topic — it appears in the standard library, not in custom topics.
5. Select it and click **Add**. Save the agent.
6. If the agent transitions out of Active state after saving, click **Activate**.
7. Test in Slack: ask the agent to look up a user, search message history, or (if the workspace is on a paid plan) create a canvas.

**Why not the alternative:** Do not build custom Apex invocable methods or external REST actions to call the Slack API directly. The managed topic provides all four actions with Trust Layer coverage, no token management, and Salesforce-maintained support. Custom Slack API calls bypass the Trust Layer, require managing OAuth tokens as Named Credentials, and duplicate functionality the platform already provides.

### Pattern 2: Configure Private Action Scope And Identity Mapping

**When to use:** One or more agent actions must return or modify data specific to the invoking Slack user (for example, querying the user's own cases, opportunities, or tasks).

**How it works:**

1. In Agent Builder, open the action that must be user-specific.
2. Set the action's **Scope** to **Private**. Save.
3. Communicate to Slack users that they must complete a one-time identity connection. Either:
   - Direct them to trigger a private action and follow the connection prompt the agent returns.
   - Or pre-provision mappings in bulk: collect Salesforce User IDs (SOQL: `SELECT Id, Name FROM User WHERE IsActive = true`) and Slack User IDs (Slack API: `GET /users.lookupByEmail` with `users:read.email` scope), format as CSV, and import via Setup > Slack for Salesforce > User Mappings > Bulk Import.
4. Verify mappings in Setup > Slack for Salesforce > User Mappings. Confirm mapped users show as "Connected".
5. Test with a mapped user: trigger the private action and confirm the response contains the user's own data, not the integration user's data.
6. Test with an unmapped user: confirm the agent returns a clear "please connect your account" message rather than an opaque error.

### Pattern 3: Validate And Handle Canvas Plan Restrictions

**When to use:** Canvas-based workflows are being designed or canvas creation is failing.

**How it works:**

1. Confirm the Slack workspace plan: ask the Slack workspace admin or check Settings > Administration > Billing in the Slack workspace.
2. If the workspace is on a paid plan (Pro, Business+, or Enterprise Grid), canvas creation is available. Proceed with canvas workflow design.
3. If the workspace is on Free, either:
   - Remove canvas-dependent agent instructions and replace with plain text equivalents.
   - Or initiate a workspace plan upgrade with the Slack workspace admin before designing canvas workflows.
4. Add explicit fallback instructions to the agent topic: "If canvas creation is unavailable, respond with a formatted plain-text summary instead."
5. After a canvas action is tested and confirmed working, check Einstein Trust Layer logs to confirm the canvas content passed through ZDR policies as expected.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Agent connected to Slack but Slack-native actions not available | Add General Slack Actions topic in Agent Builder | Topic is never auto-added; required for all four managed Slack actions |
| Action returns user-specific Salesforce data | Set action scope to Private; configure identity mapping | Public scope executes as integration user — wrong data for every user |
| Action returns shared non-sensitive data (FAQ, announcements) | Public scope is acceptable | No identity mapping needed; simpler deployment |
| Canvas creation needed | Verify paid Slack plan first; design fallback for Free plan | Canvas is unavailable on Free; failure is silent without plan check |
| New hire has no identity mapping | User self-service OAuth connection flow (or admin bulk import) | Mapping is not auto-created; must be provisioned per user |
| Moving from sandbox to production | Re-provision identity mappings in production explicitly | Mappings are data records, not metadata; deployments do not transfer them |
| Custom Slack API call being considered | Use General Slack Actions topic instead | Custom calls bypass Trust Layer and require manual OAuth token management |

---

## Recommended Workflow

Step-by-step instructions for configuring Slack-specific Agentforce capabilities on an already-deployed Slack agent:

1. **Confirm deployment baseline** — verify in Setup > Agentforce > Slack Deployment that the workspace is connected, the agent is Active, and users can already interact with the agent in Slack. This skill starts after the initial deployment is complete.
2. **Add the General Slack Actions topic** — open the agent in Agent Builder, navigate to Topics, and add the General Slack Actions standard topic. Save and reactivate if needed. This single step unlocks Create Canvas, Search Message History, Send DM, and Look Up User.
3. **Designate public vs. private scope for each action** — for every action in the agent, evaluate whether it accesses user-specific Salesforce data. Mark user-specific actions as Private. Mark shared-data actions as Public. Document the scope decision for each action.
4. **Provision identity mappings for private actions** — communicate the one-time connection flow to all Slack users who will trigger private actions, or bulk-import identity mappings via the admin interface. Verify mappings in Setup > Slack for Salesforce > User Mappings.
5. **Validate canvas plan compatibility** — if any canvas actions are configured, confirm the Slack workspace is on a paid plan. Add fallback topic instructions for canvas failure cases.
6. **Test all action types end-to-end in sandbox** — test each Slack-native action (canvas, DM, message search, user lookup), test at least one private action with a mapped user, and test the unmapped-user flow to confirm the agent returns a clear connection prompt.
7. **Confirm Trust Layer coverage** — review Einstein Trust Layer logs after testing to verify all Slack action traffic (canvas content, DM payloads, search results) is logged and subject to org ZDR policies.

---

## Review Checklist

Run through these before marking Slack action configuration work complete:

- [ ] General Slack Actions topic is present in the agent's topic list in Agent Builder.
- [ ] Agent is in Active state after the General Slack Actions topic was added.
- [ ] Every user-specific action (querying or modifying user-owned records) is set to Private scope.
- [ ] Every shared-data action (non-sensitive, org-wide content) is set to Public scope.
- [ ] Slack workspace plan has been confirmed as paid if canvas creation workflows are configured.
- [ ] Fallback topic instructions exist for canvas failure (plain text response alternative).
- [ ] All Slack users who will trigger private actions have identity mappings in Setup > Slack for Salesforce > User Mappings.
- [ ] Unmapped-user failure flow tested: agent returns a clear "connect your account" prompt.
- [ ] Private action tested with mapped user: response contains the user's own data, not integration user data.
- [ ] Identity mapping re-provisioning is included in the production go-live runbook.
- [ ] Einstein Trust Layer logs reviewed for canvas content and DM payloads.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **General Slack Actions topic is never auto-added** — every Slack deployment requires a manual post-deployment step in Agent Builder to add the topic. Missing this step means the agent has no Slack-native capabilities despite being fully connected.
2. **Canvas creation fails silently on Slack Free plan** — the Create Canvas action appears available in Agent Builder regardless of workspace plan. The failure only appears at runtime, often without a clear error in the Slack conversation.
3. **Private action failures are hard failures, not graceful degradation** — an unmapped user triggering a private action gets a hard refusal, not a fallback to a broader context. Design explicit connection-prompt instructions into private-action topics.
4. **Identity mappings are data, not metadata** — sandbox mappings do not survive sandbox refreshes or production promotions. Every go-live checklist must include re-provisioning identity mappings as a mandatory step.
5. **Send DM requires `im:write` scope which may be missing in older deployments** — workspaces that installed the Salesforce-managed Slack app before Spring '25 may lack this scope. The Slack workspace admin must re-authorize the app to grant the missing scope.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Post-deployment Slack action checklist | Ordered configuration steps to enable Slack-native actions on an existing deployment |
| Public vs. private action scope matrix | Per-action scope decisions with justification for each action in the agent |
| Identity mapping setup guide | Step-by-step instructions for self-service OAuth and admin bulk import paths |
| Canvas plan validation output | Workspace plan confirmation and fallback design recommendations |
| Trust Layer verification summary | Confirmation that Slack action traffic appears in Trust Layer logs with correct user identity stamps |

---

## Related Skills

- `agentforce/agent-channel-deployment` — use for initial Slack OAuth setup, managed app installation, and DM vs. channel-mention mode configuration. This skill starts where agent-channel-deployment ends.
- `agentforce/agent-actions` — use when the problem is action contract design, invocable method structure, or action availability within topics generally (not Slack-specific).
- `agentforce/agent-topic-design` — use when the problem is topic boundary design, topic instructions, or classification logic.
- `agentforce/einstein-trust-layer` — use alongside this skill to review ZDR, data masking, and audit logging policies for canvas content and DM payloads.
- `agentforce/agentforce-agent-creation` — use if the agent itself has not yet been created or if core agent setup work is needed before Slack channel work begins.

---

## Official Sources Used

- Connect an Agent to Slack (Agentforce for Slack Setup) — https://help.salesforce.com/s/articleView?id=ai.agent_deploy_emp_slack.htm
- Customizing Agentforce Agents with Custom Slack Actions — https://docs.slack.dev/ai/customizing-agentforce-agents-with-custom-slack-actions
- Set Up and Manage Agentforce in Slack — https://slack.com/help/36218109305875
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
