# Examples — Agentforce In Slack

## Example 1: Enabling The General Slack Actions Topic To Unlock Create Canvas

**Context:** A Salesforce admin has connected an Agentforce agent to a company Slack workspace using the standard Slack deployment flow. The agent is active and responding to Slack messages. The team wants the agent to create Slack canvases summarizing meeting action items when asked.

**Problem:** After connecting the agent to Slack, no Slack-specific actions appear in the agent's action list. The agent can answer questions using its Salesforce-backed actions but has no ability to create canvases, send DMs, or search message history. Users who ask the agent to "create a canvas" receive a response indicating the agent does not know how to do that.

**Root cause:** The General Slack Actions topic is not added to agents automatically when a Slack deployment is configured. It must be explicitly added.

**Solution:**

Step 1 — Confirm the Slack workspace is on a paid plan (Pro, Business+, or Enterprise Grid). Log in to the Slack workspace as an admin and check Settings > Administration > Billing. Canvas creation requires a paid plan.

Step 2 — In Salesforce Setup, navigate to **Agentforce Agents** and click on the relevant agent to open Agent Builder.

Step 3 — Click the **Topics** tab. Click **Add Topic**.

Step 4 — In the topic picker, search for **General Slack Actions**. This is a Salesforce-managed standard topic — it appears in the standard topic library, not in custom topics.

Step 5 — Select it and click **Add**. Save the agent.

Step 6 — If the agent transitions out of Active state after saving, click **Activate** to bring it back to Active.

Step 7 — Test in Slack:

```
User: Create a canvas summarizing the top 3 open cases for the ACME account.

Agent: I've created a Slack canvas titled "ACME Open Cases Summary" with the 3 
highest-priority open cases. You can view it here: [canvas link]
```

Step 8 — If canvas creation fails, check the Einstein Trust Layer logs for the action invocation trace. A `CANVAS_CREATE_PLAN_RESTRICTION` error code indicates the Slack plan does not support canvases. A `SCOPE_MISSING` error indicates the `canvas:write` OAuth scope was not granted during app installation.

**Why it works:** The General Slack Actions topic contains the Create Canvas, Search Message History, Send DM, and Look Up User actions bundled together. Adding the topic registers these actions with the agent's reasoning engine. The agent can then select the appropriate Slack-native action based on the user's request, just as it would select any other registered action.

---

## Example 2: Troubleshooting Private Action Authorization Failure Due To Missing Identity Mapping

**Context:** A sales team uses an Agentforce agent in their Slack workspace to retrieve their own pipeline data. The agent is configured with a private action — "Get My Open Opportunities" — that queries Opportunities owned by the invoking user. The action is marked private so that each rep sees only their own pipeline.

**Problem:** Several sales reps report that when they ask the agent about their opportunities, they receive a message: "I'm not able to retrieve your opportunities right now. Please connect your Salesforce account." Some reps have been using the agent for weeks without issue. Others, particularly new hires, consistently hit this error.

**Root cause:** Private actions require the invoking Slack user's Slack User ID to be mapped to a Salesforce User ID via the Salesforce-to-Slack identity mapping. New hires have Salesforce accounts but have never triggered the one-time OAuth flow that creates the mapping. The agent correctly refuses to execute the private action rather than falling back to a broader execution context.

**Solution:**

Step 1 — Identify the unmapped users. In Salesforce Setup, navigate to **Slack for Salesforce** > **User Mappings**. Sort by connection status. Users showing as "Not Connected" have not completed the mapping.

Step 2 — Option A (user self-service): Ask the affected Slack user to type a message to the agent that triggers a private action. The agent will respond with a connection prompt containing a link to the Salesforce OAuth authorization page. The user clicks the link, authenticates with Salesforce, and the mapping is created automatically.

Step 3 — Option B (admin provisioning): If the team requires a seamless experience where users do not see a connection prompt, the admin can pre-map identities. Collect the Salesforce User IDs and Slack User IDs for the unmapped users:

```
Salesforce User ID: retrieve via SOQL — SELECT Id, Name FROM User WHERE IsActive = true
Slack User ID: retrieve via Slack API — GET /users.lookupByEmail (requires users:read.email scope)
```

Step 4 — In the Slack for Salesforce app settings in Setup, use the bulk import interface to upload a CSV mapping Salesforce User ID to Slack User ID. Format:

```csv
salesforceUserId,slackUserId
0051a000000ABC1,U01ABCDEF12
0051a000000ABC2,U01GHIJKL34
```

Step 5 — After mapping, test with a previously unmapped user. The agent should now retrieve the user's own opportunities without a connection prompt.

Step 6 — Verify in Trust Layer logs that the private action is now stamped with the correct Salesforce User ID (not the integration user's ID) for the previously affected users.

**Why it works:** The identity proxy layer resolves the Slack User ID to a Salesforce User ID at action execution time. Once the mapping exists — whether created via user self-service OAuth or admin pre-provisioning — the proxy can perform the lookup and the private action executes under the correct Salesforce identity. The agent never needs to store or pass the user's credentials; the proxy handles the authentication context transparently.

---

## Anti-Pattern: Treating General Slack Actions Like Custom Actions

**What practitioners do:** After noticing that Create Canvas or Send DM is not available in the agent, some admins attempt to build custom Agentforce actions (Apex invocable methods or external REST actions) that call the Slack API directly to replicate the functionality.

**What goes wrong:**
- Custom Slack API calls require storing and managing a Slack OAuth token as a Named Credential or custom metadata. This token is org-wide and not associated with the invoking user's identity — private-action semantics are lost entirely.
- Custom actions that call the Slack API directly bypass the Einstein Trust Layer instrumentation. Canvas content and DM payloads sent via direct API calls are not logged or subject to ZDR policies.
- The Slack API's `canvas.create` endpoint and DM endpoint require app-level permissions that the Salesforce-managed app already holds — creating a second Slack app or token for this purpose creates a duplicate permission footprint that Slack workspace admins have to manage separately.
- Maintenance burden: when Slack updates its API or the managed app's capabilities expand with new Salesforce releases, the custom action duplicates effort and may fall out of sync.

**Correct approach:** Add the General Slack Actions standard topic to the agent in Agent Builder. This is a one-step configuration that unlocks all four Slack-native actions (Create Canvas, Search Message History, Send DM, Look Up User) without any custom code, additional OAuth tokens, or Trust Layer gaps.
